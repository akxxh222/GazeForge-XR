"""Lay out actual Blender renders for review; no generated render substitutes."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'work/review/cyberpunk'
canvas=Image.new('RGB',(1920,760),(11,16,22))
draw=ImageDraw.Draw(canvas)
font_path=Path('C:/Windows/Fonts/segoeui.ttf')
font=ImageFont.truetype(str(font_path),25)
small=ImageFont.truetype(str(font_path),19)
draw.text((22,12),'VITChennai_IrisX | Imported hair and iris asset review',font=font,fill=(224,232,240))
for i,(view,label) in enumerate([('front','Fixed 40 cm camera'),('eye','Eye material close-up'),('side','Additional side review')]):
    with Image.open(folder/('asset_'+view+'_test.png')) as src:
        tile=src.convert('RGB').resize((640,640),Image.Resampling.LANCZOS)
    canvas.paste(tile,(640*i,52))
    draw.text((640*i+18,698),label,font=small,fill=(216,227,237))
draw.text((20,731),'Actual 256-sample Cycles renders. Static Milestone 2 candidate; reference-level visual acceptance remains open.',font=small,fill=(155,173,188))
path=folder/'review_sheet.png'
canvas.save(path)
print('ASSET_REVIEW_SHEET',path)
