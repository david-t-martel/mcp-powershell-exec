# MCP PowerShell Exec Server API Reference

This document describes the API endpoints provided by the MCP PowerShell Exec server.

## Base URL

By default, the server runs at `http://localhost:8000/`

## Authentication

The API supports API key authentication. This can be enabled in the configuration:

```json
{
  "security": {
    "require_api_key": true,
    "api_keys": ["your-secret-key-1", "your-secret-key-2"]
  }
}
```

When authentication is enabled, include the API key in your requests:

```
X-API-Key: your-secret-key-1
```

If no valid API key is provided, the server will respond with a `401 Unauthorized` error.

## Endpoints

### 1. Run PowerShell Command

**Endpoint:** `/mcp/tools/run_powershell`

**Method:** `POST`

**Description:** Execute a PowerShell command and return the result.

**Request Body:**

```json
{
  "code": "Get-Process | Select-Object -First 5",
  "timeout": 30
}
```

**Parameters:**

- `code` (string, required): The PowerShell code to execute.
- `timeout` (integer, optional): Maximum execution time in seconds. Default is 30.

**Response:**

```
Id      Name            CPU
--      ----            ---
19828   ApplicationFra  4.54...
14204   audiodg         6.81...
19080   chrome          0.56...
19276   chrome          0.05...
19548   chrome          0.08...
```

**Status Codes:**

- `200 OK`: Command executed successfully.
- `400 Bad Request`: Invalid parameters.
- `500 Internal Server Error`: Error executing the command.

### 2. Run PowerShell Command with Formatted Output

**Endpoint:** `/mcp/tools/run_powershell_formatted`

**Method:** `POST`

**Description:** Execute a PowerShell command and return the result in the specified format.

**Request Body:**

```json
{
  "code": "Get-Process | Select-Object -First 5 Id, ProcessName, CPU",
  "format": "json"
}
```

**Parameters:**

- `code` (string, required): The PowerShell code to execute.
- `format` (string, optional): Output format. Options are "text" (default), "json", "xml", or "csv".

**Response (JSON format):**

```json
[
  {
    "Id": 19828,
    "ProcessName": "ApplicationFrameHost",
    "CPU": 4.54
  },
  {
    "Id": 14204,
    "ProcessName": "audiodg",
    "CPU": 6.81
  }
]
```

**Status Codes:**

- `200 OK`: Command executed successfully.
- `400 Bad Request`: Invalid parameters or format.
- `500 Internal Server Error`: Error executing the command.

### 3. Run PowerShell Script

**Endpoint:** `/mcp/tools/run_powershell_script`

**Method:** `POST`

**Description:** Run a PowerShell script from content and return the output.

**Request Body:**

```json
{
  "script_content": "param($Name)\nWrite-Output \"Hello, $Name!\"",
  "args": "World"
}
```

**Parameters:**

- `script_content` (string, required): The content of the PowerShell script to run.
- `args` (string, optional): Space-separated arguments to pass to the script.

**Response:**

```
Hello, World!
```

**Status Codes:**

- `200 OK`: Script executed successfully.
- `400 Bad Request`: Invalid parameters.
- `500 Internal Server Error`: Error executing the script.

## Error Handling

All endpoints return an error message if execution fails. Error messages are prefixed with "Error:".

**Example Error Response:**

```
Error: The term 'Get-NonExistentCommand' is not recognized as a name of a cmdlet, function, script file, or executable program.
```

## Security Considerations

The server has security checks to block potentially dangerous commands. If a command is blocked, you'll receive an error message explaining why.

**Example Blocked Command Response:**

```
Error: Potentially dangerous command pattern detected: Format-Volume
```
