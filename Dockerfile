FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --all-extras --no-dev

COPY . .

CMD ["uv", "run", "--no-project", "main.py"]
