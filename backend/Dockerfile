FROM python:3.14-slim-trixie

# uv installs dependencies from uv.lock (fast, reproducible).
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Keep the virtualenv outside /app, so mounting the source code over /app
    # in dev (for hot reload) doesn't hide the installed packages.
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first, in their own layer: Docker reuses this layer
# until pyproject.toml/uv.lock change, so code edits don't trigger reinstalls.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
