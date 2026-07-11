from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SecretFinding:
    key: str
    value: str
    line: int
    pattern_name: str
    severity: str


PATTERNS: list[tuple[str, str, str, re.Pattern]] = [
    ("AWS Access Key", "high", r"AKIA[0-9A-Z]{16}", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Token", "high", r"gh[ps]_[A-Za-z0-9]{36}", re.compile(r"gh[ps]_[A-Za-z0-9]{36}")),
    ("GitLab Token", "high", r"glpat-[A-Za-z0-9]{20}", re.compile(r"glpat-[A-Za-z0-9]{20}")),
    ("Slack Token", "high", r"xox[baprs]-[A-Za-z0-9-]{10,}", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Private Key Block", "high", r"-----BEGIN.+PRIVATE KEY-----", re.compile(r"-----BEGIN.+PRIVATE KEY-----")),
    ("JWT Token", "high", r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]

KEY_NAME_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("Generic API Key", "medium", re.compile(r"api[_-]?key", re.I)),
    ("Generic Password", "medium", re.compile(r"pass(word|wd)?", re.I)),
    ("Generic Secret", "medium", re.compile(r"secret", re.I)),
    ("Generic Token", "medium", re.compile(r"token", re.I)),
    ("AWS Secret Key", "high", re.compile(r"aws[_-]?secret", re.I)),
]


def detect_secret_in_value(value: str) -> list[tuple[str, str]]:
    """Check if a value looks like a secret based on value patterns.
    Returns list of (pattern_name, severity).
    """
    findings: list[tuple[str, str]] = []
    for name, severity, _desc, pattern in PATTERNS:
        if pattern.search(value):
            findings.append((name, severity))
    return findings


def detect_secret_by_key_name(key: str) -> list[tuple[str, str]]:
    """Check if a key name suggests it holds a secret.
    Returns list of (pattern_name, severity).
    """
    findings: list[tuple[str, str]] = []
    for name, severity, pattern in KEY_NAME_PATTERNS:
        if pattern.search(key):
            findings.append((name, severity))
    return findings


def scan_for_secrets(entries) -> list:
    """Scan entries for secrets. Returns list of SecretFinding.

    A value is flagged as a secret if:
    - It matches a value pattern (AWS key, GitHub token, JWT, etc.)
    - OR its key name matches a secret-related name (password, token, secret,
      api_key) AND the value is non-empty and not a placeholder.
    """
    from envguard.linter import EnvEntry
    findings: list[SecretFinding] = []
    for entry in entries:
        if entry.is_empty:
            continue
        # Skip obvious placeholders
        placeholder_markers = ("your-", "xxx", "changeme", "placeholder", "<", "example")
        if any(m in entry.value.lower() for m in placeholder_markers):
            continue
        results = detect_secret_in_value(entry.value)
        if not results:
            key_results = detect_secret_by_key_name(entry.key)
            results = key_results
        for name, severity in results:
            findings.append(SecretFinding(
                key=entry.key,
                value=entry.value,
                line=entry.line,
                pattern_name=name,
                severity=severity,
            ))
    return findings
