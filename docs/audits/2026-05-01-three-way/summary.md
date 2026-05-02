# Three-way audit — 2026-05-01

- Total claims: 2258
- Headline: 690 MATCH, 29 DRIFT, 1539 UNVERIFIABLE

## Top drifts

- **docs/architecture/canonical/vps-launch-and-company-operation.md:63** (DRIFT) — Compose app plane includes qdrant, neo4j, minio data stores → reconcile sources; vps says: container ['qdrant', 'neo4j', 'minio'] not found
- **docs/architecture/donna-vps-service-map.md:70** (DRIFT) — Paperclip env HOST=127.0.0.1 → reconcile sources; vps says: 127.0.0.1 not present in any env file
- **docs/architecture/donna-vps-service-map.md:71** (DRIFT) — Paperclip env PORT=3100 → reconcile sources; vps says: 3100 not present in any env file
- **docs/architecture/donna-vps-service-map.md:72** (DRIFT) — Paperclip env PAPERCLIP_DEPLOYMENT_MODE=local_trusted → reconcile sources; vps says: local_trusted not present in any env file
- **docs/architecture/donna-vps-service-map.md:73** (DRIFT) — Paperclip env PAPERCLIP_CONFIG=/paperclip/instances/default/config.json → reconcile sources; vps says: /paperclip/instances/default/config.json not present in any env file
- **docs/architecture/overview.md:6** (DRIFT) — north-star.md service roles table includes a Runtime mode column → reconcile sources; vps says: | Service | Runtime mode | Role |
- **docs/architecture/overview.md:7** (DRIFT) — north-star.md names ComfyUI as a specialized worker → reconcile sources; vps says: COMFY["ComfyUI"]
The first specialized worker on this node is **ComfyUI**, covering image and
2. `n8n` receives the request, applies policy gates, and dispatches to ComfyUI
3. ComfyUI produces the media and writes the file to MinIO
4. ComfyUI (or the `n8n` step wrapping it) publishes an `artifact.created`
| ComfyUI | Container | Specialized media-generation worker; writes artifacts to MinIO, publishes lineage to broker |
  ClickHouse, Langfuse, Open WebUI, n8n, n8n-mcp, broker, ComfyUI. No
- specialized workers (ComfyUI)
- **docs/architecture/roadmap.md:95** (DRIFT) — Honcho is exposed at http://127.0.0.1:18000 → reconcile sources; vps says: port 18000 bound by container honcho-api-1
- **docs/architecture/roadmap.md:145** (DRIFT) — Broker listens at http://127.0.0.1:8090 → reconcile sources; vps says: port 8090 bound by container 1215-prototype-local-broker-1
- **docs/architecture/roadmap.md:178** (DRIFT) — Paperclip is exposed at host port 127.0.0.1:3100 mapped to container port 3100 → reconcile sources; vps says: port 3100 present in ss output

## Drift by source

- docs/architecture/self-symptoms/2026-04-22-symptoms.md: 17 drift(s)
- docs/architecture/donna-vps-service-map.md: 4 drift(s)
- docs/architecture/roadmap.md: 3 drift(s)
- docs/architecture/overview.md: 2 drift(s)
- docs/architecture/canonical/vps-launch-and-company-operation.md: 1 drift(s)
- docs/superpowers/specs/2026-05-01-three-way-audit-design.md: 1 drift(s)
- modules/paperclip/README.md: 1 drift(s)

## Suggested fix list (grouped by file)

### docs/architecture/canonical/vps-launch-and-company-operation.md
- L63: reconcile sources; vps says: container ['qdrant', 'neo4j', 'minio'] not found

### docs/architecture/donna-vps-service-map.md
- L70: reconcile sources; vps says: 127.0.0.1 not present in any env file
- L71: reconcile sources; vps says: 3100 not present in any env file
- L72: reconcile sources; vps says: local_trusted not present in any env file
- L73: reconcile sources; vps says: /paperclip/instances/default/config.json not present in any env file

### docs/architecture/overview.md
- L6: reconcile sources; vps says: | Service | Runtime mode | Role |
- L7: reconcile sources; vps says: COMFY["ComfyUI"]
The first specialized worker on this node is **ComfyUI**, covering image and
2. `n8n` receives the request, applies policy gates, and dispatches to ComfyUI
3. ComfyUI produces the media and writes the file to MinIO
4. ComfyUI (or the `n8n` step wrapping it) publishes an `artifact.created`
| ComfyUI | Container | Specialized media-generation worker; writes artifacts to MinIO, publishes lineage to broker |
  ClickHouse, Langfuse, Open WebUI, n8n, n8n-mcp, broker, ComfyUI. No
- specialized workers (ComfyUI)

### docs/architecture/roadmap.md
- L95: reconcile sources; vps says: port 18000 bound by container honcho-api-1
- L145: reconcile sources; vps says: port 8090 bound by container 1215-prototype-local-broker-1
- L178: reconcile sources; vps says: port 3100 present in ss output

### docs/architecture/self-symptoms/2026-04-22-symptoms.md
- L64: reconcile sources; vps says: port 8080 bound by container 1215-prototype-local-open-webui-1
- L78: reconcile sources; vps says: port 5678 bound by container 1215-prototype-local-n8n-1
- L92: reconcile sources; vps says: port 13000 bound by container 1215-prototype-local-n8n-mcp-1
- L108: reconcile sources; vps says: port 3000 bound by container 1215-prototype-local-n8n-mcp-1
- L122: reconcile sources; vps says: port 7474 bound by container 1215-prototype-local-neo4j-1
- L142: reconcile sources; vps says: port 6333 bound by container 1215-prototype-local-qdrant-1
- L162: reconcile sources; vps says: port 9011 bound by container 1215-prototype-local-minio-1
- L163: reconcile sources; vps says: port 9010 bound by container 1215-prototype-local-minio-1
- L178: reconcile sources; vps says: port 8188 bound by container 1215-prototype-local-comfyui-1
- L194: reconcile sources; vps says: port 8090 bound by container 1215-prototype-local-broker-1
- L268: reconcile sources; vps says: 127.0.0.1 not present in any env file
- L269: reconcile sources; vps says: 3100 not present in any env file
- L270: reconcile sources; vps says: http://127.0.0.1:8090 not present in any env file
- L271: reconcile sources; vps says: /run/hermes-gateway/gateway.sock not present in any env file
- L272: reconcile sources; vps says: /paperclip/instances/default/config.json not present in any env file
- L276: reconcile sources; vps says: flow.pimpshizzle.com,donna.tailfedd3b.ts.net not present in any env file
- L297: reconcile sources; vps says: http://127.0.0.1:5678 not present in any env file

### docs/superpowers/specs/2026-05-01-three-way-audit-design.md
- L73: reconcile sources; vps says: path missing: ['README.md', 'STATE.md', 'AGENTS.md', 'docs/**', 'deploy/**']

### modules/paperclip/README.md
- L185: reconcile sources; vps says: port 3100 present in ss output

