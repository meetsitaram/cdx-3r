from pathlib import Path
import sys, importlib.util, json, struct
import numpy as np
import trimesh
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'cad'))
sys.path.insert(0,str(ROOT/'cad/elbow'))
from surfaces import normalize
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
mods={name:load(name+'_audit',ROOT/f'cad/{name}/build_stl.py') for name in ['elbow','shoulder','backpack','armor','system']}
def read(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 dt=np.dtype([('n','<f4',(3,)),('t','<f4',(3,3)),('a','<u2')])
 return np.frombuffer(data,dtype=dt,count=n,offset=84)['t'].copy()
def stats(t):
 m=trimesh.Trimesh(vertices=t.reshape(-1,3),faces=np.arange(t.size//3).reshape(-1,3),process=True)
 _,counts=np.unique(m.edges_sorted,axis=0,return_counts=True)
 return {'triangles':len(t),'bounds_mm':m.bounds.round(2).tolist(),'extents_mm':m.extents.round(2).tolist(),'watertight':bool(m.is_watertight),'winding_consistent':bool(m.is_winding_consistent),'boundary_edges':int((counts==1).sum()),'nonmanifold_edges':int((counts>2).sum())}
report={'layer_comparison':{},'armor_prints':{},'pack_parts':{}}
for name,mod in mods.items():
 layers=mod.assembly_layers(True)
 same=[];different=[];missing=[]
 for layer,mesh,color in layers:
  src=np.asarray(normalize(mesh).tris,dtype=np.float32)
  path=ROOT/f'public/cad/{name}/asm/{layer}.stl'
  if not path.exists():missing.append(layer);continue
  data=read(path)
  if src.shape==data.shape and np.array_equal(src,data):same.append(layer)
  else:different.append({'layer':layer,'stored_triangles':len(data),'source_triangles':len(src),'stored_extents':np.ptp(data.reshape(-1,3),axis=0).round(1).tolist(),'source_extents':np.ptp(src.reshape(-1,3),axis=0).round(1).tolist()})
 report['layer_comparison'][name]={'matching':same,'different':different,'missing':missing}
for name,mesh in mods['armor'].print_parts().items():
 report['armor_prints'][name]=stats(np.asarray(normalize(mesh).tris))
for name in ['frame','battery','winch','drives','winch_at']:
 mesh=getattr(mods['backpack'],name)(0) if name=='winch_at' else getattr(mods['backpack'],name)()
 report['pack_parts'][name]=stats(np.asarray(normalize(mesh).tris))
# Compare repository and served meshes by content
for kit in mods:
 local=ROOT/f'cad/{kit}/stl';pub=ROOT/f'public/cad/{kit}'
 shared=[p for p in local.rglob('*.stl') if (pub/p.relative_to(local)).exists()]
 changed=[str(p.relative_to(local)) for p in shared if p.read_bytes()!=(pub/p.relative_to(local)).read_bytes()]
 report['layer_comparison'][kit]['local_vs_public_different']=changed
Path(__file__).with_name('audit-current.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
