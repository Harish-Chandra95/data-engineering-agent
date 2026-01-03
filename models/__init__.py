"""
LLM abstraction layer
"""
from .llm_interface import BaseLLMClient, LLMResponse
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient
from .factory import LLMFactory

__all__ = [
    'BaseLLMClient',
    'LLMResponse',
    'OllamaClient',
    'GeminiClient',
    'LLMFactory'
]
