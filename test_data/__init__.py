"""Shared test data for automation flows."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CREDENTIALS_FILE = Path(__file__).resolve().parent / "credentials.json"

DEFAULT_LOGIN = {
    "username": "Admin",
    "password": "admin123",
}


@lru_cache
def _load_credentials_file() -> dict[str, Any]:
    if not CREDENTIALS_FILE.exists():
        return {"login": DEFAULT_LOGIN}
    return json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))


def get_login_credentials() -> dict[str, str]:
    """Return login username and password from test data."""
    data = _load_credentials_file()
    login = data.get("login", DEFAULT_LOGIN)
    return {
        "username": str(login.get("username", DEFAULT_LOGIN["username"])),
        "password": str(login.get("password", DEFAULT_LOGIN["password"])),
}


def credentials_file_path() -> Path:
    return CREDENTIALS_FILE


def get_invalid_login_credentials() -> dict[str, str]:
    """Return invalid/wrong credentials for negative-path test flows."""
    data = _load_credentials_file()
    invalid = data.get("invalid_login", {
        "username": "invalid_user",
        "password": "wrong_password",
    })
    return {
        "username": str(invalid.get("username", "invalid_user")),
        "password": str(invalid.get("password", "wrong_password")),
    }


def classify_auth_scenario(flow: str) -> str:
    """Classify a flow name into an auth scenario type for credential selection."""
    f = flow.lower()
    if any(k in f for k in ("invalid_password", "wrong password", "bad password", "incorrect password")):
        return "invalid_password"
    if any(k in f for k in ("invalid_username", "wrong user", "bad user", "unknown user")):
        return "invalid_username"
    if any(k in f for k in ("empty", "blank", "missing")):
        return "empty"
    if any(k in f for k in ("invalid", "failed", "fail", "unauthorized", "wrong", "bad", "incorrect", "error")):
        return "invalid"
    return "valid"


def get_credentials_for_scenario(flow: str) -> dict[str, str]:
    """Return the right credentials for the given flow scenario."""
    scenario = classify_auth_scenario(flow)
    valid = get_login_credentials()
    invalid = get_invalid_login_credentials()
    if scenario == "invalid_password":
        return {"username": valid["username"], "password": invalid["password"]}
    if scenario == "invalid_username":
        return {"username": invalid["username"], "password": valid["password"]}
    if scenario in ("invalid", "empty"):
        return invalid
    return valid
