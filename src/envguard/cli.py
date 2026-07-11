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
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )
    parser.add_argument(
        "--envignore",
        metavar="PATH",
        help="Path to .envignore file. Keys listed there are skipped.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix the file: sort keys, remove duplicates. Creates a .bak backup.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip creating a .bak backup when using --fix.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to .envguard.toml config file. Defaults to ./.envguard.toml.",
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

    from envguard.config import load_config, merge_config
    from envguard.reporter import Issue
    from envguard.linter import load_envignore
    from envguard.linter import filter_entries

    config = load_config(args.config)

    cli_args_dict = {
        "strict": args.strict,
        "check_secrets": args.check_secrets,
        "format": args.format,
        "no_color": args.no_color,
        "no_backup": args.no_backup,
        "envignore": args.envignore,
        "example": args.example,
    }
    merged = merge_config(cli_args_dict, config)

    strict = merged["strict"]
    check_secrets = merged["check_secrets"]
    fmt_val = merged["format"]
    no_color = merged["no_color"]
    no_backup = merged["no_backup"]
    envignore_path = merged["envignore"]
    example_path = merged["example"]

    ignored_keys: set[str] = set()
    if envignore_path:
        ignored_keys = load_envignore(envignore_path)

    if args.fix:
        from envguard.fixer import fix_env_file
        for f in args.files:
            backup = fix_env_file(
                f,
                sort_keys=True,
                deduplicate=True,
                backup=not no_backup,
            )
            if backup:
                print(f"Fixed {f}. Backup saved to {backup}")
            else:
                print(f"Fixed {f}.")
        return 0

    reports = lint_files(args.files)

    if ignored_keys:
        for report in reports:
            report.entries = filter_entries(report.entries, ignored_keys)
            report.duplicates = [
                (f, d) for f, d in report.duplicates
                if f.key not in ignored_keys and d.key not in ignored_keys
            ]
            report.empties = [
                e for e in report.empties if e.key not in ignored_keys
            ]

    all_issues: list[Issue] = []

    secrets_list = None
    if check_secrets:
        from envguard.secrets import scan_for_secrets
        all_entries = []
        for r in reports:
            all_entries.extend(r.entries)
        secrets_list = scan_for_secrets(all_entries)

    all_issues = build_issues(reports, secrets_list, strict=strict)

    if example_path:
        if not Path(example_path).exists():
            print(f"Error: example file not found: {example_path}", file=sys.stderr)
            return 2
        from envguard.reporter import Severity as Sev
        for env_file in args.files:
            result = compare_env_files(env_file, example_path)
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
                    message=f"'{key}' is in {result.env_file} but not in .env.example",
                    key=key,
                    severity=Sev.WARNING,
                ))

    fmt = "silent" if args.quiet else fmt_val
    print_report(all_issues, fmt=fmt, no_color=no_color)

    if not all_issues:
        return 0

    has_errors = any(i.severity == Severity.ERROR for i in all_issues)

    if strict:
        return 1
    if has_errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
