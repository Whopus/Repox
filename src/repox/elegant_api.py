"""Elegant torch-like API for Repox."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from .api import SearchResult, ContextResult, AnswerResult
from .config import RepoxConfig
from .assistant import RepoxAssistant
from .models import ModelFactory


# Global configuration state
_global_config: Optional[RepoxConfig] = None
_global_assistant: Optional[RepoxAssistant] = None


def configure(
    repo_path: Optional[Union[str, Path]] = None,
    model: Optional[str] = None,
    strong_model: Optional[str] = None,
    weak_model: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    max_context_size: Optional[int] = None,
    max_file_size: Optional[int] = None,
    verbose: bool = False,
    **kwargs
) -> None:
    """Configure global Repox settings.
    
    Args:
        repo_path: Repository path (defaults to current directory)
        model: Model name for both strong and weak models
        strong_model: Strong model name (overrides model)
        weak_model: Weak model name (overrides model)
        api_key: OpenAI API key
        base_url: OpenAI base URL
        max_context_size: Maximum context size
        max_file_size: Maximum file size to process
        verbose: Enable verbose output
        **kwargs: Additional configuration options
    
    Example:
        >>> import repox
        >>> repox.configure(model="gpt-4", verbose=True)
        >>> answer = repox.ask("How does authentication work?")
    """
    global _global_config, _global_assistant
    
    # Determine repository path
    if repo_path is None:
        repo_path = Path.cwd()
    else:
        repo_path = Path(repo_path)
    
    # Create configuration
    config_dict = {
        'verbose': verbose,
        **kwargs
    }
    
    # Handle model configuration
    if model:
        config_dict['strong_model'] = model
        config_dict['weak_model'] = model
    
    if strong_model:
        config_dict['strong_model'] = strong_model
    
    if weak_model:
        config_dict['weak_model'] = weak_model
    
    # Handle API configuration
    if api_key:
        config_dict['openai_api_key'] = api_key
    
    if base_url:
        config_dict['openai_base_url'] = base_url
    
    # Handle size limits
    if max_context_size:
        config_dict['max_context_size'] = max_context_size
    
    if max_file_size:
        config_dict['max_file_size'] = max_file_size
    
    # Create or update global configuration
    if _global_config is None:
        _global_config = RepoxConfig(**config_dict)
    else:
        _global_config.update(**config_dict)
    
    # Reset assistant to use new configuration
    _global_assistant = None


def _get_assistant() -> RepoxAssistant:
    """Get or create the global assistant instance."""
    global _global_config, _global_assistant
    
    if _global_assistant is None:
        # Create default configuration if none exists
        if _global_config is None:
            _global_config = RepoxConfig()
        
        # Determine repository path
        repo_path = Path.cwd()
        
        # Create assistant
        _global_assistant = RepoxAssistant(
            repo_path=repo_path,
            config=_global_config
        )
    
    return _global_assistant


def ask(question: str, **kwargs) -> str:
    """Ask a question about the codebase.
    
    Args:
        question: The question to ask
        **kwargs: Additional configuration options
    
    Returns:
        The answer as a string
    
    Example:
        >>> import repox
        >>> answer = repox.ask("How does authentication work?")
        >>> print(answer)
    """
    global _global_config
    
    # Apply temporary configuration if provided
    if kwargs:
        original_config = _global_config
        configure(**kwargs)
        try:
            assistant = _get_assistant()
            return assistant.ask(question)
        finally:
            # Restore original configuration
            _global_config = original_config
    else:
        assistant = _get_assistant()
        return assistant.ask(question)


def find(query: str, max_results: int = 10, search_content: bool = False, **kwargs) -> List[str]:
    """Find files relevant to a query.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        search_content: Whether to search file content
        **kwargs: Additional configuration options
    
    Returns:
        List of relevant file paths
    
    Example:
        >>> import repox
        >>> files = repox.find("database models")
        >>> print(files)
    """
    global _global_config
    
    # Apply temporary configuration if provided
    if kwargs:
        original_config = _global_config
        configure(**kwargs)
        try:
            assistant = _get_assistant()
            result = assistant.find(query, max_results=max_results, search_content=search_content)
            return result.files
        finally:
            # Restore original configuration
            _global_config = original_config
    else:
        assistant = _get_assistant()
        result = assistant.find(query, max_results=max_results, search_content=search_content)
        return result.files


def build(
    files: Optional[List[str]] = None,
    query: Optional[str] = None,
    **kwargs
) -> str:
    """Build context from files or query.
    
    Args:
        files: List of files to include
        query: Query to find relevant files
        **kwargs: Additional configuration options
    
    Returns:
        Built context as a string
    
    Example:
        >>> import repox
        >>> context = repox.build(query="API endpoints")
        >>> print(context)
    """
    global _global_config
    
    # Apply temporary configuration if provided
    if kwargs:
        original_config = _global_config
        configure(**kwargs)
        try:
            assistant = _get_assistant()
            result = assistant.build_context(files=files, query=query)
            return result.context
        finally:
            # Restore original configuration
            _global_config = original_config
    else:
        assistant = _get_assistant()
        result = assistant.build_context(files=files, query=query)
        return result.context


def info(**kwargs) -> Dict:
    """Get repository information.
    
    Args:
        **kwargs: Additional configuration options
    
    Returns:
        Dictionary with repository information
    
    Example:
        >>> import repox
        >>> info = repox.info()
        >>> print(f"Files: {info['file_count']}")
    """
    global _global_config
    
    # Apply temporary configuration if provided
    if kwargs:
        original_config = _global_config
        configure(**kwargs)
        try:
            assistant = _get_assistant()
            return assistant.get_repository_info()
        finally:
            # Restore original configuration
            _global_config = original_config
    else:
        assistant = _get_assistant()
        return assistant.get_repository_info()


def reset() -> None:
    """Reset global configuration and assistant.
    
    Example:
        >>> import repox
        >>> repox.configure(verbose=True)
        >>> repox.reset()  # Back to defaults
    """
    global _global_config, _global_assistant
    _global_config = None
    _global_assistant = None


# Convenience aliases
locate = find  # Alias for find
context = build  # Alias for build


# Auto-configuration from environment
def _auto_configure():
    """Automatically configure from environment variables."""
    env_config = {}
    
    # Check for environment variables
    if os.getenv('OPENAI_API_KEY'):
        env_config['api_key'] = os.getenv('OPENAI_API_KEY')
    
    if os.getenv('OPENAI_BASE_URL'):
        env_config['base_url'] = os.getenv('OPENAI_BASE_URL')
    
    if os.getenv('REPOX_STRONG_MODEL'):
        env_config['strong_model'] = os.getenv('REPOX_STRONG_MODEL')
    
    if os.getenv('REPOX_WEAK_MODEL'):
        env_config['weak_model'] = os.getenv('REPOX_WEAK_MODEL')
    
    if os.getenv('REPOX_VERBOSE'):
        env_config['verbose'] = os.getenv('REPOX_VERBOSE').lower() in ('true', '1', 'yes')
    
    # Apply configuration if any environment variables found
    if env_config:
        configure(**env_config)


# Auto-configure on import
_auto_configure()