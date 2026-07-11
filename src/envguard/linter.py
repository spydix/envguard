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


@dataclass
class ComparisonResult:
    missing_in_env: list[str]
    missing_in_example: list[str]
    env_file: str
    example_file: str


def parse_env_file(path: str | Path) -> list[EnvEntry]:
    """Parse a .env file and return a list of entries.

    Handles:
    - Lines starting with # (comments, skipped)
    - Lines starting with export (export prefix stripped)
    - Quoted values (single and double quotes stripped)
    - Empty lines (skipped)
    - Multiline values (backslash continuation at end of line)
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    entries: list[EnvEntry] = []

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        if stripped.startswith("export "):
            stripped = stripped[len("export "):].strip()

        if "=" not in stripped:
            i += 1
            continue

        key, _, value = stripped.partition("=")
        key = key.strip()

        value = value.strip()

        # Handle inline comments: if the value is not quoted and contains
        # a space followed by #, treat everything after the # as a comment.
        # But only if the # is preceded by whitespace (not part of a URL
        # like http://...#anchor).
        if value and not (value[0] in ('"', "'")):
            # Find a # that is preceded by whitespace
            for j, ch in enumerate(value):
                if ch == "#" and j > 0 and value[j - 1] == " ":
                    value = value[:j].strip()
                    break

        # Handle multiline values: if value ends with backslash, keep reading
        while value.endswith("\\"):
            value = value[:-1]
            i += 1
            if i < len(lines):
                value += lines[i].strip()

        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        is_empty = value == ""
        entries.append(EnvEntry(key=key, value=value, line=i, is_empty=is_empty))
        i += 1

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


def load_envignore(path: str | Path) -> set[str]:
    """Load a .envignore file and return a set of key names to skip.

    Each line is a key name. Lines starting with # are comments.
    """
    p = Path(path)
    if not p.exists():
        return set()
    keys: set[str] = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        keys.add(line)
    return keys


def filter_entries(
    entries: list[EnvEntry],
    ignored_keys: set[str] | None = None,
) -> list[EnvEntry]:
    """Filter out entries whose keys are in the ignored set."""
    if not ignored_keys:
        return entries
    return [e for e in entries if e.key not in ignored_keys]


def get_keys(entries: list[EnvEntry]) -> list[str]:
    """Get a list of unique keys from entries, preserving first-seen order."""
    seen: set[str] = set()
    keys: list[str] = []
    for e in entries:
        if e.key not in seen:
            seen.add(e.key)
            keys.append(e.key)
    return keys


def compare_env_files(
    env_path: str | Path,
    example_path: str | Path,
) -> ComparisonResult:
    """Compare a .env file with a .env.example file.

    Returns keys that are missing in env (but present in example)
    and keys that are missing in example (but present in env).

    Keys are returned in the order they appear in the file.
    """
    env_entries = parse_env_file(env_path)
    example_entries = parse_env_file(example_path)

    env_keys = set(e.key for e in env_entries)
    example_keys = set(e.key for e in example_entries)

    # Preserve order: iterate in file order, filter by set membership
    missing_in_env = [k for k in get_keys(example_entries) if k not in env_keys]
    missing_in_example = [k for k in get_keys(env_entries) if k not in example_keys]

    return ComparisonResult(
        missing_in_env=missing_in_env,
        missing_in_example=missing_in_example,
        env_file=str(env_path),
        example_file=str(example_path),
    )
