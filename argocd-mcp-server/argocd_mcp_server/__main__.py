"""Main entry point for ArgoCD MCP server."""

import asyncio
from argocd_mcp_server.server import main

if __name__ == "__main__":
    asyncio.run(main())
