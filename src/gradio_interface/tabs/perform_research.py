import io
import sys
import gradio as gr
import re
from ..state import AGENT, CURRENT_TOPIC, CURRENT_ANSWERS, CURRENT_SEARCH_RESULTS
from ..utils import clean_rich_output


def perform_research(breadth, depth, extract_content, progress=gr.Progress()):
    global AGENT, CURRENT_TOPIC, CURRENT_ANSWERS, CURRENT_SEARCH_RESULTS

    if not AGENT or not CURRENT_TOPIC or not CURRENT_ANSWERS:
        return "Please complete the previous steps first", ""

    try:
        # Redirect stdout to capture the output
        old_stdout = sys.stdout
        redirect_output = io.StringIO()
        sys.stdout = redirect_output

        progress(0.1, "Generating search keywords...")
        keywords = AGENT.generate_search_keywords(
            CURRENT_TOPIC, CURRENT_ANSWERS, breadth)

        # Build keyword display
        keyword_display = "Generated Keywords:\n"
        for i, kw in enumerate(keywords, 1):
            # Extract keyword from tags if needed
            search_words_pattern = r'<search_words>(.*?)</search_words>'
            search_words_match = re.search(search_words_pattern, kw)
            if search_words_match:
                display_keyword = search_words_match.group(1).strip()
            else:
                display_keyword = kw
            keyword_display += f"{i}. {display_keyword}\n"

        progress(0.2, "Starting deep search...")
        CURRENT_SEARCH_RESULTS = AGENT.deep_search(
            CURRENT_TOPIC, keywords, depth, extract_content=extract_content)

        # Restore stdout
        sys.stdout = old_stdout

        progress(0.9, "Finishing up...")

        # Clean the output for display in Gradio
        cleaned_output = clean_rich_output(redirect_output.getvalue())

        return cleaned_output, keyword_display
    except Exception as e:
        # Restore stdout in case of exception
        if 'old_stdout' in locals():
            sys.stdout = old_stdout
        return f"Error performing research: {str(e)}", ""


def create_perform_research_tab():
    with gr.Tab("3. Perform Research"):
        with gr.Row():
            with gr.Column():
                breadth_slider = gr.Slider(minimum=1, maximum=8, value=3, step=1,
                                           label="Research Breadth (number of parallel search paths)")
                depth_slider = gr.Slider(minimum=1, maximum=5, value=2, step=1,
                                         label="Research Depth (number of iterative searches)")
                extract_content_checkbox = gr.Checkbox(
                    label="Extract webpage content", value=True)
                research_button = gr.Button("Conduct Research")
            with gr.Column():
                research_output = gr.Textbox(
                    label="Research Progress", interactive=False, max_lines=20)
                keywords_output = gr.Textbox(
                    label="Generated Keywords", interactive=False)

    return {
        "breadth_slider": breadth_slider,
        "depth_slider": depth_slider,
        "extract_content_checkbox": extract_content_checkbox,
        "research_button": research_button,
        "research_output": research_output,
        "keywords_output": keywords_output
    }
