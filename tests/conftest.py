"""Test configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from repox.config import RepoxConfig
from repox.models import AIMessage, AIModel, AIResponse


class MockAIModel(AIModel):
    """Mock AI model for testing."""
    
    def __init__(self, responses: list = None):
        self.responses = responses or []
        self.call_count = 0
    
    async def generate(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> AIResponse:
        """Generate a mock response."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = "Mock response"
        
        self.call_count += 1
        return AIResponse(content=response)
    
    def generate_sync(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = None,
    ) -> AIResponse:
        """Synchronous version."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            response = "Mock response"
        
        self.call_count += 1
        return AIResponse(content=response)


@pytest.fixture
def temp_repo() -> Generator[Path, None, None]:
    """Create a temporary repository for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        
        # Create sample files
        (repo_path / "main.py").write_text("""
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()
""")
        
        (repo_path / "utils.py").write_text("""
def helper_function():
    return "helper"

class UtilityClass:
    def method(self):
        return "utility"
""")
        
        (repo_path / "config.json").write_text("""
{
    "setting1": "value1",
    "setting2": "value2"
}
""")
        
        # Create subdirectory
        subdir = repo_path / "subdir"
        subdir.mkdir()
        (subdir / "module.py").write_text("""
class Module:
    def __init__(self):
        self.name = "module"
""")
        
        # Create large file
        (repo_path / "large_file.py").write_text("# Large file\n" + "x = 1\n" * 10000)
        
        # Create binary file
        (repo_path / "binary.bin").write_bytes(b"\x00\x01\x02\x03" * 1000)
        
        yield repo_path


@pytest.fixture
def test_config() -> RepoxConfig:
    """Create a test configuration."""
    config = RepoxConfig()
    config.openai_api_key = "test-key"
    config.strong_model = "gpt-4"
    config.weak_model = "gpt-3.5-turbo"
    config.max_file_size = 50000  # Smaller for testing
    config.verbose = False
    return config


@pytest.fixture
def mock_strong_model() -> MockAIModel:
    """Create a mock strong AI model."""
    return MockAIModel([
        '{"selected_files": ["main.py", "utils.py"], "reasoning": "These files contain the main functionality"}',
        "This is a Python project with main functionality in main.py and utilities in utils.py."
    ])


@pytest.fixture
def mock_weak_model() -> MockAIModel:
    """Create a mock weak AI model."""
    return MockAIModel([
        "Optimized context: The main functionality is in main.py with utilities in utils.py.\n\nSummary: Removed boilerplate and focused on core functionality."
    ])