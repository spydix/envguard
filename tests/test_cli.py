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
        ret = main([str(Path(d) / ".env")])
        assert ret == 1


def test_cli_file_not_found():
    ret = main(["nonexistent.env"])
    assert ret == 2
