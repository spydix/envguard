from __future__ import annotations

import re
import shutil
from pathlib import Path


def _parse_line(line: str) -> tuple[str, str, str, str]:
    """Parse a single .env line into (key, value, inline_comment, comment_line).

    Returns (key, value, inline_comment, comment_line).
    - key is empty for comment/blank lines.
    - inline_comment is the # comment part of a KEY=value line.
    - comment_line is the full original line for comment/blank lines.
    """
    stripped = line.strip()

    if not stripped:
        return "", "", "", ""

    if stripped.startswith("#"):
        return "", "", "", line

    if stripped.startswith("export "):
        stripped = stripped[len("export "):].strip()

    if "=" not in stripped:
        return "", "", "", ""

    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()

    inline_comment = ""
    if value and not (value[0] in ('"', "'")):
        for j, ch in enumerate(value):
            if ch == "#" and j > 0 and value[j - 1] == " ":
                inline_comment = value[j:]
                value = value[:j].strip()
                break

    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        value = value[1:-1]

    return key, value, inline_comment, ""


def fix_env_file(
    path: str | Path,
    sort_keys: bool = True,
    deduplicate: bool = True,
    backup: bool = True,
) -> str:
    """Fix a .env file by sorting keys and removing duplicates.

    Preserves comment lines and inline comments. Removes blank lines
    between entries for a clean sorted output.

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

    raw_lines = p.read_text(encoding="utf-8").splitlines()

    key_entries: dict[str, tuple[str, str]] = {}
    key_order: list[str] = []
    comments: list[str] = []

    for line in raw_lines:
        key, value, inline, comment_line = _parse_line(line)
        if key:
            if key not in key_entries:
                key_order.append(key)
            key_entries[key] = (value, inline)
        elif comment_line:
            comments.append(comment_line)

    if sort_keys:
        sorted_keys = sorted(key_entries.keys())
    else:
        seen: set[str] = set()
        sorted_keys = []
        for k in key_order:
            if k not in seen:
                seen.add(k)
                sorted_keys.append(k)

    lines: list[str] = []

    for comment in comments:
        lines.append(comment)

    for key in sorted_keys:
        value, inline = key_entries[key]
        if value:
            line = f"{key}={value}"
        else:
            line = f"{key}="
        if inline:
            line += f" {inline}"
        lines.append(line)

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return backup_path
