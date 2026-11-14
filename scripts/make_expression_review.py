"""Make checksum-linked contact sheets covering every decoded video frame."""
import argparse
import json
from pathlib import Path

import cv2
from PIL import Image, ImageDraw
from validate_expression_capture import ROOT, MODES, sha, eye_crop


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT/'work/milestone4/capture')
    parser.add_argument('--output', type=Path, default=ROOT/'tests/milestone4/temporal')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    index = {'method': 'Decoded MP4 frames in time order; aspect-preserving eye-region crops, no synthetic intermediate images',
             'builder_sha256': sha(Path(__file__)), 'modes': {}}
    for mode in MODES:
        path = args.input/mode/'capture.json'
        if not path.exists():
            continue
        receipt = json.loads(path.read_text(encoding='utf-8'))
        if receipt['status'] != 'COMPLETE':
            continue
        video = args.input/mode/receipt['video']['file']
        if sha(video) != receipt['video']['sha256']:
            raise ValueError('Video checksum mismatch: '+str(video))
        cap = cv2.VideoCapture(str(video))
        pages, numbers, page, draw, count = [], [], None, None, 0
        for record in receipt['frames']:
            ok, frame = cap.read()
            if not ok:
                raise ValueError('Video truncated: '+str(video))
            slot = count % 36
            if slot == 0:
                page = Image.new('RGB', (1536, 960), (20, 23, 29))
                draw = ImageDraw.Draw(page)
                numbers = []
            x, y = slot % 6*256, slot // 6*160
            pose = record['pose']
            draw.text((x+7, y+5), f'{record["frame"]:03d}  {record["time_s"]:.2f}s  open {pose["opening_L"]:.2f}', fill='white')
            page.paste(eye_crop(frame, pose), (x, y+26))
            numbers.append(record['frame'])
            count += 1
            if count % 36 == 0 or count == len(receipt['frames']):
                output = args.output/f'{mode}_{len(pages)+1:02d}.png'
                page.save(output)
                pages.append({'file': output.name, 'sha256': sha(output), 'frames': numbers})
        extra, _ = cap.read()
        cap.release()
        if extra:
            raise ValueError('Unmanifested extra frames: '+str(video))
        index['modes'][mode] = {'video_sha256': sha(video), 'receipt_sha256': sha(path), 'decoded_frames': count, 'pages': pages}
    path = args.input/'clockwise/capture.json'
    if path.exists():
        receipt = json.loads(path.read_text(encoding='utf-8'))
        if receipt['status'] == 'COMPLETE':
            sheet = Image.new('RGB', (1280, 560), (20, 23, 29))
            draw = ImageDraw.Draw(sheet)
            sources = []
            for i, record in enumerate(receipt['frames']):
                image_path = args.input/'clockwise'/record['file']
                if sha(image_path) != record['sha256']:
                    raise ValueError('Clockwise image checksum mismatch: '+str(image_path))
                x, y = i % 5*256, i // 5*280
                pose = record['pose']
                draw.text((x+7, y+6), f'{record["frame"]:02d}  h={pose["input"]["h"]:+.2f} v={pose["input"]["v"]:+.2f}', fill='white')
                with Image.open(image_path) as image:
                    sheet.paste(image.convert('RGB').resize((256, 256), Image.Resampling.LANCZOS), (x, y+24))
                sources.append({'file': record['file'], 'sha256': record['sha256']})
            output = args.output/'clockwise_faces.png'
            sheet.save(output)
            index['clockwise'] = {'receipt_sha256': sha(path), 'sheet': output.name, 'sha256': sha(output), 'sources': sources}
    (args.output/'index.json').write_text(json.dumps(index, indent=2)+'\n', encoding='utf-8')
    print('IRISX_TEMPORAL_SHEETS', {mode: row['decoded_frames'] for mode, row in index['modes'].items()})


if __name__ == '__main__':
    main()
