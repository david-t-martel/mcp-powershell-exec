#!/usr/bin/env python3
"""
MCP PowerShell Execution Server

A Model Context Protocol server that provides secure PowerShell command execution.
This version supports stdio transport for MCP clients like Claude Desktop.
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

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Import local modules
from config import Config, initialize_config, validate_config
from logging_setup import get_logger, setup_logging


class PowerShellExecutor:
    """Handles secure PowerShell command execution with security controls."""

    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("powershell.executor")

    def _check_security(self, code: str) -> tuple[bool, str]:
        """Check if PowerShell code is safe to execute."""
        # Check command length
        if len(code) > self.config.security.max_command_length:
            return (
                False,
                f"Command too long (max {self.config.security.max_command_length} chars)",
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
        is_safe, error_msg = self._check_security(code)
        if not is_safe:
            self.logger.warning(f"Security check failed: {error_msg}")
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
                f"Command executed in {execution_time:.2f}s with exit code {process.returncode}"
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

        except Exception as e:
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


class MCPPowerShellServer:
    """MCP PowerShell Server implementation."""

    def __init__(self, config: Config):
        self.config = config
        self.executor = PowerShellExecutor(config)
        self.logger = get_logger("mcp.server")

        # Initialize MCP server
        self.server = Server("powershell-exec")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP server handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available PowerShell execution tools."""
            return [
                Tool(
                    name="execute_powershell",
                    description="Execute PowerShell commands securely with output formatting options",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "PowerShell command or script to execute",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Execution timeout in seconds (optional)",
                                "minimum": 1,
                                "maximum": 300,
                            },
                            "format": {
                                "type": "string",
                                "description": "Output format (text, json, xml, csv)",
                                "enum": ["text", "json", "xml", "csv"],
                                "default": "text",
                            },
                        },
                        "required": ["command"],
                    },
                ),
                Tool(
                    name="run_powershell_script",
                    description="Execute a PowerShell script with arguments",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "PowerShell script content to execute",
                            },
                            "arguments": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Arguments to pass to the script (optional)",
                                "default": [],
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Execution timeout in seconds (optional)",
                                "minimum": 1,
                                "maximum": 300,
                            },
                        },
                        "required": ["script"],
                    },
                ),
                Tool(
                    name="test_powershell_safety",
                    description="Test if a PowerShell command is safe to execute (security check only)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "PowerShell command to test for safety",
                            }
                        },
                        "required": ["command"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool execution requests."""
            try:
                if name == "execute_powershell":
                    return await self._handle_execute_powershell(arguments)
                elif name == "run_powershell_script":
                    return await self._handle_run_script(arguments)
                elif name == "test_powershell_safety":
                    return await self._handle_test_safety(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                self.logger.exception(f"Tool execution error: {name}")
                return [
                    TextContent(
                        type="text", text=f"Error executing tool '{name}': {str(e)}"
                    )
                ]

    async def _handle_execute_powershell(self, arguments: dict) -> List[TextContent]:
        """Handle PowerShell command execution."""
        command = arguments.get("command", "")
        timeout = arguments.get("timeout")
        format_type = arguments.get("format", "text")

        if not command.strip():
            return [TextContent(type="text", text="Error: Command cannot be empty")]

        result = self.executor.execute_command(command, timeout, format_type)

        # Format result as JSON for structured output
        response = {"tool": "execute_powershell", "command": command, "result": result}

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    async def _handle_run_script(self, arguments: dict) -> List[TextContent]:
        """Handle PowerShell script execution."""
        script = arguments.get("script", "")
        args = arguments.get("arguments", [])
        timeout = arguments.get("timeout")

        if not script.strip():
            return [TextContent(type="text", text="Error: Script cannot be empty")]

        # Create temporary script file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".ps1", delete=False, encoding="utf-8"
            ) as f:
                f.write(script)
                script_path = f.name

            # Build command with arguments
            command = f"& '{script_path}'"
            if args:
                escaped_args = [f"'{arg}'" for arg in args]
                command += " " + " ".join(escaped_args)

            result = self.executor.execute_command(command, timeout)

            # Clean up temp file
            try:
                os.unlink(script_path)
            except:
                pass  # Ignore cleanup errors

            response = {
                "tool": "run_powershell_script",
                "script_length": len(script),
                "arguments": args,
                "result": result,
            }

            return [TextContent(type="text", text=json.dumps(response, indent=2))]

        except Exception as e:
            return [TextContent(type="text", text=f"Error executing script: {str(e)}")]

    async def _handle_test_safety(self, arguments: dict) -> List[TextContent]:
        """Handle safety testing for PowerShell commands."""
        command = arguments.get("command", "")

        if not command.strip():
            return [TextContent(type="text", text="Error: Command cannot be empty")]

        is_safe, message = self.executor._check_security(command)

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

        return [TextContent(type="text", text=json.dumps(response, indent=2))]

    async def run_stdio(self):
        """Run the server with stdio transport for MCP clients."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="powershell-exec",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
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
    setup_logging(
        log_level=config.logging.log_level,
        log_format=config.logging.log_format,
        log_dir=config.logging.log_dir,
        app_name=config.app_name,
    )

    logger = get_logger("main")

    # Check PowerShell availability
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", "echo 'PowerShell Available'"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            logger.error("PowerShell is not available or not working properly")
            sys.exit(1)
    except Exception as e:
        logger.error(f"PowerShell check failed: {e}")
        sys.exit(1)

    # Handle direct command execution
    if args.execute:
        executor = PowerShellExecutor(config)
        result = executor.execute_command(args.execute, args.timeout, args.format)

        if result["success"]:
            print(result["stdout"])
            sys.exit(0)
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            if result["stderr"]:
                print(result["stderr"], file=sys.stderr)
            sys.exit(result.get("exit_code", 1))

    # Run MCP server
    logger.info("Starting MCP PowerShell Server in stdio mode")
    server = MCPPowerShellServer(config)

    try:
        await server.run_stdio()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception:
        logger.exception("Server error")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
