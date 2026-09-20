"""Checks the exported geometry and the critical layout invariants."""
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest
import numpy as np
import trimesh

CAD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CAD));sys.path.insert(0,str(CAD/'elbow'))
from design import WINCH_ROWS, PACK, UA, ELBOW


def load(name):
    spec=importlib.util.spec_from_file_location(name+'_test',CAD/name/'build_stl.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def bounds(mesh):return np.array(mesh.tris).reshape(-1,3).min(0),np.array(mesh.tris).reshape(-1,3).max(0)


def count(path):return struct.unpack_from('<I',path.read_bytes(),80)[0]


class RevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack=load('backpack');cls.shoulder=load('shoulder');cls.system=load('system')

    def test_exports_match_and_assemblies_contain_every_manifest_layer(self):
        for kit in ['elbow','shoulder','backpack','armor','system']:
            local=CAD/kit/'stl';public=CAD.parent/'public/cad'/kit
            manifest=json.loads((public/'asm/colors.json').read_text())
            self.assertEqual((local/'asm/colors.json').read_bytes(),(public/'asm/colors.json').read_bytes())
            for name in manifest['layers']:
                self.assertEqual((local/'asm'/f'{name}.stl').read_bytes(),(public/'asm'/f'{name}.stl').read_bytes())
            for assembly,view in [('assembly_worn','worn'),('assembly_preview','brace')]:
                self.assertEqual((local/f'{assembly}.stl').read_bytes(),(public/f'{assembly}.stl').read_bytes())
                self.assertEqual(count(public/f'{assembly}.stl'),sum(count(public/'asm'/f'{n}.stl') for n in manifest['views'][view]))
            for part in local.glob('print_*.stl'):
                self.assertEqual(part.read_bytes(),(public/part.name).read_bytes())

    def test_every_new_shell_is_one_closed_consistently_oriented_solid(self):
        armor=load('armor')
        for name in armor.print_parts():
            with self.subTest(part=name):
                mesh=trimesh.load_mesh(CAD/'armor/stl'/f'{name}.stl',process=True)
                self.assertTrue(mesh.is_watertight)
                self.assertTrue(mesh.is_winding_consistent)
                self.assertGreater(mesh.volume,0)
                self.assertEqual(len(mesh.split(only_watertight=False)),1)

    def test_pack_hardware_envelopes_do_not_overlap(self):
        p=self.pack
        parts=[(f'winch_{y}',p.winch_at(y)) for y in WINCH_ROWS]+[('battery',p.battery())]
        parts += [(f'controller_{y}',p.s1().move(0,y,10)) for y in WINCH_ROWS]
        for i,(name,a) in enumerate(parts):
            lo,hi=bounds(a)
            self.assertGreaterEqual(lo[0],-119);self.assertLessEqual(hi[0],119)
            self.assertGreaterEqual(lo[1],PACK['frame_y_min']);self.assertLessEqual(hi[1],PACK['frame_y_max'])
            self.assertGreaterEqual(lo[2],6);self.assertLessEqual(hi[2],PACK['frame_depth'])
            for other,b in parts[i+1:]:
                blo,bhi=bounds(b)
                overlap=np.minimum(hi,bhi)-np.maximum(lo,blo)
                self.assertTrue(np.any(overlap<=0),f'{name} overlaps {other}: {overlap}')

    def test_joint_axes_and_windows_share_centers(self):
        sh=self.shoulder
        lo,hi=bounds(sh.sheave_abd());self.assertEqual(int(np.argmin(hi-lo)),0)
        self.assertTrue(np.allclose((lo+hi)/2,[sh.X_ABD,0,0]))
        lo,hi=bounds(sh.sheave_flex());self.assertEqual(int(np.argmin(hi-lo)),2)
        manifest=json.loads((CAD/'system/stl/asm/colors.json').read_text())
        self.assertNotIn('ar_sheave',manifest['layers'])
        for kit,window,mechanism in [('system','ar_bezel','sh_sheave_flex'),('system','ar_elbow_bezel','el_sheave')]:
            a=trimesh.load_mesh(CAD/kit/'stl/asm'/f'{window}.stl')
            b=trimesh.load_mesh(CAD/kit/'stl/asm'/f'{mechanism}.stl')
            self.assertTrue(np.allclose(a.bounds.mean(0)[:2],b.bounds.mean(0)[:2],atol=1e-4))
        elbow=trimesh.load_mesh(CAD/'system/stl/asm/el_sheave.stl')
        self.assertTrue(np.allclose(elbow.bounds.mean(0)[:2],ELBOW[:2],atol=1e-4))
        self.assertEqual(int(np.argmin(elbow.extents)),2)

    def test_long_shell_coverage_and_cuff_clearance(self):
        ua=trimesh.load_mesh(CAD/'armor/stl/print_fairing_ua.stl')
        fa=trimesh.load_mesh(CAD/'armor/stl/print_fairing_fa.stl')
        self.assertGreater(ua.extents[1],160)
        self.assertGreater(fa.extents[0],190)
        armor=load('armor')
        for axis,t,radius in [('ua',UA-100,60.5),('fa',90,55.5)]:
            for a in np.linspace(-118,118,80):
                point=armor.limb_point(axis,t,a)
                radial=point[[0,2]] if axis=='ua' else (point-np.array([0,-UA,0]))[[1,2]]
                self.assertGreater(np.linalg.norm(radial),radius+2)


if __name__=='__main__':unittest.main(verbosity=2)
