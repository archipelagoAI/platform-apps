"""HTTP/SSE transport for ArgoCD MCP Server."""

import asyncio
import json
import logging
import os
from typing import Any, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import uvicorn

from mcp.types import Tool, TextContent

from .client import ArgoCDClient, ArgoCDConfig
from .server import format_application_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="ArgoCD MCP Server", version="0.1.0")

# Global ArgoCD client
argocd_client: Optional[ArgoCDClient] = None


def get_client() -> ArgoCDClient:
    """Get or create ArgoCD client."""
    global argocd_client
    if argocd_client is None:
        config = ArgoCDConfig.from_env()
        argocd_client = ArgoCDClient(config)
    return argocd_client


@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info("Starting ArgoCD MCP Server")
    try:
        get_client()
        logger.info("ArgoCD client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize ArgoCD client: {e}")
        raise


@app.get("/")
async def root():
    """Root endpoint with server info."""
    return {
        "name": "argocd-mcp-server",
        "version": "0.1.0",
        "description": "ArgoCD MCP Server with HTTP/SSE transport",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "argocd-mcp-server", "version": "0.1.0"}


async def list_tools_impl() -> list[dict]:
    """List available tools."""
    tools = [
        {
            "name": "list_applications",
            "description": "List all ArgoCD applications with optional filtering by project or selector",
            "inputSchema": {
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
        },
        {
            "name": "get_application",
            "description": "Get detailed information about a specific ArgoCD application",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Application name",
                    },
                },
                "required": ["name"],
            },
        },
        {
            "name": "sync_application",
            "description": "Trigger synchronization of an ArgoCD application",
            "inputSchema": {
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
        },
        {
            "name": "get_application_manifests",
            "description": "Get the Kubernetes manifests for an application",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Application name",
                    },
                },
                "required": ["name"],
            },
        },
        {
            "name": "get_sync_history",
            "description": "Get synchronization history for an application",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Application name",
                    },
                },
                "required": ["name"],
            },
        },
        {
            "name": "rollback_application",
            "description": "Rollback an application to a previous revision",
            "inputSchema": {
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
        },
        {
            "name": "list_projects",
            "description": "List all ArgoCD projects",
            "inputSchema": {
                "type": "object",
                "properties": {},
            },
        },
    ]
    return tools


async def call_tool_impl(name: str, arguments: dict) -> list[dict]:
    """Handle tool calls."""
    client = get_client()
    
    try:
        if name == "list_applications":
            apps = await client.list_applications(
                project=arguments.get("project"),
                selector=arguments.get("selector"),
            )
            
            if not apps:
                return [{"type": "text", "text": "No applications found"}]
            
            summary = f"Found {len(apps)} application(s):\n\n"
            for app in apps:
                summary += format_application_summary(app)
                summary += "\n"
            
            return [{"type": "text", "text": summary}]
        
        elif name == "get_application":
            app = await client.get_application(arguments["name"])
            return [{"type": "text", "text": json.dumps(app, indent=2)}]
        
        elif name == "sync_application":
            result = await client.sync_application(
                name=arguments["name"],
                prune=arguments.get("prune", False),
                dry_run=arguments.get("dry_run", False),
                revision=arguments.get("revision"),
            )
            return [{"type": "text", "text": f"Sync initiated for {arguments['name']}\n\n" + json.dumps(result, indent=2)}]
        
        elif name == "get_application_manifests":
            manifests = await client.get_application_manifests(arguments["name"])
            return [{"type": "text", "text": json.dumps(manifests, indent=2)}]
        
        elif name == "get_sync_history":
            history = await client.get_sync_history(arguments["name"])
            
            if not history:
                return [{"type": "text", "text": "No sync history found"}]
            
            summary = f"Sync history for {arguments['name']}:\n\n"
            for entry in history:
                revision = entry.get("revision", "unknown")
                deployed_at = entry.get("deployedAt", "unknown")
                summary += f"Revision: {revision}\n"
                summary += f"Deployed At: {deployed_at}\n\n"
            
            return [{"type": "text", "text": summary}]
        
        elif name == "rollback_application":
            result = await client.rollback_application(
                name=arguments["name"],
                revision=arguments["revision"],
            )
            return [{"type": "text", "text": f"Rollback initiated for {arguments['name']} to revision {arguments['revision']}\n\n" + json.dumps(result, indent=2)}]
        
        elif name == "list_projects":
            projects = await client.list_projects()
            
            if not projects:
                return [{"type": "text", "text": "No projects found"}]
            
            summary = f"Found {len(projects)} project(s):\n\n"
            for project in projects:
                name = project.get("metadata", {}).get("name", "unknown")
                summary += f"- {name}\n"
            
            return [{"type": "text", "text": summary}]
        
        else:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {str(e)}")
        return [{"type": "text", "text": f"Error: {str(e)}"}]


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """HTTP endpoint for MCP JSON-RPC messages."""
    body = None
    try:
        body = await request.json()
        method = body.get("method", "unknown")
        logger.info(f"Received MCP request: {method}")
        
        # Handle different MCP methods
        if method == "tools/list":
            tools = await list_tools_impl()
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"tools": tools}
            }
        elif method == "tools/call":
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = await call_tool_impl(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"content": result}
            }
        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "argocd-mcp-server",
                        "version": "0.1.0"
                    }
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": body.get("id"),
                "result": {"status": "ok", "method": method}
            }
    
    except Exception as e:
        logger.error(f"Error processing MCP request: {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": body.get("id") if body else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        }


def run_http_server():
    """Run the HTTP server."""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8080"))
    
    logger.info(f"Starting ArgoCD MCP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_http_server()
