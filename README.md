# Repox - AI-Powered Code Context Management Assistant

Repox is an intelligent assistant that helps you interact with code repositories using AI. It analyzes your questions, selects relevant code context using repomix, and provides accurate answers about your codebase.

## Features

- **Smart Context Selection**: Uses AI to determine which files are relevant to your question
- **Efficient Processing**: Filters large repositories to include only necessary context
- **Multi-Model Architecture**: Combines strong and weak AI models for optimal performance
- **Repomix Integration**: Leverages repomix for efficient code packaging
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
```

## How It Works

Repox uses a three-step process:

1. **Analysis**: A strong AI model analyzes your question and the repository structure to determine which files are relevant
2. **Context Building**: A weak AI model processes the selected files to create optimal context
3. **Answer Generation**: A strong AI model generates the final answer using the constructed context

## Configuration

Create a `.repox.json` file in your project root:

```json
{
  "strong_model": "gpt-4",
  "weak_model": "gpt-3.5-turbo",
  "max_file_size": 100000,
  "max_context_size": 50000,
  "exclude_patterns": [
    "*.log",
    "node_modules/**",
    "__pycache__/**"
  ]
}
```

## API Usage

```python
from repox import RepoxAssistant

assistant = RepoxAssistant("/path/to/repo")
answer = assistant.ask("How does the caching system work?")
print(answer)
```

## License

MIT License - see LICENSE file for details.