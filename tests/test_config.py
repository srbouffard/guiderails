"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest

from guiderails.config import OutputConfig, VerbosityLevel


def test_verbosity_level_from_string():
    """Test converting strings to VerbosityLevel."""
    assert VerbosityLevel.from_string("quiet") == VerbosityLevel.QUIET
    assert VerbosityLevel.from_string("QUIET") == VerbosityLevel.QUIET
    assert VerbosityLevel.from_string("normal") == VerbosityLevel.NORMAL
    assert VerbosityLevel.from_string("verbose") == VerbosityLevel.VERBOSE
    assert VerbosityLevel.from_string("debug") == VerbosityLevel.DEBUG
    # Invalid values default to normal
    assert VerbosityLevel.from_string("invalid") == VerbosityLevel.NORMAL


def test_output_config_defaults():
    """Test default OutputConfig values."""
    config = OutputConfig()
    assert config.verbosity == VerbosityLevel.NORMAL
    assert config.show_commands is True
    assert config.show_substituted is False
    assert config.show_expected is True
    assert config.show_captured is True
    assert config.show_timestamps is False
    assert config.show_step_banners is True
    assert config.show_previews is False
    assert config.is_ci is False
    assert config.output_format == "text"


def test_verbosity_presets_quiet():
    """Test quiet mode presets."""
    config = OutputConfig(verbosity=VerbosityLevel.QUIET)
    assert config.show_step_banners is False
    assert config.show_previews is False
    assert config.show_timestamps is False
    assert config.show_substituted is False


def test_verbosity_presets_normal():
    """Test normal mode presets."""
    config = OutputConfig(verbosity=VerbosityLevel.NORMAL)
    assert config.show_step_banners is True
    assert config.show_previews is False
    assert config.show_timestamps is False
    assert config.show_substituted is False


def test_verbosity_presets_verbose():
    """Test verbose mode presets."""
    config = OutputConfig(verbosity=VerbosityLevel.VERBOSE)
    assert config.show_step_banners is True
    assert config.show_previews is True
    assert config.show_timestamps is True
    assert config.show_substituted is True


def test_verbosity_presets_debug():
    """Test debug mode presets."""
    config = OutputConfig(verbosity=VerbosityLevel.DEBUG)
    assert config.show_step_banners is True
    assert config.show_previews is True
    assert config.show_timestamps is True
    assert config.show_substituted is True


def test_from_cli_explicit_verbosity():
    """Test creating config from explicit verbosity flag."""
    config = OutputConfig.from_cli_and_env(verbosity="quiet")
    assert config.verbosity == VerbosityLevel.QUIET

    config = OutputConfig.from_cli_and_env(verbosity="verbose")
    assert config.verbosity == VerbosityLevel.VERBOSE


def test_from_cli_quiet_flag():
    """Test creating config from --quiet flag."""
    config = OutputConfig.from_cli_and_env(quiet=True)
    assert config.verbosity == VerbosityLevel.QUIET


def test_from_cli_verbose_count():
    """Test creating config from -v flags."""
    config = OutputConfig.from_cli_and_env(verbose_count=1)
    assert config.verbosity == VerbosityLevel.VERBOSE

    config = OutputConfig.from_cli_and_env(verbose_count=2)
    assert config.verbosity == VerbosityLevel.VERBOSE

    config = OutputConfig.from_cli_and_env(verbose_count=3)
    assert config.verbosity == VerbosityLevel.DEBUG


def test_from_cli_debug_flag():
    """Test creating config from --debug flag."""
    config = OutputConfig.from_cli_and_env(debug=True)
    assert config.verbosity == VerbosityLevel.DEBUG


def test_from_cli_ci_defaults_to_quiet():
    """Test that CI mode defaults to quiet unless explicitly set."""
    config = OutputConfig.from_cli_and_env(is_ci=True)
    assert config.verbosity == VerbosityLevel.QUIET
    assert config.is_ci is True


def test_from_cli_ci_with_verbose():
    """Test that CI mode can be overridden with verbose flag."""
    config = OutputConfig.from_cli_and_env(is_ci=True, verbose_count=1)
    assert config.verbosity == VerbosityLevel.VERBOSE
    assert config.is_ci is True


def test_from_cli_toggle_overrides():
    """Test that CLI toggle flags override verbosity presets."""
    # Start with quiet (show_commands would be True by default)
    config = OutputConfig.from_cli_and_env(verbosity="quiet", show_commands=False)
    assert config.verbosity == VerbosityLevel.QUIET
    assert config.show_commands is False

    # Start with verbose (show_previews would be True)
    config = OutputConfig.from_cli_and_env(verbosity="verbose", show_previews=False)
    assert config.verbosity == VerbosityLevel.VERBOSE
    assert config.show_previews is False


