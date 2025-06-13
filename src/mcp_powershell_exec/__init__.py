"""
MCP PowerShell Execution Server

A Model Context Protocol server that provides secure PowerShell command execution.
"""

__version__ = "1.0.0"
__author__ = "MCP PowerShell Team"
__description__ = "MCP server for secure PowerShell command execution"

from .core.executor import PowerShellExecutor
from .core.security import SecurityValidator

__all__ = [
    "PowerShellExecutor",
    "SecurityValidator",
]
