# PowerShell CLI Demo for MCP Clients
# This script demonstrates useful Windows CLI operations that MCP clients can perform

Write-Host '=== MCP PowerShell CLI Capabilities Demo ===' -ForegroundColor Green

Write-Host "`n1. System Information:" -ForegroundColor Yellow
python mcp_server.py --execute 'Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, CsName, TotalPhysicalMemory' --format json

Write-Host "`n2. Available Disk Space:" -ForegroundColor Yellow
python mcp_server.py --execute "Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{Name='Size(GB)';Expression={[math]::Round($_.Used/1GB,2)}}, @{Name='Free(GB)';Expression={[math]::Round($_.Free/1GB,2)}}" --format json

Write-Host "`n3. Running Services (Top 5):" -ForegroundColor Yellow
python mcp_server.py --execute "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, Status -First 5" --format json

Write-Host "`n4. Network Adapters:" -ForegroundColor Yellow
python mcp_server.py --execute "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'} | Select-Object Name, InterfaceDescription, LinkSpeed" --format json

Write-Host "`n5. Current Directory Contents:" -ForegroundColor Yellow
python mcp_server.py --execute 'Get-ChildItem | Select-Object Name, Length, LastWriteTime -First 10' --format json

Write-Host "`n6. Environment Variables (selected):" -ForegroundColor Yellow
python mcp_server.py --execute "Get-ChildItem Env: | Where-Object {$_.Name -match 'PATH|TEMP|USER'} | Select-Object Name, Value" --format json

Write-Host "`n7. Security Test (should be blocked):" -ForegroundColor Red
python mcp_server.py --execute 'Format-Computer'

Write-Host "`n=== Demo Complete ===" -ForegroundColor Green
Write-Host 'These commands show how MCP clients like Claude Desktop can:' -ForegroundColor Cyan
Write-Host '  • Get system information' -ForegroundColor Cyan
Write-Host '  • Monitor system resources' -ForegroundColor Cyan
Write-Host '  • Check network status' -ForegroundColor Cyan
Write-Host '  • Browse files and directories' -ForegroundColor Cyan
Write-Host '  • Access environment variables' -ForegroundColor Cyan
Write-Host '  • All while maintaining security through command filtering' -ForegroundColor Cyan
