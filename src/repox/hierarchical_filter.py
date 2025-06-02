"""Hierarchical filtering system for efficient token usage."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass

from rich.console import Console

from .config import RepoxConfig
from .models import AIMessage, AIModel


@dataclass
class ContentChunk:
    """Represents a chunk of file content with metadata."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    relevance_score: float = 0.0
    chunk_type: str = "code"  # code, comment, docstring, config, etc.


@dataclass
class FileRelevanceScore:
    """Relevance scoring for a file."""
    file_path: str
    path_score: float
    content_score: float
    size_penalty: float
    final_score: float
    reasoning: str


class HierarchicalFilter:
    """Implements hierarchical filtering to minimize token usage."""
    
    def __init__(self, repo_path: Path, config: RepoxConfig, weak_model: AIModel):
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.weak_model = weak_model
        self.console = Console()
        
        # File type priorities for different query types
        self.file_type_priorities = {
            "implementation": {".py": 1.0, ".js": 1.0, ".ts": 1.0, ".java": 1.0, ".cpp": 0.9, ".c": 0.9},
            "configuration": {".json": 1.0, ".yaml": 1.0, ".yml": 1.0, ".toml": 1.0, ".ini": 0.8, ".cfg": 0.8},
            "documentation": {".md": 1.0, ".rst": 0.9, ".txt": 0.7},
            "testing": {"test_": 1.0, "_test": 1.0, "spec_": 0.9, "_spec": 0.9},
        }
        
        # Content patterns that often contain noise
        self.noise_patterns = [
            r"^#\s*Table of Contents",
            r"^#\s*Installation",
            r"^#\s*License",
            r"^#\s*Contributing",
            r"^\s*\*\s*\[.*\]\(.*\)",  # Markdown links
            r"^\s*```\s*$",  # Empty code blocks
            r"^\s*---\s*$",  # Horizontal rules
        ]
    
    def filter_and_rank_files(
        self, 
        question: str, 
        candidate_files: List[str],
        max_files: int = 15
    ) -> List[FileRelevanceScore]:
        """Apply hierarchical filtering to rank and select files."""
        
        if self.config.verbose:
            self.console.print(f"[bold blue]🔍 Applying hierarchical filtering to {len(candidate_files)} files...[/bold blue]")
        
        # Step 1: Path-based scoring
        path_scores = self._score_files_by_path(question, candidate_files)
        
        # Step 2: Content sampling and scoring
        content_scores = self._score_files_by_content_sample(question, candidate_files)
        
        # Step 3: Combine scores and apply penalties
        final_scores = []
        for file_path in candidate_files:
            path_score = path_scores.get(file_path, 0.0)
            content_score = content_scores.get(file_path, 0.0)
            size_penalty = self._calculate_size_penalty(file_path)
            
            # Weighted combination
            final_score = (path_score * 0.3 + content_score * 0.6) * size_penalty
            
            final_scores.append(FileRelevanceScore(
                file_path=file_path,
                path_score=path_score,
                content_score=content_score,
                size_penalty=size_penalty,
                final_score=final_score,
                reasoning=f"Path: {path_score:.2f}, Content: {content_score:.2f}, Size penalty: {size_penalty:.2f}"
            ))
        
        # Sort by final score and return top files
        final_scores.sort(key=lambda x: x.final_score, reverse=True)
        selected = final_scores[:max_files]
        
        if self.config.verbose:
            self.console.print(f"[bold green]✅ Selected {len(selected)} files after hierarchical filtering[/bold green]")
            for score in selected[:5]:  # Show top 5
                self.console.print(f"  📄 {score.file_path} (score: {score.final_score:.3f})")
        
        return selected
    
    def extract_relevant_content(
        self, 
        question: str, 
        file_scores: List[FileRelevanceScore],
        max_tokens: int = 50000
    ) -> Dict[str, str]:
        """Extract only relevant content from selected files."""
        
        if self.config.verbose:
            self.console.print(f"[bold blue]📝 Extracting relevant content (max {max_tokens} tokens)...[/bold blue]")
        
        result = {}
        current_tokens = 0
        
        for file_score in file_scores:
            if current_tokens >= max_tokens:
                break
                
            file_path = file_score.file_path
            full_path = self.repo_path / file_path
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract relevant chunks
                relevant_content = self._extract_relevant_chunks(question, file_path, content)
                
                if relevant_content:
                    # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
                    content_tokens = len(relevant_content) // 4
                    
                    if current_tokens + content_tokens <= max_tokens:
                        result[file_path] = relevant_content
                        current_tokens += content_tokens
                    else:
                        # Truncate to fit remaining token budget
                        remaining_chars = (max_tokens - current_tokens) * 4
                        if remaining_chars > 100:  # Only include if meaningful
                            result[file_path] = relevant_content[:remaining_chars] + "\n... [truncated]"
                        break
                        
            except Exception as e:
                if self.config.verbose:
                    self.console.print(f"[yellow]⚠️ Error reading {file_path}: {e}[/yellow]")
                continue
        
        if self.config.verbose:
            self.console.print(f"[bold green]✅ Extracted content from {len(result)} files (~{current_tokens} tokens)[/bold green]")
        
        return result
    
    def _score_files_by_path(self, question: str, files: List[str]) -> Dict[str, float]:
        """Score files based on path relevance to the question."""
        scores = {}
        
        # Extract keywords from question
        keywords = self._extract_keywords(question)
        
        for file_path in files:
            score = 0.0
            path_lower = file_path.lower()
            
            # Keyword matching in path
            for keyword in keywords:
                if keyword in path_lower:
                    score += 1.0
                # Partial matching
                elif any(keyword in part for part in path_lower.split('/')):
                    score += 0.5
            
            # File type relevance
            query_type = self._classify_query_type(question)
            file_ext = Path(file_path).suffix.lower()
            
            if query_type in self.file_type_priorities:
                type_score = self.file_type_priorities[query_type].get(file_ext, 0.0)
                score += type_score
            
            # Special patterns
            if "test" in question.lower() and ("test" in path_lower or "spec" in path_lower):
                score += 1.0
            if "config" in question.lower() and any(x in path_lower for x in ["config", "setting", "env"]):
                score += 1.0
            if "api" in question.lower() and any(x in path_lower for x in ["api", "endpoint", "route"]):
                score += 1.0
            
            scores[file_path] = score
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}
        
        return scores
    
    def _score_files_by_content_sample(self, question: str, files: List[str]) -> Dict[str, float]:
        """Score files based on content relevance using sampling."""
        scores = {}
        
        # Sample content from files for efficient processing
        samples = {}
        for file_path in files:
            sample = self._get_content_sample(file_path)
            if sample:
                samples[file_path] = sample
        
        if not samples:
            return scores
        
        # Use weak model to score relevance
        try:
            batch_scores = self._batch_score_content_relevance(question, samples)
            scores.update(batch_scores)
        except Exception as e:
            if self.config.verbose:
                self.console.print(f"[yellow]⚠️ Content scoring failed, using fallback: {e}[/yellow]")
            # Fallback: simple keyword matching
            scores = self._fallback_content_scoring(question, samples)
        
        return scores
    
    def _get_content_sample(self, file_path: str, max_lines: int = 50) -> str:
        """Get a representative sample of file content."""
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return ""
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if len(lines) <= max_lines:
                return ''.join(lines)
            
            # Smart sampling: beginning, middle, end
            sample_lines = []
            
            # Beginning (first 20 lines)
            sample_lines.extend(lines[:20])
            
            # Middle (10 lines from middle)
            mid_start = len(lines) // 2 - 5
            mid_end = len(lines) // 2 + 5
            sample_lines.extend(lines[mid_start:mid_end])
            
            # End (last 20 lines)
            sample_lines.extend(lines[-20:])
            
            return ''.join(sample_lines)
            
        except Exception:
            return ""
    
    def _batch_score_content_relevance(self, question: str, samples: Dict[str, str]) -> Dict[str, float]:
        """Use AI to score content relevance in batches."""
        
        # Prepare batch prompt
        files_text = ""
        for file_path, content in samples.items():
            files_text += f"\n--- FILE: {file_path} ---\n{content[:1000]}...\n"
        
        system_prompt = """You are analyzing code files for relevance to a user question. 
Score each file from 0.0 to 1.0 based on how relevant its content is to answering the question.

Consider:
- Direct relevance to the question topic
- Presence of relevant functions, classes, or concepts
- Quality and completeness of relevant code
- Avoid giving high scores to files with mostly boilerplate or irrelevant content

Respond with JSON: {"scores": {"file_path": score, ...}}"""

        user_prompt = f"""Question: {question}

Files to score:
{files_text}

Score each file's relevance to the question (0.0 to 1.0):"""

        messages = [
            AIMessage(role="system", content=system_prompt),
            AIMessage(role="user", content=user_prompt),
        ]
        
        response = self.weak_model.generate_sync(
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
        )
        
        try:
            result = json.loads(response.content)
            return result.get("scores", {})
        except json.JSONDecodeError:
            # Fallback parsing
            scores = {}
            for file_path in samples.keys():
                # Simple regex to find scores
                pattern = rf"{re.escape(file_path)}.*?(\d+\.?\d*)"
                match = re.search(pattern, response.content)
                if match:
                    try:
                        scores[file_path] = float(match.group(1))
                    except ValueError:
                        scores[file_path] = 0.5
                else:
                    scores[file_path] = 0.5
            return scores
    
    def _fallback_content_scoring(self, question: str, samples: Dict[str, str]) -> Dict[str, float]:
        """Fallback content scoring using keyword matching."""
        keywords = self._extract_keywords(question)
        scores = {}
        
        for file_path, content in samples.items():
            content_lower = content.lower()
            score = 0.0
            
            for keyword in keywords:
                # Count keyword occurrences
                count = content_lower.count(keyword)
                score += min(count * 0.1, 1.0)  # Cap contribution per keyword
            
            # Normalize by content length
            if len(content) > 0:
                score = score / (len(content) / 1000)  # Per 1000 chars
            
            scores[file_path] = min(score, 1.0)
        
        return scores
    
    def _extract_relevant_chunks(self, question: str, file_path: str, content: str) -> str:
        """Extract only relevant chunks from file content."""
        
        # For small files, return as-is
        if len(content) < 2000:
            return self._clean_content(content)
        
        lines = content.split('\n')
        keywords = self._extract_keywords(question)
        
        relevant_chunks = []
        current_chunk = []
        in_relevant_section = False
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains keywords
            has_keywords = any(keyword in line_lower for keyword in keywords)
            
            # Check if we're in a function/class definition
            is_definition = any(line.strip().startswith(prefix) for prefix in 
                             ['def ', 'class ', 'function ', 'const ', 'let ', 'var '])
            
            if has_keywords or is_definition:
                in_relevant_section = True
                current_chunk.append(line)
            elif in_relevant_section:
                current_chunk.append(line)
                
                # End section if we hit empty lines or new definitions
                if not line.strip() or is_definition:
                    if len(current_chunk) > 1:  # Avoid single-line chunks
                        relevant_chunks.extend(current_chunk)
                        relevant_chunks.append("")  # Separator
                    current_chunk = []
                    in_relevant_section = False
        
        # Add any remaining chunk
        if current_chunk:
            relevant_chunks.extend(current_chunk)
        
        # If no relevant chunks found, return beginning of file
        if not relevant_chunks:
            return self._clean_content('\n'.join(lines[:50]))
        
        return self._clean_content('\n'.join(relevant_chunks))
    
    def _clean_content(self, content: str) -> str:
        """Remove noise patterns from content."""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip lines matching noise patterns
            if any(re.match(pattern, line) for pattern in self.noise_patterns):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _extract_keywords(self, question: str) -> List[str]:
        """Extract relevant keywords from the question."""
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'where', 'when', 'why', 'is', 'are', 'was', 'were', 'do', 'does', 'did'}
        
        # Extract words and filter
        words = re.findall(r'\b\w+\b', question.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords[:10]  # Limit to top 10 keywords
    
    def _classify_query_type(self, question: str) -> str:
        """Classify the type of query to prioritize relevant file types."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['test', 'testing', 'spec', 'unit test']):
            return "testing"
        elif any(word in question_lower for word in ['config', 'configuration', 'setting', 'setup']):
            return "configuration"
        elif any(word in question_lower for word in ['document', 'readme', 'guide', 'how to']):
            return "documentation"
        else:
            return "implementation"
    
    def _calculate_size_penalty(self, file_path: str) -> float:
        """Calculate penalty for large files."""
        full_path = self.repo_path / file_path
        
        if not full_path.exists():
            return 0.0
        
        try:
            size = full_path.stat().st_size
            
            # No penalty for small files
            if size < 10000:  # 10KB
                return 1.0
            
            # Gradual penalty for larger files
            if size < 50000:  # 50KB
                return 0.9
            elif size < 100000:  # 100KB
                return 0.8
            elif size < 500000:  # 500KB
                return 0.6
            else:
                return 0.4  # Heavy penalty for very large files
                
        except Exception:
            return 0.5