import gradio as gr
import os
from search import DeepSearchAgent
import tempfile
import shutil
import time
import io
import sys
import re
from contextlib import redirect_stdout

# Function to clean Rich console output (remove ANSI color codes)


def clean_rich_output(text):
    # Remove ANSI escape sequences (color codes, formatting)
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    cleaned_text = ansi_escape.sub('', text)

    # Remove other formatting elements that might appear
    cleaned_text = re.sub(
        r'\[bold.*?\]|\[/\]|\[dim\]|\[.*?\]', '', cleaned_text)

    # Remove box drawing characters and panels
    cleaned_text = re.sub(r'[╭╮╯╰│]', '', cleaned_text)

    # Remove extra newlines and spaces
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)

    return cleaned_text.strip()


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


def generate_questions(topic):
    global AGENT, CURRENT_TOPIC, CURRENT_QUESTIONS

    if not AGENT:
        return "Please initialize the agent first", []

    try:
        CURRENT_TOPIC = topic
        redirect_output = io.StringIO()
        with redirect_stdout(redirect_output):
            CURRENT_QUESTIONS = AGENT.generate_initial_questions(topic)

        # Clean the raw terminal output
        cleaned_output = clean_rich_output(redirect_output.getvalue())

        # Debug output for questions
        if not CURRENT_QUESTIONS:
            cleaned_output += "\n\nWARNING: No questions were parsed from the LLM response."
            return cleaned_output, []

        return cleaned_output, CURRENT_QUESTIONS
    except Exception as e:
        error_msg = f"Error generating questions: {str(e)}"
        import traceback
        error_msg += f"\n\nTraceback: {traceback.format_exc()}"
        return error_msg, []


def process_answers(answer1, answer2, answer3):
    global AGENT, CURRENT_QUESTIONS, CURRENT_ANSWERS

    if not AGENT or not CURRENT_QUESTIONS:
        return "Please initialize the agent and generate questions first"

    try:
        # Create a list of answers
        answers_list = [answer1, answer2, answer3]

        # Process each answer
        CURRENT_ANSWERS = []
        for i, question in enumerate(CURRENT_QUESTIONS[:3]):
            if i >= len(answers_list):
                break

            answer = answers_list[i]

            # Skip empty answers
            if not isinstance(answer, str):
                answer = str(answer)

            if not answer.strip():
                continue

            # Store the answer as is
            CURRENT_ANSWERS.append(answer)

            # Store user answers in the AGENT's log
            AGENT.log_data["answers"].append({
                "question": question['question'],
                "options": question['options'],
                "selected": answer
            })

        if not CURRENT_ANSWERS:
            return "No answers were provided. Please answer at least one question."

        return f"Successfully recorded {len(CURRENT_ANSWERS)} answers. You can now proceed to the Research tab."
    except Exception as e:
        import traceback
        return f"Error processing answers: {str(e)}\n\nTraceback: {traceback.format_exc()}"


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


