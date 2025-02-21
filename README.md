# Deep Research

This is a project for Deep Research, we use the duckduckgo as search engine, and the firecrawl as the content scraper.

## Features

- Topic-based research with AI-generated questions
- Interactive Q&A for focused searching
- Intelligent search term generation
- DuckDuckGo search integration
- AI-powered comprehensive report generation
- Support for multiple AI providers (Claude, OpenAI, Gemini, Ollama)

## Install

1. Clone the project

```sh
git clone https://github.com/yourusername/deep-research.git
cd deep-research
```

2. Setup the environment

```sh
conda create -n deep_research python==3.11.10 -y
conda activate deep_research
pip install -r requirements.txt
```

3. Configure API Keys

Create a `.env` file in the project root with your AI provider API keys:

```env
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```

## Project Structure

```bash
deep-research/
├── src/
│   ├── search.py
│   ├── duckduckgo_search.py
│   └── ai_provider/
|        └── ai_provider.py
├── requirements.txt
├── .env
└── README.md
```

## Usage

1. Basic Usage

```sh
python src/search.py
```

2. Follow the interactive prompts:
   - Enter your research topic
   - Answer the AI-generated questions
   - Wait for the search and report generation
   - Review the comprehensive report

## AI Provider Support

The system supports multiple AI providers:

1. Claude (Default)
   - Models: claude-3-opus, claude-3-sonnet, claude-3-haiku
   - Requires: CLAUDE_API_KEY

2. OpenAI
   - Models: gpt-3.5-turbo, gpt-4
   - Requires: OPENAI_API_KEY

3. Gemini
   - Models: gemini-pro
   - Requires: GEMINI_API_KEY

4. Ollama (Local)
   - Models: Based on local installation
   - No API key required

## Customization

You can customize the search behavior by modifying these parameters in `src/search.py`:

- Number of questions generated
- Search result limits
- AI provider and model selection
- Report format and structure

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
