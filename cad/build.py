#!/usr/bin/env python3
"""Rebuild all synchronized CAD exports. Run from any working directory."""
from pathlib import Path
import subprocess
import sys
CAD=Path(__file__).resolve().parent
for kit in ['elbow','shoulder','backpack','armor','system']:
    subprocess.run([sys.executable,'-B',str(CAD/kit/'build_stl.py')],check=True)
