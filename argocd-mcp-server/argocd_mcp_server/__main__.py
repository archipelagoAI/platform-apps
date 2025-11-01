"""ArgoCD MCP Server entry point."""

import os


def main():
    """Main entry point for the ArgoCD MCP server."""
    # Check if we should run in HTTP mode or stdio mode
    mode = os.getenv("MCP_TRANSPORT", "stdio").lower()
    
    if mode == "http":
        from .http_server import run_http_server
        run_http_server()
    else:
        # Run in stdio mode (default)
        import asyncio
        from .server import main as stdio_main
        asyncio.run(stdio_main())


if __name__ == "__main__":
    main()
