# Repox - AI-Powered Code Context Management Assistant

Repox is an intelligent assistant that helps you interact with code repositories using AI. It analyzes your questions, selects relevant code context using repomix, and provides accurate answers about your codebase.

## Features

- **Smart Context Selection**: Uses AI to determine which files are relevant to your question
- **File Location**: Locate files and content based on natural language queries
- **Context Building**: Create optimized context from repository files with intelligent filtering
- **Enhanced Filtering**: Advanced filtering rules with smart pattern matching
- **Efficient Processing**: Filters large repositories to include only necessary context
- **Multi-Model Architecture**: Combines strong and weak AI models for optimal performance
- **Enhanced Repomix Integration**: Leverages repomix with advanced configuration and compression
- **Modular Architecture**: Highly cohesive, loosely coupled design for extensibility
- **Configurable**: Supports multiple AI providers and models

## Quick Start

### Installation

```bash
pip install repox
```

### Configuration

Set up your environment variables:

```bash
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Optional
export REPOX_STRONG_MODEL="gpt-4"
export REPOX_WEAK_MODEL="gpt-3.5-turbo"
```

### Usage

```bash
# Ask a question about your codebase
repox "How does the authentication system work?"

# Specify a different repository
repox --repo /path/to/repo "What are the main components?"

# Use verbose output
repox --verbose "Explain the database schema"

# Locate files based on a query
repox locate "authentication functions"

# Build context from specific files
repox context --files "src/auth.py,src/login.py"

# Build context based on a query with focus areas
repox context --query "authentication system" --focus "auth,security"

# Save context to a file with compression
repox context --query "API endpoints" --compression --output api_context.md
```

## How It Works

Repox uses an enhanced multi-step process:

1. **Repository Analysis**: Smart filtering analyzes the repository structure and identifies processable files
2. **File Location**: AI-powered location system finds files relevant to your query using multiple strategies
3. **Context Building**: Enhanced repomix integration creates optimized context with compression and focus areas
4. **Context Optimization**: Weak AI model refines the context for better processing
5. **Answer Generation**: Strong AI model generates the final answer using the optimized context

## Commands

### Main Command
- `repox "question"` - Ask a question about your codebase
- `repox --summary` - Show repository summary
- `repox --list-files` - List processable files
- `repox --preview "question"` - Preview file selection without generating answer

### File Location
- `repox locate "query"` - Locate files and content based on a query
- `repox locate "query" --format json` - Output results in JSON format
- `repox locate "query" --max-results 5` - Limit number of results

### Context Building
- `repox context --files "file1,file2"` - Build context from specific files
- `repox context --query "query"` - Build context based on a query
- `repox context --focus "area1,area2"` - Focus on specific areas (tests, docs, config)
- `repox context --compression` - Enable compression to reduce size
- `repox context --output file.md` - Save context to file

## Configuration

Create a `.repox.json` file in your project root:

```json
{
  "strong_model": "gpt-4",
  "weak_model": "gpt-3.5-turbo",
  "max_file_size": 100000,
  "max_context_size": 50000,
  "max_files_per_request": 20,
  "location_confidence_threshold": 0.7,
  "max_content_search_files": 50,
  "enable_compression": false,
  "preserve_file_structure": true,
  "include_file_metadata": true,
  "exclude_patterns": [
    "*.log",
    "node_modules/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "*.pyc",
    "*.so",
    "*.dll"
  ],
  "skip_large_dirs": [
    "node_modules",
    "__pycache__",
    ".git",
    "build",
    "dist"
  ],
  "large_dir_threshold": 100
}
```

## API Usage

```python
from repox import RepoxAssistant, FileLocator, RepomixIntegration
from repox.models import ModelFactory
from repox.config import RepoxConfig

# Basic usage
assistant = RepoxAssistant("/path/to/repo")
answer = assistant.ask("How does the caching system work?")
print(answer)

# Advanced usage with custom configuration
config = RepoxConfig()
config.verbose = True
config.max_context_size = 100000

assistant = RepoxAssistant("/path/to/repo", config=config)

# File location
model = ModelFactory.create_openai_model("gpt-4", "your-api-key")
locator = FileLocator("/path/to/repo", config, model)
result = locator.locate_files("authentication functions")

# Context building
repomix_integration = RepomixIntegration("/path/to/repo", config)
context = repomix_integration.build_context(
    selected_files=["src/auth.py", "src/login.py"],
    focus_areas=["auth", "security"],
    compression_enabled=True
)
```

## Architecture

Repox follows a modular, highly cohesive, and loosely coupled architecture:

- **`assistant.py`**: Main orchestrator that coordinates all components
- **`locator.py`**: AI-powered file location with content search
- **`filter.py`**: Smart filtering with pattern matching and relevance scoring
- **`context.py`**: Context building and optimization
- **`repomix_integration.py`**: Enhanced repomix integration with advanced features
- **`repository.py`**: Repository analysis and file management
- **`models.py`**: AI model interfaces and abstractions
- **`config.py`**: Configuration management with environment variable support
- **`cli.py`**: Command-line interface with subcommands

## License

MIT License - see LICENSE file for details.