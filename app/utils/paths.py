import sys
from pathlib import Path

def resource_path(rel: str) -> Path:
    """Works both from source and inside the PyInstaller exe."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
    return base / rel
