"""Tests for the main assistant."""

import pytest

from repox.core.assistant import RepoxAssistant
from repox.core.config import RepoxConfig


def test_assistant_init(temp_repo, test_config):
    """Test assistant initialization."""
    assistant = RepoxAssistant(str(temp_repo), test_config)
    
    assert assistant.repo_path == temp_repo.resolve()
    assert assistant.config == test_config


def test_assistant_init_invalid_repo():
    """Test assistant initialization with invalid repository."""
    # Set API key to avoid that error first
    config = RepoxConfig()
    config.openai_api_key = "test-key"
    
    with pytest.raises(ValueError, match="Repository path does not exist"):
        RepoxAssistant("/nonexistent/path", config)


def test_assistant_init_no_api_key(temp_repo):
    """Test assistant initialization without API key."""
    from repox.core.config import RepoxConfig
    
    config = RepoxConfig()
    config.openai_api_key = None
    
    with pytest.raises(ValueError, match="OpenAI API key is required"):
        RepoxAssistant(str(temp_repo), config)


def test_get_repository_summary(temp_repo, test_config):
    """Test getting repository summary."""
    assistant = RepoxAssistant(str(temp_repo), test_config)
    
    summary = assistant.get_repository_summary()
    
    assert isinstance(summary, dict)
    assert "total_files" in summary
    assert "total_size" in summary
    assert summary["total_files"] > 0


def test_list_processable_files(temp_repo, test_config):
    """Test listing processable files."""
    assistant = RepoxAssistant(str(temp_repo), test_config)
    
    files = assistant.list_processable_files()
    
    assert isinstance(files, list)
    assert len(files) > 0
    assert "main.py" in files
    assert "utils.py" in files


def test_preview_file_selection(temp_repo, test_config, monkeypatch):
    """Test previewing file selection."""
    # Mock the AI models to avoid actual API calls
    from repox.utils.models import FileSelectionResponse
    
    def mock_select_files(*args, **kwargs):
        return FileSelectionResponse(
            selected_files=["main.py", "utils.py"],
            reasoning="Test reasoning"
        )
    
    assistant = RepoxAssistant(str(temp_repo), test_config)
    
    # Mock the context builder method
    monkeypatch.setattr(
        assistant.context_builder,
        "select_relevant_files",
        mock_select_files
    )
    
    preview = assistant.preview_file_selection("How does the main function work?")
    
    assert isinstance(preview, dict)
    assert "question" in preview
    assert "selected_files" in preview
    assert "valid_files" in preview
    assert "invalid_files" in preview
    assert "reasoning" in preview
    
    assert preview["question"] == "How does the main function work?"
    assert "main.py" in preview["selected_files"]
    assert "utils.py" in preview["selected_files"]


# Note: We don't test the full ask() method here as it would require
# mocking multiple AI model calls and repomix integration.
# In a real test suite, you might want to create integration tests
# with proper mocking or use a test AI service.