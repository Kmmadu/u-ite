import uuid
import json
from pathlib import Path
import logging
import os


logger = logging.getLogger("U-ITE")

APP_DIR = Path.home() / ".u-ite"
DEVICE_FILE = APP_DIR / "device.json"


def ensure_app_dir():
    """
    Ensure application directory exists with safe permissions.
    """
    try:
        APP_DIR.mkdir(parents=True, exist_ok=True)

        # Set directory permission to user-only (Linux safe practice)
        os.chmod(APP_DIR, 0o700)

    except Exception as e:
        logger.error(f"Failed to create app directory: {e}")
        raise


def generate_device_id():
    """Generate a new UUID device ID."""
    return str(uuid.uuid4())


def save_device_id(device_id: str):
    """
    Persist device ID safely to disk.
    Uses atomic write to avoid corruption.
    """
    ensure_app_dir()

    temp_file = DEVICE_FILE.with_suffix(".tmp")

    data = {"device_id": device_id}

    try:
        # Write to temp file first
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)

        # Replace actual file atomically
        temp_file.replace(DEVICE_FILE)

        # Restrict file permission to user-only
        os.chmod(DEVICE_FILE, 0o600)

        logger.info("Device ID saved successfully.")

    except Exception as e:
        logger.error(f"Failed to save device ID: {e}")
        raise


def load_device_id():
    """
    Load existing device ID from disk.
    """
    if not DEVICE_FILE.exists():
        return None

    try:
        with open(DEVICE_FILE, "r") as f:
            data = json.load(f)

        device_id = data.get("device_id")

        # Validate value
        if device_id and isinstance(device_id, str):
            return device_id

    except Exception as e:
        logger.error(f"Failed to load device ID: {e}")

    return None


def get_device_id():
    """
    Main entry point.
    Returns persistent device ID.
    """
    device_id = load_device_id()

    if device_id:
        return device_id

    logger.info("Generating new device ID...")

    device_id = generate_device_id()
    save_device_id(device_id)

    return device_id
