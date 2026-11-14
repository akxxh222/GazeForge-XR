"""Project attributed scan microdetail onto native GNM skin texture samples."""
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.interpolate import RBFInterpolator
from scipy.ndimage import gaussian_filter, map_coordinates

ROOT = Path(__file__).resolve().parents[1]


def controls():
    # Target frontal world (X,Z), meters from the eye midpoint, to source
    # atlas image coordinates expressed in the 1024px albedo reference.
    pins = [((0, .102), (512, 30)), ((0, .070), (512, 125)),
            ((0, .035), (512, 235)), ((0, 0), (512, 325)),
            ((0, -.035), (512, 413)), ((0, -.065), (512, 462)),
            ((0, -.077), (512, 495)), ((0, -.110), (512, 590)),
            ((0, -.140), (512, 710))]
    for sign in (-1, 1):
        for x, z, u, v in [(.03085, 0, 81, 303), (.030, .018, 78, 270),
                            (.048, 0, 115, 300), (.016, 0, 46, 304),
                            (.050, -.040, 160, 405), (.052, -.090, 150, 540),
                            (.072, .015, 235, 272), (.080, -.035, 260, 410),
                            (.013, -.043, 30, 425), (.023, -.072, 52, 479)]:
            pins.append(((sign*x, z), (512+sign*u, v)))
    return pins


def scan_detail(surface):
    source = ROOT/'assets/skin_detail/Infinite-Level_02_Disp_NoSmoothUV-4096.jpg'
    manifest = json.loads((source.parent/'manifest.json').read_text())
    info = next(f for f in manifest['files'] if f['file'] == source.name)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != info['sha256']:
        raise ValueError('Scan source checksum mismatch')
    p = surface['position']
    fingerprint = hashlib.sha256((digest+json.dumps(controls())+str(len(p))+
                                  hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+
                                  hashlib.sha256((ROOT/'assets/gnm/skin_transfer.npz').read_bytes()).hexdigest()).encode()).hexdigest()
    cache = ROOT/'work/gnm'/('scan_detail_'+fingerprint[:16]+'.npz')
    if cache.exists():
        with np.load(cache, allow_pickle=False) as data:
            return data['micro'], data['meso']
    with Image.open(source) as image:
        height = np.array(image, dtype=np.float32)/255
    # Remove large-scale scan shape, including the closed eyelids and nose.
    # Remaining bands provide appearance detail, not metric scan deformation.
    smooth = gaussian_filter(height, .65)
    micro = smooth-gaussian_filter(height, 3.2)
    meso = gaussian_filter(height, 2.0)-gaussian_filter(height, 19)
    roi = np.s_[int(.33*height.shape[0]):int(.41*height.shape[0]),
                int(.31*height.shape[1]):int(.42*height.shape[1])]
    micro /= max(float(np.quantile(np.abs(micro[roi]), .90)), .002)
    meso /= max(float(np.quantile(np.abs(meso[roi]), .90)), .004)
    pins = controls()
    transform = RBFInterpolator(np.array([v[0] for v in pins]),
                                np.array([v[1] for v in pins])/1024,
                                kernel='thin_plate_spline', smoothing=1e-9)
    weight = np.clip((.055-p[:, 1])/.030, 0, 1)
    weight *= np.clip((p[:, 2]+.135)/.025, 0, 1)
    weight *= np.clip((.085-p[:, 2])/.020, 0, 1)
    weight *= np.clip((.080-np.abs(p[:, 0]))/.015, 0, 1)
    weight = weight*weight*(3-2*weight)
    ids = np.flatnonzero(weight > 0)
    fine = np.zeros(len(p), dtype=np.float32)
    medium = np.zeros(len(p), dtype=np.float32)
    for start in range(0, len(ids), 100000):
        selected = ids[start:start+100000]
        uv = transform(p[selected][:, [0, 2]])
        coords = np.array([uv[:, 1]*(height.shape[0]-1), uv[:, 0]*(height.shape[1]-1)])
        fine[selected] = np.clip(map_coordinates(micro, coords, order=1, mode='nearest'), -2.5, 2.5)*weight[selected]
        medium[selected] = np.clip(map_coordinates(meso, coords, order=1, mode='nearest'), -2.5, 2.5)*weight[selected]
    np.savez_compressed(cache, micro=fine, meso=medium)
    print('SCAN_DETAIL_READY', len(ids), 'frontal native surface samples', flush=True)
    return fine, medium
