"""Validate the CAD-to-viewer articulation contract and rigid attachment invariants."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np
import trimesh
CAD=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CAD));sys.path.insert(0,str(CAD/'elbow'))
from motion import transforms, pose_vertices


class MotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((CAD/'system/stl/asm/colors.json').read_text())
        cls.motion=cls.manifest['motion']

    def test_every_layer_has_one_valid_link_and_body_views_stay_separate(self):
        m=self.motion;links={'base'}|{j['id'] for j in m['joints']}
        self.assertEqual(set(m['bindings']),set(self.manifest['layers']))
        self.assertTrue(set(m['bindings'].values())<=links)
        self.assertTrue(set(m['flexible'])<=set(m['bindings']))
        self.assertEqual(set(self.manifest['ghosts']),{'human','ghost_upper','ghost_forearm'})
        self.assertFalse(set(self.manifest['ghosts']) & set(self.manifest['views']['brace']))
        for joint,layer in zip(m['joints'],['sh_sheave_abd','sh_sheave_flex','el_sheave']):
            mesh=trimesh.load_mesh(CAD/'system/stl/asm'/f'{layer}.stl')
            np.testing.assert_allclose(mesh.bounds.mean(0),joint['origin'],atol=1e-4)
            self.assertEqual(np.argmin(mesh.extents),np.argmax(np.abs(joint['axis'])))

    def test_rest_pose_preserves_all_exported_vertices(self):
        for name in self.manifest['layers']:
            vertices=trimesh.load_mesh(CAD/'system/stl/asm'/f'{name}.stl').vertices
            np.testing.assert_allclose(pose_vertices(name,vertices,self.motion,self.motion['rest']),vertices,atol=1e-9)

    def test_three_joint_sweep_preserves_hinge_closure_and_segment_lengths(self):
        m=self.motion;elbow=np.array(m['landmarks']['elbow']);wrist=np.array(m['landmarks']['wrist'])
        def apply(matrix,p):return matrix[:3,:3]@p+matrix[:3,3]
        for a in [0,30,60]:
            for f in [0,30,60,90]:
                for e in [0,45,90,135]:
                    matrices=transforms(m,dict(shoulderAbduction=a,shoulderFlexion=f,elbowFlexion=e))
                    proximal=apply(matrices['upper'],elbow);distal=apply(matrices['forearm'],elbow)
                    np.testing.assert_allclose(proximal,distal,atol=1e-9)
                    self.assertAlmostEqual(np.linalg.norm(apply(matrices['forearm'],wrist)-distal),wrist[0])
                    self.assertAlmostEqual(np.linalg.norm(proximal),-elbow[1])

    def test_split_hardware_and_trim_follow_their_host(self):
        expected={'ar_ua_trim':'upper','ar_fa_trim':'forearm','ar_ua_led':'upper','ar_fa_led':'forearm',
                  'ar_shoulder_fasteners':'shoulder','sh_anchor_abd':'base','sh_anchor_flex':'shoulder',
                  'el_cuff_upper':'upper','el_cuff_forearm':'forearm','ghost_forearm':'forearm'}
        for name,link in expected.items():self.assertEqual(self.motion['bindings'][name],link)
        pose=dict(shoulderAbduction=30,shoulderFlexion=45,elbowFlexion=120)
        for i in range(6):
            name=f'housing_{i}';spec=self.motion['flexible'][name]
            endpoints=np.array([spec['path'][0],spec['path'][-1]])
            moved=pose_vertices(name,endpoints,self.motion,pose)
            np.testing.assert_allclose(moved[0],endpoints[0],atol=1e-9)
            end_matrix=transforms(self.motion,pose)[spec['toLink']]
            np.testing.assert_allclose(moved[1],end_matrix[:3,:3]@endpoints[1]+end_matrix[:3,3],atol=1e-9)


if __name__=='__main__':unittest.main(verbosity=2)
