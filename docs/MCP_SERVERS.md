# MCP Servers in P.U.L.S.E.

## Overview

Model Context Protocol (MCP) servers enable P.U.L.S.E. to interact with external tools and services through a standardized interface. This document explains how to use and configure MCP servers in P.U.L.S.E.

## What is MCP?

MCP (Model Context Protocol) is an open standard that allows AI models to securely interact with local and remote resources. It acts as a bridge between P.U.L.S.E. and tools like GitHub, file systems, web browsers, and more.

## Installed MCP Servers

P.U.L.S.E. comes with several MCP servers pre-installed:

1. **File System MCP Server** - Access and manage local files
2. **GitHub MCP Server** - Interact with GitHub repositories
3. **Brave Search MCP Server** - Search the web using Brave Search
4. **Google Maps MCP Server** - Access location and mapping data
5. **PostgreSQL MCP Server** - Interact with PostgreSQL databases
6. **Puppeteer MCP Server** - Automate web browser interactions
7. **Sequential Thinking MCP Server** - Enhanced problem-solving capabilities
8. **Smart Crawler MCP Server** - Crawl and extract web content

## Configuration

MCP servers are configured in `configs/mcp_config.yaml`. Each server has its own configuration section with the following properties:

- `enabled` - Whether the server is enabled
- `description` - Description of the server
- `command` - Command to run the server (usually `npx`)
- `args` - Arguments to pass to the command
- `env` - Environment variables for the server

Example configuration:

```yaml
# MCP server settings
mcp_servers:
  enabled: true

  # File System MCP Server
  filesystem:
    enabled: true
    description: "Access and manage local files"
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem"]
    env:
      DIRECTORIES: "C:/Users/UMINDA/Desktop/P.U.L.S.E"
```

## Auto-Starting MCP Servers

P.U.L.S.E. can automatically start MCP servers when it starts. This is configured in `configs/agent_config.yaml`:

```yaml
tools:
  mcp_integration:
    enabled: true
    auto_start: true
    default_servers: ["filesystem", "github", "brave_search", "puppeteer"]
```

- `enabled` - Whether MCP integration is enabled
- `auto_start` - Whether to automatically start servers on startup
- `default_servers` - List of servers to auto-start (if empty, all enabled servers are started)

## Managing MCP Servers

P.U.L.S.E. includes a command-line tool for managing MCP servers. You can use it to start, stop, restart, and check the status of MCP servers.

```bash
# Start all enabled MCP servers
python scripts/tools/mcp_server_manager.py start

# Start a specific MCP server
python scripts/tools/mcp_server_manager.py start --server filesystem

# Stop all running MCP servers
python scripts/tools/mcp_server_manager.py stop

# Stop a specific MCP server
python scripts/tools/mcp_server_manager.py stop --server filesystem

# Restart a specific MCP server
python scripts/tools/mcp_server_manager.py restart --server filesystem

# Check status of all MCP servers
python scripts/tools/mcp_server_manager.py status

# Check status of a specific MCP server
python scripts/tools/mcp_server_manager.py status --server filesystem

# List available MCP servers
python scripts/tools/mcp_server_manager.py list

# Update MCP server configuration
python scripts/tools/mcp_server_manager.py config --server filesystem enabled=true
```

## Using MCP Servers in P.U.L.S.E.

MCP servers are automatically used by P.U.L.S.E. when needed. For example, when you ask P.U.L.S.E. to search the web, it will use the Brave Search MCP server. When you ask it to interact with GitHub, it will use the GitHub MCP server.

### Implementation Details

P.U.L.S.E. integrates MCP servers through the following components:

1. **MCPIntegration Tool** (`tools/mcp_integration.py`) - Provides a unified interface for interacting with MCP servers
2. **MCP Server Manager** (`utils/mcp_manager.py`) - Manages the lifecycle of MCP servers (starting, stopping, etc.)
3. **MCP Configuration** (`configs/mcp_config.yaml`) - Defines the configuration for each MCP server

The integration follows these principles:

