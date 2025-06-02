# 🤖 Repox - AI-Powered Code Assistant

> **Intelligent code analysis and Q&A for your repositories**

Repox transforms how you interact with codebases by providing AI-powered insights, smart file discovery, and intelligent context building. Ask questions in natural language and get precise answers about your code.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)


## ✨ Features

- **🧠 Smart Q&A**: Ask questions about your codebase in natural language
- **🔍 Intelligent File Discovery**: Find relevant files using AI-powered search
- **📋 Context Building**: Create optimized documentation and analysis contexts
- **⚡ Fast & Efficient**: Smart filtering and caching for large repositories
- **🎯 Multiple Output Formats**: JSON, Markdown, and rich terminal output
- **🔧 Highly Configurable**: Customize AI models, filtering rules, and behavior
- **🏗️ Modular Architecture**: Extensible design for custom integrations

## 🚀 Quick Start

### Installation

```bash
pip install repox
```

### Setup

1. **Set your OpenAI API key:**
   ```bash
    # Required
    export OPENAI_API_KEY="your-api-key"

    # Optional
    export OPENAI_BASE_URL="https://api.openai.com/v1"
    export REPOX_STRONG_MODEL="claude-sonnet-4-20250514"
    export REPOX_WEAK_MODEL="gpt-4.1-mini"
    export REPOX_VERBOSE="true"
   ```

2. **Initialize configuration (optional):**
   ```bash
   cd your-project
   repox init
   ```

3. **Start asking questions:**
   ```bash
   repox ask "How does authentication work in this project?"
   ```

## 💡 Usage Examples

### Ask Questions About Your Code

```bash
# Basic question
repox ask "What are the main components of this system?"

# Preview file selection before generating answer
repox ask "How does the database layer work?" --preview

# Get answer in different formats
repox ask "Explain the API structure" --format markdown
repox ask "What are the security measures?" --format json
```

### Find Files and Content

```bash
# Find files by description
repox find "authentication functions"

# Search with content analysis (slower but more accurate)
repox find "database models" --content


# Limit results and format output
repox find "test files" --limit 5 --format json


### Build Documentation Context


```bash
# Build context from specific files
repox build --files "src/auth.py,src/models.py"

# Auto-select files based on query
repox build --query "authentication system"

# Focus on specific areas with compression
repox build --query "API endpoints" --focus "api,routes" --compress

# Save to file
repox build --query "database schema" --output docs/database.md
```

### Repository Information

```bash
# Show repository summary
repox info --summary

# List all processable files
repox info --files

# Detailed statistics
repox info --stats
```

## 🏗️ Architecture

Repox follows a clean, modular architecture designed for extensibility and maintainability:

```
repox/
├── cli.py              # Command-line interface
├── assistant.py        # Main orchestrator
├── locator.py          # AI-powered file discovery
├── context.py          # Context building and optimization
├── repomix_integration.py  # Enhanced repomix integration
├── repository.py       # Repository analysis
├── filter.py           # Smart filtering system
├── models.py           # AI model abstractions
└── config.py           # Configuration management
```

### Design Principles

- **🎯 Simplicity First**: Common tasks should be simple, complex tasks possible
- **🔧 Composable**: Features work well together and can be combined
- **⚡ Performance**: Optimized for speed with smart caching and filtering
- **🛡️ Reliable**: Graceful error handling and fallback mechanisms
- **📈 Extensible**: Easy to add new features and integrations

## ⚙️ Configuration

### Configuration File

Create `.repox.json` in your project root:

```json
{
  "strong_model": "gpt-4",
  "weak_model": "gpt-3.5-turbo",
  "max_file_size": 100000,
  "max_context_size": 50000,
  "location_confidence_threshold": 0.7,
  "enable_compression": false,
  "exclude_patterns": [
    "*.log", "node_modules/**", "__pycache__/**",
    "build/**", "dist/**", "*.pyc"
  ],
  "skip_large_dirs": [
    "node_modules", "__pycache__", ".git", "build", "dist"
  ]
}
```

## 🔧 API Usage

### Basic Usage

```python
from repox import RepoxAssistant, FileLocator, RepomixIntegration
from repox.models import ModelFactory
from repox.config import RepoxConfig

# Initialize with default configuration
assistant = RepoxAssistant("/path/to/repo")

# Ask a question
answer = assistant.ask("How does the authentication system work?")
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

### Advanced Usage

```python
from repox import RepoxAssistant, FileLocator, RepoxConfig
from repox.models import ModelFactory

# Custom configuration
config = RepoxConfig()
config.verbose = True
config.max_context_size = 100000

# Initialize assistant
assistant = RepoxAssistant("/path/to/repo", config=config)

# File discovery
model = ModelFactory.create_openai_model("gpt-4", "your-api-key")
locator = FileLocator("/path/to/repo", config, model)
result = locator.locate_files("authentication functions")

# Context building
context = assistant.build_context_with_repomix(result.located_files)
```

### Custom AI Models

```python
from repox.models import AIModel

class CustomModel(AIModel):
    def generate_sync(self, messages, **kwargs):
        # Your custom implementation
        pass

# Use with Repox
assistant = RepoxAssistant("/path/to/repo")
assistant.strong_model = CustomModel()
```

## 🎨 Output Formats

### Terminal (Default)
Rich, colorized output with tables, panels, and progress indicators.

### JSON
Structured data perfect for automation and integration:
```json
{
  "question": "How does authentication work?",
  "answer": "The authentication system uses...",
  "files": ["src/auth.py", "src/models/user.py"],
  "confidence": 0.95
}
```

### Markdown
Human-readable format ideal for documentation:
```markdown
# Question
How does authentication work?

# Answer
The authentication system uses JWT tokens...
```

## 🔍 Smart Filtering

Repox automatically excludes irrelevant files to improve performance and accuracy:

- **Build artifacts**: `build/`, `dist/`, `*.pyc`, `*.so`
- **Dependencies**: `node_modules/`, `__pycache__/`, `.venv/`
- **Version control**: `.git/`, `.svn/`, `.hg/`
- **Logs and temp files**: `*.log`, `*.tmp`, `cache/`
- **Media files**: `*.jpg`, `*.png`, `*.mp4`, `*.pdf`
- **Security sensitive**: `.env`, `*.key`, `*.pem`

## 🚀 Performance Tips

1. **Use `.repox.json`** to customize filtering for your project
2. **Set appropriate file size limits** to avoid processing huge files
3. **Use `--preview`** to check file selection before full analysis
4. **Enable compression** for large contexts with `--compress`
5. **Focus on specific areas** with `--focus` to reduce noise

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Whopus/Repox.git
cd Repox

# Install in development mode
pip install -e .

# Run tests
pytest

# Install pre-commit hooks
pre-commit install
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of the excellent [repomix](https://github.com/andersonby/python-repomix) library
- Inspired by the need for better code understanding tools
- Thanks to the open-source community for continuous inspiration

---

**Made with ❤️ by the Repox team**

*Transform your codebase interaction with AI-powered intelligence.*