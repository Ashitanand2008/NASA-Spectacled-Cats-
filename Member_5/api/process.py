"""Vercel Serverless Function entry point for /api/process."""

import sys
from pathlib import Path

# Ensure Member_5 directory is in Python search path
MEMBER5_DIR = Path(__file__).resolve().parent.parent
if str(MEMBER5_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER5_DIR))

# Expose WSGI app for Vercel
from app import app
