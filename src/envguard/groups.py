from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any

from envguard.linter import compare_env_files
from envguard.linter import get_keys
from envguard.linter import lint_files
from envguard.linter import LintReport
from envguard.linter import parse_env_file


@dataclass
class FileGroup:
    """A named group of .env files to lint and compare together."""
    name: str
    files: list[str] = field(default_factory=list)
    example: str | None = None

    def resolve_files(self, base_dir: str | Path | None = None) -> list[str]:
        """Return resolved file paths that exist."""
        base = Path(base_dir) if base_dir else Path.cwd()
        result: list[str] = []
        for f in self.files:
            p = Path(f)
            if not p.is_absolute():
                p = base / p
            if p.exists():
                result.append(str(p))
        return result

    def resolve_example(self, base_dir: str | Path | None = None) -> str | None:
        if not self.example:
            return None
        base = Path(base_dir) if base_dir else Path.cwd()
        p = Path(self.example)
        if not p.is_absolute():
            p = base / p
        return str(p) if p.exists() else None


def load_file_groups(config: dict[str, Any]) -> list[FileGroup]:
    """Extract file groups from config dict.

    Config format in TOML:
        [[envguard.file_groups]]
        name = "production"
        files = [".env", ".env.production"]
        example = ".env.example"
    """
    groups: list[FileGroup] = []
    raw_groups = config.get("file_groups", [])
    if not isinstance(raw_groups, list):
        return groups
    for g in raw_groups:
        if not isinstance(g, dict):
            continue
        name = g.get("name", "unnamed")
        files = g.get("files", [])
        example = g.get("example")
        if isinstance(files, str):
            files = [files]
        groups.append(FileGroup(name=name, files=files, example=example))
    return groups


def lint_file_group(group: FileGroup, base_dir: str | Path | None = None) -> list[dict[str, Any]]:
    """Lint a file group and return comparison results.

    Returns a list of dicts with keys:
        - file: str
        - issues: list of LintReport
        - missing_in_env: list[str] (from example comparison)
        - missing_in_example: list[str]
    """
    resolved = group.resolve_files(base_dir)
    if not resolved:
        return []

    reports = lint_files(resolved)
    results: list[dict[str, Any]] = []

    example_path = group.resolve_example(base_dir)

    for i, report in enumerate(reports):
        entry: dict[str, Any] = {
            "file": report.file,
            "report": report,
            "missing_in_env": [],
            "missing_in_example": [],
        }
        if example_path:
            cmp = compare_env_files(report.file, example_path)
            entry["missing_in_env"] = cmp.missing_in_env
            entry["missing_in_example"] = cmp.missing_in_example
        results.append(entry)

    if len(resolved) > 1:
        all_keys_per_file = []
        for f in resolved:
            entries = parse_env_file(f)
            all_keys_per_file.append(set(e.key for e in entries))

        for i in range(len(results)):
            for j in range(len(results)):
                if i == j:
                    continue
                own_keys = all_keys_per_file[i]
                other_keys = all_keys_per_file[j]
                keys_in_other = list(sorted(other_keys - own_keys))
                if keys_in_other:
                    results[i].setdefault("keys_missing_vs", {})
                    results[i]["keys_missing_vs"][reports[j].file] = keys_in_other

    return results
