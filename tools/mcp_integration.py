"""
MCP Integration Tool for P.U.L.S.E.
Provides a unified interface for interacting with Model Context Protocol servers
"""

import os
import sys
import json
import asyncio
from datetime import datetime
import structlog

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_yaml_config
from utils.mcp_manager import get_mcp_manager

# Get logger
logger = structlog.get_logger("mcp_integration")

class MCPIntegration:
    """Tool for interacting with Model Context Protocol servers."""

    def __init__(self, config_path="configs/mcp_config.yaml"):
        """Initialize MCP integration with configuration."""
        self.config_path = config_path
        self.logger = logger
        self.logger.debug(f"MCPIntegration initializing with config path: {config_path}")

        try:
            self.config = load_yaml_config(config_path)
            self.mcp_config = self.config.get('mcp_servers', {})
            self.enabled = self.mcp_config.get('enabled', True)

            # Initialize MCP server manager
            self.mcp_manager = get_mcp_manager(config_path)

            if self.enabled:
                self.logger.info("MCP integration enabled")
            else:
                self.logger.info("MCP integration disabled")
        except Exception as e:
            self.logger.error(f"Error initializing MCP integration: {str(e)}", exc_info=True)
            self.config = {}
            self.mcp_config = {}
            self.enabled = False
            self.mcp_manager = None

    def is_configured(self):
        """Check if MCP integration is properly configured."""
        configured = self.enabled and self.mcp_manager is not None
        self.logger.debug(f"MCP integration configured: {configured}")
        return configured

    async def start_servers(self, server_names=None):
        """
        Start MCP servers.

        Args:
            server_names: Optional list of server names to start. If None, starts all enabled servers.

        Returns:
            Dictionary with server names as keys and success status as values
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return {"error": "MCP integration is not configured"}

        try:
            if server_names:
                results = {}
                for name in server_names:
                    results[name] = await self.mcp_manager.start_server(name)
                return results
            else:
                return await self.mcp_manager.start_all_servers()
        except Exception as e:
            self.logger.error(f"Error starting MCP servers: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def stop_servers(self, server_names=None):
        """
        Stop MCP servers.

        Args:
            server_names: Optional list of server names to stop. If None, stops all running servers.

        Returns:
            Dictionary with server names as keys and success status as values
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return {"error": "MCP integration is not configured"}

        try:
            if server_names:
                results = {}
                for name in server_names:
                    results[name] = await self.mcp_manager.stop_server(name)
                return results
            else:
                return await self.mcp_manager.stop_all_servers()
        except Exception as e:
            self.logger.error(f"Error stopping MCP servers: {str(e)}", exc_info=True)
            return {"error": str(e)}

    def get_server_status(self, server_name=None):
        """
        Get status of MCP servers.

        Args:
            server_name: Optional name of specific server to check

        Returns:
            Dictionary with server status information
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return {"error": "MCP integration is not configured"}

        try:
            return self.mcp_manager.get_server_status(server_name)
        except Exception as e:
            self.logger.error(f"Error getting MCP server status: {str(e)}", exc_info=True)
            return {"error": str(e)}

    async def restart_server(self, server_name):
        """
        Restart a specific MCP server.

        Args:
            server_name: Name of the server to restart

        Returns:
            True if server restarted successfully, False otherwise
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return False

        try:
            return await self.mcp_manager.restart_server(server_name)
        except Exception as e:
            self.logger.error(f"Error restarting MCP server: {str(e)}", exc_info=True)
            return False

    def update_server_config(self, server_name, config_updates):
        """
        Update configuration for a specific MCP server.

        Args:
            server_name: Name of the server to update
            config_updates: Dictionary with configuration updates

        Returns:
            True if configuration updated successfully, False otherwise
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return False

        try:
            return self.mcp_manager.update_server_config(server_name, config_updates)
        except Exception as e:
            self.logger.error(f"Error updating MCP server configuration: {str(e)}", exc_info=True)
            return False

    def get_available_servers(self):
        """
        Get list of available MCP servers.

        Returns:
            List of server names
        """
        if not self.is_configured():
            self.logger.warning("MCP integration is not configured")
            return []

        try:
            servers = []
            for name, config in self.mcp_config.items():
                if name != 'enabled' and isinstance(config, dict) and config.get('enabled', True):
                    servers.append({
                        'name': name,
                        'description': config.get('description', ''),
                        'running': self.mcp_manager.is_server_running(name)
                    })
            return servers
        except Exception as e:
            self.logger.error(f"Error getting available MCP servers: {str(e)}", exc_info=True)
            return []

    def cleanup(self):
        """Clean up resources and stop all servers."""
        if self.mcp_manager:
            self.mcp_manager.cleanup()
        self.logger.info("MCP integration cleaned up")


# Global function for easier access from other modules
def is_mcp_configured():
    """External helper to check if MCP integration is configured"""
    try:
        mcp = MCPIntegration()
        return mcp.is_configured()
    except Exception as e:
        logger.error(f"Error checking MCP configuration: {str(e)}")
        return False
