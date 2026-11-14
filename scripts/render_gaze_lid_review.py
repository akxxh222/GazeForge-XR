"""Actual Cycles gaze/lid proof images and a small continuous review clip."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids,expressions
from render_device import configure


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',action='store_true')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    folder=ROOT/'work/milestone3/gaze_lids'
    path=folder/'IRISX_GAZE_LIDS_RIG.blend'
    bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
    configure()
    scene=bpy.context.scene
    scene.render.use_persistent_data=True
    scene.cycles.samples=64
    scene.render.resolution_x=1024
    scene.render.resolution_y=1024
    started=time.perf_counter()
    receipt={'scene_sha256':sha(path),'views':[]}
    shots=[('up_open',0,1,1,.35,'Review_macro'),('down_open',0,-1,1,0,'Review_macro'),
           ('up_half',0,1,.5,.35,'Review_eye_closeup'),('down_half',0,-1,.5,0,'Review_eye_closeup'),
           ('up_closed',0,1,0,.35,'Review_eye_closeup'),('front',0,0,1,0,'RenderCamera')]
    with expressions.manual():
        for label,h,v,opening,brow,camera in shots:
            eyes.move(h,v)
            lids.set_opening(opening)
            expressions.set_brows(brow)
            scene.camera=bpy.data.objects[camera]
            image_path=folder/(label+'.png')
            eyes.render(image_path)
            record={'view':label,'sha256':sha(image_path),'camera':camera,'state':expressions.state()}
            receipt['views'].append(record)
            receipt['runtime_s']=time.perf_counter()-started
            (folder/'render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
            print('GAZE_LID_IMAGE',label,flush=True)
    if not args.video:return
    scene.camera=bpy.data.objects['Review_macro']
    scene.render.resolution_x=384
    scene.render.resolution_y=384
    scene.cycles.samples=24
    frames=folder/'frames'
    frames.mkdir(exist_ok=True)
    records=[]
    for frame in range(1,145):
        scene.frame_set(frame)
        image_path=frames/f'frame_{frame:03d}.png'
        scene.render.filepath=str(image_path)
        bpy.ops.render.render(write_still=True)
        records.append({'frame':frame,'time_s':(frame-1)/24,'sha256':sha(image_path),'state':expressions.state()})
        print('GAZE_LID_FRAME',frame,flush=True)
    encoded=bpy.data.scenes.new('IrisX | review video encode')
    bpy.context.window.scene=encoded
    encoded.render.resolution_x=384
    encoded.render.resolution_y=384
    encoded.render.resolution_percentage=100
    encoded.render.fps=24
    encoded.render.image_settings.media_type='VIDEO'
    encoded.render.image_settings.file_format='FFMPEG'
    encoded.render.ffmpeg.format='MPEG4'
    encoded.render.ffmpeg.codec='H264'
    encoded.render.ffmpeg.audio_codec='NONE'
    encoded.render.ffmpeg.constant_rate_factor='HIGH'
    encoded.render.filepath=str(folder/'gaze_lids_preview.mp4')
    encoded.view_settings.view_transform='Standard'
    encoded.view_settings.look='None'
    editor=encoded.sequence_editor_create()
    strip=editor.strips.new_image('Continuous actual Cycles frames',filepath=str(frames/'frame_001.png'),channel=1,frame_start=1)
    for frame in range(2,145):strip.elements.append(f'frame_{frame:03d}.png')
    encoded.frame_start=1
    encoded.frame_end=144
    bpy.ops.render.render(animation=True)
    receipt['video']={'sha256':sha(folder/'gaze_lids_preview.mp4'),'fps':24,'frames':144,'duration_s':6,
                      'resolution':[384,384],'cycles_samples':24,'poses':records}
    receipt['runtime_s']=time.perf_counter()-started
    (folder/'render_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('GAZE_LID_REVIEW_COMPLETE',receipt['runtime_s'],flush=True)


if __name__=='__main__':main()
