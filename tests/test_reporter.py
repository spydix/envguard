from __future__ import annotations

import json

from envguard.linter import EnvEntry
from envguard.linter import LintReport
from envguard.reporter import build_issues
from envguard.reporter import format_json
from envguard.reporter import format_text
from envguard.reporter import Issue
from envguard.reporter import Severity


def _make_report(dups=(), empties=()):
    return LintReport(
        file="test.env",
        duplicates=list(dups),
        empties=list(empties),
        entries=[],
    )


def test_build_issues_duplicates():
    e1 = EnvEntry("KEY", "val1", 1, False)
    e2 = EnvEntry("KEY", "val2", 5, False)
    report = _make_report(dups=[(e1, e2)])
    issues = build_issues([report], strict=False)
    assert len(issues) == 1
    assert issues[0].issue_type == "DUPLICATE_KEY"
    assert issues[0].severity == Severity.ERROR


def test_build_issues_empties_not_strict():
    e = EnvEntry("KEY", "", 3, True)
    report = _make_report(empties=[e])
    issues = build_issues([report], strict=False)
    assert len(issues) == 1
    assert issues[0].severity == Severity.WARNING


def test_build_issues_empties_strict():
    e = EnvEntry("KEY", "", 3, True)
    report = _make_report(empties=[e])
    issues = build_issues([report], strict=True)
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR


def test_format_json_output():
    issues = [
        Issue(file="test.env", line=3, issue_type="DUPLICATE_KEY",
              message="test", key="KEY", severity=Severity.ERROR),
    ]
    out = format_json(issues)
    parsed = json.loads(out)
    assert len(parsed) == 1
    assert parsed[0]["type"] == "DUPLICATE_KEY"
    assert parsed[0]["severity"] == "error"


def test_format_text_output():
    issues = [
        Issue(file="test.env", line=3, issue_type="EMPTY_VALUE",
              message="test", key="KEY", severity=Severity.WARNING),
    ]
    out = format_text(issues)
    assert "EMPTY_VALUE" in out
    assert "test.env" in out


def test_format_text_empty():
    out = format_text([])
    assert out == ""
