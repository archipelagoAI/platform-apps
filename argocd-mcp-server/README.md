# ArgoCD MCP Server

A Model Context Protocol (MCP) server for ArgoCD that enables AI assistants to interact with ArgoCD applications and resources.

## Features

- **List Applications**: View all ArgoCD applications with their status
- **Get Application Details**: Retrieve detailed information about specific applications
- **Sync Applications**: Trigger application synchronization
- **Application Health**: Check application health status
- **Sync History**: View synchronization history
- **Application Parameters**: Manage application parameters
- **Rollback**: Execute application rollbacks

## Installation

```bash
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
ARGOCD_SERVER=<argocd-server-url>
ARGOCD_TOKEN=<argocd-auth-token>
# Optional: Skip TLS verification (not recommended for production)
ARGOCD_INSECURE=false
```

## Usage

### With Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "argocd": {
      "command": "python",
      "args": ["-m", "argocd_mcp_server"],
      "env": {
        "ARGOCD_SERVER": "argocd.example.com",
        "ARGOCD_TOKEN": "your-token-here"
      }
    }
  }
}
```

### Standalone

```bash
python -m argocd_mcp_server
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .
ruff check --fix .
```

## License

MIT
