from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import requests
import json
from anthropic import Anthropic
from google import genai
from openai import OpenAI
from ollama import Client as ollamaClient


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def chat(self, message: str, model: str) -> str:
        """Send a chat message and get response"""
        pass


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.available_models = {
            "gpt-3.5-turbo": "gpt-3.5-turbo-1106",
            "gpt-4": "gpt-4o"
        }

    def chat(self, message: str, model: str = "gpt-3.5-turbo") -> str:
        try:
            model_version = self.available_models.get(model, model)
            response = self.client.chat.completions.create(
                model=model_version,
                messages=[{"role": "user", "content": message}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI Error: {str(e)}"


class ClaudeProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.available_models = {
            "claude-3.7-sonnet": "claude-3-7-sonnet-20250219",
            "claude-3.5-haiku": "claude-3-5-haiku-20241022",
            "claude-3-opus": "claude-3-opus-20240229"
        }

    def chat(self, message: str, model: str = "claude-3.7-sonnet") -> str:
        try:
            model_version = self.available_models.get(model, model)
            response = self.client.create_message(
                model=model_version,
                messages=[{"role": "user", "content": message}]
            )
            return response.content
        except Exception as e:
            return f"Claude Error: {str(e)}"


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.available_models = {
            "gemini-flash": "models/gemini-2.5-flash-preview-04-17",
            "gemini-pro": "gemini-2.5-pro-exp-03-25",
        }

    def chat(self, message: str, model: str = "gemini-2.5-flash-preview-04-17") -> str:
        try:
            model_version = self.available_models.get(model, f"models/{model}")
            response = self.client.models.generate_content(
                model=model_version,
                contents=message
            )
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"


class ollamaProvider(AIProvider):
    def __init__(self, host: str = "http://localhost:11434"):
        self.client = ollamaClient(host=host)
        self.available_models = self._get_available_models()

    def _get_available_models(self) -> Dict[str, str]:
        try:
            models = self.client.list()
            return {model['name']: model['name'] for model in models}
        except Exception:
            return {}

    def chat(self, message: str, model: str = "llama3.1") -> str:
        try:
            response = self.client.chat(model=model, messages=[
                                        {"role": "user", "content": message}])
            return response['message']['content']
        except Exception as e:
            return f"ollama Error: {str(e)}"


class AIProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> AIProvider:
        providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "ollama": ollamaProvider
        }

        if provider_type not in providers:
            raise ValueError(f"Unknown provider type: {provider_type}")

        return providers[provider_type](**kwargs)


def chat(message: str, provider_type: str, model: str, **kwargs) -> str:
    """
    Unified chat function that works with any supported AI provider

    Args:
        message (str): The message to send
        provider_type (str): The type of provider ("openai", "claude", "gemini", "ollama")
        model (str): The model to use
        **kwargs: Additional arguments for provider initialization

    Returns:
        str: The response from the AI model
    """
    try:
        provider = AIProviderFactory.create_provider(provider_type, **kwargs)
        return provider.chat(message, model)
    except Exception as e:
        return f"Error: {str(e)}"


# Usage example:
if __name__ == "__main__":
    # Load environment variables from .env file if needed
    from dotenv import load_dotenv
    load_dotenv()

    # Example usage with different providers
    message = "Tell me a joke about programming."

    # OpenAI example
    openai_response = chat(
        message=message,
        provider_type="openai",
        model="gpt-3.5-turbo",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    print("OpenAI Response:", openai_response)

    # Claude example
    claude_response = chat(
        message=message,
        provider_type="claude",
        model="claude-3.7-sonnet",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print("Claude Response:", claude_response)

    # Gemini example
    gemini_response = chat(
        message=message,
        provider_type="gemini",
        model="gemini-pro",
        api_key=os.getenv("GEMINI_API_KEY")
    )
    print("Gemini Response:", gemini_response)

    # ollama example (assuming local installation)
    ollama_response = chat(
        message=message,
        provider_type="ollama",
        model="llama3.1"
    )
    print("ollama Response:", ollama_response)
