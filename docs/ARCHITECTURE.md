# Repox Architecture

This document describes the architecture and design of Repox, an AI-powered code context management assistant.

## Overview

Repox follows a three-step process to answer questions about codebases:

1. **File Selection**: Use a strong AI model to analyze the question and repository structure to select relevant files
2. **Context Building**: Use repomix to package selected files and a weak AI model to optimize the context
3. **Answer Generation**: Use a strong AI model to generate answers based on the optimized context

## Components

### Core Components

#### `RepoxAssistant`
The main entry point that orchestrates the entire process. It:
- Initializes and validates configuration
- Creates AI model instances
- Coordinates between repository analysis, context building, and answer generation
- Provides high-level API for users

#### `RepositoryAnalyzer`
Analyzes repository structure and manages file selection. It:
- Builds tree representations of repository structure
- Identifies processable files based on size and exclusion patterns
- Validates file selections from AI models
- Provides repository statistics and summaries

#### `ContextBuilder`
Manages context creation and optimization. It:
- Uses strong AI to select relevant files based on questions
- Integrates with repomix to package selected files
- Uses weak AI to optimize context for better processing
- Handles fallback context building when repomix fails

### Configuration System

#### `RepoxConfig`
Centralized configuration management that:
- Loads settings from files and environment variables
- Provides sensible defaults
- Supports hierarchical configuration (env > file > defaults)
- Validates configuration parameters

### AI Model Abstraction

#### `AIModel` (Abstract Base Class)
Defines the interface for AI models with:
- Async and sync generation methods
- Standardized message format
- Usage tracking capabilities

#### `OpenAIModel`
OpenAI-specific implementation that:
- Handles OpenAI API communication
- Manages authentication and base URL configuration
- Provides error handling and response parsing

#### `ModelFactory`
Factory pattern for creating AI model instances:
- Supports multiple AI providers (currently OpenAI)
- Simplifies model instantiation
- Enables easy extension for new providers

### Data Models

#### Request/Response Models
Structured data models for different processing stages:
- `FileSelectionRequest/Response`: File selection analysis
- `ContextBuildingRequest/Response`: Context optimization
- `AnswerGenerationRequest/Response`: Final answer generation

## Design Principles

### Modularity
Each component has a single responsibility and well-defined interfaces, making the system easy to understand, test, and extend.

### Configurability
Extensive configuration options allow users to customize behavior for different use cases and environments.

### Error Handling
Robust error handling with fallback mechanisms ensures the system continues to work even when individual components fail.

### Performance
- Efficient file filtering to avoid processing unnecessary files
- Context size optimization to reduce AI model costs
- Lazy loading and caching where appropriate

### Security
- Built-in exclusion patterns for sensitive files
- API key management through environment variables
- Input validation and sanitization

## Data Flow

```
User Question
     ↓
Repository Analysis
     ↓
File Selection (Strong AI)
     ↓
File Validation
     ↓
Context Building (Repomix)
     ↓
Context Optimization (Weak AI)
     ↓
Answer Generation (Strong AI)
     ↓
Final Answer
```

## Extension Points

### Adding New AI Providers
1. Implement the `AIModel` interface
2. Add provider-specific configuration options
3. Update `ModelFactory` to support the new provider

### Custom Context Builders
The `ContextBuilder` can be extended or replaced to support:
- Different file packaging strategies
- Custom optimization algorithms
- Integration with other code analysis tools

### Repository Analyzers
The `RepositoryAnalyzer` can be extended to support:
- Different version control systems
- Custom file type detection
- Advanced repository metrics

## Testing Strategy

### Unit Tests
- Individual component testing with mocks
- Configuration validation
- Error handling scenarios

### Integration Tests
- End-to-end workflows with mock AI responses
- File system operations
- Configuration loading

### Mock AI Models
Custom mock implementations for testing without API calls:
- Predictable responses for test scenarios
- Usage tracking for verification
- Error simulation capabilities

## Performance Considerations

### File Processing
- Early filtering to avoid processing large or irrelevant files
- Efficient directory traversal with skip patterns
- Memory-conscious file reading

### AI Model Usage
- Strategic use of strong vs. weak models to balance cost and quality
- Context size optimization to reduce token usage
- Caching of repository analysis results

### Scalability
- Designed to handle repositories of various sizes
- Configurable limits to prevent resource exhaustion
- Efficient data structures for large file lists

## Security Considerations

### API Key Management
- Environment variable-based configuration
- No storage of sensitive data in configuration files
- Secure transmission to AI providers

### File Access
- Respect for gitignore and custom exclusion patterns
- Protection against path traversal attacks
- Safe handling of binary and large files

### Data Privacy
- Local processing where possible
- Minimal data sent to AI providers
- User control over what files are included