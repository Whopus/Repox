"""Tests for context building."""

import json

import pytest

from repox.context import ContextBuilder
from repox.models import FileSelectionResponse


def test_context_builder_init(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test context builder initialization."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    assert builder.repo_path == temp_repo.resolve()
    assert builder.config == test_config
    assert builder.strong_model == mock_strong_model
    assert builder.weak_model == mock_weak_model


def test_select_relevant_files(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test selecting relevant files."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    question = "How does the main function work?"
    repository_structure = "main.py\nutils.py\nconfig.json"
    file_sizes = {"main.py": 100, "utils.py": 200, "config.json": 50}
    
    selection = builder.select_relevant_files(question, repository_structure, file_sizes)
    
    assert isinstance(selection, FileSelectionResponse)
    assert isinstance(selection.selected_files, list)
    assert isinstance(selection.reasoning, str)
    
    # Based on our mock response
    assert "main.py" in selection.selected_files
    assert "utils.py" in selection.selected_files


def test_select_relevant_files_json_parse_error(temp_repo, test_config, mock_weak_model):
    """Test handling of JSON parse errors in file selection."""
    # Create a mock model that returns invalid JSON
    invalid_json_model = type(mock_weak_model)([
        "This is not valid JSON but contains main.py and utils.py files"
    ])
    
    builder = ContextBuilder(temp_repo, test_config, invalid_json_model, mock_weak_model)
    
    question = "How does the main function work?"
    repository_structure = "main.py\nutils.py\nconfig.json"
    file_sizes = {"main.py": 100, "utils.py": 200, "config.json": 50}
    
    selection = builder.select_relevant_files(question, repository_structure, file_sizes)
    
    # Should still extract files even with JSON parse error
    assert isinstance(selection, FileSelectionResponse)
    assert "JSON parsing failed" in selection.reasoning


def test_build_context_with_repomix(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test building context with repomix."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    selected_files = ["main.py", "utils.py"]
    
    context = builder.build_context_with_repomix(selected_files)
    
    assert isinstance(context, str)
    assert len(context) > 0
    
    # Should contain file content or fallback content
    assert "main.py" in context or "Repository Context" in context


def test_build_context_empty_files(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test building context with empty file list."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    context = builder.build_context_with_repomix([])
    
    assert context == "No files selected for context."


def test_build_context_fallback(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test fallback context building."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    selected_files = ["main.py", "utils.py"]
    
    context = builder._build_context_fallback(selected_files)
    
    assert isinstance(context, str)
    assert "Repository Context" in context
    assert "main.py" in context
    assert "utils.py" in context
    assert "```python" in context  # Should detect Python files


def test_optimize_context_small(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test context optimization for small context."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    question = "How does this work?"
    raw_context = "Small context that doesn't need optimization"
    selected_files = ["main.py"]
    
    result = builder.optimize_context(question, raw_context, selected_files)
    
    # Small context should not be optimized
    assert result.optimized_context == raw_context
    assert "within size limits" in result.summary


def test_optimize_context_large(temp_repo, test_config, mock_strong_model, mock_weak_model):
    """Test context optimization for large context."""
    builder = ContextBuilder(temp_repo, test_config, mock_strong_model, mock_weak_model)
    
    question = "How does this work?"
    # Create large context that exceeds max_context_size
    raw_context = "Large context " * (test_config.max_context_size // 10)
    selected_files = ["main.py"]
    
    result = builder.optimize_context(question, raw_context, selected_files)
    
    # Should be optimized by weak model
    assert isinstance(result.optimized_context, str)
    assert isinstance(result.summary, str)
    assert len(result.optimized_context) > 0