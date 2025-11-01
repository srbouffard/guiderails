"""Configuration management for GuideRails verbosity and output controls."""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class VerbosityLevel(Enum):
    """Verbosity levels for output control."""
    
    QUIET = "quiet"
    NORMAL = "normal"
    VERBOSE = "verbose"
    DEBUG = "debug"
    
    @classmethod
    def from_string(cls, value: str) -> "VerbosityLevel":
        """Convert string to VerbosityLevel."""
        try:
            return cls(value.lower())
        except ValueError:
            return cls.NORMAL


@dataclass
class OutputConfig:
    """Configuration for output behavior and verbosity."""
    
    # Verbosity level
    verbosity: VerbosityLevel = VerbosityLevel.NORMAL
    
    # Toggle flags for specific output types
    show_commands: bool = True
    show_substituted: bool = True
    show_expected: bool = True
    show_captured: bool = True
    show_timestamps: bool = False
    show_step_banners: bool = True
    show_previews: bool = True
    
    # CI mode flag
    is_ci: bool = False
    
    # Output format
    output_format: str = "text"  # text or jsonl
    
    def __post_init__(self):
        """Apply verbosity level presets after initialization."""
        self._apply_verbosity_presets()
    
    def _apply_verbosity_presets(self):
        """Apply default settings based on verbosity level."""
        if self.verbosity == VerbosityLevel.QUIET:
            # Minimal output
            self.show_step_banners = False
            self.show_previews = False
            self.show_timestamps = False
            self.show_substituted = False
        elif self.verbosity == VerbosityLevel.NORMAL:
            # Default behavior (current)
            self.show_step_banners = True
            self.show_previews = False
            self.show_timestamps = False
            self.show_substituted = False
        elif self.verbosity == VerbosityLevel.VERBOSE:
            # Show more details
            self.show_step_banners = True
            self.show_previews = True
            self.show_timestamps = True
            self.show_substituted = True
        elif self.verbosity == VerbosityLevel.DEBUG:
            # Show everything
            self.show_step_banners = True
            self.show_previews = True
            self.show_timestamps = True
            self.show_substituted = True
    
    @classmethod
    def from_cli_and_env(
        cls,
        verbosity: Optional[str] = None,
        quiet: bool = False,
        verbose_count: int = 0,
        debug: bool = False,
        is_ci: bool = False,
        output_format: Optional[str] = None,
        # Toggle overrides
        show_commands: Optional[bool] = None,
        show_substituted: Optional[bool] = None,
        show_expected: Optional[bool] = None,
        show_captured: Optional[bool] = None,
        show_timestamps: Optional[bool] = None,
        show_step_banners: Optional[bool] = None,
        show_previews: Optional[bool] = None,
    ) -> "OutputConfig":
        """Create OutputConfig from CLI arguments and environment variables.
        
        Precedence: CLI flags > environment vars > config file > defaults
        
        Args:
            verbosity: Explicit verbosity level (quiet/normal/verbose/debug)
            quiet: --quiet flag
            verbose_count: Count of -v flags (0, 1, 2, 3+)
            debug: --debug flag
            is_ci: CI mode flag
            output_format: Output format (text or jsonl)
            show_*: Toggle overrides (None means not specified)
        
        Returns:
            OutputConfig instance
        """
        # Start with defaults from config file (if exists)
        config = cls._load_config_file()
        
        # Determine verbosity level from CLI or environment
        level = cls._determine_verbosity_level(
            verbosity, quiet, verbose_count, debug,
            config.verbosity if config else None
        )
        
        # Create base config with determined level
        result = config if config else cls()
        result.verbosity = level
        result.is_ci = is_ci
        
        # Apply CI defaults only if verbosity wasn't explicitly set anywhere
        env_verbosity = os.environ.get("GUIDERAILS_VERBOSITY")
        if (is_ci and verbosity is None and not quiet and verbose_count == 0 
            and not debug and not env_verbosity and 
            (not config or config.verbosity == VerbosityLevel.NORMAL)):
            # CI defaults to quiet unless explicitly set
            result.verbosity = VerbosityLevel.QUIET
        
        # Apply verbosity presets
        result._apply_verbosity_presets()
        
        # Apply environment variable overrides
        result._apply_env_overrides()
        
        # Apply CLI toggle overrides (highest precedence)
        if show_commands is not None:
            result.show_commands = show_commands
        if show_substituted is not None:
            result.show_substituted = show_substituted
        if show_expected is not None:
            result.show_expected = show_expected
        if show_captured is not None:
            result.show_captured = show_captured
        if show_timestamps is not None:
            result.show_timestamps = show_timestamps
        if show_step_banners is not None:
            result.show_step_banners = show_step_banners
        if show_previews is not None:
            result.show_previews = show_previews
        
        # Set output format
        if output_format:
            result.output_format = output_format
        
        return result
    
    @classmethod
    def _determine_verbosity_level(
        cls,
        verbosity: Optional[str],
        quiet: bool,
        verbose_count: int,
        debug: bool,
        config_level: Optional[VerbosityLevel],
    ) -> VerbosityLevel:
        """Determine verbosity level from various sources.
        
        Precedence:
        1. Explicit --verbosity flag
        2. --quiet, -v, -vv, -vvv, --debug flags
        3. GUIDERAILS_VERBOSITY environment variable
        4. Config file verbosity
        5. Default (NORMAL)
        """
        # 1. Explicit verbosity flag
        if verbosity:
            return VerbosityLevel.from_string(verbosity)
        
        # 2. Convenience flags
        if debug:
            return VerbosityLevel.DEBUG
        if quiet:
            return VerbosityLevel.QUIET
        if verbose_count >= 3:
            return VerbosityLevel.DEBUG
        if verbose_count == 2:
            return VerbosityLevel.VERBOSE
        if verbose_count == 1:
            return VerbosityLevel.VERBOSE
        
        # 3. Environment variable
        env_verbosity = os.environ.get("GUIDERAILS_VERBOSITY")
        if env_verbosity:
            return VerbosityLevel.from_string(env_verbosity)
        
        # 4. Config file
        if config_level:
            return config_level
        
        # 5. Default
        return VerbosityLevel.NORMAL
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides for toggle flags."""
        env_vars = {
            "GUIDERAILS_SHOW_COMMANDS": "show_commands",
            "GUIDERAILS_SHOW_SUBSTITUTED": "show_substituted",
            "GUIDERAILS_SHOW_EXPECTED": "show_expected",
            "GUIDERAILS_SHOW_CAPTURED": "show_captured",
            "GUIDERAILS_TIMESTAMPS": "show_timestamps",
            "GUIDERAILS_STEP_BANNERS": "show_step_banners",
            "GUIDERAILS_PREVIEWS": "show_previews",
        }
        
        for env_var, attr_name in env_vars.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Parse boolean value
                bool_value = value.lower() in ("true", "1", "yes", "on")
                setattr(self, attr_name, bool_value)
    
    @classmethod
    def _load_config_file(cls) -> Optional["OutputConfig"]:
        """Load configuration from guiderails.yml if it exists.
        
        Searches for guiderails.yml in current directory and parent directories.
        
        Returns:
            OutputConfig from file, or None if not found or YAML not available
        """
        if not HAS_YAML:
            return None
        
        # Search for guiderails.yml in current and parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            config_file = parent / "guiderails.yml"
            if config_file.exists():
                return cls._parse_config_file(config_file)
        
        return None
    
    @classmethod
    def _parse_config_file(cls, config_file: Path) -> Optional["OutputConfig"]:
        """Parse guiderails.yml configuration file.
        
        Args:
            config_file: Path to configuration file
        
        Returns:
            OutputConfig instance or None if parsing fails
        """
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            
            if not isinstance(data, dict):
                return None
            
            # Extract configuration
            config = cls()
            
            # Set verbosity level
            if "verbosity" in data:
                config.verbosity = VerbosityLevel.from_string(data["verbosity"])
            
            # Set toggle flags
            toggle_flags = [
                "show_commands",
                "show_substituted",
                "show_expected",
                "show_captured",
                "show_timestamps",
                "show_step_banners",
                "show_previews",
            ]
            
            for flag in toggle_flags:
                if flag in data and isinstance(data[flag], bool):
                    setattr(config, flag, data[flag])
            
            return config
        
        except Exception:
            # If parsing fails, return None and use defaults
            return None
    
    def should_show_at_level(self, min_level: VerbosityLevel) -> bool:
        """Check if current verbosity level is at least the minimum level.
        
        Args:
            min_level: Minimum verbosity level required
        
        Returns:
            True if current level >= min_level
        """
        levels = [VerbosityLevel.QUIET, VerbosityLevel.NORMAL, 
                  VerbosityLevel.VERBOSE, VerbosityLevel.DEBUG]
        current_idx = levels.index(self.verbosity)
        min_idx = levels.index(min_level)
        return current_idx >= min_idx
