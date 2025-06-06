"""
MCP resources providing PowerShell syntax and examples for LLMs.
"""

from mcp.server.fastmcp import FastMCP


def register_resources(mcp: FastMCP):
    """Register PowerShell resources for the MCP server."""

    # PowerShell cheatsheet resource
    mcp.resource(
        name="powershell_command_syntax",
        description="Common PowerShell command syntax reference",
        uri="/powershell/syntax",
        content="""
# PowerShell Command Syntax Reference

## Basic Commands

- **Get-Command**: List available commands
  ```powershell
  Get-Command -Name "*process*" -CommandType Cmdlet
  ```

- **Get-Help**: Get help documentation for commands
  ```powershell
  Get-Help Get-Process -Detailed
  ```

- **Get-Process**: List running processes
  ```powershell
  Get-Process | Sort-Object CPU -Descending | Select-Object -First 5
  ```

- **Get-Service**: List services
  ```powershell
  Get-Service | Where-Object {$_.Status -eq "Running"}
  ```

## File System Operations

- **Get-ChildItem**: List files and folders (like ls or dir)
  ```powershell
  Get-ChildItem -Path C:\\Windows -Filter *.exe -Recurse `
    -ErrorAction SilentlyContinue
  Get-ChildItem -Path C:\\Windows -Filter *.exe -Recurse -ErrorAction SilentlyContinue
  ```

- **New-Item**: Create new files or directories
  ```powershell
  New-Item -Path "C:\\temp\\test.txt" -ItemType File -Value "Hello, World!"
  New-Item -Path "C:\\temp\\newdir" -ItemType Directory
  ```

- **Copy-Item**: Copy files or directories
  ```powershell
  Copy-Item -Path "C:\\source\\file.txt" -Destination "C:\\dest\\file.txt"
  ```

- **Remove-Item**: Delete files or directories
  ```powershell
  Remove-Item -Path "C:\\temp\\file.txt"
  ```

## Data Manipulation

- **Select-Object**: Select properties from objects
  ```powershell
  Get-Process | Select-Object Name, CPU, WorkingSet
  ```

- **Where-Object**: Filter objects based on properties
  ```powershell
  Get-Process | Where-Object {$_.CPU -gt 10}
  ```

- **Sort-Object**: Sort objects
  ```powershell
  Get-Process | Sort-Object CPU -Descending
  ```

- **Group-Object**: Group objects by property
  ```powershell
  Get-Process | Group-Object Company
  ```

- **Measure-Object**: Calculate statistics
  ```powershell
  Get-Process | Measure-Object WorkingSet -Average -Sum -Maximum
  ```

## Output Formats

- **ConvertTo-Json**: Convert objects to JSON
  ```powershell
  Get-Process | Select-Object Name, CPU | ConvertTo-Json
  ```

- **ConvertTo-Csv**: Convert objects to CSV
  ```powershell
  Get-Process | Select-Object Name, CPU | ConvertTo-Csv
  ```

- **Export-Csv**: Export objects to a CSV file
  ```powershell
  Get-Process | Export-Csv -Path "processes.csv" -NoTypeInformation
  ```

- **Out-File**: Send output to a file
  ```powershell
  Get-Process | Out-File -FilePath "processes.txt"
  ```

## System Administration

- **Restart-Computer**: Restart the computer
  ```powershell
  Restart-Computer -ComputerName "ServerName" -Force
  ```

- **Get-EventLog**: Get event log entries
  ```powershell
  Get-EventLog -LogName System -Newest 10 -EntryType Error
  ```

- **Get-CimInstance**: Get WMI/CIM information
  ```powershell
  Get-CimInstance -ClassName Win32_OperatingSystem
  ```

- **Invoke-Command**: Run commands remotely
  ```powershell
  Invoke-Command -ComputerName "Server01" -ScriptBlock {Get-Service}
  ```
""",

    mcp.resource(
        name="powershell_scripting_examples",
        description="Examples of PowerShell scripts for common tasks",
        uri="/powershell/examples",
        content="""
# PowerShell Scripting Examples

## Basic Script Structure
## Basic Script Structure

```powershell
# Comments start with #
param (
    [string]$Name = "World"  # Default parameter value
)

# Function definition
function Say-Hello {
    param (
        [string]$Name
    )
    Write-Output "Hello, $Name!"
}

# Main script execution
Say-Hello -Name $Name
```

## Working with Variables

```powershell
$name = "John"
$age = 30
$isActive = $true
$items = @("apple", "banana", "orange")
$person = @{Name = "John"; Age = 30; IsActive = $true}

Write-Output "Name: $name, Age: $age"
Write-Output "First item: $($items[0])"
Write-Output "Person's name: $($person.Name)"
```

## Conditionals

```powershell
$number = 5

if ($number -gt 10) {
    Write-Output "Number is greater than 10"
}
elseif ($number -eq 10) {
    Write-Output "Number is equal to 10"
}
else {
    Write-Output "Number is less than 10"
}

# Switch statement
switch ($number) {
    {$_ -gt 10} { "Greater than 10"; break }
    10 { "Equal to 10"; break }
    default { "Less than 10" }
}
```

## Loops

```powershell
# For loop
for ($i = 1; $i -le 5; $i++) {
    Write-Output "Iteration $i"
}

# ForEach loop
$fruits = @("apple", "banana", "orange")
foreach ($fruit in $fruits) {
    Write-Output "Fruit: $fruit"
}

# While loop
$counter = 0
while ($counter -lt 5) {
    Write-Output "Counter: $counter"
    $counter++
}

# Do-While loop
$counter = 0
do {
    Write-Output "Counter: $counter"
    $counter++
} while ($counter -lt 5)
```

## Error Handling

```powershell
try {
    $result = 10 / 0
    Write-Output $result
}
catch {
    Write-Error "An error occurred: $_"
}
finally {
    Write-Output "This code always runs"
}
```

## Working with Files

```powershell
# Reading a file
$content = Get-Content -Path "C:\\path\\to\\file.txt"
foreach ($line in $content) {
    Write-Output $line
}

# Writing to a file
"Hello, World!" | Out-File -FilePath "C:\\path\\to\\output.txt"
Add-Content -Path "C:\\path\\to\\log.txt" -Value "$(Get-Date) - Script executed"

# Working with CSV
$users = Import-Csv -Path "users.csv"
foreach ($user in $users) {
    Write-Output "User: $($user.Name), Role: $($user.Role)"
}

$newUsers = @()
$newUsers += [PSCustomObject]@{Name = "John"; Role = "Admin"}
$newUsers += [PSCustomObject]@{Name = "Jane"; Role = "User"}
$newUsers | Export-Csv -Path "newusers.csv" -NoTypeInformation
```

## Working with APIs

```powershell
# Making a REST API call
$response = Invoke-RestMethod -Uri "https://api.example.com/data" -Method Get
$response | ConvertTo-Json -Depth 4

# Making a POST request with JSON body
$body = @{
    name = "John Doe"
    email = "john@example.com"
} | ConvertTo-Json

$headers = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer token123"
}

$response = Invoke-RestMethod -Uri "https://api.example.com/users" `
                             -Method Post `
                             -Body $body `
                             -Headers $headers

Write-Output "Created user with ID: $($response.id)"
```
""",
    mcp.resource(
"""
    )

    mcp.resource(
        name="powershell_best_practices",
        description="Best practices for PowerShell scripting",
        uri="/powershell/best-practices",
        content="""
## Naming Conventions

- **Use approved verbs**: PowerShell has a specific set of approved verbs
  ```powershell
  # Good
  Get-Process, Set-Variable, New-Item

  # Bad
  Fetch-Process, Change-Variable, Create-Item
  ```

- **Use singular nouns**: Use singular nouns for cmdlet names
  ```powershell
  # Good
  Get-User, Add-Member

  # Bad
  Get-Users, Add-Members
  ```

- **Use Pascal case for functions and cmdlets**
  ```powershell
  # Good
  function Get-UserProfile { }

  # Bad
  function get_user_profile { }
  ```

- **Use camelCase for variables and parameters**
  ```powershell
  # Good
  $userName, $currentStatus

  # Bad
  $UserName, $current_status
  ```

## Script Structure

- **Use comment-based help**: Document your functions and scripts
  ```powershell
  <#
  .SYNOPSIS
  Short description of what the script does.

  .DESCRIPTION
  Detailed description of what the script does.

  .PARAMETER Name
  Name parameter description.

  .EXAMPLE
  PS> .\MyScript.ps1 -Name "John"
  #>
  param (
      [string]$Name
  )
  ```

- **Declare mandatory parameters**: Use parameter attributes
  ```powershell
  param (
      [Parameter(Mandatory=$true)]
      [string]$ComputerName,

      [Parameter(Mandatory=$false)]
      [int]$Timeout = 30
  )
  ```

- **Use standard parameter names**: Use standard parameter names when possible
  ```powershell
  # Good
  param (
      [string]$ComputerName,
      [string]$Path
  )

  # Bad
  param (
      [string]$Computer,
      [string]$FilePath
  )
  ```

## Error Handling

- **Use Try-Catch-Finally blocks** for proper error handling
  ```powershell
  try {
      # Code that might generate an error
      Get-Content -Path $filePath -ErrorAction Stop
  }
  catch [System.IO.FileNotFoundException] {
      # Handle specific error
      Write-Error "File not found: $filePath"
  }
  catch {
      # Generic error handler
      Write-Error "An error occurred: $_"
  }
  finally {
      # Clean-up code that runs regardless of error
      Write-Output "Operation completed"
  }
  ```

- **Use -ErrorAction parameter**
  ```powershell
  # Stop execution on error
  Get-Content -Path $filePath -ErrorAction Stop

  # Continue execution on error
  Get-Content -Path $filePath -ErrorAction Continue

  # Silently ignore errors (use sparingly)
  Get-Content -Path $filePath -ErrorAction SilentlyContinue
  ```

## Performance

- **Use the pipeline efficiently**
  ```powershell
  # Good - processes one item at a time through pipeline
  Get-ChildItem | Where-Object { $_.Length -gt 1MB } | ForEach-Object { $_.Delete() }

  # Bad - loads everything into memory first
  $files = Get-ChildItem
  $largeFiles = $files | Where-Object { $_.Length -gt 1MB }
  foreach ($file in $largeFiles) {
      $file.Delete()
  }
  ```

- **Filter left, format right**
  ```powershell
  # Good - filter early in the pipeline
  Get-ChildItem -Filter "*.log" | Select-Object Name, Length

  # Bad - filter late in the pipeline
  Get-ChildItem | Where-Object { $_.Extension -eq ".log" } | Select-Object Name, Length
  ```

- **Avoid Write-Host** (use Write-Output, Write-Verbose, etc.)
  ```powershell
  # Good
  Write-Output "Operation successful"
  Write-Verbose "Processing file: $filePath"
  Write-Debug "Current value: $value"

  # Bad (unless specifically targeting the console)
  Write-Host "Operation successful"
  ```

## Security

- **Use the strictest execution policy appropriate**
  ```powershell
  # Set policy
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

- **Never store credentials in plain text**
  ```powershell
  # Good
  $credential = Get-Credential

  # Bad
  $username = "admin"
  $password = "password123"  # Never do this
  ```

- **Use SecureString for sensitive data**
  ```powershell
  $securePassword = Read-Host -AsSecureString "Enter password"
  $credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
    $securePassword = Read-Host -AsSecureString "Enter password"
    $credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
    ```
  """
    )

    mcp.resource(
        name="powershell_examples_for_llms",
        description="Examples of PowerShell commands specifically formatted for LLM consumption",
        uri="/powershell/llm-examples",
          uri="/powershell/llm-examples",
          content="""

### Get Basic System Information
```powershell
Get-ComputerInfo | Select-Object CsManufacturer, CsModel, WindowsVersion, OsName, OsVersion
```

### Get CPU Usage
```powershell
Get-Counter '\\Processor(_Total)\\% Processor Time' | Select-Object -ExpandProperty CounterSamples | Select-Object CookedValue
```

### Get Memory Usage
```powershell
Get-Counter '\\Memory\\Available MBytes' | Select-Object -ExpandProperty CounterSamples | Select-Object CookedValue
```

### Get Disk Space
```powershell
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{Name="Size(GB)";Expression={$_.Free/1GB}}
```

## File Operations

### Find Files by Pattern
```powershell
Get-ChildItem -Path 'C:\\' -Filter '*.log' -Recurse -ErrorAction SilentlyContinue
```

### Search Within Files
```powershell
Select-String -Path 'C:\\logs\\*.log' -Pattern 'error' -CaseSensitive:$false
```

### Get File Hash (for verification)
```powershell
Get-FileHash -Path 'C:\\path\\to\\file.exe' -Algorithm SHA256
```

## Network Operations

### Test Network Connection
```powershell
Test-NetConnection -ComputerName 'google.com' -Port 443
```

### Get IP Configuration
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Select-Object InterfaceAlias, IPAddress
```

### Check DNS Resolution
```powershell
Resolve-DnsName -Name 'github.com' -Type A
```

## Process Management

### Get Running Processes
```powershell
Get-Process | Sort-Object -Property CPU -Descending | Select-Object -First 10
```

### Start a Process
```powershell
Start-Process -FilePath 'notepad.exe' -ArgumentList 'C:\\temp\\file.txt'
```

### Stop a Process
```powershell
Stop-Process -Name 'notepad' -Force
```

## Data Conversion Examples

### Convert to JSON
```powershell
Get-Process | Select-Object Name, Id, CPU | ConvertTo-Json
```

### Parse JSON
```powershell
$json = '{"name":"test", "value":123}'
$object = $json | ConvertFrom-Json
$object.name
```

### Working with CSV
Get-Process | Select-Object Name, Id, CPU | Export-Csv -Path 'processes.csv' -NoTypeInformation
$data = Import-Csv -Path 'processes.csv'
$data = Import-Csv -Path 'processes.csv'
### Process Information
```powershell
Get-Process | Select-Object Name, Id, CPU, WorkingSet | ConvertTo-Json
```
Example output schema:
```json
[
  {
    "Name": "chrome",
    "Id": 1234,
    "CPU": 10.5,
    "WorkingSet": 150000000
  },
  {
    "Name": "explorer",
    "Id": 5678,
    "CPU": 5.2,
    "WorkingSet": 80000000
  }
]
```

### System Information
```powershell
[PSCustomObject]@{
    ComputerName = $env:COMPUTERNAME
    OSVersion = [System.Environment]::OSVersion.VersionString
    PowerShellVersion = $PSVersionTable.PSVersion.ToString()
    TotalMemory = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
    CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
} | ConvertTo-Json
```
Example output schema:
```json
{
  "ComputerName": "DESKTOP-ABC123",
  "OSVersion": "Microsoft Windows NT 10.0.19044.0",
  "PowerShellVersion": "7.3.4",
  "TotalMemory": 16.0,
  "CurrentUser": "DOMAIN\\username"
}
```

### File Information
```powershell
Get-ChildItem -Path 'C:\\Windows' -File | Select-Object Name, Length, LastWriteTime | ConvertTo-Json
```
Example output schema:
```json
[
  {
    "Name": "notepad.exe",
    "Length": 204800,
    "LastWriteTime": "2023-10-15T14:30:00"
  },
  {
    "Name": "explorer.exe",
    "Length": 4596224,
    "LastWriteTime": "2023-10-15T14:30:00"
  }
]
```

## CSV Output Example
```powershell
Get-Service | Select-Object Name, DisplayName, Status | ConvertTo-Csv -NoTypeInformation
```
Example output:
```
"Name","DisplayName","Status"
"AdobeARMservice","Adobe Acrobat Update Service","Running"
"AJRouter","AllJoyn Router Service","Stopped"
"ALG","Application Layer Gateway Service","Stopped"
```

## XML Output Example
```powershell
Get-Process | Select-Object Name, Id | ConvertTo-Xml -As String
```
Example output:
```xml
<?xml version="1.0" encoding="utf-8"?>
<Objects>
  <Object Type="System.Management.Automation.PSCustomObject">
    <Property Name="Name" Type="System.String">chrome</Property>
    <Property Name="Id" Type="System.Int32">1234</Property>
  </Object>
  <Object Type="System.Management.Automation.PSCustomObject">
    <Property Name="Name" Type="System.String">explorer</Property>
    <Property Name="Id" Type="System.Int32">5678</Property>
  </Object>
</Objects>
```

## Table Output Format
When PowerShell output is displayed as text, it's typically formatted as a table:

```
Name      Id    CPU WorkingSet
----      --    --- ----------
chrome    1234 10.5  150000000
explorer  5678  5.2   80000000
```

Parsing tip: Each line represents an object, columns are separated by whitespace, and the first line contains headers.
""",
    )

""",
    )

    mcp.resource(
        name="powershell_api_response_schemas",
        description="Examples of PowerShell output formats that can be used by LLMs for parsing",
        uri="/powershell/api-schemas",
        content="""
### Process Information
