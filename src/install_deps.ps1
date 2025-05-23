# install_deps.ps1
# Setup virtual environment and install dependencies
param (
	[switch]$Dev = $false,
	[switch]$Force = $false
)

# Set environment variables
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path -Path $ScriptDir -ChildPath '.venv'
$ActivateScript = Join-Path -Path $VenvDir -ChildPath 'Scripts\Activate.ps1'

Write-Host "Setting up Python virtual environment in $VenvDir"

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
	Write-Error 'Python is not installed or not in PATH. Please install Python and try again.'
	exit 1
}

# Create virtual environment if it doesn't exist or force recreate
if ((-not (Test-Path $VenvDir)) -or $Force) {
	if ($Force -and (Test-Path $VenvDir)) {
		Write-Host 'Removing existing virtual environment...'
		Remove-Item -Recurse -Force $VenvDir
	}
	Write-Host 'Creating virtual environment...'
	python -m venv $VenvDir
	if (-not $?) {
		Write-Error 'Failed to create virtual environment. Please check if the venv module is available.'
		exit 1
	}
} else {
	Write-Host 'Virtual environment already exists.'
}

# Check if the activation script exists
if (-not (Test-Path $ActivateScript)) {
	Write-Error 'Activation script not found. Virtual environment may be corrupted.'
	exit 1
}

# Activate the virtual environment
Write-Host 'Activating virtual environment...'
& $ActivateScript

if (-not $?) {
	Write-Error 'Failed to activate virtual environment.'
	exit 1
}

# Install dependencies
if ($Dev) {
	Write-Host 'Installing development dependencies...'
	$ReqFile = 'requirements-dev.txt'
} else {
	Write-Host 'Installing standard dependencies...'
	$ReqFile = 'requirements.txt'
}

if (Get-Command uv -ErrorAction SilentlyContinue) {
	Write-Host 'Using UV package manager...'
	uv pip install --upgrade pip
	uv pip install -r $ReqFile
} else {
	Write-Host 'Using standard pip...'
	python -m pip install --upgrade pip
	python -m pip install -r $ReqFile
}

if (-not $?) {
	Write-Error 'Failed to install dependencies.'
	exit 1
}

Write-Host ''
Write-Host '========================================================'
if ($Dev) {
	Write-Host 'Development dependencies installed successfully!'
} else {
	Write-Host 'Dependencies installed successfully!'
}
Write-Host 'To activate the virtual environment in a new PowerShell session, run:'
Write-Host '    .\.venv\Scripts\Activate.ps1'
Write-Host ''
Write-Host 'For development environment:'
Write-Host '    .\install_deps.ps1 -Dev'
Write-Host ''
Write-Host 'To force recreation of the virtual environment:'
Write-Host '    .\install_deps.ps1 -Force'
Write-Host '========================================================'
