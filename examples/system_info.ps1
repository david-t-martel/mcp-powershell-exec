# A sample script to demonstrate the PowerShell script execution capability
# This script gets system information and formats it as a report

# Get basic system information
$computerSystem = Get-CimInstance -Class Win32_ComputerSystem
$computerBIOS = Get-CimInstance -Class Win32_BIOS
$computerOS = Get-CimInstance -Class Win32_OperatingSystem

# Display system information
Write-Output '===== System Information Report ====='
Write-Output ''
Write-Output "Computer Name: $($computerSystem.Name)"
Write-Output "Manufacturer: $($computerSystem.Manufacturer)"
Write-Output "Model: $($computerSystem.Model)"
Write-Output "Serial Number: $($computerBIOS.SerialNumber)"
Write-Output ''
Write-Output "Operating System: $($computerOS.Caption) $($computerOS.Version)"
Write-Output "Last Boot Time: $($computerOS.LastBootUpTime)"
Write-Output ''

# Get disk information
Write-Output '===== Disk Information ====='
Get-CimInstance -Class Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,
@{Name = 'Size(GB)'; Expression = { [math]::Round($_.Size / 1GB, 2) } },
@{Name = 'Free Space(GB)'; Expression = { [math]::Round($_.FreeSpace / 1GB, 2) } },
@{Name = 'Free(%)'; Expression = { [math]::Round(($_.FreeSpace / $_.Size) * 100, 2) } }

Write-Output ''

# Get top 5 processes by memory usage
Write-Output '===== Top 5 Processes by Memory Usage ====='
Get-Process | Sort-Object -Property WorkingSet64 -Descending | Select-Object -First 5 Name,
@{Name = 'Memory Usage(MB)'; Expression = { [math]::Round($_.WorkingSet64 / 1MB, 2) } },
CPU, Id
