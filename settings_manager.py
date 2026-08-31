"""Local-only persistence helpers for SONIC FORGE."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import dotenv_values, set_key, unset_key

APP_DIR = Path(__file__).resolve().parent
ENV_PATH = APP_DIR / ".env"
SETTINGS_PATH = APP_DIR / "settings.json"
DEFAULT_SETTINGS = {"default_model": "medium", "default_duration": 30}


def load_token() -> str:
    """Return the locally saved token without ever exposing it to the UI."""
    token = dotenv_values(ENV_PATH).get("HF_TOKEN") or os.getenv("HF_TOKEN", "")
    return token.strip()


def load_settings() -> dict:
    """Load preferences, falling back safely when the JSON file is absent or invalid."""
    settings = DEFAULT_SETTINGS.copy()
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as file:
            saved = json.load(file)
        if isinstance(saved, dict):
            settings.update({key: saved[key] for key in DEFAULT_SETTINGS if key in saved})
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return settings


def save_token(token: str) -> None:
    """Persist a Hugging Face token in the local .env file."""
    set_key(str(ENV_PATH), "HF_TOKEN", token.strip(), quote_mode="auto")


def save_settings(default_model: str, default_duration: int | float) -> None:
    """Persist non-sensitive UI preferences locally."""
    payload = {
        "default_model": default_model,
        "default_duration": int(default_duration),
    }
    SETTINGS_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def clear_local_setup() -> None:
    """Remove the app-managed token and settings from this computer."""
    if ENV_PATH.exists():
        unset_key(str(ENV_PATH), "HF_TOKEN")
        # Avoid leaving an empty .env behind unless it carries other variables.
        if not dotenv_values(ENV_PATH):
            ENV_PATH.unlink(missing_ok=True)
    SETTINGS_PATH.unlink(missing_ok=True)
