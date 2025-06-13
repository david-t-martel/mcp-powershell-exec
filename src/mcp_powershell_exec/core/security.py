"""
Security validation for PowerShell commands.
"""
import re

from config import Config
from logging_setup import get_logger
from .types import SecurityCheckResult


class SecurityValidator:
    """Validates PowerShell commands for security compliance."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("powershell.security")

    def check_security(self, code: str) -> SecurityCheckResult:
        """Check if PowerShell code is safe to execute."""
        # Check command length
        if len(code) > self.config.security.max_command_length:
            return SecurityCheckResult(
                is_safe=False,
                error_message=(
                    f"Command too long (max "
                    f"{self.config.security.max_command_length} chars)"
                ),
            )

        # Check for blocked commands
        code_lower = code.lower()
        for blocked_cmd in self.config.security.blocked_commands:
            if blocked_cmd.lower() in code_lower:
                return SecurityCheckResult(
                    is_safe=False,
                    error_message=f"Blocked command detected: {blocked_cmd}"
                )

        # Check dangerous patterns
        for pattern in self.config.security.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return SecurityCheckResult(
                    is_safe=False,
                    error_message=f"Dangerous pattern detected: {pattern}"
                )

        return SecurityCheckResult(is_safe=True)

    def is_command_allowed(self, command: str) -> bool:
        """Quick check if a command is allowed."""
        result = self.check_security(command)
        return result.is_safe
