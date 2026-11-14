"""Render changing 3D blink frames, then encode a small diagnostic MP4."""
import hashlib
import json
from pathlib import Path
import sys
import time
import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from wrapper import eyes,lids
from render_device import configure


def main():
    folder=ROOT/'work/milestone3'
    source=folder/'IRISX_BLINK_PROTOTYPE.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
    configure()
    scene=bpy.context.scene
    scene.camera=bpy.data.objects['Review_eye_closeup']
    scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.render.resolution_x=512
    scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.use_persistent_data=True
    frames=folder/'blink_frames'
    frames.mkdir(exist_ok=True)
    records=[]
    started=time.perf_counter()
    for frame in range(1,37):
        scene.frame_set(frame)
        eyes.reset()
        path=frames/f'frame_{frame:03d}.png'
        scene.render.filepath=str(path)
        bpy.ops.render.render(write_still=True)
        records.append({'frame':frame,'time_s':(frame-1)/24,**lids.state(),
                        'image':str(path.relative_to(folder)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        print('BLINK_FRAME',frame,flush=True)
    # VSE encodes the actual sequential renders without held pose cards.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene.render.resolution_x=512
    scene.render.resolution_y=512
    scene.render.resolution_percentage=100
    scene.render.fps=24
    scene.render.image_settings.media_type='VIDEO'
    scene.render.image_settings.file_format='FFMPEG'
    scene.render.ffmpeg.format='MPEG4'
    scene.render.ffmpeg.codec='H264'
    scene.render.ffmpeg.constant_rate_factor='HIGH'
    scene.render.ffmpeg.audio_codec='NONE'
    scene.render.filepath=str(folder/'blink_preview.mp4')
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    editor=scene.sequence_editor_create()
    strip=editor.strips.new_image('Actual 3D blink',filepath=str(frames/'frame_001.png'),channel=1,frame_start=1)
    for frame in range(2,37):strip.elements.append(f'frame_{frame:03d}.png')
    scene.frame_start=1
    scene.frame_end=36
    bpy.ops.render.render(animation=True)
    report={'scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fps':24,'frame_count':36,'duration_s':1.5,
            'resolution':[512,512],'cycles_samples':32,'frames':records,'runtime_s':time.perf_counter()-started,
            'video_sha256':hashlib.sha256((folder/'blink_preview.mp4').read_bytes()).hexdigest(),
            'scope':'Small Cycles blink diagnostic. Not one of the three final expression-mode videos.'}
    (folder/'blink_preview.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BLINK_PREVIEW_COMPLETE',flush=True)


if __name__=='__main__':main()
