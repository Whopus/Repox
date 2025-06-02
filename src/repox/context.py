"""Context building and management using repomix."""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from repomix import RepoProcessor, RepomixConfig
from rich.console import Console

from .config import RepoxConfig
from .models import (
    AIMessage,
    AIModel,
    ContextBuildingRequest,
    ContextBuildingResponse,
    FileSelectionRequest,
    FileSelectionResponse,
)


class ContextBuilder:
    """Builds optimized context using repomix and AI models."""
    
    def __init__(
        self,
        repo_path: Path,
        config: RepoxConfig,
        strong_model: AIModel,
        weak_model: AIModel,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.strong_model = strong_model
        self.weak_model = weak_model
        self.console = Console()
    
    def select_relevant_files(
        self,
        question: str,
        repository_structure: str,
        file_sizes: Dict[str, int],
    ) -> FileSelectionResponse:
        """Use strong AI model to select relevant files for the question."""
        
        # Prepare the prompt for file selection
        system_prompt = """You are an expert code analyst. Your task is to analyze a user's question about a codebase and determine which files are most relevant to answer that question.

Given:
1. A user question about the codebase
2. The repository structure
3. File sizes for each file

Your goal is to select the most relevant files that would help answer the question. Consider:
- Files that likely contain the functionality being asked about
- Configuration files if the question is about setup or configuration
- Test files if the question is about testing or examples
- Documentation files if they might contain relevant information
- Avoid selecting too many files (prefer quality over quantity)
- Avoid very large files unless they're clearly essential
- Prioritize files with clear, descriptive names related to the question

Respond with a JSON object containing:
- "selected_files": A list of file paths (relative to repository root)
- "reasoning": A brief explanation of why these files were selected

Keep the selection focused and relevant. Aim for 5-15 files unless the question requires broader context."""

        user_prompt = f"""Question: {question}

Repository Structure:
{repository_structure}

File Sizes:
{json.dumps(file_sizes, indent=2)}

Please select the most relevant files to answer this question."""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]
        
        if self.config.verbose:
            self.console.print("[bold blue]🤖 Analyzing question and selecting relevant files...[/bold blue]")
        
        response = self.strong_model.generate_sync(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        
        try:
            # Parse JSON response
            response_data = json.loads(response.content)
            return FileSelectionResponse(
                selected_files=response_data.get("selected_files", []),
                reasoning=response_data.get("reasoning", "No reasoning provided"),
            )
        except json.JSONDecodeError:
            # Fallback: try to extract file paths from response
            import re
            
            # Extract file paths using regex patterns
            selected_files = []
            
            # Pattern 1: Look for file paths in markdown format **path** or just path
            file_patterns = [
                r'\*\*([^*]+\.[a-zA-Z0-9]+)\*\*',  # **file.ext**
                r'`([^`]+\.[a-zA-Z0-9]+)`',        # `file.ext`
                r'"([^"]+\.[a-zA-Z0-9]+)"',        # "file.ext"
                r"'([^']+\.[a-zA-Z0-9]+)'",        # 'file.ext'
                r'([a-zA-Z0-9_/.-]+\.[a-zA-Z0-9]+)', # plain file.ext
            ]
            
            for pattern in file_patterns:
                matches = re.findall(pattern, response.content)
                for match in matches:
                    # Clean up the path
                    clean_path = match.strip().strip('"\'').strip('*').strip()
                    
                    # Validate it looks like a real file path
                    if ('/' in clean_path or '.' in clean_path) and not clean_path.startswith('http'):
                        # Check if it has a valid file extension
                        if any(ext in clean_path for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.md', '.txt', '.json', '.yaml', '.yml', '.toml']):
                            if clean_path not in selected_files:
                                selected_files.append(clean_path)
            
            return FileSelectionResponse(
                selected_files=selected_files,
                reasoning="Extracted files from response (JSON parsing failed)",
            )
    
    def build_context_with_repomix(self, selected_files: List[str]) -> str:
        """Use repomix to build context from selected files."""
        
        if not selected_files:
            return "No files selected for context."
        
        if self.config.verbose:
            self.console.print(f"[bold green]📦 Building context with repomix for {len(selected_files)} files...[/bold green]")
        
        # Create repomix configuration
        repomix_config = RepomixConfig()
        
        # Configure repomix to include only selected files
        repomix_config.include = selected_files
        
        # Configure output settings
        repomix_config.output.style = "markdown"
        repomix_config.output.show_line_numbers = True
        repomix_config.output.show_file_stats = True
        repomix_config.output.calculate_tokens = False
        
        # Disable security checks for internal processing
        repomix_config.security.enable_security_check = False
        
        # Configure ignore patterns to be more permissive
        repomix_config.ignore.use_default_ignore = False
        repomix_config.ignore.use_gitignore = False
        repomix_config.ignore.custom_patterns = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
                repomix_config.output.file_path = temp_file.name
            
            # Process repository with repomix
            processor = RepoProcessor(str(self.repo_path), config=repomix_config)
            result = processor.process()
            
            # Read the generated content
            with open(repomix_config.output.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up temporary file
            Path(repomix_config.output.file_path).unlink(missing_ok=True)
            
            return content
            
        except Exception as e:
            if self.config.verbose:
                self.console.print(f"[bold red]❌ Error building context with repomix: {e}[/bold red]")
            
            # Fallback: read files directly
            return self._build_context_fallback(selected_files)
    
    def _build_context_fallback(self, selected_files: List[str]) -> str:
        """Fallback method to build context by reading files directly."""
        context_parts = ["# Repository Context\n"]
        
        for file_path in selected_files:
            full_path = self.repo_path / file_path
            
            if not full_path.exists() or not full_path.is_file():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Determine file type for syntax highlighting
                suffix = full_path.suffix.lower()
                language_map = {
                    '.py': 'python',
                    '.js': 'javascript',
                    '.ts': 'typescript',
                    '.java': 'java',
                    '.cpp': 'cpp',
                    '.c': 'c',
                    '.h': 'c',
                    '.md': 'markdown',
                    '.json': 'json',
                    '.yaml': 'yaml',
                    '.yml': 'yaml',
                }
                language = language_map.get(suffix, 'text')
                
                context_parts.append(f"\n## File: {file_path}\n")
                context_parts.append(f"```{language}\n{content}\n```\n")
                
            except Exception as e:
                context_parts.append(f"\n## File: {file_path}\n")
                context_parts.append(f"Error reading file: {e}\n")
        
        return '\n'.join(context_parts)
    
    def optimize_context(
        self,
        question: str,
        raw_context: str,
        selected_files: List[str],
    ) -> ContextBuildingResponse:
        """Use weak AI model to optimize the context for the question."""
        
        # Check if context is too large
        if len(raw_context) <= self.config.max_context_size:
            return ContextBuildingResponse(
                optimized_context=raw_context,
                summary=f"Context is within size limits ({len(raw_context):,} characters). No optimization needed.",
            )
        
        if self.config.verbose:
            self.console.print("[bold yellow]🔧 Optimizing context for better AI processing...[/bold yellow]")
        
        system_prompt = """You are an expert at optimizing code context for AI analysis. Your task is to take a large code context and optimize it to focus on the most relevant parts for answering a specific question.

Guidelines:
1. Keep all code that is directly relevant to the question
2. Summarize or remove boilerplate code that doesn't add value
3. Preserve important function signatures, class definitions, and key logic
4. Keep comments and docstrings that explain functionality
5. Remove or summarize repetitive code patterns
6. Maintain the overall structure and relationships between components
7. Ensure the optimized context is still coherent and useful

Your goal is to create a focused, relevant context that helps answer the question while staying within reasonable size limits."""

        user_prompt = f"""Question: {question}

Selected Files: {', '.join(selected_files)}

Raw Context (truncated if too long):
{raw_context[:self.config.max_context_size]}

Please optimize this context to focus on answering the question. Provide:
1. The optimized context
2. A brief summary of what was changed

Optimized Context:"""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]
        
        response = self.weak_model.generate_sync(
            messages=messages,
            temperature=0.3,
            max_tokens=4000,
        )
        
        # Extract optimized context and summary
        content = response.content
        
        # Try to split into context and summary
        if "Summary:" in content or "Changes:" in content:
            parts = content.split("Summary:")
            if len(parts) == 1:
                parts = content.split("Changes:")
            
            if len(parts) == 2:
                optimized_context = parts[0].strip()
                summary = parts[1].strip()
            else:
                optimized_context = content
                summary = "Context optimized by AI model"
        else:
            optimized_context = content
            summary = "Context optimized by AI model"
        
        return ContextBuildingResponse(
            optimized_context=optimized_context,
            summary=summary,
        )