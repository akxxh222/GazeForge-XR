"""Encode a 90-second silent overview using actual renders and capture clips."""
import hashlib
import json
from pathlib import Path
import sys

import bpy

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report=json.loads((ROOT/'tests/capture.json').read_text())
    if report['status']!='PASS':raise ValueError('Complete verified captures before making the overview')
    original_scene=bpy.context.scene
    scene=bpy.data.scenes.new('IrisX | actual-render overview')
    bpy.context.window.scene=scene
    scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
    scene.render.fps=24;scene.render.fps_base=1;scene.frame_start=1;scene.frame_end=2160
    scene.render.image_settings.media_type='VIDEO';scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.audio_codec='NONE';scene.render.ffmpeg.constant_rate_factor='HIGH'
    scene.render.filepath=str(ROOT/'demo/overview.mp4')
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    editor=scene.sequence_editor_create();chapters=[]
    def text(content,start,end,y,size=30,channel=10):
        strip=editor.strips.new_effect('Caption',type='TEXT',channel=channel,frame_start=start,length=end-start)
        strip.text=content;strip.font_size=size;strip.color=(1,1,1,1)
        strip.location=(.04,y);strip.alignment_x='LEFT';strip.anchor_x='LEFT';strip.anchor_y='CENTER'
        strip.use_shadow=True
    def still(path,start,end):
        strip=editor.strips.new_image(path.stem,filepath=str(path),channel=1,frame_start=start)
        strip.frame_final_duration=end-start
        strip.transform.scale_x=strip.transform.scale_y=.68
        strip.transform.offset_x=265
    def chapter(title,body,file,start_s,end_s,movie=False):
        start=round(start_s*24)+1;end=round(end_s*24)+1
        if movie:
            strip=editor.strips.new_movie(title,filepath=str(file),channel=1,frame_start=start)
            strip.frame_final_duration=end-start
            strip.transform.scale_x=strip.transform.scale_y=.95
            strip.transform.offset_x=265
        else:still(file,start,end)
        text(title,start,end,.81,38)
        for index,line in enumerate(body):text(line,start,end,.69-index*.065,25,11+index)
        text('VITChennai_IrisX',start,end,.055,22,20)
        chapters.append({'title':title,'start_s':start_s,'end_s':end_s,
                         'source':file.relative_to(ROOT).as_posix(),'sha256':sha(file),'captions':body})
    preview=ROOT/'previews'
    chapter('GazeForge XR',['Synthetic gaze data','Samsung XR Track 01','Actual Blender renders'],preview/'look_01_front.png',0,6)
    chapter('Metric calibration',['40 cm fixed camera','35 cm fixation plane','Target offsets within 5 cm','Shared target, separate pivots'],preview/'look_01_eyes.png',6,18)
    chapter('Python controls',['eyes.move(h, v)','eyes.reset()','eyes.render()','Saved editable eye/lid actions'],preview/'look_02_eyes.png',18,30)
    for mode,start,label in [('left',30,'Left'),('right',36,'Right'),('generate_motion',42,'Generate Motion')]:
        chapter(label,['144 actual rendered frames','24 fps, six seconds','720 px, Cycles 96 samples'],ROOT/'videos'/(mode+'.mp4'),start,start+6,True)
    for number in range(1,6):
        start=48+(number-1)*3
        chapter(f'Native look {number:02d}',['Original GNM UVs','Portable skin and eye maps'],preview/f'look_{number:02d}_front.png',start,start+3)
    metadata=json.loads((ROOT/'metadata.json').read_text())
    for index,row in enumerate(metadata['frames']):
        start=63+index*1.5
        chapter(f'Clockwise sample {index:02d}',[f"h = {row['input']['h']:+.3f}",f"v = {row['input']['v']:+.3f}",'1024-square PNG','Geometric projection labels'],ROOT/row['image'],start,start+1.5)
    chapter('Results and limits',[f"{report['passed']:,} capture checks pass",'Five native texture looks','Scan detail is transferred','Motion is authored','Setup and credits in README'],preview/'look_04_eyes.png',78,90)
    (ROOT/'demo').mkdir(exist_ok=True)
    (ROOT/'tests/receipts').mkdir(parents=True,exist_ok=True)
    bpy.ops.render.render(animation=True)
    receipt={'schema':'IrisX actual-render overview 1','duration_s':90,'frames':2160,'fps':24,'resolution':[1280,720],
             'file':'overview.mp4','sha256':sha(ROOT/'demo/overview.mp4'),'chapters':chapters,
             'capture_report_sha256':sha(ROOT/'tests/capture.json'),'builder_sha256':sha(Path(__file__)),
             'scope':'Silent captioned overview assembled from existing actual Blender renders and complete rendered clips. It is additional presentation media, not a live screen recording or new physical render sequence.'}
    (ROOT/'tests/receipts/overview.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    scene.sequence_editor_clear()
    bpy.context.window.scene=original_scene
    bpy.data.scenes.remove(scene)
    print('ACTUAL_RENDER_OVERVIEW_COMPLETE',flush=True)


if __name__=='__main__':main()
