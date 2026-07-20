# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.13.3
ARG DEBIAN_VARIANT=bookworm
ARG PYTHON_BASE_DIGEST=sha256:56a11364ffe0fee3bd60af6d6d5209eba8a99c2c16dc4c7c5861dc06261503cc
ARG UV_VERSION=0.11.29

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VARIANT}@${PYTHON_BASE_DIGEST} AS builder

ARG UV_VERSION

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

WORKDIR /build

RUN python -m pip install --no-cache-dir "uv==${UV_VERSION}"

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable

FROM python:${PYTHON_VERSION}-slim-${DEBIAN_VARIANT}@${PYTHON_BASE_DIGEST} AS runtime

LABEL org.opencontainers.image.title="workbench-mcp" \
      org.opencontainers.image.description="Secure stdio FastMCP workspace server" \
      org.opencontainers.image.source="https://github.com/bhawnapannu2701/workbench-mcp"

ENV PATH="/opt/venv/bin:${PATH}" \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    WORKSPACE_ROOT=/workspace \
    ARTIFACT_DIRECTORY=/artifacts \
    READ_ONLY_MODE=true \
    MAX_FILE_SIZE_BYTES=1048576 \
    MAX_COMMAND_SECONDS=30 \
    MAX_OUTPUT_BYTES=1048576 \
    LOG_LEVEL=INFO

RUN apt-get update \
    && apt-get install --no-install-recommends --yes ca-certificates git \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 workbench \
    && useradd --uid 10001 --gid workbench --home-dir /nonexistent --shell /usr/sbin/nologin --no-create-home workbench \
    && mkdir -p /app/scripts /workspace /artifacts /tmp/workbench-mcp \
    && chown -R workbench:workbench /app /artifacts /tmp/workbench-mcp \
    && chmod 0755 /app /workspace \
    && chmod 0775 /artifacts /tmp/workbench-mcp

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY scripts/container-smoke-test.py /app/scripts/container-smoke-test.py

USER 10001:10001

ENTRYPOINT ["workbench-mcp"]
CMD ["--transport", "stdio"]