- **Lazy Loading** - MCP servers are only started when needed to conserve resources
- **Graceful Degradation** - P.U.L.S.E. continues to function even if MCP servers are unavailable
- **Secure Communication** - All communication with MCP servers is done through a secure channel
- **Resource Management** - MCP servers are properly cleaned up when no longer needed

### Programmatic Usage

You can use the MCP integration in your own code:

```python
from tools.mcp_integration import MCPIntegration

# Initialize MCP integration
mcp = MCPIntegration()

# Start specific servers
await mcp.start_servers(["filesystem", "github"])

# Check server status
status = mcp.get_server_status("filesystem")
print(status)

# Stop servers when done
await mcp.stop_servers()
```

### Example Use Cases

1. **File System MCP Server**

   - "Create a new file in my project directory"
   - "List all Python files in the current directory"
   - "Organize my downloads folder by file type"

2. **GitHub MCP Server**

   - "Create a new issue in my repository"
   - "Check the status of my pull requests"
   - "Clone a repository to my local machine"

3. **Brave Search MCP Server**

   - "Search for the latest news on AI"
   - "Find information about Python programming"
   - "Look up the weather forecast for today"

4. **Puppeteer MCP Server**
   - "Take a screenshot of a website"
   - "Fill out a form on a website"
   - "Automate a repetitive web task"

## Troubleshooting

If you encounter issues with MCP servers, check the following:

1. **Logs** - Check the logs in `logs/mcp_servers/` for error messages
2. **Configuration** - Verify that the server is properly configured in `configs/mcp_config.yaml`
3. **Dependencies** - Make sure all required dependencies are installed
4. **Environment Variables** - Verify that all required environment variables are set
5. **Node.js Version** - Ensure you have Node.js 16+ installed
6. **NPM Permissions** - Make sure you have the necessary permissions to install and run npm packages

### Common Issues and Solutions

#### Server Fails to Start

If a server fails to start, check the following:

1. **Log Files** - Check the server's log file in `logs/mcp_servers/[server_name].log`
2. **Command Path** - Verify that the command path in the configuration is correct
3. **Environment Variables** - Make sure all required environment variables are set
4. **Port Conflicts** - Check if another process is using the same port

#### Server Crashes Frequently

If a server crashes frequently, try the following:

1. **Update the Server** - Update to the latest version of the MCP server
2. **Increase Memory** - Allocate more memory to the server process
3. **Check Dependencies** - Verify that all dependencies are installed and up to date
4. **Restart the Server** - Sometimes a simple restart can fix issues

## Adding New MCP Servers

To add a new MCP server:

1. Install the server using npm or npx
2. Add the server configuration to `configs/mcp_config.yaml`
3. Restart P.U.L.S.E. or use the MCP server manager to start the new server

Example:

```bash
# Install a new MCP server
npx -y @modelcontextprotocol/server-new-server

# Add configuration to configs/mcp_config.yaml
# ...

# Start the new server
python scripts/tools/mcp_server_manager.py start --server new_server
```

## API Keys and Security

Some MCP servers require API keys or other credentials to function. These should be stored as environment variables in your `.env` file. Never hardcode API keys in configuration files.

Example `.env` entries:

```
GITHUB_TOKEN=your_github_token
BRAVE_API_KEY=your_brave_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

## Performance Considerations

MCP servers can consume significant system resources, especially when running multiple servers simultaneously. Consider the following performance optimizations:

1. **Selective Enabling** - Only enable the MCP servers you actually need
2. **Lazy Loading** - Use the `auto_start: false` option and start servers only when needed
3. **Resource Limits** - Set resource limits for MCP servers to prevent them from consuming too much memory or CPU
4. **Cleanup** - Always stop MCP servers when they are no longer needed

## Security Considerations

MCP servers can pose security risks if not properly configured:

1. **API Keys** - Store API keys securely in environment variables, never in configuration files
2. **Access Control** - Limit the directories and resources that MCP servers can access
3. **Sandboxing** - Run MCP servers in a sandboxed environment when possible
4. **Audit** - Regularly audit MCP server logs for suspicious activity

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.github.io/docs/)
- [MCP GitHub Repository](https://github.com/modelcontextprotocol/mcp)
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
- [Top MCP Servers](https://apidog.com/blog/top-10-mcp-servers/)
