"""Working with config ~/.config/derpi-cli/config.json."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# ---------- Paths ----------
CONFIG_DIR = Path(os.environ.get(
    "XDG_CONFIG_HOME", Path.home() / ".config"
)) / "derpi-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

# ---------- Default ----------
DEFAULT_DELAY = 0.5
DEFAULT_OUTPUT = "./downloads"
DEFAULT_FILTER_ID: Optional[int] = None

DEFAULTS: Dict[str, Any] = {
    "api_key": "",
    "rate_limit_delay": DEFAULT_DELAY,
    "default_filter_id": DEFAULT_FILTER_ID,
    "default_output_dir": DEFAULT_OUTPUT,
}


def config_exists() -> bool:
    """Checks if config exists"""
    return CONFIG_FILE.exists()


def load_config(create_if_missing: bool = True) -> Dict[str, Any]:
    """
    Loads config. If config unavailable create_if_missing=True -
    starts interactable creation.
    """
    if not CONFIG_FILE.exists():
        if create_if_missing:
            return create_config_interactive()
        return dict(DEFAULTS)

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Err: Couldn't read config {CONFIG_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Populating missing fields
    for key, value in DEFAULTS.items():
        cfg.setdefault(key, value)

    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Saves configs with 600 perms."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(CONFIG_FILE, 0o600)
    except OSError:
        pass


def create_config_interactive() -> Dict[str, Any]:
    """Creates config in interactive mode."""
    print("First start. Creating config.")
    print(f"   File: {CONFIG_FILE}\n")

    # API-key
    key = input("API-key for derpibooru (Enter - skip): ").strip()

    # Requests delay
    delay_raw = input(
        f"Delay between requests, sec [{DEFAULT_DELAY}]: "
    ).strip()
    try:
        delay = float(delay_raw) if delay_raw else DEFAULT_DELAY
        if delay < 0:
            raise ValueError
    except ValueError:
        print(f"   Incorrect value. Using {DEFAULT_DELAY}")
        delay = DEFAULT_DELAY

    # Output directory
    out_raw = input(
        f"Default output directory [{DEFAULT_OUTPUT}]: "
    ).strip()
    output = out_raw if out_raw else DEFAULT_OUTPUT

    # filter_id
    filter_raw = input(
        "Filter ID (Enter - without filter): "
    ).strip()
    filter_id: Optional[int] = None
    if filter_raw:
        try:
            filter_id = int(filter_raw)
        except ValueError:
            print("   Incorrect ID, filter would not be applied.")

    cfg: Dict[str, Any] = {
        "api_key": key,
        "rate_limit_delay": delay,
        "default_filter_id": filter_id,
        "default_output_dir": output,
    }

    save_config(cfg)
    print(f"\nConfig saved: {CONFIG_FILE}\n")
    return cfg