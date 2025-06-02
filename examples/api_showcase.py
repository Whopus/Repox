#!/usr/bin/env python3
"""
Repox API Showcase - Demonstrating the elegant Python API

This file showcases the new, improved Repox API with examples
of all major functionality.
"""

import os
from pathlib import Path

# Import the elegant Repox API
from repox import Repox, RepoxConfig, ask, find, build_context


def main():
    """Demonstrate Repox API capabilities."""
    
    print("🤖 Repox API Showcase")
    print("=" * 50)
    
    # Example 1: Quick functions for simple use cases
    print("\n1. 📚 Quick Functions (Simplest API)")
    print("-" * 40)
    
    # Quick ask function
    print("# Quick question about the repository")
    print("answer = ask('What is this repository about?')")
    
    # Quick find function  
    print("\n# Quick file search")
    print("files = find('configuration files')")
    
    # Quick context building
    print("\n# Quick context building")
    print("context = build_context(query='main components')")
    
    
    # Example 2: Main Repox class for more control
    print("\n\n2. 🎛️ Main Repox Class (Full Control)")
    print("-" * 40)
    
    # Initialize with default settings
    repox = Repox()
    print(f"Repository: {repox.repo_path}")
    
    # Get repository information
    print("\n# Repository information")
    info = repox.info()
    print(f"Total files: {info.get('total_files', 'N/A')}")
    
    # List processable files
    files = repox.list_files()
    print(f"Processable files: {len(files)}")
    
    
    # Example 3: Configuration management
    print("\n\n3. ⚙️ Configuration Management")
    print("-" * 40)
    
    # Create different configuration presets
    default_config = RepoxConfig.create_default()
    large_repo_config = RepoxConfig.create_for_large_repo()
    dev_config = RepoxConfig.create_for_development()
    
    print("# Configuration presets available:")
    print("- RepoxConfig.create_default()")
    print("- RepoxConfig.create_for_large_repo()")
    print("- RepoxConfig.create_for_development()")
    
    # Custom configuration
    custom_config = RepoxConfig(
        verbose=True,
        max_context_size=100000,
        enable_compression=True
    )
    
    print(f"\n# Custom config valid: {custom_config.is_valid()}")
    missing = custom_config.get_missing_requirements()
    if missing:
        print(f"Missing requirements: {missing}")
    
    
    # Example 4: Method chaining for fluent interface
    print("\n\n4. 🔗 Method Chaining (Fluent Interface)")
    print("-" * 40)
    
    print("# Fluent configuration and usage")
    print("""
repox = (Repox()
         .configure(verbose=True, max_context_size=100000)
         .configure(enable_compression=True))
    """)
    
    # Demonstrate method chaining
    repox_configured = (Repox()
                       .configure(verbose=True)
                       .configure(max_context_size=100000))
    
    print("✅ Method chaining configured successfully")
    
    
    # Example 5: Rich result objects
    print("\n\n5. 📊 Rich Result Objects")
    print("-" * 40)
    
    print("# Results have rich functionality:")
    print("""
# Search results
search_result = repox.find('authentication')
search_result.save('search_results.json')  # Save to file
search_result.to_dict()                    # Convert to dict
search_result.to_json()                    # Convert to JSON

# Context results  
context_result = repox.build_context(query='API endpoints')
context_result.save('api_context.md')     # Save context
context_result.metadata                   # Access metadata

# Answer results
answer_result = repox.ask('How does auth work?')
answer_result.confidence                  # Access confidence
answer_result.files_used                  # See which files were used
    """)
    
    
    # Example 6: Advanced usage patterns
    print("\n\n6. 🚀 Advanced Usage Patterns")
    print("-" * 40)
    
    print("# Custom repository path")
    print("repox = Repox('/path/to/other/repo')")
    
    print("\n# Custom API key and model")
    print("repox = Repox(api_key='sk-...', model='gpt-4-turbo')")
    
    print("\n# Preview mode for file selection")
    print("preview = repox.ask('How does caching work?', preview=True)")
    
    print("\n# Content search in files")
    print("files = repox.find('database models', search_content=True)")
    
    print("\n# Context with focus areas")
    print("""
context = repox.build_context(
    query='authentication system',
    focus_areas=['auth', 'security'],
    compress=True
)
    """)
    
    
    # Example 7: Error handling and validation
    print("\n\n7. 🛡️ Error Handling & Validation")
    print("-" * 40)
    
    print("# Configuration validation")
    try:
        invalid_config = RepoxConfig(max_file_size=-1)
    except ValueError as e:
        print(f"✅ Validation caught error: {e}")
    
    print("\n# Graceful error handling built-in")
    print("# - Missing API keys")
    print("# - Invalid file paths") 
    print("# - Network errors")
    print("# - AI model failures")
    
    
    # Example 8: Integration examples
    print("\n\n8. 🔌 Integration Examples")
    print("-" * 40)
    
    print("# Jupyter notebook integration")
    print("""
import repox
answer = repox.ask("Explain this algorithm")
display(Markdown(answer.answer))
    """)
    
    print("\n# CI/CD pipeline integration")
    print("""
# Generate documentation
context = repox.build_context(query="API documentation")
context.save("docs/api_reference.md")

# Code review assistance  
files = repox.find("recently changed files")
for file in files.files:
    analysis = repox.ask(f"Review {file} for issues")
    """)
    
    print("\n# VS Code extension integration")
    print("""
# Right-click context menu
selected_files = get_selected_files()
context = repox.build_context(files=selected_files)
show_in_panel(context.content)
    """)
    
    
    print("\n\n✨ API Showcase Complete!")
    print("=" * 50)
    print("The new Repox API provides:")
    print("• 🎯 Simple functions for quick tasks")
    print("• 🎛️ Full control when needed")
    print("• 🔗 Fluent method chaining")
    print("• 📊 Rich result objects")
    print("• ⚙️ Flexible configuration")
    print("• 🛡️ Built-in validation")
    print("• 🚀 Advanced features")


if __name__ == "__main__":
    main()