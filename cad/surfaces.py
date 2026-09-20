"""Closed parametric surface patches for concept shells and trim.

No unclosed sheet surfaces or implicit boolean unions. Separate panels remain
separate solids. Export normalizes the winding of each connected component.
"""
from pathlib import Path
import sys
import numpy as np
import trimesh
sys.path.insert(0, str(Path(__file__).resolve().parent / 'elbow'))
from build_stl import Mesh, annulus, cylinder


def quad(mesh, a, b, c, d):
    mesh.add_tri(a, b, c)
    mesh.add_tri(a, c, d)


def patch(point, nu=24, nv=20):
    """point(u, v, inner) supplies both skins; all four boundaries are capped."""
    grid = np.array([[[point(u, v, inside) for v in np.linspace(0, 1, nv)]
                      for u in np.linspace(0, 1, nu)] for inside in [False, True]])
    m = Mesh()
    for i in range(nu - 1):
        for j in range(nv - 1):
            quad(m, grid[0,i,j], grid[0,i+1,j], grid[0,i+1,j+1], grid[0,i,j+1])
            quad(m, grid[1,i,j], grid[1,i,j+1], grid[1,i+1,j+1], grid[1,i+1,j])
    for i in range(nu - 1):
        quad(m, grid[0,i,0], grid[1,i,0], grid[1,i+1,0], grid[0,i+1,0])
        quad(m, grid[0,i,-1], grid[0,i+1,-1], grid[1,i+1,-1], grid[1,i,-1])
    for j in range(nv - 1):
        quad(m, grid[0,0,j], grid[0,0,j+1], grid[1,0,j+1], grid[1,0,j])
        quad(m, grid[0,-1,j], grid[1,-1,j], grid[1,-1,j+1], grid[0,-1,j+1])
    return m


def normalize(mesh):
    tris = np.asarray(mesh.tris)
    if not len(tris): return mesh
    tm = trimesh.Trimesh(vertices=tris.reshape(-1,3), faces=np.arange(len(tris)*3).reshape(-1,3), process=True)
    tm.fix_normals(multibody=True)
    out = Mesh()
    out.tris = list(tm.triangles)
    return out


def ring(ro, ri, thickness, z=0., n=96):
    # Four radial stations give machined chamfers instead of a flat washer.
    stations = [(ri, -thickness/2+.7), (ri+.7, -thickness/2),
                (ro-.7, -thickness/2), (ro, -thickness/2+.7),
                (ro, thickness/2-.7), (ro-.7, thickness/2),
                (ri+.7, thickness/2), (ri, thickness/2-.7)]
    m = Mesh()
    for i in range(n):
        a,b = 2*np.pi*i/n,2*np.pi*(i+1)/n
        for j in range(len(stations)):
            r0,h0=stations[j];r1,h1=stations[(j+1)%len(stations)]
            quad(m,[r0*np.cos(a),r0*np.sin(a),z+h0],[r0*np.cos(b),r0*np.sin(b),z+h0],
                 [r1*np.cos(b),r1*np.sin(b),z+h1],[r1*np.cos(a),r1*np.sin(a),z+h1])
    return m


def plate(outline, z, thickness, bevel=1.5):
    """Convex beveled plate in XY. Useful for frame rails and service covers."""
    p=np.asarray(outline,float);center=p.mean(0)
    delta=p-center;length=np.linalg.norm(delta,axis=1)
    inset=center+delta*np.maximum(0.1,(length-bevel)/length)[:,None]
    rings=[np.column_stack([inset,np.full(len(p),z)]),
           np.column_stack([p,np.full(len(p),z+bevel)]),
           np.column_stack([p,np.full(len(p),z+thickness-bevel)]),
           np.column_stack([inset,np.full(len(p),z+thickness)])]
    m=Mesh()
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(len(p)):
            k=(j+1)%len(p);quad(m,a[j],a[k],b[k],b[j])
    # Ear clipping supports the concave tapered pack rails as well as convex
    # covers. A triangle fan would wrongly fill the rail's viewing recess.
    area=np.sum(p[:,0]*np.roll(p[:,1],-1)-np.roll(p[:,0],-1)*p[:,1])
    ids=list(range(len(p))) if area>0 else list(reversed(range(len(p))))
    triangles=[]
    def cross(a,b,c):
        d,e=b-a,c-a
        return float(d[0]*e[1]-d[1]*e[0])
    while len(ids)>3:
        for k in range(len(ids)):
            a,b,c=ids[k-1],ids[k],ids[(k+1)%len(ids)]
            if cross(p[a],p[b],p[c])<=1e-8:continue
            if any(cross(p[a],p[b],p[q])>=-1e-8 and cross(p[b],p[c],p[q])>=-1e-8 and cross(p[c],p[a],p[q])>=-1e-8
                   for q in ids if q not in [a,b,c]):continue
            triangles.append((a,b,c));ids.pop(k);break
        else:raise ValueError('Panel outline cannot be triangulated')
    triangles.append(tuple(ids))
    for a,b,c in triangles:
        m.add_tri(rings[0][a],rings[0][c],rings[0][b])
        m.add_tri(rings[-1][a],rings[-1][b],rings[-1][c])
    return m


def tube(points, radius=3., sides=10):
    """Continuous capped sweep with shared vertices at every path station."""
    pts=np.asarray(points,float);rings=[]
    for i,p in enumerate(pts):
        tangent=pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)];tangent/=np.linalg.norm(tangent)
        ref=np.array([0.,0.,1.]) if abs(tangent[2])<.9 else np.array([0.,1.,0.])
        x=np.cross(tangent,ref);x/=np.linalg.norm(x);y=np.cross(tangent,x)
        rings.append([p+radius*(x*np.cos(a)+y*np.sin(a)) for a in np.linspace(0,2*np.pi,sides,endpoint=False)])
    m=Mesh()
    for a,b in zip(rings[:-1],rings[1:]):
        for j in range(sides):
            k=(j+1)%sides;quad(m,a[j],a[k],b[k],b[j])
    for j in range(sides):
        k=(j+1)%sides;m.add_tri(pts[0],rings[0][k],rings[0][j]);m.add_tri(pts[-1],rings[-1][j],rings[-1][k])
    return m


def curve(points, samples=60):
    from scipy.interpolate import PchipInterpolator
    p=np.asarray(points,float);s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    return PchipInterpolator(s,p,axis=0)(np.linspace(0,s[-1],samples))


def ellipsoid(radii, center=(0,0,0), subdivisions=2):
    t=trimesh.creation.icosphere(subdivisions=subdivisions)
    t.vertices=t.vertices*np.array(radii)+np.array(center)
    m=Mesh();m.tris=list(t.triangles);return m
