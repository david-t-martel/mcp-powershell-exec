import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP

# Import our modules
from config import initialize_config
from logging_setup import get_logger, log_command, setup_logging
from mcp_resources import register_resources
from security import check_security, rate_limit

# Initialize configuration (will be populated from CLI args later)
config = initialize_config()

# Set up logging
setup_logging(
    log_level=config.logging.log_level,
    log_format=config.logging.log_format,
    log_dir=config.logging.log_dir,
    app_name=config.app_name,
)

# Get logger for this module
logger = get_logger("mcp.server")

# Initialize the MCP server
mcp = FastMCP("powershell-integration")

# Register MCP resources
register_resources(mcp)

# Get FastAPI app from MCP server
app = mcp.get_app()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure OpenAPI metadata
app.title = "MCP PowerShell Exec Server"
app.description = "Execute PowerShell commands and scripts securely via MCP"
app.version = "1.0.0"
app.openapi_tags = [
    {
        "name": "tools",
        "description": "PowerShell execution tools",
    },
    {
        "name": "resources",
        "description": "PowerShell documentation resources",
    },
    {
        "name": "system",
        "description": "System endpoints",
    },
]

# Create command history directory if logging is enabled
if config.logging.enable_command_logging:
    os.makedirs(config.logging.command_history_dir, exist_ok=True)


# Add request middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        rate_limit(request)
    except Exception as e:
        # Log but don't block if rate limiting fails
        logger.warning(f"Rate limiting error: {str(e)}")

    response = await call_next(request)
    return response


