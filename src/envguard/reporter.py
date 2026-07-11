from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from envguard.linter import LintReport
from envguard.secrets import SecretFinding


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Issue:
    file: str
    line: int
    issue_type: str
    message: str
    key: str = ""
    severity: Severity = Severity.WARNING


@dataclass
class ReportResult:
    issues: list[Issue] = field(default_factory=list)
    files_checked: int = 0

    @property
    def has_errors(self) -> bool:
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == Severity.WARNING for i in self.issues)


def build_issues(
    reports: list[LintReport],
    secrets: list[SecretFinding] | None = None,
    strict: bool = False,
) -> list[Issue]:
    """Build a list of Issue objects from lint reports and secret findings."""
    issues: list[Issue] = []

    for report in reports:
        for first, dup in report.duplicates:
            issues.append(Issue(
                file=report.file,
                line=dup.line,
                issue_type="DUPLICATE_KEY",
                message=f"'{dup.key}' already defined on line {first.line}",
                key=dup.key,
                severity=Severity.ERROR,
            ))
        for entry in report.empties:
            sev = Severity.ERROR if strict else Severity.WARNING
            issues.append(Issue(
                file=report.file,
                line=entry.line,
                issue_type="EMPTY_VALUE",
                message=f"'{entry.key}' has an empty value",
                key=entry.key,
                severity=sev,
            ))

    if secrets:
        for s in secrets:
            sev = Severity.ERROR if s.severity == "high" else Severity.WARNING
            issues.append(Issue(
                file="",
                line=s.line,
                issue_type="SECRET",
                message=f"'{s.key}' looks like a {s.pattern_name}",
                key=s.key,
                severity=sev,
            ))

    return issues


def format_text(issues: list[Issue], no_color: bool = False) -> str:
    """Format issues as colored text output."""
    RED = "" if no_color else "\033[91m"
    YELLOW = "" if no_color else "\033[93m"
    RESET = "" if no_color else "\033[0m"
    BOLD = "" if no_color else "\033[1m"

    lines: list[str] = []
    for issue in issues:
        color = RED if issue.severity == Severity.ERROR else YELLOW
        line_prefix = f"{issue.file}:{issue.line}" if issue.line else issue.file
        lines.append(
            f"{color}{BOLD}{issue.issue_type}{RESET}  "
            f"{line_prefix}  {issue.message}{RESET}"
        )
    return "\n".join(lines)


def format_json(issues: list[Issue]) -> str:
    """Format issues as JSON for programmatic use."""
    return json.dumps([
        {
            "file": i.file,
            "line": i.line,
            "type": i.issue_type,
            "key": i.key,
            "message": i.message,
            "severity": i.severity.value,
        }
        for i in issues
    ], indent=2)


def format_silent(issues: list[Issue]) -> str:
    """No output, just return issues count."""
    return ""


def print_report(
    issues: list[Issue],
    fmt: str = "text",
    stream=None,
    no_color: bool = False,
) -> None:
    """Print issues in the specified format."""
    if stream is None:
        stream = sys.stdout

    if not issues:
        if fmt == "text":
            print("No issues found.", file=stream)
        elif fmt == "json":
            print("[]", file=stream)
        return

    if fmt == "json":
        print(format_json(issues), file=stream)
    elif fmt == "text":
        print(format_text(issues, no_color=no_color), file=stream)
