from __future__ import annotations

from envguard.linter import EnvEntry
from envguard.linter import compare_env_files
from envguard.linter import find_duplicates
from envguard.linter import find_empties
from envguard.linter import lint_file
from envguard.linter import parse_env_file

import tempfile
from pathlib import Path


def _write(tmp: Path, content: str, name: str = ".env") -> Path:
    f = tmp / name
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


def test_parse_multiline():
    """Multiline values with backslash continuation should be joined."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "PRIVATE_KEY=-----BEGIN\\\nPRIVATE KEY-----\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert "BEGIN" in entries[0].value
        assert "PRIVATE KEY" in entries[0].value


def test_parse_inline_comment_unquoted():
    """Inline comments after unquoted values should be stripped."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=value # this is a comment\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].value == "value"


def test_parse_inline_comment_quoted():
    """Inline comments after quoted values should be stripped."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), 'KEY="value # not a comment"\n')
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert "value" in entries[0].value
        assert "# not a comment" in entries[0].value


def test_parse_no_inline_comment_in_url():
    """Hash in a URL should not be treated as a comment."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "URL=http://example.com/page#section\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].value == "http://example.com/page#section"


def test_parse_hash_without_space_not_comment():
    """Hash without preceding space should not be treated as a comment."""
    with tempfile.TemporaryDirectory() as d:
        f = _write(Path(d), "KEY=val#ue\n")
        entries = parse_env_file(f)
        assert len(entries) == 1
        assert entries[0].value == "val#ue"


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


def test_compare_no_diff():
    with tempfile.TemporaryDirectory() as d:
        env = _write(Path(d), "KEY=val\nOTHER=hello\n", ".env")
        example = _write(Path(d), "KEY=val\nOTHER=hello\n", ".env.example")
        result = compare_env_files(env, example)
        assert result.missing_in_env == []
        assert result.missing_in_example == []


def test_compare_missing_in_env():
    with tempfile.TemporaryDirectory() as d:
        env = _write(Path(d), "KEY=val\n", ".env")
        example = _write(Path(d), "KEY=val\nREDIS_URL=redis://\n", ".env.example")
        result = compare_env_files(env, example)
        assert "REDIS_URL" in result.missing_in_env
        assert result.missing_in_example == []


def test_compare_missing_in_example():
    with tempfile.TemporaryDirectory() as d:
        env = _write(Path(d), "KEY=val\nSECRET=xyz\n", ".env")
        example = _write(Path(d), "KEY=val\n", ".env.example")
        result = compare_env_files(env, example)
        assert result.missing_in_env == []
        assert "SECRET" in result.missing_in_example


def test_compare_preserves_order():
    """Comparison output should preserve the order keys appear in the file."""
    with tempfile.TemporaryDirectory() as d:
        env = _write(Path(d), "A=1\nB=2\nC=3\n", ".env")
        example = _write(Path(d), "C=3\nD=4\n", ".env.example")
        result = compare_env_files(env, example)
        assert result.missing_in_env == ["D"]
        assert result.missing_in_example == ["A", "B"]
