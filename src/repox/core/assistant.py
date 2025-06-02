"""Main Repox assistant implementation."""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import RepoxConfig
from ..processing.context import ContextBuilder
from ..utils.models import AIMessage, AIModel, AnswerGenerationResponse, ModelFactory
from ..repository.analyzer import RepositoryAnalyzer


class RepoxAssistant:
    """AI-powered code context management assistant."""
    
    def __init__(
        self,
        repo_path: str = ".",
        config: Optional[RepoxConfig] = None,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.config = config or RepoxConfig().get_effective_config()
        self.console = Console()
        
        # Validate configuration
        self._validate_config()
        
        # Initialize AI models
        self.strong_model = self._create_model(self.config.strong_model)
        self.weak_model = self._create_model(self.config.weak_model)
        
        # Initialize components
        self.repository_analyzer = RepositoryAnalyzer(self.repo_path, self.config)
        self.context_builder = ContextBuilder(
            self.repo_path,
            self.config,
            self.strong_model,
            self.weak_model,
        )
    
    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not self.config.openai_api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide it in the configuration."
            )
        
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")
        
        if not self.repo_path.is_dir():
            raise ValueError(f"Repository path is not a directory: {self.repo_path}")
    
    def _create_model(self, model_name: str) -> AIModel:
        """Create an AI model instance."""
        return ModelFactory.create_openai_model(
            model_name=model_name,
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
        )
    
    def ask(self, question: str) -> str:
        """Ask a question about the repository and get an AI-generated answer."""
        
        if self.config.verbose:
            self.console.print(Panel(
                f"[bold blue]Question:[/bold blue] {question}",
                title="🤖 Repox Assistant",
                border_style="blue"
            ))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            
            # Step 1: Analyze repository structure
            task1 = progress.add_task("Analyzing repository structure...", total=None)
            
            repository_structure = self.repository_analyzer.get_repository_structure()
            file_sizes = self.repository_analyzer.get_file_sizes()
            
            if self.config.verbose:
                repo_summary = self.repository_analyzer.get_repository_summary()
                self.console.print(f"📊 Found {repo_summary['total_files']} processable files")
            
            progress.update(task1, completed=True)
            
            # Step 2: Build optimized context using hierarchical filtering
            task2 = progress.add_task("Building optimized context...", total=None)
            
            # Use hierarchical filtering for efficient context building
            optimized_context = self.context_builder.build_context_with_hierarchical_filtering(
                question=question,
                repository_structure=repository_structure,
                file_sizes=file_sizes,
            )
            
            progress.update(task2, completed=True)
            
            # Step 3: Generate answer using strong AI
            task3 = progress.add_task("Generating answer...", total=None)
            
            answer = self._generate_answer(question, optimized_context)
            
            progress.update(task3, completed=True)
        
        if self.config.verbose:
            self.console.print(Panel(
                answer,
                title="💡 Answer",
                border_style="green"
            ))
        
        return answer
    
    def _generate_answer(self, question: str, context: str) -> str:
        """Generate the final answer using the strong AI model."""
        
        system_prompt = """You are an expert software engineer and code analyst. You have been provided with relevant code context from a repository to answer a specific question.

Your task is to:
1. Analyze the provided code context carefully
2. Answer the user's question based on the code and your understanding
3. Provide specific examples from the code when relevant
4. Be clear and concise in your explanation
5. If the context doesn't contain enough information to fully answer the question, say so

Guidelines:
- Reference specific files, functions, or code snippets when relevant
- Explain complex concepts in simple terms
- Provide actionable insights when possible
- If you notice potential issues or improvements, mention them
- Be honest about limitations of your analysis"""

        user_prompt = f"""Question: {question}

Code Context:
{context}

Please analyze the code context and provide a comprehensive answer to the question."""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]
        
        response = self.strong_model.generate_sync(
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )
        
        return response.content
    
    def get_repository_summary(self) -> dict:
        """Get a summary of the repository."""
        return self.repository_analyzer.get_repository_summary()
    
    def get_repository_info(self) -> dict:
        """Get repository information (alias for get_repository_summary)."""
        return self.get_repository_summary()
    
    def find(self, query: str, max_results: int = 10, search_content: bool = True) -> list:
        """Find files and content in the repository."""
        from ..processing.locator import FileLocator
        
        locator = FileLocator(
            repo_path=self.repo_path,
            config=self.config,
            strong_model=self.strong_model
        )
        
        result = locator.locate_files(query, max_results=max_results, search_content=search_content)
        return result.get('files', [])[:max_results]
    
    def build_context(self, files: Optional[list] = None, query: Optional[str] = None) -> object:
        """Build context from files or query."""
        from ..processing.context import ContextBuilder
        
        context_builder = ContextBuilder(
            repo_path=self.repo_path,
            config=self.config,
            weak_model=self.weak_model
        )
        
        if files:
            # Build context from specific files
            result = context_builder.build_context_from_files(files)
        elif query:
            # Build context from query
            result = context_builder.build_context_from_query(query)
        else:
            # Build context from all files
            result = context_builder.build_context_from_files([])
        
        # Return a simple object with context attribute
        class ContextResult:
            def __init__(self, context):
                self.context = context
        
        return ContextResult(result)
    
    def list_processable_files(self) -> list:
        """Get a list of files that can be processed."""
        return self.repository_analyzer.get_processable_files()
    
    def preview_file_selection(self, question: str) -> dict:
        """Preview which files would be selected for a question without generating an answer."""
        
        repository_structure = self.repository_analyzer.get_repository_structure()
        file_sizes = self.repository_analyzer.get_file_sizes()
        
        file_selection = self.context_builder.select_relevant_files(
            question=question,
            repository_structure=repository_structure,
            file_sizes=file_sizes,
        )
        
        valid_files, invalid_files = self.repository_analyzer.validate_file_selection(
            file_selection.selected_files
        )
        
        return {
            "question": question,
            "selected_files": file_selection.selected_files,
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "reasoning": file_selection.reasoning,
        }