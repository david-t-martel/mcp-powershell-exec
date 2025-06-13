import os
import subprocess
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import mcp_server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestPowerShellExec(unittest.TestCase):
    """Test case for PowerShell execution functions"""

    @patch("subprocess.Popen")
    def test_run_powershell(self, mock_popen):
        """Test run_powershell function"""
        # Setup mock
        process_mock = MagicMock()
        process_mock.returncode = 0
        process_mock.communicate.return_value = ("test output", "")
        mock_popen.return_value = process_mock

        # Run the function
        result = server.run_powershell("Get-Process")

        # Verify correct command was executed
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0][0], "powershell")
        self.assertEqual(args[0][2], "Get-Process")

        # Verify result
        self.assertEqual(result, "test output")

    @patch("subprocess.Popen")
    def test_run_powershell_error(self, mock_popen):
        """Test run_powershell with command error"""
        # Setup mock
        process_mock = MagicMock()
        process_mock.returncode = 1
        process_mock.communicate.return_value = ("", "command not found")
        mock_popen.return_value = process_mock

        # Run the function
        result = server.run_powershell("Get-NonExistentCommand")

        # Verify error is returned
        self.assertTrue(result.startswith("Error:"))

    @patch("subprocess.Popen")
    def test_run_powershell_timeout(self, mock_popen):
        """Test run_powershell with timeout"""
        # Setup mock
        process_mock = MagicMock()
        process_mock.communicate.side_effect = subprocess.TimeoutExpired(
            cmd="powershell", timeout=1
        )
        mock_popen.return_value = process_mock

        # Run the function
        result = server.run_powershell("Start-Sleep -Seconds 30", timeout=1)

        # Verify timeout error is returned
        self.assertTrue("timeout" in result.lower())

    @patch("server.check_security")
    def test_security_check(self, mock_check_security):
        """Test security check functionality"""
        # Setup mock to indicate dangerous command
        mock_check_security.return_value = (False, "Dangerous command")

        # Run the function
        result = server.run_powershell("Format-Volume -DriveLetter C")

        # Verify command was blocked
        self.assertTrue("error" in result.lower())

        # Change mock to allow the command
        mock_check_security.return_value = (True, "")

        # Setup subprocess mock
        with patch("subprocess.Popen") as mock_popen:
            process_mock = MagicMock()
            process_mock.returncode = 0
            process_mock.communicate.return_value = ("safe command output", "")
            mock_popen.return_value = process_mock

            # Run the function
            result = server.run_powershell("Get-Process")

            # Verify command was executed
            mock_popen.assert_called_once()
            self.assertEqual(result, "safe command output")


if __name__ == "__main__":
    unittest.main()
