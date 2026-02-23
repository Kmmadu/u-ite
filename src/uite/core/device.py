"""
Device Identification Module for U-ITE
=======================================
Manages a persistent unique identifier for the device running U-ITE.

This module ensures that each installation of U-ITE has a consistent,
persistent identifier that survives across reboots and application updates.
The device ID is used to:
- Correlate data from the same device over time
- Identify the source of network measurements
- Enable future multi-device synchronization features

Features:
- Generates a unique UUID4 on first run
- Persists to disk with safe atomic writes
- Sets secure file permissions (user-only)
- Handles corruption gracefully
- Provides a simple getter interface
"""

import uuid
import json
from pathlib import Path
import logging
import os


# Configure module logger
logger = logging.getLogger("U-ITE")

# Application directory and device file paths
# Uses XDG-compatible location: ~/.u-ite/device.json
APP_DIR = Path.home() / ".u-ite"
DEVICE_FILE = APP_DIR / "device.json"


def ensure_app_dir():
    """
    Ensure the application directory exists with proper permissions.
    
    Creates the directory if it doesn't exist and sets secure permissions
    (user-only read/write/execute) to protect sensitive data.
    
    Raises:
        Exception: If directory creation or permission setting fails
    """
    try:
        # Create directory and all parents if needed
        APP_DIR.mkdir(parents=True, exist_ok=True)

        # Set directory permission to user-only (rwx------)
        # This prevents other users on the system from reading device info
        os.chmod(APP_DIR, 0o700)

    except Exception as e:
        logger.error(f"Failed to create app directory: {e}")
        raise


def generate_device_id():
    """
    Generate a new unique device identifier.
    
    Uses UUID4 (random UUID) which provides:
    - 122 bits of randomness
    - Extremely low collision probability
    - No reliance on hardware identifiers (privacy-friendly)
    
    Returns:
        str: A new UUID4 string (e.g., "123e4567-e89b-12d3-a456-426614174000")
    """
    return str(uuid.uuid4())


def save_device_id(device_id: str):
    """
    Persist device ID to disk using atomic write pattern.
    
    Uses a temporary file and atomic rename to prevent corruption:
    1. Write to temporary file
    2. Replace actual file (atomic operation on most filesystems)
    3. Set secure permissions
    
    This ensures that even if the process is killed during write,
    we never end up with a corrupted device.json file.
    
    Args:
        device_id (str): The device ID to save
        
    Raises:
        Exception: If write or permission setting fails
    """
    ensure_app_dir()

    # Temporary file in same directory (atomic rename works within same filesystem)
    temp_file = DEVICE_FILE.with_suffix(".tmp")

    data = {"device_id": device_id}

    try:
        # Write to temporary file first
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=4)

        # Replace actual file atomically
        # On Unix, this is an atomic operation (rename)
        temp_file.replace(DEVICE_FILE)

        # Restrict file permission to user-only (rw-------)
        # Prevents other users from reading device ID
        os.chmod(DEVICE_FILE, 0o600)

        logger.info("Device ID saved successfully.")

    except Exception as e:
        logger.error(f"Failed to save device ID: {e}")
        # Clean up temporary file if it exists
        if temp_file.exists():
            temp_file.unlink()
        raise


def load_device_id():
    """
    Load existing device ID from disk.
    
    Returns None if:
    - File doesn't exist (first run)
    - File is corrupted (invalid JSON)
    - Device ID is missing or invalid
    
    Returns:
        str or None: The loaded device ID, or None if not found/invalid
    """
    if not DEVICE_FILE.exists():
        return None

    try:
        with open(DEVICE_FILE, "r") as f:
            data = json.load(f)

        device_id = data.get("device_id")

        # Validate that we got a valid string
        if device_id and isinstance(device_id, str):
            return device_id
        else:
            logger.warning("Device file exists but contains invalid data")

    except json.JSONDecodeError:
        logger.error("Device file is corrupted (invalid JSON)")
    except Exception as e:
        logger.error(f"Failed to load device ID: {e}")

    return None


def get_device_id():
    """
    Main entry point: Get or create persistent device ID.
    
    This is the only function that should be called from other modules.
    It implements the singleton pattern:
    1. Try to load existing ID from disk
    2. If not found, generate new ID and save it
    3. Return the ID
    
    The device ID is guaranteed to be consistent across all calls
    and across application restarts.
    
    Returns:
        str: The persistent device ID for this installation
        
    Example:
        >>> from uite.core.device import get_device_id
        >>> device_id = get_device_id()
        >>> print(device_id)
        '123e4567-e89b-12d3-a456-426614174000'
    """
    # Try to load existing ID
    device_id = load_device_id()

    if device_id:
        return device_id

    # No existing ID found - generate and save new one
    logger.info("Generating new device ID...")
    device_id = generate_device_id()
    save_device_id(device_id)

    return device_id


# Optional: Add a function to reset device ID (for testing/debugging)
def reset_device_id():
    """
    Delete existing device ID and generate a new one.
    
    Useful for testing or when you want to reset the device identity.
    Use with caution - this will make the device appear as a new device
    to any synchronization services.
    
    Returns:
        str: The new device ID
        
    Example:
        >>> new_id = reset_device_id()
    """
    if DEVICE_FILE.exists():
        DEVICE_FILE.unlink()
    logger.info("Device ID reset")
    return get_device_id()
