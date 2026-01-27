"""Pytest configuration for backend tests."""

import sys
from pathlib import Path

# Add the backend-python directory to the path so 'app' module can be imported
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
