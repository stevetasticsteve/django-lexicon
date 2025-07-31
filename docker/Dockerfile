FROM ghcr.io/astral-sh/uv:debian

# System dependencies
RUN apt-get update && \
    apt-get install -y hunspell-tools && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:${PYTHONPATH}"

# Copy only dependency files first for caching
COPY pyproject.toml uv.lock .python-version /app/

# Use cache to speed up dependency install
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy the rest of the source code
COPY . /app

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Create expected folders
RUN mkdir -p /app/data/exports /app/data/logs

# Collect static assets
RUN uv run manage.py collectstatic --noinput --clear

# Migrate and runserver at startup
CMD set -xe; \
    uv run manage.py migrate; \
    gunicorn config.wsgi:application --workers ${GUNICORN_WORKERS} --timeout 60 --access-logfile /app/data/logs/requests.log --error-logfile /app/data/logs/gunicorn_errors.log --bind 0.0.0.0:8000 --reload    
