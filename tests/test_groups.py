from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from envguard.groups import FileGroup, load_file_groups, lint_file_group


def _write(tmp: Path, name: str, content: str) -> Path:
    f = tmp / name
    f.write_text(content)
    return f


class TestFileGroup:
    def test_resolve_files_existing(self, tmp_path):
        _write(tmp_path, ".env", "KEY=1\n")
        _write(tmp_path, ".env.local", "KEY=2\n")
        g = FileGroup(name="dev", files=[".env", ".env.local"])
        resolved = g.resolve_files(base_dir=tmp_path)
        assert len(resolved) == 2

    def test_resolve_files_skips_missing(self, tmp_path):
        _write(tmp_path, ".env", "KEY=1\n")
        g = FileGroup(name="dev", files=[".env", ".env.missing"])
        resolved = g.resolve_files(base_dir=tmp_path)
        assert len(resolved) == 1

    def test_resolve_example(self, tmp_path):
        _write(tmp_path, ".env.example", "KEY=\n")
        g = FileGroup(name="dev", files=[".env"], example=".env.example")
        example = g.resolve_example(base_dir=tmp_path)
        assert example is not None
        assert example.endswith(".env.example")

    def test_resolve_example_none(self, tmp_path):
        g = FileGroup(name="dev", files=[".env"])
        assert g.resolve_example(base_dir=tmp_path) is None


class TestLoadFileGroups:
    def test_load_groups_from_config(self):
        config = {
            "file_groups": [
                {"name": "production", "files": [".env", ".env.production"], "example": ".env.example"},
                {"name": "staging", "files": [".env.staging"]},
            ],
        }
        groups = load_file_groups(config)
        assert len(groups) == 2
        assert groups[0].name == "production"
        assert groups[0].files == [".env", ".env.production"]
        assert groups[0].example == ".env.example"
        assert groups[1].name == "staging"
        assert groups[1].files == [".env.staging"]

    def test_load_groups_empty(self):
        groups = load_file_groups({})
        assert groups == []

    def test_load_groups_string_file(self):
        config = {
            "file_groups": [
                {"name": "single", "files": ".env"},
            ],
        }
        groups = load_file_groups(config)
        assert len(groups) == 1
        assert groups[0].files == [".env"]


class TestLintFileGroup:
    def test_lint_clean_group(self, tmp_path):
        _write(tmp_path, ".env", "A=1\nB=2\n")
        _write(tmp_path, ".env.example", "A=\nB=\n")
        g = FileGroup(name="prod", files=[".env"], example=".env.example")
        results = lint_file_group(g, base_dir=tmp_path)
        assert len(results) == 1
        assert results[0]["missing_in_env"] == []
        assert results[0]["missing_in_example"] == []

    def test_lint_missing_in_env(self, tmp_path):
        _write(tmp_path, ".env", "A=1\n")
        _write(tmp_path, ".env.example", "A=\nB=\n")
        g = FileGroup(name="prod", files=[".env"], example=".env.example")
        results = lint_file_group(g, base_dir=tmp_path)
        assert "B" in results[0]["missing_in_env"]

    def test_lint_missing_in_example(self, tmp_path):
        _write(tmp_path, ".env", "A=1\nB=2\n")
        _write(tmp_path, ".env.example", "A=\n")
        g = FileGroup(name="prod", files=[".env"], example=".env.example")
        results = lint_file_group(g, base_dir=tmp_path)
        assert "B" in results[0]["missing_in_example"]

    def test_lint_compare_between_files(self, tmp_path):
        _write(tmp_path, ".env", "A=1\nB=2\n")
        _write(tmp_path, ".env.local", "A=1\nC=3\n")
        g = FileGroup(name="dev", files=[".env", ".env.local"])
        results = lint_file_group(g, base_dir=tmp_path)
        assert len(results) == 2
        assert "keys_missing_vs" in results[0]
        assert any("C" in v for v in results[0]["keys_missing_vs"].values())
        assert "keys_missing_vs" in results[1]
        assert any("B" in v for v in results[1]["keys_missing_vs"].values())

    def test_lint_no_files(self, tmp_path):
        g = FileGroup(name="empty", files=[".env.nonexistent"])
        results = lint_file_group(g, base_dir=tmp_path)
        assert results == []

    def test_lint_single_file_no_compare(self, tmp_path):
        _write(tmp_path, ".env", "A=1\n")
        g = FileGroup(name="single", files=[".env"])
        results = lint_file_group(g, base_dir=tmp_path)
        assert len(results) == 1
        assert "keys_missing_vs" not in results[0]