def generate_final_report(progress=gr.Progress()):
    global AGENT, CURRENT_TOPIC, CURRENT_ANSWERS, CURRENT_SEARCH_RESULTS

    if not AGENT or not CURRENT_SEARCH_RESULTS:
        return "Please complete the research first", None, ""

    try:
        # Initialize report content
        report_content = ""

        progress(0.05, "Initializing report generation...")

        # Redirect stdout to capture the output
        old_stdout = sys.stdout
        redirect_output = io.StringIO()
        sys.stdout = redirect_output

        # First, generate the report structure
        progress(0.1, "Generating report structure...")
        report_structure = AGENT._generate_report_structure(CURRENT_TOPIC)

        # Restore stdout for first update
        sys.stdout = old_stdout

        # Update report content
        report_content = f"# Research Report Structure\n\n{report_structure}\n\n"
        progress(0.15, "Report structure generated.")

        # Redirect stdout again
        sys.stdout = redirect_output

        # Organize search results
        progress(0.2, "Organizing research results...")
        content_summary = AGENT._organize_search_results(
            CURRENT_SEARCH_RESULTS)

        # Parse the structure to identify sections
        sections = []
        current_section = ""
        current_headers = []

        for line in report_structure.split('\n'):
            line = line.strip()
            if line.startswith('#'):
                if current_section and '[Content Tag]' in current_section:
                    sections.append({
                        'headers': current_headers.copy(),
                        'content': current_section
                    })
                current_section = line + '\n'
                current_headers = [line]
            else:
                current_section += line + '\n'

        if current_section and '[Content Tag]' in current_section:
            sections.append({
                'headers': current_headers.copy(),
                'content': current_section
            })

        # Restore stdout
        sys.stdout = old_stdout

        # Generate content for each section with updates
        final_report = []
        previous_content = ""

        progress(0.25, "Extracting key findings...")
        research_context = {
            'topic': CURRENT_TOPIC,
            'focus_areas': CURRENT_ANSWERS,
            'total_sources': len(CURRENT_SEARCH_RESULTS),
            'key_findings': AGENT._extract_key_findings(CURRENT_SEARCH_RESULTS)
        }

        progress(0.3, "Key findings extracted. Building report sections...")
        report_content = f"# Research Report: {CURRENT_TOPIC}\n\n## Key Findings\n\n{research_context['key_findings']}\n\n"

        # Generate content for each section
        total_sections = len(sections)
        for i, section in enumerate(sections):
            section_title = ' '.join(h.lstrip('#').strip()
                                     for h in section['headers'])
            section_progress = 0.3 + (0.5 * (i / total_sections))
            progress(
                section_progress, f"Generating section {i+1}/{total_sections}: {section_title}")

            # Redirect stdout for section generation
            sys.stdout = redirect_output

            # Generate section content
            prompt = f"""Write comprehensive content for the {section_title} section of the research report about '{CURRENT_TOPIC}'.

            Research Context:
            - Topic: {research_context['topic']}
            - Focus Areas: {', '.join(research_context['focus_areas'])}
            - Total Sources: {research_context['total_sources']}
            - Key Findings: {research_context['key_findings']}

            Previous Content Generated:
            {previous_content}

            Research Data Available:
            {content_summary}

            IMPORTANT: 
            1. Wrap your response in triple backticks (```). Only the content within the backticks will be used.
            2. Write detailed, well-structured content that integrates findings from multiple sources.
            3. Make connections between different aspects of the research.
            4. Include specific examples and data points from the research.
            5. Maintain academic tone and proper citations.
            6. Ensure content flows naturally from previous sections.
            7. Do not include any meta-commentary or reasoning outside the backticks."""

            response = AGENT._call_llm(prompt)
            section_content = AGENT._extract_content_between_backticks(
                response)

            # Restore stdout
            sys.stdout = old_stdout

            # Replace [Content Tag] with generated content
            final_section = section['content'].replace(
                '[Content Tag]', section_content)
            final_report.append(final_section)

            # Update previous content for context in next iteration
            previous_content += f"\n{section_title}:\n{section_content}\n"

            # Update the report content for UI
            report_content = '\n'.join(final_report)

            # Update progress after each section
            progress(section_progress + (0.5 / total_sections),
                     f"Completed section {i+1}/{total_sections}")

        # Generate executive summary
        progress(0.85, "Generating executive summary...")
        executive_summary = AGENT._generate_executive_summary(
            CURRENT_TOPIC, research_context, report_content)

        # Add executive summary at the beginning
        complete_report = f"# Executive Summary\n\n{executive_summary}\n\n{report_content}"
        progress(0.9, "Executive summary added. Finalizing report...")

        # Store the report
        AGENT.log_data["report"] = complete_report

        # Create temporary directory for report download
        progress(0.92, "Preparing files for download...")
        temp_dir = tempfile.mkdtemp()
        temp_output_dir = os.path.join(temp_dir, "results")
        os.makedirs(temp_output_dir, exist_ok=True)

        progress(0.95, "Saving results...")
        results_path = AGENT.save_results(CURRENT_TOPIC, temp_output_dir)

        # Package results into a zip file
        progress(0.98, "Creating downloadable archive...")
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        zip_filename = f"results_{timestamp}.zip"

        # Create the archive in the temp directory
        zip_basename = os.path.join(temp_dir, f"results_{timestamp}")
        zip_path = f"{zip_basename}.zip"

        shutil.make_archive(
            zip_basename, 'zip', temp_output_dir
        )

        # Clean up temp output directory but keep temp dir until the file is downloaded
        shutil.rmtree(temp_output_dir, ignore_errors=True)

        progress(1.0, "Report generation complete!")

        # Return with complete report and download link
        return complete_report, zip_path, "Report generation complete. You can download the full results."

    except Exception as e:
        # Restore stdout in case of exception
        if 'old_stdout' in locals():
            sys.stdout = old_stdout
        error_msg = f"Error generating report: {str(e)}"
        import traceback
        error_msg += f"\n\nTraceback: {traceback.format_exc()}"
        return "", None, error_msg

