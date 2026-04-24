"""Node-RED Automation Skill for OpenClaw"""

from .client import NodeREDClient
from .flow_manager import FlowManager
from .event_monitor import EventMonitor

__version__ = "1.0.0"
__all__ = ["NodeREDClient", "FlowManager", "EventMonitor"]

def get_client(host: str = "localhost", port: int = 1880, username: str = None, password: str = None) -> NodeREDClient:
    """Get Node-RED client instance"""
    return NodeREDClient(host=host, port=port, username=username, password=password)

def get_flow_manager(host: str = "localhost", port: int = 1880) -> FlowManager:
    """Get Flow Manager instance"""
    return FlowManager(host=host, port=port)

def get_event_monitor(host: str = "localhost", port: int = 1880) -> EventMonitor:
    """Get Event Monitor instance"""
    return EventMonitor(host=host, port=port)