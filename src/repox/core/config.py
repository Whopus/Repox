"""Configuration management for Repox."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, field_validator, model_validator


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
    
    @field_validator('max_file_size')
    @classmethod
    def validate_max_file_size(cls, v):
        """Validate max file size is reasonable."""
        if v <= 0:
            raise ValueError("max_file_size must be positive")
        if v > 10_000_000:  # 10MB
            raise ValueError("max_file_size too large (max 10MB)")
        return v
    
    @field_validator('max_context_size')
    @classmethod
    def validate_max_context_size(cls, v):
        """Validate max context size is reasonable."""
        if v <= 0:
            raise ValueError("max_context_size must be positive")
        if v > 1_000_000:  # 1M tokens
            raise ValueError("max_context_size too large (max 1M tokens)")
        return v
    
    @field_validator('location_confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        """Validate confidence threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("location_confidence_threshold must be between 0 and 1")
        return v
    
    @field_validator('openai_base_url')
    @classmethod
    def validate_openai_base_url(cls, v):
        """Validate OpenAI base URL format."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("openai_base_url must start with http:// or https://")
        return v
    
    @model_validator(mode='after')
    def validate_model_config(self):
        """Validate model configuration consistency."""
        api_key = self.openai_api_key
        strong_model = self.strong_model
        weak_model = self.weak_model
        
        # Check if OpenAI models are used without API key
        openai_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
        if (strong_model in openai_models or weak_model in openai_models) and not api_key:
            # Only warn, don't fail - API key might be set later
            pass
        
        return self
    
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
    
    def update(self, **kwargs) -> "RepoxConfig":
        """Update configuration with new values and return a new instance."""
        config_data = self.model_dump()
        config_data.update(kwargs)
        return RepoxConfig(**config_data)
    
    def is_valid(self) -> bool:
        """Check if configuration is valid for operation."""
        try:
            # Check if we have an API key for OpenAI models
            openai_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            if (self.strong_model in openai_models or self.weak_model in openai_models):
                return bool(self.openai_api_key)
            return True
        except Exception:
            return False
    
    def get_missing_requirements(self) -> List[str]:
        """Get list of missing requirements for operation."""
        missing = []
        
        # Check API key for OpenAI models
        openai_models = ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
        if (self.strong_model in openai_models or self.weak_model in openai_models):
            if not self.openai_api_key:
                missing.append("OPENAI_API_KEY environment variable")
        
        return missing
    
    def to_dict(self, exclude_secrets: bool = True) -> Dict[str, Any]:
        """Convert to dictionary, optionally excluding secrets."""
        exclude_fields = {"openai_api_key"} if exclude_secrets else set()
        return self.model_dump(exclude=exclude_fields)
    
    def to_json(self, exclude_secrets: bool = True, indent: int = 2) -> str:
        """Convert to JSON string, optionally excluding secrets."""
        return json.dumps(self.to_dict(exclude_secrets), indent=indent)
    
    @classmethod
    def create_default(cls) -> "RepoxConfig":
        """Create a default configuration with sensible defaults."""
        return cls()
    
    @classmethod
    def create_for_large_repo(cls) -> "RepoxConfig":
        """Create configuration optimized for large repositories."""
        return cls(
            max_file_size=50000,  # Smaller files only
            max_context_size=30000,  # Smaller context
            max_files_per_request=10,  # Fewer files
            enable_compression=True,  # Enable compression
            location_confidence_threshold=0.8,  # Higher confidence
        )
    
    @classmethod
    def create_for_development(cls) -> "RepoxConfig":
        """Create configuration optimized for development."""
        return cls(
            verbose=True,  # Verbose output
            max_file_size=200000,  # Larger files OK
            max_context_size=100000,  # Larger context
            preserve_file_structure=True,  # Keep structure
            include_file_metadata=True,  # Include metadata
        )