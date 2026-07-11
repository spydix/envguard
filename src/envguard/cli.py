from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envguard.linter import lint_files


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
    args = parser.parse_args(argv)

    if not args.files:
        print("Error: no files specified", file=sys.stderr)
        return 2

    for f in args.files:
        if not Path(f).exists():
            print(f"Error: file not found: {f}", file=sys.stderr)
            return 2

    reports = lint_files(args.files)
    found_issues = False

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

    if found_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
