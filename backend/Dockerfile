FROM python:3.15-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies separately for Docker layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# Install the application
COPY . .
RUN uv sync --locked

EXPOSE 8000

CMD ["uvicorn", "sameplate.presentation.api.main:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory"]
