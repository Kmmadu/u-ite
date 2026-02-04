import json
from pathlib import Path

APP_DIR = Path.home() / ".u-ite"
EVENT_FILE = APP_DIR / "events.json"


def _ensure():
    APP_DIR.mkdir(exist_ok=True)
    if not EVENT_FILE.exists():
        EVENT_FILE.write_text("[]")


def save_events(events):
    if not events:
        return

    _ensure()
    history = json.loads(EVENT_FILE.read_text())
    history.extend(events)

    EVENT_FILE.write_text(json.dumps(history, indent=2))
