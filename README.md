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

### Strict mode

In strict mode, empty values are treated as errors (exit code 1) instead of
warnings (exit code 0):

```sh
envguard .env --strict
```

### JSON output

For CI pipelines and programmatic use:

```sh
envguard .env --format json
```

### Auto-fix: sort and deduplicate

```sh
envguard .env --fix
```

This merges duplicate keys (keeping the last value) and sorts them
alphabetically. The original file is backed up to `.env.bak` before any
changes are made.

### Config file

Create `.envguard.toml` in your project root:

```toml
[envguard]
strict = true
format = "text"
check_secrets = true
ignore_values = ["DEV_PASSWORD"]
```

### .envignore

Create a `.envignore` file to skip certain keys from checks:

```
DEV_PASSWORD
LOCAL_TOKEN
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0    | No issues found |
| 1    | Issues found (errors in strict mode, or any problem) |
| 2    | File not found or read error |

## Pre-commit hook

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/spydix/envguard
    rev: v2.0.0
    hooks:
      - id: envguard
        args: ['--strict']
```

## Why not just use shell scripts?

You can. People do. But shell scripts that grep through env files break on
multiline values, quoted strings, comments, and edge cases that envguard
handles correctly because it actually parses the file instead of running
regex on it.

## License

Apache License 2.0. See [LICENSE](LICENSE) for the full text.
