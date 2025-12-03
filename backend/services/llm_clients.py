"""Unified LLM client interface for Gemini and Ollama."""
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
import google.generativeai as genai
from ollama import AsyncClient
from config import settings
import asyncio


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream_generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:
        """Stream response generation from the LLM."""
        pass


class GeminiClient(BaseLLMClient):
    """Google Gemini API client."""
    
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """
        Initialize Gemini client.
        
        Args:
            model_name: Gemini model to use (e.g., "gemini-pro", "gemini-pro-vision")
        """
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response from Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            # Combine system prompt with user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}"
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            )
            
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    async def stream_generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:
        """
        Stream response generation from Gemini.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks as they are generated
        """
        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}"
            
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Gemini's stream is synchronous, so we need to handle it carefully
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    stream=True
                )
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            raise RuntimeError(f"Gemini streaming error: {str(e)}")


class OllamaClient(BaseLLMClient):
    """Ollama API client."""
    
    def __init__(self, model_name: str = "llama2"):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Ollama model to use (e.g., "llama2", "mistral", "codellama")
        """
        self.model_name = model_name
        self.client = AsyncClient(host=settings.ollama_base_url)
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """
        Generate a response from Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            response = await self.client.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {str(e)}")
    
    async def stream_generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> AsyncIterator[str]:
        """
        Stream response generation from Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks as they are generated
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            stream = await self.client.chat(
                model=self.model_name,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                }
            )
            
            async for chunk in stream:
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                    
        except Exception as e:
            raise RuntimeError(f"Ollama streaming error: {str(e)}")


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(provider: str, model_name: str) -> BaseLLMClient:
        """
        Create an LLM client based on provider.
        
        Args:
            provider: "gemini" or "ollama"
            model_name: Name of the model to use
            
        Returns:
            Appropriate LLM client instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider == "gemini":
            return GeminiClient(model_name=model_name)
        elif provider == "ollama":
            return OllamaClient(model_name=model_name)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'gemini' or 'ollama'.")
