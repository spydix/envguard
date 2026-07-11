from __future__ import annotations

import tempfile
from pathlib import Path

from envguard.cli import main


def _write(tmp: Path, content: str, name: str = ".env") -> Path:
    f = tmp / name
    f.write_text(content)
    return f


def test_cli_no_issues():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=value\nOTHER=hello\n")
        ret = main([str(Path(d) / ".env")])
        assert ret == 0


def test_cli_finds_duplicates():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=value\nKEY=other\n")
        ret = main([str(Path(d) / ".env")])
        assert ret == 1


def test_cli_finds_empties():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "EMPTY=\n")
        ret = main([str(Path(d) / ".env"), "--strict"])
        assert ret == 1


def test_cli_empties_warning_no_strict():
    """Without --strict, empty values are warnings and return 0."""
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "EMPTY=\n")
        ret = main([str(Path(d) / ".env")])
        assert ret == 0


def test_cli_file_not_found():
    ret = main(["nonexistent.env"])
    assert ret == 2


def test_cli_compare_with_example():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=val\n", ".env")
        _write(Path(d), "KEY=val\nREDIS_URL=redis://\n", ".env.example")
        ret = main([str(Path(d) / ".env"), "--example", str(Path(d) / ".env.example")])
        assert ret == 1


def test_cli_compare_no_diff():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=val\n", ".env")
        _write(Path(d), "KEY=val\n", ".env.example")
        ret = main([str(Path(d) / ".env"), "--example", str(Path(d) / ".env.example")])
        assert ret == 0


def test_cli_strict_mode():
    """In strict mode, empty values should cause exit 1."""
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "EMPTY=\n")
        ret = main([str(Path(d) / ".env"), "--strict"])
        assert ret == 1


def test_cli_json_format():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=value\nKEY=other\n")
        ret = main([str(Path(d) / ".env"), "--format", "json"])
        assert ret == 1


def test_cli_quiet():
    with tempfile.TemporaryDirectory() as d:
        _write(Path(d), "KEY=value\nKEY=other\n")
        ret = main([str(Path(d) / ".env"), "--quiet"])
        assert ret == 1
