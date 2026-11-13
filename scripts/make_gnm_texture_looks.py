"""Rasterize skin transfer onto native UVs and author portable eye/PBR maps."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt, map_coordinates

ROOT = Path(__file__).resolve().parents[1]
LOOKS = [
    ('look_01', 'Mature skin / warm hazel', 'onlytheghosts_old_eurasian_male', 'old_eurasian_male_diffuse.png', (.30, .19, .065)),
    ('look_02', 'Deep skin / amber', 'mindfront_skin_male_african_middleage', 'skin_male_african_middleage.png', (.23, .105, .035)),
    ('look_03', 'Freckled / green', 'toigo_light_skin_male_freckles', 'young_lightskinned_male_diffuse_Freckles.png', (.14, .23, .12)),
    ('look_04', 'Ginger / blue grey', 'toigo_light_skin_male_ginger', 'young_lightskinned_male_diffuse_Ginger.png', (.11, .20, .27)),
    ('look_05', 'Bronze / brown', 'toigo_light_skin_male_bronze', 'young_lightskinned_male_diffuse_Bronze.png', (.22, .12, .045)),
]


def uv_surface(size):
    cache = ROOT/f'work/gnm/uv_surface_{size}.npz'
    transfer_hash = hashlib.sha256((ROOT/'assets/gnm/skin_transfer.npz').read_bytes()).hexdigest()
    if cache.exists():
        with np.load(cache) as data:
            if str(data['transfer_hash']) == transfer_hash:
                return {key: data[key] for key in ('mask', 'source_uv', 'position', 'lip', 'padding')}
    with np.load(ROOT/'assets/gnm/skin_transfer.npz') as data:
        uv, source, position, lip = [data[k] for k in ('native_uvs', 'source_uvs', 'positions', 'lip_weights')]
    mask = np.zeros((size, size), bool)
    coords = np.zeros((size, size, 6), np.float32)
    for face in range(len(uv)):
        for corner in ([0, 1, 2], [0, 2, 3]):
            points = uv[face, corner] * size
            points[:, 1] = size-points[:, 1]
            low = np.maximum(np.floor(points.min(0)).astype(int), 0)
            high = np.minimum(np.ceil(points.max(0)).astype(int), size-1)
            if (low > high).any():
                continue
            x, y = np.meshgrid(np.arange(low[0], high[0]+1)+.5, np.arange(low[1], high[1]+1)+.5)
            p0, p1, p2 = points
            denominator = (p1[1]-p2[1])*(p0[0]-p2[0])+(p2[0]-p1[0])*(p0[1]-p2[1])
            if abs(denominator) < 1e-10:
                continue
            w0 = ((p1[1]-p2[1])*(x-p2[0])+(p2[0]-p1[0])*(y-p2[1]))/denominator
            w1 = ((p2[1]-p0[1])*(x-p2[0])+(p0[0]-p2[0])*(y-p2[1]))/denominator
            weights = np.stack([w0, w1, 1-w0-w1], -1)
            inside = (weights >= -1e-6).all(-1)
            values = np.concatenate([source[face, corner], position[face, corner], lip[face, corner, None]], axis=-1)
            patch = weights @ values
            view = coords[low[1]:high[1]+1, low[0]:high[0]+1]
            view[inside] = patch[inside]
            mask[low[1]:high[1]+1, low[0]:high[0]+1] |= inside
    ids = np.full((size, size), -1, np.int32)
    ids[mask] = np.arange(mask.sum())
    nearest = distance_transform_edt(~mask, return_distances=False, return_indices=True)
    padding = ids[nearest[0], nearest[1]]
    compact = coords[mask]
    result = {'mask': mask, 'source_uv': compact[:, :2], 'position': compact[:, 2:5], 'lip': compact[:, 5], 'padding': padding}
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **result, transfer_hash=transfer_hash)
    print('NATIVE_UV_RASTER_READY', size, int(mask.sum()), flush=True)
    return result


def field(position, seed, frequency, terms=8):
    rng = np.random.default_rng(seed)
    result = np.zeros(len(position), np.float32)
    for i in range(terms):
        direction = rng.normal(size=3)
        direction *= frequency*rng.uniform(.75, 1.4)/np.linalg.norm(direction)
        phase = (position*direction.astype(np.float32)).sum(1)*np.float32(2*math.pi)+rng.uniform(0, 6.28)
        result += np.sin(phase).astype(np.float32)
    return result/math.sqrt(terms/2)


def write_map(path, values, surface, bits=8):
    dense = values[surface['padding']]
    if bits == 16:
        Image.fromarray(np.round(np.clip(dense, 0, 1)*65535).astype(np.uint16)).save(path)
    else:
        Image.fromarray(np.round(np.clip(dense, 0, 1)*255).astype(np.uint8)).save(path)


def skin_maps(folder, source_path, surface, seed):
    with Image.open(source_path) as image:
        source = np.asarray(image.convert('RGB'), dtype=np.float32)/255
    coordinates = np.array([(1-surface['source_uv'][:, 1])*(source.shape[0]-1), surface['source_uv'][:, 0]*(source.shape[1]-1)])
    color = np.stack([map_coordinates(source[:, :, c], coordinates, order=1, mode='nearest') for c in range(3)], 1)
    p = surface['position']
    detail = field(p, seed, 2400, 10)
    fine = field(p, seed+1, 6500, 6)
    mottling = np.clip(field(p, 416, 38, 6), -2, 2)
    # These continuous 3D fields agree on both sides of a native UV seam.
    color *= 1+mottling[:, None]*np.array([.008, .012, .013], np.float32)
    color *= 1+np.clip(detail[:, None], -2, 2)*.004
    lip = np.clip(surface['lip'], 0, 1)
    pore = np.clip((-detail-.65)/1.5, 0, 1)**1.6
    height = .55-.22*pore+.025*np.clip(fine, -2, 2)
    t_zone = np.exp(-(p[:, 0]/.026)**2)*np.exp(-((p[:, 2]+.02)/.10)**4)*(p[:, 1] < .01)
    rough = np.clip(.48-.10*t_zone-.08*lip+.022*detail, .28, .62)
    write_map(folder/'skin_basecolor.png', color, surface)
    write_map(folder/'skin_height.png', height, surface, 16)
    write_map(folder/'skin_roughness.png', rough, surface)
    Image.fromarray(surface['mask'].astype('uint8')*255).save(folder/'skin_coverage.png')


def eye_maps(folder, side, base_color, seed, size=2048):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    x = (xx+.5)/size-.5
    y = .5-(yy+.5)/size
    radius = np.sqrt(x*x+y*y)
    angle = np.arctan2(y, x)
    iris_r, pupil_r = .18492, .04985
    r = (radius-pupil_r)/(iris_r-pupil_r)
    phase = rng.uniform(0, 2*math.pi)
    warp = .038*np.sin(angle*17+phase)+.025*np.sin(angle*37-radius*80+phase*.7)
    fiber = np.zeros_like(radius)
    for frequency, strength in [(71, .30), (119, .24), (181, .15), (293, .07)]:
        fiber += strength*np.sin(angle*frequency+warp*frequency+np.sin(r*13+angle*7)*1.8+r*frequency*.023)
    crypts = np.clip(np.sin(angle*43+np.sin(angle*11+phase)*2+r*4)*np.sin(r*27+angle*9+phase), 0, 1)
    ring = np.exp(-((r-.29)/.09)**2)
    limbus = np.clip((1-r)/.11, 0, 1)
    iris = np.array(base_color, np.float32)[None, None, :]*(1.0+fiber[:, :, None]*.50)
    iris *= (1-.35*crypts[:, :, None])
    iris += ring[:, :, None]*np.array([.07, .035, .006])
    iris *= (.26+.74*limbus[:, :, None])
    veins = Image.new('L', (size, size), 0)
    draw = ImageDraw.Draw(veins)
    for i in range(38):
        start = rng.uniform(-math.pi, math.pi)
        inner = rng.uniform(.215, .30)
        outer = rng.uniform(.38, .48)
        phase = rng.uniform(0, 6.28)
        coords = []
        for t in np.linspace(0, 1, 55):
            rad = inner+(outer-inner)*t
            theta = start+.035*math.sin(t*13+phase)+.055*math.sin(t*5+phase)
            coords.append(((.5+rad*math.cos(theta))*size, (.5-rad*math.sin(theta))*size))
        draw.line(coords, fill=int(rng.uniform(45, 115)), width=int(rng.integers(1, 3)))
        for j in (20, 35):
            branch = [coords[j]]
            fork = rng.choice([-.10, .10])
            for k in range(1, 15):
                t = j/54+k/80
                rad = inner+(outer-inner)*t
                theta = start+.07*math.sin(t*10+phase)+(k/14)*fork
                branch.append(((.5+rad*math.cos(theta))*size, (.5-rad*math.sin(theta))*size))
            draw.line(branch, fill=40, width=1)
    vein = np.asarray(veins.filter(ImageFilter.GaussianBlur(.55)), dtype=np.float32)/255
    base = np.empty((size, size, 3), np.float32)
    peripheral = np.clip((radius-.20)/.28, 0, 1)
    base[:] = (.87, .85, .80)
    base -= peripheral[:, :, None]*np.array([.02, .045, .045])
    base += vein[:, :, None]*np.array([.10, -.20, -.18])
    iris_mask = radius < iris_r
    pupil_mask = radius < pupil_r
    base[iris_mask] = iris[iris_mask]
    base[pupil_mask] = (.001, .001, .001)
    height = np.full((size, size), .5, np.float32)
    height[iris_mask] = np.clip(.5+.2*fiber[iris_mask]-.13*crypts[iris_mask], 0, 1)
    height[pupil_mask] = .3
    Image.fromarray(np.round(np.clip(base, 0, 1)*255).astype('uint8')).save(folder/f'eye_{side}_basecolor.png')
    Image.fromarray(np.round(height*65535).astype('uint16')).save(folder/f'eye_{side}_height.png')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, default=4096)
    parser.add_argument('--look', choices=[a[0] for a in LOOKS])
    parser.add_argument('--eyes-only', action='store_true')
    args = parser.parse_args()
    surface = None if args.eyes_only else uv_surface(args.size)
    source_manifest = json.loads((ROOT/'assets/source_skins/manifest.json').read_text())
    output = ROOT/'textures'
    entries = []
    for index, (key, label, source, filename, color) in enumerate(LOOKS):
        if args.look and key != args.look:
            continue
        folder = output/key
        folder.mkdir(parents=True, exist_ok=True)
        source_path = ROOT/'work/source_skins/skins'/source/filename
        if not args.eyes_only:
            skin_maps(folder, source_path, surface, 2026+index*101)
        elif not (folder/'skin_basecolor.png').exists():
            raise ValueError('Generate the skin maps before using --eyes-only')
        for side_index, side in enumerate(('L', 'R')):
            eye_maps(folder, side, color, 7051+index*91+side_index*17)
        entry = {'id': key, 'label': label, 'source_material': source,
                 'source_image': source_path.relative_to(ROOT).as_posix(), 'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
                 'source_license': 'CC0-1.0', 'source_author': source_manifest['materials'][source]['author'],
                 'face_resolution': [args.size, args.size], 'eye_resolution': [2048, 2048],
                 'skin_height_encoding': '16-bit UNORM; shader bump distance defines physical amplitude',
                 'eye_uv_contract': 'GNM native eye-interior disk; pupil radius .04985 UV, iris radius .18492 UV; separate L/R maps',
                 'native_uvs': 'Unchanged GNM Head 3.0 per-region quad_uvs',
                 'status': 'Generated; visual/portability review pending',
                 'modifications': 'Spatial transfer onto native GNM UVs, continuous object-space pore/roughness fields and minor color modulation. Iris/sclera maps authored procedurally for this project.',
                 'files': {p.name: {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in folder.glob('*.png')}}
        (folder/'manifest.json').write_text(json.dumps(entry, indent=2)+'\n')
        entries.append(entry)
        print('TEXTURE_LOOK_READY', key, label, flush=True)
    existing = {p.parent.name: json.loads(p.read_text()) for p in output.glob('look_*/manifest.json')}
    (output/'manifest.json').write_text(json.dumps({'looks': list(existing.values()), 'visual_acceptance': 'Pending render review; source facial resolution is lower than exported 4K maps.'}, indent=2)+'\n')


if __name__ == '__main__':
    main()
