# 🤖 Repox v0.2.0 - AI-Powered Code Assistant

> **Intelligent code analysis and Q&A for your repositories with hierarchical filtering and elegant PyTorch-like API**

Repox transforms how you interact with codebases by providing AI-powered insights, smart file discovery, and intelligent context building. Ask questions in natural language and get precise answers about your code with minimal token usage through advanced hierarchical filtering.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Key Features

### 🧠 **Intelligent Analysis**
- **Smart Q&A**: Ask questions about your codebase in natural language
- **AI-Powered File Discovery**: Find relevant files using advanced semantic search
- **Context-Aware Responses**: Get precise answers with relevant code context

### ⚡ **Performance & Efficiency**
- **Hierarchical Filtering**: 60-80% token reduction through multi-stage filtering
- **Smart Caching**: Efficient processing for large repositories
- **Optimized Context Building**: Minimal token usage with maximum relevance

### 🎯 **Elegant API Design**
- **PyTorch-like Interface**: Clean, intuitive API inspired by modern ML libraries
- **Multiple Repository Support**: Switch between repositories dynamically
- **Flexible Output Formats**: JSON, Markdown, and rich terminal output

### 🏗️ **Architecture & Extensibility**
- **Modular Design**: Highly cohesive, loosely coupled components
- **Extensible Framework**: Easy to customize and extend
- **Professional Structure**: Clean separation of concerns

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

3. **Start using Repox:**
   ```bash
   # CLI usage
   repox ask "How does authentication work in this project?"
   
   # Python API usage
   python -c "import repox; repox.configure(); print(repox.ask('What does this code do?'))"
   ```

## 💡 Usage Examples

### 🎯 **Elegant Python API** (PyTorch-like)

```python
import repox

# Configure once (global state)
repox.configure(
    repo_path="/path/to/your/repo",
    model="gpt-4",
    verbose=True
)

# Ask questions
answer = repox.ask("How does authentication work?")
print(answer.content)

# Find relevant files
files = repox.find("database models")
print(f"Found {len(files.files)} relevant files")

# Build context
context = repox.build(query="API endpoints")
print(f"Context: {len(context.content)} characters")

# Get repository info
info = repox.info()
print(f"Repository: {info['name']}")

# Work with multiple repositories
answer = repox.ask("How does auth work?", repo_path="/other/repo")

# Convenience functions
files = repox.locate("authentication logic")  # alias for find
context = repox.context("API design")         # alias for build

# Reset global configuration
repox.reset()
```

### 🖥️ **Command Line Interface**

```bash
# Initialize configuration
repox init

# Get repository information
repox info

# Ask questions about your code
repox ask "What is the main purpose of this repository?"
repox ask "How does the CLI system work?" --verbose
repox ask "Explain the hierarchical filtering" --format markdown

# Find files and content
repox find "authentication functions"
repox find "CLI commands" --content
repox find "test files" --limit 5

# Locate specific files
repox locate "configuration files"
repox locate "main entry point" --verbose

# Build context from files
repox build --files "README.md,src/repox/cli/main.py"
repox build --query "CLI implementation"

# Build optimized context
repox context --query "how does the assistant work"

# Focus on specific areas with compression
repox build --query "API endpoints" --focus "api,routes" --compress
```

### 📊 **Example Output**

When you run `repox ask "What is the main purpose of this repository?"`, you get:

```
🤖 Generating answer...
╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── 🤖 Repox Assistant ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ Question: What is the main purpose of this repository?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Based on my analysis of the code context, **Repox is an AI-powered code context management assistant designed to help developers understand and analyze codebases through natural language queries**.

## Core Purpose

The main purpose of this repository is to provide an intelligent tool that can:

1. **Answer questions about codebases** - Users can ask natural language questions like "How does authentication work in this project?" and get AI-generated answers based on the actual code
2. **Intelligently locate relevant files** - Uses AI to find files related to specific queries or topics  
3. **Build optimized context** - Creates well-structured summaries of repository content for AI analysis
4. **Analyze repository structure** - Provides insights into codebase organization, file types, and statistics
```

When you run `repox info`, you see:

