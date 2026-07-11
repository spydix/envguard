import os
import tempfile
from pathlib import Path

import pytest

from envguard.config import load_config, merge_config, DEFAULT_CONFIG


class TestLoadConfig:
    def test_no_config_file_returns_defaults(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config = load_config()
        assert config == DEFAULT_CONFIG

    def test_load_config_from_file(self, tmp_path):
        config_file = tmp_path / ".envguard.toml"
        config_file.write_text(
            "[envguard]\nstrict = true\ncheck_secrets = true\nformat = \"json\"\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config["strict"] is True
        assert config["check_secrets"] is True
        assert config["format"] == "json"

    def test_load_partial_config(self, tmp_path):
        config_file = tmp_path / ".envguard.toml"
        config_file.write_text(
            "[envguard]\nstrict = true\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config["strict"] is True
        assert config["check_secrets"] is False
        assert config["format"] == "text"

    def test_nonexistent_file_returns_defaults(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.toml")
        assert config == DEFAULT_CONFIG

    def test_no_envguard_section_uses_top_level(self, tmp_path):
        config_file = tmp_path / ".envguard.toml"
        config_file.write_text(
            "strict = true\ncheck_secrets = true\n",
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config["strict"] is True
        assert config["check_secrets"] is True

    def test_envignore_path_from_config(self, tmp_path):
        config_file = tmp_path / ".envguard.toml"
        config_file.write_text(
            '[envguard]\nenvignore = ".envignore"\n',
            encoding="utf-8",
        )
        config = load_config(config_file)
        assert config["envignore"] == ".envignore"


class TestMergeConfig:
    def test_cli_overrides_config(self):
        cli_args = {
            "strict": True,
            "check_secrets": True,
            "format": "json",
            "no_color": False,
            "no_backup": False,
            "envignore": ".myignore",
            "example": None,
        }
        config = {
            "strict": False,
            "check_secrets": False,
            "format": "text",
            "no_color": False,
            "no_backup": False,
            "envignore": ".otherignore",
            "example": ".env.example",
        }
        merged = merge_config(cli_args, config)
        assert merged["strict"] is True
        assert merged["check_secrets"] is True
        assert merged["format"] == "json"
        assert merged["envignore"] == ".myignore"

    def test_config_used_when_cli_not_set(self):
        cli_args = {
            "strict": False,
            "check_secrets": False,
            "format": "text",
            "no_color": False,
            "no_backup": False,
            "envignore": None,
            "example": None,
        }
        config = {
            "strict": True,
            "check_secrets": True,
            "format": "json",
            "no_color": True,
            "no_backup": True,
            "envignore": ".envignore",
            "example": ".env.example",
        }
        merged = merge_config(cli_args, config)
        assert merged["strict"] is True
        assert merged["check_secrets"] is True
        assert merged["format"] == "json"
        assert merged["no_color"] is True
        assert merged["no_backup"] is True
        assert merged["envignore"] == ".envignore"
        assert merged["example"] == ".env.example"

    def test_cli_format_overrides_config(self):
        cli_args = {
            "strict": False,
            "check_secrets": False,
            "format": "silent",
            "no_color": False,
            "no_backup": False,
            "envignore": None,
            "example": None,
        }
        config = {
            "strict": False,
            "check_secrets": False,
            "format": "json",
            "no_color": False,
            "no_backup": False,
            "envignore": None,
            "example": None,
        }
        merged = merge_config(cli_args, config)
        assert merged["format"] == "silent"

    def test_merge_all_defaults(self):
        cli_args = dict(DEFAULT_CONFIG)
        config = dict(DEFAULT_CONFIG)
        merged = merge_config(cli_args, config)
        assert merged == DEFAULT_CONFIG
