"""Elegant Python API for Repox - AI-Powered Code Assistant."""

from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import json

from ..core.assistant import RepoxAssistant
from ..core.config import RepoxConfig
from ..processing.locator import FileLocator
from ..utils.models import ModelFactory
from ..repository.repomix_integration import RepomixIntegration


@dataclass
class SearchResult:
    """Result from file search operations."""
    files: List[str]
    confidence: float
    reasoning: str
    content_matches: Dict[str, List[Dict[str, Any]]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "files": self.files,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "content_matches": self.content_matches
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class ContextResult:
    """Result from context building operations."""
    content: str
    files: List[str]
    metadata: Dict[str, Any]
    
    def save(self, path: Union[str, Path]) -> None:
        """Save context to file."""
        Path(path).write_text(self.content, encoding='utf-8')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "files": self.files,
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class AnswerResult:
    """Result from Q&A operations."""
    question: str
    answer: str
    files_used: List[str]
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "question": self.question,
            "answer": self.answer,
            "files_used": self.files_used,
            "confidence": self.confidence
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class Repox:
    """Main Repox API class - elegant interface for AI-powered code analysis."""
    
    def __init__(
        self, 
        repo_path: Union[str, Path] = None,
        config: Optional[RepoxConfig] = None,
        api_key: Optional[str] = None,
        model: str = "gpt-4"
    ):
        """Initialize Repox with optional configuration.
        
        Args:
            repo_path: Path to repository (default: current directory)
            config: Custom configuration (default: auto-detected)
            api_key: OpenAI API key (default: from environment)
            model: AI model to use (default: gpt-4)
        """
        self.repo_path = Path(repo_path or Path.cwd())
        
        # Setup configuration
        if config is None:
            config = RepoxConfig.load_from_env()
            if api_key:
                config.openai_api_key = api_key
            if model:
                config.strong_model = model
        
        self.config = config
        self._assistant = None
        self._locator = None
        self._repomix = None
    
    @property
    def assistant(self) -> RepoxAssistant:
        """Lazy-loaded assistant instance."""
        if self._assistant is None:
            self._assistant = RepoxAssistant(self.repo_path, self.config)
        return self._assistant
    
    @property
    def locator(self) -> FileLocator:
        """Lazy-loaded file locator instance."""
        if self._locator is None:
            model = ModelFactory.create_openai_model(
                self.config.strong_model,
                self.config.openai_api_key,
                self.config.openai_base_url
            )
            self._locator = FileLocator(self.repo_path, self.config, model)
        return self._locator
    
    @property
    def repomix(self) -> RepomixIntegration:
        """Lazy-loaded repomix integration instance."""
        if self._repomix is None:
            self._repomix = RepomixIntegration(self.repo_path, self.config)
        return self._repomix
    
    def ask(self, question: str, preview: bool = False) -> Union[AnswerResult, SearchResult]:
        """Ask a question about the codebase.
        
        Args:
            question: Natural language question
            preview: If True, return file selection instead of answer
            
        Returns:
            AnswerResult with the answer or SearchResult if preview=True
        """
        if preview:
            selection = self.assistant.select_files(question)
            return SearchResult(
                files=selection.selected_files,
                confidence=0.8,  # Default confidence for file selection
                reasoning=selection.reasoning,
                content_matches={}
            )
        
        # Get file selection first
        selection = self.assistant.select_files(question)
        
        # Generate answer
        answer = self.assistant.ask(question)
        
        return AnswerResult(
            question=question,
            answer=answer,
            files_used=selection.selected_files,
            confidence=0.9  # Default confidence for answers
        )
    
    def find(
        self, 
        query: str, 
        limit: int = 10, 
        search_content: bool = False
    ) -> SearchResult:
        """Find files matching a query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            search_content: Whether to search file content
            
        Returns:
            SearchResult with matching files
        """
        result = self.locator.locate_files(
            query, 
            max_results=limit, 
            search_content=search_content
        )
        
        return SearchResult(
            files=result.located_files,
            confidence=result.confidence,
            reasoning=result.reasoning,
            content_matches=result.content_matches
        )
    
    def build_context(
        self,
        files: Optional[List[str]] = None,
        query: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        compress: bool = False,
        max_size: Optional[int] = None
    ) -> ContextResult:
        """Build context from repository files.
        
        Args:
            files: Specific files to include
            query: Query to auto-select files
            focus_areas: Areas to focus on
            compress: Enable compression
            max_size: Maximum context size
            
        Returns:
            ContextResult with the built context
        """
        if files is None and query is None:
            raise ValueError("Must specify either files or query")
        
        if files is None:
            # Auto-select files based on query
            search_result = self.find(query)
            files = search_result.files
        
        # Build context using repomix
        context_result = self.repomix.build_context(
            selected_files=files,
            focus_areas=focus_areas,
            compression_enabled=compress,
            max_size=max_size or self.config.max_context_size
        )
        
        return ContextResult(
            content=context_result["content"],
            files=files,
            metadata=context_result["metadata"]
        )
    
    def info(self) -> Dict[str, Any]:
        """Get repository information.
        
        Returns:
            Dictionary with repository statistics
        """
        return self.assistant.repository_analyzer.get_repository_summary()
    
    def list_files(self) -> List[str]:
        """List all processable files in the repository.
        
        Returns:
            List of file paths
        """
        return self.assistant.repository_analyzer.get_processable_files()
    
    def configure(self, **kwargs) -> 'Repox':
        """Update configuration and return self for chaining.
        
        Args:
            **kwargs: Configuration parameters to update
            
        Returns:
            Self for method chaining
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Reset cached instances to pick up new config
        self._assistant = None
        self._locator = None
        self._repomix = None
        
        return self
    
    def save_config(self, path: Optional[Union[str, Path]] = None) -> None:
        """Save current configuration to file.
        
        Args:
            path: Configuration file path (default: .repox.json)
        """
        if path is None:
            path = self.repo_path / ".repox.json"
        self.config.save_to_file(Path(path))


# Convenience functions for quick usage
def ask(question: str, repo_path: Union[str, Path] = None, **kwargs) -> AnswerResult:
    """Quick function to ask a question about a repository.
    
    Args:
        question: Question to ask
        repo_path: Repository path (default: current directory)
        **kwargs: Additional configuration options
        
    Returns:
        AnswerResult with the answer
    """
    repox = Repox(repo_path, **kwargs)
    return repox.ask(question)


def find(query: str, repo_path: Union[str, Path] = None, **kwargs) -> SearchResult:
    """Quick function to find files in a repository.
    
    Args:
        query: Search query
        repo_path: Repository path (default: current directory)
        **kwargs: Additional configuration options
        
    Returns:
        SearchResult with matching files
    """
    repox = Repox(repo_path, **kwargs)
    return repox.find(query, **kwargs)


def build_context(
    files: Optional[List[str]] = None,
    query: Optional[str] = None,
    repo_path: Union[str, Path] = None,
    **kwargs
) -> ContextResult:
    """Quick function to build context from repository files.
    
    Args:
        files: Specific files to include
        query: Query to auto-select files
        repo_path: Repository path (default: current directory)
        **kwargs: Additional configuration options
        
    Returns:
        ContextResult with the built context
    """
    repox = Repox(repo_path, **kwargs)
    return repox.build_context(files=files, query=query, **kwargs)


# Example usage patterns
if __name__ == "__main__":
    # Basic usage
    repox = Repox()
    
    # Ask a question
    result = repox.ask("How does authentication work?")
    print(result.answer)
    
    # Find files
    search = repox.find("database models")
    print(f"Found {len(search.files)} files")
    
    # Build context
    context = repox.build_context(query="API endpoints")
    context.save("api_context.md")
    
    # Method chaining
    result = (Repox()
              .configure(verbose=True, max_context_size=100000)
              .ask("What are the main components?"))
    
    # Quick functions
    answer = ask("How does caching work?")
    files = find("test files")
    context = build_context(query="authentication system")