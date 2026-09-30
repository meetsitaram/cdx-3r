"""Pack body + layout parts into one self-contained three.js viewer (out/layout/viewer.html)."""
from pathlib import Path
import base64, json
import numpy as np
import trimesh

LAY = Path(__file__).resolve().parent.parent / 'out' / 'layout'
info = json.load(open(LAY / 'layout.json'))
COL = {'body_torso': '#e8c9a8', 'body_arm': '#e8c9a8', 'back_plate': '#5b6770', 'hip_belt': '#3a3f44',
       'R_shoulder_rest': '#d4a017', 'L_shoulder_pad': '#8a7a4a', 'pack': '#4a5560', 'PVC_pipes': '#e9eef2',
       'frame_pipes': '#e9eef2', 'frame_nodes': '#647684', 'abduction_mount_block': '#647684', 'rest_struts': '#b8860b',
       'webbing': '#2b2f33', 'buckles': '#0d0d0d'}
scene = trimesh.Scene()
names = []
colmap = {}
for f in sorted(LAY.glob('*.stl')):
    m = trimesh.load(f, force='mesh')
    lim = 40000 if f.stem.startswith('body') else 8000
    if len(m.faces) > lim:
        m = m.simplify_quadric_decimation(face_count=lim)
    # three.js is Y-up like our world: X fwd, Y up, Z right -> keep, units mm -> m
    m.apply_scale(0.001)
    c = COL.get(f.stem, '#647684' if any(k in f.stem for k in ('hub', 'yoke', 'strut', 'bracket', 'UA')) else '#8fa3b3')
    rgb = trimesh.visual.color.hex_to_rgba(c)
    m.visual = trimesh.visual.ColorVisuals(m, face_colors=np.tile(rgb, (len(m.faces), 1)))
    colmap[f.stem] = c
    scene.add_geometry(m, node_name=f.stem, geom_name=f.stem)
    names.append(f.stem)
glb = base64.b64encode(scene.export(file_type='glb')).decode()

rows = []
for k, r in info['clearance'].items():
    if 'arm_min' in r:
        rows.append('<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td>%.1f</td></tr>' % (k, r['arm_min'], r['arm_p5'], r['torso_min']))
    else:
        rows.append('<tr><td>%s</td><td>%.1f</td><td>%.1f</td><td></td></tr>' % (k, r['min'], r['p5']))

