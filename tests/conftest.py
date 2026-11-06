import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

for app in sorted((REPO / "applications").iterdir()):
    if app.is_dir() and str(app) not in sys.path:
        sys.path.insert(0, str(app))
