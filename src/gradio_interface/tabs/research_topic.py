import gradio as gr
import io
from contextlib import redirect_stdout
from ..state import AGENT, CURRENT_TOPIC, CURRENT_QUESTIONS, CURRENT_ANSWERS
from ..utils import clean_rich_output


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


def create_research_topic_tab():
    with gr.Tab("2. Define Research Topic"):
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

    return {
        "topic_textbox": topic_textbox,
        "generate_questions_button": generate_questions_button,
        "questions_output": questions_output,
        "question1_label": question1_label,
        "question1_text": question1_text,
        "answer1": answer1,
        "question2_label": question2_label,
        "question2_text": question2_text,
        "answer2": answer2,
        "question3_label": question3_label,
        "question3_text": question3_text,
        "answer3": answer3,
        "process_answers_button": process_answers_button,
        "answers_output": answers_output,
        "questions_state": questions_state
    }
