"""Node-RED HTTP API Client

Wrapper for Node-RED Admin API:
https://nodered.org/docs/api/admin/
"""

import json
from typing import Any, Optional
import requests
from requests.auth import HTTPBasicAuth


class NodeREDClient:
    """Node-RED Admin API Client"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1880,
        username: Optional[str] = None,
        password: Optional[str] = None,
        base_path: str = "",
        timeout: int = 30
    ):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.base_path = base_path
        self.timeout = timeout
        
        self.session = requests.Session()
        if username and password:
            self.session.auth = HTTPBasicAuth(username, password)
        
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None
    ) -> dict:
        """Make HTTP request to Node-RED API"""
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else {}
        except requests.exceptions.ConnectionError:
            raise ConnectionError(f"Cannot connect to Node-RED at {self.base_url}. Is Node-RED running?")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Node-RED API error: {e}")

    # ==================== Flow Management ====================

    def get_flows(self) -> list:
        """Get all flows"""
        return self._request("GET", "flows")

    def set_flows(self, flows: list) -> dict:
        """Set all flows (deploy)"""
        return self._request("PUT", "flows", data=flows)

    def get_flow(self, id: str) -> dict:
        """Get a specific flow"""
        return self._request("GET", f"flow/{id}")

    def set_flow(self, id: str, flow: dict) -> dict:
        """Set a specific flow"""
        return self._request("PUT", f"flow/{id}", data=flow)

    def add_flow(self, flow: dict) -> dict:
        """Add a new flow"""
        return self._request("POST", "flows", data=flow)

    def delete_flow(self, id: str) -> dict:
        """Delete a flow"""
        return self._request("DELETE", f"flow/{id}")

    # ==================== Node Management ====================

    def get_nodes(self) -> list:
        """Get all installed nodes"""
        return self._request("GET", "nodes")

    def get_node_config(self, module: str) -> dict:
        """Get node configuration"""
        return self._request("GET", f"nodes/{module}")

    def get_settings(self) -> dict:
        """Get runtime settings"""
        return self._request("GET", "settings")

    # ==================== Library ====================

    def get_library_entries(self, type: str = "flows") -> list:
        """Get library entries"""
        return self._request("GET", f"library/{type}")

    def add_library_entry(self, type: str, name: str, data: dict) -> dict:
        """Add library entry"""
        return self._request("POST", f"library/{type}", data={
            "name": name,
            "data": data
        })

    # ==================== Info ====================

    def get_info(self) -> dict:
        """Get Node-RED info (returns settings as fallback)"""
        try:
            return self._request("GET", "info")
        except:
            # Fallback to settings if /info is not available
            settings = self.get_settings()
            return {
                "version": settings.get("version", "unknown"),
                "node-red": settings.get("version", "unknown")
            }

    def get_status(self) -> dict:
        """Get Node-RED status (returns flows as fallback)"""
        try:
            return self._request("GET", "status")
        except:
            # Fallback to flows count
            flows = self.get_flows()
            return {"flows": len(flows), "status": "running"}

    # ==================== Auth ====================

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate user"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/token",
                json={"username": username, "password": password, "client": "node-red"},
                timeout=self.timeout
            )
            return response.status_code == 200
        except:
            return False

    def get_me(self) -> dict:
        """Get current user info"""
        return self._request("GET", "auth/me")

    # ==================== Utilities ====================

    def is_running(self) -> bool:
        """Check if Node-RED is running"""
        try:
            self.get_settings()
            return True
        except:
            return False

    def export_flows_json(self) -> str:
        """Export all flows as JSON string"""
        flows = self.get_flows()
        return json.dumps(flows, indent=2, ensure_ascii=False)

    def import_flows_json(self, json_str: str) -> dict:
        """Import flows from JSON string"""
        flows = json.loads(json_str)
        return self.set_flows(flows)

    # ==================== Debug ====================

    def get_debug_recent(self, node_id: Optional[str] = None) -> list:
        """Get recent debug messages"""
        params = {}
        if node_id:
            params["node"] = node_id
        return self._request("GET", "debug", params=params)

    # ==================== HTTP Admin ====================

    def get_admin_settings(self) -> dict:
        """Get HTTP Admin settings"""
        return self._request("GET", "settings/section/httpAdmin")

    def set_admin_settings(self, settings: dict) -> dict:
        """Set HTTP Admin settings"""
        return self._request("PUT", "settings/section/httpAdmin", data=settings)