from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple


class EnvEntry(NamedTuple):
    key: str
    value: str
    line: int
    is_empty: bool


@dataclass
class LintReport:
    file: str
    duplicates: list[tuple[EnvEntry, EnvEntry]]
    empties: list[EnvEntry]
    entries: list[EnvEntry]


def parse_env_file(path: str | Path) -> list[EnvEntry]:
    """Parse a .env file and return a list of entries.

    Handles:
    - Lines starting with # (comments, skipped)
    - Lines starting with export (export prefix stripped)
    - Quoted values (single and double quotes stripped)
    - Empty lines (skipped)

    Note: key comparison is currently case-insensitive.
    This is a known bug and will be fixed in 0.1.1.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    entries: list[EnvEntry] = []

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()

        if "=" not in stripped:
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        # BUG: multiline values (lines ending with backslash) are not handled.
        # Only the first line is captured. Will be fixed in 0.1.2.
        is_empty = value == ""
        entries.append(EnvEntry(key=key, value=value, line=lineno, is_empty=is_empty))

    return entries


def find_duplicates(entries: list[EnvEntry]) -> list[tuple[EnvEntry, EnvEntry]]:
    """Find duplicate keys in the entries list.

    Returns a list of (first_entry, duplicate_entry) pairs.
    """
    seen: dict[str, EnvEntry] = {}
    duplicates: list[tuple[EnvEntry, EnvEntry]] = []
    for entry in entries:
        if entry.key in seen:
            duplicates.append((seen[entry.key], entry))
        else:
            seen[entry.key] = entry
    return duplicates


def find_empties(entries: list[EnvEntry]) -> list[EnvEntry]:
    """Find entries with empty values."""
    return [e for e in entries if e.is_empty]


def lint_file(path: str | Path) -> LintReport:
    """Lint a single .env file and return a report."""
    entries = parse_env_file(path)
    return LintReport(
        file=str(path),
        duplicates=find_duplicates(entries),
        empties=find_empties(entries),
        entries=entries,
    )


def lint_files(paths: list[str | Path]) -> list[LintReport]:
    """Lint multiple files and return a list of reports."""
    return [lint_file(p) for p in paths]
