#!/usr/bin/env python3
"""
MCP PowerShell Execution Server

A Model Context Protocol server that provides secure PowerShell command execution.
This version uses FastMCP for modern MCP implementation patterns.
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import List, Optional

from mcp.server.fastmcp import Context, FastMCP

# Import local modules
from config import Config, initialize_config, validate_config
from logging_setup import get_logger, setup_logging


class PowerShellExecutor:
    """Handles secure PowerShell command execution with security controls."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("powershell.executor")

    def check_security(self, code: str) -> tuple[bool, str]:
        """Check if PowerShell code is safe to execute."""
        # Check command length
        if len(code) > self.config.security.max_command_length:
            return (
                False,
                (
                    f"Command too long (max "
                    f"{self.config.security.max_command_length} chars)"
                ),
            )

        # Check for blocked commands
        code_lower = code.lower()
        for blocked_cmd in self.config.security.blocked_commands:
            if blocked_cmd.lower() in code_lower:
                return False, f"Blocked command detected: {blocked_cmd}"

        # Check dangerous patterns
        for pattern in self.config.security.dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        return True, ""

    def execute_command(
        self, code: str, timeout: Optional[int] = None, format_output: str = "text"
    ) -> dict:
        """Execute PowerShell command with security checks and formatting."""
        # Security validation
        is_safe, error_msg = self.check_security(code)
        if not is_safe:
            self.logger.warning("Security check failed: %s", error_msg)
            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": "",
                "exit_code": -1,
                "execution_time": 0,
            }

        # Use configured timeout if none specified
        if timeout is None:
            timeout = self.config.security.command_timeout

        # Add output formatting if requested
        if format_output == "json":
            code += " | ConvertTo-Json -Depth 10"
        elif format_output == "xml":
            code += " | ConvertTo-Xml -As String"
        elif format_output == "csv":
            code += " | ConvertTo-Csv -NoTypeInformation"

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
                    code,
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

            return {
                "success": process.returncode == 0,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "exit_code": process.returncode,
                "execution_time": round(execution_time, 2),
                "error": stderr.strip() if process.returncode != 0 else None,
            }

        except subprocess.TimeoutExpired:
            process.kill()
            execution_time = time.time() - start_time
            error_msg = f"Command timed out after {timeout} seconds"
            self.logger.warning(error_msg)

            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
                "execution_time": round(execution_time, 2),
            }

        except (subprocess.CalledProcessError, OSError) as e:
            execution_time = time.time() - start_time
            error_msg = f"Execution failed: {str(e)}"
            self.logger.exception("PowerShell execution error")

            return {
                "success": False,
                "error": error_msg,
                "stdout": "",
                "stderr": error_msg,
                "exit_code": -1,
                "execution_time": round(execution_time, 2),
            }


# Initialize FastMCP server
mcp = FastMCP("powershell-exec")


@mcp.tool(description="Execute PowerShell commands securely with output formatting")
async def execute_powershell(
    command: str,
    ctx: Context,
    timeout: Optional[int] = None,
    output_format: str = "text"
) -> str:
    """Execute PowerShell commands securely."""
    await ctx.info(f"Executing PowerShell command: {command[:100]}...")

    if not command.strip():
        await ctx.error("Command cannot be empty")
        return json.dumps({"error": "Command cannot be empty", "success": False})

    # Get config from server settings (we'll need to pass this through)
    # For now, use default security settings
    config = initialize_config()
    executor = PowerShellExecutor(config)

    result = executor.execute_command(command, timeout, output_format)

    if result["success"]:
        execution_time = result.get('execution_time', 0)
        await ctx.info(f"Command executed successfully in {execution_time}s")
    else:
        await ctx.warning(f"Command failed: {result.get('error', 'Unknown error')}")

    response = {"tool": "execute_powershell", "command": command, "result": result}
    return json.dumps(response, indent=2)


@mcp.tool(description="Execute PowerShell scripts with optional arguments")
async def run_powershell_script(
    script: str,
    ctx: Context,
    arguments: Optional[List[str]] = None,
    timeout: Optional[int] = None
) -> str:
    """Execute PowerShell scripts with arguments."""
    await ctx.info(f"Executing PowerShell script ({len(script)} chars)...")

    if not script.strip():
        await ctx.error("Script cannot be empty")
        return json.dumps({"error": "Script cannot be empty", "success": False})

    config = initialize_config()
    executor = PowerShellExecutor(config)

    try:
        # Create temporary script file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ps1", delete=False, encoding="utf-8"
        ) as f:
            f.write(script)
            script_path = f.name

        # Build command with arguments
        command = f"& '{script_path}'"
        if arguments:
            escaped_args = [f"'{arg}'" for arg in arguments]
            command += " " + " ".join(escaped_args)

        result = executor.execute_command(command, timeout)

        # Clean up temp file
        try:
            os.unlink(script_path)
        except (OSError, PermissionError):
            pass  # Ignore cleanup errors

        if result["success"]:
            execution_time = result.get('execution_time', 0)
            await ctx.info(f"Script executed successfully in {execution_time}s")
        else:
            await ctx.warning(f"Script failed: {result.get('error', 'Unknown error')}")

        response = {
            "tool": "run_powershell_script",
            "script_length": len(script),
            "arguments": arguments or [],
            "result": result
        }
        return json.dumps(response, indent=2)

    except (OSError, PermissionError, ValueError) as e:
        await ctx.error(f"Error executing script: {str(e)}")
        error_msg = f"Error executing script: {str(e)}"
        return json.dumps({"error": error_msg, "success": False})


