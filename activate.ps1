# Simple wrapper script to activate the virtual environment

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ActivateScript = Join-Path -Path $ScriptDir -ChildPath '.venv\Scripts\Activate.ps1'

if (-not (Test-Path $ActivateScript)) {
	Write-Error 'Virtual environment not found. Please run .\install_deps.ps1 first.'
	exit 1
}

# Activate the virtual environment
& $ActivateScript

Write-Verbose 'Virtual environment activated!'
Write-Verbose 'To run the MCP server, use:'
Write-Verbose '    python mcp_server.py'
Write-Verbose '    - or -'
Write-Verbose '    uv run mcp_server.py   (if UV is installed)'
