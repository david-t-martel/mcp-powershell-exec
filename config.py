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
            logger.warning(f"Configuration file not found: {file_path}")
            return cls()

        try:
            with open(file_path, "r") as f:
                if file_path.suffix.lower() in (".yml", ".yaml"):
                    try:
                        import yaml

                        config_data = yaml.safe_load(f)
                    except ImportError:
                        logger.warning("PyYAML not installed, falling back to JSON")
                        config_data = json.load(f)
                else:
                    config_data = json.load(f)

            return cls(**config_data)
        except Exception as e:
            logger.error(f"Error loading configuration from {file_path}: {e}")
            return cls()


# Global configuration instance
config = Config()


def initialize_config(
    config_file: Optional[str] = None, env_file: Optional[str] = None, **overrides
) -> Config:
    """Initialize configuration with optional file and overrides"""
    global config

    # Load from environment file if specified
    if env_file:
        os.environ["SETTINGS_ENV_FILE"] = env_file

    # Start with environment variables and defaults
    config = Config()

    # Load from config file if specified
    if config_file and os.path.exists(config_file):
        file_config = Config.load_from_file(config_file)
        for key, value in file_config.model_dump().items():
            setattr(config, key, value)

    # Apply any direct overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Create log directory if needed
    if not os.path.exists(config.logging.log_dir):
        os.makedirs(config.logging.log_dir, exist_ok=True)

    # Create command history directory if needed
    if config.logging.enable_command_logging:
        os.makedirs(config.logging.command_history_dir, exist_ok=True)

    return config


def get_config() -> Config:
    """Get the current configuration instance"""
    return config


def validate_config(config: Config) -> List[str]:
    """Validate configuration and return list of issues"""
    issues = []
    
    # Validate logging directory
    try:
        os.makedirs(config.logging.log_dir, exist_ok=True)
    except Exception as e:
        issues.append(f"Cannot create log directory '{config.logging.log_dir}': {e}")
    
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.logging.log_level.upper() not in valid_levels:
        issues.append(
            f"Invalid log level '{config.logging.log_level}'. "
            f"Must be one of: {', '.join(valid_levels)}"
        )
    
    # Validate execution policy
    valid_policies = [
        "Restricted", "AllSigned", "RemoteSigned",
        "Unrestricted", "Bypass", "Undefined"
    ]
    if config.security.execution_policy not in valid_policies:
        issues.append(
            f"Invalid execution policy '{config.security.execution_policy}'. "
            f"Must be one of: {', '.join(valid_policies)}"
        )
    
    # Validate timeout
    if config.security.command_timeout <= 0:
        issues.append("Command timeout must be greater than 0")
    
    # Validate max command length
    if config.security.max_command_length <= 0:
        issues.append("Max command length must be greater than 0")
    
    return issues
