#!/usr/bin/env python3
"""Render the armor previews using the shared CAD renderer."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_previews import main

if __name__ == '__main__':
    main(('armor',))
