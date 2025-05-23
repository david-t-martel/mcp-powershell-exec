# MCP PowerShell Exec Server

## Overview

MCP PowerShell Exec Server is a lightweight server that accepts PowerShell scripts as strings, executes them, and returns the output. Enabling AI assistants to understand and work with PowerShell.

## Features

- Accepts PowerShell scripts via string input
- Executes scripts securely in an MCP Server environment
- Returns execution results in real-time

## Installation

Clone the repository and set up the server:

```powershell
git clone https://github.com/yourusername/mcp-powershell-exec.git
cd mcp-powershell-exec
```

### Setup with Virtual Environment (Recommended)

The project includes scripts to automatically set up a Python virtual environment:

```powershell
# Setup the virtual environment and install all dependencies
.\install_deps.ps1

# For development environment (includes testing and linting tools)
.\install_deps.ps1 -Dev

# Force recreate virtual environment
.\install_deps.ps1 -Force

# Activate the virtual environment in the current PowerShell session
.\activate.ps1

# Start the server (automatically sets up and activates the virtual environment)
.\start-server.ps1
```

### Alternative: Install with UV Package Manager

If you prefer using UV:

```powershell
# Install UV if you don't have it
pip install uv

# Install dependencies with UV
uv pip install -r requirements.txt

# Run the server with UV
uv run server.py
```

## In Action

Watch the video to see MCP PowerShell Exec Server in action:

<a href="https://youtu.be/XmYaCJ0bNsE"><img src="https://img.youtube.com/vi/XmYaCJ0bNsE/0.jpg" width="600"/></a>

## Usage

### Command Line Interface

The server can be used directly from the command line for quick PowerShell operations:

```powershell
# Run a PowerShell command
python server.py run "Get-Process | Select-Object -First 5"

# Run a PowerShell command with JSON output
python server.py format "Get-Process | Select-Object -First 5" --format json

# Run a PowerShell script file
python server.py script path/to/script.ps1 --args "arg1 arg2"

# Get help on available commands
python server.py --help
```

With UV:

```powershell
# Run a PowerShell command
uv run server.py run "Get-Process | Select-Object -First 5"

# Run a PowerShell command with JSON output
uv run server.py format "Get-Process | Select-Object -First 5" --format json
```

### Integration with GitHub Copilot in VSCode Insiders

To use this MCP server with GitHub Copilot in VSCode Insiders, follow these steps:

1. **Install VSCode Insiders**

   - Download and install the latest version of [VSCode Insiders](https://code.visualstudio.com/insiders/)

1. **Install GitHub Copilot Extension**

   - Open VSCode Insiders
   - Go to the Extensions marketplace
   - Search for and install "GitHub Copilot"

1. **Configure MCP Server**

   - Open .vscode/mcp.json

   ```json
   {
     "servers": {
       "powershell-integration": {
         "command": "uv", // UV package manager for Python
         "args": ["run", "drive:/yourpath/server.py"],
         "env": {}
       }
     }
   }
   ```

   Replace the path with the actual path to your `server.py` file.

1. **Enable Agent Mode**
   - Open Copilot chat in VSCode Insiders
   - Click on "Copilot Edits"
   - Choose "Agent mode"
   - Click the refresh button in the chat input to load the available tools

## System Requirements

- **Python**: Version 3.10 or higher (required for optimal performance)
- **UV**: Python package manager (will be installed by installation script)
- **PowerShell**: Version 5.1 or higher

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

- Create an issue in this GitHub repository