html = """<!doctype html><html><head><meta charset="utf-8"><title>Exo on body scan</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#f4f5f7;--panel:#ffffffee;--ink:#1d232a;--mut:#5d6873;--line:#d8dde2}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mut:#9aa6b1;--line:#333c45}}
:root[data-theme="dark"]{--bg:#15191d;--panel:#1f252bee;--ink:#e6eaee;--mut:#9aa6b1;--line:#333c45}
html,body{margin:0;height:100%%;background:var(--bg);color:var(--ink);font:13px/1.4 system-ui,sans-serif;overflow:hidden}
#c{position:fixed;inset:0}
#ui{position:fixed;top:12px;left:12px;max-width:min(360px,calc(100vw - 32px));max-height:calc(100vh - 24px);overflow:auto;
background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
h1{font-size:15px;margin:0 0 4px}p{margin:4px 0;color:var(--mut)}label{display:block;cursor:pointer}
table{border-collapse:collapse;width:100%%;margin-top:6px;font-size:12px}td,th{border-bottom:1px solid var(--line);padding:2px 4px;text-align:right}
td:first-child,th:first-child{text-align:left}details{margin-top:8px}summary{cursor:pointer;font-weight:600}
.views button{margin:2px 2px 0 0;padding:3px 8px;border:1px solid var(--line);background:transparent;color:var(--ink);border-radius:6px;cursor:pointer}
</style></head><body><canvas id="c"></canvas>
<div id="ui"><h1>CDX-3R on the exoarm2 scan</h1>
<p>Layout v2: PVC frame + triangulated shoulder beam, rigid right shoulder rest, camping-pack harness (webbing + buckles). Rest pose: arm %(abd).0f&deg; abducted.</p>
<label>Shoulder abduction <b id="av">%(abd).0f</b>&deg; <input id="abd" type="range" min="%(abd).0f" max="60" step="1" value="%(abd).0f" style="width:100%%"></label>
<label>Shoulder flexion <b id="fv">0</b>&deg; <input id="flx" type="range" min="-20" max="120" step="1" value="0" style="width:100%%"></label>
<p>Hard stops: abduction %(abd).0f-60&deg;, flexion -20..120&deg; (swept clear: torso &ge;15 mm, frame/harness &ge;6 mm).</p>
<div class="views"><button data-v="front">Front</button><button data-v="right">Right</button><button data-v="back">Back</button><button data-v="top">Top</button><button data-v="iso">Iso</button></div>
<label>Body opacity <input id="op" type="range" min="0" max="1" step="0.05" value="0.85"></label>
<details open><summary>Parts</summary><div id="parts"></div></details>
<details><summary>Clearance (mm)</summary><table><tr><th>part</th><th>min</th><th>p5</th><th>torso</th></tr>%(rows)s</table>
<p>Arm parts: gap to the (posed) scanned arm, and to the torso. Others: gap to the body. Negative = overlap. Scan noise is about 3-5 mm.</p></details>
</div>
<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const COLS=%(cols)s;
const cv=document.getElementById('c'), r=new THREE.WebGLRenderer({canvas:cv,antialias:true,alpha:true});
r.setPixelRatio(devicePixelRatio);
const sc=new THREE.Scene(), cam=new THREE.PerspectiveCamera(35,1,0.01,20);
sc.add(new THREE.HemisphereLight(0xffffff,0x667788,1.6)); const dl=new THREE.DirectionalLight(0xffffff,1.6); dl.position.set(2,3,1.5); sc.add(dl);
const ctl=new OrbitControls(cam,cv); ctl.target.set(0,1.25,0); ctl.enableDamping=true;
const V={front:[2.2,1.3,0],right:[0,1.3,2.2],back:[-2.2,1.3,0],top:[0.01,3.5,0],iso:[1.5,1.8,1.6]};
function view(k){cam.position.set(...V[k]);ctl.target.set(0,1.2,0);ctl.update();}
document.querySelectorAll('.views button').forEach(b=>b.onclick=()=>view(b.dataset.v)); view('iso');
function size(){const w=innerWidth,h=innerHeight;r.setSize(w,h,false);cam.aspect=w/h;cam.updateProjectionMatrix();} addEventListener('resize',size); size();
const bin=Uint8Array.from(atob('%(glb)s'),c=>c.charCodeAt(0));
new GLTFLoader().parse(bin.buffer,'',g=>{
  sc.add(g.scene); const box=document.getElementById('parts');
  const GH=new THREE.Vector3(-0.025,1.345,0.165), REST=%(abd)f*Math.PI/180;
  const FLEX=new Set(['UA_near_ring','UA_far_ring','FA_near_ring','wrist_ring_cuff','PVC_pipes','elbow_hub_lateral','elbow_hub_medial','UA_strut','body_arm']);
  const ABD=new Set(['yoke','flexion_hub']);
  const abdG=new THREE.Group(); abdG.position.copy(GH); sc.add(abdG);
  const flxG=new THREE.Group(); abdG.add(flxG);
  const un1=new THREE.Group(); un1.rotation.x=REST; flxG.add(un1);
  const un2=new THREE.Group(); un2.rotation.x=REST; abdG.add(un2);
  const meshes=[]; g.scene.traverse(o=>{ if(o.isMesh) meshes.push(o); });
  for(const o of meshes){ if(FLEX.has(o.name)||ABD.has(o.name)){ (FLEX.has(o.name)?un1:un2).add(o); o.position.set(-GH.x,-GH.y,-GH.z); o.rotation.set(0,0,0); o.scale.set(1,1,1);} }
  const upd=()=>{const a=+document.getElementById('abd').value, f=+document.getElementById('flx').value;
    document.getElementById('av').textContent=a; document.getElementById('fv').textContent=f;
    abdG.rotation.x=-a*Math.PI/180; flxG.rotation.z=f*Math.PI/180;};
  document.getElementById('abd').oninput=upd; document.getElementById('flx').oninput=upd; upd();
  const bodies=[];
  meshes.forEach(o=>{
    o.geometry.deleteAttribute('normal'); o.geometry.computeVertexNormals();
    o.material=new THREE.MeshStandardMaterial({color:COLS[o.name]||'#8fa3b3',roughness:.7,metalness:.05,side:THREE.DoubleSide});
    if(o.name.startsWith('body')){o.material.transparent=true;o.material.opacity=.85;o.material.depthWrite=false;o.renderOrder=2;bodies.push(o);
      document.getElementById('op').oninput=e=>bodies.forEach(b=>{b.material.opacity=+e.target.value;b.visible=+e.target.value>0;});}
    const l=document.createElement('label'); l.innerHTML='<input type="checkbox" checked> '+o.name.replace(/_/g,' ');
    l.firstChild.onchange=e=>o.visible=e.target.checked; box.appendChild(l); });
});
(function loop(){requestAnimationFrame(loop);ctl.update();r.render(sc,cam);})();
</script></body></html>""" % dict(abd=info['params']['rest_abd'], rows=''.join(rows), glb=glb, cols=json.dumps(colmap))
(LAY / 'viewer.html').write_text(html, encoding='utf-8')
print('viewer.html %.1f MB, parts: %s' % (len(html) / 1e6, ', '.join(names)))
