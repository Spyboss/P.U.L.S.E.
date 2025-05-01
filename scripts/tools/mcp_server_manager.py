#!/usr/bin/env python3
"""
MCP Server Manager Script for P.U.L.S.E.
Utility script to manage Model Context Protocol servers
"""

import os
import sys
import argparse
import asyncio
import json
from pathlib import Path

# Add parent directories to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.append(root_dir)

from tools.mcp_integration import MCPIntegration
import structlog
from utils.unified_logger import configure_logging

# Configure logging
configure_logging(log_file="logs/mcp_manager.log")
logger = structlog.get_logger("mcp_manager_script")

async def start_servers(args):
    """Start MCP servers."""
    mcp = MCPIntegration(args.config)

    if args.server:
        logger.info(f"Starting MCP server: {args.server}")
        result = await mcp.start_servers([args.server])
        print(f"Started server {args.server}: {result.get(args.server, False)}")
    else:
        logger.info("Starting all enabled MCP servers")
        result = await mcp.start_servers()
        print("Started servers:")
        for server, status in result.items():
            print(f"  - {server}: {'Success' if status else 'Failed'}")

async def stop_servers(args):
    """Stop MCP servers."""
    mcp = MCPIntegration(args.config)

    if args.server:
        logger.info(f"Stopping MCP server: {args.server}")
        result = await mcp.stop_servers([args.server])
        print(f"Stopped server {args.server}: {result.get(args.server, False)}")
    else:
        logger.info("Stopping all running MCP servers")
        result = await mcp.stop_servers()
        print("Stopped servers:")
        for server, status in result.items():
            print(f"  - {server}: {'Success' if status else 'Failed'}")

async def restart_servers(args):
    """Restart MCP servers."""
    mcp = MCPIntegration(args.config)

    if args.server:
        logger.info(f"Restarting MCP server: {args.server}")
        result = await mcp.restart_server(args.server)
        print(f"Restarted server {args.server}: {result}")
    else:
        logger.info("Restarting all MCP servers")
        # Stop all servers
        await mcp.stop_servers()
        # Start all servers
        result = await mcp.start_servers()
        print("Restarted servers:")
        for server, status in result.items():
            print(f"  - {server}: {'Success' if status else 'Failed'}")

def status(args):
    """Show status of MCP servers."""
    mcp = MCPIntegration(args.config)

    if args.server:
        logger.info(f"Getting status of MCP server: {args.server}")
        status = mcp.get_server_status(args.server)
        print(f"Status of server {args.server}:")
        print(json.dumps(status, indent=2))
    else:
        logger.info("Getting status of all MCP servers")
        status = mcp.get_server_status()
        print("MCP server status:")
        print(json.dumps(status, indent=2))

def list_servers(args):
    """List available MCP servers."""
    mcp = MCPIntegration(args.config)

    logger.info("Listing available MCP servers")
    servers = mcp.get_available_servers()

    print("Available MCP servers:")
    for server in servers:
        status = "Running" if server.get('running', False) else "Stopped"
        print(f"  - {server['name']}: {server.get('description', '')} [{status}]")

def update_config(args):
    """Update MCP server configuration."""
    mcp = MCPIntegration(args.config)

    if not args.server:
        print("Error: Server name is required for config update")
        return

    # Parse config updates
    updates = {}
    for update in args.updates:
        key, value = update.split('=', 1)

        # Convert value to appropriate type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)

        updates[key] = value

    logger.info(f"Updating configuration for MCP server: {args.server}")
    result = mcp.update_server_config(args.server, updates)

    if result:
        print(f"Updated configuration for server {args.server}")
    else:
        print(f"Failed to update configuration for server {args.server}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Manage MCP servers for P.U.L.S.E.")
    parser.add_argument('--config', default="configs/mcp_config.yaml", help="Path to MCP configuration file")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start MCP servers')
    start_parser.add_argument('--server', help='Name of specific server to start')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop MCP servers')
    stop_parser.add_argument('--server', help='Name of specific server to stop')

    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart MCP servers')
    restart_parser.add_argument('--server', help='Name of specific server to restart')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show status of MCP servers')
    status_parser.add_argument('--server', help='Name of specific server to check')

    # List command
    list_parser = subparsers.add_parser('list', help='List available MCP servers')

    # Config command
    config_parser = subparsers.add_parser('config', help='Update MCP server configuration')
    config_parser.add_argument('--server', required=True, help='Name of server to update')
    config_parser.add_argument('updates', nargs='+', help='Configuration updates in key=value format')

    args = parser.parse_args()

    if args.command == 'start':
        asyncio.run(start_servers(args))
    elif args.command == 'stop':
        asyncio.run(stop_servers(args))
    elif args.command == 'restart':
        asyncio.run(restart_servers(args))
    elif args.command == 'status':
        status(args)
    elif args.command == 'list':
        list_servers(args)
    elif args.command == 'config':
        update_config(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