# Build Gradio Interface


def create_interface():
    custom_css = """
    #header {text-align: center; margin-bottom: 1rem;}
    .gradio-container {max-width: 900px; margin: 0 auto;}
    """

    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate"
    )

    with gr.Blocks(title="DeepSearch Research Agent", css=custom_css, theme=theme) as demo:
        gr.Markdown("# DeepSearch Research Agent", elem_id="header")
        gr.Markdown(
            "This web interface allows you to perform deep research on any topic using advanced search techniques and AI assistance.")

        gr.Markdown("## 1. Initialize")
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

                def update_ollama_host(host):
                    global OLLAMA_HOST
                    if host and host.strip():
                        OLLAMA_HOST = host.strip()
                    return f"Ollama host set to: {OLLAMA_HOST}"

                ollama_host_textbox.change(
                    update_ollama_host,
                    inputs=[ollama_host_textbox],
                    outputs=[]
                )

                init_button = gr.Button("Initialize Agent")
            with gr.Column():
                init_output = gr.Textbox(
                    label="Initialization Status", interactive=False
                )

        gr.Markdown("## 2. Define Research Topic")
        with gr.Row():
            with gr.Column():
                    topic_textbox = gr.Textbox(
                        label="Research Topic",
                        placeholder="Enter the topic you want to research"
                    )
                    generate_questions_button = gr.Button("Generate Questions")

            # System output (can be hidden if desired)
            questions_output = gr.Textbox(
                label="System Output", interactive=False, visible=True)

            # Three fixed question-answer blocks
            with gr.Row(visible=True) as questions_container:
                with gr.Column():
                    # Question 1
                    question1_label = gr.Markdown("Question 1", visible=False)
                    question1_text = gr.Markdown("", visible=False)
                    answer1 = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here",
                        visible=False,
                        interactive=True
                    )

                    # Question 2
                    question2_label = gr.Markdown("Question 2", visible=False)
                    question2_text = gr.Markdown("", visible=False)
                    answer2 = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here",
                        visible=False,
                        interactive=True
                    )

                    # Question 3
                    question3_label = gr.Markdown("Question 3", visible=False)
                    question3_text = gr.Markdown("", visible=False)
                    answer3 = gr.Textbox(
                        label="Your Answer",
                        placeholder="Type your answer here",
                        visible=False,
                        interactive=True
                    )

            # Process answers button
            process_answers_button = gr.Button("Submit Answers", visible=False)
            answers_output = gr.Textbox(
                label="Status", interactive=False)

            # Store questions in state
            questions_state = gr.State([])

            # Function to update the questions display
            def update_questions_display(questions_data, output_text):
                if not questions_data or len(questions_data) == 0:
                    return [
                        gr.update(visible=False), gr.update(
                            visible=False), gr.update(visible=False),
                        gr.update(visible=False), gr.update(
                            visible=False), gr.update(visible=False),
                        gr.update(visible=False), gr.update(
                            visible=False), gr.update(visible=False),
                        gr.update(visible=False), questions_data
                    ]

                # Make sure we have up to 3 questions
                questions = questions_data[:3]
                while len(questions) < 3:
                    questions.append({"question": "", "options": []})

                # Get the first 3 questions
                q1 = questions[0]
                q2 = questions[1]
                q3 = questions[2]

                # Format questions with options
                def format_question_with_options(q):
                    if not q["question"]:
                        return ""

                    question_text = q["question"]

                    if q["options"]:
                        options_text = "\n\n"
                        for i, option in enumerate(q["options"]):
                            options_text += f"{chr(97+i)}) {option}\n"
                        question_text += options_text

                    return question_text

                q1_text = format_question_with_options(q1)
                q2_text = format_question_with_options(q2)
                q3_text = format_question_with_options(q3)

                # Determine visibility based on if questions exist
                q1_visible = bool(q1["question"])
                q2_visible = bool(q2["question"])
                q3_visible = bool(q3["question"])

                # Show the process button if we have at least one question
                process_visible = q1_visible

                return [
                    gr.update(visible=q1_visible), gr.update(
                        value=q1_text, visible=q1_visible), gr.update(visible=q1_visible, interactive=True),
                    gr.update(visible=q2_visible), gr.update(
                        value=q2_text, visible=q2_visible), gr.update(visible=q2_visible, interactive=True),
                    gr.update(visible=q3_visible), gr.update(
                        value=q3_text, visible=q3_visible), gr.update(visible=q3_visible, interactive=True),
                    gr.update(visible=process_visible), questions_data
                ]

        gr.Markdown("## 3. Perform Research")
        with gr.Row():
            with gr.Column():
                breadth_slider = gr.Slider(
                    minimum=1,
                    maximum=8,
                    value=3,
                    step=1,
                    label="Research Breadth (number of parallel search paths)"
                )
                depth_slider = gr.Slider(
                    minimum=1,
                    maximum=5,
                    value=2,
                    step=1,
                    label="Research Depth (number of iterative searches)"
                )
                extract_content_checkbox = gr.Checkbox(
                    label="Extract webpage content",
                    value=True
                )
                research_button = gr.Button("Conduct Research")
            with gr.Column():
                research_output = gr.Textbox(
                    label="Research Progress", interactive=False, max_lines=20
                )
                keywords_output = gr.Textbox(
                    label="Generated Keywords", interactive=False
                )

        gr.Markdown("## 4. Generate Report")
        generate_report_button = gr.Button("Generate Final Report")
        with gr.Row():
                with gr.Column(scale=2):
                    report_markdown = gr.Markdown(
                        label="Final Research Report")
                with gr.Column(scale=1):
                    report_status = gr.Textbox(
                        label="Report Status", interactive=False)
                    report_download = gr.File(label="Download Results")

        # Connect components
        init_button.click(
            initialize_agent,
            inputs=[provider_dropdown, model_textbox],
            outputs=[init_output]
        )

        # Update the question display workflow with proper state management
        generate_questions_button.click(
            generate_questions,
            inputs=[topic_textbox],
            outputs=[questions_output, questions_state]
        ).then(
            update_questions_display,
            inputs=[questions_state, questions_output],
            outputs=[
                question1_label, question1_text, answer1,
                question2_label, question2_text, answer2,
                question3_label, question3_text, answer3,
                process_answers_button, questions_state
            ]
        )

        process_answers_button.click(
            process_answers,
            inputs=[answer1, answer2, answer3],
            outputs=[answers_output]
        )

        research_button.click(
            perform_research,
            inputs=[breadth_slider, depth_slider, extract_content_checkbox],
            outputs=[research_output, keywords_output]
        )

        generate_report_button.click(
            generate_final_report,
            inputs=[],
            outputs=[report_markdown, report_download, report_status]
        )

    return demo


# Run the app
if __name__ == "__main__":
    demo = create_interface()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
