"""
Configuration management for MCP PowerShell Exec Server.

This module handles loading configuration from multiple sources:
- Configuration files (JSON/YAML)
- Environment variables
- Command line arguments
- Default values
"""

import json
import os
import yaml
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class SecurityConfig:
    """Security-related configuration settings."""
    require_api_key: bool = False
    api_keys: List[str] = field(default_factory=list)
    execution_policy: str = "Restricted"
    dangerous_patterns: List[str] = field(default_factory=lambda: [
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
        r"Invoke-Command\s+.*\s+-ScriptBlock",
        r"New-PSSession",
        r"Enter-PSSession",
        r"Enable-PSRemoting",
        r"Set-Item\s+WSMan:",
        r"Registry::",
        r"HKEY_",
        r"Get-Credential",
    ])
    blocked_commands: List[str] = field(default_factory=lambda: [
        "Format-Computer",
        "Remove-Computer", 
        "Reset-ComputerMachinePassword",
        "Restart-Computer",
        "Stop-Computer",
        "Checkpoint-Computer",
        "Restore-Computer",
        "Clear-RecycleBin",
        "Remove-Item",
        "rd",
        "rmdir",
        "del",
        "erase",
    ])
    max_command_length: int = 5000
    command_timeout: int = 30


@dataclass  
class ServerConfig:
    """Server-related configuration settings."""
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    default_timeout: int = 30
    max_concurrent_requests: int = 10


@dataclass
class LoggingConfig:
    """Logging-related configuration settings."""
    log_level: str = "INFO"
    log_format: str = "text"  # text, json
    log_dir: str = "logs"
    enable_command_logging: bool = True
    command_history_dir: str = "command_history"
    max_log_file_size: int = 10 * 1024 * 1024  # 10MB
    max_log_files: int = 5


@dataclass
class AppConfig:
    """Main application configuration."""
    app_name: str = "mcp-powershell-exec"
    version: str = "1.0.0"
    debug: bool = False
    security: SecurityConfig = field(default_factory=SecurityConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_config_file(file_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON or YAML file."""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.lower().endswith(('.yml', '.yaml')):
                return yaml.safe_load(f) or {}
            else:
                return json.load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load config file {file_path}: {e}")
        return {}


def load_env_vars(prefix: str = "MCP_PWSH_") -> Dict[str, Any]:
    """Load configuration from environment variables."""
    config = {}
    
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to config structure
            config_key = key[len(prefix):].lower()
            
            # Handle nested configuration (e.g., MCP_PWSH_SERVER__PORT)
            parts = config_key.split('__')
            current = config
            
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Convert string values to appropriate types
            final_key = parts[-1]
            try:
                # Try to parse as JSON (for lists, booleans, numbers)
                current[final_key] = json.loads(value)
            except (json.JSONDecodeError, ValueError):
                # Keep as string if not valid JSON
                current[final_key] = value
    
    return config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries."""
    result = {}
    
    for config in configs:
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_configs(result[key], value)
            else:
                result[key] = value
    
    return result


def create_config_from_dict(config_dict: Dict[str, Any]) -> AppConfig:
    """Create AppConfig instance from dictionary, handling nested structures."""
    # Create nested config objects
    security_data = config_dict.get('security', {})
    server_data = config_dict.get('server', {})
    logging_data = config_dict.get('logging', {})
    
    security_config = SecurityConfig(**{
        k: v for k, v in security_data.items() 
        if k in SecurityConfig.__dataclass_fields__
    })
    
    server_config = ServerConfig(**{
        k: v for k, v in server_data.items() 
        if k in ServerConfig.__dataclass_fields__
    })
    
    logging_config = LoggingConfig(**{
        k: v for k, v in logging_data.items() 
        if k in LoggingConfig.__dataclass_fields__
    })
    
    # Create main config
    main_data = {
        k: v for k, v in config_dict.items() 
        if k not in ['security', 'server', 'logging'] and k in AppConfig.__dataclass_fields__
    }
    
    return AppConfig(
        security=security_config,
        server=server_config,
        logging=logging_config,
        **main_data
    )


def initialize_config(
    config_file: Optional[str] = None,
    env_file: Optional[str] = None,
    **overrides
) -> AppConfig:
    """
    Initialize configuration from multiple sources.
    
    Priority order (highest to lowest):
    1. Direct overrides (keyword arguments)
    2. Environment variables
    3. Configuration file
    4. Default values
    """
    # Load .env file if specified
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)
    
    # Start with default configuration
    default_config = asdict(AppConfig())
    
    # Load from configuration file
    file_config = {}
    if config_file:
        file_config = load_config_file(config_file)
    else:
        # Try to find default config files
        for default_file in ['config.json', 'config.yaml', 'config.yml']:
            if os.path.exists(default_file):
                file_config = load_config_file(default_file)
                break
    
    # Load from environment variables
    env_config = load_env_vars()
    
    # Process command line overrides into nested structure
    override_config = {}
    for key, value in overrides.items():
        if '.' in key:
            # Handle nested keys like "server.port"
            parts = key.split('.')
            current = override_config
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            override_config[key] = value
    
    # Merge all configurations
    merged_config = merge_configs(
        default_config,
        file_config,
        env_config,
        override_config
    )
    
    return create_config_from_dict(merged_config)


def save_config(config: AppConfig, file_path: str, format: str = "json") -> None:
    """Save configuration to a file."""
    config_dict = asdict(config)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format.lower() in ['yml', 'yaml']:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        else:
            json.dump(config_dict, f, indent=2)


def validate_config(config: AppConfig) -> List[str]:
    """Validate configuration and return list of issues."""
    issues = []
    
    # Validate security settings
    if config.security.require_api_key and not config.security.api_keys:
        issues.append("API key authentication is required but no keys are configured")
    
    if config.security.command_timeout <= 0:
        issues.append("Command timeout must be greater than 0")
    
    if config.security.max_command_length <= 0:
        issues.append("Max command length must be greater than 0")
    
    # Validate server settings
    if not (1 <= config.server.port <= 65535):
        issues.append("Server port must be between 1 and 65535")
    
    if config.server.default_timeout <= 0:
        issues.append("Default timeout must be greater than 0")
    
    # Validate logging settings
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if config.logging.log_level.upper() not in valid_log_levels:
        issues.append(f"Log level must be one of: {', '.join(valid_log_levels)}")
    
    valid_log_formats = ['text', 'json']
    if config.logging.log_format not in valid_log_formats:
        issues.append(f"Log format must be one of: {', '.join(valid_log_formats)}")
    
    return issues


# Default instance for backward compatibility
config = AppConfig()


if __name__ == "__main__":
    # Example usage
    config = initialize_config()
    print("Current configuration:")
    print(json.dumps(asdict(config), indent=2))
    
    # Validate configuration
    issues = validate_config(config)
    if issues:
        print("\nConfiguration issues:")
        for issue in issues:
            print(f"  - {issue}")
