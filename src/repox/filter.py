"""Enhanced filtering functionality for Repox."""

import fnmatch
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pathspec
from rich.console import Console

from .config import RepoxConfig


class SmartFilter:
    """Enhanced filtering system with intelligent pattern matching."""
    
    def __init__(self, config: RepoxConfig):
        self.config = config
        self.console = Console()
        
        # Create pathspec for exclusion patterns
        self.exclude_spec = pathspec.PathSpec.from_lines(
            "gitwildmatch", self.config.exclude_patterns
        )
        
        # Define file type categories
        self.file_categories = {
            "source_code": {
                ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".hpp",
                ".cs", ".php", ".rb", ".go", ".rs", ".swift", ".kt", ".scala", ".clj",
                ".hs", ".ml", ".fs", ".vb", ".pas", ".ada", ".cob", ".for", ".f90",
                ".pl", ".pm", ".r", ".m", ".mm", ".asm", ".s"
            },
            "config": {
                ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".config",
                ".properties", ".env", ".envrc", ".editorconfig", ".gitignore",
                ".dockerignore", ".eslintrc", ".prettierrc", ".babelrc"
            },
            "documentation": {
                ".md", ".rst", ".txt", ".adoc", ".org", ".tex", ".rtf"
            },
            "web": {
                ".html", ".htm", ".css", ".scss", ".sass", ".less", ".vue", ".svelte"
            },
            "data": {
                ".csv", ".json", ".xml", ".sql", ".db", ".sqlite", ".sqlite3"
            },
            "build": {
                ".mk", ".cmake", ".gradle", ".maven", ".sbt", ".cabal", ".stack"
            },
            "scripts": {
                ".sh", ".bash", ".zsh", ".fish", ".ps1", ".bat", ".cmd"
            }
        }
        
        # Reverse mapping for quick lookup
        self.extension_to_category = {}
        for category, extensions in self.file_categories.items():
            for ext in extensions:
                self.extension_to_category[ext] = category
    
    def should_include_file(self, file_path: Path, base_path: Path) -> Tuple[bool, str]:
        """
        Determine if a file should be included based on enhanced filtering rules.
        
        Returns:
            Tuple of (should_include, reason)
        """
        try:
            relative_path = file_path.relative_to(base_path)
        except ValueError:
            return False, "File is outside repository"
        
        # Check basic file properties
        if not file_path.exists():
            return False, "File does not exist"
        
        if not file_path.is_file():
            return False, "Not a regular file"
        
        # Check if file is too large
        try:
            file_size = file_path.stat().st_size
            if file_size > self.config.max_file_size:
                return False, f"File too large ({file_size:,} bytes)"
        except OSError:
            return False, "Cannot access file size"
        
        # Check exclusion patterns
        if self.exclude_spec.match_file(str(relative_path)):
            return False, "Matches exclusion pattern"
        
        # Check if it's a hidden file (but allow some exceptions)
        if file_path.name.startswith('.'):
            allowed_hidden = {'.env.example', '.gitignore', '.dockerignore', '.editorconfig'}
            if file_path.name not in allowed_hidden:
                return False, "Hidden file"
        
        # Check file extension
        extension = file_path.suffix.lower()
        if not extension:
            # Files without extension - be selective
            if self._is_likely_text_file(file_path):
                return True, "Text file without extension"
            else:
                return False, "Binary file without extension"
        
        # Check if it's a known file type
        if extension in self.extension_to_category:
            return True, f"Known {self.extension_to_category[extension]} file"
        
        # Check for binary files
        if self._is_binary_file(file_path):
            return False, "Binary file"
        
        # Default: include if it seems like a text file
        if self._is_likely_text_file(file_path):
            return True, "Likely text file"
        
        return False, "Unknown file type"
    
    def filter_files_by_relevance(
        self,
        files: List[Path],
        query: str,
        base_path: Path,
    ) -> List[Tuple[Path, float, str]]:
        """
        Filter and rank files by relevance to the query.
        
        Returns:
            List of (file_path, relevance_score, reason) tuples, sorted by relevance
        """
        scored_files = []
        
        for file_path in files:
            should_include, reason = self.should_include_file(file_path, base_path)
            
            if not should_include:
                continue
            
            relevance_score = self._calculate_relevance_score(file_path, query, base_path)
            scored_files.append((file_path, relevance_score, reason))
        
        # Sort by relevance score (descending)
        scored_files.sort(key=lambda x: x[1], reverse=True)
        
        return scored_files
    
    def _calculate_relevance_score(self, file_path: Path, query: str, base_path: Path) -> float:
        """Calculate relevance score for a file based on the query."""
        score = 0.0
        
        try:
            relative_path = file_path.relative_to(base_path)
        except ValueError:
            return 0.0
        
        # Extract keywords from query
        query_keywords = self._extract_keywords(query)
        
        # Score based on filename match
        filename = file_path.name.lower()
        for keyword in query_keywords:
            if keyword in filename:
                score += 2.0
        
        # Score based on path match
        path_str = str(relative_path).lower()
        for keyword in query_keywords:
            if keyword in path_str:
                score += 1.0
        
        # Score based on file type relevance
        extension = file_path.suffix.lower()
        category = self.extension_to_category.get(extension, "unknown")
        
        # Boost certain file types based on query context
        if any(word in query.lower() for word in ["config", "configuration", "settings"]):
            if category == "config":
                score += 3.0
        
        if any(word in query.lower() for word in ["test", "testing", "spec"]):
            if "test" in path_str or "spec" in path_str:
                score += 3.0
        
        if any(word in query.lower() for word in ["doc", "documentation", "readme"]):
            if category == "documentation":
                score += 3.0
        
        # Boost main/important files
        important_files = {
            "main.py", "app.py", "index.js", "main.js", "server.js",
            "readme.md", "readme.txt", "license", "makefile", "dockerfile"
        }
        if filename in important_files:
            score += 1.5
        
        # Penalize deeply nested files
        depth = len(relative_path.parts)
        if depth > 3:
            score -= (depth - 3) * 0.2
        
        # Boost recently modified files (if we can access the info)
        try:
            import time
            mtime = file_path.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            if age_days < 7:  # Recently modified
                score += 0.5
        except OSError:
            pass
        
        return max(0.0, score)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from the query."""
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'how', 'what', 'where', 'when', 'why', 'which',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if a file is binary."""
        binary_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o', '.a', '.lib',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg', '.webp',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
            '.db', '.sqlite', '.sqlite3', '.mdb'
        }
        
        if file_path.suffix.lower() in binary_extensions:
            return True
        
        # Check file content for binary data
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:  # Null bytes indicate binary
                    return True
        except (OSError, PermissionError):
            return True  # Assume binary if we can't read it
        
        return False
    
    def _is_likely_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        if self._is_binary_file(file_path):
            return False
        
        # Check for text file indicators
        text_indicators = [
            'readme', 'license', 'changelog', 'makefile', 'dockerfile',
            'requirements', 'pipfile', 'gemfile', 'package'
        ]
        
        filename_lower = file_path.name.lower()
        if any(indicator in filename_lower for indicator in text_indicators):
            return True
        
        # Try to read a small portion to check encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(512)  # Try to read first 512 characters
            return True
        except (UnicodeDecodeError, OSError, PermissionError):
            return False
    
    def get_smart_exclusion_patterns(self, repo_path: Path) -> List[str]:
        """Generate smart exclusion patterns based on repository analysis."""
        patterns = list(self.config.exclude_patterns)
        
        # Analyze repository to add smart patterns
        try:
            # Check for common large directories
            large_dirs = []
            for item in repo_path.iterdir():
                if item.is_dir():
                    try:
                        file_count = sum(1 for _ in item.rglob('*') if _.is_file())
                        if file_count > self.config.large_dir_threshold:
                            large_dirs.append(item.name)
                    except (OSError, PermissionError):
                        pass
            
            # Add patterns for large directories
            for dir_name in large_dirs:
                if dir_name not in self.config.skip_large_dirs:
                    patterns.append(f"{dir_name}/**")
            
            # Check for language-specific patterns
            has_python = any(f.suffix == '.py' for f in repo_path.rglob('*.py'))
            has_node = (repo_path / 'package.json').exists()
            has_java = any(f.suffix == '.java' for f in repo_path.rglob('*.java'))
            
            if has_python:
                patterns.extend([
                    '**/__pycache__/**',
                    '*.pyc',
                    '*.pyo',
                    '*.pyd',
                    '.pytest_cache/**',
                    '.mypy_cache/**'
                ])
            
            if has_node:
                patterns.extend([
                    'node_modules/**',
                    'npm-debug.log*',
                    'yarn-debug.log*',
                    'yarn-error.log*'
                ])
            
            if has_java:
                patterns.extend([
                    '*.class',
                    'target/**',
                    '.gradle/**'
                ])
        
        except Exception as e:
            if self.config.verbose:
                self.console.print(f"[yellow]Warning: Could not analyze repository for smart patterns: {e}[/yellow]")
        
        return patterns
    
    def create_focused_filter(self, focus_areas: List[str]) -> 'SmartFilter':
        """Create a filter focused on specific areas of the codebase."""
        # Create a copy of the current filter with modified patterns
        focused_config = RepoxConfig(**self.config.model_dump())
        
        # Adjust patterns based on focus areas
        additional_excludes = []
        
        for area in focus_areas:
            area_lower = area.lower()
            
            if area_lower in ['test', 'tests', 'testing']:
                # When focusing on tests, exclude non-test files more aggressively
                additional_excludes.extend([
                    'docs/**',
                    'examples/**',
                    'demo/**'
                ])
            elif area_lower in ['doc', 'docs', 'documentation']:
                # When focusing on docs, exclude test and build files
                additional_excludes.extend([
                    'test/**',
                    'tests/**',
                    'build/**',
                    'dist/**'
                ])
            elif area_lower in ['config', 'configuration']:
                # Focus on configuration files
                additional_excludes.extend([
                    'test/**',
                    'tests/**',
                    'docs/**',
                    'examples/**'
                ])
        
        focused_config.exclude_patterns.extend(additional_excludes)
        
        return SmartFilter(focused_config)