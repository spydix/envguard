from __future__ import annotations

from envguard.linter import EnvEntry
from envguard.secrets import detect_secret_in_value
from envguard.secrets import detect_secret_by_key_name
from envguard.secrets import scan_for_secrets


def test_detect_aws_access_key():
    results = detect_secret_in_value("AKIA1234567890ABCDEF")
    assert any(r[0] == "AWS Access Key" for r in results)


def test_detect_github_token():
    results = detect_secret_in_value("ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD")
    assert any(r[0] == "GitHub Token" for r in results)


def test_detect_api_key():
    results = detect_secret_by_key_name("API_KEY")
    assert any(r[0] == "Generic API Key" for r in results)


def test_detect_password_by_key():
    results = detect_secret_by_key_name("PASSWORD")
    assert any(r[0] == "Generic Password" for r in results)


def test_detect_secret_by_key():
    results = detect_secret_by_key_name("API_SECRET")
    assert any(r[0] == "Generic Secret" for r in results)


def test_detect_token_by_key():
    results = detect_secret_by_key_name("AUTH_TOKEN")
    assert any(r[0] == "Generic Token" for r in results)


def test_detect_no_secret_by_key():
    results = detect_secret_by_key_name("APP_NAME")
    assert results == []


def test_detect_jwt():
    results = detect_secret_in_value(
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc123def456ghi789jkl"
    )
    assert any(r[0] == "JWT Token" for r in results)


def test_detect_no_secret():
    results = detect_secret_in_value("just a regular value")
    assert results == []


def test_scan_for_secrets():
    entries = [
        EnvEntry("API_KEY", "ghp_1234567890abcdefghijklmnopqrstuvwxyzABCD", 1, False),
        EnvEntry("NAME", "myapp", 2, False),
    ]
    findings = scan_for_secrets(entries)
    assert len(findings) == 1
    assert findings[0].key == "API_KEY"
    assert findings[0].pattern_name == "GitHub Token"


def test_scan_password_by_key_name():
    """A key named PASSWORD with a real value should be flagged."""
    entries = [
        EnvEntry("PASSWORD", "supersecret123", 1, False),
    ]
    findings = scan_for_secrets(entries)
    assert len(findings) == 1
    assert findings[0].pattern_name == "Generic Password"


def test_scan_skips_placeholders():
    """Placeholder values should not be flagged."""
    entries = [
        EnvEntry("PASSWORD", "your-password-here", 1, False),
        EnvEntry("API_KEY", "xxx-replace-me", 2, False),
    ]
    findings = scan_for_secrets(entries)
    assert findings == []


def test_scan_skip_empty_values():
    """Empty values should not be flagged."""
    entries = [
        EnvEntry("PASSWORD", "", 1, True),
    ]
    findings = scan_for_secrets(entries)
    assert findings == []


def test_scan_no_secrets():
    entries = [
        EnvEntry("APP_NAME", "myapp", 1, False),
        EnvEntry("PORT", "8080", 2, False),
    ]
    findings = scan_for_secrets(entries)
    assert findings == []
