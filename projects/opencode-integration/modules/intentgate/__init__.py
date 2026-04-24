"""
IntentGate - 意圖分類引擎

Semantic routing system for OpenClaw + ClawTeam
"""

from .engine import (
    IntentGate,
    IntentClassification,
    RoutingDecision,
    IntentCategory,
    IntentType,
    classify_intent,
    route_intent,
    process_query,
)

__all__ = [
    'IntentGate',
    'IntentClassification',
    'RoutingDecision',
    'IntentCategory',
    'IntentType',
    'classify_intent',
    'route_intent',
    'process_query',
]