@mcp.tool(description="Test PowerShell commands for safety before execution")
async def test_powershell_safety(command: str, ctx: Context) -> str:
    """Test if a PowerShell command is safe to execute."""
    await ctx.info(f"Testing safety of command: {command[:100]}...")

    if not command.strip():
        await ctx.error("Command cannot be empty")
        return json.dumps({"error": "Command cannot be empty", "is_safe": False})

    config = initialize_config()
    executor = PowerShellExecutor(config)

    is_safe, message = executor.check_security(command)

    if is_safe:
        await ctx.info("Command passed safety checks")
    else:
        await ctx.warning(f"Command failed safety check: {message}")

    response = {
        "tool": "test_powershell_safety",
        "command": command,
        "is_safe": is_safe,
        "message": message if message else "Command passed security checks",
        "checks_performed": [
            "Command length validation",
            "Blocked command detection",
            "Dangerous pattern detection",
        ],
    }

    return json.dumps(response, indent=2)


@mcp.resource("powershell://help/commands")
def powershell_commands_help() -> str:
    """Get help documentation for available PowerShell commands."""
    return """
# PowerShell MCP Server Commands

## execute_powershell
Execute PowerShell commands securely with output formatting options.

Parameters:
- command (required): PowerShell command or script to execute
- timeout (optional): Execution timeout in seconds (1-300)
- format (optional): Output format - text, json, xml, or csv

## run_powershell_script
Execute PowerShell scripts with optional arguments.

Parameters:
- script (required): PowerShell script content to execute
- arguments (optional): List of arguments to pass to the script
- timeout (optional): Execution timeout in seconds (1-300)

## test_powershell_safety
Test PowerShell commands for safety before execution.

Parameters:
- command (required): PowerShell command to test for safety

## Security Features
- Command length limits
- Blocked command detection
- Safe execution environment
- Timeout protection
- Output sanitization
"""


@mcp.prompt(description="Generate PowerShell commands for Windows administration")
async def windows_admin_prompt(task: str, context: str = "general") -> str:
    """Generate PowerShell commands for Windows administration tasks."""
    return f"""
You are a Windows PowerShell expert. Generate safe and effective PowerShell \
commands for the following task:

Task: {task}
Context: {context}

Please provide:
1. The PowerShell command(s) to accomplish this task
2. Brief explanation of what each command does
3. Any important safety considerations
4. Expected output or results

Focus on commonly used, safe commands that are appropriate for system \
administration.
"""


async def main() -> None:
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(description="MCP PowerShell Execution Server")

    # Configuration arguments
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--env-file", help="Path to .env file")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )

    # Server mode arguments
    parser.add_argument(
        "--stdio",
        action="store_true",
        default=True,
        help="Run in stdio mode for MCP clients (default)",
    )

    # CLI command arguments
    parser.add_argument("--execute", help="Execute a PowerShell command directly")
    parser.add_argument(
        "--format",
        choices=["text", "json", "xml", "csv"],
        default="text",
        help="Output format for direct execution",
    )
    parser.add_argument("--timeout", type=int, help="Execution timeout in seconds")

    args = parser.parse_args()

    # Initialize configuration
    config_overrides = {}
    if args.log_level:
        config_overrides["logging.log_level"] = args.log_level

    config = initialize_config(
        config_file=args.config, env_file=args.env_file, **config_overrides
    )

    # Validate configuration
    issues = validate_config(config)
    if issues:
        print("Configuration issues found:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    # Setup logging
    logging_config = config.logging
    setup_logging(
        log_level=getattr(logging_config, "log_level", "INFO"),
        log_format=getattr(logging_config, "log_format", "text"),
        log_dir=getattr(logging_config, "log_dir", "logs"),
        app_name=config.app_name,
    )

    logger = get_logger("main")

    # Check PowerShell availability
    try:
        ps_check = subprocess.run(
            ["powershell.exe", "-Command", "echo 'PowerShell Available'"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if ps_check.returncode != 0:
            logger.error("PowerShell is not available or not working properly")
            sys.exit(1)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, OSError) as e:
        logger.error("PowerShell check failed: %s", e)
        sys.exit(1)

    # Handle direct command execution
    if args.execute:
        executor = PowerShellExecutor(config)
        exec_result = executor.execute_command(args.execute, args.timeout, args.format)

        if exec_result["success"]:
            print(exec_result["stdout"])
            sys.exit(0)
        else:
            print(f"Error: {exec_result['error']}", file=sys.stderr)
            if exec_result["stderr"]:
                print(exec_result["stderr"], file=sys.stderr)
            sys.exit(exec_result.get("exit_code", 1))

    # Run MCP server using FastMCP
    logger.info("Starting MCP PowerShell Server in stdio mode")

    try:
        mcp.run("stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except (OSError, ConnectionError, RuntimeError):
        logger.exception("Server error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
