"""One export path for local and served CAD, with deterministic layer manifests."""
from pathlib import Path
import json
import numpy as np
from design import CAD, public_dir
from surfaces import Mesh, normalize


def write_mesh(path,mesh):
    path.parent.mkdir(parents=True,exist_ok=True)
    triangles=np.asarray(mesh.tris,dtype=np.float32)
    records=np.zeros(len(triangles),dtype=[('normal','<f4',(3,)),('vertices','<f4',(3,3)),('attr','<u2')])
    if len(triangles):
        normals=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
        lengths=np.linalg.norm(normals,axis=1)
        normals/=np.maximum(lengths,1e-12)[:,None]
        records['normal']=normals;records['vertices']=triangles
    data=path.stem.encode('ascii')[:80].ljust(80,b'\0')+np.array([len(triangles)],dtype='<u4').tobytes()+records.tobytes()
    path.write_bytes(data)


def export_kit(kit,layers_fn,parts,palette):
    layers=[(name,normalize(mesh),color) for name,mesh,color in layers_fn(True)]
    body={'human','torso','arm'}|{n for n,_,_ in layers if n.startswith('ghost_')}
    full,brace=Mesh(),Mesh()
    for name,mesh,_ in layers:
        full.add(mesh)
        if name not in body:brace.add(mesh)
    parts={name:normalize(mesh) for name,mesh in parts.items() if not name.startswith('assembly_')}
    parts.update(assembly_worn=full,assembly_preview=brace)
    manifest={'revision':'shells-b','palette':palette,'layers':{n:c for n,_,c in layers},
              'views':{'worn':[n for n,_,_ in layers], 'brace':[n for n,_,_ in layers if n not in body]},
              'ghosts':sorted(body & {n for n,_,_ in layers})}
    local=CAD/kit/'stl';served=public_dir(kit)
    for dest in [local,served]:
        asm=dest/'asm';asm.mkdir(parents=True,exist_ok=True)
        # Only remove obsolete generated layers listed in the previous manifest.
        old=json.loads((asm/'colors.json').read_text())['layers'] if (asm/'colors.json').exists() else {}
        for stale in set(old)-set(manifest['layers']):
            (asm/f'{stale}.stl').unlink(missing_ok=True)
        for name,mesh in parts.items():write_mesh(dest/f'{name}.stl',mesh)
        for name,mesh,_ in layers:write_mesh(asm/f'{name}.stl',mesh)
        (asm/'colors.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{kit}: {len(layers)} layers, {len(full.tris):,} triangles; local and public exports synchronized')
