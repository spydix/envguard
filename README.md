# envguard

A linter and validator for `.env` files.

## The problem

You have a `.env` file. Maybe several. There are duplicate keys because someone
added `DATABASE_URL` at the top and then another one at the bottom. One of the
values is empty. A teammate committed an API key by accident. The `.env.example`
is out of sync with the real `.env` because nobody remembers to update it.

This happens in every project that uses `.env` files. It happens in your project
right now.

## What envguard does

envguard scans your `.env` files and finds:

- **Duplicate keys** - two entries with the same name, where the second one
  silently overrides the first. This is the most common and the most dangerous
  issue because it breaks things in production without any error message.
- **Empty values** - `API_KEY=` with nothing after the equals sign. Usually
  means someone forgot to fill it in or deleted the value by accident.
- **Missing keys** - keys that exist in `.env.example` but not in your `.env`,
  or the other way around. Catches drift between what the app expects and what
  is actually configured.
- **Secrets in plaintext** - looks for values that match patterns of API keys,
  tokens, passwords, and private keys. Flags them so you know what is sitting
  in your repo unencrypted.

## Installation

```sh
pip install envguard
```

Or with pipx:

```sh
pipx install envguard
```

## Usage

### Basic lint

Scan a single file:

```sh
envguard .env
```

Output:

```
.env:3  DUPLICATE_KEY   'DATABASE_URL' already defined on line 1
.env:5  EMPTY_VALUE     'API_KEY' has an empty value
```

### Compare with .env.example

```sh
envguard .env --example .env.example
```

Output:

```
.env:3  DUPLICATE_KEY       'DATABASE_URL' already defined on line 1
.env:5  EMPTY_VALUE         'API_KEY' has an empty value
.env.example  MISSING_IN_ENV       'REDIS_URL' is in .env.example but not in .env
.env          MISSING_IN_EXAMPLE   'SECRET_KEY' is in .env but not in .env.example
```

### Secret detection

Scan for secrets like API keys, tokens, passwords, and private keys:

```sh
envguard .env --check-secrets
```

Detects AWS access keys, GitHub tokens, GitLab tokens, Slack tokens, JWT
tokens, private key blocks, and flag suspicious key names like `password`,
`secret`, `token`, and `api_key`.

### Strict mode

In strict mode, empty values are treated as errors (exit code 1) instead of
warnings (exit code 0):

```sh
envguard .env --strict
```

### Output formats

Four output formats are available:

```sh
envguard .env --format text      # default, colored
envguard .env --format json      # machine-readable JSON
envguard .env --format silent    # no output, exit code only
envguard .env --format summary   # per-file breakdown with summary
```

Summary output example:

```
a.env: 2 error(s)
  DUPLICATE_KEY  K:2  'K' already defined on line 1
  SECRET  TOKEN:5  'TOKEN' looks like a GitHub Token
b.env: 1 warning(s)
  EMPTY_VALUE  E:3  'E' has an empty value

3 error(s), 1 warning(s) in 2 file(s).
```

### Auto-fix: sort and deduplicate

```sh
envguard .env --fix
```

This merges duplicate keys (keeping the last value) and sorts them
alphabetically. The original file is backed up to `.env.bak` before any
changes are made. Skip the backup with `--no-backup`.

Comment lines and inline comments are preserved during fix.

### Config file

Create `.envguard.toml` in your project root:

```toml
[envguard]
strict = true
format = "summary"
check_secrets = true
```

CLI flags override config file values. Use `--config PATH` to specify a
custom config file location.

### .envignore

Create a `.envignore` file to skip certain keys from checks:

```
DEV_PASSWORD
LOCAL_TOKEN
```

Use `--envignore PATH` to specify a custom path.

### File groups

Define groups of `.env` files to lint and compare together in `.envguard.toml`:

```toml
[[envguard.file_groups]]
name = "production"
files = [".env", ".env.production"]
example = ".env.example"
```

This allows cross-file comparison. If `.env.production` has a key that `.env`
does not, envguard reports it. Useful for multi-environment setups where
`.env`, `.env.local`, and `.env.production` should share a common set of keys.

### Pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/spydix/envguard
    rev: v2.0.0
    hooks:
      - id: envguard
        args: ['--strict']
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | No issues found |
| 1    | Issues found (errors, or any issue in strict mode) |
| 2    | File not found or read error |

## API

envguard can be used as a library:

```python
from envguard.linter import lint_file, parse_env_file, compare_env_files
from envguard.secrets import scan_for_secrets
from envguard.reporter import build_report, format_summary
from envguard.fixer import fix_env_file
from envguard.config import load_config, merge_config
from envguard.groups import FileGroup, lint_file_group

# Parse entries
entries = parse_env_file(".env")
for entry in entries:
    print(f"{entry.key} = {entry.value} (line {entry.line})")

# Lint
report = lint_file(".env")
if report.duplicates:
    print(f"Found {len(report.duplicates)} duplicate keys")

# Compare
result = compare_env_files(".env", ".env.example")
print(f"Missing: {result.missing_in_env}")

# Scan for secrets
findings = scan_for_secrets(entries)
for f in findings:
    print(f"Secret: {f.key} matches {f.pattern_name}")

# Build report and print summary
result = build_report([report], findings, strict=False)
print(format_summary(result))

# Fix
backup = fix_env_file(".env", sort_keys=True, backup=True)
```

## Why not just use shell scripts?

You can. People do. But shell scripts that grep through env files break on
multiline values, quoted strings, comments, and edge cases that envguard
handles correctly because it actually parses the file instead of running
regex on it.

## License

Apache License 2.0. See [LICENSE](LICENSE) for the full text.
