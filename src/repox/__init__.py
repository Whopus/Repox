"""Repox - AI-Powered Code Assistant."""

__version__ = "0.2.0"

# Elegant torch-like API (primary interface)
from .elegant_api import (
    ask,
    find,
    build,
    info,
    locate,
    context,
    configure,
    reset,
)

# Full API classes (for advanced usage)
from .api import Repox, SearchResult, ContextResult, AnswerResult
from .api import ask as api_ask, find as api_find, build_context as api_build_context

# Core components (for advanced usage)
from .assistant import RepoxAssistant
from .config import RepoxConfig
from .filter import SmartFilter
from .locator import FileLocator
from .models import AIModel, OpenAIModel, ModelFactory
from .repomix_integration import RepomixIntegration

# Expose the elegant API as the primary interface
__all__ = [
    # Elegant API (primary - torch-like)
    "ask",
    "find", 
    "build",
    "info",
    "locate",
    "context",
    "configure",
    "reset",
    
    # Full API classes
    "Repox",
    "SearchResult", 
    "ContextResult", 
    "AnswerResult",
    "api_ask",
    "api_find", 
    "api_build_context",
    
    # Core components (advanced usage)
    "RepoxAssistant",
    "RepoxConfig", 
    "SmartFilter",
    "FileLocator",
    "AIModel",
    "OpenAIModel",
    "ModelFactory",
    "RepomixIntegration",
]