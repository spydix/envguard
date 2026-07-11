# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
