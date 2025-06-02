"""Repox - AI-Powered Code Assistant."""

__version__ = "0.2.0"

# Main API classes (elegant interface)
from .api import Repox, SearchResult, ContextResult, AnswerResult
from .api import ask, find, build_context

# Core components (for advanced usage)
from .assistant import RepoxAssistant
from .config import RepoxConfig
from .filter import SmartFilter
from .locator import FileLocator
from .models import AIModel, OpenAIModel, ModelFactory
from .repomix_integration import RepomixIntegration

# Expose the elegant API as the primary interface
__all__ = [
    # Primary API (recommended)
    "Repox",
    "SearchResult", 
    "ContextResult", 
    "AnswerResult",
    "ask",
    "find", 
    "build_context",
    
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