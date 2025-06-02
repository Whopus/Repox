"""Configuration management for Repox."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RepoxConfig(BaseModel):
    """Configuration for Repox assistant."""
    
    # AI Model Configuration
    strong_model: str = Field(default="gpt-4", description="Strong AI model for analysis and answers")
    weak_model: str = Field(default="gpt-3.5-turbo", description="Weak AI model for context building")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI API base URL")
    
    # Processing Configuration
    max_file_size: int = Field(default=100000, description="Maximum file size to process (bytes)")
    max_context_size: int = Field(default=50000, description="Maximum context size for AI models")
    max_files_per_request: int = Field(default=20, description="Maximum files to include in context")
    
    # Repository Analysis
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [
            # Version control
            ".git/**", ".svn/**", ".hg/**", ".bzr/**",
            
            # Build artifacts
            "build/**", "dist/**", "out/**", "target/**",
            "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", "*.dylib",
            "*.class", "*.o", "*.obj", "*.exe", "*.bin",
            
            # Dependencies
            "node_modules/**", "__pycache__/**", ".venv/**", "venv/**",
            "vendor/**", "bower_components/**",
            
            # Logs and temporary files
            "*.log", "*.tmp", "*.cache", "*.pid",
            "logs/**", "tmp/**", "temp/**", "cache/**",
            
            # Media files
            "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.ico", "*.svg",
            "*.mp3", "*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv",
            "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx",
            
            # Archives
            "*.zip", "*.tar", "*.gz", "*.rar", "*.7z", "*.bz2",
            
            # Databases
            "*.db", "*.sqlite", "*.sqlite3", "*.mdb",
            
            # Security sensitive
            ".env", ".env.*", "*.key", "*.pem", "*.cert", "*.crt",
            "*.p12", "*.pfx", "*.jks", "*.keystore",
            
            # IDE and editor files
            ".idea/**", ".vscode/**", "*.swp", "*.swo", "*~", "*.bak",
            ".project", ".settings/**", ".classpath", "*.sublime-*",
            
            # OS files
            ".DS_Store", "Thumbs.db", "desktop.ini",
            
            # Package manager files
            "package-lock.json", "yarn.lock", "Pipfile.lock", "poetry.lock",
            
            # Test coverage and reports
            ".coverage", "htmlcov/**", ".pytest_cache/**", ".tox/**",
            "coverage.xml", "*.cover", "*.py,cover",
        ],
        description="Patterns to exclude from analysis"
    )
    
    skip_large_dirs: List[str] = Field(
        default_factory=lambda: [
            "node_modules", "__pycache__", ".git", ".venv", "venv",
            "build", "dist", "target", "out", "bin", "obj",
            "logs", "tmp", "temp", "cache"
        ],
        description="Directory names to skip if they contain too many files"
    )
    
    large_dir_threshold: int = Field(default=100, description="Skip directories with more than this many files")
    
    # File Location Configuration
    location_confidence_threshold: float = Field(default=0.7, description="Minimum confidence for file location")
    max_content_search_files: int = Field(default=50, description="Maximum files to search for content matches")
    
    # Context Building Configuration
    enable_compression: bool = Field(default=False, description="Enable context compression by default")
    preserve_file_structure: bool = Field(default=True, description="Preserve file structure in context")
    include_file_metadata: bool = Field(default=True, description="Include file metadata in context")
    
    # Output Configuration
    verbose: bool = Field(default=False, description="Enable verbose output")
    
    @classmethod
    def load_from_file(cls, config_path: Optional[Path] = None) -> "RepoxConfig":
        """Load configuration from file."""
        if config_path is None:
            config_path = Path.cwd() / ".repox.json"
        
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = json.load(f)
            return cls(**config_data)
        
        return cls()
    
    @classmethod
    def load_from_env(cls) -> "RepoxConfig":
        """Load configuration from environment variables."""
        config_data = {}
        
        # AI Model Configuration
        if api_key := os.getenv("OPENAI_API_KEY"):
            config_data["openai_api_key"] = api_key
        if base_url := os.getenv("OPENAI_BASE_URL"):
            config_data["openai_base_url"] = base_url
        if strong_model := os.getenv("REPOX_STRONG_MODEL"):
            config_data["strong_model"] = strong_model
        if weak_model := os.getenv("REPOX_WEAK_MODEL"):
            config_data["weak_model"] = weak_model
        
        # Processing Configuration
        if max_file_size := os.getenv("REPOX_MAX_FILE_SIZE"):
            config_data["max_file_size"] = int(max_file_size)
        if max_context_size := os.getenv("REPOX_MAX_CONTEXT_SIZE"):
            config_data["max_context_size"] = int(max_context_size)
        if max_files := os.getenv("REPOX_MAX_FILES_PER_REQUEST"):
            config_data["max_files_per_request"] = int(max_files)
        
        # Verbose mode
        if os.getenv("REPOX_VERBOSE", "").lower() in ("true", "1", "yes"):
            config_data["verbose"] = True
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = Path.cwd() / ".repox.json"
        
        with open(config_path, "w") as f:
            json.dump(self.model_dump(exclude={"openai_api_key"}), f, indent=2)
    
    def get_effective_config(self) -> "RepoxConfig":
        """Get effective configuration by merging file and environment settings."""
        # Start with file config
        file_config = self.load_from_file()
        
        # Override with environment variables
        env_config = self.load_from_env()
        
        # Merge configurations (env takes precedence)
        config_data = file_config.model_dump()
        config_data.update({k: v for k, v in env_config.model_dump().items() if v is not None})
        
        return RepoxConfig(**config_data)