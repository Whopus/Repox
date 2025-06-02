"""File location functionality for Repox."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table

from .config import RepoxConfig
from .models import AIMessage, AIModel
from .repository import RepositoryAnalyzer


class FileLocator:
    """Locates files and content based on user queries."""
    
    def __init__(
        self,
        repo_path: Path,
        config: RepoxConfig,
        strong_model: AIModel,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.strong_model = strong_model
        self.console = Console()
        self.repository_analyzer = RepositoryAnalyzer(self.repo_path, self.config)
    
    def locate_files(self, query: str, max_results: Optional[int] = None, search_content: bool = False) -> Dict[str, any]:
        """Locate files relevant to the user's query."""
        
        if self.config.verbose:
            self.console.print(f"[bold blue]🔍 Locating files for query:[/bold blue] {query}")
        
        # Get repository structure and file information
        repository_structure = self.repository_analyzer.get_repository_structure()
        file_sizes = self.repository_analyzer.get_file_sizes()
        processable_files = self.repository_analyzer.get_processable_files()
        
        # Use AI to analyze and locate relevant files
        location_result = self._analyze_query_for_location(
            query, repository_structure, file_sizes, processable_files
        )
        
        # Validate and categorize files
        valid_files, invalid_files = self.repository_analyzer.validate_file_selection(
            location_result["files"]
        )
        
        # Search for content within files if needed
        content_matches = []
        if search_content:
            content_matches = self._search_content_in_files(query, valid_files)
        
        # Apply max_results limit if specified
        if max_results and len(valid_files) > max_results:
            valid_files = valid_files[:max_results]
        
        result = {
            "query": query,
            "located_files": valid_files,
            "invalid_files": invalid_files,
            "reasoning": location_result["reasoning"],
            "confidence": location_result["confidence"],
            "content_matches": content_matches,
            "search_strategy": location_result["strategy"],
        }
        
        if self.config.verbose:
            self._display_location_results(result)
        
        return result
    
    def _analyze_query_for_location(
        self,
        query: str,
        repository_structure: str,
        file_sizes: Dict[str, int],
        processable_files: List[str],
    ) -> Dict[str, any]:
        """Use AI to analyze the query and determine location strategy."""
        
        system_prompt = """You are an expert code analyst and file locator. Your task is to analyze a user's query and determine the best strategy to locate relevant files in a codebase.

Given:
1. A user query about finding specific functionality, files, or content
2. Repository structure
3. Available files and their sizes

Your goal is to:
1. Identify the most relevant files that likely contain what the user is looking for
2. Determine the search strategy (filename-based, content-based, or hybrid)
3. Provide reasoning for your choices
4. Assign a confidence level

Consider these strategies:
- **Filename-based**: When the query mentions specific file types, modules, or components
- **Content-based**: When looking for specific functions, classes, or code patterns
- **Hybrid**: When both filename and content analysis are needed

Respond with a JSON object containing:
- "files": List of file paths most likely to contain relevant content
- "strategy": One of "filename", "content", "hybrid"
- "reasoning": Detailed explanation of your analysis
- "confidence": Float between 0.0 and 1.0 indicating confidence in the selection
- "search_terms": List of terms to search for within files (if content-based)

Focus on precision over recall - it's better to find fewer, highly relevant files."""

        user_prompt = f"""Query: {query}

Repository Structure:
{repository_structure}

Available Files ({len(processable_files)} total):
{chr(10).join(processable_files[:50])}
{"..." if len(processable_files) > 50 else ""}

File Sizes:
{str(dict(list(file_sizes.items())[:20]))}
{"..." if len(file_sizes) > 20 else ""}

Please analyze this query and locate the most relevant files."""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]
        
        response = self.strong_model.generate_sync(
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        
        try:
            import json
            result = json.loads(response.content)
            
            # Ensure required fields exist
            result.setdefault("files", [])
            result.setdefault("strategy", "hybrid")
            result.setdefault("reasoning", "AI analysis completed")
            result.setdefault("confidence", 0.5)
            result.setdefault("search_terms", [])
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: extract information from text response
            return self._parse_location_response_fallback(response.content, processable_files)
    
    def _parse_location_response_fallback(
        self, response_text: str, processable_files: List[str]
    ) -> Dict[str, any]:
        """Fallback parser for location response."""
        
        # Extract file paths from response
        files = []
        for file_path in processable_files:
            if file_path in response_text or Path(file_path).name in response_text:
                files.append(file_path)
        
        # Determine strategy based on keywords
        strategy = "hybrid"
        if any(word in response_text.lower() for word in ["filename", "file name", "extension"]):
            strategy = "filename"
        elif any(word in response_text.lower() for word in ["content", "function", "class", "search"]):
            strategy = "content"
        
        # Extract confidence if mentioned
        confidence = 0.5
        confidence_match = re.search(r"confidence[:\s]*([0-9.]+)", response_text.lower())
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0  # Convert percentage
            except ValueError:
                pass
        
        return {
            "files": files[:10],  # Limit to top 10
            "strategy": strategy,
            "reasoning": "Extracted from AI response (JSON parsing failed)",
            "confidence": confidence,
            "search_terms": [],
        }
    
    def _search_content_in_files(
        self, query: str, file_paths: List[str]
    ) -> Dict[str, List[Dict[str, any]]]:
        """Search for content within the specified files."""
        
        content_matches = {}
        
        # Extract search terms from query
        search_terms = self._extract_search_terms(query)
        
        for file_path in file_paths:
            full_path = self.repo_path / file_path
            
            if not full_path.exists() or not full_path.is_file():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                matches = []
                lines = content.split('\n')
                
                # Search for each term
                for term in search_terms:
                    for line_num, line in enumerate(lines, 1):
                        if term.lower() in line.lower():
                            matches.append({
                                "line_number": line_num,
                                "line_content": line.strip(),
                                "search_term": term,
                                "context": self._get_line_context(lines, line_num - 1, 2)
                            })
                
                if matches:
                    content_matches[file_path] = matches
                    
            except Exception as e:
                if self.config.verbose:
                    self.console.print(f"[yellow]Warning: Could not search in {file_path}: {e}[/yellow]")
        
        return content_matches
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract potential search terms from the query."""
        
        # Remove common words and extract meaningful terms
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'how', 'what', 'where', 'when', 'why', 'which',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'can', 'may', 'might', 'must', 'this', 'that', 'these', 'those'
        }
        
        # Extract words and filter
        words = re.findall(r'\b\w+\b', query.lower())
        search_terms = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Also look for quoted strings
        quoted_terms = re.findall(r'"([^"]+)"', query)
        search_terms.extend(quoted_terms)
        
        # Look for function/class patterns
        function_patterns = re.findall(r'\b(\w+)\s*\(', query)
        search_terms.extend(function_patterns)
        
        class_patterns = re.findall(r'\bclass\s+(\w+)', query, re.IGNORECASE)
        search_terms.extend(class_patterns)
        
        return list(set(search_terms))  # Remove duplicates
    
    def _get_line_context(self, lines: List[str], line_index: int, context_size: int) -> List[str]:
        """Get context lines around a specific line."""
        start = max(0, line_index - context_size)
        end = min(len(lines), line_index + context_size + 1)
        return lines[start:end]
    
    def _display_location_results(self, result: Dict[str, any]) -> None:
        """Display location results in a formatted way."""
        
        # Main results table
        table = Table(title=f"🔍 File Location Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Query", result["query"])
        table.add_row("Strategy", result["search_strategy"])
        table.add_row("Confidence", f"{result['confidence']:.2f}")
        table.add_row("Files Found", str(len(result["located_files"])))
        table.add_row("Content Matches", str(len(result["content_matches"])))
        
        self.console.print(table)
        
        # Located files
        if result["located_files"]:
            self.console.print(f"\n[bold green]📁 Located Files ({len(result['located_files'])}):[/bold green]")
            for file_path in result["located_files"]:
                self.console.print(f"  ✅ {file_path}")
        
        # Content matches
        if result["content_matches"]:
            self.console.print(f"\n[bold yellow]🔍 Content Matches:[/bold yellow]")
            for file_path, matches in result["content_matches"].items():
                self.console.print(f"\n  📄 {file_path} ({len(matches)} matches):")
                for match in matches[:3]:  # Show first 3 matches per file
                    self.console.print(f"    Line {match['line_number']}: {match['line_content'][:80]}...")
                if len(matches) > 3:
                    self.console.print(f"    ... and {len(matches) - 3} more matches")
        
        # Reasoning
        self.console.print(f"\n[bold blue]💭 Reasoning:[/bold blue]")
        self.console.print(result["reasoning"])