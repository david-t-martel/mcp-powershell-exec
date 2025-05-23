# Script to activate the virtual environment and start the server

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path -Path $ScriptDir -ChildPath '.venv'
$ActivateScript = Join-Path -Path $VenvDir -ChildPath 'Scripts\Activate.ps1'
$ServerScript = Join-Path -Path $ScriptDir -ChildPath 'server.py'

if (-not (Test-Path $VenvDir)) {
	Write-Host 'Virtual environment not found. Setting up now...'
	$InstallScript = Join-Path -Path $ScriptDir -ChildPath 'install_deps.ps1'
	& $InstallScript
	if (-not $?) {
		Write-Error 'Failed to set up virtual environment. Please run install_deps.ps1 manually.'
		exit 1
	}
} else {
	# Activate the virtual environment
	& $ActivateScript
}

# Start the server
Write-Host 'Starting MCP PowerShell Exec Server...'
$Params = $args

if (Get-Command uv -ErrorAction SilentlyContinue) {
	# If UV is available, use it
	uv run $ServerScript @Params
} else {
	# Otherwise use standard Python
	python $ServerScript @Params
}
