# Research OS Cursor Engineering Framework v0.4.0

本仓库是 Research OS 的 **system specification + Cursor project engineering framework**。

当前仓库统一版本：`0.4.0`，唯一来源为根 `VERSION`。

## 产品边界

Research OS 保持：

```text
User LLM Relay = Base URL + API Key + Model ID
```

并保持：

- 每个 Agent 独立配置模型；
- Role 与 Agent 分离；
- OpenHands Native 作为 MVP 通用 Agent Runtime；
- Tool / Skill / Capability 独立；
- MCP / REST Research Tools 独立于 LLM Relay；
- Workspace / Sandbox / Evidence / Evaluation / RunManifest 由 Research OS 控制。

## Cursor 工程层

```text
AGENTS.md             跨工具工程契约
.cursor/rules/        稳定、作用域化约束
.cursor/skills/       可重复工程流程
.cursor/agents/       独立上下文的专业子代理
.cursor/hooks.json    机器观测与防护
.cursor/knowledge/    Cursor 官方规范、caveat 与工程证据
.cursor/learning/     受控经验提案与回放
.cursor/plans/        项目计划与证据
.cursor/memory/       已验证仓库工程经验
```

## Subagent 原则

Subagent **不是每个任务必需**。只有并行调查、独立验证或明显可分离工作流有收益时才委派。

一次并行委派波次中：

```text
child subagents < 4
```

即最多 3 个并行子代理。

这不是“整个用户任务累计只能创建 3 个”。前一波完成并被根代理整合后，如果仍有新的独立必要工作，可以启动下一波。

子代理禁止继续创建子代理，避免调用树失控。

## Cursor 工程规范

- Project Rules 使用 `.cursor/rules/*.mdc`。
- Skills 使用 `<skill>/SKILL.md`，只在相关时加载。
- Custom Subagents 放在 workspace root 的 `.cursor/agents/*.md`。
- Hooks 用于机器级观测/阻断，但不是 OS Sandbox。
- MCP 是外部工具/数据连接边界，不替代产品 Capability/Policy。

## Cursor Runtime

完整治理 profile 以 IDE/local 为主验证目标。Cloud Agent 的 Hook 支持面不同；敏感 MCP/credential 工作流必须使用等价 Cloud/Enterprise 或 Research OS 产品安全控制。

## 当前工程状态

```text
Foundation / Executable Research Kernel = completed
```

M0-M7（含 M5R）核心基础设施阶段已全部完成，真实完成顺序为
`M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7`（M3 先于 M2：M2 Preflight
消费 M3 Model Relay 产物）。完整完成矩阵见
[docs/roadmap/COMPLETION_MATRIX_M0_M7.md](docs/roadmap/COMPLETION_MATRIX_M0_M7.md)，
M7 集成里程碑记录见
[docs/roadmap/M7_COMPLETION_RECORD.md](docs/roadmap/M7_COMPLETION_RECORD.md)。

当前已落地：

- `packages/domain/`（29 模块）Domain Kernel：实体/值对象/枚举/状态机/
  RunManifest+digest/UsageLedger；
- `packages/application/`（protocol_compile / preflight / model_relay /
  policy / ports / run_orchestration）use cases + 14 inward-owned Ports；
- `adapters/`（contracts loaders / fakes / relay / openhands /
  sqlite）——OpenHandsRuntimeAdapter（openhands-sdk v1.42.0，pin 于
  `UPSTREAM_COMPONENTS.yaml` 与 revision lock）与 SQLite 持久化；
- `tests/`（domain / application / adapters / contracts / e2e /
  architecture）——E2E 垂直切片含故障注入矩阵 F-01..F-12。

M7 之后仓库进入**产品能力建设阶段**：未来 Milestone 路线（M8-M19）以
`docs/roadmap/MILESTONES.md` 的 Post-M7 Roadmap 节为唯一权威；已完成
事项、Remaining Technical Debt 与 Next Product Capability 的执行映射
见 `BACKLOG.md`。规格目标（PostgreSQL Canonical State、ADR-0002）与
当前实现（同 Port 契约的 SQLite）之间的差异作为技术债显式记录，不以
文档覆盖实现。

## 开发入口

1. `AGENTS.md`
2. `.cursor/README.md`
3. `docs/INDEX.md`
4. `docs/PRODUCT.md`
5. `docs/roadmap/COMPLETION_MATRIX_M0_M7.md`
6. `docs/roadmap/M7_COMPLETION_RECORD.md`
7. `docs/architecture/SYSTEM_ARCHITECTURE.md`
8. `docs/architecture/DOMAIN_MODEL.md`
9. `.cursor/knowledge/INDEX.md`
10. `BACKLOG.md`

## 校验

首次准备或锁文件变更后，先同步冻结环境：

### POSIX shell

```bash
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
# 可选 GNU Make convenience：make bootstrap && make validate-all
```

### PowerShell

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

可用 `--profile framework`、`--profile python` 或 `--profile typescript` 单独定位失败。聚合入口只执行确定性校验与 eval，不安装依赖，也不生成或刷新 `FRAMEWORK_MANIFEST.json` / Release Evidence。

本仓库不内置会话级自审次数、固定 reviewer 人数或数值自评分阈值。是否需要独立 reviewer，由变更风险和任务范围决定。
