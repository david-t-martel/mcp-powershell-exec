#!/usr/bin/env python3
"""
Test script for MCP PowerShell Server - Simple version without emojis
"""

import asyncio
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import initialize_config, validate_config
from logging_setup import setup_logging, get_logger


def test_basic_functionality():
    """Test basic functionality without complex async operations."""
    print("Running basic MCP PowerShell server tests...")

    # Test 1: Configuration
    print("\n1. Testing configuration...")
    try:
        config = initialize_config()
        issues = validate_config(config)

        if issues:
            print(f"   FAIL - Configuration issues: {issues}")
            return False

        print("   PASS - Configuration loaded successfully")

    except Exception as e:
        print(f"   FAIL - Configuration error: {e}")
        return False

    # Test 2: PowerShell availability
    print("\n2. Testing PowerShell availability...")
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", "echo 'test'"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print("   PASS - PowerShell is available")
        else:
            print(f"   FAIL - PowerShell test failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"   FAIL - PowerShell not available: {e}")
        return False

    # Test 3: Logging
    print("\n3. Testing logging setup...")
    try:
        setup_logging(log_level="INFO", log_format="text", log_dir="test_logs")
        logger = get_logger("test")
        logger.info("Test message")
        print("   PASS - Logging setup successful")

    except Exception as e:
        print(f"   FAIL - Logging setup failed: {e}")
        return False

    # Test 4: PowerShell execution (basic)
    print("\n4. Testing PowerShell execution...")
    try:
        from mcp_server import PowerShellExecutor

        config = initialize_config()
        executor = PowerShellExecutor(config)

        # Test simple command
        result = executor.execute_command("echo 'Hello World'")

        if result["success"] and "Hello World" in result["stdout"]:
            print("   PASS - PowerShell execution working")
        else:
            print(f"   FAIL - PowerShell execution failed: {result}")
            return False

    except Exception as e:
        print(f"   FAIL - PowerShell execution test failed: {e}")
        return False

    # Test 5: Security validation
    print("\n5. Testing security validation...")
    try:
        # Test that dangerous commands are blocked
        result = executor.execute_command("Remove-Item C:\\* -Recurse")

        if not result["success"] and "Blocked command" in result["error"]:
            print("   PASS - Security validation working")
        else:
            print(f"   FAIL - Dangerous command was not blocked: {result}")
            return False

    except Exception as e:
        print(f"   FAIL - Security test failed: {e}")
        return False

    print("\nAll basic tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_basic_functionality()

        if success:
            print("\nSUCCESS: MCP PowerShell server is ready to use!")
            print("\nTo start the server:")
            print("  python mcp_server.py")
            print("\nTo use with Claude Desktop, add this to your config:")
            print('  "powershell-exec": {')
            print('    "command": "python",')
            print(f'    "args": ["{Path(__file__).parent / "mcp_server.py"}"]')
            print("  }")
            sys.exit(0)
        else:
            print("\nFAILED: Please fix the issues above before using the server.")
            sys.exit(1)

    except Exception as e:
        print(f"\nTest execution failed: {e}")
        sys.exit(1)
