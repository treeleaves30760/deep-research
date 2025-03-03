from typing import List, Dict, Any, Optional
from ai_provider.ai_provider import chat
from search_engine.duckduckgo_search import search
import os
import json
import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import re

# Import the WebsiteToMarkdown converter
from content_extract.website_to_markdown import WebsiteToMarkdown


# Initialize Rich console
console = Console()


class DeepSearchAgent:
    def __init__(self, ai_provider: str = "ollama", model: str = "deepseek-r1"):
        load_dotenv()
        self.ai_provider = ai_provider
        self.model = model
        if ai_provider != "ollama":
            self.api_key = os.getenv(f"{ai_provider.upper()}_API_KEY")
        else:
            self.api_key = None

        # Initialize log storage
        self.log_data = {
            "llm_interactions": [],
            "search_results": [],
            "answers": [],
            "keywords": [],
            "report": "",
            "webpage_contents": []  # Store webpage markdown content
        }

        # Initialize WebsiteToMarkdown converter
        self.markdown_converter = WebsiteToMarkdown(headless=True)

    def _log_llm_interaction(self, prompt: str, response: str):
        """Log LLM interaction for detailed reporting"""
        interaction = {
            "timestamp": datetime.datetime.now().isoformat(),
            "provider": self.ai_provider,
            "model": self.model,
            "prompt": prompt,
            "response": response
        }
        self.log_data["llm_interactions"].append(interaction)

        # Display in console
        console.print(Panel(f"[bold blue]Prompt to {self.ai_provider}/{self.model}:[/]",
                            expand=False, border_style="blue"))
        console.print(Syntax(prompt, "markdown",
                      theme="monokai", line_numbers=True))
        console.print()

        console.print(Panel(f"[bold green]Response from {self.ai_provider}/{self.model}:[/]",
                            expand=False, border_style="green"))
        console.print(Markdown(response))
        console.print()

    def _call_llm(self, prompt: str) -> str:
        """Centralized method to call LLM and log interactions"""
        with Progress(
            SpinnerColumn(),
            TextColumn(
                f"[bold green]Querying {self.ai_provider}/{self.model}..."),
            transient=True,
        ) as progress:
            progress.add_task("querying", total=None)

            # Call chat with or without api_key based on provider
            if self.ai_provider == "ollama":
                response = chat(prompt, self.ai_provider, self.model)
            else:
                response = chat(prompt, self.ai_provider,
                                self.model, api_key=self.api_key)

        # Log the interaction
        self._log_llm_interaction(prompt, response)

        return response

    def generate_initial_questions(self, topic: str) -> List[Dict[str, Any]]:
        """Generate initial questions to understand user's research focus"""
        console.print(
            f"[bold cyan]Generating initial questions for topic:[/] {topic}")

        prompt = f"""Given the topic '{topic}', generate 3 important questions that would help understand 
        which specific aspect the user wants to research. Each question should have 3-4 multiple choice options.
        
        Format example:
        1. Question: What specific aspect of [topic] interests you most?
           Options:
           a) [specific area 1]
           b) [specific area 2]
           c) [specific area 3]
        """

        response = self._call_llm(prompt)
        return self._parse_questions(response)

    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured question format - optimized for numbered questions with lettered options"""
        questions = []
        current_question = None
        current_options = []

        # Remove any thinking or system outputs that might be enclosed in angle brackets
        response = re.sub(r'<.*?>.*?</.*?>', '', response, flags=re.DOTALL)

        # Process each line
        for line in response.strip().split('\n'):
            line = line.strip()
            if not line:  # Skip empty lines
                continue

            # Match numbered questions: "1. Question: What specific..."
            question_match = re.match(
                r'^\d+\.\s*(?:Question:?\s*)?(.+)$', line)
            if question_match:
                # If we already have a question with options, add it to results
                if current_question and current_options:
                    questions.append({
                        'question': current_question,
                        'options': current_options
                    })
                    current_options = []

                # Start a new question
                current_question = question_match.group(1).strip()
                continue

            # Match "Options:" header - just skip it
            if line.lower() == 'options:':
                continue

            # Match lettered options: "a) Option text" or "a. Option text"
            option_match = re.match(r'^([a-z][\)\.:])\s*(.+)$', line)
            if option_match and current_question:
                option_text = option_match.group(2).strip()
                current_options.append(option_text)
                continue

        # Add the last question if we have one
        if current_question and current_options:
            questions.append({
                'question': current_question,
                'options': current_options
            })

        return questions

    def generate_search_keywords(self, topic: str, answers: List[str], breadth: int) -> List[str]:
        """Generate search keywords based on topic and user answers"""
        console.print(f"[bold cyan]Generating search keywords based on:[/]")
        console.print(f"  Topic: {topic}")
        console.print(f"  User interests: {', '.join(answers)}")
        console.print(f"  Desired breadth: {breadth} keywords")

        prompt = f"""Based on the topic '{topic}' and these specific interests: {answers},
        generate {breadth} specific search keywords or phrases that would help gather targeted information.
        Each keyword should be focused and specific.
        
        IMPORTANT: Format each keyword by wrapping it with <search_words> tags like this:
        <search_words>keyword or phrase</search_words>
        
        Return only the keywords, one per line with the tags."""

        response = self._call_llm(prompt)

        # Parse keywords with search_words tags
        search_words_pattern = r'<search_words>(.*?)</search_words>'
        # Find all matches
        matches = re.findall(search_words_pattern, response)

        # If no matches found, try to parse line by line
        if not matches:
            keywords = [kw.strip()
                        for kw in response.split('\n') if kw.strip()]
            # Wrap each keyword with search_words tags if they don't have them already
            keywords = [
                f"<search_words>{kw}</search_words>" for kw in keywords]
        else:
            # Use the extracted matches and wrap them again in search_words tags
            keywords = [
                f"<search_words>{match}</search_words>" for match in matches]

        # Limit to requested breadth
        keywords = keywords[:breadth]

        # Store keywords
        self.log_data["keywords"] = keywords

        return keywords

    def deep_search(self, topic: str, keywords: List[str], depth: int, extract_content: bool = True) -> List[Dict[str, Any]]:
        """Perform deep search with iterative refinement and optional webpage content extraction"""
        import time
        import random

        all_results = []
        current_keywords = keywords.copy()

        for iteration in range(depth):
            console.print(
                f"[bold magenta]Search iteration {iteration+1}/{depth}[/]")

            # Search for each current keyword
            for i, keyword in enumerate(current_keywords):
                # Extract the keyword from the search_words tags if present
                search_words_pattern = r'<search_words>(.*?)</search_words>'
                search_words_match = re.search(search_words_pattern, keyword)

                if search_words_match:
                    display_keyword = search_words_match.group(1).strip()
                    search_query = f"{topic} {display_keyword}"
                else:
                    display_keyword = keyword
                    search_query = f"{topic} {display_keyword}"

                console.print(
                    f"  [bold]Keyword {i+1}/{len(current_keywords)}:[/] {display_keyword}")
                console.print(f"  [dim]Search query: {search_query}[/dim]")

                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[bold yellow]Searching...[/]"),
                    transient=True,
                ) as progress:
                    progress.add_task("searching", total=None)
                    results = search(search_query, limit=3)

                if results['success']:
                    console.print(
                        f"    [green]Found {len(results['data'])} results[/]")
                    for j, result in enumerate(results['data']):
                        console.print(
                            f"      [dim]{j+1}. {result['title']} - {result['url']}[/dim]")

                    # If extract_content is True, fetch and convert webpage content to markdown
                    if extract_content:
                        self._extract_webpage_content(
                            results['data'], topic, display_keyword, iteration)

                    all_results.extend(results['data'])

                    # Store search results
                    self.log_data["search_results"].extend([
                        {
                            "keyword": display_keyword,
                            "search_query": search_query,
                            "iteration": iteration + 1,
                            "results": results['data']
                        }
                    ])
                else:
                    console.print(f"    [red]Error: {results['error']}[/red]")

                # Add random sleep between searches to avoid rate limiting
                if i < len(current_keywords) - 1:  # Don't sleep after the last keyword
                    sleep_time = random.uniform(1, 3)
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(
                            f"[bold blue]Waiting {sleep_time:.1f} seconds before next search...[/]"),
                        transient=True,
                    ) as progress:
                        progress.add_task("sleeping", total=None)
                        time.sleep(sleep_time)

            if iteration < depth - 1:  # Don't generate new keywords on last iteration
                console.print(
                    "[bold cyan]Generating refined keywords based on search results...[/]")
                # Generate new keywords based on current search results
                new_keywords = self._generate_refined_keywords(
                    topic, all_results, len(current_keywords))
                current_keywords = new_keywords

                # Store refined keywords
                self.log_data["keywords"].extend([
                    {
                        "iteration": iteration + 2,  # Next iteration
                        "keywords": new_keywords
                    }
                ])

                # Add a longer sleep between iterations
                if iteration < depth - 1:  # Don't sleep after the last iteration
                    sleep_time = random.uniform(2, 5)
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(
                            f"[bold blue]Waiting {sleep_time:.1f} seconds before next iteration...[/]"),
                        transient=True,
                    ) as progress:
                        progress.add_task("sleeping", total=None)
                        time.sleep(sleep_time)

        return all_results

    def _extract_webpage_content(self, search_results: List[Dict[str, Any]], topic: str, keyword: str, iteration: int):
        """Extract content from webpages found in search results"""
        import time
        import random

        console.print(
            f"    [bold cyan]Extracting content from search results...[/]")

        # Process each search result
        for i, result in enumerate(search_results):
            url = result['url']

            # Skip if URL is empty or invalid
            if not url or not url.startswith(('http://', 'https://')):
                console.print(
                    f"      [yellow]Skipping invalid URL: {url}[/yellow]")
                continue

            console.print(f"      [dim]Extracting content from: {url}[/dim]")

            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        f"[bold blue]Converting webpage to markdown...[/]"),
                    transient=True,
                ) as progress:
                    progress.add_task("converting", total=None)

                    # Determine if JavaScript rendering is needed
                    # Simplified heuristic: render JS for modern domains or if URL contains certain keywords
                    render_js = any(js_indicator in url.lower() for js_indicator in
                                    ['.io', 'github', 'medium', 'dev.to', 'react', 'vue', 'angular', 'app'])

                    # Extract content
                    try:
                        markdown_content = self.markdown_converter.url_to_markdown(
                            url,
                            render_js=render_js,
                            wait_time=5,  # 5 seconds wait time
                            use_readability=True  # Use readability for better extraction
                        )

                        # Store the extracted content
                        self.log_data["webpage_contents"].append({
                            "url": url,
                            "title": result['title'],
                            "topic": topic,
                            "keyword": keyword,
                            "iteration": iteration + 1,
                            "markdown": markdown_content,
                            "timestamp": datetime.datetime.now().isoformat()
                        })

                        # Update the search result to include the markdown content
                        result['full_markdown'] = markdown_content

                        console.print(
                            f"      [green]Successfully extracted content (length: {len(markdown_content)} chars)[/green]")

                    except Exception as e:
                        console.print(
                            f"      [red]Error extracting content: {str(e)}[/red]")

            except Exception as e:
                console.print(
                    f"      [red]Error processing URL {url}: {str(e)}[/red]")

            # Add random sleep between URL processing to avoid detection
            if i < len(search_results) - 1:  # Don't sleep after the last URL
                sleep_time = random.uniform(2, 4)
                with Progress(
                    SpinnerColumn(),
                    TextColumn(
                        f"[bold blue]Waiting {sleep_time:.1f} seconds before next URL...[/]"),
                    transient=True,
                ) as progress:
                    progress.add_task("sleeping", total=None)
                    time.sleep(sleep_time)

    def _generate_refined_keywords(self, topic: str, search_results: List[Dict[str, Any]], num_keywords: int) -> List[str]:
        """Generate refined keywords based on search results"""
        # Use full markdown content if available, otherwise use the snippet
        content_summary = []

        for r in search_results[:5]:  # Limit to prevent token overflow
            if 'full_markdown' in r:
                # If we have full markdown content, extract the most relevant parts
                # For brevity, just use the first 1000 characters
                content = r.get('full_markdown', '')[:1000] + "..."
            else:
                content = r.get('markdown', '')

            content_summary.append(f"Title: {r['title']}\nContent: {content}")

        content_summary_text = "\n\n".join(content_summary)

        prompt = f"""Based on these search results about '{topic}':

        {content_summary_text}

        Generate {num_keywords} new, more specific search keywords that would help explore deeper aspects 
        revealed in these results. Focus on interesting patterns or concepts that deserve further investigation.
        
        IMPORTANT: Format each keyword by wrapping it with <search_words> tags like this:
        <search_words>keyword or phrase</search_words>
        
        Return only the keywords, one per line with the tags."""

        response = self._call_llm(prompt)

        # Parse keywords with search_words tags
        search_words_pattern = r'<search_words>(.*?)</search_words>'
        # Find all matches
        matches = re.findall(search_words_pattern, response)

        # If no matches found, try to parse line by line
        if not matches:
            keywords = [kw.strip()
                        for kw in response.split('\n') if kw.strip()]
            # Wrap each keyword with search_words tags if they don't have them already
            keywords = [
                f"<search_words>{kw}</search_words>" for kw in keywords]
        else:
            # Use the extracted matches and wrap them again in search_words tags
            keywords = [
                f"<search_words>{match}</search_words>" for match in matches]

        # Limit to requested number of keywords
        keywords = keywords[:num_keywords]

        return keywords

    def generate_report(self, topic: str, focus_areas: List[str],
                        search_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive research report"""
        console.print("[bold cyan]Generating final research report...[/]")

        # Organize search results by relevance
        content_summary = self._organize_search_results(search_results)

        prompt = f"""Write a comprehensive research report about '{topic}' focusing on: {focus_areas}.

        Based on this research data:
        {content_summary}

        Structure the report with:
        1. Executive Summary
        2. Key Findings for each focus area
        3. Detailed Analysis
        4. Emerging Patterns and Insights
        5. Conclusions

        Make it detailed and analytical, citing specific findings from the research."""

        report = self._call_llm(prompt)

        # Store the report
        self.log_data["report"] = report

        return report

    def _organize_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Organize and summarize search results for report generation"""
        console.print(
            "[cyan]Organizing search results for report generation...[/]")

        # Remove duplicates and organize by relevance
        unique_results = []
        seen_urls = set()

        for result in search_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)

        console.print(
            f"[green]Using {len(unique_results)} unique sources from {len(search_results)} total results[/]")

        # Format for the prompt
        summary = []
        for i, result in enumerate(unique_results, 1):
            summary.append(f"Source {i}:")
            summary.append(f"Title: {result['title']}")

            # Use the full extracted markdown if available
            if 'full_markdown' in result:
                # Limit to a reasonable size for the prompt
                content = result['full_markdown'][:2000] + "..." if len(
                    result['full_markdown']) > 2000 else result['full_markdown']
                summary.append(f"Content: {content}\n")
            else:
                summary.append(f"Content: {result['markdown']}\n")

        return "\n".join(summary)

    def save_results(self, topic: str, output_dir: str):
        """Save all results to the specified directory"""
        # Create timestamp for filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_topic = topic.replace(" ", "-").lower()

        # Create output directory if it doesn't exist
        output_path = Path(output_dir) / f"{safe_topic}-{timestamp}"
        output_path.mkdir(parents=True, exist_ok=True)

        # Save report to markdown file
        report_path = output_path / "report.md"
        with open(report_path, "w") as f:
            f.write(f"# Research Report: {topic}\n\n")
            f.write(
                f"*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(self.log_data["report"])

        # Save extracted webpage contents separately
        if self.log_data["webpage_contents"]:
            webpages_dir = output_path / "extracted_webpages"
            webpages_dir.mkdir(exist_ok=True)

            for i, webpage in enumerate(self.log_data["webpage_contents"]):
                # Create a safe filename from the URL
                import hashlib
                url_hash = hashlib.md5(webpage["url"].encode()).hexdigest()[:8]
                safe_title = re.sub(r'[^\w\-]', '_', webpage["title"])[:50]
                filename = f"{i+1:02d}_{safe_title}_{url_hash}.md"

                with open(webpages_dir / filename, "w") as f:
                    f.write(webpage["markdown"])

        # Save all logs to JSON file
        log_path = output_path / "search_logs.json"
        with open(log_path, "w") as f:
            json.dump(self.log_data, f, indent=2)

        console.print(f"[bold green]Results saved to:[/] {output_path}")
        return str(output_path)

    def close(self):
        """Close the WebsiteToMarkdown converter"""
        if hasattr(self, 'markdown_converter'):
            self.markdown_converter.close()

    def __del__(self):
        """Ensure resources are properly released"""
        self.close()


def main():
    # Clear console and show banner
    console.clear()
    console.print(Panel("[bold cyan]DeepSearch Research Agent[/]",
                        subtitle="Enhanced with Rich Logging & Web Content Extraction",
                        expand=False))

    # Initialize the agent
    console.print("Initializing DeepSearch Agent...")
    # Let user choose provider and model
    provider_options = ["ollama", "openai", "claude", "gemini"]

    console.print("\n[bold]Available AI providers:[/]")
    for i, provider in enumerate(provider_options):
        console.print(f"{i+1}. {provider}")

    provider_choice = int(input("\nSelect provider (number): ")) - 1
    ai_provider = provider_options[provider_choice]

    # Default models per provider
    default_models = {
        "ollama": "deepseek-r1",
        "openai": "gpt-4o",
        "claude": "claude-3-sonnet",
        "gemini": "gemini"
    }

    model = input(
        f"Enter model name (default: {default_models[ai_provider]}): ")
    if not model:
        model = default_models[ai_provider]

    agent = DeepSearchAgent(ai_provider=ai_provider, model=model)

    # Get topic
    topic = input("\nEnter the topic you want to research: ")

    # Generate and ask initial questions
    console.print("\n[bold cyan]Focusing your research...[/]")
    questions = agent.generate_initial_questions(topic)

    # Check if we got valid questions
    if not questions or not any(q.get('question') for q in questions):
        console.print(
            "[yellow]Could not parse questions from LLM response. Let's try again with a more structured format...[/]")

        # Try again with a more structured format
        prompt = f"""Given the topic '{topic}', I need EXACTLY 3 important questions to understand which specific aspect the user wants to research.
        
        Please follow this EXACT format for each question:
        
        Question 1: [Question text]
        Option a: [Option text]
        Option b: [Option text]
        Option c: [Option text]
        
        Question 2: [Question text]
        Option a: [Option text]
        Option b: [Option text]
        Option c: [Option text]
        
        Question 3: [Question text]
        Option a: [Option text]
        Option b: [Option text]
        Option c: [Option text]
        """

        response = agent._call_llm(prompt)
        questions = agent._parse_questions(response)

        if not questions or not any(q.get('question') for q in questions):
            console.print(
                "[yellow]Still having trouble parsing questions. Let's create some basic questions manually.[/]")

            # Create manual fallback questions
            questions = [
                {
                    'question': f"What specific aspect of {topic} interests you most?",
                    'options': ["General overview", "Recent developments", "Practical applications", "Technical details"]
                },
                {
                    'question': f"What is your primary goal for researching {topic}?",
                    'options': ["Learning basics", "Solving a problem", "Academic research", "Personal interest"]
                },
                {
                    'question': "What depth of information are you looking for?",
                    'options': ["Beginner-friendly introduction", "Intermediate overview", "Advanced technical details", "Expert analysis"]
                }
            ]

    answers = []
    for i, q in enumerate(questions):
        console.print(Panel(f"[bold]{i+1}. {q['question']}[/]", expand=False))

        # Make sure we have options to display
        if not q['options']:
            console.print(
                "[yellow]No options found for this question. Please enter your answer directly.[/]")
            user_answer = input("Your answer: ")
            answers.append(user_answer)

            # Store user answers
            agent.log_data["answers"].append({
                "question": q['question'],
                "options": [],
                "selected": user_answer
            })
            continue

        # Display options
        console.print("Options:")
        for j, option in enumerate(q['options']):
            console.print(f"   [bold]{chr(97+j)})[/] {option}")

        # Get and validate user input
        while True:
            answer = input(
                "Your answer (enter option letter, or type your answer if none match): ").strip()

            if len(answer) == 1 and ord('a') <= ord(answer.lower()) < ord('a') + len(q['options']):
                # Valid option letter selected
                selected_option = q['options'][ord(answer.lower()) - ord('a')]
                answers.append(selected_option)

                # Store user answers
                agent.log_data["answers"].append({
                    "question": q['question'],
                    "options": q['options'],
                    "selected": selected_option
                })
                break
            elif answer:
                # User typed a custom answer
                console.print(f"[yellow]Using custom answer: {answer}[/]")
                answers.append(answer)

                # Store user answers
                agent.log_data["answers"].append({
                    "question": q['question'],
                    "options": q['options'],
                    "selected": answer
                })
                break
            else:
                console.print(
                    "[red]Please enter a valid option letter or type your answer.[/]")

    # Get search parameters
    console.print(Panel("[bold]Configure Search Parameters[/]", expand=False))
    breadth = int(input(
        "Enter the breadth of research (number of parallel search paths, e.g., 3-5): "))
    depth = int(
        input("Enter the depth of research (number of iterative searches, e.g., 2-4): "))

    # Ask if the user wants to extract webpage content
    extract_content = input(
        "Extract content from webpages? (y/n, default: y): ").strip().lower() != 'n'

    # Generate initial keywords and perform deep search
    console.print("\n[bold cyan]Beginning research process...[/]")
    keywords = agent.generate_search_keywords(topic, answers, breadth)

    console.print("\n[bold cyan]Initial keywords:[/]")
    for i, kw in enumerate(keywords):
        console.print(f"{i+1}. {kw}")

    search_results = agent.deep_search(
        topic, keywords, depth, extract_content=extract_content)

    # Generate final report
    console.print(
        Panel("[bold]Final Research Report Generation[/]", expand=False))
    report = agent.generate_report(topic, answers, search_results)

    # Create output directory and save results
    output_dir = "./results"
    agent.save_results(topic, output_dir)

    # Display report
    console.print("\n[bold green]Final Research Report:[/]")
    console.print(Panel(Markdown(report), title=f"Report: {topic}",
                        border_style="green", expand=True))

    # Clean up resources
    agent.close()


if __name__ == "__main__":
    main()
