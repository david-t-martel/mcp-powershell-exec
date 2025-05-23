import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import server module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import server


class TestCommandLineInterface(unittest.TestCase):
    """Test case for command-line interface functions"""

    @patch("argparse.ArgumentParser.parse_args")
    @patch("server.run_powershell")
    def test_run_command(self, mock_run_powershell, mock_parse_args):
        """Test CLI run command"""
        # Setup mock args
        args = MagicMock()
        args.command = "run"
        args.code = "Get-Process"
        args.timeout = 30
        mock_parse_args.return_value = args

        # Setup mock output
        mock_run_powershell.return_value = "mock output"

        # Redirect stdout to capture print output
        with patch("sys.stdout", new=MagicMock()) as mock_stdout:
            server.run_command_line()

        # Verify run_powershell was called with correct args
        mock_run_powershell.assert_called_once_with("Get-Process", 30)

    @patch("argparse.ArgumentParser.parse_args")
    @patch("server.run_powershell_formatted")
    def test_format_command(self, mock_run_powershell_formatted, mock_parse_args):
        """Test CLI format command"""
        # Setup mock args
        args = MagicMock()
        args.command = "format"
        args.code = "Get-Process"
        args.format = "json"
        mock_parse_args.return_value = args

        # Setup mock output
        mock_run_powershell_formatted.return_value = '{"mock": "output"}'

        # Redirect stdout to capture print output
        with patch("sys.stdout", new=MagicMock()) as mock_stdout:
            server.run_command_line()

        # Verify run_powershell_formatted was called with correct args
        mock_run_powershell_formatted.assert_called_once_with("Get-Process", "json")

    @patch("argparse.ArgumentParser.parse_args")
    @patch("server.run_powershell_script")
    @patch("os.path.isfile")
    def test_script_command(
        self, mock_isfile, mock_run_powershell_script, mock_parse_args
    ):
        """Test CLI script command"""
        # Setup mock args
        args = MagicMock()
        args.command = "script"
        args.file = "test_script.ps1"
        args.args = "arg1 arg2"
        mock_parse_args.return_value = args

        # Setup mock file check and file read
        mock_isfile.return_value = True
        mock_open = unittest.mock.mock_open(read_data="# PowerShell script content")

        # Setup mock output
        mock_run_powershell_script.return_value = "script output"

        # Redirect stdout and patch open
        with patch("sys.stdout", new=MagicMock()) as mock_stdout, patch(
            "builtins.open", mock_open
        ):
            server.run_command_line()

        # Verify run_powershell_script was called with correct args
        mock_run_powershell_script.assert_called_once()
        args, kwargs = mock_run_powershell_script.call_args
        self.assertEqual(args[0], "# PowerShell script content")
        self.assertEqual(args[1], "arg1 arg2")

    @patch("argparse.ArgumentParser.parse_args")
    @patch("server.mcp.run")
    def test_server_mode(self, mock_mcp_run, mock_parse_args):
        """Test CLI server mode"""
        # Setup mock args
        args = MagicMock()
        args.command = None
        mock_parse_args.return_value = args

        server.run_command_line()

        # Verify MCP server was started
        mock_mcp_run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
