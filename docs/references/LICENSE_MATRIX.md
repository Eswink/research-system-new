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
| Temporal Server/SDK | verify exact components/version | later adapter |
| Open Policy Agent | Apache-2.0 | optional adapter |
| OpenTelemetry | Apache-2.0 ecosystem; verify packages | observability |
| MCP SDK | verify selected language SDK/version | Tool provider protocol |
| SWE-ReX | MIT | optional execution adapter |
| Cline | Apache-2.0 | reference/optional |
| Cline Kanban | Apache-2.0 | UX donor |
| Claw AI Lab | verify pinned revision | research UX donor |
| AutoResearchClaw | verify pinned revision | workflow donor |
| Dr. Claw | copyleft boundary from prior audit | reference only |

`pyproject.toml` + `uv.lock` 与 `package.json` + `pnpm-lock.yaml` 是当前工程工具依赖及完整解析的权威来源。`UPSTREAM_COMPONENTS.yaml` 额外记录需要显式采用审批和独立许可证证据的核心复用组件；其中 `PLANNED` 条目只表示决策，不表示已安装或已解析。

每个 ToolPack/Skill/Plugin 单独记录 license；宿主仓库许可不自动覆盖插件内容。
