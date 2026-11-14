"""Feather shared color along native UV cut edges without changing the UVs."""
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, map_coordinates


def paired_cut_samples(model_path, size):
    with np.load(model_path, allow_pickle=False) as model:
        faces, uv = model['quads'], model['quad_uvs']
        skin = model['vertex_groups'][model['vertex_group_names'].tolist().index('skin')]
        ids = np.flatnonzero((skin[faces] > .5).all(1))
    edges, left, right = {}, [], []
    for face in ids:
        for corner in range(4):
            a, b = int(faces[face, corner]), int(faces[face, (corner+1)%4])
            coords = uv[face, [corner, (corner+1)%4]]
            if a > b:
                a, b, coords = b, a, coords[::-1]
            key = a, b
            if key not in edges:
                edges[key] = face, coords
                continue
            other, other_uv = edges[key]
            if np.max(np.abs(coords-other_uv)) <= 1e-5:
                continue
            count = max(4, int(np.ceil(max(np.linalg.norm(coords[1]-coords[0]),
                                           np.linalg.norm(other_uv[1]-other_uv[0]))*size*3)))
            t = (np.arange(count, dtype=np.float32)+.5)/count
            pair = []
            for edge, center in [(coords, uv[face].mean(0)), (other_uv, uv[other].mean(0))]:
                points = edge[0]*(1-t[:, None])+edge[1]*t[:, None]
                direction = center-points
                points += direction/np.maximum(np.linalg.norm(direction, axis=1, keepdims=True), 1e-12)*(.6/size)
                pair.append(np.stack([(1-points[:, 1])*size-.5, points[:, 0]*size-.5], 1))
            left.append(pair[0])
            right.append(pair[1])
    return np.concatenate(left), np.concatenate(right)


def feather_native_seams(image_path, model_path, iterations=4, width_px=18):
    image_path = Path(image_path)
    with Image.open(image_path) as image:
        rgb = np.array(image.convert('RGB'), dtype=np.float32)/255
    size = rgb.shape[0]
    left, right = paired_cut_samples(model_path, size)
    locations = np.concatenate([left, right])
    pixel = np.clip(np.round(locations).astype(int), 0, size-1)
    counts = np.zeros((size, size), dtype=np.float32)
    np.add.at(counts, (pixel[:, 0], pixel[:, 1]), 1)
    distance = distance_transform_edt(counts == 0).astype(np.float32)
    falloff = np.clip(1-distance/width_px, 0, 1)
    falloff = falloff*falloff*(3-2*falloff)
    sigma = width_px/3
    smooth_counts = gaussian_filter(counts, sigma, mode='nearest')
    valid = smooth_counts > 1e-10
    delta = np.zeros_like(counts)
    before = None
    for iteration in range(iterations):
        values = []
        for points in (left, right):
            values.append(np.stack([map_coordinates(rgb[:, :, c], points.T, order=1, mode='nearest')
                                    for c in range(3)], 1))
        difference = values[1]-values[0]
        if before is None:
            before = float(np.quantile(np.sqrt(np.square(difference).mean(1)), .95))
        correction = np.concatenate([difference*.5, -difference*.5])
        for channel in range(3):
            delta.fill(0)
            np.add.at(delta, (pixel[:, 0], pixel[:, 1]), correction[:, channel])
            filtered = gaussian_filter(delta, sigma, mode='nearest')
            filtered[valid] /= smooth_counts[valid]
            filtered[~valid] = 0
            rgb[:, :, channel] += filtered*falloff
        np.clip(rgb, 0, 1, out=rgb)
    Image.fromarray(np.round(rgb*255).astype(np.uint8)).save(image_path)
    a = np.stack([map_coordinates(rgb[:, :, c], left.T, order=1, mode='nearest') for c in range(3)], 1)
    b = np.stack([map_coordinates(rgb[:, :, c], right.T, order=1, mode='nearest') for c in range(3)], 1)
    return {'method':'Paired native cut-edge color constraints with smooth local correction on both charts',
            'dense_paired_samples':len(left), 'iterations':iterations, 'feather_width_px':width_px,
            'p95_rgb_rms_before':before, 'p95_rgb_rms_after':float(np.quantile(np.sqrt(np.square(a-b).mean(1)), .95)),
            'scope':'Albedo cut continuity only; render review still required. Geometry and UV coordinates are unchanged.'}
