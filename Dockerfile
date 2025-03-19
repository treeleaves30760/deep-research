FROM python:3.11-slim

WORKDIR /app

# Install Chrome for Selenium
RUN if [ "$(dpkg --print-architecture)" = "amd64" ]; then \
  apt-get update && apt-get install -y wget gnupg unzip && \
  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
  echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list && \
  apt-get update && apt-get install -y google-chrome-stable && \
  apt-get clean && rm -rf /var/lib/apt/lists/*; \
  else \
  echo "Skipping google-chrome installation on non-amd64 architecture"; \
  fi

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directories for results
RUN mkdir -p results search_results

# Set environment variables (to be overridden at runtime)
ENV CLAUDE_API_KEY=""
ENV OPENAI_API_KEY=""
ENV GEMINI_API_KEY=""

# Run the application
ENTRYPOINT ["python", "src/search.py"] 