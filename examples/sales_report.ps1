# A sample script to demonstrate data processing with PowerShell
# This script reads the sales.csv file and generates a summary report

# Check if the sales.csv file exists
if (-not (Test-Path -Path '../sales.csv')) {
	Write-Error 'sales.csv file not found. This script should be run from the examples directory.'
	exit 1
}

# Read the sales data
$salesData = Import-Csv -Path '../sales.csv'

# Calculate sales summary
$totalSales = $salesData | Measure-Object -Property 'Amount' -Sum | Select-Object -ExpandProperty Sum
$averageSale = $salesData | Measure-Object -Property 'Amount' -Average | Select-Object -ExpandProperty Average
$salesByCategory = $salesData | Group-Object -Property 'Category' |
	Select-Object Name, Count, @{Name = 'Total'; Expression = { ($_.Group | Measure-Object -Property 'Amount' -Sum).Sum } }

# Display summary
Write-Output '===== Sales Summary Report ====='
Write-Output ''
Write-Output "Total Sales: $($totalSales)"
Write-Output "Number of Transactions: $($salesData.Count)"
Write-Output "Average Sale: $([math]::Round($averageSale, 2))"
Write-Output ''
Write-Output 'Sales by Category:'
$salesByCategory | ForEach-Object {
	Write-Output "  $($_.Name): $($_.Count) sales, Total: $($_.Total)"
}

# Find top selling products
Write-Output ''
Write-Output 'Top 5 Products by Sales:'
$salesData | Group-Object -Property 'Product' |
	Select-Object Name, Count, @{Name = 'Total'; Expression = { ($_.Group | Measure-Object -Property 'Amount' -Sum).Sum } } |
	Sort-Object -Property Total -Descending |
	Select-Object -First 5 |
	ForEach-Object {
		Write-Output "  $($_.Name): $($_.Count) sales, Total: $($_.Total)"
	}
