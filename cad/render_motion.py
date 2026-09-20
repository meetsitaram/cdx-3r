#!/usr/bin/env python3
"""Render motion evidence from the exported meshes and their joint manifest."""
import sys
from pathlib import Path
import tempfile
import shutil
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent/'elbow'))
from render_mesh import render, system_names, PUBLIC

POSES=[('Work pose',0,0,90),('Arm down',0,0,0),('Forward reach',10,65,25),('Side lift',50,0,75)]

def main():
    names=system_names()
    sheet=Image.new('RGB',(1600,970),'#edf0f3')
    draw=ImageDraw.Draw(sheet)
    font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    font=ImageFont.truetype(font_path,22);small=ImageFont.truetype(font_path,16)
    draw.text((28,18),'CDX-3R · articulated CAD · actual exported meshes',fill='#203342',font=font)
    with tempfile.TemporaryDirectory(prefix='cdx-motion-') as tmp:
        for i,(label,a,s,e) in enumerate(POSES):
            pose=dict(shoulderAbduction=a,shoulderFlexion=s,elbowFlexion=e)
            path=Path(tmp)/f'{i}.png'
            render('system',names,path,view=(.65,.23,1),size=(800,400),pose=pose)
            x=(i%2)*800;y=60+(i//2)*435
            sheet.paste(Image.open(path),(x,y))
            draw.text((x+28,y+395),f'{label} · abduction {a}° / shoulder {s}° / elbow {e}°',fill='#203342',font=small)
    draw.text((28,938),'Inspection poses only. Mounts, clearances, and cable tension require mechanical validation.',fill='#4d5e6a',font=small)
    dest=PUBLIC/'system/preview/motion.png';sheet.save(dest)
    shutil.copyfile(dest,Path(__file__).resolve().parent/'system/preview/motion.png')
    print(dest)

if __name__=='__main__':main()


def animate():
    """Small fixed-camera GIF, useful when WebGL is unavailable."""
    import json
    import numpy as np
    import trimesh
    from motion import pose_vertices
    names=system_names()
    manifest=json.loads((PUBLIC/'system/asm/colors.json').read_text())
    # Work -> reach -> side lift -> work, with smooth endpoint interpolation.
    keys=['shoulderAbduction','shoulderFlexion','elbowFlexion']
    targets=[np.array(p[1:],float) for p in [POSES[0],POSES[2],POSES[3],POSES[0]]]
    poses=[]
    for a,b in zip(targets,targets[1:]):
        for t in np.linspace(0,1,8,endpoint=False):
            u=t*t*(3-2*t);poses.append(dict(zip(keys,a*(1-u)+b*u)))
    vertices={n:trimesh.load_mesh(PUBLIC/'system/asm'/f'{n}.stl').vertices for n in names}
    bounds=[]
    for pose in poses:
        for name,points in vertices.items():
            moved=pose_vertices(name,points,manifest['motion'],pose)
            bounds.extend([moved.min(0),moved.max(0)])
    bounds=np.asarray(bounds)
    frames=[]
    with tempfile.TemporaryDirectory(prefix='cdx-animate-') as tmp:
        for i,pose in enumerate(poses):
            dest=Path(tmp)/f'{i}.png'
            render('system',names,dest,view=(.65,.23,1),size=(600,650),pose=pose,frame_vertices=bounds)
            frame=Image.open(dest).convert('RGB')
            d=ImageDraw.Draw(frame)
            font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17)
            d.text((18,15),'CDX-3R · actual CAD joint motion',font=font,fill='#203342')
            d.text((18,620),'Inspection model · clearances not validated',font=font,fill='#4d5e6a')
            frames.append(frame)
    dest=PUBLIC/'system/preview/motion.gif'
    frames[0].save(dest,save_all=True,append_images=frames[1:],duration=180,loop=0,optimize=True)
    shutil.copyfile(dest,Path(__file__).resolve().parent/'system/preview/motion.gif')
    print(dest)


if __name__=='__main__' and '--animate' in sys.argv:animate()
