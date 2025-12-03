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
            
            # Configure safety settings to be less restrictive for legitimate use cases
            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_ONLY_HIGH"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_ONLY_HIGH"
                }
            ]
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            )
            
            # Handle response - properly extract text from parts
            # Gemini can return multi-part responses, so we need to handle them correctly
            if not response.candidates:
                raise RuntimeError("No candidates in Gemini response")
            
            candidate = response.candidates[0]
            
            # Check if response was blocked due to safety filters
            if hasattr(candidate, 'finish_reason'):
                finish_reason = str(candidate.finish_reason)
                # Map common finish reasons
                finish_reason_map = {
                    '1': 'STOP (normal completion)',
                    '2': 'MAX_TOKENS (response cut off)',
                    '3': 'SAFETY (blocked by safety filters)',
                    '4': 'RECITATION (would recite training data)',
                    '5': 'OTHER'
                }
                finish_reason_desc = finish_reason_map.get(finish_reason, finish_reason)
                
                if 'SAFETY' in finish_reason or finish_reason == '3':
                    safety_info = ""
                    if hasattr(candidate, 'safety_ratings'):
                        safety_info = f" Safety ratings: {candidate.safety_ratings}"
                    raise RuntimeError(f"Response blocked by Gemini safety filters.{safety_info}")
                elif finish_reason == '2':  # MAX_TOKENS
                    # This is not necessarily an error - the response might just be long
                    # Let's try to extract what we have
                    print(f"WARNING: Gemini response hit max_tokens limit. Response may be incomplete.")
                elif 'PROHIBITED' in finish_reason or 'RECITATION' in finish_reason or finish_reason in ['4', '5']:
                    raise RuntimeError(f"Response blocked by Gemini ({finish_reason_desc})")
            
            if not hasattr(candidate, 'content') or not hasattr(candidate.content, 'parts'):
                raise RuntimeError("Invalid response structure from Gemini")
            
            parts = candidate.content.parts
            if not parts:
                # Check finish reason for more context
                finish_reason = str(getattr(candidate, 'finish_reason', 'unknown'))
                # Debug: print the full response to understand what's happening
                print(f"DEBUG: Gemini response candidate: {candidate}")
                print(f"DEBUG: Finish reason: {finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    print(f"DEBUG: Safety ratings: {candidate.safety_ratings}")
                raise RuntimeError(f"No content parts in Gemini response (finish_reason: {finish_reason})")
            
            # Extract text from all parts and join them
            text_parts = []
            for part in parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            
            if not text_parts:
                raise RuntimeError("No text content found in Gemini response parts")
            
            return ''.join(text_parts)
            
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
            # Stream response
            # accumulated_text = "" # This variable is not needed for streaming yield
            for chunk in response:
                # Handle chunk with proper parts accessor
                if chunk.candidates and chunk.candidates[0].content.parts:
                    chunk_text = chunk.candidates[0].content.parts[0].text
                    # accumulated_text += chunk_text # Not needed for streaming yield
                    yield chunk_text
            
            # return accumulated_text # A generator should yield, not return a final value in this context
                    
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
