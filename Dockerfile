# Builder
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project --no-dev

COPY . .

RUN uv sync --frozen --no-dev

RUN mkdir -p /data \
    && ln -sf /usr/bin/python3.11 /app/.venv/bin/python \
    && sed -i 's|^home = .*|home = /usr/bin|' /app/.venv/pyvenv.cfg


# Development
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS development

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1


RUN useradd --system \
    --uid 10001 \
    --create-home \
    --shell /bin/bash \
    appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /data

#Cacheo dependencias completas
COPY pyproject.toml uv.lock ./ 
RUN uv sync --frozen --no-install-project

# Copiar el código fuente con permisos de appuser
COPY --chown=appuser:appuser . /app
RUN uv sync --frozen

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--no-access-log", "--log-config", "app/core/logging_config.json"]


# Production
FROM gcr.io/distroless/python3-debian12:nonroot AS production

WORKDIR /app

COPY --from=builder --chown=nonroot:nonroot /app/.venv /app/.venv
COPY --from=builder --chown=nonroot:nonroot /app/app /app/app
COPY --from=builder --chown=nonroot:nonroot /app/pyproject.toml /app/pyproject.toml /app/pyproject.toml
COPY --from=builder --chown=nonroot:nonroot /data /data

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-config", "app/core/logging_config.json"]
