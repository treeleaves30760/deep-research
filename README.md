# Deep Research

This is a project for Deep Research, we use the duckduckgo as search engine, and the firecrawl as the content scraper.

## Features

- Topic-based research with AI-generated questions
- Interactive Q&A for focused searching
- Intelligent search term generation
- DuckDuckGo search integration
- AI-powered comprehensive report generation
- Support for multiple AI providers (Claude, OpenAI, Gemini, Ollama)
- Docker support for easy deployment
- GitHub Actions integration for CI/CD

## Install

### Option 1: Standard Installation

1. Clone the project

```sh
git clone https://github.com/treeleaves30760/deep-research.git
cd deep-research
```

2. Setup the environment

```sh
conda create -n deep_research python==3.11.10 -y
conda activate deep_research
pip install -r requirements.txt
```

3. Configure API Keys

Create a `.env` file in the project root with your AI provider API keys

> ![NOTE]
> If you are going to use ollama, then this step is not needed

```env
CLAUDE_API_KEY=your_claude_api_key
OPENAI_API_KEY=your_openai_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### Option 2: Docker Installation

1. Clone the project

```sh
git clone https://github.com/treeleaves30760/deep-research.git
cd deep-research
```

2. Create a `.env` file (as described above)

3. Build and run with Docker Compose

```sh
docker-compose up --build
```

Alternatively, you can pull the pre-built image from Docker Hub:

```sh
# Create .env file first
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results treeleaves30760/deep-research
```

## Usage

1. Basic Usage

```sh
python src/search.py  # If using standard installation
# OR
docker-compose up     # If using Docker
```

2. Follow the interactive prompts:
   - Enter your research topic
   - Answer the AI-generated questions
   - Answer the breadth and depth of the search
   - Wait for the search and report generation
   - Review the comprehensive report

![Model Select](./images/model_select.png)

![QA](./images/questions.png)

## Project Structure

```bash
deep-research/
├── LICENSE
├── README.md
├── .env.example
├── .gitignore
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
├── .github/
│   └── workflows/
│       └── docker-build.yml  # GitHub Actions workflow
├── images
│   ├── model_select.png
│   └── questions.png
├── requirements.txt
├── results
└── src
    ├── ai_provider
    │   ├── ai_provider.py
    │   └── ollama_test.py
    ├── search.py
    ├── content_extract
    │   └── website_to_markdown.py
    └── search_engine
        ├── bing_search.py
        ├── duckduckgo_search.py
        └── search_test.py
```

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

## Docker Deployment

### Building the Docker Image Locally

```sh
docker build -t deep-research .
```

### Running the Docker Container

```sh
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results deep-research
```

### Environment Variables

When running with Docker, you can pass environment variables in several ways:

1. Using a `.env` file with docker-compose
2. Using the `--env-file` flag with docker run
3. Directly with `-e` flag:

```sh
docker run -it -e CLAUDE_API_KEY=your_key -e OPENAI_API_KEY=your_key -v $(pwd)/results:/app/results deep-research
```

## GitHub Actions

This repository includes a GitHub Actions workflow that automatically builds and pushes the Docker image to Docker Hub whenever changes are pushed to the main branch.

To use this feature:

1. Fork the repository
2. Add the following secrets to your GitHub repository:
   - `DOCKER_HUB_USERNAME`: Your Docker Hub username
   - `DOCKER_HUB_TOKEN`: Your Docker Hub access token (not your password)
3. Push changes to the main branch to trigger the workflow

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
