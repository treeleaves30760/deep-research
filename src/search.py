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

# Import the content processing components
from content_processing import WebContent, ContentQualityChecker, ContentProcessor, ContentSummarizer


# Initialize Rich console
console = Console()


class DeepSearchAgent:
    def __init__(self, ai_provider: str = "ollama", model: str = "deepseek-r1", ollama_host: str = None):
        load_dotenv()
        self.ai_provider = ai_provider
        self.model = model
        self.ollama_host = ollama_host
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

        # Initialize content processing components
        self.content_processor = ContentProcessor()
        self.content_quality_checker = ContentQualityChecker()

        # Initialize content summarizer if LLM is available
        self.content_summarizer = None
        if ai_provider != "ollama":
            # Create a mock LLM client for the summarizer
            self.content_summarizer = ContentSummarizer(
                self._create_llm_client())

    def _create_llm_client(self):
        """Create a mock LLM client for the content summarizer"""
        class MockLLMClient:
            def __init__(self, agent):
                self.agent = agent

            def generate_summary(self, content, summary_type="concise"):
                """Generate a summary using the agent's LLM"""
                prompt = f"""Summarize the following content in a {summary_type} way:

                {content[:2000]}  # Limit content length to avoid token limits
                
                Provide a {summary_type} summary that captures the main points.
                """

                return self.agent._call_llm(prompt)

        return MockLLMClient(self)

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
                if self.ollama_host:
                    response = chat(prompt, self.ai_provider,
                                    self.model, host=self.ollama_host)
                else:
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

IMPORTANT: Format your response using XML-like tags as follows:

<question_1>What specific aspect of [topic] interests you most?</question_1>
<options_1>
a) [specific area 1]
b) [specific area 2]
c) [specific area 3]
</options_1>

<question_2>What is your primary goal for researching [topic]?</question_2>
<options_2>
a) [goal 1]
b) [goal 2]
c) [goal 3]
</options_2>

<question_3>What depth of information are you looking for?</question_3>
<options_3>
a) [depth level 1]
b) [depth level 2]
c) [depth level 3]
</options_3>

