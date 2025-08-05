# Use slim image for smaller size
FROM python:3.13-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile Python bytecode for faster startup
ENV UV_COMPILE_BYTECODE=1

# Set up application directory
WORKDIR /app

# Install Python dependencies using cached mounts for speed
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-default-groups

# Copy all application files
ADD . .

# Start the bot
CMD ["uv", "run", "--no-sync", "main.py"]
