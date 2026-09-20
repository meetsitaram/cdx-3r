from pathlib import Path
import json,struct
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
def read(path):
 data=path.read_bytes();n=struct.unpack_from('<I',data,80)[0]
 dt=np.dtype([('n','<f4',(3,)),('t','<f4',(3,3)),('a','<u2')])
 return np.frombuffer(data,dtype=dt,count=n,offset=84)['t'].copy()[:,:,[0,2,1]]
def render(kit,names,out,elev=13,azim=140):
 fig=plt.figure(figsize=(7,7),dpi=130,facecolor='#edf0f2');ax=fig.add_subplot(111,projection='3d')
 pts=[]
 for name in names:
  t=read(ROOT/f'public/cad/{kit}/asm/{name}.stl');pts.append(t.reshape(-1,3))
  if name in ['human','torso']:color='#d5d0c8'
  elif name.startswith('ar_'):color='#45677c' if 'led' not in name else '#42c6ff'
  elif 'sheave' in name or 'motor' in name:color='#989b9e'
  elif 'cable' in name or 'housing' in name:color='#313e48'
  elif 'cuff' in name:color='#b4cbd3'
  elif name in ['frame','pk_frame']:color='#b8c0c6'
  elif name=='battery':color='#658670'
  else:color='#8394a1'
  ax.add_collection3d(Poly3DCollection(t,facecolors=color,edgecolors=color,linewidths=0,shade=True,zsort='average'))
 pts=np.vstack(pts);lo=pts.min(0);hi=pts.max(0);c=(lo+hi)/2;half=max(hi-lo)*.52
 for method,i in [(ax.set_xlim,0),(ax.set_ylim,1),(ax.set_zlim,2)]:method(c[i]-half,c[i]+half)
 ax.set_box_aspect([1,1,1],zoom=1.32);ax.set_proj_type('ortho');ax.view_init(elev=elev,azim=azim);ax.set_axis_off();ax.set_facecolor('#edf0f2');fig.subplots_adjust(0,0,1,1);fig.savefig(OUT/out);plt.close(fig)
names=list(json.loads((ROOT/'public/cad/system/asm/colors.json').read_text())['layers'])
render('system',names,'system-current.png')
render('system',[n for n in names if n in ['beam'] or n.startswith(('sh_','el_','ar_')) and n not in ['ar_pack','ar_lid','ar_led']],'arm-current.png',elev=6,azim=70)
render('backpack',['sled','battery','motor','s1','spreader','bulkhead','housing','xt90'],'pack-current.png',elev=12,azim=74)
print('Rendered three views from the served assembly STLs.')
