"""Vercel Serverless Function entry point for Flask WSGI application."""

import sys
from pathlib import Path

# Ensure Member_5 directory is in the Python search path so app and team modules import cleanly
MEMBER5_DIR = Path(__file__).resolve().parent.parent
if str(MEMBER5_DIR) not in sys.path:
    sys.path.insert(0, str(MEMBER5_DIR))

# Import the configured Flask application instance
from app import app
