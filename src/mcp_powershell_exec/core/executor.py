"""
PowerShell command execution with security and formatting.
"""
import subprocess
import time
from typing import Optional

from config import Config
from logging_setup import get_logger
from .security import SecurityValidator
from .formatters import OutputFormatter
from .types import ExecutionResult, OutputFormat


class PowerShellExecutor:
    """Handles secure PowerShell command execution with security controls."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("powershell.executor")
        self.security_validator = SecurityValidator(config)
        self.formatter = OutputFormatter()

    def execute_command(
        self,
        code: str,
        timeout: Optional[int] = None,
        format_output: OutputFormat = "text"
    ) -> ExecutionResult:
        """Execute PowerShell command with security checks and formatting."""
        # Security validation
        security_result = self.security_validator.check_security(code)
        if not security_result.is_safe:
            self.logger.warning(
                "Security check failed: %s", security_result.error_message
            )
            return ExecutionResult(
                success=False,
                error=security_result.error_message,
                stdout="",
                stderr="",
                exit_code=-1,
                execution_time=0,
            )

        # Use configured timeout if none specified
        if timeout is None:
            timeout = self.config.security.command_timeout

        # Apply output formatting
        formatted_code = self.formatter.apply_format(code, format_output)

        start_time = time.time()

        try:
            # Execute PowerShell command
            process = subprocess.Popen(
                [
                    "powershell.exe",
                    "-ExecutionPolicy",
                    self.config.security.execution_policy,
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    formatted_code,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            stdout, stderr = process.communicate(timeout=timeout)
            execution_time = time.time() - start_time

            self.logger.info(
                "Command executed in %.2fs with exit code %d",
                execution_time,
                process.returncode,
            )

            return ExecutionResult(
                success=process.returncode == 0,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                exit_code=process.returncode,
                execution_time=round(execution_time, 2),
                error=stderr.strip() if process.returncode != 0 else None,
            )

        except subprocess.TimeoutExpired:
            process.kill()
            execution_time = time.time() - start_time
            error_msg = f"Command timed out after {timeout} seconds"
            self.logger.warning(error_msg)

            return ExecutionResult(
                success=False,
                error=error_msg,
                stdout="",
                stderr=error_msg,
                exit_code=-1,
                execution_time=round(execution_time, 2),
            )

        except (subprocess.CalledProcessError, OSError) as e:
            execution_time = time.time() - start_time
            error_msg = f"Execution failed: {str(e)}"
            self.logger.exception("PowerShell execution error")

            return ExecutionResult(
                success=False,
                error=error_msg,
                stdout="",
                stderr=error_msg,
                exit_code=-1,
                execution_time=round(execution_time, 2),
            )

    def test_safety(self, code: str) -> dict:
        """Test command safety without execution."""
        security_result = self.security_validator.check_security(code)
        return {
            "is_safe": security_result.is_safe,
            "message": (
                security_result.error_message 
                if not security_result.is_safe 
                else "Command is safe to execute"
            ),
            "command": code
        }
