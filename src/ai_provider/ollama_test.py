import requests
import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def test_ollama_connection():
    """Test the Ollama API connection and display available models"""
    console.print(
        Panel("[bold cyan]Testing Ollama Connection[/]", expand=False))

    try:
        response = requests.get("http://localhost:11434/api/tags")

        if response.status_code == 200:
            models = response.json().get("models", [])
            console.print("[green]Connection successful![/]")

            if models:
                console.print(f"[bold]Available models:[/]")
                for model in models:
                    console.print(f"- {model['name']}")
            else:
                console.print(
                    "[yellow]No models found. Have you pulled any models with Ollama?[/]")
        else:
            console.print(f"[red]HTTP Error: {response.status_code}[/]")
            console.print(response.text)
    except Exception as e:
        console.print(f"[red bold]Connection Error:[/] {str(e)}")
        console.print(
            "\n[yellow]Is Ollama running? Start it with 'ollama serve'[/]")


def test_ollama_chat(model="llama2"):
    """Test Ollama chat endpoint"""
    console.print(
        Panel(f"[bold cyan]Testing Ollama Chat with model: {model}[/]", expand=False))

    message = "Hello, tell me a short joke about programming."

    try:
        # Non-streaming request
        console.print("[bold]Sending non-streaming request...[/]")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
        )

        if response.status_code == 200:
            try:
                result = response.json()
                console.print("[green]Non-streaming request successful![/]")
                console.print("[bold]Response JSON structure:[/]")
                console.print(Syntax(json.dumps(result, indent=2), "json"))

                if "message" in result and "content" in result["message"]:
                    console.print("\n[bold]Response content:[/]")
                    console.print(result["message"]["content"])
                else:
                    console.print("\n[yellow]Unexpected response structure[/]")
            except json.JSONDecodeError as e:
                console.print(f"[red]JSON decode error: {str(e)}[/]")
                console.print("[bold]Raw response:[/]")
                console.print(
                    response.text[:500] + "..." if len(response.text) > 500 else response.text)
        else:
            console.print(f"[red]HTTP Error: {response.status_code}[/]")
            console.print(response.text)

        # Streaming request (for comparison)
        console.print(
            "\n[bold]Sending streaming request (showing first few chunks)...[/]")
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [{"role": "user", "content": message}],
                "stream": True
            },
            stream=True
        )

        if response.status_code == 200:
            console.print(
                "[green]Streaming request initiated successfully![/]")
            console.print("[bold]First few response chunks:[/]")

            for i, line in enumerate(response.iter_lines()):
                if i >= 5:  # Only show first 5 chunks
                    console.print("...")
                    break

                if line:
                    try:
                        line_data = json.loads(line.decode('utf-8'))
                        console.print(
                            Syntax(json.dumps(line_data, indent=2), "json"))
                    except json.JSONDecodeError:
                        console.print(f"[red]Chunk {i} JSON decode error[/]")
                        console.print(line.decode('utf-8'))
        else:
            console.print(
                f"[red]HTTP Error for streaming request: {response.status_code}[/]")

    except Exception as e:
        console.print(f"[red bold]Error:[/] {str(e)}")


if __name__ == "__main__":
    console.print("[bold]Ollama API Debug Tool[/]\n")

    test_ollama_connection()
    print("\n")

    # Ask user which model to test
    model = input(
        "\nEnter model name to test (default: llama2): ").strip() or "llama2"

    test_ollama_chat(model)
