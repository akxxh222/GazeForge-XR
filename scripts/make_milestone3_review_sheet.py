"""Arrange checksum-verified actual M3 renders for visual review."""
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'work/milestone3/final'
output=ROOT/'tests/milestone3/final'
receipt=json.loads((folder/'render_receipt.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(folder/'IRISX_MILESTONE3.blend')==receipt['scene_sha256']
views={v['view']:v for v in receipt['views']}
for filename,labels in [
    ('uv_sheet.png',[('uv_open','Open | native UV'),('uv_half','Half | native UV'),('uv_closed','Closed | native UV')]),
    ('pose_sheet.png',[('up_open','Up | macro'),('up_half','Up / half | single eye'),('up_closed','Up / closed | single eye'),
                       ('down_open','Down | macro'),('down_half','Down / half | single eye'),('down_closed','Down / closed | single eye')])]:
    sheet=Image.new('RGB',(1536,544*((len(labels)+2)//3)),(20,23,29));draw=ImageDraw.Draw(sheet)
    for index,(name,label) in enumerate(labels):
        path=folder/(name+'.png');assert sha(path)==views[name]['sha256']
        x,y=(index%3)*512,(index//3)*544
        draw.text((x+12,y+9),label,fill='white')
        with Image.open(path) as image:sheet.paste(image.convert('RGB').resize((512,512),Image.Resampling.LANCZOS),(x,y+32))
    sheet.save(output/filename)
print('M3_REVIEW_SHEETS',receipt['scene_sha256'])
