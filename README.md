# MCP PowerShell Exec Server

## Overview

MCP PowerShell Exec Server is a lightweight server that accepts PowerShell scripts as strings, executes them, and returns the output. Enabling AI assistants to understand and work with PowerShell.

## Features

- Accepts PowerShell scripts via string input
- Executes scripts securely in an MCP Server environment
- Returns execution results in real-time
- Configurable via environment variables, config files, or command-line options
- API key authentication for secure access
- Structured logging with multiple output formats
- CORS support for web client integration
- Rate limiting for API protection

## Installation

Clone the repository and set up the server:

```powershell
git clone https://github.com/david-t-martel/mcp-powershell-exec.git
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

### Alternative: Install with Docker (Recommended for Production)

The project includes Docker support for easy deployment:

```bash
# Build and start the container
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

You can customize the Docker deployment by editing the `docker-compose.yml` file or environment variables.

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

## Configuration

MCP PowerShell Exec Server can be configured using:

1. **Configuration file** (JSON or YAML):

   ```powershell
   # Start with a custom config file
   python server.py --config config.json
   ```

2. **Environment variables**:

   ```powershell
   # Set environment variables directly
   $env:MCP_PWSH_SERVER__PORT = 8080
   $env:MCP_PWSH_SECURITY__REQUIRE_API_KEY = "true"
   $env:MCP_PWSH_SECURITY__API_KEYS = "key1,key2"
   python server.py

   # Or use a .env file
   python server.py --env-file .env
   ```

3. **Command-line arguments**:

   ```powershell
   python server.py --port 8080 --host 0.0.0.0 --log-level DEBUG
   ```

### Configuration Options

| Category | Option                   | Description                                | Default                 |
| -------- | ------------------------ | ------------------------------------------ | ----------------------- |
| Security | `require_api_key`        | Whether API key authentication is required | `false`                 |
| Security | `api_keys`               | List of valid API keys                     | `[]`                    |
| Security | `execution_policy`       | PowerShell execution policy                | `Restricted`            |
| Security | `dangerous_patterns`     | Regex patterns for blocked commands        | See config.json.example |
| Logging  | `log_level`              | Logging level (DEBUG, INFO, etc.)          | `INFO`                  |
| Logging  | `log_format`             | Log format (text, json)                    | `text`                  |
| Logging  | `log_dir`                | Directory for log files                    | `logs`                  |
| Logging  | `command_history_dir`    | Directory for command history              | `command_history`       |
| Logging  | `enable_command_logging` | Whether to save command history            | `true`                  |
| Server   | `host`                   | Host to bind the server to                 | `127.0.0.1`             |
| Server   | `port`                   | Port to run the server on                  | `8000`                  |
| Server   | `cors_origins`           | List of allowed CORS origins               | `["*"]`                 |
| Server   | `default_timeout`        | Default timeout for commands (seconds)     | `30`                    |

A full configuration example is available in the `config.json.example` file.

## Docker Deployment

MCP PowerShell Exec server can be easily deployed using Docker for a consistent and isolated environment.

### Quick Start with Docker

```bash
# Build and run the Docker container
docker-compose up -d

# Check the logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Docker Configuration

The Docker deployment can be customized in several ways:

1. **Environment Variables**: Set environment variables in the `docker-compose.yml` file:

   ```yaml
   environment:
     - MCP_PWSH_SERVER__PORT=8080
     - MCP_PWSH_SECURITY__REQUIRE_API_KEY=true
     - MCP_PWSH_SECURITY__API_KEYS=your-secret-key
   ```

2. **Volume Mounting**: The Docker setup mounts several directories for persistence and configuration:

   ```yaml
   volumes:
     # Mount custom configuration
     - ./config.json:/app/config.json:ro
     # Mount logs directory
     - ./logs:/app/logs
     # Mount command history
     - ./command_history:/app/command_history
   ```

3. **Custom Building**: You can customize the Dockerfile for your specific requirements:

   ```bash
   # Build a custom image
   docker build -t custom-mcp-pwsh .
   ```

4. **Health Checks**: The Docker configuration includes health checks to monitor the service status.

### Running the Docker Container Behind a Proxy

For production deployments, we recommend running the Docker container behind a reverse proxy like Nginx or Traefik for enhanced security and SSL termination.

## Security and Authentication

### API Key Authentication

The server supports API key authentication to secure access to the PowerShell execution endpoints. To manage API keys:

```powershell
# Create a new API key
python auth_manager.py create --name "my-client"

# List existing API keys
python auth_manager.py list

# Remove an API key
python auth_manager.py remove "my-client"
```

To enable authentication, update your configuration:

1. **Using configuration file**:

   ```json
   {
     "security": {
       "require_api_key": true,
       "api_keys": ["your-secret-key-1", "your-secret-key-2"]
     }
   }
   ```

2. **Using environment variables**:

   ```powershell
   $env:MCP_PWSH_SECURITY__REQUIRE_API_KEY = "true"
   $env:MCP_PWSH_SECURITY__API_KEYS = "key1,key2,key3"
   ```

When making API requests to an authenticated server, include the API key in the header:

```
X-API-Key: your-secret-key
```

### PowerShell Security

The server implements security measures to prevent execution of potentially dangerous PowerShell commands:

1. All scripts run with a restricted execution policy
2. Commands matching dangerous patterns are blocked
3. Command history is logged for auditing
4. Commands run with configurable timeouts

You can customize the security settings in the configuration file.

## System Requirements

- **Python**: Version 3.10 or higher (required for optimal performance)
- **UV**: Python package manager (will be installed by installation script)
- **PowerShell**: Version 5.1 or higher

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:

- Create an issue in this GitHub repository
