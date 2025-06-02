"""Repox - AI-Powered Code Assistant."""

__version__ = "0.2.0"

# Elegant torch-like API (primary interface)
from .api.elegant import (
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
from .api.classic import Repox, SearchResult, ContextResult, AnswerResult
from .api.classic import ask as api_ask, find as api_find, build_context as api_build_context

# Core components (for advanced usage)
from .core.assistant import RepoxAssistant
from .core.config import RepoxConfig
from .processing.filter import SmartFilter
from .processing.locator import FileLocator
from .core.models import AIModel, OpenAIModel, ModelFactory
from .repository.repomix_integration import RepomixIntegration

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