"""ArgoCD MCP Server implementation."""

import asyncio
import json
import sys
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .client import ArgoCDClient, ArgoCDConfig


def format_application_summary(app: dict[str, Any]) -> str:
    """Format application summary."""
    metadata = app.get("metadata", {})
    spec = app.get("spec", {})
    status = app.get("status", {})
    
    name = metadata.get("name", "unknown")
    namespace = metadata.get("namespace", "unknown")
    
    source = spec.get("source", {})
    repo_url = source.get("repoURL", "unknown")
    path = source.get("path", "unknown")
    target_revision = source.get("targetRevision", "unknown")
    
    sync_status = status.get("sync", {}).get("status", "unknown")
    health_status = status.get("health", {}).get("status", "unknown")
    
    return f"""Application: {name}
Namespace: {namespace}
Repository: {repo_url}
Path: {path}
Revision: {target_revision}
Sync Status: {sync_status}
Health Status: {health_status}
"""


def create_server() -> Server:
    """Create and configure the ArgoCD MCP server."""
    server = Server("argocd-mcp-server")
    
    # Initialize ArgoCD client
    try:
        config = ArgoCDConfig.from_env()
        client = ArgoCDClient(config)
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="list_applications",
                description="List all ArgoCD applications with optional filtering by project or selector",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string",
                            "description": "Filter applications by project name",
                        },
                        "selector": {
                            "type": "string",
                            "description": "Filter applications by label selector (e.g., 'app=myapp')",
                        },
                    },
                },
            ),
            Tool(
                name="get_application",
                description="Get detailed information about a specific ArgoCD application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Application name",
                        },
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="sync_application",
                description="Trigger synchronization of an ArgoCD application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Application name",
                        },
                        "prune": {
                            "type": "boolean",
                            "description": "Prune resources that are no longer in git",
                            "default": False,
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Preview sync without applying changes",
                            "default": False,
                        },
                        "revision": {
                            "type": "string",
                            "description": "Specific git revision to sync to",
                        },
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="get_application_manifests",
                description="Get the Kubernetes manifests for an application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Application name",
                        },
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="get_sync_history",
                description="Get synchronization history for an application",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Application name",
                        },
                    },
                    "required": ["name"],
                },
            ),
            Tool(
                name="rollback_application",
                description="Rollback an application to a previous revision",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Application name",
                        },
                        "revision": {
                            "type": "string",
                            "description": "Git revision to rollback to",
                        },
                    },
                    "required": ["name", "revision"],
                },
            ),
            Tool(
                name="list_projects",
                description="List all ArgoCD projects",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "list_applications":
                apps = await client.list_applications(
                    project=arguments.get("project"),
                    selector=arguments.get("selector"),
                )
                
                if not apps:
                    return [TextContent(type="text", text="No applications found")]
                
                summary = f"Found {len(apps)} application(s):\n\n"
                for app in apps:
                    summary += format_application_summary(app)
                    summary += "\n"
                
                return [TextContent(type="text", text=summary)]
            
            elif name == "get_application":
                app = await client.get_application(arguments["name"])
                return [TextContent(
                    type="text",
                    text=json.dumps(app, indent=2)
                )]
            
            elif name == "sync_application":
                result = await client.sync_application(
                    name=arguments["name"],
                    prune=arguments.get("prune", False),
                    dry_run=arguments.get("dry_run", False),
                    revision=arguments.get("revision"),
                )
                return [TextContent(
                    type="text",
                    text=f"Sync initiated for {arguments['name']}\n\n" + json.dumps(result, indent=2)
                )]
            
            elif name == "get_application_manifests":
                manifests = await client.get_application_manifests(arguments["name"])
                return [TextContent(
                    type="text",
                    text=json.dumps(manifests, indent=2)
                )]
            
            elif name == "get_sync_history":
                history = await client.get_sync_history(arguments["name"])
                
                if not history:
                    return [TextContent(type="text", text="No sync history found")]
                
                summary = f"Sync history for {arguments['name']}:\n\n"
                for entry in history:
                    revision = entry.get("revision", "unknown")
                    deployed_at = entry.get("deployedAt", "unknown")
                    summary += f"Revision: {revision}\n"
                    summary += f"Deployed At: {deployed_at}\n\n"
                
                return [TextContent(type="text", text=summary)]
            
            elif name == "rollback_application":
                result = await client.rollback_application(
                    name=arguments["name"],
                    revision=arguments["revision"],
                )
                return [TextContent(
                    type="text",
                    text=f"Rollback initiated for {arguments['name']} to revision {arguments['revision']}\n\n" + json.dumps(result, indent=2)
                )]
            
            elif name == "list_projects":
                projects = await client.list_projects()
                
                if not projects:
                    return [TextContent(type="text", text="No projects found")]
                
                summary = f"Found {len(projects)} project(s):\n\n"
                for project in projects:
                    name = project.get("metadata", {}).get("name", "unknown")
                    summary += f"- {name}\n"
                
                return [TextContent(type="text", text=summary)]
            
            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]
        
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    return server


async def main():
    """Run the server."""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