def check_security(code: str) -> tuple[bool, str]:
    """
    Check if the PowerShell code contains potentially dangerous commands.

    Args:
        code: The PowerShell code to check

    Returns:
        Tuple of (is_safe, message)
    """
    # Block potentially dangerous commands
    dangerous_patterns = [
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
        # Add more patterns as needed
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return (False, f"Potentially dangerous command pattern detected: {pattern}")

    return (True, "")


# Define the command to run PowerShell code
@mcp.tool()
def run_powershell(code: str, timeout: Optional[int] = None) -> str:
    """Runs PowerShell code and returns the output.

    Args:
        code: The PowerShell code to execute
        timeout: Maximum execution time in seconds
    """
    # Use configured default timeout if none specified
    if timeout is None:
        timeout = config.server.default_timeout

    # Check for security issues using imported function
    is_safe, security_msg = check_security(code)
    if not is_safe:
        logger.warning(f"Security check failed: {security_msg}")
        return f"Error: {security_msg}"

    try:
        # Log the command using our structured logging
        log_command(code, "standard", {"timeout": timeout})

        # Run the PowerShell command with configured execution policy
        process = subprocess.Popen(
            [
                "powershell",
                "-ExecutionPolicy",
                config.security.execution_policy,
                "-Command",
                code,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Get the output and error messages with timeout
        output, error = process.communicate(timeout=timeout)

        if process.returncode != 0:
            logger.error(f"PowerShell command failed: {error}")
            return f"Error: {error}"

        logger.debug("PowerShell command executed successfully")
        return output
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning(f"PowerShell command timed out after {timeout} seconds")
        return f"Error: Command execution timed out after {timeout} seconds"
    except Exception as e:
        logger.exception("Unexpected error running PowerShell command")
        return f"Error: {str(e)}"


@mcp.tool()
def run_powershell_formatted(code: str, output_format: str = "text") -> str:
    """Runs PowerShell code and returns the output in specified format.

    Args:
        code: The PowerShell code to execute
        output_format: Output format (text, json, xml, csv)
    """
    # Check for security issues
    is_safe, security_msg = check_security(code)
    if not is_safe:
        logger.warning(f"Security check failed: {security_msg}")
        return f"Error: {security_msg}"

    format_cmd = ""
    if output_format.lower() == "json":
        format_cmd = " | ConvertTo-Json"
    elif output_format.lower() == "xml":
        format_cmd = " | ConvertTo-Xml -As String"
    elif output_format.lower() == "csv":
        format_cmd = " | ConvertTo-Csv"
    elif output_format.lower() not in ["text", ""]:
        return (
            f"Error: Unknown format '{output_format}'. Supported: text, json, xml, csv"
        )

    full_command = code + format_cmd

    # Log the command using structured logging
    log_command(full_command, "formatted", {"format": output_format})

    # Run the PowerShell command
    timeout = config.server.default_timeout
    process = subprocess.Popen(
        [
            "powershell",
            "-ExecutionPolicy",
            config.security.execution_policy,
            "-Command",
            full_command,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Get the output and error messages
    try:
        output, error = process.communicate(timeout=timeout)

        if process.returncode != 0:
            logger.error(f"Formatted PowerShell command failed: {error}")
            return f"Error: {error}"

        logger.debug("Formatted PowerShell command executed successfully")
        return output
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning(f"Command timed out after {timeout} seconds")
        return f"Error: Command execution timed out after {timeout} seconds"
    except Exception as e:
        logger.exception("Unexpected error running formatted PowerShell command")
        return f"Error: {str(e)}"


@mcp.tool()
def run_powershell_script(script_content: str, args: str = "") -> str:
    """Runs a PowerShell script from content and returns the output.

    Args:
        script_content: The content of the PowerShell script
        args: Arguments to pass to the script
    """
    # Check for security issues
    is_safe, security_msg = check_security(script_content)
    if not is_safe:
        logger.warning(f"Security check failed for script: {security_msg}")
        return f"Error: {security_msg}"

    # Create a temporary script file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".ps1", mode="w", encoding="utf-8"
    ) as temp:
        temp.write(script_content)
        script_path = temp.name

    # Log the script using structured logging
    log_command(script_content, "script", {"args": args})

    try:
        # Run the script with the configured execution policy
        cmd_args = [
            "powershell",
            "-ExecutionPolicy",
            config.security.execution_policy,
            "-File",
            script_path,
        ]
        if args:
            cmd_args.extend(args.split())

        process = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            # Use configured timeout
            timeout = config.server.default_timeout
            output, error = process.communicate(timeout=timeout)

            if process.returncode != 0:
                logger.error(f"PowerShell script execution failed: {error}")
                return f"Error: {error}"

            logger.debug("PowerShell script executed successfully")
            return output
        except subprocess.TimeoutExpired:
            process.kill()
            logger.warning(f"Script execution timed out after {timeout} seconds")
            return f"Error: Script execution timed out after {timeout} seconds"
        except Exception as e:
            logger.exception("Unexpected error running PowerShell script")
            return f"Error: {str(e)}"
    finally:
        # Clean up the temporary file
        try:
            os.unlink(script_path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary script file: {e}")


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint to verify server status."""
    # Check PowerShell availability
    try:
        result = subprocess.run(
            ["powershell", "-Command", "echo 'OK'"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        powershell_status = "OK" if result.returncode == 0 else "ERROR"
    except Exception:
        powershell_status = "ERROR"

    return {
        "status": "healthy",
        "version": "1.0.0",
        "powershell": powershell_status,
        "timestamp": datetime.now().isoformat(),
    }


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PowerShell MCP Server")

    # Global arguments
    parser.add_argument(
        "--server", action="store_true", help="Run as MCP server (default mode)"
    )
    parser.add_argument("--config", help="Path to configuration file (JSON or YAML)")
    parser.add_argument(
        "--env-file", help="Path to .env file with environment variables"
    )
    parser.add_argument(
        "--host", help="Host to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, help="Port to run the server on (default: 8000)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Parser for direct command execution
    cmd_parser = subparsers.add_parser("run", help="Run a PowerShell command")
    cmd_parser.add_argument("code", help="PowerShell code to execute")
    cmd_parser.add_argument("--timeout", type=int, help="Command timeout in seconds")

    # Parser for formatted output
    fmt_parser = subparsers.add_parser(
        "format", help="Run a command with formatted output"
    )
    fmt_parser.add_argument("code", help="PowerShell code to execute")
    fmt_parser.add_argument(
        "--format",
        dest="output_format",
        choices=["text", "json", "xml", "csv"],
        default="text",
        help="Output format",
    )

    # Parser for script execution
    script_parser = subparsers.add_parser("script", help="Run a PowerShell script")
    script_parser.add_argument("file", help="Path to PowerShell script file")
    script_parser.add_argument(
        "--args", default="", help="Arguments to pass to the script"
    )

    return parser.parse_args()


def run_command_line():
    """Run in command line mode using arguments"""
    args = parse_arguments()

    # Initialize configuration with command line options
    overrides = {}
    if args.host:
        overrides["server.host"] = args.host
    if args.port:
        overrides["server.port"] = args.port
    if args.log_level:
        overrides["logging.log_level"] = args.log_level

    # Initialize config with options from command line
    global config
    config = initialize_config(
        config_file=args.config, env_file=args.env_file, **overrides
    )

    # Re-setup logging with new configuration
    setup_logging(
        log_level=config.logging.log_level,
        log_format=config.logging.log_format,
        log_dir=config.logging.log_dir,
        app_name=config.app_name,
    )

    if args.command == "run":
        # Run a simple command
        if os.path.isfile(args.code):
            with open(args.code, "r", encoding="utf-8") as f:
                code = f.read()
        else:
            code = args.code

        result = run_powershell(code, args.timeout)
        print(result)

    elif args.command == "format":
        # Run with formatted output
        if os.path.isfile(args.code):
            with open(args.code, "r", encoding="utf-8") as f:
                code = f.read()
        else:
            code = args.code

        result = run_powershell_formatted(code, args.output_format)
        print(result)

    elif args.command == "script":
        # Run a script from file
        if not os.path.isfile(args.file):
            print(f"Error: Script file '{args.file}' not found")
            sys.exit(1)

        with open(args.file, "r", encoding="utf-8") as f:
            script_content = f.read()
            result = run_powershell_script(script_content, args.args)
            print(result)

    else:
        # Server mode with uvicorn for better performance
        logger.info(f"Starting MCP server at {config.server.host}:{config.server.port}")
        if config.security.require_api_key:
            if not config.security.api_keys:
                logger.warning(
                    "API key authentication is required but no keys are configured!"
                )
            else:
                logger.info(
                    f"API key authentication is enabled ({len(config.security.api_keys)} key(s) configured)"
                )

        uvicorn.run(
            app,
            host=config.server.host,
            port=config.server.port,
            log_level=config.logging.log_level.lower(),
        )


if __name__ == "__main__":
    # Check if PowerShell is available
    try:
        result = subprocess.run(
            ["powershell", "-Command", "echo 'PowerShell is available'"],
            capture_output=True,
            text=True,
            check=True,
        )

        if "PowerShell is available" not in result.stdout:
            print("Error: PowerShell check failed")
            sys.exit(1)
    except Exception as e:
        print(f"Error: PowerShell is not available - {str(e)}")
        sys.exit(1)

    # If arguments are provided, run in command line mode
    run_command_line()
