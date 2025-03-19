# Deep Research: Fully Local Deep Search & Report Generation

Deep Research is a fully local deep search system that leverages DuckDuckGo for search and Firecrawl for content scraping. This repository is built to operate entirely on your local machine, ensuring privacy and complete control over your research data. With our innovative design, you can generate extensive, in-depth reports that can exceed 10,000 tokens in length!

## Key Features

- **Fully Local Implementation:** No external servers required. Every component runs on your local machine.
- **In-depth Research:** Topic-based search enhanced by AI-generated questions to guide your inquiry.
- **Interactive Q&A:** Refine your search with an intuitive Q&A interface.
- **Intelligent Search Term Generation:** Utilize local and AI-powered techniques to craft effective search queries.
- **DuckDuckGo Integration:** Leverage the privacy and reliability of DuckDuckGo for your search needs.
- **Extended Report Generation:** Produce detailed reports that can exceed 10K tokens, perfect for deep research projects.
- **Multiple AI Provider Support:** Choose from local Ollama (no API key needed), Claude, OpenAI, or Gemini.
- **Docker & CI/CD Ready:** Easy deployment with Docker and automated workflows with GitHub Actions.

## Installation & Usage

Deep Research offers several ways to quickly get started, whether you prefer using Docker or running the application locally via Python. Choose from the following options:

### Use Pre-Built Image from Docker Hub

The image is automatically built and pushed to Docker Hub via GitHub Actions. You can pull the latest pre-built image directly:

```sh
docker pull treeleaves30760/deep-research
```

Then run the container:

```sh
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results treeleaves30760/deep-research
```

### Option A: Docker Quick Start

1. Clone the repository:

```sh
git clone https://github.com/treeleaves30760/deep-research.git
cd deep-research
```

2. **Using Docker Compose:** Build and run the application in one step:

```sh
docker-compose up --build
```

3. **Alternatively, using a pre-built Docker image:** (Ensure you have created a `.env` file if using remote AI providers)

```sh
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results deep-research
```

### Option B: Local Python Installation

1. Clone the repository:

```sh
git clone https://github.com/treeleaves30760/deep-research.git
cd deep-research
```

2. Set up your Python environment:

```sh
conda create -n deep_research python==3.11.10 -y
conda activate deep_research
pip install -r requirements.txt
```

3. Launch the application:

```sh
python src/search.py
```

### Option C: Docker Build Locally

1. Clone the repository:

```sh
git clone https://github.com/treeleaves30760/deep-research.git
cd deep-research
```

2. Build the Docker image:

```sh
docker build -t deep-research .
```

3. Run the Docker container:

```sh
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results deep-research
```

Once running, follow the interactive prompts:
- Enter your research topic.
- Answer AI-generated questions to tailor your research.
- Define the breadth and depth of the search.
- Wait as the system scrapes content and generates a comprehensive report that can exceed 10,000 tokens.

## Project Structure

```
deep-research/
├── LICENSE
├── README.md                # This file
├── .env.example
├── .gitignore
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── .github/
│   └── workflows/
│       └── docker-build.yml # GitHub Actions workflow
├── images/
│   ├── model_select.png
│   └── questions.png
├── requirements.txt
├── results/                 # Generated reports
└── src/
    ├── ai_provider/
    │   ├── ai_provider.py
    │   └── ollama_test.py  # Local provider implementation
    ├── search.py
    ├── content_extract/
    │   └── website_to_markdown.py
    └── search_engine/
        ├── bing_search.py
        ├── duckduckgo_search.py
        └── search_test.py
```

## AI Provider Options

Deep Research supports a variety of AI providers:

- **Ollama (Local):** Ideal for a completely local environment — no API key required.
- **Claude (Default):**
  - Models: claude-3-opus, claude-3-sonnet, claude-3-haiku.
  - Requires: CLAUDE_API_KEY.
- **OpenAI:**
  - Models: gpt-3.5-turbo, gpt-4.
  - Requires: OPENAI_API_KEY.
- **Gemini:**
  - Model: gemini-pro.
  - Requires: GEMINI_API_KEY.

## Customization

Adjust system behavior in `src/search.py` including:

- Number of AI-generated questions.
- Search result limits.
- Choice of AI provider and model.
- Report format — enabling detailed reports exceeding 10K tokens.

## Docker Deployment

### Building the Docker Image Locally

```sh
docker build -t deep-research .
```

### Running the Docker Container

```sh
docker run -it --env-file .env -v $(pwd)/results:/app/results -v $(pwd)/search_results:/app/search_results deep-research
```

### Managing Environment Variables

Pass environment variables via:
- A `.env` file (with docker-compose)
- The `--env-file` flag with Docker run
- Directly using the `-e` flag, for example:

```sh
docker run -it -e CLAUDE_API_KEY=your_key -e OPENAI_API_KEY=your_key -v $(pwd)/results:/app/results deep-research
```

## GitHub Actions

Our GitHub Actions workflow automatically builds and pushes the Docker image to Docker Hub upon commits to the main branch. To set this up:

1. Fork the repository.
2. Configure the following secrets in your GitHub repository:
   - DOCKER_HUB_USERNAME
   - DOCKER_HUB_TOKEN (use an access token, not your password)
3. Push changes to trigger the workflow.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch:

```sh
git checkout -b feature/your-feature
```

3. Commit your changes:

```sh
git commit -m 'Add new feature'
```

4. Push your branch:

```sh
git push origin feature/your-feature
```

5. Open a pull request for review.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