def test_env_var_verbosity(monkeypatch):
    """Test GUIDERAILS_VERBOSITY environment variable."""
    monkeypatch.setenv("GUIDERAILS_VERBOSITY", "quiet")
    config = OutputConfig.from_cli_and_env()
    assert config.verbosity == VerbosityLevel.QUIET

    monkeypatch.setenv("GUIDERAILS_VERBOSITY", "verbose")
    config = OutputConfig.from_cli_and_env()
    assert config.verbosity == VerbosityLevel.VERBOSE


def test_env_var_toggles(monkeypatch):
    """Test environment variable toggle flags."""
    monkeypatch.setenv("GUIDERAILS_SHOW_COMMANDS", "false")
    config = OutputConfig.from_cli_and_env()
    assert config.show_commands is False

    monkeypatch.setenv("GUIDERAILS_SHOW_COMMANDS", "true")
    config = OutputConfig.from_cli_and_env()
    assert config.show_commands is True

    monkeypatch.setenv("GUIDERAILS_TIMESTAMPS", "1")
    config = OutputConfig.from_cli_and_env()
    assert config.show_timestamps is True


def test_cli_precedence_over_env(monkeypatch):
    """Test that CLI flags take precedence over environment variables."""
    monkeypatch.setenv("GUIDERAILS_VERBOSITY", "quiet")
    config = OutputConfig.from_cli_and_env(verbosity="verbose")
    assert config.verbosity == VerbosityLevel.VERBOSE

    monkeypatch.setenv("GUIDERAILS_SHOW_COMMANDS", "false")
    config = OutputConfig.from_cli_and_env(show_commands=True)
    assert config.show_commands is True


def test_config_file_loading(tmp_path):
    """Test loading configuration from guiderails.yml."""
    # Create a config file
    config_file = tmp_path / "guiderails.yml"
    config_file.write_text("""
verbosity: verbose
show_commands: false
show_expected: false
show_timestamps: true
""")

    # Change to directory with config file
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        config = OutputConfig._load_config_file()
        
        assert config is not None
        assert config.verbosity == VerbosityLevel.VERBOSE
        assert config.show_commands is False
        assert config.show_expected is False
        assert config.show_timestamps is True
    finally:
        os.chdir(original_dir)


def test_should_show_at_level():
    """Test should_show_at_level method."""
    quiet_config = OutputConfig(verbosity=VerbosityLevel.QUIET)
    assert quiet_config.should_show_at_level(VerbosityLevel.QUIET) is True
    assert quiet_config.should_show_at_level(VerbosityLevel.NORMAL) is False
    assert quiet_config.should_show_at_level(VerbosityLevel.VERBOSE) is False
    assert quiet_config.should_show_at_level(VerbosityLevel.DEBUG) is False

    verbose_config = OutputConfig(verbosity=VerbosityLevel.VERBOSE)
    assert verbose_config.should_show_at_level(VerbosityLevel.QUIET) is True
    assert verbose_config.should_show_at_level(VerbosityLevel.NORMAL) is True
    assert verbose_config.should_show_at_level(VerbosityLevel.VERBOSE) is True
    assert verbose_config.should_show_at_level(VerbosityLevel.DEBUG) is False


def test_precedence_order(tmp_path, monkeypatch):
    """Test full precedence order: CLI > env > config file > defaults."""
    # Set up config file
    config_file = tmp_path / "guiderails.yml"
    config_file.write_text("""
verbosity: normal
show_commands: true
""")

    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Config file only
        config = OutputConfig.from_cli_and_env()
        assert config.verbosity == VerbosityLevel.NORMAL
        assert config.show_commands is True
        
        # Config file + env var (env wins)
        monkeypatch.setenv("GUIDERAILS_VERBOSITY", "quiet")
        config = OutputConfig.from_cli_and_env()
        assert config.verbosity == VerbosityLevel.QUIET
        
        # Config file + env var + CLI (CLI wins)
        config = OutputConfig.from_cli_and_env(verbosity="debug")
        assert config.verbosity == VerbosityLevel.DEBUG
        
        # Toggle precedence
        monkeypatch.setenv("GUIDERAILS_SHOW_COMMANDS", "false")
        config = OutputConfig.from_cli_and_env(show_commands=True)
        assert config.show_commands is True
        
    finally:
        os.chdir(original_dir)
