from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.linter import compare_env_files
from envguard.linter import lint_files
from envguard.secrets import scan_for_secrets


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

    found_issues = False

    reports = lint_files(args.files)

    for report in reports:
        for first, dup in report.duplicates:
            found_issues = True
            print(
                f"{report.file}:{dup.line}  DUPLICATE_KEY  "
                f"'{dup.key}' already defined on line {first.line}"
            )
        for entry in report.empties:
            found_issues = True
            print(
                f"{report.file}:{entry.line}  EMPTY_VALUE  "
                f"'{entry.key}' has an empty value"
            )

        if args.check_secrets:
            secrets = scan_for_secrets(report.entries)
            for s in secrets:
                found_issues = True
                print(
                    f"{report.file}:{s.line}  SECRET  "
                    f"'{s.key}' looks like a {s.pattern_name} (severity: {s.severity})"
                )

    if args.example:
        for env_file in args.files:
            result = compare_env_files(env_file, args.example)
            for key in result.missing_in_env:
                found_issues = True
                print(
                    f"{result.example_file}  MISSING_IN_ENV  "
                    f"'{key}' is in .env.example but not in {result.env_file}"
                )
            for key in result.missing_in_example:
                found_issues = True
                print(
                    f"{result.env_file}  MISSING_IN_EXAMPLE  "
                    f"'{key}' is in {result.env_file} but not in {result.example_file}"
                )

    if found_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
