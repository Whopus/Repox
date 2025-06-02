"""Context building and management using repomix."""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from repomix import RepoProcessor, RepomixConfig
from rich.console import Console

from ..core.config import RepoxConfig
from .filter import SmartFilter
from .hierarchical_filter import HierarchicalFilter
from ..utils.models import (
    AIMessage,
    AIModel,
    ContextBuildingRequest,
    ContextBuildingResponse,
    FileSelectionRequest,
    FileSelectionResponse,
)
from ..repository.repomix_integration import RepomixIntegration


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
        self.smart_filter = SmartFilter(config)
        self.hierarchical_filter = HierarchicalFilter(repo_path, config, weak_model)
        self.repomix_integration = RepomixIntegration(repo_path, config)
    
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
    
    def select_relevant_files_hierarchical(
        self,
        question: str,
        repository_structure: str,
        file_sizes: Dict[str, int],
    ) -> FileSelectionResponse:
        """Use hierarchical filtering for efficient file selection."""
        
        if self.config.verbose:
            self.console.print("[bold blue]🔍 Using hierarchical filtering for file selection...[/bold blue]")
        
        # Get candidate files from repository
        candidate_files = list(file_sizes.keys())
        
        # Apply hierarchical filtering
        file_scores = self.hierarchical_filter.filter_and_rank_files(
            question=question,
            candidate_files=candidate_files,
            max_files=15
        )
        
        # Extract selected files
        selected_files = [score.file_path for score in file_scores]
        
        # Create reasoning summary
        reasoning_parts = [
            f"Applied hierarchical filtering to {len(candidate_files)} files.",
            f"Selected top {len(selected_files)} files based on relevance scoring.",
        ]
        
        if file_scores:
            top_score = file_scores[0]
            reasoning_parts.append(
                f"Top file: {top_score.file_path} (score: {top_score.final_score:.3f})"
            )
        
        return FileSelectionResponse(
            selected_files=selected_files,
            reasoning=" ".join(reasoning_parts),
        )
    
    def build_context_with_hierarchical_filtering(
        self,
        question: str,
        repository_structure: str,
        file_sizes: Dict[str, int],
    ) -> str:
        """Build context using hierarchical filtering for optimal token usage."""
        
        if self.config.verbose:
            self.console.print("[bold blue]🚀 Building context with hierarchical filtering...[/bold blue]")
        
        # Step 1: Select relevant files using hierarchical filtering
        file_selection = self.select_relevant_files_hierarchical(
            question, repository_structure, file_sizes
        )
        
        if not file_selection.selected_files:
            return "No relevant files found for the question."
        
        # Step 2: Extract relevant content with token optimization
        relevant_content = self.hierarchical_filter.extract_relevant_content(
            question=question,
            file_scores=self.hierarchical_filter.filter_and_rank_files(
                question, file_selection.selected_files
            ),
            max_tokens=self.config.max_context_size // 4  # Conservative token estimate
        )
        
        if not relevant_content:
            return "No relevant content found in selected files."
        
        # Step 3: Build formatted context
        context_parts = [
            "# Repository Context (Hierarchically Filtered)\n",
            f"**Question:** {question}\n",
            f"**Files analyzed:** {len(relevant_content)}\n",
            f"**Selection reasoning:** {file_selection.reasoning}\n\n",
        ]
        
        for file_path, content in relevant_content.items():
            context_parts.append(f"## File: {file_path}\n")
            context_parts.append(f"```{self._get_file_language(file_path)}\n")
            context_parts.append(content)
            context_parts.append("\n```\n\n")
        
        final_context = "".join(context_parts)
        
        if self.config.verbose:
            estimated_tokens = len(final_context) // 4
            self.console.print(f"[bold green]✅ Built optimized context (~{estimated_tokens} tokens)[/bold green]")
        
        return final_context
    
    def _get_file_language(self, file_path: str) -> str:
        """Get language identifier for syntax highlighting."""
        suffix = Path(file_path).suffix.lower()
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
            '.toml': 'toml',
            '.ini': 'ini',
            '.cfg': 'ini',
        }
        return language_map.get(suffix, 'text')
    
    def build_context_with_repomix(self, selected_files: List[str]) -> str:
        """Use enhanced repomix integration to build context from selected files."""
        
        if not selected_files:
            return "No files selected for context."
        
        if self.config.verbose:
            self.console.print(f"[bold green]📦 Building context with enhanced repomix for {len(selected_files)} files...[/bold green]")
        
        try:
            # Use enhanced repomix integration
            context_result = self.repomix_integration.build_context(
                selected_files=selected_files,
                compression_enabled=False,
                max_size=self.config.max_context_size,
            )
            
            if context_result["success"]:
                return context_result["content"]
            else:
                if self.config.verbose:
                    self.console.print(f"[bold red]❌ Error building context: {context_result['error']}[/bold red]")
                return self._build_context_fallback(selected_files)
            
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