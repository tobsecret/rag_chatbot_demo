FROM python:3.12-slim

# Docling and underlying libraries (like OpenCV) require several C-level graphics dependencies.
# We install them here to ensure parsing doesn't crash during extraction.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Astral's 'uv' package manager
RUN pip install uv

# Create the application directory
WORKDIR /app

# Copy dependency configuration files first to optimize layer caching
COPY pyproject.toml uv.lock* ./

# Sync dependencies (including non-editable local project)
RUN uv sync --no-dev

# Copy all source files into the backend subdirectory to preserve package structure
COPY . ./backend/

# Set PYTHONPATH to /app so that 'import backend' works correctly
ENV PYTHONPATH=/app

# Run the preload script to bake all AI models directly into the Docker image cache
# We run it directly from its location to avoid module resolution debt
RUN uv run python backend/preload_models.py

EXPOSE 8000

# Execute the FastAPI server, explicitly bound to 0.0.0.0 so it routes outside the container
CMD ["uv", "run", "fastapi", "run", "backend/main.py", "--host", "0.0.0.0", "--port", "8000"]
