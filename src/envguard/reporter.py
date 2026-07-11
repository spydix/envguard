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

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == Severity.WARNING)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def is_clean(self) -> bool:
        return len(self.issues) == 0

    def group_by_file(self) -> dict[str, list[Issue]]:
        """Group issues by file path."""
        groups: dict[str, list[Issue]] = {}
        for issue in self.issues:
            groups.setdefault(issue.file, []).append(issue)
        return groups

    def to_summary(self) -> str:
        """Return a one-line summary string."""
        if self.is_clean:
            return f"No issues found in {self.files_checked} file(s)."
        parts: list[str] = []
        if self.error_count:
            parts.append(f"{self.error_count} error(s)")
        if self.warning_count:
            parts.append(f"{self.warning_count} warning(s)")
        return f"{', '.join(parts)} in {self.files_checked} file(s)."


def build_report(
    reports: list[LintReport],
    secrets: list[SecretFinding] | None = None,
    strict: bool = False,
) -> ReportResult:
    """Build a ReportResult from lint reports and secret findings."""
    issues = build_issues(reports, secrets, strict=strict)
    return ReportResult(
        issues=issues,
        files_checked=len(reports),
    )


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


def format_summary(result: ReportResult, no_color: bool = False) -> str:
    """Format a ReportResult as a summary with per-file breakdown."""
    GREEN = "" if no_color else "\033[92m"
    RED = "" if no_color else "\033[91m"
    YELLOW = "" if no_color else "\033[93m"
    RESET = "" if no_color else "\033[0m"
    BOLD = "" if no_color else "\033[1m"

    if result.is_clean:
        return f"{GREEN}{BOLD}No issues found{RESET} in {result.files_checked} file(s)."

    lines: list[str] = []

    by_file = result.group_by_file()
    for file_path in sorted(by_file):
        file_issues = by_file[file_path]
        errors = sum(1 for i in file_issues if i.severity == Severity.ERROR)
        warnings = sum(1 for i in file_issues if i.severity == Severity.WARNING)
        parts: list[str] = []
        if errors:
            parts.append(f"{RED}{errors} error(s){RESET}")
        if warnings:
            parts.append(f"{YELLOW}{warnings} warning(s){RESET}")
        lines.append(f"{BOLD}{file_path}{RESET}: {', '.join(parts)}")
        for issue in file_issues:
            color = RED if issue.severity == Severity.ERROR else YELLOW
            loc = f":{issue.line}" if issue.line else ""
            lines.append(f"  {color}{issue.issue_type}{RESET}  {issue.key}{loc}  {issue.message}")

    lines.append("")
    lines.append(result.to_summary())

    return "\n".join(lines)


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
