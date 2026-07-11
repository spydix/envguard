# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-15

### Added
- **File groups**: Define groups of .env files in `.envguard.toml` to lint
  and compare together. Useful for multi-environment setups like
  `.env`, `.env.local`, `.env.production`.
  ```toml
  [[envguard.file_groups]]
  name = "production"
  files = [".env", ".env.production"]
  example = ".env.example"
  ```
- New `groups` module with `FileGroup`, `load_file_groups()`, and
  `lint_file_group()` functions.
- `--format summary` option: shows a per-file breakdown of errors and
  warnings with a footer summary line.
- `ReportResult` dataclass with `error_count`, `warning_count`,
  `is_clean`, `has_issues`, `group_by_file()`, `to_summary()`.
- `build_report()` function that returns a `ReportResult` object.
- `format_summary()` function for structured summary output.
- Cross-file comparison: when a file group has multiple files, envguard
  reports keys that are present in one file but missing in another.

### Changed
- Refactored reporter module to support `ReportResult` with richer
  metadata while keeping backward compatibility with `build_issues()`
  and `print_report()`.
- `--format` now accepts `summary` as a fourth option.
- Bumped version to 2.0.0. The public API from 1.x is still supported.
  The `build_issues()` and `print_report()` functions remain unchanged.
  New code should use `build_report()` and `format_summary()` instead.

### Tests
- 96 tests passing (22 new tests for groups and reporter).

## [1.3.1] - 2025-11-02

### Fixed
- `--fix` now preserves inline comments (e.g. `KEY=value # comment`) instead
  of dropping them during sort/deduplicate.
- `--fix` now preserves standalone comment lines (`# ...`) instead of
  removing them from the file.
- `--fix` now strips the `export ` prefix so that `export KEY=value` is
  normalized to `KEY=value` in the fixed output.

### Added
- Tests for inline comment preservation, standalone comments, empty value
  with inline comment, and export prefix stripping in the fixer.

## [1.3.0] - 2025-10-18

### Added
- `.envguard.toml` config file support. Define default settings for
  `strict`, `check_secrets`, `format`, `no_color`, `no_backup`,
  `envignore`, and `example` in a TOML file. CLI flags override config
  file values.
- `--config PATH` flag to specify a custom config file location.
- New `config` module with `load_config()` and `merge_config()` functions.
- pre-commit hook support via `.pre-commit-hooks.yaml`. Use envguard as
  a pre-commit hook in your repository.
- Tests for config loading and merging logic.

## [1.2.0] - 2025-09-12

### Added
- `--fix` flag: automatically fixes common issues in .env files.
  Sorts keys alphabetically, removes duplicate keys (keeps last value),
  and creates a backup of the original file before writing changes.
- `--no-backup` flag: skips backup creation when using `--fix`.
- New `fixer` module with `fix_env_file()` function.
- Tests for the fixer module covering sorting, deduplication, backup
  creation, backup skip, and preserving last values.

## [1.1.0] - 2025-08-05

### Added
- `.envignore` support. Create a `.envignore` file listing key names to
  skip during linting. Use `--envignore PATH` to specify the file.
- `--no-color` flag to disable colored output. Useful for CI environments
  that do not support ANSI escape codes.
- `load_envignore()` and `filter_entries()` functions in the linter module.
- Tests for envignore loading and entry filtering.

## [1.0.0] - 2025-07-10

### Added
- Stable public API. The `envguard` CLI and the `envguard.linter`,
  `envguard.secrets`, and `envguard.reporter` modules are now considered
  stable and will not have breaking changes within the 1.x series.
- Color output for text format: errors in red, warnings in yellow.
- `--strict` flag: treats warnings as errors (exit 1 on any issue).
- `--format` flag with choices: `text` (default), `json`, `silent`.
- `--quiet` flag: suppresses all output, only returns exit code.
- New `reporter` module with structured issue reporting:
  - `Issue` dataclass with file, line, type, message, key, severity.
  - `Severity` enum: ERROR and WARNING.
  - `build_issues()` to construct issues from lint reports and secrets.
  - `format_text()`, `format_json()`, `print_report()` for output.
- Empty values are now warnings by default, errors in strict mode.
- Duplicate keys are always errors.
- Secret findings with high severity are errors, medium are warnings.

### Changed
- CLI refactored to use the new reporter module.
- Exit code logic is now: 0 (no issues), 1 (any error, or any issue in
  strict mode), 2 (file not found).
- JSON output uses proper structured format with severity levels.

## [0.3.2] - 2025-06-15

### Fixed
- Inline comments in unquoted values are now properly stripped. Previously a
  `#` anywhere in the value would truncate it, even mid-word. Now only a `#`
  preceded by whitespace is treated as a comment marker for unquoted values.
  Quoted values preserve `#` as part of the value.
  Reported by a user whose URL value `http://example.com/page#section` was
  being cut to `http://example.com/page`.

### Added
- Tests for inline comment stripping (unquoted, quoted, URLs, hash-without-space).

## [0.3.1] - 2025-06-02

### Fixed
- Secret detection no longer produces false positives from comments.
  Previously the "password" pattern used a regex that matched `password=`
  anywhere in the raw line text, including comments. Now detection is split
  into two separate checks:
  - Value patterns: match the actual value against known formats (AWS keys,
    GitHub tokens, JWT, private keys, etc.)
  - Key name patterns: match the key name against secret-related names
    (password, token, secret, api_key) and only flag if the value is
    non-empty and not a placeholder.
- Placeholder values (your-, xxx, changeme, placeholder, <, example) are
  now skipped and not flagged as secrets.

### Added
- `detect_secret_by_key_name()` function for key-name based detection.
- Tests for key-name detection, placeholder skipping, and empty value skipping.

## [0.3.0] - 2025-05-18

### Added
- Secret detection module with patterns for AWS keys, GitHub tokens,
  GitLab tokens, Slack tokens, JWT tokens, private key blocks, and generic
  API keys / passwords / secrets / tokens.
- `--check-secrets` CLI flag to enable secret scanning.
- Severity levels: high and medium.
- Tests for secret detection patterns.

### Known issues
- Secret detection runs on values but the password pattern uses
  case-insensitive regex which matches the word "password" even in
  comments that happen to be on the same line as a key=value pair.
  This causes false positives. Will be fixed in 0.3.1.
- Values containing `#` (inline comments) are truncated at the `#`
  symbol, losing part of the value. Will be fixed in 0.3.2.

## [0.2.1] - 2025-05-01

### Fixed
- Key ordering in comparison output is now deterministic. Keys are returned
  in the order they appear in the file, not in random set order. The
  `get_keys` function now preserves first-seen order. Comparison results
  no longer jump around between runs.

### Added
- Test for deterministic key ordering in comparison output.

## [0.2.0] - 2025-04-20

### Added
- Compare `.env` with `.env.example` using `--example` flag.
- Reports keys missing in env but present in example (MISSING_IN_ENV).
- Reports keys missing in example but present in env (MISSING_IN_EXAMPLE).
- Tests for comparison functionality.

### Known issues
- Key ordering in comparison output is non-deterministic because keys are
  stored in a set internally. The output order may change between runs.
  This will be fixed in 0.2.1.

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
