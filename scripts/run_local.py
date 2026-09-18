"""Launch a loopback-only demo with a fresh secret. Never commit real tokens."""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import uvicorn

parser = argparse.ArgumentParser(description="Launch the local coordinator prototype")
parser.add_argument("--semantic", action="store_true", help="Enable the optional local multilingual model")
args = parser.parse_args()
if args.semantic:
    os.environ["ORTAK_MATCHER"] = "semantic"

token = secrets.token_urlsafe(32)
os.environ["ORTAK_REVIEWERS"] = json.dumps({token: "local-reviewer"})
print("Koordinatör arayüzü: http://127.0.0.1:8000", flush=True)
print("API: http://127.0.0.1:8000/docs", flush=True)
print("Koordinatör anahtarı (giriş ekranına yapıştır):", token, flush=True)
print("Synthetic exercises only. Press Ctrl+C to stop.", flush=True)
uvicorn.run("app.main:create_app", factory=True, host="127.0.0.1", port=8000)
