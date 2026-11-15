"""Vercel Serverless Function entry point from repository root."""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
MEMBER5_DIR = ROOT_DIR / "Member_5"

for p in [str(MEMBER5_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app import app
