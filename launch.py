#!/usr/bin/env python3
"""
MCP PowerShell Server Launcher

Simple launcher script that handles common startup scenarios and provides
helpful error messages and debugging information.
"""

import argparse
import asyncio
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 10):
        print("❌ Python 3.10 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'mcp',
        'pydantic', 
        'click',
        'pyyaml',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print("❌ Missing required dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\nInstall with: pip install -r requirements.txt")
        return False
    
    return True


def check_powershell():
    """Check if PowerShell is available."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-Command", "echo 'test'"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


async def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="MCP PowerShell Server Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch.py                    # Start with default settings
  python launch.py --test             # Run tests first
  python launch.py --config my.json   # Use custom config
  python launch.py --debug            # Enable debug logging
  python launch.py --check-only       # Just check system requirements
        """
    )
    
    parser.add_argument("--test", action="store_true", 
                       help="Run tests before starting server")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check requirements, don't start server")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug logging")
    parser.add_argument("--env-file", help="Environment file path")
    
    args = parser.parse_args()
    
    print("🚀 MCP PowerShell Server Launcher")
    print("=" * 40)
    
    # System checks
    print("🔍 Checking system requirements...")
    
    if not check_python_version():
        return 1
    print("✅ Python version OK")
    
    if not check_dependencies():
        return 1
    print("✅ Dependencies OK")
    
    if not check_powershell():
        print("❌ PowerShell not available")
        print("   Make sure PowerShell is installed and in PATH")
        return 1
    print("✅ PowerShell available")
    
    if args.check_only:
        print("\n🎉 All system requirements satisfied!")
        return 0
    
    # Run tests if requested
    if args.test:
        print("\n🧪 Running tests...")
        try:
            from test_server import run_all_tests
            success = await run_all_tests()
            if not success:
                print("\n❌ Tests failed. Fix issues before starting server.")
                return 1
        except ImportError:
            print("❌ Test module not found")
            return 1
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return 1
    
    # Prepare server arguments
    server_args = []
    
    if args.config:
        server_args.extend(["--config", args.config])
    
    if args.env_file:
        server_args.extend(["--env-file", args.env_file])
    
    if args.debug:
        server_args.extend(["--log-level", "DEBUG"])
    
    # Start the server
    print("\n🌟 Starting MCP PowerShell Server...")
    print("   Press Ctrl+C to stop")
    
    try:
        # Import and run the server
        from mcp_server import main as server_main
        
        # Temporarily modify sys.argv for the server
        original_argv = sys.argv[:]
        sys.argv = ["mcp_server.py"] + server_args
        
        try:
            await server_main()
        finally:
            sys.argv = original_argv
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Server stopped by user")
        return 0
    except ImportError as e:
        print(f"\n❌ Failed to import server module: {e}")
        print("   Make sure all files are in place")
        return 1
    except Exception as e:
        print(f"\n💥 Server failed to start: {e}")
        print("\nFor debugging, try:")
        print("  python launch.py --debug")
        print("  python launch.py --test")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nLauncher error: {e}")
        sys.exit(1)
