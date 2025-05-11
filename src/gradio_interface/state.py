import os

# Global variables
AGENT = None
CURRENT_TOPIC = ""
CURRENT_QUESTIONS = []
CURRENT_ANSWERS = []
CURRENT_SEARCH_RESULTS = []

# Available providers and models
PROVIDERS = ["ollama", "openai", "claude", "gemini"]
DEFAULT_MODELS = {
    "ollama": "deepseek-r1",
    "openai": "gpt-4o",
    "claude": "claude-3-sonnet",
    "gemini": "gemini-2.5-flash-preview-04-17"
}

# Default Ollama host - will be used when in Docker
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "host.docker.internal:11434")


def update_ollama_host(host):
    """Update the Ollama host"""
    global OLLAMA_HOST
    if host and host.strip():
        OLLAMA_HOST = host.strip()
    return f"Ollama host set to: {OLLAMA_HOST}"
