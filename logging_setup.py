"""
Logging configuration for MCP PowerShell Exec Server.

This module provides structured logging capabilities with support for:
- Different log levels
- JSON or text formatting
- File or console output
- Log rotation
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union, Any

# Import config without creating circular dependency
# We'll use the module's get_config() only when needed
import config as config_module


class JsonFormatter(logging.Formatter):
    """
    Formatter for JSON logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        # Add extra fields
        if hasattr(record, "data") and isinstance(record.data, dict):
            log_record.update(record.data)

        return json.dumps(log_record)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_dir: Optional[str] = None,
    app_name: str = "mcp-powershell-exec",
) -> None:
    """
    Set up logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ("text" or "json")
        log_dir: Directory for log files (if None, logs to console only)
        app_name: Name of the application (used for log file naming)
    """
    # Get numeric log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    if log_format.lower() == "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log directory is specified)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{app_name}.log")

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10485760, backupCount=5  # 10 MB per file, keep 5 backups
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Create a logger for the application
    logger = logging.getLogger(app_name)
    logger.info(f"Logging initialized at level {log_level}, format: {log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (usually module name)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_command(
    command: str,
    command_type: str = "standard",
    args: Optional[Dict[str, Any]] = None,
    save_to_file: bool = True,
) -> None:
    """
    Log a PowerShell command execution.

    Args:
        command: The PowerShell command or script
        command_type: Type of command (standard, formatted, script)
        args: Additional arguments
        save_to_file: Whether to save to command history file
    """
    logger = get_logger("mcp.commands")

    # Log to application logs
    logger.info(
        f"Executing {command_type} PowerShell command",
        extra={"data": {"command_type": command_type, "args": args or {}}},
    )

    # Save to command history file if enabled
    if save_to_file:
        try:
            config = config_module.get_config()
            if config.logging.enable_command_logging:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                cmd_dir = config.logging.command_history_dir
                os.makedirs(cmd_dir, exist_ok=True)

                filename = f"cmd_{timestamp}.txt"
                if command_type == "script":
                    filename = f"script_{timestamp}.ps1"

                with open(os.path.join(cmd_dir, filename), "w", encoding="utf-8") as f:
                    f.write(f"Command executed at {datetime.now()}:\n{command}\n")
                    if args:
                        f.write(f"Args: {json.dumps(args)}\n")
        except Exception as e:
            logger.error(f"Failed to save command to history file: {e}")
