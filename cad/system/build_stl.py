#!/usr/bin/env python3
"""Integrated CDX-3R, all layers share the same shoulder, elbow and pack datums."""
from __future__ import annotations
import sys
import importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent;CAD=ROOT.parent
sys.path.insert(0,str(CAD));sys.path.insert(0,str(CAD/'elbow'))
import build_stl as elbow_mod
from build_stl import Mesh, annulus, box, cylinder
from design import UA, FA, ELBOW, MID_Z, R_PACK, T_PACK, place_elbow, pack_point, public_dir
from surfaces import plate, tube, curve, ellipsoid


def _load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


sh=_load('shoulder_mod',CAD/'shoulder/build_stl.py')
pk=_load('backpack_mod',CAD/'backpack/build_stl.py')
ar=_load('armor_mod',CAD/'armor/build_stl.py')
OUT=ROOT/'stl';PUB=public_dir('system')
FOREARM_DIR=np.array([1.,0.,0.])
PALETTE={'human':'#b8aca0','saddle':'#384956','yoke':'#647684','beam':'#6e8393','belt':'#2b353d',
'park':'#536775','strap':'#34414a','housing':'#15212a','cable_el':'#334956','cable_flex':'#334956',
'cable_abd':'#334956','ferrule':'#a5b3bd'}


def human():
    m=ellipsoid([96,178,155],[-15,-110,MID_Z+20],3)
    m.add(ellipsoid([43,38,44],[-5,80,MID_Z+10]))
    m.add(ellipsoid([68,84,70],[-5,164,MID_Z+10],3))
    m.add(ellipsoid([36,UA/2-8,36],[0,-UA/2,0],3))
    m.add(ellipsoid([FA/2-5,31,32],[FA/2,-UA,0],3))
    return m


def saddle():
    return plate([[-62,-58],[-38,-72],[25,-45],[30,20],[-10,30],[-55,5]],0,12,2).rx(90).move(0,35,0)


def yoke():
    m=Mesh()
    for z in [-35,35]:
        m.add(tube(curve([pack_point([z,145,10]),[-122,84,-110],[-68,68,-45],[-26,35,15]],35),7,12))
    return m


def ua_beam():
    return tube([[0,0,sh.Z_FLEX],[0,-UA+25,elbow_mod.Z_PLATE]],7,12)


def hip_belt():
    # Oval belt follows the mannequin's torso, rather than a horizontal disc.
    belt=annulus(1,.89,22,n=80)
    return belt.transformed(np.diag([104,161,1])).rx(90).move(-15,-263,MID_Z+20)


def park_rest():
    mid=ELBOW+FOREARM_DIR*122
    m=box(-25,25,-8,0,-38,38)
    m.add(box(-25,25,0,15,-38,-32));m.add(box(-25,25,0,15,32,38))
    m=m.move(mid[0],mid[1]-36,mid[2])
    m.add(tube(curve([[35,-263,-65],[90,-295,-42],[122,-UA-41,0]],20),6,10))
    return m


def straps():
    m=Mesh()
    for z in [-95,25]:
        m.add(tube(curve([[-150,56,MID_Z+z],[-40,68,MID_Z+z],[65,6,MID_Z+z],[65,-180,MID_Z+z]],40),8,10))
    return m


def housing_paths():
    routes=[]
    for i,x in enumerate([-50,-30,-10,10,30,50]):
        start=pack_point([x,160,39])
        path=[start,[-157,106,-130+i*9],[-103-i*2,104,2+i*8],[-78-i*2,65,64+i*3]]
        if i<2:
            path += [[-62-i*9,-40,88],[-52-i*8,-140,87],[-37,-UA+88,80],[18 if i==0 else -18,-UA+58,elbow_mod.Z_PLATE+10]]
        elif i<4:path += [[-52,58,86],[20 if i==2 else -20,55,sh.Z_FLEX-8]]
        else:path += [[sh.X_ABD-24,28 if i==4 else -28,50],[sh.X_ABD+10,50 if i==4 else -50,20]]
        routes.append(curve(path,70))
    return routes


def housing():
    m=Mesh()
    for path in housing_paths():m.add(tube(path,3.3,10))
    return m


def ferrules():
    m=Mesh()
    for path in housing_paths():
        for endpoint,neighbor in [(path[0],path[1]),(path[-1],path[-2])]:
            tangent=neighbor-endpoint;tangent/=np.linalg.norm(tangent)
            m.add(tube([endpoint,endpoint+tangent*9],4.8,12))
    return m


def cable_collars():
    m=Mesh()
    # Short segmented sleeves make the shoulder bundles legible in close-up.
    for path in housing_paths():
        for index in range(3,len(path)-3,5):
            m.add(tube(path[index:index+2],3.9,10))
    return m


def cables():return {}


def elbow_layers():
    return [(f'el_{name}',place_elbow(mesh),color) for name,mesh,color in elbow_mod.assembly_layers(False)
            if name not in {'arm','housing'}]


def shoulder_layers():
    layers=[]
    for name,mesh,color in sh.assembly_layers(False):
        # Onward cable routes are replaced by the continuous system harness.
        if name in {'arm','torso','housing','cable_elbow'}:continue
        if name in {'cuff','flex_yoke'}:mesh=mesh.rz(-90)
        layers.append((f'sh_{name}',mesh,color))
    return layers


def pack_layers():
    return [(f'pk_{name}',mesh.transformed(R_PACK,T_PACK),color) for name,mesh,color in pk.assembly_layers(False)
            if name not in {'torso','strap'}]


def armor_layers():
    return [(f'ar_{name}',mesh,color) for name,mesh,color in ar.shell_layers()]


def assembly_layers(with_human=True):
    layers=[('human',human(),PALETTE['human'])] if with_human else []
    for name,fn in [('saddle',saddle),('yoke',yoke),('beam',ua_beam),('belt',hip_belt),('park',park_rest),
                    ('strap',straps),('ferrule',ferrules),('housing',housing)]:
        layers.append((name,fn(),PALETTE[name]))
    layers.append(('cable_collars',cable_collars(),'#536471'))
    return layers+pack_layers()+shoulder_layers()+elbow_layers()+armor_layers()


def main():
    from export import export_kit
    parts={'print_saddle':saddle(),'print_yoke':yoke(),'print_ua_beam':ua_beam(),
           'print_hip_belt':hip_belt(),'print_park_rest':park_rest()}
    export_kit('system',assembly_layers,parts,PALETTE)


if __name__=='__main__':main()
