import sys
from pathlib import Path

# src/ must be on sys.path so that src/main.py's bare imports
# (api, services, utils) resolve correctly when pytest imports via `from src.main import app`.
sys.path.insert(0, str(Path(__file__).parent / "src"))
