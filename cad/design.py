"""Shared dimensions and assembly coordinates. Millimetres, right-handed world."""
from pathlib import Path
import json
import numpy as np

CAD = Path(__file__).resolve().parent
REPO = CAD.parent
PARAMS = json.loads((CAD / 'params.json').read_text())
HUMAN = PARAMS['human']
UA = float(HUMAN['upper_arm_len'])
FA = float(HUMAN['forearm_len'])
# World: X forward, Y up, Z outboard. Both flexion axes are parallel to Z.
ELBOW = np.array([0., -UA, 0.])
SHOULDER_Z = 72.
SHOULDER_ABD_X = -78.
MID_Z = -200.
R_PACK = np.array([[0., 0., -1.], [0., 1., 0.], [1., 0., 0.]])
T_PACK = np.array([-145., -65., MID_Z])
# Three transverse winches. Separate lower battery compartment.
PACK = PARAMS['packaging']
WINCH_ROWS = tuple(PACK['winch_rows_y'])
WINCH_Z = float(PACK['winch_center_z'])
WINCH_X = -35.75
BATTERY_SIZE = np.array(PACK['battery_envelope_xyz'], float)
BATTERY_CENTER = np.array(PACK['battery_center_xyz'], float)


def public_dir(kit):
    return REPO / 'public' / 'cad' / kit


def place_elbow(mesh):
    # The legacy elbow mesh points toward -X. Mirror it into the right-arm
    # work pose, without the old 45-degree yaw that misaligned the hinge axes.
    result = type(mesh)()
    for tri in mesh.tris:
        points = np.asarray(tri).copy()
        points[:, 0] *= -1
        result.tris.append(points[::-1] + ELBOW)
    return result


def pack_point(point):
    return R_PACK @ np.asarray(point, float) + T_PACK
