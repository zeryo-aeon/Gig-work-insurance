# Use a lightweight python image
FROM python:3.11-slim

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

# Expose port (Cloud Run sets PORT env var automatically)
ENV PORT=8000
EXPOSE 8000

# Command to run the app using uvicorn out of the src directory
# Using sh -c to ensure $PORT is evaluated correctly
CMD ["sh", "-c", "uv run uvicorn main:app --app-dir src --host 0.0.0.0 --port ${PORT:-8000}"]
