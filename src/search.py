from typing import List, Dict, Any, Optional
from ai_provider import chat
from duckduckgo_search import search
import os
from dotenv import load_dotenv


class DeepSearchAgent:
    def __init__(self, ai_provider: str = "claude", model: str = "claude-3-sonnet"):
        load_dotenv()
        self.ai_provider = ai_provider
        self.model = model
        self.api_key = os.getenv(f"{ai_provider.upper()}_API_KEY")

    def generate_initial_questions(self, topic: str) -> List[Dict[str, Any]]:
        """Generate initial questions to understand user's research focus"""
        prompt = f"""Given the topic '{topic}', generate 3 important questions that would help understand 
        which specific aspect the user wants to research. Each question should have 3-4 multiple choice options.
        
        Format example:
        1. Question: What specific aspect of [topic] interests you most?
           Options:
           a) [specific area 1]
           b) [specific area 2]
           c) [specific area 3]
        """

        response = chat(prompt, self.ai_provider,
                        self.model, api_key=self.api_key)
        return self._parse_questions(response)

    def _parse_questions(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured question format"""
        questions = []
        current_question = {}

        for line in response.split('\n'):
            line = line.strip()
            if line.startswith(('1.', '2.', '3.')):
                if 'Question:' in line:
                    if current_question:
                        questions.append(current_question)
                    current_question = {
                        'question': line[line.index('Question:') + 9:].strip(),
                        'options': []
                    }
            elif line.startswith(('a)', 'b)', 'c)', 'd)')):
                current_question['options'].append(line[3:].strip())

        if current_question:
            questions.append(current_question)

        return questions

    def generate_search_keywords(self, topic: str, answers: List[str], breadth: int) -> List[str]:
        """Generate search keywords based on topic and user answers"""
        prompt = f"""Based on the topic '{topic}' and these specific interests: {answers},
        generate {breadth} specific search keywords or phrases that would help gather targeted information.
        Each keyword should be focused and specific.
        Format: Return only the keywords, one per line."""

        response = chat(prompt, self.ai_provider,
                        self.model, api_key=self.api_key)
        return [kw.strip() for kw in response.split('\n') if kw.strip()]

    def deep_search(self, topic: str, keywords: List[str], depth: int) -> List[Dict[str, Any]]:
        """Perform deep search with iterative refinement"""
        all_results = []
        current_keywords = keywords.copy()

        for _ in range(depth):
            # Search for each current keyword
            for keyword in current_keywords:
                results = search(f"{topic} {keyword}", limit=3)
                if results['success']:
                    all_results.extend(results['data'])

            if _ < depth - 1:  # Don't generate new keywords on last iteration
                # Generate new keywords based on current search results
                new_keywords = self._generate_refined_keywords(
                    topic, all_results, len(current_keywords))
                current_keywords = new_keywords

        return all_results

    def _generate_refined_keywords(self, topic: str, search_results: List[Dict[str, Any]], num_keywords: int) -> List[str]:
        """Generate refined keywords based on search results"""
        content_summary = "\n".join([f"Title: {r['title']}\nContent: {r['markdown']}"
                                     for r in search_results[:5]])  # Limit to prevent token overflow

        prompt = f"""Based on these search results about '{topic}':

        {content_summary}

        Generate {num_keywords} new, more specific search keywords that would help explore deeper aspects 
        revealed in these results. Focus on interesting patterns or concepts that deserve further investigation.
        Format: Return only the keywords, one per line."""

        response = chat(prompt, self.ai_provider,
                        self.model, api_key=self.api_key)
        return [kw.strip() for kw in response.split('\n') if kw.strip()]

    def generate_report(self, topic: str, focus_areas: List[str],
                        search_results: List[Dict[str, Any]]) -> str:
        """Generate comprehensive research report"""
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

        return chat(prompt, self.ai_provider, self.model, api_key=self.api_key)

    def _organize_search_results(self, search_results: List[Dict[str, Any]]) -> str:
        """Organize and summarize search results for report generation"""
        # Remove duplicates and organize by relevance
        unique_results = []
        seen_urls = set()

        for result in search_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)

        # Format for the prompt
        summary = []
        for i, result in enumerate(unique_results, 1):
            summary.append(f"Source {i}:")
            summary.append(f"Title: {result['title']}")
            summary.append(f"Content: {result['markdown']}\n")

        return "\n".join(summary)


def main():
    # Initialize the agent
    agent = DeepSearchAgent()

    # Get topic
    topic = input("Enter the topic you want to research: ")

    # Generate and ask initial questions
    print("\nLet's narrow down your research focus...")
    questions = agent.generate_initial_questions(topic)

    answers = []
    for i, q in enumerate(questions):
        print(f"\n{i+1}. {q['question']}")
        print("Options:")
        for j, option in enumerate(q['options']):
            print(f"   {chr(97+j)}) {option}")
        answer = input("Your answer (enter option letter): ")
        answers.append(q['options'][ord(answer.lower()) - ord('a')])

    # Get search parameters
    breadth = int(input(
        "\nEnter the breadth of research (number of parallel search paths, e.g., 3-5): "))
    depth = int(
        input("Enter the depth of research (number of iterative searches, e.g., 2-4): "))

    # Generate initial keywords and perform deep search
    print("\nGenerating search keywords...")
    keywords = agent.generate_search_keywords(topic, answers, breadth)

    print("\nPerforming deep search...")
    search_results = agent.deep_search(topic, keywords, depth)

    # Generate final report
    print("\nGenerating comprehensive report...")
    report = agent.generate_report(topic, answers, search_results)

    print("\nFinal Research Report:")
    print("=" * 80)
    print(report)
    print("=" * 80)


if __name__ == "__main__":
    main()
