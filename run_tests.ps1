# Script to run tests for the MCP PowerShell Exec project

# Set environment variables
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path -Path $ScriptDir -ChildPath '.venv'
$ActivateScript = Join-Path -Path $VenvDir -ChildPath 'Scripts\Activate.ps1'
$TestDir = Join-Path -Path $ScriptDir -ChildPath 'tests'

# Check if virtual environment exists
if (-not (Test-Path $ActivateScript)) {
	Write-Error 'Virtual environment not found. Please run install_deps.ps1 first.'
	exit 1
}

# Activate the virtual environment
Write-Host 'Activating virtual environment...'
& $ActivateScript

# Run tests with pytest if available
if (Get-Command pytest -ErrorAction SilentlyContinue) {
	Write-Host 'Running tests with pytest...'
	if ($args.Length -gt 0) {
		# Run specific tests if arguments are provided
		pytest $TestDir $args -v
	} else {
		# Run all tests with coverage
		pytest $TestDir -v --cov=server
	}
} else {
	# Fall back to unittest
	Write-Host 'pytest not found, using unittest...'
	if (Test-Path $TestDir) {
		python -m unittest discover -s $TestDir -p 'test_*.py' -v
	} else {
		Write-Error "Test directory not found at $TestDir"
		exit 1
	}
}

Write-Host ''
Write-Host 'Tests completed!'
