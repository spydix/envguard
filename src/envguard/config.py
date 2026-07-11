from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


DEFAULT_CONFIG_NAME = ".envguard.toml"

DEFAULT_CONFIG: dict[str, Any] = {
    "strict": False,
    "check_secrets": False,
    "format": "text",
    "no_color": False,
    "no_backup": False,
    "envignore": None,
    "example": None,
}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load envguard configuration from a TOML file.

    Looks for .envguard.toml in the current directory if no path is given.
    Returns a dict with keys matching CLI flags.
    """
    if tomllib is None:
        return dict(DEFAULT_CONFIG)

    if path is None:
        p = Path(DEFAULT_CONFIG_NAME)
        if not p.exists():
            return dict(DEFAULT_CONFIG)
    else:
        p = Path(path)

    if not p.exists():
        return dict(DEFAULT_CONFIG)

    data = tomllib.loads(p.read_text(encoding="utf-8"))

    config: dict[str, Any] = dict(DEFAULT_CONFIG)

    section = data.get("envguard", data)

    for key in DEFAULT_CONFIG:
        if key in section:
            config[key] = section[key]

    return config


def merge_config(cli_args: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Merge CLI args with config file. CLI args take priority.

    A CLI arg is considered 'set' if it differs from its default value
    (for flags: True means set; for values: non-None means set).
    """
    merged: dict[str, Any] = {}

    for key in DEFAULT_CONFIG:
        cli_val = cli_args.get(key)
        config_val = config.get(key)

        if key in ("strict", "check_secrets", "no_color", "no_backup"):
            if cli_val:
                merged[key] = cli_val
            else:
                merged[key] = config_val
        elif key in ("format",):
            if cli_val and cli_val != "text":
                merged[key] = cli_val
            else:
                merged[key] = config_val
        elif key in ("envignore", "example"):
            if cli_val:
                merged[key] = cli_val
            else:
                merged[key] = config_val
        else:
            merged[key] = config_val

    return merged
