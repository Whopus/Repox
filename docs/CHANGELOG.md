# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-06-02

### Added
- Initial release of Repox
- AI-powered code context management assistant
- Three-step process: file selection, context building, answer generation
- Support for OpenAI models (strong and weak model configuration)
- Repository analysis and file selection
- Integration with repomix for code packaging
- Command-line interface with comprehensive options
- Python API for programmatic usage
- Configuration management with environment variables and files
- Comprehensive test suite with 35 tests
- Documentation and examples
- Interactive demo script

### Features
- **Repository Analysis**: Analyze repository structure, file types, and sizes
- **Smart File Selection**: AI-powered selection of relevant files based on questions
- **Context Building**: Optimized context creation using repomix and AI
- **Answer Generation**: High-quality answers using strong AI models
- **Configuration System**: Flexible configuration via files and environment variables
- **CLI Interface**: Full-featured command-line interface
- **Python API**: Programmatic access to all functionality
- **File Filtering**: Intelligent exclusion of irrelevant files
- **Preview Mode**: Preview file selection without generating answers
- **Verbose Logging**: Detailed logging for debugging and monitoring

### Technical Details
- Built with Python 3.8+ support
- Uses OpenAI API for AI model access
- Integrates with repomix for code packaging
- Comprehensive error handling and validation
- Modular architecture with clear separation of concerns
- Extensive test coverage with mock AI models
- Type hints throughout the codebase
- Rich CLI output with tables and formatting

### Dependencies
- repomix >= 0.1.0
- openai >= 1.0.0
- click >= 8.0.0
- pydantic >= 2.0.0
- rich >= 13.0.0
- pathspec >= 0.11.0