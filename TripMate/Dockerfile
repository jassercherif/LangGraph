FROM python:3.11-slim

# 1. Copy the uv binary
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_NO_CACHE=1 

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Copy the configuration and lockfile
COPY pyproject.toml uv.lock ./

# 3. Synchronize dependencies using the correct modern command
# --system installs packages directly into the container's global Python environment
# --frozen locks versions and blocks uv from modifying the uv.lock file
# --no-dev skips installing development-only tools
RUN uv sync --system --frozen --no-dev

# 4. Copy the rest of the application
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
