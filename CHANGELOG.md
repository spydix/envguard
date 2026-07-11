# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-04-03

### Fixed
- Multiline values (lines ending with backslash) are now properly joined
  instead of being truncated at the first line. This was breaking PEM keys
  and SQL queries stored in .env files.
  Reported by a user who had their private key split across multiple lines
  and the parser only captured the first line.

### Added
- Test for multiline value parsing.

## [0.1.1] - 2025-03-22

### Fixed
- Key comparison is now case-sensitive. `API_KEY` and `api_key` are treated
  as two separate keys, not duplicates. This was causing false-positive
  duplicate warnings in projects that use mixed casing conventions.
  Reported by a user who had `DATABASE_URL` and `database_url` in the same
  file on purpose (one for the app, one for the migration tool).

### Added
- Test for case-sensitive key parsing.

## [0.1.0] - 2025-03-15

### Added
- Basic `.env` file parser that handles comments, quoted values, and exports
- Duplicate key detection with line numbers
- Empty value detection
- `envguard` CLI entry point
- Exit codes: 0 for clean, 1 for issues found
- Apache 2.0 license
- Initial test suite (8 tests)
- GitHub Actions CI for Python 3.9 through 3.12

### Known issues
- Key comparison is case-insensitive, so `API_KEY` and `api_key` are treated
  as duplicates of each other. This will be fixed in 0.1.1.
- Multiline values (lines ending with backslash) are truncated at the first
  line. This will be fixed in 0.1.2.
