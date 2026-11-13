"""Compose material comparison evidence from the actual five GNM look renders."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'tests/milestone2'
canvas = Image.new('RGB', (1800, 780), '#101820')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
draw.text((22, 16), 'VITChennai_IrisX | Native GNM texture looks | Milestone 2 work in progress', font=font, fill='#eef6f7')
for i in range(5):
    look = f'look_{i+1:02d}'
    manifest = json.loads((ROOT/'textures'/look/'manifest.json').read_text())
    x = i*360+10
    draw.text((x+6, 64), look+' | '+manifest['label'].split(' / ')[0], font=small, fill='#89dccb')
    face = Image.open(folder/look/'front.png').convert('RGB').resize((340, 340), Image.Resampling.LANCZOS)
    canvas.paste(face, (x, 96))
    macro = Image.open(folder/look/'macro.png').convert('RGB').crop((0, 190, 1024, 730))
    macro = macro.resize((340, 179), Image.Resampling.LANCZOS)
    canvas.paste(macro, (x, 460))
    draw.text((x+6, 655), '4K skin | separate 2K eye maps', font=small, fill='#c0d0d7')
draw.text((22, 708), 'Actual Cycles renders under common lighting. Source maps transferred to unchanged native UVs; fine PBR/iris detail authored separately.', font=small, fill='#b7c9d1')
draw.text((22, 740), 'Visual refinement and full-head seam acceptance remain pending. Static appearance only; eyelid animation is Milestone 3.', font=small, fill='#b7c9d1')
canvas.save(folder/'contact_sheet.png')
print('GNM_MATERIAL_SHEET', folder/'contact_sheet.png')
