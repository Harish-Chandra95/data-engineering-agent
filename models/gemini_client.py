"""
Google Gemini implementation with new SDK
"""
from google import genai
from google.genai import types
import os
from .llm_interface import BaseLLMClient, LLMResponse


class GeminiClient(BaseLLMClient):
    """Google Gemini client with new SDK"""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        super().__init__(model_name)
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found")
        
        self.client = genai.Client(api_key=api_key)
        self.model_id = model_name
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        response_format: str = "text"
    ) -> LLMResponse:
        """Send chat request to Gemini"""
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type='application/json' if response_format == 'json' else 'text/plain'
        )
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=full_prompt,
                config=config
            )
            
            return LLMResponse(
                content=response.text,
                model=self.model_id,
                tokens_used=None,  # New SDK handles this differently
                raw_response={'text': response.text}
            )
        
        except Exception as e:
            raise Exception(f"Gemini chat failed: {str(e)}")
    
    def is_available(self) -> bool:
        return os.getenv("GOOGLE_API_KEY") is not None
