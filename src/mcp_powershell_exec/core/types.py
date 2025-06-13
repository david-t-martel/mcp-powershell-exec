"""
Shared type definitions for MCP PowerShell Exec Server.
"""
from typing import Optional, Literal
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    """Result of PowerShell command execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None


class SecurityCheckResult(BaseModel):
    """Result of security validation."""
    is_safe: bool
    error_message: str = ""


OutputFormat = Literal["text", "json", "xml", "csv"]
"""Supported output formats for PowerShell commands."""
