import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime

from mcp.server.fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("powershell-integration")

# Create a command history directory
os.makedirs("command_history", exist_ok=True)


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
def run_powershell(code: str, timeout: int = 30) -> str:
    """Runs PowerShell code and returns the output.

    Args:
        code: The PowerShell code to execute
        timeout: Maximum execution time in seconds (default: 30)
    """
    # Check for security issues
    is_safe, security_msg = check_security(code)
    if not is_safe:
        return f"Error: {security_msg}"

    try:
        # Log the command
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"command_history/cmd_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write(f"Command executed at {datetime.now()}:\n{code}\n")

        # Run the PowerShell command with timeout
        process = subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Restricted", "-Command", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Get the output and error messages with timeout
        output, error = process.communicate(timeout=timeout)

        if process.returncode != 0:
            return f"Error: {error}"

        return output
    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: Command execution timed out"


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

    # Log the command
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"command_history/cmd_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write(f"Formatted command executed at {datetime.now()}:\n{full_command}\n")

    # Run the PowerShell command
    process = subprocess.Popen(
        ["powershell", "-ExecutionPolicy", "Restricted", "-Command", full_command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Get the output and error messages
    try:
        # Default timeout of 30 seconds
        output, error = process.communicate(timeout=30)

        if process.returncode != 0:
            return f"Error: {error}"

        return output
    except subprocess.TimeoutExpired:
        process.kill()
        return "Error: Command execution timed out"


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
        return f"Error: {security_msg}"

    # Create a temporary script file
    with tempfile.NamedTemporaryFile(
        delete=False, suffix=".ps1", mode="w", encoding="utf-8"
    ) as temp:
        temp.write(script_content)
        script_path = temp.name

    # Log the script
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"command_history/script_{timestamp}.ps1", "w", encoding="utf-8") as f:
        f.write(f"Script executed at {datetime.now()}:\n{script_content}\n")
        if args:
            f.write(f"Arguments: {args}\n")

    try:
        # Run the script with a restricted execution policy
        cmd_args = [
            "powershell",
            "-ExecutionPolicy",
            "Restricted",
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
            # Default timeout of 30 seconds
            output, error = process.communicate(timeout=30)

            if process.returncode != 0:
                return f"Error: {error}"

            return output
        except subprocess.TimeoutExpired:
            process.kill()
            return "Error: Script execution timed out"
    finally:
        # Clean up the temporary file
        os.unlink(script_path)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="PowerShell MCP Server")

    # Global arguments
    parser.add_argument(
        "--server", action="store_true", help="Run as MCP server (default mode)"
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Parser for direct command execution
    cmd_parser = subparsers.add_parser("run", help="Run a PowerShell command")
    cmd_parser.add_argument("code", help="PowerShell code to execute")
    cmd_parser.add_argument(
        "--timeout", type=int, default=30, help="Command timeout in seconds"
    )

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
        # Default to server mode
        mcp.run()


if __name__ == "__main__":
    # If arguments are provided, run in command line mode
    if len(sys.argv) > 1:
        run_command_line()
    else:
        # Run the MCP server
        mcp.run()
