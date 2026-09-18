"""Launch a loopback-only demo with a fresh secret. Never commit real tokens."""
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

import uvicorn

token = secrets.token_urlsafe(32)
os.environ["ORTAK_REVIEWERS"] = json.dumps({token: "local-reviewer"})
print("API: http://127.0.0.1:8000/docs", flush=True)
print("Local reviewer token (paste into Authorize):", token, flush=True)
print("Synthetic exercises only. Press Ctrl+C to stop.", flush=True)
uvicorn.run("app.main:create_app", factory=True, host="127.0.0.1", port=8000)
