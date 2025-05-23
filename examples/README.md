# MCP PowerShell Exec Examples

This directory contains example scripts and notebooks to help you get started with the MCP PowerShell Exec server.

## Example Files

### PowerShell Scripts

1. **system_info.ps1**

   - Gets detailed information about the system
   - Demonstrates how to use CIM instances and format output
   - Shows system specs, disk information, and process usage

2. **sales_report.ps1**
   - Processes CSV data to generate sales reports
   - Demonstrates data grouping and aggregation in PowerShell
   - Analyzes sales by category and product

### Python Examples

1. **usage_guide.ipynb**
   - Jupyter notebook showing how to interact with the MCP server from Python
   - Demonstrates all available API endpoints
   - Includes examples of error handling

## Running the Examples

### PowerShell Scripts

You can run these scripts through the MCP server using:

```powershell
# Start the server in one terminal
.\start-server.ps1

# In another terminal, run the script through the server
.\start-server.ps1 script .\examples\system_info.ps1
```

Or run them directly with PowerShell:

```powershell
cd examples
.\system_info.ps1
```

### Python Notebook

1. Start the MCP server in one terminal:

   ```powershell
   .\start-server.ps1
   ```

2. Open the Jupyter notebook in VS Code or Jupyter Lab:

   ```powershell
   jupyter lab examples/usage_guide.ipynb
   ```

   Or with VS Code:

   ```
   code examples/usage_guide.ipynb
   ```

3. Run the cells to see the examples in action

## Creating Your Own Examples

Feel free to modify these examples or create your own. The key components to understand are:

1. For direct PowerShell execution:

   - Scripts receive their content as input to the server
   - Standard output and error are captured and returned

2. For Python integration:
   - Use the HTTP endpoints to call the server
   - Format the JSON payload according to the API documentation
