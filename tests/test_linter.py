from __future__ import annotations

from envguard.linter import EnvEntry
from envguard.linter import find_duplicates
from envguard.linter import find_empties
from envguard.linter import lint_file
from envguard.linter import parse_env_file

import tempfile
from pathlib import Path


def _write(tmp: Path, content: str) -> Path:
    f = tmp / ".env"
    f.write_text(content)
    return f


def test_parse_basic():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=value\nOTHER=hello\n")
        entries = parse_env_file(f)
        assert len(entries) == 2
        assert entries[0].key == "KEY"
        assert entries[0].value == "value"
        assert entries[1].key == "OTHER"
        assert entries[1].value == "hello"


def test_parse_case_sensitive():
    """Keys with different casing should be treated as separate keys."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "API_KEY=secret\napi_key=other\n")
        entries = parse_env_file(f)
        assert len(entries) == 2
        assert entries[0].key == "API_KEY"
        assert entries[1].key == "api_key"


def test_parse_comments_skipped():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "# comment\nKEY=val\n\n# another\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].key == "KEY"


def test_parse_quotes_stripped():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), 'KEY="value"\nSINGLE=\'val\'\n')
        entries = parse_env_file(f)
        assert entries[0].value == "value"
        assert entries[1].value == "val"


def test_parse_export_prefix():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "export KEY=value\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].key == "KEY"
        assert entries[0].value == "value"


def test_parse_empty_value():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].is_empty is True


def test_find_duplicates():
    entries = [
        EnvEntry("key", "a", 1, False),
        EnvEntry("key", "b", 5, False),
    ]
    dups = find_duplicates(entries)
    assert len(dups) == 1
    assert dups[0][0].line == 1
    assert dups[0][1].line == 5


def test_find_empties():
    entries = [
        EnvEntry("KEY", "", 1, True),
        EnvEntry("OTHER", "val", 2, False),
    ]
    empties = find_empties(entries)
    assert len(empties) == 1
    assert empties[0].key == "KEY"


def test_lint_file_clean():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=value\nOTHER=hello\n")
        report = lint_file(f)
        assert report.duplicates == []
        assert report.empties == []


def test_lint_file_with_issues():
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=value\nKEY=other\nEMPTY=\n")
        report = lint_file(f)
        assert len(report.duplicates) == 1
        assert len(report.empties) == 1
