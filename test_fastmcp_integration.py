#!/usr/bin/env python3
"""
Integration test for FastMCP PowerShell server modernization.
This verifies that our FastMCP conversion is working correctly.
"""

import asyncio
import json
import os
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.shared.memory import create_connected_server_and_client_session

from mcp_server import mcp


async def test_fastmcp_server():
    """Test that the FastMCP server works correctly."""
    print("Testing FastMCP PowerShell server...")

    try:
        # Create a client connected to our FastMCP server
        async with create_connected_server_and_client_session(
            mcp._mcp_server
        ) as client:
            print("✓ Successfully connected to FastMCP server")

            # Test initialization
            print("Testing server initialization...")
            # The connection itself validates initialization

            # Test listing tools
            print("Testing tools/list...")
            tools = await client.list_tools()
            print(f"✓ Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Verify we have the expected tools
            expected_tools = {
                "execute_powershell",
                "run_powershell_script",
                "test_powershell_safety",
            }
            actual_tools = {tool.name for tool in tools.tools}
            assert expected_tools.issubset(
                actual_tools
            ), f"Missing tools: {expected_tools - actual_tools}"
            print("✓ All expected tools found")

            # Test listing resources
            print("Testing resources/list...")
            resources = await client.list_resources()
            print(f"✓ Found {len(resources.resources)} resources:")
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.name}")

            # Test listing prompts
            print("Testing prompts/list...")
            prompts = await client.list_prompts()
            print(f"✓ Found {len(prompts.prompts)} prompts:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")

            # Test a simple tool call
            print("Testing tool execution...")
            result = await client.call_tool(
                "test_powershell_safety", {"command": "Get-Date"}
            )
            print("✓ Tool execution successful")

            # Parse and validate the result
            content = result.content[0].text
            response = json.loads(content)
            assert response["is_safe"] == True, "Get-Date should be safe"
            print("✓ Security check works correctly")

            print("\n🎉 All FastMCP integration tests passed!")
            return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fastmcp_server())
    sys.exit(0 if success else 1)
