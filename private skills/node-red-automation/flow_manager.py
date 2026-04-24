"""Node-RED Flow Manager

Manages flow import/export/deploy with version control.
"""

import json
import os
from typing import Any, Optional
from pathlib import Path
from datetime import datetime

from .client import NodeREDClient


class FlowManager:
    """Node-RED Flow Manager"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1880,
        username: Optional[str] = None,
        password: Optional[str] = None,
        storage_dir: str = "./flows_storage"
    ):
        self.client = NodeREDClient(host, port, username, password)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    # ==================== Import/Export ====================

    def export_all(self) -> list:
        """Export all flows from Node-RED"""
        return self.client.get_flows()

    def export_to_file(self, filename: str = "flows.json") -> Path:
        """Export flows to file"""
        flows = self.export_all()
        path = self.storage_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(flows, f, indent=2, ensure_ascii=False)
        return path

    def import_from_file(self, filename: str) -> dict:
        """Import flows from file"""
        path = self.storage_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Flow file not found: {path}")
        
        with open(path, encoding="utf-8") as f:
            flows = json.load(f)
        return self.client.set_flows(flows)

    def import_from_json(self, json_str: str) -> dict:
        """Import flows from JSON string"""
        flows = json.loads(json_str)
        return self.client.set_flows(flows)

    def import_from_clipboard(self, json_str: str) -> dict:
        """Import flows from Node-RED clipboard (JSON array)"""
        return self.import_from_json(json_str)

    # ==================== Version Control ====================

    def backup(self, tag: Optional[str] = None) -> Path:
        """Create a backup with optional tag"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_str = f"_{tag}" if tag else ""
        filename = f"backup_{timestamp}{tag_str}.json"
        return self.export_to_file(filename)

    def list_backups(self) -> list:
        """List all backups"""
        backups = []
        for f in self.storage_dir.glob("backup_*.json"):
            backups.append({
                "name": f.name,
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "size": f.stat().st_size
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def restore(self, filename: str) -> dict:
        """Restore from backup"""
        return self.import_from_file(filename)

    def get_latest_backup(self) -> Optional[Path]:
        """Get latest backup file"""
        backups = list(self.storage_dir.glob("backup_*.json"))
        if not backups:
            return None
        return max(backups, key=lambda f: f.stat().st_mtime)

    # ==================== Deploy ====================

    def deploy(self, flows: list) -> dict:
        """Deploy flows"""
        return self.client.set_flows(flows)

    def deploy_file(self, filename: str) -> dict:
        """Deploy flows from file"""
        return self.import_from_file(filename)

    def deploy_json(self, json_str: str) -> dict:
        """Deploy flows from JSON string"""
        return self.import_from_json(json_str)

    # ==================== Flow Operations ====================

    def get_flow_by_id(self, flow_id: str) -> Optional[dict]:
        """Get flow by ID"""
        flows = self.export_all()
        for flow in flows:
            if flow.get("id") == flow_id:
                return flow
        return None

    def get_flow_by_name(self, name: str) -> Optional[dict]:
        """Get flow by name"""
        flows = self.export_all()
        for flow in flows:
            if flow.get("name") == name:
                return flow
        return None

    def delete_flow_by_id(self, flow_id: str) -> dict:
        """Delete flow by ID"""
        flows = self.export_all()
        flows = [f for f in flows if f.get("id") != flow_id]
        return self.client.set_flows(flows)

    # ==================== Node Analysis ====================

    def get_node_types(self) -> dict:
        """Get all node types used in flows"""
        flows = self.export_all()
        node_types = {}
        
        for node in flows:
            node_type = node.get("type")
            if node_type:
                node_types[node_type] = node_types.get(node_type, 0) + 1
        
        return node_types

    def find_nodes_by_type(self, node_type: str) -> list:
        """Find all nodes of a specific type"""
        flows = self.export_all()
        nodes = []
        
        for node in flows:
            if node.get("type") == node_type:
                nodes.append(node)
        
        return nodes

    # ==================== Validation ====================

    def validate_flows(self, flows: Optional[list] = None) -> dict:
        """Validate flows structure"""
        if flows is None:
            flows = self.export_all()
        
        errors = []
        warnings = []
        
        if not isinstance(flows, list):
            errors.append("Flows must be an array")
            return {"valid": False, "errors": errors, "warnings": warnings}
        
        node_ids = set()
        
        for i, node in enumerate(flows):
            if "id" not in node:
                errors.append(f"Node {i} missing ID")
            else:
                node_id = node["id"]
                if node_id in node_ids:
                    errors.append(f"Duplicate node ID: {node_id}")
                node_ids.add(node_id)
            
            if "type" not in node:
                errors.append(f"Node {i} missing type")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "node_count": len(flows)
        }

    # ==================== JSON <-> CSV Conversion ====================

    def flows_to_csv(self) -> str:
        """Export flows as CSV (node ID, type, name)"""
        flows = self.export_all()
        lines = ["id,type,name"]
        
        for node in flows:
            node_id = node.get("id", "")
            node_type = node.get("type", "")
            name = node.get("name", "").replace(",", ";")
            lines.append(f"{node_id},{node_type},{name}")
        
        return "\n".join(lines)

    # ==================== Diff ====================

    def diff(self, flows1: list, flows2: list) -> dict:
        """Compare two flow configurations"""
        ids1 = {n.get("id"): n for n in flows1 if n.get("id")}
        ids2 = {n.get("id"): n for n in flows2 if n.get("id")}
        
        added = set(ids2.keys()) - set(ids1.keys())
        removed = set(ids1.keys()) - set(ids2.keys())
        common = set(ids1.keys()) & set(ids2.keys())
        
        modified = []
        for node_id in common:
            if ids1[node_id] != ids2[node_id]:
                modified.append(node_id)
        
        return {
            "added": list(added),
            "removed": list(removed),
            "modified": modified,
            "unchanged": len(common) - len(modified)
        }