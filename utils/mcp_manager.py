"""
MCP Server Manager for P.U.L.S.E.
Handles initialization and management of Model Context Protocol servers
"""

import os
import sys
import json
import subprocess
import asyncio
import signal
from pathlib import Path
import structlog
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_yaml_config, save_yaml_config, ensure_directory_exists

# Set up logger
logger = structlog.get_logger("mcp_manager")

class MCPServerManager:
    """
    Manager for Model Context Protocol servers.
    Handles initialization, configuration, and management of MCP servers.
    """

    def __init__(self, config_path="configs/mcp_config.yaml"):
        """
        Initialize the MCP Server Manager.

        Args:
            config_path: Path to the MCP configuration file
        """
        self.config_path = config_path
        self.servers = {}
        self.processes = {}
        self.config = self._load_config()
        self.enabled = self.config.get('mcp_servers', {}).get('enabled', True)

        # Create directory for MCP server logs
        self.log_dir = Path("logs/mcp_servers")
        ensure_directory_exists(self.log_dir)

        logger.info("MCP Server Manager initialized",
                   enabled=self.enabled,
                   config_path=config_path)

    def _load_config(self):
        """Load MCP server configuration."""
        try:
            config = load_yaml_config(self.config_path)
            if not config:
                logger.warning("MCP configuration not found or empty, using defaults")
                return {'mcp_servers': {'enabled': True}}
            return config
        except Exception as e:
            logger.error("Error loading MCP configuration", error=str(e))
            return {'mcp_servers': {'enabled': True}}

    def _resolve_env_vars(self, env_dict):
        """
        Resolve environment variables in the configuration.

        Args:
            env_dict: Dictionary of environment variables

        Returns:
            Dictionary with resolved environment variables
        """
        resolved = {}
        for key, value in env_dict.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                resolved[key] = os.environ.get(env_var, "")
                if not resolved[key]:
                    logger.warning(f"Environment variable {env_var} not set for MCP server")
            else:
                resolved[key] = value
        return resolved

    async def start_server(self, server_name):
        """
        Start a specific MCP server.

        Args:
            server_name: Name of the server to start

        Returns:
            True if server started successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("MCP servers are disabled in configuration")
            return False

        server_config = self.config.get('mcp_servers', {}).get(server_name)
        if not server_config:
            logger.error(f"Server configuration not found for {server_name}")
            return False

        if not server_config.get('enabled', True):
            logger.info(f"Server {server_name} is disabled in configuration")
            return False

        if server_name in self.processes and self.processes[server_name].poll() is None:
            logger.info(f"Server {server_name} is already running")
            return True

        try:
            command = server_config.get('command', 'npm')
            args = server_config.get('args', [])
            env_vars = self._resolve_env_vars(server_config.get('env', {}))

            # Prepare environment
            env = os.environ.copy()
            env.update(env_vars)

            # Prepare log files
            log_file = self.log_dir / f"{server_name}.log"

            # Start the server process
            # Use npm exec instead of npx
            if command == 'npx':
                command = 'npm'
                args = ['exec', '--yes'] + args[1:]  # Replace -y with --yes

            cmd = [command] + args
            logger.info(f"Starting MCP server: {server_name}", command=cmd)

            with open(log_file, 'a') as log:
                process = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            self.processes[server_name] = process
            self.servers[server_name] = {
                'pid': process.pid,
                'config': server_config,
                'started_at': datetime.now().isoformat()
            }

            logger.info(f"Started MCP server: {server_name}", pid=process.pid)
            return True

        except Exception as e:
            logger.error(f"Error starting MCP server: {server_name}", error=str(e))
            return False

    async def start_all_servers(self):
        """
        Start all enabled MCP servers.

        Returns:
            Dictionary with server names as keys and success status as values
        """
        if not self.enabled:
            logger.warning("MCP servers are disabled in configuration")
            return {}

        results = {}
        server_configs = self.config.get('mcp_servers', {})

        for server_name, server_config in server_configs.items():
            if server_name != 'enabled' and server_config.get('enabled', True):
                results[server_name] = await self.start_server(server_name)

        return results

    async def stop_server(self, server_name):
        """
        Stop a specific MCP server.

        Args:
            server_name: Name of the server to stop

        Returns:
            True if server stopped successfully, False otherwise
        """
        if server_name not in self.processes:
            logger.warning(f"Server {server_name} is not running")
            return False

        process = self.processes[server_name]
        if process.poll() is not None:
            logger.info(f"Server {server_name} is already stopped")
            self.processes.pop(server_name)
            return True

        try:
            logger.info(f"Stopping MCP server: {server_name}", pid=process.pid)

            # Try graceful termination first
            process.terminate()

            # Wait for process to terminate
            for _ in range(5):
                if process.poll() is not None:
                    break
                await asyncio.sleep(1)

            # Force kill if still running
            if process.poll() is None:
                logger.warning(f"Forcefully killing MCP server: {server_name}", pid=process.pid)
                process.kill()

            self.processes.pop(server_name)
            if server_name in self.servers:
                self.servers.pop(server_name)

            logger.info(f"Stopped MCP server: {server_name}")
            return True

        except Exception as e:
            logger.error(f"Error stopping MCP server: {server_name}", error=str(e))
            return False

    async def stop_all_servers(self):
        """
        Stop all running MCP servers.

        Returns:
            Dictionary with server names as keys and success status as values
        """
        results = {}
        server_names = list(self.processes.keys())

        for server_name in server_names:
            results[server_name] = await self.stop_server(server_name)

        return results

    def get_server_status(self, server_name=None):
        """
        Get status of MCP servers.

        Args:
            server_name: Optional name of specific server to check

        Returns:
            Dictionary with server status information
        """
        if server_name:
            if server_name not in self.processes:
                return {
                    'name': server_name,
                    'running': False,
                    'enabled': self.config.get('mcp_servers', {}).get(server_name, {}).get('enabled', True)
                }

            process = self.processes[server_name]
            return {
                'name': server_name,
                'running': process.poll() is None,
                'pid': process.pid if process.poll() is None else None,
                'enabled': self.config.get('mcp_servers', {}).get(server_name, {}).get('enabled', True),
                'info': self.servers.get(server_name, {})
            }

        # Return status of all servers
        status = {}
        server_configs = self.config.get('mcp_servers', {})

        for name, config in server_configs.items():
            if name != 'enabled':
                status[name] = self.get_server_status(name)

        return status

    def is_server_running(self, server_name):
        """
        Check if a specific MCP server is running.

        Args:
            server_name: Name of the server to check

        Returns:
            True if server is running, False otherwise
        """
        if server_name not in self.processes:
            return False

        process = self.processes[server_name]
        return process.poll() is None

    async def restart_server(self, server_name):
        """
        Restart a specific MCP server.

        Args:
            server_name: Name of the server to restart

        Returns:
            True if server restarted successfully, False otherwise
        """
        await self.stop_server(server_name)
        return await self.start_server(server_name)

    def update_server_config(self, server_name, config_updates):
        """
        Update configuration for a specific MCP server.

        Args:
            server_name: Name of the server to update
            config_updates: Dictionary with configuration updates

        Returns:
            True if configuration updated successfully, False otherwise
        """
        try:
            if 'mcp_servers' not in self.config:
                self.config['mcp_servers'] = {}

            if server_name not in self.config['mcp_servers']:
                self.config['mcp_servers'][server_name] = {}

            # Update configuration
            self.config['mcp_servers'][server_name].update(config_updates)

            # Save updated configuration
            save_yaml_config(self.config, self.config_path)

            logger.info(f"Updated configuration for MCP server: {server_name}")
            return True

        except Exception as e:
            logger.error(f"Error updating MCP server configuration: {server_name}", error=str(e))
            return False

    def cleanup(self):
        """Clean up resources and stop all servers."""
        asyncio.run(self.stop_all_servers())
        logger.info("MCP Server Manager cleaned up")


# Singleton instance
_instance = None

def get_mcp_manager(config_path="configs/mcp_config.yaml"):
    """
    Get the singleton instance of the MCP Server Manager.

    Args:
        config_path: Path to the MCP configuration file

    Returns:
        MCPServerManager instance
    """
    global _instance
    if _instance is None:
        _instance = MCPServerManager(config_path)
    return _instance
