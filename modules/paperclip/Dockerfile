FROM node:lts-trixie-slim AS base
ARG USER_UID=1000
ARG USER_GID=1000
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates gosu curl gh git wget ripgrep python3 \
  && rm -rf /var/lib/apt/lists/* \
  && corepack enable

# Modify the existing node user/group to have the specified UID/GID to match host user
RUN usermod -u $USER_UID --non-unique node \
  && groupmod -g $USER_GID --non-unique node \
  && usermod -g $USER_GID -d /paperclip node

FROM base AS deps
WORKDIR /workspace/modules/paperclip
COPY modules/paperclip/package.json modules/paperclip/pnpm-workspace.yaml modules/paperclip/pnpm-lock.yaml modules/paperclip/.npmrc ./
COPY modules/paperclip/cli/package.json cli/
COPY modules/paperclip/server/package.json server/
COPY modules/paperclip/ui/package.json ui/
COPY modules/paperclip/packages/shared/package.json packages/shared/
COPY modules/paperclip/packages/db/package.json packages/db/
COPY modules/paperclip/packages/adapter-utils/package.json packages/adapter-utils/
COPY modules/paperclip/packages/mcp-server/package.json packages/mcp-server/
COPY modules/paperclip/packages/adapters/claude-local/package.json packages/adapters/claude-local/
COPY modules/paperclip/packages/adapters/codex-local/package.json packages/adapters/codex-local/
COPY modules/paperclip/packages/adapters/cursor-local/package.json packages/adapters/cursor-local/
COPY modules/paperclip/packages/adapters/gemini-local/package.json packages/adapters/gemini-local/
COPY modules/paperclip/packages/adapters/openclaw-gateway/package.json packages/adapters/openclaw-gateway/
COPY modules/paperclip/packages/adapters/opencode-local/package.json packages/adapters/opencode-local/
COPY modules/paperclip/packages/adapters/pi-local/package.json packages/adapters/pi-local/
COPY modules/paperclip/packages/plugins/sdk/package.json packages/plugins/sdk/
COPY modules/hermes-paperclip-adapter/package.json ../hermes-paperclip-adapter/
COPY modules/paperclip/patches/ patches/

RUN pnpm install --frozen-lockfile

FROM base AS build
WORKDIR /workspace/modules/paperclip
COPY --from=deps /workspace /workspace
COPY modules/paperclip/ .
COPY modules/hermes-paperclip-adapter/ ../hermes-paperclip-adapter/
RUN pnpm --filter hermes-paperclip-adapter build
RUN pnpm --filter @paperclipai/ui build
RUN pnpm --filter @paperclipai/plugin-sdk build
RUN pnpm --filter @paperclipai/server build
RUN test -f server/dist/index.js || (echo "ERROR: server build output missing" && exit 1)

FROM base AS production
ARG USER_UID=1000
ARG USER_GID=1000
WORKDIR /workspace/modules/paperclip
COPY --chown=node:node --from=build /workspace /workspace
COPY modules/hermes-agent/ /opt/hermes-agent/
RUN npm install --global --omit=dev @anthropic-ai/claude-code@latest @openai/codex@latest opencode-ai \
  && apt-get update \
  && apt-get install -y --no-install-recommends openssh-client jq build-essential python3-venv python3-dev libffi-dev \
  && curl -LsSf https://astral.sh/uv/install.sh | sh \
  && mkdir -p /opt/uv-python \
  && cd /opt/hermes-agent \
  && UV_PYTHON_INSTALL_DIR=/opt/uv-python /root/.local/bin/uv venv venv --python 3.11 \
  && VIRTUAL_ENV=/opt/hermes-agent/venv /root/.local/bin/uv pip install -e ".[honcho]" \
  && chmod -R a+rX /opt/uv-python /opt/hermes-agent \
  && ln -sf /opt/hermes-agent/venv/bin/hermes /usr/local/bin/hermes \
  && rm -rf /var/lib/apt/lists/* \
  && mkdir -p /paperclip \
  && chown node:node /paperclip

COPY modules/paperclip/scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV NODE_ENV=production \
  HOME=/paperclip \
  PATH=/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOST=0.0.0.0 \
  PORT=3100 \
  SERVE_UI=true \
  PAPERCLIP_HOME=/paperclip \
  PAPERCLIP_INSTANCE_ID=default \
  USER_UID=${USER_UID} \
  USER_GID=${USER_GID} \
  PAPERCLIP_CONFIG=/paperclip/instances/default/config.json \
  PAPERCLIP_DEPLOYMENT_MODE=authenticated \
  PAPERCLIP_DEPLOYMENT_EXPOSURE=private \
  OPENCODE_ALLOW_ALL_MODELS=true

VOLUME ["/paperclip"]
EXPOSE 3100

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["node", "--import", "./server/node_modules/tsx/dist/loader.mjs", "server/dist/index.js"]