```
                                                                        📊 Repository Summary
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Metric            ┃ Value                                                                                                                                         ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Total Files       │ 57                                                                                                                                            │
│ Processable Files │ 57                                                                                                                                            │
│ Total Size        │ 333303                                                                                                                                        │
│ Total Size Mb     │ 0.32 MB                                                                                                                                       │
│ File Types        │ .py: 35, .md: 10, .txt: 6, .in: 1, (no extension): 4                                                                                         │
│ Languages         │ Python, Markdown, Text, TOML                                                                                                                  │
│ Largest Files     │ src/repox/cli/main.py (28.6 KB), src/repox/processing/context.py (17.8 KB)                                                                   │
│ Repository Path   │ /workspace/Repox                                                                                                                              │
└───────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

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

Repox v0.2.0 features a completely redesigned modular architecture:

```
repox/
├── api/                    # Public APIs
│   ├── elegant.py         # PyTorch-like elegant API
│   └── classic.py         # Traditional class-based API
├── core/                   # Core functionality
│   ├── assistant.py       # Main orchestrator
│   └── config.py          # Configuration management
├── processing/             # Data processing
│   ├── context.py         # Context building
│   ├── locator.py         # AI-powered file discovery
│   ├── filter.py          # Smart filtering
│   └── hierarchical_filter.py  # Advanced hierarchical filtering
├── repository/             # Repository analysis
│   ├── analyzer.py        # Repository structure analysis
│   └── repomix_integration.py  # Enhanced repomix integration
├── cli/                    # Command line interface
│   ├── main.py           # CLI commands
│   └── commands.py       # Modular CLI structure
└── utils/                  # Utilities
    └── models.py          # AI model abstractions
```

### 🎯 **Key Architectural Improvements**

- **Hierarchical Filtering**: Multi-stage filtering reduces token usage by 60-80%
- **Elegant API**: PyTorch-inspired interface with global state management
- **Modular Design**: High cohesion, loose coupling between components
- **Performance Optimization**: Smart caching and efficient processing
- **Extensible Framework**: Easy to add new features and integrations

### 🔧 **Design Principles**

- **🎯 Simplicity First**: Common tasks should be simple, complex tasks possible
- **🔧 Composable**: Features work well together and can be combined
- **⚡ Performance**: Optimized for speed with smart caching and filtering
- **🛡️ Reliable**: Graceful error handling and fallback mechanisms
- **📈 Extensible**: Easy to add new features and integrations
- **🧩 Modular**: Clean separation of concerns with well-defined interfaces

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

## 🆕 What's New in v0.2.0

### 🎯 **Hierarchical Filtering System**
- **Multi-stage filtering**: Filename → Content → AI analysis
- **60-80% token reduction** compared to previous versions
- **Smart relevance scoring** with confidence thresholds
- **Optimized context building** for large repositories

### 🔥 **Elegant PyTorch-like API**
- **Global state management**: Configure once, use everywhere
- **Intuitive interface**: `repox.ask()`, `repox.find()`, `repox.build()`
- **Multiple repository support**: Switch between repos dynamically
- **Convenience functions**: `repox.locate()`, `repox.context()`

### 🏗️ **Modular Architecture**
- **Clean separation of concerns**: api/, core/, processing/, repository/
- **High cohesion, loose coupling**: Easy to extend and maintain
- **Professional structure**: Industry-standard organization

### ⚡ **Performance Improvements**
- **Optimized assistant workflow**: 3-step process instead of 5
- **Smart caching**: Reduced redundant operations
- **Efficient file processing**: Better memory usage

## 🔧 API Reference

### 🎯 **Elegant API** (Recommended)

```python
import repox

# Configure globally (PyTorch-style)
repox.configure(
    repo_path="/path/to/repo",
    model="gpt-4",
    verbose=True
)

# Core functions
answer = repox.ask("How does auth work?")
files = repox.find("database models") 
context = repox.build(query="API design")
info = repox.info()

# Convenience aliases
files = repox.locate("auth logic")      # alias for find()
context = repox.context("API design")  # alias for build()

# Multi-repository support
answer = repox.ask("How does this work?", repo_path="/other/repo")

# Reset global state
repox.reset()
```

### 🏛️ **Classic API** (Advanced)

```python
from repox import RepoxAssistant, RepoxConfig

# Custom configuration
config = RepoxConfig(
    strong_model="gpt-4",
    weak_model="gpt-3.5-turbo",
    verbose=True,
    max_context_size=100000
)

# Initialize assistant
assistant = RepoxAssistant("/path/to/repo", config=config)

# Use assistant methods
answer = assistant.ask("How does authentication work?")
files = assistant.find("database models")
context = assistant.build_context("API endpoints")
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