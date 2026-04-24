"""Node-RED Event Monitor

Monitors Node-RED events and handles webhooks.
"""

import json
import threading
import queue
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime
from pathlib import Path

from .client import NodeREDClient


class EventMonitor:
    """Node-RED Event Monitor"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 1880,
        username: Optional[str] = None,
        password: Optional[str] = None,
        storage_dir: str = "./events_storage"
    ):
        self.client = NodeREDClient(host, port, username, password)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._event_queue = queue.Queue()
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

    # ==================== Event Handlers ====================

    def on(self, event_type: str, handler: Callable) -> None:
        """Register event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable) -> None:
        """Unregister event handler"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def emit(self, event_type: str, data: Any) -> None:
        """Emit event to handlers"""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    print(f"Event handler error: {e}")

    # ==================== Monitor ====================

    def start_monitoring(self) -> None:
        """Start monitoring events"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop monitoring events"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        last_messages = []
        
        while self._running:
            try:
                messages = self.client.get_debug_recent()
                
                for msg in messages:
                    if msg not in last_messages:
                        self._process_message(msg)
                
                last_messages = messages[-100:]  # Keep last 100
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            import time
            time.sleep(2)

    def _process_message(self, msg: dict) -> None:
        """Process a debug message"""
        msg_type = msg.get("type", "unknown")
        
        self.emit(msg_type, msg)
        self._event_queue.put(msg)
        
        self._save_event(msg)

    # ==================== Event Queue ====================

    def get_event(self, timeout: Optional[float] = None) -> Optional[dict]:
        """Get event from queue"""
        try:
            return self._event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_events(self, count: int = 10, timeout: Optional[float] = 1.0) -> list:
        """Get multiple events"""
        events = []
        for _ in range(count):
            event = self.get_event(timeout=timeout)
            if event is None:
                break
            events.append(event)
        return events

    # ==================== Storage ====================

    def _save_event(self, event: dict) -> Path:
        """Save event to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"event_{timestamp}.json"
        path = self.storage_dir / filename
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(event, f, indent=2, ensure_ascii=False)
        
        return path

    def list_events(self, limit: int = 50) -> list:
        """List recent events"""
        events = []
        for f in sorted(self.storage_dir.glob("event_*.json"), reverse=True)[:limit]:
            with open(f, encoding="utf-8") as fp:
                events.append(json.load(fp))
        return events

    # ==================== Webhook Handler ====================

    def create_webhook_handler(
        self,
        path: str,
        callback: Callable[[dict], dict],
        method: str = "POST"
    ) -> Callable:
        """Create a webhook handler"""
        def handler(request_data: dict) -> dict:
            result = callback(request_data)
            return {
                "status": "success",
                "result": result
            }
        
        handler._webhook_path = path
        handler._webhook_method = method
        return handler

    # ==================== Node-RED Events ====================

    def get_runtime_status(self) -> dict:
        """Get runtime status"""
        return self.client.get_status()

    def get_flow_status(self) -> dict:
        """Get flow status"""
        return {
            "running": self.client.is_running(),
            "info": self.client.get_info()
        }

    # ==================== Alert Rules ====================

    def add_alert_rule(
        self,
        name: str,
        condition: Callable[[dict], bool],
        action: Callable[[dict], None]
    ) -> None:
        """Add alert rule"""
        def rule_handler(event: dict):
            if condition(event):
                action(event)
        
        self.on(name, rule_handler)

    # ==================== Utilities ====================

    def filter_events(
        self,
        events: List[dict],
        node_id: Optional[str] = None,
        msg_type: Optional[str] = None
    ) -> List[dict]:
        """Filter events"""
        filtered = events
        
        if node_id:
            filtered = [e for e in filtered if e.get("id") == node_id]
        
        if msg_type:
            filtered = [e for e in filtered if e.get("type") == msg_type]
        
        return filtered

    def get_event_summary(self) -> dict:
        """Get event summary"""
        events = self.list_events(limit=100)
        
        types = {}
        nodes = {}
        
        for event in events:
            msg_type = event.get("type", "unknown")
            types[msg_type] = types.get(msg_type, 0) + 1
            
            node_id = event.get("id")
            if node_id:
                nodes[node_id] = nodes.get(node_id, 0) + 1
        
        return {
            "total_events": len(events),
            "types": types,
            "nodes": nodes,
            "latest": events[0] if events else None
        }


class WebhookServer:
    """Simple webhook server for Node-RED callbacks"""

    def __init__(self, port: int = 1881):
        self.port = port
        self.routes: Dict[str, Callable] = {}

    def route(self, path: str, method: str = "POST"):
        """Register webhook route"""
        def decorator(func: Callable):
            self.routes[f"{method}:{path}"] = func
            return func
        return decorator

    def handle(self, method: str, path: str, data: dict) -> Optional[dict]:
        """Handle webhook request"""
        key = f"{method}:{path}"
        handler = self.routes.get(key)
        
        if handler:
            return handler(data)
        return None

    def list_routes(self) -> List[str]:
        """List all routes"""
        return list(self.routes.keys())