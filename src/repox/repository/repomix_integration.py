"""Enhanced repomix integration for Repox."""

import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from repomix import RepoProcessor, RepomixConfig
from rich.console import Console

from ..core.config import RepoxConfig
from ..processing.filter import SmartFilter


class RepomixIntegration:
    """Enhanced integration with repomix for better context building."""
    
    def __init__(self, repo_path: Path, config: RepoxConfig):
        self.repo_path = Path(repo_path).resolve()
        self.config = config
        self.console = Console()
        self.smart_filter = SmartFilter(config)
    
    def create_optimized_config(
        self,
        selected_files: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        compression_enabled: bool = False,
    ) -> RepomixConfig:
        """Create an optimized repomix configuration."""
        
        repomix_config = RepomixConfig()
        
        # Configure file inclusion
        if selected_files:
            repomix_config.include = selected_files
        
        # Configure output settings
        repomix_config.output.style = "markdown"
        repomix_config.output.show_line_numbers = True
        repomix_config.output.show_file_stats = True
        repomix_config.output.calculate_tokens = True
        
        # Configure compression
        repomix_config.compression.enabled = compression_enabled
        if compression_enabled:
            repomix_config.compression.keep_signatures = True
            repomix_config.compression.keep_docstrings = True
            repomix_config.compression.keep_interfaces = True
        
        # Configure security
        repomix_config.security.enable_security_check = True
        
        # Configure ignore patterns
        repomix_config.ignore.use_default_ignore = True
        repomix_config.ignore.use_gitignore = True
        
        # Add smart exclusion patterns
        smart_patterns = self.smart_filter.get_smart_exclusion_patterns(self.repo_path)
        repomix_config.ignore.custom_patterns = smart_patterns
        
        # Apply focus-specific filtering
        if focus_areas:
            focused_filter = self.smart_filter.create_focused_filter(focus_areas)
            repomix_config.ignore.custom_patterns.extend(
                focused_filter.config.exclude_patterns
            )
        
        return repomix_config
    
    def build_context(
        self,
        selected_files: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None,
        compression_enabled: bool = False,
        max_size: Optional[int] = None,
    ) -> Dict[str, any]:
        """Build context using repomix with enhanced configuration."""
        
        if self.config.verbose:
            self.console.print("[bold green]📦 Building context with enhanced repomix integration...[/bold green]")
        
        # Create optimized configuration
        repomix_config = self.create_optimized_config(
            selected_files=selected_files,
            focus_areas=focus_areas,
            compression_enabled=compression_enabled,
        )
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
            repomix_config.output.file_path = temp_file.name
        
        try:
            # Process repository with repomix
            processor = RepoProcessor(str(self.repo_path), config=repomix_config)
            result = processor.process()
            
            # Read the generated content
            with open(repomix_config.output.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if content is too large
            if max_size and len(content) > max_size:
                if self.config.verbose:
                    self.console.print(f"[yellow]⚠️  Content too large ({len(content):,} chars), enabling compression...[/yellow]")
                
                # Retry with compression
                return self.build_context(
                    selected_files=selected_files,
                    focus_areas=focus_areas,
                    compression_enabled=True,
                    max_size=max_size,
                )
            
            # Extract metadata from result
            metadata = {
                "total_files": getattr(result, 'total_files', 0),
                "total_size": getattr(result, 'total_size', 0),
                "total_tokens": getattr(result, 'total_tokens', 0),
                "compression_enabled": compression_enabled,
                "focus_areas": focus_areas or [],
                "selected_files": selected_files or [],
            }
            
            return {
                "content": content,
                "metadata": metadata,
                "success": True,
                "error": None,
            }
            
        except Exception as e:
            error_msg = f"Error building context with repomix: {e}"
            
            if self.config.verbose:
                self.console.print(f"[bold red]❌ {error_msg}[/bold red]")
            
            # Fallback to direct file reading
            return self._build_context_fallback(selected_files or [])
            
        finally:
            # Clean up temporary file
            try:
                Path(repomix_config.output.file_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def _build_context_fallback(self, selected_files: List[str]) -> Dict[str, any]:
        """Fallback method to build context by reading files directly."""
        
        if self.config.verbose:
            self.console.print("[yellow]🔄 Using fallback context building method...[/yellow]")
        
        context_parts = ["# Repository Context (Fallback Method)\n"]
        total_size = 0
        processed_files = 0
        
        for file_path in selected_files:
            full_path = self.repo_path / file_path
            
            if not full_path.exists() or not full_path.is_file():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Check file size
                if len(content) > self.config.max_file_size:
                    context_parts.append(f"\n## File: {file_path}\n")
                    context_parts.append(f"*File too large ({len(content):,} characters) - showing first 1000 characters*\n")
                    context_parts.append(f"```\n{content[:1000]}\n...\n```\n")
                else:
                    # Determine file type for syntax highlighting
                    suffix = full_path.suffix.lower()
                    language_map = {
                        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                        '.java': 'java', '.cpp': 'cpp', '.c': 'c', '.h': 'c',
                        '.md': 'markdown', '.json': 'json', '.yaml': 'yaml',
                        '.yml': 'yaml', '.toml': 'toml', '.ini': 'ini',
                        '.sh': 'bash', '.bash': 'bash', '.zsh': 'zsh',
                        '.html': 'html', '.css': 'css', '.scss': 'scss',
                        '.xml': 'xml', '.sql': 'sql'
                    }
                    language = language_map.get(suffix, 'text')
                    
                    context_parts.append(f"\n## File: {file_path}\n")
                    context_parts.append(f"```{language}\n{content}\n```\n")
                
                total_size += len(content)
                processed_files += 1
                
            except Exception as e:
                context_parts.append(f"\n## File: {file_path}\n")
                context_parts.append(f"*Error reading file: {e}*\n")
        
        content = '\n'.join(context_parts)
        
        metadata = {
            "total_files": processed_files,
            "total_size": total_size,
            "total_tokens": 0,  # Not calculated in fallback
            "compression_enabled": False,
            "focus_areas": [],
            "selected_files": selected_files,
        }
        
        return {
            "content": content,
            "metadata": metadata,
            "success": True,
            "error": None,
        }
    
    def analyze_repository_structure(self) -> Dict[str, any]:
        """Analyze repository structure using repomix."""
        
        try:
            # Create a minimal config for structure analysis
            repomix_config = RepomixConfig()
            repomix_config.output.style = "markdown"
            repomix_config.output.show_file_stats = True
            repomix_config.output.calculate_tokens = False
            
            # Only include a few representative files for structure analysis
            repomix_config.include = []
            
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
                repomix_config.output.file_path = temp_file.name
            
            processor = RepoProcessor(str(self.repo_path), config=repomix_config)
            result = processor.process()
            
            # Extract structure information
            structure_info = {
                "total_files": getattr(result, 'total_files', 0),
                "total_size": getattr(result, 'total_size', 0),
                "file_types": getattr(result, 'file_types', {}),
                "directory_structure": getattr(result, 'directory_structure', {}),
            }
            
            return structure_info
            
        except Exception as e:
            if self.config.verbose:
                self.console.print(f"[yellow]Warning: Could not analyze structure with repomix: {e}[/yellow]")
            
            return {
                "total_files": 0,
                "total_size": 0,
                "file_types": {},
                "directory_structure": {},
            }
        
        finally:
            # Clean up temporary file
            try:
                Path(repomix_config.output.file_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def validate_repomix_config(self, config: RepomixConfig) -> List[str]:
        """Validate repomix configuration and return any warnings."""
        
        warnings = []
        
        # Check if include patterns are valid
        if config.include:
            for pattern in config.include:
                file_path = self.repo_path / pattern
                if not file_path.exists():
                    warnings.append(f"Included file does not exist: {pattern}")
        
        # Check if output path is writable
        try:
            output_path = Path(config.output.file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Try to create a test file
            test_file = output_path.parent / f".repox_test_{output_path.name}"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            warnings.append(f"Output path may not be writable: {e}")
        
        # Check for conflicting patterns
        if config.ignore.custom_patterns:
            for pattern in config.ignore.custom_patterns:
                if pattern in config.include:
                    warnings.append(f"Pattern appears in both include and exclude: {pattern}")
        
        return warnings