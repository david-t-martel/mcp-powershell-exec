import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import mcp_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import initialize_config
from mcp_server import PowerShellExecutor


class TestPowerShellExecutor(unittest.TestCase):
    """Test case for PowerShellExecutor class"""

    def setUp(self):
        """Set up test instance"""
        self.config = initialize_config()
        self.executor = PowerShellExecutor(self.config)

    @patch("subprocess.run")
    def test_execute_command_success(self, mock_run):
        """Test successful PowerShell command execution"""
        # Setup mock
        mock_run.return_value = MagicMock(returncode=0, stdout="test output", stderr="")

        # Run the function
        result = self.executor.execute("Get-Date")

        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["stdout"], "test output")
        self.assertEqual(result["stderr"], "")
        self.assertEqual(result["exit_code"], 0)

        # Verify correct command was executed
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        self.assertIn("powershell", args[0])

    @patch("subprocess.run")
    def test_execute_command_error(self, mock_run):
        """Test PowerShell command execution with error"""
        # Setup mock
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="command not found"
        )

        # Run the function
        result = self.executor.execute("Get-NonExistentCommand")

        # Verify result
        self.assertFalse(result["success"])
        self.assertEqual(result["stdout"], "")
        self.assertEqual(result["stderr"], "command not found")
        self.assertEqual(result["exit_code"], 1)

    @patch("subprocess.run")
    def test_execute_command_timeout(self, mock_run):
        """Test PowerShell command execution with timeout"""
        # Setup mock to raise timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="powershell", timeout=1)

        # Run the function
        result = self.executor.execute("Start-Sleep -Seconds 30")

        # Verify result
        self.assertFalse(result["success"])
        self.assertIn("timeout", result["stderr"].lower())

    def test_security_check_safe_commands(self):
        """Test security check allows safe commands"""
        safe_commands = ["Get-Process", "Get-Date", "Get-Location", "Get-ChildItem"]

        for command in safe_commands:
            is_safe, message = self.executor._check_security(command)
            self.assertTrue(
                is_safe, f"Command '{command}' should be allowed: {message}"
            )

    def test_security_check_dangerous_commands(self):
        """Test security check blocks dangerous commands"""
        dangerous_commands = [
            "Remove-Item -Recurse -Force",
            "Format-Volume",
            "Stop-Computer",
            "Restart-Computer",
        ]

        for command in dangerous_commands:
            is_safe, message = self.executor._check_security(command)
            self.assertFalse(is_safe, f"Command '{command}' should be blocked")

    def test_security_check_command_length(self):
        """Test security check blocks commands that are too long"""
        long_command = "Get-Process " + "A" * 5000

        is_safe, message = self.executor._check_security(long_command)
        self.assertFalse(is_safe)
        self.assertIn("too long", message)

    def test_security_check_blocked_commands(self):
        """Test security check blocks specifically configured commands"""
        # Test with a command that should be in the blocked list
        blocked_commands = ["Remove-Item", "rmdir", "del"]

        for command in blocked_commands:
            is_safe, message = self.executor._check_security(command)
            self.assertFalse(is_safe, f"Command '{command}' should be blocked")


if __name__ == "__main__":
    unittest.main()
