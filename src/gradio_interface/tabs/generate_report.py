import gradio as gr
import os
import tempfile
import shutil
import time
import io
import sys
from ..state import AGENT, CURRENT_TOPIC, CURRENT_ANSWERS, CURRENT_SEARCH_RESULTS
from ..utils import clean_rich_output


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


def create_generate_report_tab():
    with gr.Tab("4. Generate Report"):
        generate_report_button = gr.Button("Generate Final Report")
        with gr.Row():
            with gr.Column(scale=2):
                report_markdown = gr.Markdown(
                    label="Final Research Report")
            with gr.Column(scale=1):
                report_status = gr.Textbox(
                    label="Report Status", interactive=False)
                report_download = gr.File(label="Download Results")

    return {
        "generate_report_button": generate_report_button,
        "report_markdown": report_markdown,
        "report_status": report_status,
        "report_download": report_download
    }
