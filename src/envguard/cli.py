from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.linter import compare_env_files
from envguard.linter import lint_files
from envguard.reporter import build_issues
from envguard.reporter import print_report
from envguard.reporter import Severity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="envguard",
        description="Lint and validate .env files.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Path(s) to .env file(s) to check.",
    )
    parser.add_argument(
        "--example",
        metavar="PATH",
        help="Compare .env with a .env.example file.",
    )
    parser.add_argument(
        "--check-secrets",
        action="store_true",
        help="Scan for secrets like API keys, tokens, and passwords.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (exit 1 on any issue).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "silent"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress output. Only return exit code.",
    )
    args = parser.parse_args(argv)

    if not args.files:
        print("Error: no files specified", file=sys.stderr)
        return 2

    for f in args.files:
        if not Path(f).exists():
            print(f"Error: file not found: {f}", file=sys.stderr)
            return 2

    if args.example and not Path(args.example).exists():
        print(f"Error: example file not found: {args.example}", file=sys.stderr)
        return 2

    from envguard.reporter import Issue

    reports = lint_files(args.files)
    all_issues: list[Issue] = []

    secrets_list = None
    if args.check_secrets:
        from envguard.secrets import scan_for_secrets
        all_entries = []
        for r in reports:
            all_entries.extend(r.entries)
        secrets_list = scan_for_secrets(all_entries)

    all_issues = build_issues(reports, secrets_list, strict=args.strict)

    if args.example:
        from envguard.reporter import Severity as Sev
        for env_file in args.files:
            result = compare_env_files(env_file, args.example)
            for key in result.missing_in_env:
                all_issues.append(Issue(
                    file=result.example_file,
                    line=0,
                    issue_type="MISSING_IN_ENV",
                    message=f"'{key}' is in .env.example but not in {result.env_file}",
                    key=key,
                    severity=Sev.ERROR,
                ))
            for key in result.missing_in_example:
                all_issues.append(Issue(
                    file=result.env_file,
                    line=0,
                    issue_type="MISSING_IN_EXAMPLE",
                    message=f"'{key}' is in {result.env_file} but not in {result.example_file}",
                    key=key,
                    severity=Sev.WARNING,
                ))

    fmt = "silent" if args.quiet else args.format
    print_report(all_issues, fmt=fmt)

    if not all_issues:
        return 0

    has_errors = any(i.severity == Severity.ERROR for i in all_issues)
    has_warnings = any(i.severity == Severity.WARNING for i in all_issues)

    if args.strict:
        return 1
    if has_errors:
        return 1
    if has_warnings:
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
