from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import os
import requests
import json
from anthropic import Anthropic
from google import genai
from openai import OpenAI


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
            "gpt-3.5-turbo": "gpt-3.5-turbo-0125",
            "gpt-4": "gpt-4-0125-preview"
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
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307"
        }

    def chat(self, message: str, model: str = "claude-3-sonnet") -> str:
        try:
            model_version = self.available_models.get(model, model)
            response = self.client.messages.create(
                model=model_version,
                messages=[{"role": "user", "content": message}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Claude Error: {str(e)}"


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.available_models = {
            "gemini-pro": "gemini-pro",
            "gemini-pro-vision": "gemini-pro-vision"
        }

    def chat(self, message: str, model: str = "gemini-pro") -> str:
        try:
            model_version = self.available_models.get(model, model)
            model = genai.GenerativeModel(model_version)
            response = model.generate_content(message)
            return response.text
        except Exception as e:
            return f"Gemini Error: {str(e)}"


class OllamaProvider(AIProvider):
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        # Get available models from Ollama
        self.available_models = self._get_available_models()

    def _get_available_models(self) -> Dict[str, str]:
        try:
            response = requests.get(f"{self.host}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                return {model["name"]: model["name"] for model in models}
            return {}
        except Exception:
            return {}

    def chat(self, message: str, model: str = "llama2") -> str:
        """Improved Ollama chat implementation that handles streaming responses properly"""
        try:
            # Option 1: Non-streaming request
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                    "stream": False  # Explicitly disable streaming
                }
            )

            if response.status_code == 200:
                try:
                    # Parse the JSON response
                    result = response.json()
                    return result.get("message", {}).get("content", "")
                except json.JSONDecodeError:
                    # Fallback to Option 2 if JSON parsing fails
                    pass

            # Option 2: Handle streaming response (fallback)
            full_response = ""
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": message}],
                    "stream": True
                },
                stream=True
            )

            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            line_data = json.loads(line.decode('utf-8'))
                            if "message" in line_data and "content" in line_data["message"]:
                                chunk = line_data["message"]["content"]
                                full_response += chunk
                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue

                return full_response

            return f"Ollama Error: HTTP {response.status_code}"
        except Exception as e:
            return f"Ollama Error: {str(e)}"


class AIProviderFactory:
    @staticmethod
    def create_provider(provider_type: str, **kwargs) -> AIProvider:
        providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "ollama": OllamaProvider
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
        model="gpt-o3-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    print("OpenAI Response:", openai_response)

    # Claude example
    claude_response = chat(
        message=message,
        provider_type="claude",
        model="claude-3-sonnet",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    print("Claude Response:", claude_response)

    # Gemini example
    gemini_response = chat(
        message=message,
        provider_type="gemini",
        model="gemini-pro",
        api_key=os.getenv("GOOGLE_API_KEY")
    )
    print("Gemini Response:", gemini_response)

    # Ollama example (assuming local installation)
    ollama_response = chat(
        message=message,
        provider_type="ollama",
        model="llama3.1"
    )
    print("Ollama Response:", ollama_response)
