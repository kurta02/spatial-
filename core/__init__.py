"""
Spatial Constellation Core Components

This package contains the core functionality of the Spatial Constellation System:
- Brain: Multi-LLM orchestrator and coordination
- Persistent Memory: PostgreSQL-based memory management with vector search
- Conversational CLI: Natural language interface for AI interactions
"""

from .brain import Brain
from .persistent_memory import store_memory, retrieve_memory, get_memory_stats
from .conversational_cli import ConversationalCLI

__version__ = "0.5.0"
__all__ = ["Brain", "store_memory", "retrieve_memory", "get_memory_stats", "ConversationalCLI"]