# syntax=docker/dockerfile:1.6
# AI Design Theater container image
# Provides Python runtime + Node + mermaid-cli for diagram rendering & tests.

ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    MERMAID_CLI_COMMAND="npx -y @mermaid-js/mermaid-cli" \
    PROJECTS_DIR=/app/projects

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg git build-essential ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Install Node (20.x) via NodeSource for recent mermaid-cli support
RUN bash -lc 'set -e; curl -fsSL https://deb.nodesource.com/setup_20.x | bash -' && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies first (leverage layer caching)
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install mermaid-cli globally (also gives us npx path)
RUN npm install -g @mermaid-js/mermaid-cli && \
    ln -sf /usr/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/.bin/mmdc /usr/local/bin/mmdc || true

# Create non-root user
RUN useradd -ms /bin/bash appuser

# Copy source
COPY . .
RUN chown -R appuser:appuser /app
USER appuser

# Default command runs a random design session (requires API keys unless --simulate supplied)
# Override with: docker run --rm -e OPENAI_API_KEY=... -e ANTHROPIC_API_KEY=... image python scripts/run_daily_local.py --mode random
CMD ["python", "scripts/run_daily_local.py", "--mode", "random", "--simulate"]

# Healthcheck: ensure python & mmdc available
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; import shutil; sys.exit(0 if shutil.which('mmdc') else 1)" || exit 1
