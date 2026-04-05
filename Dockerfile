# Use a lightweight python image
FROM python:3.11-slim

# Install system dependencies for building certain packages (like easyocr)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Set up the working directory inside the container
WORKDIR /app

# Copy dependency definitions
COPY pyproject.toml uv.lock ./

# Sync dependencies using uv. We use --no-dev if you only want production dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the project files
COPY . .

# Expose port (Hugging Face Spaces default to 7860)
ENV PORT=7860
EXPOSE 7860

# Command to run the app using uvicorn out of the src directory
# Using exec form (JSON array) and hardcoding 7860 for reliability
CMD ["uv", "run", "uvicorn", "main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "7860"]