Make sure to:
1. Use exactly 3 questions
2. Each question should have 3-4 options
3. Use the exact tag format shown above
4. Keep questions focused and specific to the topic
5. Make options clear and distinct"""

        response = self._call_llm(prompt)
        return self._parse_questions(response)

    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured question format using XML-like tags"""
        questions = []

        # Pattern to match question and options blocks
        pattern = r'<question_(\d+)>(.*?)</question_\1>\s*<options_\1>\s*(.*?)\s*</options_\1>'

        # Find all matches
        matches = re.finditer(pattern, response, re.DOTALL)

        for match in matches:
            question_number = match.group(1)
            question_text = match.group(2).strip()
            options_text = match.group(3).strip()

            # Parse options - improved to handle multi-line options
            options = []
            # First split by lines that start with a letter followed by ) or .
            option_blocks = re.split(
                r'(?:\r?\n|\r)(?=[a-z][\)\.:]\s+)', options_text)

            for block in option_blocks:
                block = block.strip()
                if not block:
                    continue

                # Match option pattern: a) text or a. text
                option_match = re.match(
                    r'^([a-z][\)\.:]\s*)(.+)$', block, re.DOTALL)
                if option_match:
                    # Get everything after the option letter, joining any multi-line content
                    option_text = option_match.group(2).strip()
                    # Join multiple lines and normalize whitespace
                    option_text = ' '.join([line.strip()
                                           for line in option_text.split('\n')])
                    options.append(option_text)

            # Fallback for simpler line by line parsing if regex didn't work
            if not options:
                for line in options_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    # Match option pattern: a) text or a. text
                    option_match = re.match(r'^[a-z][\)\.:]\s*(.+)$', line)
                    if option_match:
                        options.append(option_match.group(1).strip())

            if question_text and options:
                questions.append({
                    'question': question_text,
                    'options': options
                })

        # If no matches found with tags, try the old parsing method as fallback
        if not questions:
            console.print(
                "[yellow]No tagged questions found, falling back to basic parsing...[/]")
            current_question = None
            current_options = []

            for line in response.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Match numbered questions
                question_match = re.match(
                    r'^\d+\.\s*(?:Question:?\s*)?(.+)$', line)
                if question_match:
                    if current_question and current_options:
                        questions.append({
                            'question': current_question,
                            'options': current_options
                        })
                        current_options = []
                    current_question = question_match.group(1).strip()
                    continue

                # Skip "Options:" header
                if line.lower() == 'options:':
                    continue

                # Match lettered options
                option_match = re.match(r'^([a-z][\)\.:])\s*(.+)$', line)
                if option_match and current_question:
                    option_text = option_match.group(2).strip()
                    current_options.append(option_text)

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

        # Calculate total number of searches based on breadth and depth
        total_searches = len(current_keywords) * depth
        console.print(
            f"[bold magenta]Starting comprehensive research with {total_searches} total searches[/]")

        for iteration in range(depth):
            console.print(
                f"[bold magenta]Research iteration {iteration+1}/{depth}[/]")
            console.print(
                f"[dim]Current breadth: {len(current_keywords)} keywords[/dim]")

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
                    f"  [bold]Researching {i+1}/{len(current_keywords)}:[/] {display_keyword}")
                console.print(f"  [dim]Search query: {search_query}[/dim]")

                with Progress(
                    SpinnerColumn(),
                    TextColumn(f"[bold yellow]Searching...[/]"),
                    transient=True,
                ) as progress:
                    progress.add_task("searching", total=None)
                    # Increased limit for more comprehensive results
                    results = search(search_query, limit=10)

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
                    "[bold cyan]Expanding research scope with refined keywords...[/]")
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

                        # Process the content using our new content processing system
                        web_content = self.content_processor.process_content(
                            url=url,
                            raw_content=markdown_content,
                            title=result['title'],
                            metadata={"source": "web", "topic": topic,
                                      "keyword": keyword, "iteration": iteration + 1}
                        )

                        # Check content quality
                        quality_metrics = self.content_quality_checker.check_quality(
                            web_content)
                        web_content.quality_metrics = quality_metrics

                        # Generate summary if summarizer is available
                        if self.content_summarizer:
                            try:
                                summary = self.content_summarizer.summarize_content(
                                    web_content.content,
                                    summary_type="concise"
                                )
                                web_content.update_summary(summary, "concise")
                                console.print(
                                    f"      [green]Generated summary (length: {len(summary)} chars)[/green]")
                            except Exception as e:
                                console.print(
                                    f"      [yellow]Error generating summary: {str(e)}[/yellow]")

                        # Store the processed content
                        self.log_data["webpage_contents"].append({
                            "url": url,
                            "title": result['title'],
                            "topic": topic,
                            "keyword": keyword,
                            "iteration": iteration + 1,
                            "markdown": markdown_content,
                            "processed_content": web_content.to_dict(),
                            "timestamp": datetime.datetime.now().isoformat()
                        })

                        # Update the search result to include the processed content
                        result['full_markdown'] = markdown_content
                        result['processed_content'] = web_content.to_dict()

                        console.print(
                            f"      [green]Successfully processed content (length: {len(markdown_content)} chars)[/green]")
                        console.print(
                            f"      [dim]Quality score: {quality_metrics.get('overall_score', 'N/A')}[/dim]")

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

    def _extract_content_between_backticks(self, text: str) -> str:
        """Extract content between triple backticks, if exists"""
        pattern = r"```(?:markdown)?\n(.*?)```"
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
        return text.strip()

    def _generate_report_structure(self, topic: str) -> str:
        """Generate the initial structure of the research report"""
        console.print("[bold cyan]Generating report structure...[/]")

        prompt = f"""Create a detailed structure for a research report about '{topic}'.
        
        The structure should include all major sections and subsections, but instead of actual content,
        use [Content Tag] as a placeholder.
        
        IMPORTANT: Wrap your response in triple backticks (```). Only the content within the backticks will be used.
        
        Example format:
        ```
        # Title
        [Content Tag]
        
        ## Abstract
        [Content Tag]
        
        ## Introduction
        [Content Tag]
        
        // ... other sections
        ```
        
        Include all necessary sections for a comprehensive academic research report, such as:
        - Background/Literature Review
        - Methodology/Methods
        - Results/Findings
        - Discussion
        - Conclusion
        - References
        
        Each section should have appropriate subsections where relevant."""

        response = self._call_llm(prompt)
        structure = self._extract_content_between_backticks(response)
        return structure

    def generate_report(self, topic: str, focus_areas: List[str], search_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive research report in stages"""
        console.print(
            "[bold cyan]Generating comprehensive research report...[/]")

        # First, generate the report structure
        report_structure = self._generate_report_structure(topic)

        # Organize search results by relevance and topic areas
        content_summary = self._organize_search_results(search_results)

        # Parse the structure to identify all [Content Tag] locations
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

        # Generate content for each section with comprehensive context
        final_report = []
        previous_content = ""
        research_context = {
            'topic': topic,
            'focus_areas': focus_areas,
            'total_sources': len(search_results),
            'key_findings': self._extract_key_findings(search_results)
        }

        for section in sections:
            section_title = ' '.join(h.lstrip('#').strip()
                                     for h in section['headers'])
            console.print(
                f"[bold cyan]Generating content for section: {section_title}[/]")

            prompt = f"""Write comprehensive content for the {section_title} section of the research report about '{topic}'.

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

            response = self._call_llm(prompt)
            section_content = self._extract_content_between_backticks(response)

            # Replace [Content Tag] with generated content
            final_section = section['content'].replace(
                '[Content Tag]', section_content)
            final_report.append(final_section)

            # Update previous content for context in next iteration
            previous_content += f"\n{section_title}:\n{section_content}\n"

        # Combine all sections
        complete_report = '\n'.join(final_report)

        # Add executive summary at the beginning
        executive_summary = self._generate_executive_summary(
            topic, research_context, complete_report)
        complete_report = f"# Executive Summary\n\n{executive_summary}\n\n{complete_report}"

        # Store the report
        self.log_data["report"] = complete_report

        return complete_report

    def _extract_key_findings(self, search_results: List[Dict[str, Any]]) -> str:
        """Extract key findings from search results"""
        prompt = f"""Based on the following research results, identify the 5 most significant findings:

        {self._organize_search_results(search_results)}

        Format each finding as a concise statement. Focus on unique insights and important discoveries.
        """

        response = self._call_llm(prompt)
        return self._extract_content_between_backticks(response)

    def _generate_executive_summary(self, topic: str, research_context: Dict[str, Any], full_report: str) -> str:
        """Generate an executive summary of the research"""
        prompt = f"""Create a comprehensive executive summary for the research report about '{topic}'.

        Research Context:
        - Topic: {research_context['topic']}
        - Focus Areas: {', '.join(research_context['focus_areas'])}
        - Total Sources: {research_context['total_sources']}
        - Key Findings: {research_context['key_findings']}

        Full Report:
        {full_report}

        IMPORTANT:
        1. Wrap your response in triple backticks (```). Only the content within the backticks will be used.
        2. Provide a clear overview of the research scope and methodology.
        3. Highlight the most significant findings and their implications.
        4. Include key recommendations or conclusions.
        5. Keep it concise but comprehensive (2-3 paragraphs).
        6. Do not include any meta-commentary or reasoning outside the backticks."""

        response = self._call_llm(prompt)
        return self._extract_content_between_backticks(response)

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

            # Use the processed content if available
            if 'processed_content' in result:
                processed = result['processed_content']
                summary.append(f"URL: {processed['url']}")

                # Add summary if available
                if processed.get('summary'):
                    summary.append(f"Summary: {processed['summary']}")

                # Add quality metrics if available
                if processed.get('quality_metrics'):
                    metrics = processed['quality_metrics']
                    summary.append(
                        f"Quality Score: {metrics.get('overall_score', 'N/A')}")

                # Add content (limited to a reasonable size)
                content = processed.get('content', '')
                if content:
                    content = content[:2000] + \
                        "..." if len(content) > 2000 else content
                    summary.append(f"Content: {content}\n")
            # Fall back to full markdown if available
            elif 'full_markdown' in result:
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

                # Save processed content as JSON if available
                if "processed_content" in webpage:
                    json_filename = f"{i+1:02d}_{safe_title}_{url_hash}.json"
                    with open(webpages_dir / json_filename, "w") as f:
                        json.dump(webpage["processed_content"], f, indent=2)

        # Save all logs to JSON file
        log_path = output_path / "search_logs.json"
        with open(log_path, "w") as f:
            json.dump(self.log_data, f, indent=2)

        # Save content quality report
        quality_report_path = output_path / "content_quality_report.md"
        with open(quality_report_path, "w") as f:
            f.write(f"# Content Quality Report: {topic}\n\n")
            f.write(
                f"*Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")

            # Collect all processed content with quality metrics
            quality_data = []
            for webpage in self.log_data["webpage_contents"]:
                if "processed_content" in webpage and "quality_metrics" in webpage["processed_content"]:
                    quality_data.append({
                        "url": webpage["url"],
                        "title": webpage["title"],
                        "quality_metrics": webpage["processed_content"]["quality_metrics"],
                        "summary": webpage["processed_content"].get("summary", "No summary available")
                    })

            # Sort by quality score (descending)
            quality_data.sort(key=lambda x: x["quality_metrics"].get(
                "overall_score", 0), reverse=True)

            # Write quality report
            f.write("## Content Quality Summary\n\n")
            f.write(f"Total processed content: {len(quality_data)}\n\n")

            f.write("## Content by Quality Score\n\n")
            for i, item in enumerate(quality_data, 1):
                f.write(f"### {i}. {item['title']}\n\n")
                f.write(f"**URL:** {item['url']}\n\n")
                f.write(
                    f"**Quality Score:** {item['quality_metrics'].get('overall_score', 'N/A')}\n\n")

                # Add summary if available
                if item.get("summary"):
                    f.write("**Summary:**\n\n")
                    f.write(f"{item['summary']}\n\n")

                # Add detailed metrics
                f.write("**Detailed Metrics:**\n\n")
                for metric, value in item["quality_metrics"].items():
                    if metric != "overall_score":
                        f.write(f"- {metric}: {value}\n")

                f.write("\n---\n\n")

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
        "ollama": "gemma3:latest",
        "openai": "gpt-4.1",
        "claude": "claude-3.5-sonnet",
        "gemini": "gemini-2.5-flash-preview-04-17"
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

    # Display questions and get answers
    answers = []
    for i, q in enumerate(questions, 1):
        console.print(f"\n[bold cyan]Question {i}:[/] {q['question']}")
        console.print("\n[bold]Options:[/]")
        for j, option in enumerate(q['options']):
            console.print(f"  {chr(97+j)}. {option}")

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

    # Ask if the user wants to generate summaries (only if LLM is available)
    generate_summaries = False
    if agent.content_summarizer:
        generate_summaries = input(
            "Generate content summaries? (y/n, default: y): ").strip().lower() != 'n'
        if generate_summaries:
            console.print(
                "[green]Content summaries will be generated for each webpage.[/]")
        else:
            console.print(
                "[yellow]Content summaries will not be generated.[/]")
    else:
        console.print(
            "[yellow]Content summaries cannot be generated with the current LLM provider.[/]")

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
