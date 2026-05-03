FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    jq \
    make \
    nodejs \
    npm \
    shellcheck \
    tmux \
  && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
  && ln -sf /root/.local/bin/uv /usr/local/bin/uv

RUN npm install -g pnpm@latest
