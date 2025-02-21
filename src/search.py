from typing import List, Dict, Any
from ai_provider.ai_provider import chat, AIProvider, AIProviderFactory
from duckduckgo_search import search
import os
from dotenv import load_dotenv


class DeepSearchAgent:
    def __init__(self, ai_provider: str = "claude", model: str = "claude-3-sonnet"):
        load_dotenv()
        self.ai_provider = ai_provider
        self.model = model
        self.api_key = os.getenv(f"{ai_provider.upper()}_API_KEY")

    def generate_questions(self, topic: str) -> List[Dict[str, Any]]:
        """Generate relevant questions for the topic using LLM"""
        prompt = f"""Given the topic '{topic}', generate 3-5 important questions that would help understand it better.
        Format each question with 3-4 multiple choice options.
        Return the response in this format:
        1. Question: [question text]
           Options:
           a) [option text]
           b) [option text]
           c) [option text]
        """

        response = chat(prompt, self.ai_provider,
                        self.model, api_key=self.api_key)
        # Parse the response into structured format
        questions = []
        current_question = {}

        for line in response.split('\n'):
            line = line.strip()
            if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                if current_question:
                    questions.append(current_question)
                current_question = {
                    'question': line[3:].strip(), 'options': []}
            elif line.startswith(('a)', 'b)', 'c)', 'd)')):
                current_question['options'].append(line[3:].strip())

        if current_question:
            questions.append(current_question)

        return questions

    def collect_search_data(self, topic: str, answers: List[str]) -> List[Dict[str, Any]]:
        """Collect search results based on topic and answers"""
        search_results = []

        # Search for main topic
        results = search(topic, limit=5)
        if results['success']:
            search_results.extend(results['data'])

        # Generate related search terms based on answers
        prompt = f"""Based on the topic '{topic}' and these answers: {answers},
        generate 3-5 related search terms that would help gather more specific information."""

        related_terms = chat(prompt, self.ai_provider,
                             self.model, api_key=self.api_key)
        for term in related_terms.split('\n'):
            term = term.strip()
            if term:
                results = search(f"{topic} {term}", limit=3)
                if results['success']:
                    search_results.extend(results['data'])

        return search_results

    def generate_report(self, topic: str, questions: List[Dict[str, Any]],
                        answers: List[str], search_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive report based on all collected data"""
        prompt = f"""Write a comprehensive report about '{topic}' based on the following:

        Questions and Answers:
        {self._format_qa(questions, answers)}

        Research Data:
        {self._format_research(search_results)}

        Format the report with clear sections, insights from the answers, and supporting information 
        from the research. Make it engaging and informative."""

        report = chat(prompt, self.ai_provider,
                      self.model, api_key=self.api_key)
        return report

    def _format_qa(self, questions: List[Dict[str, Any]], answers: List[str]) -> str:
        """Format Q&A for the prompt"""
        qa_text = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            qa_text.append(f"Q{i+1}: {q['question']}")
            qa_text.append(f"Selected Answer: {a}")
        return "\n".join(qa_text)

    def _format_research(self, search_results: List[Dict[str, Any]]) -> str:
        """Format search results for the prompt"""
        research_text = []
        for result in search_results:
            research_text.append(f"Title: {result['title']}")
            research_text.append(f"Content: {result['markdown']}\n")
        return "\n".join(research_text)


def main():
    # Initialize the deep search agent
    agent = DeepSearchAgent()

    # Get topic from user
    topic = input("Enter the topic you want to research: ")

    # Generate questions
    print("\nGenerating questions about the topic...")
    questions = agent.generate_questions(topic)

    # Collect user answers
    answers = []
    print("\nPlease answer the following questions:")
    for i, q in enumerate(questions):
        print(f"\n{i+1}. {q['question']}")
        print("Options:")
        for j, option in enumerate(q['options']):
            print(f"   {chr(97+j)}) {option}")
        answer = input("Your answer (enter the option letter): ")
        answers.append(q['options'][ord(answer.lower()) - ord('a')])

    # Collect search data
    print("\nGathering research data...")
    search_results = agent.collect_search_data(topic, answers)

    # Generate report
    print("\nGenerating comprehensive report...")
    report = agent.generate_report(topic, questions, answers, search_results)

    print("\nFinal Report:")
    print("=" * 80)
    print(report)
    print("=" * 80)


if __name__ == "__main__":
    main()
