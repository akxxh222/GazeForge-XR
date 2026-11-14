"""Compare actual pre-groom and revised Cycles review images."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'tests/milestone2'
before = ROOT/'work/milestone2_before_groom'
after = folder/'look_01'
size, margin = 600, 28
canvas = Image.new('RGB', (1284, 1390), '#101820')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 27)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 20)
draw.text((margin, 18), 'IrisX | Scalp groom, shaved stubble and controlled eye reflections', font=font, fill='#ecf4f7')
draw.text((margin, 66), 'Before | bald static draft', font=small, fill='#b7c9d1')
draw.text((656, 66), 'Revised | actual Cycles render', font=small, fill='#92dcc9')
for column, source in enumerate([before, after]):
    x = margin+column*628
    for row, name in enumerate(['front.png', 'eye_closeup.png']):
        with Image.open(source/name) as image:
            canvas.paste(image.convert('RGB').resize((size, size), Image.Resampling.LANCZOS), (x, 104+row*612))
draw.text((margin, 1337), 'Same native head, gaze and camera. Lighting, materials, sampling and strands revised.', font=small, fill='#b7c9d1')
canvas.save(folder/'groom_comparison.png')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

receipt = {
    'stage': 'Milestone 2 static scalp groom and eye-reflection refinement',
    'status': 'Implemented and rendered; final visual acceptance remains open',
    'primary_scene': 'work/gnm/scene_look_01_realism.blend',
    'all_scenes': [f'work/gnm/scene_look_{i:02d}_realism.blend' for i in range(1, 6)],
    'changes': [
        'Original 64,000 native hair curves with 12 points each, irregular hairline, anatomical ear exclusion, tapered sides and a swept-back side part.',
        'Original sparse short shaved stubble and darker neutral brows.',
        'Fill light raised above the pupil; one restrained rectangular key catchlight; less duplicated interior specularity and reduced micro-bump.',
        '256-sample denoised Cycles review renders; 128-sample denoised viewport previews, indirect clamp and glossy filtering.',
        'Material Preview/camera framing and hidden rig overlays saved; F12 is the authoritative Cycles result.',
    ],
    'rejected_local_tests': [
        'Disabling refractive caustics produced dark eye interiors; both caustic settings restored.',
        'An X-threshold ear exclusion produced a bare temple strip; replaced with native anatomical ear membership.',
        'Saved Rendered shading reopened as Solid; Material Preview persists and is used for startup.',
    ],
    'before': {name: {'path': str((before/name).relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(before/name)}
               for name in ['front.png', 'eye_closeup.png']},
    'after': {name: {'path': str((after/name).relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(after/name)}
              for name in ['front.png', 'eye_closeup.png']},
    'source_sha256': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in
                      [ROOT/'wrapper/groom.py', ROOT/'wrapper/appearance.py', ROOT/'wrapper/materials.py', ROOT/'scripts/build_gnm_look.py']},
    'native_contract': 'Head/eye topology and UVs, eye pivots and 35/40 cm calibration unchanged. No additional third-party asset.',
    'remaining_limits': [
        'This remains an authored CG portrait; native hair counts and numerical tests do not establish reference-level photorealism.',
        'Broad diffuse source information remains limited by 2K full-body source maps; side, oral and ear color continuity still needs acceptance.',
        'Facial hair and lids are static; deformation-aware binding, blinking and expressions remain Milestone 3 work.',
        'Apparent refracted pupil centroids have not been measured; existing labels retain geometric semantics.',
    ],
    'git': 'Uncommitted refinement; no commit created in this pass.',
}
(folder/'groom_refinement.json').write_text(json.dumps(receipt, indent=2)+'\n')
print('GROOM_COMPARISON', folder/'groom_comparison.png')
