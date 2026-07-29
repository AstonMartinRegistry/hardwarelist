import os
import sys

# Repo root on sys.path so `from app import app` works in the Vercel Python runtime.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
