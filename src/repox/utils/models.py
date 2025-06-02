"""AI model interfaces for Repox."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel


class AIMessage(BaseModel):
    """Represents an AI message."""
    role: str
    content: str


class AIResponse(BaseModel):
    """Represents an AI response."""
    content: str
    usage: Optional[Dict[str, Any]] = None


class AIModel(ABC):
    """Abstract base class for AI models."""
    
    @abstractmethod
    async def generate(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Generate a response from the AI model."""
        pass
    
    def generate_sync(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Synchronous version of generate."""
        import asyncio
        return asyncio.run(self.generate(messages, temperature, max_tokens))


class OpenAIModel(AIModel):
    """OpenAI model implementation."""
    
    def __init__(
        self,
        model_name: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
    ):
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    async def generate(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Generate a response using OpenAI API."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return AIResponse(content=content, usage=usage)
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {str(e)}")
    
    def generate_sync(
        self,
        messages: List[AIMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AIResponse:
        """Synchronous version using the sync client."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response content
            content = response.choices[0].message.content or ""
            
            # Extract usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
            
            return AIResponse(content=content, usage=usage)
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {str(e)}")


class ModelFactory:
    """Factory for creating AI models."""
    
    @staticmethod
    def create_openai_model(
        model_name: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
    ) -> OpenAIModel:
        """Create an OpenAI model."""
        return OpenAIModel(model_name, api_key, base_url)
    
    @staticmethod
    def create_model(
        model_type: str,
        model_name: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
    ) -> AIModel:
        """Create a model based on type."""
        if model_type.lower() == "openai":
            return ModelFactory.create_openai_model(model_name, api_key, base_url)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")


class FileSelectionRequest(BaseModel):
    """Request for file selection analysis."""
    question: str
    repository_structure: str
    file_sizes: Dict[str, int]


class FileSelectionResponse(BaseModel):
    """Response for file selection analysis."""
    selected_files: List[str]
    reasoning: str


class ContextBuildingRequest(BaseModel):
    """Request for context building."""
    question: str
    raw_context: str
    file_list: List[str]


class ContextBuildingResponse(BaseModel):
    """Response for context building."""
    optimized_context: str
    summary: str


class AnswerGenerationRequest(BaseModel):
    """Request for answer generation."""
    question: str
    context: str


class AnswerGenerationResponse(BaseModel):
    """Response for answer generation."""
    answer: str
    confidence: Optional[float] = None