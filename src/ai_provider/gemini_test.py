import os
from dotenv import load_dotenv
from ai_provider import GeminiProvider
from rich.console import Console

console = Console()


def test_gemini_connection():
    """Test the connection to Gemini API"""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        console.print(
            "[red]Error: GEMINI_API_KEY not found in environment variables[/]")
        return False

    try:
        provider = GeminiProvider(api_key=api_key)
        console.print("[green]Successfully initialized Gemini provider[/]")
        return True
    except Exception as e:
        console.print(f"[red]Error initializing Gemini provider: {str(e)}[/]")
        return False


def test_gemini_chat(model: str = "gemini-2.5-flash-preview-04-17"):
    """Test chat functionality with Gemini"""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        console.print(
            "[red]Error: GEMINI_API_KEY not found in environment variables[/]")
        return

    try:
        provider = GeminiProvider(api_key=api_key)
        console.print(f"\n[cyan]Testing chat with model: {model}[/]")

        # Test message
        test_message = "What is 2+2? Please respond with just the number."
        console.print(f"\n[bold]Sending message:[/] {test_message}")

        # Get response
        response = provider.chat(test_message, model)
        console.print(f"\n[bold]Response:[/] {response}")

        return True
    except Exception as e:
        console.print(f"[red]Error in chat test: {str(e)}[/]")
        return False


if __name__ == "__main__":
    console.print("[bold]Gemini API Test Tool[/]\n")

    # Test connection
    if test_gemini_connection():
        # Test chat with default model
        test_gemini_chat()

        # Ask user if they want to test with a different model
        model = input(
            "\nEnter model name to test (press Enter for default): ").strip()
        if model:
            test_gemini_chat(model)
