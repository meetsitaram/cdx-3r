"""Rigid joint ownership and flexible display routing for the integrated CAD.

Angles are inspection ranges, not validated mechanical travel. Flexible meshes
use geometric skinning only; this is not a cable tension or bend-radius solver.
"""
import numpy as np
from design import UA, FA, PARAMS, SHOULDER_Z, SHOULDER_ABD_X
from build_stl import Z_SHEAVE


def motion_manifest(layers, paths):
    joints=[
        dict(id='shoulder',parent='base',key='shoulderAbduction',label='Shoulder abduction',
             origin=[SHOULDER_ABD_X,0,0],axis=[-1,0,0],rest=0,min=0,max=60),
        dict(id='upper',parent='shoulder',key='shoulderFlexion',label='Shoulder flexion',
             origin=[0,0,SHOULDER_Z],axis=[0,0,1],rest=0,min=0,max=90),
        dict(id='forearm',parent='upper',key='elbowFlexion',label='Elbow flexion',
             origin=[0,-UA,Z_SHEAVE],axis=[0,0,1],rest=90,
             min=PARAMS['human']['elbow_rom_ext_deg'],max=PARAMS['human']['elbow_rom_flex_deg']),
    ]
    bindings={}
    for name,_,_ in layers:
        link='base'
        if name in {'beam','ghost_upper'}:link='upper'
        elif name=='ghost_forearm':link='forearm'
        elif name.startswith('el_'):
            link='forearm' if name in {'el_cuff_forearm','el_distal','el_sheave','el_clamp'} else 'upper'
        elif name.startswith('sh_'):
            part=name[3:]
            if part in {'cuff','flex_yoke','sheave_flex','clamp_flex'}:link='upper'
            elif part in {'abd_yoke','sheave_abd','screw_flex','bearing_flex','cups_flex','anchor_flex','cable_flex','stop','clamp_abd'}:link='shoulder'
        elif name.startswith('ar_'):
            part=name[3:]
            if part.startswith('ua'):link='upper'
            elif part.startswith(('fa','vent_','wrist')):link='forearm'
            elif part.startswith('deltoid') or part in {'bezel','shoulder_trim','shoulder_fasteners','shoulder_led'}:link='shoulder'
            elif part in {'elbow_bezel','elbow_led'}:link='upper'
        elif name.startswith('ferrule_') and name.endswith('_end'):
            i=int(name.split('_')[1]);link='upper' if i<2 else 'shoulder' if i<4 else 'base'
        bindings[name]=link
    flexible={}
    for i,path in enumerate(paths):
        target='upper' if i<2 else 'shoulder' if i<4 else 'base'
        # Nearest rest-route sample determines the skin weight, so collars and
        # housing share exactly the same deformation. End fittings stay rigid.
        stations=[]
        for t in np.linspace(0,1,len(path)):
            u=float(np.clip((t-.18)/.62,0,1));u=u*u*(3-2*u)
            stations.append(u)
        for name in [f'housing_{i}',f'collars_{i}']:
            flexible[name]=dict(fromLink='base',toLink=target,path=np.asarray(path).tolist(),weights=stations)
    # Exposed cable curves stay anchored to their idlers while their final
    # portions follow the driven sheave. Shape is an inspection approximation.
    for name,parent,child,axis,low,high in [
        ('el_cable_flex','upper','forearm',1,-UA+42,-UA+5),
        ('el_cable_ext','upper','forearm',1,-UA+42,-UA+5),
        ('sh_cable_flex','shoulder','upper',1,38,5),
        ('sh_cable_abd','base','shoulder',1,36,0),
    ]:
        flexible[name]=dict(fromLink=parent,toLink=child,coordinate=axis,start=low,end=high)
    return dict(version=1,joints=joints,bindings=bindings,flexible=flexible,
                landmarks={'shoulder':[0,0,0],'elbow':[0,-UA,0],'wrist':[FA,-UA,0]},
                rest={'shoulderAbduction':0,'shoulderFlexion':0,'elbowFlexion':90},
                note='Inspection kinematics; travel and cable routing are not mechanically validated.')


def transforms(motion,pose):
    """Rest-world to posed-world matrices, matching the viewer's nested rig."""
    result={'base':np.eye(4)}
    for joint in motion['joints']:
        value=float(pose.get(joint['key'],joint['rest']))
        if not np.isfinite(value):value=joint['rest']
        angle=np.radians(np.clip(value,joint['min'],joint['max'])-joint['rest'])
        a=np.array(joint['axis'],float);a/=np.linalg.norm(a)
        cross=np.array([[0,-a[2],a[1]],[a[2],0,-a[0]],[-a[1],a[0],0]])
        rotation=np.eye(3)+np.sin(angle)*cross+(1-np.cos(angle))*(cross@cross)
        local=np.eye(4);local[:3,:3]=rotation
        origin=np.array(joint['origin']);local[:3,3]=origin-rotation@origin
        result[joint['id']]=result[joint['parent']]@local
    return result


def skin_weights(spec,points):
    points=np.asarray(points)
    if 'path' in spec:
        path=np.array(spec['path']);weights=np.array(spec['weights'])
        # Process in chunks to bound memory for full triangle arrays.
        out=[]
        for chunk in np.array_split(points,max(1,len(points)//2000)):
            out.extend(weights[np.argmin(np.sum((chunk[:,None]-path[None])**2,axis=2),axis=1)])
        return np.array(out)
    w=np.clip((points[:,spec['coordinate']]-spec['start'])/(spec['end']-spec['start']),0,1)
    return w*w*(3-2*w)


def pose_vertices(name,points,motion,pose):
    matrices=transforms(motion,pose);points=np.asarray(points)
    def apply(link):
        m=matrices[link];return points@m[:3,:3].T+m[:3,3]
    if name in motion['flexible']:
        spec=motion['flexible'][name];w=skin_weights(spec,points)[:,None]
        return apply(spec['fromLink'])*(1-w)+apply(spec['toLink'])*w
    return apply(motion['bindings'][name])
