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


def test_format_text_no_color():
    issues = [
        Issue(file="test.env", line=3, issue_type="ERROR",
              message="test", key="KEY", severity=Severity.ERROR),
    ]
    out = format_text(issues, no_color=True)
    assert "\033" not in out
    assert "ERROR" in out


# --- v2.0.0: ReportResult and summary tests ---

from envguard.reporter import ReportResult
from envguard.reporter import build_report
from envguard.reporter import format_summary


def test_report_result_is_clean():
    result = ReportResult(issues=[], files_checked=2)
    assert result.is_clean is True
    assert result.has_issues is False
    assert result.error_count == 0
    assert result.warning_count == 0


def test_report_result_has_errors_and_warnings():
    issues = [
        Issue(file="a.env", line=1, issue_type="DUPLICATE_KEY",
              message="dup", key="K", severity=Severity.ERROR),
        Issue(file="a.env", line=2, issue_type="EMPTY_VALUE",
              message="empty", key="E", severity=Severity.WARNING),
    ]
    result = ReportResult(issues=issues, files_checked=1)
    assert result.is_clean is False
    assert result.error_count == 1
    assert result.warning_count == 1


def test_report_result_group_by_file():
    issues = [
        Issue(file="a.env", line=1, issue_type="T1", message="m", key="K", severity=Severity.ERROR),
        Issue(file="b.env", line=2, issue_type="T2", message="m", key="J", severity=Severity.WARNING),
        Issue(file="a.env", line=3, issue_type="T3", message="m", key="L", severity=Severity.WARNING),
    ]
    result = ReportResult(issues=issues, files_checked=2)
    groups = result.group_by_file()
    assert set(groups.keys()) == {"a.env", "b.env"}
    assert len(groups["a.env"]) == 2
    assert len(groups["b.env"]) == 1


def test_report_result_to_summary_clean():
    result = ReportResult(issues=[], files_checked=3)
    s = result.to_summary()
    assert "No issues" in s
    assert "3 file(s)" in s


def test_report_result_to_summary_with_issues():
    issues = [
        Issue(file="a.env", line=1, issue_type="E", message="m", key="K", severity=Severity.ERROR),
        Issue(file="a.env", line=2, issue_type="W", message="m", key="J", severity=Severity.WARNING),
        Issue(file="a.env", line=3, issue_type="W2", message="m", key="L", severity=Severity.WARNING),
    ]
    result = ReportResult(issues=issues, files_checked=1)
    s = result.to_summary()
    assert "1 error(s)" in s
    assert "2 warning(s)" in s


def test_build_report():
    e1 = EnvEntry("KEY", "val1", 1, False)
    e2 = EnvEntry("KEY", "val2", 5, False)
    report = LintReport(
        file="test.env",
        duplicates=[(e1, e2)],
        empties=[],
        entries=[e1, e2],
    )
    result = build_report([report])
    assert result.files_checked == 1
    assert result.error_count == 1
    assert result.is_clean is False


def test_format_summary_clean():
    result = ReportResult(issues=[], files_checked=2)
    out = format_summary(result, no_color=True)
    assert "No issues found" in out
    assert "2 file(s)" in out


def test_format_summary_with_issues():
    issues = [
        Issue(file="a.env", line=1, issue_type="DUPLICATE_KEY",
              message="dup", key="K", severity=Severity.ERROR),
        Issue(file="a.env", line=2, issue_type="EMPTY_VALUE",
              message="empty", key="E", severity=Severity.WARNING),
        Issue(file="b.env", line=3, issue_type="SECRET",
              message="secret", key="TOKEN", severity=Severity.ERROR),
    ]
    result = ReportResult(issues=issues, files_checked=2)
    out = format_summary(result, no_color=True)
    assert "a.env" in out
    assert "b.env" in out
    assert "DUPLICATE_KEY" in out
    assert "SECRET" in out
    assert "2 error(s)" in out
    assert "1 warning(s)" in out
    assert "2 file(s)" in out


def test_format_summary_no_color():
    issues = [
        Issue(file="a.env", line=1, issue_type="ERR", message="m", key="K", severity=Severity.ERROR),
    ]
    result = ReportResult(issues=issues, files_checked=1)
    out = format_summary(result, no_color=True)
    assert "\033" not in out
