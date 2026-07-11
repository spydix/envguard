from __future__ import annotations

import shutil
from pathlib import Path

from envguard.linter import parse_env_file


def fix_env_file(
    path: str | Path,
    sort_keys: bool = True,
    deduplicate: bool = True,
    backup: bool = True,
) -> str:
    """Fix a .env file by sorting keys and removing duplicates.

    Args:
        path: Path to the .env file.
        sort_keys: If True, sort keys alphabetically.
        deduplicate: If True, keep only the last value for duplicate keys.
        backup: If True, create a .bak backup before modifying.

    Returns the path to the backup file, or empty string if no backup was made.
    """
    p = Path(path)
    backup_path = ""

    if backup:
        backup_path = str(p.with_suffix(p.suffix + ".bak"))
        shutil.copy2(p, backup_path)

    entries = parse_env_file(p)
    comments = []
    key_entries: dict[str, str] = {}

    for entry in entries:
        if deduplicate and entry.key in key_entries:
            key_entries[entry.key] = entry.value
        else:
            key_entries[entry.key] = entry.value

    if sort_keys:
        sorted_keys = sorted(key_entries.keys())
    else:
        # preserve file order
        seen: set[str] = set()
        sorted_keys = []
        for e in entries:
            if e.key not in seen:
                seen.add(e.key)
                sorted_keys.append(e.key)

    lines: list[str] = []
    for key in sorted_keys:
        value = key_entries[key]
        lines.append(f"{key}={value}")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return backup_path
