#!/usr/bin/env python3
"""Local CPU depth-buffer rendering of the actual STL triangles (no browser).

Orthographic cameras and smooth mesh normals make panel shape and fit readable.
No geometry is fabricated by this renderer. Each pixel resolves the closest
triangle, unlike a painter-order plot of overlapping assembly components.
"""
from pathlib import Path
import json
import os
import sys
import numpy as np
import trimesh
from PIL import Image

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT.parent/'public/cad'


def render(kit,names,destination,view=(.65,.32,1.),size=(1300,1200),clay=False,pose=None,frame_vertices=None):
    manifest=json.loads((PUBLIC/kit/'asm/colors.json').read_text())
    meshes=[]
    for name in names:
        mesh_path=PUBLIC/kit/f'{name}.stl' if name.startswith(('print_','ref_')) else PUBLIC/kit/f'asm/{name}.stl'
        mesh=trimesh.load_mesh(mesh_path,process=True)
        if pose is not None:
            from motion import pose_vertices
            mesh.vertices=pose_vertices(name,mesh.vertices,manifest['motion'],pose)
        meshes.append((name,mesh,manifest['layers'].get(name,'#344653')))
    vertices=np.vstack([m.vertices for _,m,_ in meshes])
    framing=np.asarray(frame_vertices) if frame_vertices is not None else vertices
    center=(framing.min(0)+framing.max(0))/2
    eye=np.array(view,float);eye/=np.linalg.norm(eye)
    right=np.cross([0,1,0],eye);right/=np.linalg.norm(right);up=np.cross(eye,right)
    basis=np.column_stack([right,up,eye])
    projected=(framing-center)@basis
    low,high=projected.min(0),projected.max(0)
    width,height=size;scale=min((width-100)/(high[0]-low[0]),(height-100)/(high[1]-low[1]))
    mid=(low+high)/2
    depth=np.full((height,width),-np.inf,dtype=np.float32)
    bg=np.array([.925,.94,.951],dtype=np.float32)
    pixels=np.tile(bg,(height,width,1))
    key=np.array([-.25,.8,1.]);key/=np.linalg.norm(key)
    fill=np.array([1.,.25,-.4]);fill/=np.linalg.norm(fill)
    half=key+eye;half/=np.linalg.norm(half)
    for name,m,hexcolor in meshes:
        p=(m.vertices-center)@basis
        screen=np.column_stack([(p[:,0]-mid[0])*scale+width/2, height/2-(p[:,1]-mid[1])*scale,p[:,2]])
        # Smooth curved panels, preserve machined edges. Averaging across all
        # adjacent faces would incorrectly make flat sheaves look domed.
        adjacent=m.vertex_faces[m.faces]
        valid=adjacent>=0
        neighbors=m.face_normals[np.maximum(adjacent,0)]
        dot=np.sum(neighbors*m.face_normals[:,None,None,:],axis=-1)
        crease=valid & (dot>np.cos(np.radians(35)))
        normals=np.sum(neighbors*crease[:,:,:,None],axis=2)
        normals/=np.maximum(np.linalg.norm(normals,axis=2)[:,:,None],1e-12)
        color=np.array([int(hexcolor[k:k+2],16) for k in (1,3,5)])/255
        ismetal=any(word in name for word in ['trim','bezel','screw','sheave','fastener','motor','ferrule'])
        led='led' in name
        if clay:color=np.array([.54,.62,.69]);ismetal=False;led=False
        for face_index,face in enumerate(m.faces):
            q=screen[face];n=normals[face_index]
            x0=max(0,int(np.floor(q[:,0].min())));x1=min(width-1,int(np.ceil(q[:,0].max())))
            y0=max(0,int(np.floor(q[:,1].min())));y1=min(height-1,int(np.ceil(q[:,1].max())))
            if x1<x0 or y1<y0:continue
            denom=(q[1,1]-q[2,1])*(q[0,0]-q[2,0])+(q[2,0]-q[1,0])*(q[0,1]-q[2,1])
            if abs(denom)<1e-7:continue
            yy,xx=np.mgrid[y0:y1+1,x0:x1+1];xx=xx+.5;yy=yy+.5
            a=((q[1,1]-q[2,1])*(xx-q[2,0])+(q[2,0]-q[1,0])*(yy-q[2,1]))/denom
            b=((q[2,1]-q[0,1])*(xx-q[2,0])+(q[0,0]-q[2,0])*(yy-q[2,1]))/denom;c=1-a-b
            z=a*q[0,2]+b*q[1,2]+c*q[2,2]
            region=depth[y0:y1+1,x0:x1+1]
            mask=(a>=-1e-5)&(b>=-1e-5)&(c>=-1e-5)&(z>region)
            if not mask.any():continue
            weights=np.column_stack([a[mask],b[mask],c[mask]])
            normal=weights@n;normal/=np.maximum(np.linalg.norm(normal,axis=1)[:,None],1e-12)
            diffuse=.36+.64*np.maximum(normal@key,0)+.16*np.maximum(normal@fill,0)
            specular=np.maximum(normal@half,0)**(55 if ismetal else 35)*(.38 if ismetal else .07)
            shade=color[None,:]*diffuse[:,None]+specular[:,None]
            if led:shade=np.tile(np.minimum(color*1.25,.98),(len(weights),1))
            pixels[y0:y1+1,x0:x1+1][mask]=np.clip(shade,0,1)
            region[mask]=z[mask]
    dest=Path(destination);dest.parent.mkdir(parents=True,exist_ok=True)
    Image.fromarray(np.uint8(pixels*255)).save(dest)
    print(dest,flush=True)


def system_names():return list(json.loads((PUBLIC/'system/asm/colors.json').read_text())['layers'])

def arm_names():
    return [n for n in system_names() if n.startswith(('ar_','el_','sh_')) and not any(x in n for x in ['pack','lid','scapula'])]


if __name__=='__main__':
    render('system',arm_names(),'/tmp/cdx-shell-b/arm-depth.png',view=(.42,.28,1))
