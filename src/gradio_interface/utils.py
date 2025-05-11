import re
import io
import sys
from contextlib import redirect_stdout


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


def capture_output(func, *args, **kwargs):
    """Capture stdout output from a function call"""
    old_stdout = sys.stdout
    redirect_output = io.StringIO()
    sys.stdout = redirect_output

    try:
        result = func(*args, **kwargs)
        output = redirect_output.getvalue()
        return result, output
    finally:
        sys.stdout = old_stdout
