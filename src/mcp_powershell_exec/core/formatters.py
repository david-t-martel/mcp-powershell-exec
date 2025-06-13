"""
Output formatting utilities for PowerShell commands.
"""
from .types import OutputFormat


class OutputFormatter:
    """Handles PowerShell output formatting."""

    @staticmethod
    def apply_format(command: str, format_type: OutputFormat) -> str:
        """Apply output formatting to a PowerShell command."""
        if format_type == "json":
            return f"{command} | ConvertTo-Json -Depth 10"
        elif format_type == "xml":
            return f"{command} | ConvertTo-Xml -As String"
        elif format_type == "csv":
            return f"{command} | ConvertTo-Csv -NoTypeInformation"
        else:  # text
            return command

    @staticmethod
    def get_supported_formats() -> list[str]:
        """Get list of supported output formats."""
        return ["text", "json", "xml", "csv"]
