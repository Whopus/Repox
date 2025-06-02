"""Basic usage examples for Repox."""

import os
from pathlib import Path

from repox import RepoxAssistant, RepoxConfig


def basic_example():
    """Basic usage example."""
    print("=== Basic Repox Usage ===")
    
    # Ensure API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Initialize assistant with current directory
    assistant = RepoxAssistant(".")
    
    # Ask a question about the codebase
    question = "What is the main purpose of this project?"
    print(f"Question: {question}")
    
    try:
        answer = assistant.ask(question)
        print(f"Answer: {answer}")
    except Exception as e:
        print(f"Error: {e}")


def custom_config_example():
    """Example with custom configuration."""
    print("\n=== Custom Configuration Example ===")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create custom configuration
    config = RepoxConfig()
    config.strong_model = "gpt-4"
    config.weak_model = "gpt-3.5-turbo"
    config.max_file_size = 50000  # Smaller file size limit
    config.verbose = True  # Enable verbose output
    
    # Add custom exclude patterns
    config.exclude_patterns.extend([
        "*.example",
        "temp/**",
    ])
    
    # Initialize assistant with custom config
    assistant = RepoxAssistant(".", config)
    
    # Get repository summary
    summary = assistant.get_repository_summary()
    print(f"Repository summary: {summary}")


def preview_example():
    """Example of previewing file selection."""
    print("\n=== File Selection Preview Example ===")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    assistant = RepoxAssistant(".")
    
    # Preview which files would be selected for a question
    question = "How is the configuration system implemented?"
    preview = assistant.preview_file_selection(question)
    
    print(f"Question: {question}")
    print(f"Selected files: {preview['selected_files']}")
    print(f"Valid files: {preview['valid_files']}")
    print(f"Invalid files: {preview['invalid_files']}")
    print(f"Reasoning: {preview['reasoning']}")


def repository_analysis_example():
    """Example of repository analysis features."""
    print("\n=== Repository Analysis Example ===")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    assistant = RepoxAssistant(".")
    
    # Get list of processable files
    files = assistant.list_processable_files()
    print(f"Processable files ({len(files)}):")
    for file_path in files[:10]:  # Show first 10
        print(f"  - {file_path}")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more")
    
    # Get detailed repository summary
    summary = assistant.get_repository_summary()
    print(f"\nRepository Summary:")
    print(f"  Total files: {summary['total_files']}")
    print(f"  Total size: {summary['total_size']:,} bytes")
    print(f"  File types: {dict(list(summary['file_types'].items())[:5])}")


if __name__ == "__main__":
    basic_example()
    custom_config_example()
    preview_example()
    repository_analysis_example()