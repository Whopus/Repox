"""Repository analysis and file management."""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pathspec
from rich.console import Console
from rich.tree import Tree

from ..core.config import RepoxConfig


class RepositoryAnalyzer:
    """Analyzes repository structure and manages file selection."""
    
    def __init__(self, repo_path: Path, config: RepoxConfig):
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.console = Console()
        
        # Create pathspec for exclusion patterns
        self.exclude_spec = pathspec.PathSpec.from_lines(
            "gitwildmatch", self.config.exclude_patterns
        )
    
    def get_repository_structure(self) -> str:
        """Get a tree representation of the repository structure."""
        tree = Tree(f"📁 {self.repo_path.name}")
        self._build_tree(self.repo_path, tree, max_depth=3)
        
        # Convert tree to string representation
        with self.console.capture() as capture:
            self.console.print(tree)
        
        return capture.get()
    
    def _build_tree(self, path: Path, tree: Tree, max_depth: int, current_depth: int = 0) -> None:
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                # Skip hidden files and excluded patterns
                if item.name.startswith('.') or self._should_exclude(item):
                    continue
                
                # Skip large directories
                if item.is_dir() and self._is_large_directory(item):
                    tree.add(f"📁 {item.name} (skipped - too many files)")
                    continue
                
                if item.is_dir():
                    subtree = tree.add(f"📁 {item.name}")
                    self._build_tree(item, subtree, max_depth, current_depth + 1)
                else:
                    size = self._get_file_size(item)
                    if size > self.config.max_file_size:
                        tree.add(f"📄 {item.name} (too large - {size:,} bytes)")
                    else:
                        tree.add(f"📄 {item.name}")
        
        except PermissionError:
            tree.add("❌ Permission denied")
    
    def _should_exclude(self, path: Path) -> bool:
        """Check if a path should be excluded."""
        relative_path = path.relative_to(self.repo_path)
        return self.exclude_spec.match_file(str(relative_path))
    
    def _is_large_directory(self, dir_path: Path) -> bool:
        """Check if a directory is too large to process."""
        if dir_path.name in self.config.skip_large_dirs:
            return True
        
        try:
            file_count = sum(1 for _ in dir_path.iterdir())
            return file_count > self.config.large_dir_threshold
        except (PermissionError, OSError):
            return True
    
    def _get_file_size(self, file_path: Path) -> int:
        """Get file size safely."""
        try:
            return file_path.stat().st_size
        except (OSError, PermissionError):
            return 0
    
    def get_file_sizes(self) -> Dict[str, int]:
        """Get sizes of all processable files in the repository."""
        file_sizes = {}
        
        for file_path in self._walk_repository():
            if file_path.is_file() and not self._should_exclude(file_path):
                size = self._get_file_size(file_path)
                if size <= self.config.max_file_size:
                    relative_path = str(file_path.relative_to(self.repo_path))
                    file_sizes[relative_path] = size
        
        return file_sizes
    
    def _walk_repository(self) -> List[Path]:
        """Walk through repository files, skipping large directories."""
        files = []
        
        def _walk_dir(dir_path: Path) -> None:
            try:
                if self._is_large_directory(dir_path):
                    return
                
                for item in dir_path.iterdir():
                    if item.name.startswith('.'):
                        continue
                    
                    if item.is_dir():
                        _walk_dir(item)
                    elif item.is_file():
                        files.append(item)
            
            except (PermissionError, OSError):
                pass
        
        _walk_dir(self.repo_path)
        return files
    
    def get_processable_files(self) -> List[str]:
        """Get list of files that can be processed."""
        processable_files = []
        
        for file_path in self._walk_repository():
            if (file_path.is_file() and 
                not self._should_exclude(file_path) and
                self._get_file_size(file_path) <= self.config.max_file_size):
                
                relative_path = str(file_path.relative_to(self.repo_path))
                processable_files.append(relative_path)
        
        return processable_files
    
    def validate_file_selection(self, selected_files: List[str]) -> Tuple[List[str], List[str]]:
        """Validate and filter selected files."""
        valid_files = []
        invalid_files = []
        
        for file_path in selected_files:
            full_path = self.repo_path / file_path
            
            if not full_path.exists():
                invalid_files.append(f"{file_path} (not found)")
                continue
            
            if not full_path.is_file():
                invalid_files.append(f"{file_path} (not a file)")
                continue
            
            if self._should_exclude(full_path):
                invalid_files.append(f"{file_path} (excluded by patterns)")
                continue
            
            size = self._get_file_size(full_path)
            if size > self.config.max_file_size:
                invalid_files.append(f"{file_path} (too large - {size:,} bytes)")
                continue
            
            valid_files.append(file_path)
        
        return valid_files, invalid_files
    
    def get_repository_summary(self) -> Dict[str, any]:
        """Get a summary of the repository."""
        file_sizes = self.get_file_sizes()
        
        total_files = len(file_sizes)
        total_size = sum(file_sizes.values())
        
        # Get file type distribution
        file_types = {}
        for file_path in file_sizes.keys():
            ext = Path(file_path).suffix.lower()
            if not ext:
                ext = "(no extension)"
            file_types[ext] = file_types.get(ext, 0) + 1
        
        # Get largest files
        largest_files = sorted(
            file_sizes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Get processable files count
        processable_files = self.get_processable_files()
        processable_count = len(processable_files)
        
        # Extract languages from file extensions
        languages = set()
        for ext in file_types.keys():
            if ext != "(no extension)":
                # Map common extensions to languages
                lang_map = {
                    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
                    '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.cs': 'C#',
                    '.go': 'Go', '.rs': 'Rust', '.php': 'PHP', '.rb': 'Ruby',
                    '.swift': 'Swift', '.kt': 'Kotlin', '.scala': 'Scala',
                    '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
                    '.json': 'JSON', '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML',
                    '.md': 'Markdown', '.txt': 'Text', '.sh': 'Shell',
                    '.sql': 'SQL', '.r': 'R', '.m': 'MATLAB'
                }
                if ext in lang_map:
                    languages.add(lang_map[ext])
                else:
                    languages.add(ext[1:].upper())  # Remove dot and uppercase
        
        return {
            "total_files": total_files,
            "processable_files": processable_count,
            "total_size": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "file_types": file_types,
            "languages": sorted(list(languages)),
            "largest_files": largest_files,
            "repository_path": str(self.repo_path),
        }