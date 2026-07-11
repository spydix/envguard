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
    ("AWS Secret Key", "high", r"aws_secret_access_key", re.compile(r"aws_secret_access_key\s*=\s*\S+", re.I)),
    ("GitHub Token", "high", r"gh[ps]_[A-Za-z0-9]{36}", re.compile(r"gh[ps]_[A-Za-z0-9]{36}")),
    ("GitLab Token", "high", r"glpat-[A-Za-z0-9]{20}", re.compile(r"glpat-[A-Za-z0-9]{20}")),
    ("Slack Token", "high", r"xox[baprs]-[A-Za-z0-9-]{10,}", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Generic API Key", "medium", r"api[_-]?key\s*=\s*\S{8,}", re.compile(r"api[_-]?key\s*=\s*\S{8,}", re.I)),
    ("Generic Password", "medium", r"password\s*=\s*\S{1,}", re.compile(r"password\s*=\s*\S{1,}", re.I)),
    ("Generic Secret", "medium", r"secret\s*=\s*\S{8,}", re.compile(r"secret\s*=\s*\S{8,}", re.I)),
    ("Generic Token", "medium", r"token\s*=\s*\S{8,}", re.compile(r"token\s*=\s*\S{8,}", re.I)),
    ("Private Key Block", "high", r"-----BEGIN.+PRIVATE KEY-----", re.compile(r"-----BEGIN.+PRIVATE KEY-----")),
    ("JWT Token", "high", r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
]


def detect_secret_in_value(value: str) -> list[tuple[str, str]]:
    """Check if a value looks like a secret. Returns list of (pattern_name, severity)."""
    findings: list[tuple[str, str]] = []
    for name, severity, _desc, pattern in PATTERNS:
        if pattern.search(value):
            findings.append((name, severity))
    return findings


def scan_for_secrets(entries) -> list:
    """Scan entries for secrets. Returns list of SecretFinding."""
    from envguard.linter import EnvEntry
    findings: list[SecretFinding] = []
    for entry in entries:
        # BUG: we run detection on the raw line text, not just the value.
        # This means if a comment contains "password" it will be flagged.
        # Will be fixed in 0.3.1.
        results = detect_secret_in_value(entry.value)
        for name, severity in results:
            findings.append(SecretFinding(
                key=entry.key,
                value=entry.value,
                line=entry.line,
                pattern_name=name,
                severity=severity,
            ))
    return findings
