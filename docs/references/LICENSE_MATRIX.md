# License Matrix — 2026-08-11 Snapshot

| Component | Observed License/Status | Decision |
|---|---|---|
| PyYAML 6.0.3 | MIT; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED build tooling |
| jsonschema 4.26.0 | MIT; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED contract validator |
| Ruff 0.16.2 | MIT; artifacts pinned in `uv.lock` | ADOPTED Python lint/format tooling |
| mypy 2.3.0 | MIT; artifacts pinned in `uv.lock` | ADOPTED strict typecheck tooling |
| pytest 9.1.1 | MIT; artifacts pinned in `uv.lock` | ADOPTED test tooling |
| import-linter 2.13 | BSD-2-Clause; artifacts pinned in `uv.lock` | ADOPTED Python architecture tooling |
| httpx 0.28.1 | BSD-3-Clause; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED OpenAI-compatible HTTP transport |
| tenacity 9.1.4 | Apache-2.0; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED retry/backoff policy |
| pnpm 9.15.1 | MIT; runtime pinned by `packageManager` and CI | ADOPTED package manager |
| TypeScript 6.0.3 | Apache-2.0; exact package + sha512 integrity in `pnpm-lock.yaml` | ADOPTED typecheck tooling |
| ESLint / `@eslint/js` 10.8.1 / 10.0.1 | MIT; exact packages + sha512 integrity in `pnpm-lock.yaml` | ADOPTED lint tooling |
| typescript-eslint 8.67.0 | MIT; exact package + sha512 integrity in `pnpm-lock.yaml` | ADOPTED typed lint tooling |
| dependency-cruiser 18.2.0 | MIT; exact package + sha512 integrity in `pnpm-lock.yaml` | ADOPTED TypeScript architecture tooling |
| Prettier 3.9.6 | MIT; exact package + sha512 integrity in `pnpm-lock.yaml` | ADOPTED format-check tooling |
| OpenHands Software Agent SDK | MIT | dependency + adapter |
| OpenHands Software Agent SDK v1.42.0 (391fbb8d) — `openhands_sdk` | MIT; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml`; revision lock in `docs/references/upstream/OPENHANDS_REVISION_LOCK.yaml` | ADOPTED runtime adapter (M6) |
| docker-py 7.2.0 (`docker`) — id `docker_py` | Apache-2.0; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED Docker Engine client for execution backend (M9) |
| research-os-sandbox 镜像（`adapters/execution/sandbox/Dockerfile`）— id `research_os_sandbox_image` | 基础镜像 `python:3.12-slim`（OCI index digest pin）；构建产物运行时记录实际 digest | ADOPTED experiment sandbox image (M9) |
| NCBI E-utilities API（`eutils.ncbi.nlm.nih.gov`）— id `ncbi_eutils` | NLM Terms of Use（`https://www.ncbi.nlm.nih.gov/books/NBK25497/`）；resolution `2026-08-22-eutils-api`；ToolPack manifest `examples/contracts/toolpack_ncbi_eutils.yaml`（digest `947cbb22…`）；adapter `adapters/research_tools/ncbi.py` | ADOPTED research literature tool (M12) |
| fastapi 0.141.1 | MIT; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED Control Plane API framework (M13) |
| uvicorn 0.52.4 | BSD-3-Clause; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED Control Plane HTTP server (M13) |
| starlette 1.6.0 | BSD-3-Clause; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED fastapi HTTP core (M13, shared with openhands-sdk) |
| pydantic 2.13.4 | MIT; exact sdist hash in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED API DTO schema validation (M13) |
| psycopg 3.2.13 (`psycopg[binary]`) — id `psycopg` | LGPL-3.0-only; exact sdist hash `309adaeda61d44556046ec9a83a93f42bbe5310120b1995f3af49ab6d9f13c1d` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED PostgreSQL canonical state driver (M14) |
| Temporal Server/SDK | verify exact components/version | later adapter |
| Open Policy Agent | Apache-2.0 | optional adapter |
| OpenTelemetry API 1.39.1 (`opentelemetry-api`) — id `opentelemetry_api` | Apache-2.0; sdist sha256 `fbde8c...67c9c` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED telemetry API (M15, adapter-confined) |
| OpenTelemetry SDK 1.39.1 (`opentelemetry-sdk`) — id `opentelemetry_sdk` | Apache-2.0; sdist sha256 `cf4d45...995cc6` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED telemetry SDK (M15, batching + bounded queue) |
| OpenTelemetry OTLP/HTTP exporter 1.39.1 (`opentelemetry-exporter-otlp-proto-http`) — id `opentelemetry_exporter_otlp_proto_http` | Apache-2.0; sdist sha256 `31bdab...0b9cb` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED OTLP/HTTP export (M15; gRPC exporter rejected) |
| OpenTelemetry OTLP proto common 1.39.1 (`opentelemetry-exporter-otlp-proto-common`) — id `opentelemetry_exporter_otlp_proto_common` | Apache-2.0; sdist sha256 `763370...027464` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED exporter shared helpers (M15) |
| OpenTelemetry wire protobuf 1.39.1 (`opentelemetry-proto`) — id `opentelemetry_proto` | Apache-2.0; sdist sha256 `6c8e05...2e2c8` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED OTLP wire format (M15, receiver evidence) |
| OpenTelemetry semconv 0.60b1 (`opentelemetry-semantic-conventions`) — id `opentelemetry_semantic_conventions` | Apache-2.0; sdist sha256 `87c228...4bc953` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED semconv constants only (pre-release risk acknowledged; no content-bearing GenAI attrs) |
| OTel Collector Contrib image 0.139.0 (`otel/opentelemetry-collector-contrib@sha256:faf125d…`) — id `otel_collector_image` | Apache-2.0; manifest digest pinned in `adapters/otel/collector/Dockerfile` / `UPSTREAM_COMPONENTS.yaml` | ADOPTED telemetry collector evidence pipeline (M15; debug/file exporters only) |
| MCP SDK | verify selected language SDK/version | Tool provider protocol |
| MCP Python SDK v1.29.0 (`mcp`) — MIT; sdist sha256 `52d01f...15ec36` in `uv.lock` / `UPSTREAM_COMPONENTS.yaml`; spec `>=1.28,<2`（v1 stable line，v2 与 openhands-sdk 依赖冲突）| ADOPTED MCP client adapter（M8） |
| SWE-ReX | MIT | optional execution adapter |
| Cline | Apache-2.0 | reference/optional |
| Cline Kanban | Apache-2.0 | UX donor |
| Claw AI Lab | verify pinned revision | research UX donor |
| AutoResearchClaw | verify pinned revision | workflow donor |
| Dr. Claw | copyleft boundary from prior audit | reference only |

`pyproject.toml` + `uv.lock` 与 `package.json` + `pnpm-lock.yaml` 是当前工程工具依赖及完整解析的权威来源。`UPSTREAM_COMPONENTS.yaml` 额外记录需要显式采用审批和独立许可证证据的核心复用组件；其中 `PLANNED` 条目只表示决策，不表示已安装或已解析。

每个 ToolPack/Skill/Plugin 单独记录 license；宿主仓库许可不自动覆盖插件内容。
