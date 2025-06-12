"""
Logging setup and utilities for MCP PowerShell Exec Server.
"""

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    log_dir: str = "logs",
    app_name: str = "mcp-powershell-exec"
) -> None:
    """Set up logging configuration for the application."""
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Setup formatters
    if log_format.lower() == "json":
        formatter = JsonFormatter()
        console_formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler
    log_file = log_path / f"{app_name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)


def log_command(
    command: str,
    command_type: str = "standard",
    metadata: Optional[Dict[str, Any]] = None,
    log_dir: str = "command_history"
) -> None:
    """Log PowerShell command execution for audit purposes."""
    try:
        history_path = Path(log_dir)
        history_path.mkdir(exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "command_type": command_type,
            "metadata": metadata or {}
        }
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        history_file = history_path / f"commands-{date_str}.jsonl"
        
        with open(history_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, default=str) + '\n')
        
        logger = get_logger("command_history")
        logger.info(f"Command executed: {command_type}")
        
    except Exception as e:
        logger = get_logger("command_history")
        logger.warning(f"Failed to log command: {e}")


if __name__ == "__main__":
    setup_logging(log_level="DEBUG", log_format="text")
    
    logger = get_logger("test")
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    log_command("Get-Process | Select-Object Name, CPU", "standard", {"timeout": 30})
    print("Logging test completed")
