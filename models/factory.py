"""
Factory for creating LLM clients
"""
import os
from .llm_interface import BaseLLMClient
from .ollama_client import OllamaClient
from .gemini_client import GeminiClient


class LLMFactory:
    """Factory to create appropriate LLM client"""
    
    @staticmethod
    def create_client(provider: str = None, model: str = None) -> BaseLLMClient:
        """
        Create LLM client based on configuration
        """
        # Read from environment if not specified
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "gemini")  # Default to Gemini now
        
        provider = provider.lower()
        
        if provider == "ollama":
            model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
            client = OllamaClient(model_name=model)
            
            if not client.is_available():
                raise Exception(
                    "Ollama is not available. "
                    "Make sure Ollama is running: ollama serve"
                )
            
            print(f"✓ Using Ollama with model: {model}")
            return client
        
        elif provider == "gemini":
            model = model or os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            client = GeminiClient(model_name=model)
            
            if not client.is_available():
                raise Exception(
                    "Gemini API key not found. "
                    "Set GOOGLE_API_KEY in .env file"
                )
            
            print(f"✓ Using Gemini with model: {model}")
            return client
        
        else:
            raise ValueError(
                f"Unknown LLM provider: {provider}. "
                "Supported: 'ollama', 'gemini'"
            )
    
    @staticmethod
    def auto_select() -> BaseLLMClient:
        """
        Automatically select best available LLM
        Priority: Gemini (better quality) > Ollama (free local)
        """
        # Try Gemini first (better for structured output)
        try:
            client = GeminiClient()
            if client.is_available():
                print("✓ Auto-selected: Gemini 2.0 Flash (best quality)")
                return client
        except:
            pass
        
        # Fallback to Ollama
        try:
            client = OllamaClient()
            if client.is_available():
                print("✓ Auto-selected: Ollama (local, free)")
                return client
        except:
            pass
        
        raise Exception(
            "No LLM available. Please:\n"
            "1. Set GOOGLE_API_KEY for Gemini, or\n"
            "2. Start Ollama: ollama serve"
        )
