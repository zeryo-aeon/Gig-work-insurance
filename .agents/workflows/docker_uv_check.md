---
description: Check if Dockerfile is compatible with uv sync and uvicorn
---

# Docker compatibility check for uv sync and uvicorn

Follow these steps to verify that the project's Dockerfile correctly installs dependencies via `uv sync` and runs the application using `uvicorn`.

// turbo
1. Check if Docker is installed.
`docker --version`

2. Check if `Dockerfile` exists.
`Test-Path Dockerfile`

3. If it exists, build the Docker image to ensure `uv sync` correctly installs dependencies from `pyproject.toml` and `uv.lock`.
`docker build -t gig-insurance-app .`

4. Run the image to verify `uvicorn` starts successfully.
`docker run -d -p 8080:7860 --name test-gig-app gig-insurance-app`

5. Check the logs of the container (wait a few seconds first) to confirm `uvicorn` is running without errors.
`docker logs test-gig-app`

6. Stop and remove the test container.
`docker stop test-gig-app`
`docker rm test-gig-app`
