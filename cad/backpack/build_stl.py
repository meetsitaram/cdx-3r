#!/usr/bin/env python3
"""Three transverse winches in separated bays above a compact battery envelope."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from design import PACK, WINCH_ROWS, WINCH_X, WINCH_Z, BATTERY_SIZE, BATTERY_CENTER, public_dir
from surfaces import Mesh, plate, ring, curve, tube, ellipsoid, cylinder, annulus
from build_stl import box, idler_bearing
OUT=ROOT/'stl';PUB=public_dir('backpack')
PALETTE={'torso':'#b2a79a','frame':'#697987','sled':'#536572','battery':'#283c43',
'motor':'#8f9eaa','s1':'#2d5a57','spreader':'#687b88','xt90':'#c4803c','bullet':'#bda071',
'bulkhead':'#8496a5','housing':'#15212a','cable_el':'#465968','cable_flex':'#465968',
'cable_abd':'#465968','strap':'#303b42'}


def frame():
    # Open ladder chassis: no front wall hiding the motors or crossing the
    # armor windows. Backplane and rails meet without overlapping volumes.
    m=plate([[-120,-240],[120,-240],[125,-218],[125,132],[106,152],[-106,152],[-125,132],[-125,-218]],0,6,1)
    for x in [-122,122]:
        m.add(box(x-3,x+3,-220,126,6,113))
    for y in [-132,-35,55,145]:
        m.add(box(-119,119,y-3,y+3,6,21))
    return m


def sled():
    x,y,z=BATTERY_CENTER;w,h,d=BATTERY_SIZE
    m=box(-w/2-3,w/2+3,y-h/2-5,y+h/2+5,z-d/2-5,z-d/2-2)
    for sign in [-1,1]:m.add(box(sign*(w/2+3)-2,sign*(w/2+3)+2,y-h/2-5,y+h/2+5,z-d/2-2,z+d/2))
    return m


def battery():
    x,y,z=BATTERY_CENTER;w,h,d=BATTERY_SIZE
    return box(x-w/2,x+w/2,y-h/2,y+h/2,z-d/2,z+d/2)


def motor() -> Mesh:
    m = cylinder(37.5, 74)
    m.add(cylinder(5.0, 28, z0=37))  # 10 mm shaft
    m.add(cylinder(4.0, 16, z0=-37 - 16))  # rear 8 mm for encoder
    return m


def planetary() -> Mesh:
    m = box(-30, 30, -30, 30, -36, 36)
    m.add(cylinder(7.0, 22, z0=36))
    return m


def drum() -> Mesh:
    return annulus(22, 7.2, 18)


def encoder() -> Mesh:
    return cylinder(15, 18)


def winch() -> Mesh:
    """One axis: D6374 + 10:1 + drum + 608s. Local: motor along +Z."""
    m = motor()
    m.add(planetary().move(0, 0, 74))
    m.add(drum().move(0, 0, 74 + 36 + 16))
    m.add(idler_bearing().move(0, 0, 74 + 36 + 8))
    m.add(idler_bearing().move(0, 0, 74 + 36 + 24))
    m.add(encoder().move(0, 0, -74 / 2 - 20))
    return m


def winch_at(y):
    return winch().ry(90).move(WINCH_X,y,WINCH_Z)


def s1():
    # Existing board envelope; positioned in the shallow backplane layer.
    return box(-40,40,-28,28,0,16)


def drives():
    m=Mesh()
    for y in WINCH_ROWS:m.add(s1().move(0,y,10))
    return m


def spreader():
    m=Mesh()
    for y in WINCH_ROWS:m.add(box(-43,43,y-30,y+30,6,9))
    return m


def xt90():
    return box(-10,10,-8,8,0,18)


def bullets():
    m=Mesh()
    for y in WINCH_ROWS:
        for dy in [-5,5]:m.add(cylinder(2.2,10).ry(90).move(-110,y+dy,69))
    return m


def bulkhead():
    m=box(-65,65,139,148,30,48)
    for x in [-50,-30,-10,10,30,50]:m.add(annulus(5,2.8,10).rx(90).move(x,153,39))
    return m


def housing():
    m=Mesh()
    for index,y in enumerate(WINCH_ROWS):
        for side in [-1,1]:
            x=-50+index*40+(side+1)*10
            pts=[[104,y+side*18,88],[112,y+side*22,92],[112,132,92],[x,148,39],[x,160,39]]
            m.add(tube(curve(pts,32),2.7,8))
    return m


def cables():
    # Cable cores within the continuous housings; the system owns the onward
    # runs over the shoulder so a second floating harness is not assembled.
    return {}


def straps():
    m=Mesh()
    for x in [-82,82]:m.add(box(x-10,x+10,-200,120,-8,-2))
    return m


def ghost_torso():
    return ellipsoid([150,205,87],[0,-25,-92])


def assembly_layers(with_body=True):
    layers=[('torso',ghost_torso(),PALETTE['torso'])] if with_body else []
    functions={'frame':frame,'sled':sled,'battery':battery,'s1':drives,'spreader':spreader,
               'bulkhead':bulkhead,'housing':housing,'strap':straps,'bullet':bullets}
    for name,fn in functions.items():layers.append((name,fn(),PALETTE[name]))
    motors=Mesh()
    for y in WINCH_ROWS:motors.add(winch_at(y))
    layers.append(('motor',motors,PALETTE['motor']))
    layers.append(('xt90',xt90().move(-35,-231,51).add(xt90().move(35,-231,51)),PALETTE['xt90']))
    return layers


def main():
    from export import export_kit
    parts={'print_frame':frame(),'print_sled':sled(),'print_drum':drum(),'print_bulkhead':bulkhead(),
           'ref_battery_DO_NOT_PRINT':battery(),'ref_motor_DO_NOT_PRINT':motor(),
           'ref_planetary_DO_NOT_PRINT':planetary(),'ref_s1_DO_NOT_PRINT':s1()}
    export_kit('backpack',assembly_layers,parts,PALETTE)


if __name__=='__main__':main()
