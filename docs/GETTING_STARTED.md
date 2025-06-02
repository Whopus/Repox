# Getting Started with Repox

This guide will help you get started with Repox, an AI-powered code context management assistant.

## Installation

### From Source

1. Clone the repository:
```bash
git clone <repository-url>
cd repox
```

2. Install dependencies:
```bash
pip install -e .
```

### Using pip (when published)

```bash
pip install repox
```

## Configuration

### Environment Variables

Set the following environment variables:

```bash
# Required
export OPENAI_API_KEY="your-openai-api-key"

# Optional
export OPENAI_BASE_URL="https://api.openai.com/v1"  # Custom API endpoint
export REPOX_STRONG_MODEL="gpt-4"                   # Strong model for analysis
export REPOX_WEAK_MODEL="gpt-3.5-turbo"            # Weak model for context building
```

### Configuration File

Create a `.repox.json` file in your project root:

```json
{
  "strong_model": "gpt-4",
  "weak_model": "gpt-3.5-turbo",
  "max_file_size": 100000,
  "max_context_size": 50000,
  "max_files_per_request": 20,
  "exclude_patterns": [
    "*.log",
    "*.tmp",
    "node_modules/**",
    "__pycache__/**"
  ],
  "verbose": false
}
```

## Quick Start

### Command Line Usage

1. **Ask a question about your codebase:**
```bash
repox "How does authentication work in this project?"
```

2. **Get repository summary:**
```bash
repox --summary
```

3. **List processable files:**
```bash
repox --list-files
```

4. **Preview file selection:**
```bash
repox --preview "Explain the database schema"
```

5. **Initialize configuration:**
```bash
repox --init
```

### Python API Usage

```python
from repox import RepoxAssistant

# Initialize assistant
assistant = RepoxAssistant(".")

# Ask a question
answer = assistant.ask("What is the main purpose of this project?")
print(answer)

# Get repository summary
summary = assistant.get_repository_summary()
print(f"Total files: {summary['total_files']}")

# Preview file selection
preview = assistant.preview_file_selection("How is error handling implemented?")
print(f"Selected files: {preview['valid_files']}")
```

## Examples

### Basic Questions

- "What is the main purpose of this project?"
- "How is the project structured?"
- "What dependencies does this project have?"
- "How does error handling work?"
- "What testing framework is used?"

### Architecture Questions

- "Explain the overall architecture"
- "What design patterns are used?"
- "How are the components connected?"
- "What is the data flow?"

### Implementation Questions

- "How does authentication work?"
- "How is the database accessed?"
- "What is the API structure?"
- "How are configurations managed?"

## Advanced Usage

### Custom Configuration

```python
from repox import RepoxAssistant, RepoxConfig

# Create custom configuration
config = RepoxConfig()
config.strong_model = "gpt-4-turbo"
config.weak_model = "gpt-3.5-turbo-16k"
config.max_file_size = 200000
config.verbose = True

# Add custom exclude patterns
config.exclude_patterns.extend([
    "*.example",
    "temp/**",
    "build/**"
])

# Initialize with custom config
assistant = RepoxAssistant(".", config)
```

### Repository Analysis

```python
# Get detailed repository information
summary = assistant.get_repository_summary()

print(f"Repository: {summary['repository_path']}")
print(f"Total files: {summary['total_files']}")
print(f"Total size: {summary['total_size']:,} bytes")
print(f"File types: {summary['file_types']}")
print(f"Largest files: {summary['largest_files']}")
```

### File Selection Preview

```python
# Preview which files would be selected for a question
preview = assistant.preview_file_selection("How does the API work?")

print(f"Selected files: {preview['valid_files']}")
print(f"Invalid files: {preview['invalid_files']}")
print(f"AI reasoning: {preview['reasoning']}")
```

## Troubleshooting

### Common Issues

1. **API Key Error:**
   - Make sure `OPENAI_API_KEY` is set correctly
   - Verify the API key is valid and has sufficient credits

2. **No Files Found:**
   - Check exclude patterns in configuration
   - Verify repository path is correct
   - Ensure files are not too large (check `max_file_size`)

3. **Context Too Large:**
   - Reduce `max_files_per_request` in configuration
   - Add more specific exclude patterns
   - Reduce `max_context_size`

### Debug Mode

Enable verbose logging:

```bash
repox --verbose "Your question here"
```

Or in Python:

```python
config = RepoxConfig()
config.verbose = True
assistant = RepoxAssistant(".", config)
```

### Configuration Validation

Test your configuration:

```bash
repox --summary  # This will validate configuration and show repository info
```

## Best Practices

1. **Be Specific:** Ask specific questions for better results
2. **Use Exclude Patterns:** Exclude irrelevant files to improve performance
3. **Monitor Token Usage:** Be aware of API costs with large repositories
4. **Iterate:** Refine your questions based on initial results
5. **Preview First:** Use `--preview` to see which files will be analyzed

## Next Steps

- Try the interactive demo: `python examples/demo.py`
- Read the [Architecture Documentation](ARCHITECTURE.md)
- Explore the examples in the `examples/` directory
- Check out the test suite for more usage patterns