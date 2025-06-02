"""Tests for AI models."""

import pytest

from repox.models import AIMessage, AIResponse, ModelFactory, OpenAIModel


def test_ai_message():
    """Test AIMessage model."""
    message = AIMessage(role="user", content="Hello")
    
    assert message.role == "user"
    assert message.content == "Hello"


def test_ai_response():
    """Test AIResponse model."""
    response = AIResponse(content="Hello back")
    
    assert response.content == "Hello back"
    assert response.usage is None
    
    # Test with usage
    response_with_usage = AIResponse(
        content="Hello",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    )
    
    assert response_with_usage.usage["total_tokens"] == 15


def test_openai_model_init():
    """Test OpenAI model initialization."""
    model = OpenAIModel("gpt-3.5-turbo", "test-key", "https://api.openai.com/v1")
    
    assert model.model_name == "gpt-3.5-turbo"
    assert model.client.api_key == "test-key"


def test_model_factory_create_openai():
    """Test creating OpenAI model through factory."""
    model = ModelFactory.create_openai_model("gpt-4", "test-key")
    
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "gpt-4"


def test_model_factory_create_model():
    """Test creating model through factory."""
    model = ModelFactory.create_model("openai", "gpt-4", "test-key")
    
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "gpt-4"


def test_model_factory_unsupported_type():
    """Test creating unsupported model type."""
    with pytest.raises(ValueError, match="Unsupported model type"):
        ModelFactory.create_model("unsupported", "model", "key")


# Note: We don't test actual OpenAI API calls here as they require real API keys
# and would make network requests. In a real test suite, you might want to use
# mock responses or a test server.