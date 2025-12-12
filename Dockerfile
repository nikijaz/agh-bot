FROM python:3.13-slim AS base
# UV package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Compile Python bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1
# Set up application directory
WORKDIR /app

FROM base AS dev
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project
# Copy application code
COPY . .
# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen
# Start the watchdog
CMD ["uv", "run", "--no-sync", "watchmedo", "auto-restart", "--directory=src", "--pattern=*.py", "--recursive", "--debug-force-polling", "--no-restart-on-command-exit", "--", "python", "-m", "agh_bot"]

FROM base AS prod
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
# Copy application code
COPY . .
# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev
# Start the bot
CMD ["uv", "run", "--no-sync", "python", "-m", "agh_bot"]
