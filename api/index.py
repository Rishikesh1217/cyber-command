import sys
import os

# Add the parent directory to the path so we can find server.py
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from server import app

# Vercel needs the app as 'app' or 'application'
application = app
