# Platform Apps

This repository contains custom platform infrastructure applications and services for ArchipelagoAI.

## Repository Structure

```
platform-apps/
├── .github/
│   └── workflows/
│       ├── argocd-mcp-server.yml    # Build workflow for ArgoCD MCP
│       └── TEMPLATE.yml              # Template for new app workflows
├── argocd-mcp-server/                # ArgoCD MCP Server
│   ├── argocd_mcp_server/            # Python package
│   ├── Dockerfile                    # Container build
│   ├── pyproject.toml               # Dependencies
│   └── README.md                    # App-specific docs
└── <future-app>/                     # Future platform apps
```

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
**Image:** `ghcr.io/archipelagoai/platform-apps/argocd-mcp-server:latest`

## Adding a New Platform App

1. **Create app directory**: `mkdir <app-name>`
2. **Add app code and Dockerfile**
3. **Copy workflow template**:
   ```bash
   cp .github/workflows/TEMPLATE.yml .github/workflows/<app-name>.yml
   ```
4. **Customize workflow**:
   - Update `APP_NAME` to match your app
   - Update `paths` to trigger on your app directory
   - Update metadata (title, description)
5. **Create Kubernetes manifests** in the `configs` repo:
   - `configs/argocd/mcp/manifests/<app-name>/`
   - `configs/argocd/mcp/apps/<app-name>.yaml`

## Development

Each service is self-contained with its own:
- Dependencies and build configuration
- Documentation
- Dockerfile
- Tests (if applicable)

## CI/CD

- **Automated Builds**: GitHub Actions builds and pushes Docker images to GHCR
- **Triggers**: Builds run on changes to app directories or workflow files
- **Image Tags**:
  - `latest` - Latest main branch build
  - `<branch-name>` - Branch builds
  - `<branch-name>-<sha>` - Commit-specific builds
  - `<version>` - Semantic version tags (when tagged)

## Image Registry

All images are published to GitHub Container Registry (GHCR):
- Registry: `ghcr.io/archipelagoai/platform-apps`
- Format: `ghcr.io/archipelagoai/platform-apps/<app-name>:<tag>`

## License

MIT
