"""
MCP PowerShell Exec Server - Authentication Management Tool

This script allows you to create, list, and remove API keys for authenticating
with the MCP PowerShell Exec Server.

Usage:
    python auth_manager.py create [--name NAME]
    python auth_manager.py list
    python auth_manager.py remove KEY
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from security import generate_api_key


def get_auth_file_path() -> Path:
    """Get the path to the authentication file."""
    script_dir = Path(__file__).parent.absolute()
    return script_dir / "auth_keys.json"


def load_keys() -> Dict[str, str]:
    """Load existing API keys."""
    auth_file = get_auth_file_path()
    if not auth_file.exists():
        return {}

    try:
        with open(auth_file, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading authentication file: {e}", file=sys.stderr)
        return {}


def save_keys(keys: Dict[str, str]) -> bool:
    """Save API keys to file."""
    auth_file = get_auth_file_path()
    try:
        with open(auth_file, "w") as f:
            json.dump(keys, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving authentication file: {e}", file=sys.stderr)
        return False


def create_key(name: Optional[str] = None) -> str:
    """Create a new API key."""
    keys = load_keys()
    new_key = generate_api_key()

    # If no name provided, use a default with a number
    if not name:
        existing_defaults = [k for k in keys.keys() if k.startswith("api_key_")]
        name = f"api_key_{len(existing_defaults) + 1}"

    keys[name] = new_key
    if save_keys(keys):
        return new_key
    return ""


def list_keys() -> List[Dict[str, str]]:
    """List all API keys."""
    keys = load_keys()
    return [{"name": name, "key": key} for name, key in keys.items()]


def remove_key(key_name: str) -> bool:
    """Remove an API key."""
    keys = load_keys()
    if key_name not in keys:
        print(f"Key '{key_name}' not found.", file=sys.stderr)
        return False

    del keys[key_name]
    return save_keys(keys)


def main():
    """Main entry point for the authentication manager."""
    parser = argparse.ArgumentParser(
        description="MCP PowerShell Exec Authentication Manager"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API key")
    create_parser.add_argument("--name", help="Name for the API key")

    # List command
    subparsers.add_parser("list", help="List all API keys")

    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an API key")
    remove_parser.add_argument("name", help="Name of the key to remove")

    # Parse arguments
    args = parser.parse_args()

    if args.command == "create":
        new_key = create_key(args.name)
        if new_key:
            print(f"Created new API key: {new_key}")
            print("Add this key to your configuration to enable authentication.")
        else:
            print("Failed to create API key.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "list":
        keys = list_keys()
        if not keys:
            print("No API keys found.")
        else:
            print(f"Found {len(keys)} API key(s):")
            for key_info in keys:
                print(f"Name: {key_info['name']}, Key: {key_info['key']}")

    elif args.command == "remove":
        if remove_key(args.name):
            print(f"Removed API key: {args.name}")
        else:
            print(f"Failed to remove API key: {args.name}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
