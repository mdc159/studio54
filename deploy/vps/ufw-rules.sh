#!/usr/bin/env bash
# ==============================================================================
# studio54 / VPS firewall ruleset (idempotent)
# ==============================================================================
# Reapplies the UFW ruleset the Hostinger KVM 8 (148.230.95.154) is running
# under at snapshot time. Safe to re-run; ufw dedupes identical rules.
#
# Public surface: only 22 (ssh), 80, 443 (Caddy). Everything else — including
# 9119 (hermes dashboard) and 3100 (Paperclip via socat bridge) — is
# reachable only from the compose bridge network (172.18.0.0/16) so Caddy can
# reverse-proxy in while the internet stays locked out.
# ==============================================================================
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "run as root" >&2
  exit 1
fi

ufw default deny incoming
ufw default allow outgoing
ufw default deny routed

ufw allow 22/tcp comment 'ssh'
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp

# Bridge -> host service ports (Caddy reaches host-native services this way).
# If the compose network ever gets a different /16 on rebuild, update the
# source CIDR here AND in stack/prototype-local/docker-compose.substrate.yml
# (caddy.extra_hosts pin).
ufw allow from 172.18.0.0/16 to any port 9119 proto tcp comment 'caddy bridge -> hermes dashboard'
ufw allow from 172.18.0.0/16 to any port 3100 proto tcp comment 'caddy bridge -> paperclip'

ufw --force enable
ufw status verbose
