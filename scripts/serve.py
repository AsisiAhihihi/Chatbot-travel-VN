"""Run from the repository root: .venv/Scripts/python.exe scripts/serve.py."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "src"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("rag.api:app", host="127.0.0.1", port=int(os.getenv("API_PORT", "8000")))