"""
Abstract base class for LLM implementations
Allows easy switching between Ollama, Gemini, OpenAI, etc.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class LLMResponse(BaseModel):
    """Standardized response format across all LLMs"""
    content: str
    model: str
    tokens_used: Optional[int] = None
    raw_response: Optional[Dict] = None


class BaseLLMClient(ABC):
    """Abstract base class that all LLM clients must implement"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
    
    @abstractmethod
    def chat(
        self, 
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: str = "text"  # "text" or "json"
    ) -> LLMResponse:
        """
        Send a chat message and get response
        
        Args:
            system_prompt: System instructions for the LLM
            user_prompt: User message/query
            temperature: Creativity level (0.0 to 1.0)
            response_format: Expected format ("text" or "json")
        
        Returns:
            LLMResponse object with standardized format
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this LLM is available and ready to use"""
        pass
