import json
from pathlib import Path

APP_DIR = Path.home() / ".u-ite"
TRACKING_FILE = APP_DIR / "tracking.json"


def ensure_tracking_file():
    APP_DIR.mkdir(parents=True, exist_ok=True)

    if not TRACKING_FILE.exists():
        TRACKING_FILE.write_text("[]")


def load_history():
    ensure_tracking_file()

    try:
        return json.loads(TRACKING_FILE.read_text())
    except Exception:
        return []


def save_snapshot(snapshot):
    history = load_history()
    history.append(snapshot)

    TRACKING_FILE.write_text(json.dumps(history, indent=2))
