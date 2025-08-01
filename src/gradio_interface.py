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
        # Store topic in agent's log data
        AGENT.log_data["topic"] = topic
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


def perform_research(breadth, depth, extract_content, use_adaptive_search, max_iterations, progress=gr.Progress()):
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
        
        # Use adaptive search if enabled
        if use_adaptive_search:
            CURRENT_SEARCH_RESULTS = AGENT.adaptive_deep_search(
                CURRENT_TOPIC, keywords, max_iterations, extract_content=extract_content)
        else:
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
    .gradio-container {max-width: 1200px; margin: 0 auto;}
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
        text-align: center;
        font-weight: bold;
    }
    .status-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 10px;
        margin: 5px 0;
    }
    .research-controls {
        background-color: #f1f3f4;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    """

    theme = gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate"
    )

    with gr.Blocks(title="DeepSearch Research Agent", css=custom_css, theme=theme) as demo:
        # Header
        gr.Markdown("# 🔍 DeepSearch Research Agent", elem_id="header")
        gr.Markdown(
            "**Advanced AI-powered research tool with adaptive search capabilities**\n"
            "This tool performs comprehensive research using intelligent search strategies that adapt based on results."
        )
        
        # Status indicator
        with gr.Row():
            with gr.Column():
                status_display = gr.Markdown("**Status:** Ready to start", elem_classes=["status-box"])
        
        # Main content in tabs for better organization but all on same page
        with gr.Row():
            # Left column - Setup and Controls
            with gr.Column(scale=1):
                gr.Markdown("### 🚀 Setup", elem_classes=["section-header"])
                
                # AI Provider setup
                with gr.Group():
                    provider_dropdown = gr.Dropdown(
                        choices=PROVIDERS,
                        label="AI Provider",
                        value="ollama"
                    )
                    model_textbox = gr.Textbox(
                        label="Model Name (optional)",
                        placeholder="e.g., deepseek-r1, gpt-4o",
                        scale=2
                    )
                    ollama_host_textbox = gr.Textbox(
                        label="Ollama Host (Docker only)",
                        placeholder="host.docker.internal:11434",
                        value=OLLAMA_HOST,
                        visible=True
                    )
                    init_button = gr.Button("🔧 Initialize Agent", variant="primary")
                    init_output = gr.Textbox(
                        label="Initialization Status", 
                        interactive=False,
                        max_lines=2
                    )
                
                # Research Topic
                gr.Markdown("### 📋 Research Topic", elem_classes=["section-header"])
                with gr.Group():
                    topic_textbox = gr.Textbox(
                        label="Research Topic",
                        placeholder="Enter your research topic here...",
                        lines=2
                    )
                    generate_questions_button = gr.Button("📝 Generate Focus Questions", variant="secondary")
                
                # Research Configuration
                gr.Markdown("### ⚙️ Research Settings", elem_classes=["section-header"])
                with gr.Group(elem_classes=["research-controls"]):
                    with gr.Row():
                        breadth_slider = gr.Slider(
                            minimum=1,
                            maximum=8,
                            value=3,
                            step=1,
                            label="Search Breadth",
                            info="Number of parallel search paths"
                        )
                        depth_slider = gr.Slider(
                            minimum=1,
                            maximum=5,
                            value=2,
                            step=1,
                            label="Fixed Depth",
                            info="For traditional search mode"
                        )
                    
                    extract_content_checkbox = gr.Checkbox(
                        label="📄 Extract Full Webpage Content",
                        value=True,
                        info="Deeper analysis but slower"
                    )
                    
                    use_adaptive_search_checkbox = gr.Checkbox(
                        label="🤖 Use Adaptive Search (Recommended)",
                        value=True,
                        info="AI decides when to stop searching"
                    )
                    
                    max_iterations_slider = gr.Slider(
                        minimum=2,
                        maximum=10,
                        value=5,
                        step=1,
                        label="Max Iterations",
                        info="Maximum search rounds for adaptive mode"
                    )
                
                research_button = gr.Button("🔬 Start Research", variant="primary", size="lg")
                generate_report_button = gr.Button("📊 Generate Final Report", variant="primary", size="lg")
            
            # Right column - Results and Interaction
            with gr.Column(scale=2):
                # Questions and Answers Section
                gr.Markdown("### 💭 Focus Questions", elem_classes=["section-header"])
                
                questions_output = gr.Textbox(
                    label="Question Generation Status", 
                    interactive=False, 
                    visible=True,
                    max_lines=3
                )
                
                # Dynamic Questions Display
                with gr.Group(visible=True) as questions_container:
                    # Question 1
                    with gr.Group(visible=False) as question1_group:
                        question1_text = gr.Markdown("", visible=False)
                        answer1 = gr.Textbox(
                            label="Your Answer",
                            placeholder="Type your answer here...",
                            visible=False,
                            interactive=True,
                            lines=2
                        )
                    
                    # Question 2
                    with gr.Group(visible=False) as question2_group:
                        question2_text = gr.Markdown("", visible=False)
                        answer2 = gr.Textbox(
                            label="Your Answer",
                            placeholder="Type your answer here...",
                            visible=False,
                            interactive=True,
                            lines=2
                        )
                    
                    # Question 3
                    with gr.Group(visible=False) as question3_group:
                        question3_text = gr.Markdown("", visible=False)
                        answer3 = gr.Textbox(
                            label="Your Answer",
                            placeholder="Type your answer here...",
                            visible=False,
                            interactive=True,
                            lines=2
                        )
                    
                    process_answers_button = gr.Button("✅ Submit Answers", visible=False, variant="secondary")
                    answers_output = gr.Textbox(
                        label="Answer Processing Status", 
                        interactive=False,
                        max_lines=2
                    )
                
                # Research Progress Section
                gr.Markdown("### 🔬 Research Progress", elem_classes=["section-header"])
                
                with gr.Row():
                    with gr.Column():
                        research_output = gr.Textbox(
                            label="Live Research Log", 
                            interactive=False, 
                            max_lines=15,
                            info="Real-time search progress and AI decisions"
                        )
                    with gr.Column():
                        keywords_output = gr.Textbox(
                            label="Generated Keywords", 
                            interactive=False,
                            max_lines=8,
                            info="Search terms being used"
                        )
                
                # Final Report Section
                gr.Markdown("### 📑 Research Report", elem_classes=["section-header"])
                
                with gr.Row():
                    with gr.Column(scale=3):
                        report_markdown = gr.Markdown(
                            "Report will appear here after research is complete...",
                            label="Final Research Report"
                        )
                    with gr.Column(scale=1):
                        report_status = gr.Textbox(
                            label="Report Status", 
                            interactive=False,
                            max_lines=3
                        )
                        report_download = gr.File(
                            label="📥 Download Results",
                            visible=False
                        )
        
        # Store questions in state
        questions_state = gr.State([])
        
        # Enhanced question display function
        def update_questions_display(questions_data, output_text):
            if not questions_data or len(questions_data) == 0:
                return [
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                    gr.update(visible=False), questions_data
                ]

            # Ensure we have up to 3 questions
            questions = questions_data[:3]
            while len(questions) < 3:
                questions.append({"question": "", "options": []})

            # Format questions with better styling
            def format_question_with_options(q, num):
                if not q["question"]:
                    return ""

                question_text = f"**Question {num}:** {q['question']}"

                if q["options"]:
                    options_text = "\n\n**Options:**\n"
                    for i, option in enumerate(q["options"]):
                        options_text += f"**{chr(97+i)}.** {option}\n"
                    question_text += options_text

                return question_text

            q1_text = format_question_with_options(questions[0], 1)
            q2_text = format_question_with_options(questions[1], 2)
            q3_text = format_question_with_options(questions[2], 3)

            # Determine visibility
            q1_visible = bool(questions[0]["question"])
            q2_visible = bool(questions[1]["question"])
            q3_visible = bool(questions[2]["question"])
            process_visible = q1_visible

            return [
                gr.update(visible=q1_visible), gr.update(value=q1_text, visible=q1_visible), gr.update(visible=q1_visible),
                gr.update(visible=q2_visible), gr.update(value=q2_text, visible=q2_visible), gr.update(visible=q2_visible),
                gr.update(visible=q3_visible), gr.update(value=q3_text, visible=q3_visible), gr.update(visible=q3_visible),
                gr.update(visible=process_visible), questions_data
            ]
        
        # Enhanced status updates
        def update_status(message):
            return f"**Status:** {message}"
        
        # Event handlers with status updates
        def init_agent_with_status(provider, model):
            success, message = initialize_agent(provider, model)
            status = "✅ Agent Ready" if success else "❌ Initialization Failed"
            return message, update_status(status)
        
        def generate_questions_with_status(topic):
            if not topic.strip():
                return "Please enter a research topic first", [], update_status("⚠️ Topic Required")
            
            output, questions = generate_questions(topic)
            status = "✅ Questions Generated" if questions else "❌ Question Generation Failed"
            return output, questions, update_status(status)
        
        def process_answers_with_status(answer1, answer2, answer3):
            result = process_answers(answer1, answer2, answer3)
            if "Successfully recorded" in result:
                status = "✅ Answers Recorded"
            else:
                status = "❌ Answer Processing Failed"
            return result, update_status(status)
        
        def perform_research_with_status(breadth, depth, extract_content, use_adaptive_search, max_iterations):
            max_iter = int(max_iterations)
            
            output, keywords = perform_research(breadth, depth, extract_content, use_adaptive_search, max_iter)
            if "Error" not in output:
                status = "✅ Research Complete"
            else:
                status = "❌ Research Failed"
            return output, keywords, update_status(status)
        
        def generate_report_with_status():
            report, download, status_msg = generate_final_report()
            if download:
                status = "✅ Report Generated"
                download_visible = True
            else:
                status = "❌ Report Generation Failed"
                download_visible = False
            return report, download if download_visible else None, status_msg, update_status(status), gr.update(visible=download_visible)

        # Connect all components
        init_button.click(
            init_agent_with_status,
            inputs=[provider_dropdown, model_textbox],
            outputs=[init_output, status_display]
        )

        generate_questions_button.click(
            generate_questions_with_status,
            inputs=[topic_textbox],
            outputs=[questions_output, questions_state, status_display]
        ).then(
            update_questions_display,
            inputs=[questions_state, questions_output],
            outputs=[
                question1_group, question1_text, answer1,
                question2_group, question2_text, answer2,
                question3_group, question3_text, answer3,
                process_answers_button, questions_state
            ]
        )

        process_answers_button.click(
            process_answers_with_status,
            inputs=[answer1, answer2, answer3],
            outputs=[answers_output, status_display]
        )

        research_button.click(
            perform_research_with_status,
            inputs=[breadth_slider, depth_slider, extract_content_checkbox, use_adaptive_search_checkbox, max_iterations_slider],
            outputs=[research_output, keywords_output, status_display]
        )

        generate_report_button.click(
            generate_report_with_status,
            inputs=[],
            outputs=[report_markdown, report_download, report_status, status_display, report_download]
        )

    return demo


# Run the app
if __name__ == "__main__":
    demo = create_interface()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
