"""ArgoCD API client."""

import os
from typing import Any, Dict, List, Optional
import httpx
from pydantic import BaseModel


class ArgoCDConfig(BaseModel):
    """ArgoCD configuration."""
    
    server: str
    token: str
    insecure: bool = False
    
    @classmethod
    def from_env(cls) -> "ArgoCDConfig":
        """Create config from environment variables."""
        server = os.getenv("ARGOCD_SERVER")
        token = os.getenv("ARGOCD_TOKEN")
        insecure = os.getenv("ARGOCD_INSECURE", "false").lower() == "true"
        
        if not server:
            raise ValueError("ARGOCD_SERVER environment variable is required")
        if not token:
            raise ValueError("ARGOCD_TOKEN environment variable is required")
        
        return cls(server=server, token=token, insecure=insecure)


class ArgoCDClient:
    """ArgoCD API client."""
    
    def __init__(self, config: ArgoCDConfig):
        """Initialize ArgoCD client."""
        self.config = config
        self.base_url = f"https://{config.server}/api/v1"
        self.headers = {
            "Authorization": f"Bearer {config.token}",
            "Content-Type": "application/json",
        }
        self.verify = not config.insecure
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request."""
        url = f"{self.base_url}{path}"
        
        async with httpx.AsyncClient(verify=self.verify) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()
    
    async def list_applications(
        self,
        project: Optional[str] = None,
        selector: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all applications."""
        params = {}
        if project:
            params["project"] = project
        if selector:
            params["selector"] = selector
        
        result = await self._request("GET", "/applications", params=params)
        return result.get("items", [])
    
    async def get_application(self, name: str) -> Dict[str, Any]:
        """Get application details."""
        return await self._request("GET", f"/applications/{name}")
    
    async def sync_application(
        self,
        name: str,
        prune: bool = False,
        dry_run: bool = False,
        revision: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sync an application."""
        payload = {
            "prune": prune,
            "dryRun": dry_run,
        }
        if revision:
            payload["revision"] = revision
        
        return await self._request("POST", f"/applications/{name}/sync", json=payload)
    
    async def get_application_manifests(self, name: str) -> Dict[str, Any]:
        """Get application manifests."""
        return await self._request("GET", f"/applications/{name}/manifests")
    
    async def get_sync_history(self, name: str) -> List[Dict[str, Any]]:
        """Get application sync history."""
        app = await self.get_application(name)
        return app.get("status", {}).get("history", [])
    
    async def rollback_application(
        self,
        name: str,
        revision: str,
    ) -> Dict[str, Any]:
        """Rollback application to a specific revision."""
        payload = {
            "revision": revision,
        }
        return await self._request("POST", f"/applications/{name}/rollback", json=payload)
    
    async def delete_application(
        self,
        name: str,
        cascade: bool = True,
    ) -> Dict[str, Any]:
        """Delete an application."""
        params = {"cascade": str(cascade).lower()}
        return await self._request("DELETE", f"/applications/{name}", params=params)
    
    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        result = await self._request("GET", "/projects")
        return result.get("items", [])
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """Get ArgoCD cluster information."""
        return await self._request("GET", "/clusters")
