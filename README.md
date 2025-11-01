# Platform Apps

This repository contains custom platform infrastructure applications and services for ArchipelagoAI.

## Services

### ArgoCD MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with ArgoCD.

**Features:**
- List and inspect ArgoCD applications
- Trigger application synchronization
- View sync history and rollback applications
- Manage application parameters
- Query project and cluster information

**Documentation:** [argocd-mcp-server/README.md](argocd-mcp-server/README.md)

## Development

Each service is contained in its own directory with its own README, Dockerfile, and dependencies.

## CI/CD

All services are automatically built and published to GitHub Container Registry (GHCR) when changes are pushed to the main branch.

## License

MIT
