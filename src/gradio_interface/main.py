import gradio as gr
from src.gradio_interface.tabs.initialize import create_initialize_tab, initialize_agent
from src.gradio_interface.tabs.research_topic import (
    create_research_topic_tab,
    generate_questions,
    process_answers,
    update_questions_display
)
from src.gradio_interface.tabs.perform_research import create_perform_research_tab, perform_research
from src.gradio_interface.tabs.generate_report import create_generate_report_tab, generate_final_report


def create_interface():
    with gr.Blocks(title="DeepSearch Research Agent") as demo:
        gr.Markdown("# DeepSearch Research Agent")
        gr.Markdown(
            "This web interface allows you to perform deep research on any topic using advanced search techniques and AI assistance.")

        # Create all tabs
        init_components = create_initialize_tab()
        research_topic_components = create_research_topic_tab()
        perform_research_components = create_perform_research_tab()
        generate_report_components = create_generate_report_tab()

        # Connect components
        init_components["init_button"].click(
            initialize_agent,
            inputs=[init_components["provider_dropdown"],
                    init_components["model_textbox"]],
            outputs=[init_components["init_output"]]
        )

        # Update the question display workflow with proper state management
        research_topic_components["generate_questions_button"].click(
            generate_questions,
            inputs=[research_topic_components["topic_textbox"]],
            outputs=[research_topic_components["questions_output"],
                     research_topic_components["questions_state"]]
        ).then(
            update_questions_display,
            inputs=[research_topic_components["questions_state"],
                    research_topic_components["questions_output"]],
            outputs=[
                research_topic_components["question1_label"], research_topic_components[
                    "question1_text"], research_topic_components["answer1"],
                research_topic_components["question2_label"], research_topic_components[
                    "question2_text"], research_topic_components["answer2"],
                research_topic_components["question3_label"], research_topic_components[
                    "question3_text"], research_topic_components["answer3"],
                research_topic_components["process_answers_button"], research_topic_components["questions_state"]
            ]
        )

        research_topic_components["process_answers_button"].click(
            process_answers,
            inputs=[
                research_topic_components["answer1"],
                research_topic_components["answer2"],
                research_topic_components["answer3"]
            ],
            outputs=[research_topic_components["answers_output"]]
        )

        perform_research_components["research_button"].click(
            perform_research,
            inputs=[
                perform_research_components["breadth_slider"],
                perform_research_components["depth_slider"],
                perform_research_components["extract_content_checkbox"]
            ],
            outputs=[
                perform_research_components["research_output"],
                perform_research_components["keywords_output"]
            ]
        )

        generate_report_components["generate_report_button"].click(
            generate_final_report,
            inputs=[],
            outputs=[
                generate_report_components["report_markdown"],
                generate_report_components["report_download"],
                generate_report_components["report_status"]
            ]
        )

    return demo


def launch_app():
    demo = create_interface()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    launch_app()
