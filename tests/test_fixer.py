from __future__ import annotations

import tempfile
from pathlib import Path

from envguard.fixer import fix_env_file


def _write(tmp: Path, content: str, name: str = ".env") -> Path:
    f = tmp / name
    f.write_text(content)
    return f


def test_fix_sorts_keys():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "ZEBRA=1\nAPPLE=2\nMANGO=3\n")
        fix_env_file(f, sort_keys=True, backup=False)
        content = f.read_text()
        lines = content.strip().split("\n")
        assert lines[0].startswith("APPLE")
        assert lines[1].startswith("MANGO")
        assert lines[2].startswith("ZEBRA")


def test_fix_deduplicates():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=first\nKEY=second\nKEY=third\n")
        fix_env_file(f, sort_keys=False, deduplicate=True, backup=False)
        content = f.read_text()
        assert "third" in content
        assert "first" not in content
        assert "second" not in content
        assert content.count("KEY=") == 1


def test_fix_creates_backup():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=val\n")
        backup = fix_env_file(f, sort_keys=True, backup=True)
        assert Path(backup).exists()
        assert Path(backup).read_text().strip() == "KEY=val"


def test_fix_no_backup():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=val\n")
        backup = fix_env_file(f, sort_keys=True, backup=False)
        assert backup == ""
        assert not (Path(d) / ".env.bak").exists()


def test_fix_preserves_last_value():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=old\nKEY=new\n")
        fix_env_file(f, sort_keys=False, deduplicate=True, backup=False)
        content = f.read_text()
        assert "new" in content
        assert "old" not in content


def test_fix_sort_and_deduplicate():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "ZEBRA=1\nAPPLE=2\nZEBRA=3\nAPPLE=4\n")
        fix_env_file(f, sort_keys=True, deduplicate=True, backup=False)
        content = f.read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert lines[0] == "APPLE=4"
        assert lines[1] == "ZEBRA=3"


def test_fix_preserves_inline_comment():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=value # this is a comment\n")
        fix_env_file(f, sort_keys=True, backup=False)
        content = f.read_text()
        assert "KEY=value" in content
        assert "# this is a comment" in content


def test_fix_preserves_comment_lines():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "# top comment\nKEY=value\n# another comment\n")
        fix_env_file(f, sort_keys=True, backup=False)
        content = f.read_text()
        assert "# top comment" in content
        assert "# another comment" in content
        assert "KEY=value" in content


def test_fix_preserves_empty_value_with_inline_comment():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY= # commented empty\n")
        fix_env_file(f, sort_keys=True, backup=False)
        content = f.read_text()
        assert "KEY=" in content
        assert "# commented empty" in content


def test_fix_strips_export_prefix():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "export KEY=value\n")
        fix_env_file(f, sort_keys=True, backup=False)
        content = f.read_text()
        assert "KEY=value" in content
        assert "export" not in content
