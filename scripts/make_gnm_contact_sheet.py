"""Compose a labeled diagnostic contact sheet from actual GNM draft renders."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT/'tests/milestone1'
poses = json.loads((folder/'direction_metadata.json').read_text())
canvas = Image.new('RGB', (1600, 600), '#101821')
draw = ImageDraw.Draw(canvas)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
draw.text((24, 14), 'VITChennai_IrisX | GNM native-UV baseline | Draft materials', font=font, fill='#e8f2f5')
for i, name in enumerate(('reset', 'left', 'right', 'up', 'down')):
    im = Image.open(folder/(name+'.png')).convert('RGB')
    scale = im.width/1024
    left, right = [poses[name]['pupil_center_2D_'+side] for side in ('L', 'R')]
    x0 = min(left[0], right[0])-45
    x1 = max(left[0], right[0])+45
    y = (left[1]+right[1])/2
    eyes = im.crop((round(x0*scale), round((y-35)*scale), round(x1*scale), round((y+35)*scale)))
    eyes = eyes.resize((264, round(eyes.height*264/eyes.width)), Image.Resampling.LANCZOS)
    face = im.resize((304, 304), Image.Resampling.LANCZOS)
    x = i*320+8
    draw.text((x+8, 56), name.upper(), font=font, fill='#82dac6')
    canvas.paste(face, (x, 90))
    canvas.paste(eyes, (x+(304-eyes.width)//2, 414))
draw.text((24, 558), 'Actual Cycles renders. UVs, gaze geometry and calibration checked; photoreal skin, brows and eyelid motion remain pending.', font=small, fill='#b0bec8')
canvas.save(folder/'contact_sheet.png')
print('GNM_CONTACT_SHEET', folder/'contact_sheet.png')
