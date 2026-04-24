"""
OpenClaw Oh-My-Opencode Integration Modules
"""

__version__ = "1.0.0"
__author__ = "ClawTeam"

from .intentgate.engine import IntentGate, IntentClassification, RoutingDecision
from .hash_anchored_edit.editor import HashAnchoredEditor, LineAnchor, EditOperation
from .todo_enforcer.enforcer import TodoEnforcer, Task, TaskStatus
from .plan_driven.manager import PlanManager, Plan, PlanStatus

__all__ = [
    'IntentGate',
    'IntentClassification',
    'RoutingDecision',
    'HashAnchoredEditor',
    'LineAnchor',
    'EditOperation',
    'TodoEnforcer',
    'Task',
    'TaskStatus',
    'PlanManager',
    'Plan',
    'PlanStatus',
]
