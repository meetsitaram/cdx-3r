#!/usr/bin/env python3
"""CDX-3R revision B: segmented, tapered armor around shared joint datums."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent))
from design import UA, FA, ELBOW, R_PACK, T_PACK, public_dir, WINCH_ROWS
from surfaces import Mesh, patch, ring, plate, tube, curve, cylinder, annulus

OUT=ROOT/'stl'
PUB=public_dir('armor')
PALETTE={'carbon':'#242d36','carbon_side':'#303c47','metal':'#a5b3c0',
         'dark_metal':'#526477','rubber':'#111922','led':'#64d9f5','fastener':'#d0d9df'}
WALL=3.2


def limb_point(axis,t,angle,offset=0):
    if axis=='ua':
        stations=np.array([[60,69,82],[100,73,85],[165,68,81],[230,59,84],[254,57,80]],float)
    else:
        stations=np.array([[45,58,73],[70,61,73],[120,56,67],[205,44,52],[258,38,44]],float)
        stations[:,0]*=FA/260
    if axis=='ua': stations[:,0]*=UA/290
    r=np.interp(t,stations[:,0],stations[:,1])+offset
    z=np.interp(t,stations[:,0],stations[:,2])+offset
    a=np.radians(angle)
    if axis=='ua': return np.array([r*np.sin(a),-t,z*np.cos(a)])
    return np.array([t,-UA+r*np.sin(a),z*np.cos(a)])


def limb_patch(axis,t0,t1,a0,a1,offset=0,wall=WALL,taper=True,nu=30,nv=18):
    def point(u,v,inner):
        # Clipped corners and a subtle central ridge give the long plates a
        # shaped silhouette. All edge skins are explicitly closed by patch().
        inset=(max(0,1-u/.12)+max(0,1-(1-u)/.12))*7 if taper else 0
        a=(a0+inset)*(1-v)+(a1-inset)*v
        ridge=2.8*np.sin(np.pi*v)**2*np.sin(np.pi*u) if taper else 0
        return limb_point(axis,t0+(t1-t0)*u,a,offset+ridge+(0 if inner else wall))
    return patch(point,nu,nv)


def panel_point(axis,t0,t1,a0,a1,u,v,offset):
    inset=(max(0,1-u/.12)+max(0,1-(1-u)/.12))*7
    angle=(a0+inset)*(1-v)+(a1-inset)*v
    ridge=2.8*np.sin(np.pi*v)**2*np.sin(np.pi*u)
    return limb_point(axis,t0+(t1-t0)*u,angle,offset+ridge)


def panel(axis,t0,t1,a0,a1):
    return patch(lambda u,v,inner:panel_point(axis,t0,t1,a0,a1,u,v,0 if inner else WALL),30,18)


def panel_border(axis,t0,t1,a0,a1):
    m=Mesh()
    # Subpatches of the exact panel surface, including its clipped corners.
    strips=[(.015,.985,0,.075),(.015,.985,.925,1),(.015,.065,.075,.925),(.935,.985,.075,.925)]
    for u0,u1,v0,v1 in strips:
        m.add(patch(lambda u,v,inner:panel_point(axis,t0,t1,a0,a1,u0+(u1-u0)*u,v0+(v1-v0)*v,3.4 if inner else 5.2),
                    26 if u1-u0>.5 else 3,3 if v1-v0<.1 else 18))
    return m


def cap_patch(phi0,phi1,u0=0,u1=1,lift=0,wall=3.5,nu=15,nv=34):
    def point(u,v,inner):
        u=u0+(u1-u0)*u
        ph=np.radians(phi0+(phi1-phi0)*v)
        # Elliptical shoulder outline, circular joint window; same XY origin
        # as the real flexion axle, with 2 mm minimum radial bezel clearance.
        outer=1/np.sqrt((np.cos(ph)/87)**2+(np.sin(ph)/99)**2)
        r=53+(outer-53)*u
        z=96-65*u**2.5+lift-(wall if inner else 0)
        return np.array([r*np.cos(ph),r*np.sin(ph),z])
    return patch(point,nu,nv)


def cap_trim():
    m=Mesh()
    for a,b in [(4,118),(122,238),(242,356)]:
        m.add(cap_patch(a,b,.86,.99,2,1.6,3,30))
        m.add(cap_patch(a,a+4,.10,.86,2,1.6,14,3))
        m.add(cap_patch(b-4,b,.10,.86,2,1.6,14,3))
    return m


def ring_arc(radius,z,a0,a1,center=(0,0,0),r=1.3):
    a=np.radians(np.linspace(a0,a1,70));c=np.asarray(center)
    return tube(np.column_stack([radius*np.cos(a),radius*np.sin(a),np.full(len(a),z)])+c,r,8)


def bolt_at(point,normal):
    n=np.asarray(normal,float);n/=np.linalg.norm(n)
    ref=np.array([0.,1.,0.]) if abs(n[1])<.9 else np.array([1.,0.,0.])
    x=np.cross(ref,n);x/=np.linalg.norm(x);y=np.cross(n,x)
    # Recessed head with visible central bore; reference hardware, not a hole
    # claim in the mounting panel beneath it.
    return ring(3.6,1.5,2.2,n=16).transformed(np.column_stack([x,y,n]),point)


def limb_bolts(axis,t0,t1,a0,a1):
    m=Mesh()
    for t in [t0+12,t1-12]:
        for a in [a0+6,a1-6]:
            p=limb_point(axis,t,a,6)
            n=limb_point(axis,t,a,7)-p
            m.add(bolt_at(p,n))
    return m


def fairing_scapula():
    return plate([[-72,-25],[-48,-42],[40,-30],[68,0],[42,38],[-42,40],[-72,20]],0,5).rx(-65).move(-32,62,-12)


def pack_side(sign):
    # Continuous side rails flare around the winch viewing slots and taper
    # into the lower battery cover. The chassis and cover share pack coords.
    shape=np.array([[92,146],[120,124],[128,70],[128,-166],[108,-234],[80,-236],[96,-180],[96,112]],float)
    if sign<0: shape[:,0]*=-1;shape=shape[::-1]
    return plate(shape,109,7,1.8)


def pack_tub():
    return pack_side(-1)


def pack_lid():
    return plate([[-94,-128],[94,-128],[104,-166],[78,-230],[-78,-230],[-104,-166]],105,9,2)


def pack_layers_local():
    layers=[('pack',pack_side(-1),'carbon'),('pack_right',pack_side(1),'carbon'),('lid',pack_lid(),'carbon')]
    layers.append(('pack_crown',plate([[-100,126],[100,126],[85,148],[-85,148]],105,9,2),'carbon_side'))
    for index,y in enumerate([55,-35,-125]):
        layers.append((f'pack_bridge_{index}',plate([[-100,y-5],[100,y-5],[100,y+5],[-100,y+5]],106,7,1.5),'dark_metal'))
    trim=Mesh();led=Mesh()
    for sign in [-1,1]:
        trim.add(tube(curve([[sign*108,136,120],[sign*124,100,120],[sign*124,-150,120],[sign*95,-228,118]],32),2.4,8))
        led.add(tube(curve([[sign*103,114,119],[sign*112,85,119],[sign*112,-100,119]],24),1.15,8))
    layers += [('pack_trim',trim,'metal'),('pack_led',led,'led')]
    return layers


def shell_layers():
    """All armor in the shared work pose; no duplicate cosmetic mechanisms."""
    items=[];trim=Mesh();screws=Mesh();led=Mesh()
    for axis,start,end in [('ua',68*UA/290,246*UA/290),('fa',51*FA/260,252*FA/260)]:
        for name,a,b,color in [('',-39,39,'carbon'),('_front',43,118,'carbon_side'),('_rear',-118,-43,'carbon_side')]:
            items.append((axis+name,panel(axis,start,end,a,b),color))
            trim.add(panel_border(axis,start,end,a,b));screws.add(limb_bolts(axis,start,end,a,b))
        for angle in [-31,31]:
            v0=(angle-1+39)/78;v1=(angle+1+39)/78
            led.add(patch(lambda u,v,inner:panel_point(axis,start,end,-39,39,.17+.67*u,v0+(v1-v0)*v,3.4 if inner else 4.4),24,3))
    for i,(a,b) in enumerate([(4,118),(122,238),(242,356)]):
        items.append((['deltoid','deltoid_front','deltoid_rear'][i],cap_patch(a,b),'carbon'))
        led.add(ring_arc(58,100,a+5,b-5,r=1.1))
        for ph in [a+10,b-10]:
            angle=np.radians(ph);r=78
            outer=1/np.sqrt((np.cos(angle)/87)**2+(np.sin(angle)/99)**2)
            u=(r-53)/(outer-53);z=96-65*u**2.5
            slope=65*2.5*u**1.5/(outer-53)
            normal=np.array([slope*np.cos(angle),slope*np.sin(angle),1.]);normal/=np.linalg.norm(normal)
            screws.add(bolt_at(np.array([r*np.cos(angle),r*np.sin(angle),z])+normal*1.3,normal))
    items += [('shoulder_trim',cap_trim(),'metal'),('bezel',ring(56,46.5,6,99),'metal'),
              ('scapula',fairing_scapula(),'carbon_side')]
    # Elbow bezel is coaxial with the real elbow sheave. The inner edge clears
    # its 44.45 mm OD radius; there is no second decorative sheave.
    from build_stl import Z_SHEAVE
    items.append(('elbow_bezel',ring(54,47,6,Z_SHEAVE+13).move(*ELBOW),'metal'))
    for a,b in [(12,162),(192,342)]:led.add(ring_arc(55.5,Z_SHEAVE+16,a,b,ELBOW,1.0))
    # A short wrist collar finishes the forearm silhouette without a powered
    # wrist joint. Split vent ribs and two wrap bands echo the reference.
    items.append(('wrist',limb_patch('fa',FA-8,FA+15,-120,120,2,3,False,6,36),'dark_metal'))
    for t in [FA-3,FA+10]:trim.add(limb_patch('fa',t,t+3,-112,112,5.3,1.5,False,3,36))
    for t in np.linspace(FA-62,FA-37,4):
        items.append((f'vent_{round(t)}',limb_patch('fa',t,t+3,52,105,4,2,False,2,12),'dark_metal'))
    items += [('trim',trim,'metal'),('fasteners',screws,'fastener'),('led',led,'led')]
    for name,mesh,color in pack_layers_local():
        items.append((name,mesh.transformed(R_PACK,T_PACK),color))
    return [(name,mesh,PALETTE[color]) for name,mesh,color in items]


def assembly_layers(with_ghost=True):
    layers=shell_layers()
    if with_ghost:
        from surfaces import ellipsoid
        layers=[('ghost_ua',ellipsoid([34,UA/2-12,35],[0,-UA/2,0]),'#b2a79a'),
                ('ghost_fa',ellipsoid([FA/2-10,30,31],[FA/2,-UA,0]),'#b2a79a')]+layers
    return layers


def print_parts():
    # Every primary carbon panel is a separate closed part. Hardware, trim,
    # LEDs and grouping meshes are assembly references, not single prints.
    parts={}
    for name,mesh,_ in shell_layers():
        if name in ['ua','ua_front','ua_rear','fa','fa_front','fa_rear','deltoid','deltoid_front','deltoid_rear','scapula','wrist']:
            parts[f'print_fairing_{name}']=mesh
    for name,mesh,_ in pack_layers_local():
        if name in ['pack','pack_right','lid','pack_crown'] or name.startswith('pack_bridge'):
            label={'pack':'pack_tub','lid':'pack_lid'}.get(name,name)
            parts[f'print_fairing_{label}']=mesh
    parts['print_bezel_deltoid']=ring(56,46.5,6,99)
    return parts


def main():
    from export import export_kit
    export_kit('armor',assembly_layers,print_parts(),PALETTE)


if __name__=='__main__':main()
