# MCP PowerShell CLI Usage Guide

This guide shows how to use the MCP PowerShell server to provide CLI capabilities to MCP clients like Claude Desktop.

## Overview

The MCP PowerShell server allows MCP clients to execute PowerShell commands on Windows machines securely. This enables Claude Desktop to:

- Get system information (OS version, hardware specs, etc.)
- Monitor system resources (CPU, memory, disk space)
- Manage files and directories
- Check network status
- View running processes and services
- Access environment variables
- Execute custom scripts safely

## Available MCP Tools

### 1. `execute_powershell`

Execute PowerShell commands with various output formats.

**Parameters:**

- `command` (required): PowerShell command to execute
- `timeout` (optional): Execution timeout in seconds (1-300)
- `format` (optional): Output format - "text", "json", "xml", or "csv"

**Example Commands:**

#### System Information

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, CsName
```

#### Disk Space

```powershell
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{Name='Free(GB)';Expression={[math]::Round($_.Free/1GB,2)}}
```

#### Running Processes

```powershell
Get-Process | Select-Object Name, CPU, WorkingSet | Sort-Object CPU -Descending | Select-Object -First 10
```

#### Network Adapters

```powershell
Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription
```

#### Current Directory

```powershell
Get-ChildItem | Select-Object Name, Length, LastWriteTime
```

### 2. `run_powershell_script`

Execute PowerShell scripts with arguments.

**Parameters:**

- `script` (required): PowerShell script content
- `arguments` (optional): Array of arguments to pass to script
- `timeout` (optional): Execution timeout in seconds

**Example:**

```powershell
param($Name)
Write-Host "Hello, $Name!"
Get-Date
```

### 3. `test_powershell_safety`

Test if a command is safe to execute (security check only).

**Parameters:**

- `command` (required): PowerShell command to test

## Security Features

The server includes multiple security layers:

### Blocked Commands

- `Format-Computer`
- `Remove-Computer`
- `Reset-ComputerMachinePassword`
- `Restart-Computer`
- `Stop-Computer`

### Dangerous Pattern Detection

- Recursive file deletion (`Remove-Item ... -Recurse`)
- Volume formatting (`Format-Volume`)
- Execution policy changes (`Set-ExecutionPolicy Unrestricted`)
- Web script execution (`Invoke-Expression ... Invoke-WebRequest`)
- Administrative elevation (`Start-Process ... -Verb RunAs`)
- Service manipulation
- Registry access

### Other Protections

- Command length limits (configurable, default 10,000 chars)
- Execution timeouts (configurable, default 30 seconds)
- Restricted execution policy
- Command logging for auditing

## Common Use Cases for MCP Clients

### 1. System Monitoring

```powershell
# CPU and Memory usage
Get-Counter "\\Processor(_Total)\\% Processor Time", "\\Memory\\Available MBytes"

# Disk usage by drive
Get-WmiObject -Class Win32_LogicalDisk | Select-Object DeviceID, @{Name="Size(GB)";Expression={[math]::Round($_.Size/1GB,2)}}, @{Name="Free(GB)";Expression={[math]::Round($_.FreeSpace/1GB,2)}}
```

### 2. File Operations

```powershell
# Search for files
Get-ChildItem -Path C:\\ -Filter "*.log" -Recurse -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime

# Get file content (first 20 lines)
Get-Content "C:\\Windows\\System32\\drivers\\etc\\hosts" | Select-Object -First 20
```

### 3. Network Information

```powershell
# Network connections
Get-NetTCPConnection | Where-Object {$_.State -eq "Established"} | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort

# IP configuration
Get-NetIPAddress | Where-Object {$_.AddressFamily -eq "IPv4"} | Select-Object InterfaceAlias, IPAddress, PrefixLength
```

### 4. Process Management

```powershell
# Find specific processes
Get-Process | Where-Object {$_.ProcessName -like "*chrome*"} | Select-Object Name, CPU, WorkingSet

# Process with highest CPU usage
Get-Process | Sort-Object CPU -Descending | Select-Object -First 5 Name, CPU, WorkingSet
```

### 5. Windows Services

```powershell
# Running services
Get-Service | Where-Object {$_.Status -eq "Running"} | Select-Object Name, Status, StartType

# Specific service status
Get-Service -Name "Windows Update" | Select-Object Name, Status, StartType
```

## Claude Desktop Integration

1. Add the server to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "powershell-cli": {
      "command": "python",
      "args": ["C:\\path\\to\\mcp-powershell-exec\\mcp_server.py"],
      "env": {
        "MCP_PWSH_LOGGING__LOG_LEVEL": "INFO",
        "MCP_PWSH_SECURITY__EXECUTION_POLICY": "RemoteSigned"
      }
    }
  }
}
```

2. Restart Claude Desktop

3. You can now ask Claude to:
   - "Check my system's disk space"
   - "Show me the top 5 processes using the most CPU"
   - "List all running Windows services"
   - "What's my current IP address?"
   - "Find all .log files in my system"

## Best Practices

1. **Use specific commands**: Be precise about what information you need
2. **Limit output**: Use `Select-Object -First N` to avoid overwhelming responses
3. **Use formatting**: Request JSON format for structured data
4. **Be patient**: Some commands may take time, especially system queries
5. **Check safety**: Use the safety check tool for unfamiliar commands

## Troubleshooting

### Common Issues

- **Timeout errors**: Increase timeout or simplify the command
- **Access denied**: Some operations require administrator privileges
- **Command blocked**: The security system blocked a potentially dangerous command
- **No output**: Command executed but produced no results

### Logs

Check the logs directory for detailed execution logs and command history.

## Example Session

**User:** "Can you check my system information?"

**Claude:** I'll check your system information using PowerShell.

_[Uses execute_powershell tool with Get-ComputerInfo command]_

**Result:** Shows Windows version, computer name, memory, etc.

**User:** "What processes are using the most CPU?"

**Claude:** Let me check the top CPU-consuming processes.

_[Uses execute_powershell tool with Get-Process command, sorted by CPU]_

**Result:** Shows top 10 processes with CPU usage data.

This integration allows Claude Desktop to become a powerful system administration assistant for Windows machines while maintaining security and safety.
