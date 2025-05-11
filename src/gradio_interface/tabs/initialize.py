import gradio as gr
from ..state import AGENT, PROVIDERS, DEFAULT_MODELS, OLLAMA_HOST, update_ollama_host
from src.search import DeepSearchAgent


def initialize_agent(provider, model):
    global AGENT

    if provider not in PROVIDERS:
        return False, f"Invalid provider: {provider}"

    if not model:
        model = DEFAULT_MODELS[provider]

    try:
        # Pass the OLLAMA_HOST to DeepSearchAgent when provider is ollama
        if provider == "ollama":
            AGENT = DeepSearchAgent(
                ai_provider=provider, model=model, ollama_host=OLLAMA_HOST)
        else:
            AGENT = DeepSearchAgent(ai_provider=provider, model=model)
        return True, f"Successfully initialized agent with {provider}/{model}"
    except Exception as e:
        return False, f"Error initializing agent: {str(e)}"


def create_initialize_tab():
    with gr.Tab("1. Initialize"):
        with gr.Row():
            with gr.Column():
                provider_dropdown = gr.Dropdown(
                    choices=PROVIDERS,
                    label="AI Provider",
                    value="ollama"
                )
                model_textbox = gr.Textbox(
                    label="Model Name (leave empty for default)",
                    placeholder="e.g., deepseek-r1, gpt-4o"
                )
                # Add Ollama host configuration for Docker
                ollama_host_textbox = gr.Textbox(
                    label="Ollama Host (only for Ollama provider)",
                    placeholder="e.g., host.docker.internal:11434",
                    value=OLLAMA_HOST
                )

                ollama_host_textbox.change(
                    update_ollama_host,
                    inputs=[ollama_host_textbox],
                    outputs=[]
                )

                init_button = gr.Button("Initialize Agent")
            with gr.Column():
                init_output = gr.Textbox(
                    label="Initialization Status", interactive=False)

    return {
        "init_button": init_button,
        "init_output": init_output,
        "provider_dropdown": provider_dropdown,
        "model_textbox": model_textbox
    }
