"""
Ollama/Llama implementation of LLM interface
"""
import ollama
from typing import Dict
from .llm_interface import BaseLLMClient, LLMResponse


class OllamaClient(BaseLLMClient):
    """Ollama client for local Llama models"""
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        super().__init__(model_name)
        self.base_url = "http://localhost:11434"
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: str = "text"
    ) -> LLMResponse:
        """Send chat request to Ollama"""
        
        messages = [
            {
                'role': 'system',
                'content': system_prompt
            },
            {
                'role': 'user',
                'content': user_prompt
            }
        ]
        
        # Configure response format
        options = {'temperature': temperature}
        format_option = 'json' if response_format == 'json' else None
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                format=format_option,
                options=options
            )
            
            return LLMResponse(
                content=response['message']['content'],
                model=self.model_name,
                tokens_used=response.get('eval_count'),
                raw_response=response
            )
        
        except Exception as e:
            raise Exception(f"Ollama chat failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Ollama is running"""
        try:
            ollama.list()
            return True
        except:
            return False
