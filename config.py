"""
Configuration management for MCP PowerShell Exec Server.

This module provides a central configuration system that supports:
- Default values
- Environment variable overrides
- Configuration file (YAML/JSON) overrides
- Command-line argument overrides
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional, Union

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Set up logger
logger = logging.getLogger("mcp.config")


class SecurityConfig(BaseModel):
    """Security configuration settings"""

    dangerous_patterns: List[str] = Field(
        default=[
            r"rm\s+-Recurse",
            r"Remove-Item\s+.*\s+-Recurse",
            r"Format-Volume",
            r"Clear-Disk",
            r"Reset-ComputerMachinePassword",
            r"Invoke-Expression.*Invoke-WebRequest",
            r"Start-Process.*-Verb\s+RunAs",
            r"New-Service",
            r"Stop-Service",
            r"Set-ExecutionPolicy\s+Unrestricted",
        ],
        description="Regular expression patterns for dangerous commands",
    )
    api_keys: List[str] = Field(
        default=[],
        description="List of valid API keys (empty list means no authentication)",
    )
    require_api_key: bool = Field(
        default=False,
        description="Whether API key authentication is required",
    )
    execution_policy: str = Field(
        default="Restricted",
        description="PowerShell execution policy (Restricted, RemoteSigned, etc.)",
    )
    max_command_length: int = Field(
        default=10000,
        description="Maximum length of PowerShell commands in characters",
    )
    command_timeout: int = Field(
        default=30,
        description="Command execution timeout in seconds",
    )
    blocked_commands: List[str] = Field(
        default=[
            "Format-Computer",
            "Remove-Computer",
            "Reset-ComputerMachinePassword",
            "Restart-Computer",
            "Stop-Computer",
        ],
        description="List of explicitly blocked command names",
    )


class LoggingConfig(BaseModel):
    """Logging configuration settings"""

    log_dir: str = Field(
        default="logs",
        description="Directory for log files",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="text",
        description="Log format (text, json)",
    )
    command_history_dir: str = Field(
        default="command_history",
        description="Directory for command history files",
    )
    enable_command_logging: bool = Field(
        default=True,
        description="Whether to save command history to files",
    )


class ServerConfig(BaseModel):
    """Server configuration settings"""

    host: str = Field(
        default="127.0.0.1",
        description="Host to bind the server to",
    )
    port: int = Field(
        default=8000,
        description="Port to run the server on",
    )
    cors_origins: List[str] = Field(
        default=["*"],
        description="List of allowed CORS origins, or ['*'] for any origin",
    )
    default_timeout: int = Field(
        default=30,
        description="Default timeout for PowerShell commands (seconds)",
    )


class Config(BaseSettings):
    """Main configuration class"""

    model_config = SettingsConfigDict(
        env_prefix="MCP_PWSH_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app_name: str = Field(
        default="mcp-powershell-exec",
        description="Application name",
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration",
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration",
    )
    server: ServerConfig = Field(
        default_factory=ServerConfig,
        description="Server configuration",
    )

    @classmethod
    def load_from_file(cls, file_path: Union[str, Path]) -> "Config":
        """Load configuration from a JSON or YAML file"""
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning("Configuration file not found: %s", file_path)
            return cls()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() in (".yml", ".yaml"):
                    if yaml is not None:
                        config_data = yaml.safe_load(f)
                    else:
                        logger.warning("PyYAML not installed, falling back to JSON")
                        config_data = json.load(f)
                else:
                    config_data = json.load(f)

            return cls(**config_data)
        except (FileNotFoundError, PermissionError, OSError) as e:
            logger.error("Error loading configuration from %s: %s", file_path, e)
            return cls()


class ConfigManager:
    """Configuration manager singleton"""

    _instance: Optional[Config] = None

    @classmethod
    def get_instance(cls) -> Config:
        """Get the configuration instance"""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def set_instance(cls, config: Config) -> None:
        """Set the configuration instance"""
        cls._instance = config


def initialize_config(
    config_file: Optional[str] = None,
    env_file: Optional[str] = None,
    **overrides: Union[str, int, bool, List[str]],
) -> Config:
    """Initialize configuration with optional file and overrides"""
    # Load from environment file if specified
    if env_file:
        os.environ["SETTINGS_ENV_FILE"] = env_file

    # Start with environment variables and defaults
    config_instance = Config()

    # Load from config file if specified
    if config_file and os.path.exists(config_file):
        file_config = Config.load_from_file(config_file)
        for key, value in file_config.model_dump().items():
            setattr(config_instance, key, value)

    # Apply any direct overrides
    for key, value in overrides.items():
        if hasattr(config_instance, key):
            setattr(config_instance, key, value)

    # Create log directory if needed
    # Pydantic v2 nested model access may trigger false mypy warnings
    logging_config = config_instance.logging
    log_dir = getattr(logging_config, "log_dir", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    # Create command history directory if needed
    enable_cmd_logging = getattr(logging_config, "enable_command_logging", True)
    if enable_cmd_logging:
        cmd_history_dir = getattr(
            logging_config, "command_history_dir", "command_history"
        )
        os.makedirs(cmd_history_dir, exist_ok=True)

    # Store in the manager
    ConfigManager.set_instance(config_instance)
    return config_instance


def get_config() -> Config:
    """Get the current configuration instance"""
    return ConfigManager.get_instance()


def validate_config(config_instance: Config) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []

    # Validate logging directory
    try:
        os.makedirs(config_instance.logging.log_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        issues.append(
            f"Cannot create log directory '{config_instance.logging.log_dir}': {e}"
        )

    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config_instance.logging.log_level.upper() not in valid_levels:
        issues.append(
            f"Invalid log level '{config_instance.logging.log_level}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        )

    # Validate execution policy
    valid_policies = [
        "Restricted",
        "AllSigned",
        "RemoteSigned",
        "Unrestricted",
        "Bypass",
        "Undefined",
    ]
    if config_instance.security.execution_policy not in valid_policies:
        issues.append(
            f"Invalid execution policy '{config_instance.security.execution_policy}'. "
            f"Must be one of: {', '.join(valid_policies)}"
        )

    # Validate timeout
    if config_instance.security.command_timeout <= 0:
        issues.append("Command timeout must be greater than 0")

    # Validate max command length
    if config_instance.security.max_command_length <= 0:
        issues.append("Max command length must be greater than 0")

    return issues
