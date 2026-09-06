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
Foundation / Executable Research Kernel（M0-M7 含 M5R）= completed
MVP 能力平面（M8-M11）= completed（2026-08-15）
Post-M7 产品能力（M12-M17）= completed（M17 真实单卡 GPU 全链 VERIFIED，2026-09-02）
SI-1 Personal Scale Integration Review = PASS（2026-09-02）
PA-1 Personal Production Acceptance = PASS（2026-09-03）
PA-1R Independent Personal Production Re-audit = PASS（2026-09-06）
Personal Production Baseline = COMPLETE；固定 Milestone 主线暂停
M18/M19 = DEFERRED；HPC Track 未激活，当前无真实 multi-GPU/multi-node/Slurm/HPC 环境
```

M0-M11（含 M5R）全部完成，真实完成顺序为
`M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7 → M8 → M9 → M10 → M11`
（M3 先于 M2：M2 Preflight 消费 M3 Model Relay 产物；M8-M11 为 M7 后
并行组 1）。完整完成矩阵见
[docs/roadmap/COMPLETION_MATRIX_M0_M11.md](docs/roadmap/COMPLETION_MATRIX_M0_M11.md)
（唯一权威），集成里程碑记录见
[docs/roadmap/M7_COMPLETION_RECORD.md](docs/roadmap/M7_COMPLETION_RECORD.md)、
[M8_COMPLETION_RECORD.md](docs/roadmap/M8_COMPLETION_RECORD.md)、
[M9_COMPLETION_RECORD.md](docs/roadmap/M9_COMPLETION_RECORD.md)、
[M10_COMPLETION_RECORD.md](docs/roadmap/M10_COMPLETION_RECORD.md)、
[M11_COMPLETION_RECORD.md](docs/roadmap/M11_COMPLETION_RECORD.md)、
[M12_R1_COMPLETION_RECORD.md](docs/roadmap/M12_R1_COMPLETION_RECORD.md)、
[M13_R1_COMPLETION_RECORD.md](docs/roadmap/M13_R1_COMPLETION_RECORD.md)。

当前已落地：

- `packages/domain/`（37 模块）Domain Kernel：实体/值对象/枚举/状态机/
  RunManifest+digest/UsageLedger/experiments/reproducibility/eval 契约；
- `packages/application/`（protocol_compile / preflight / model_relay /
  policy / ports / run_orchestration / tool_plane / skill_registry /
  experiments / evidence / memory / evaluation）use cases +
  17 inward-owned Ports；
- `adapters/`（contracts loaders / fakes / relay / openhands / sqlite /
  mcp / execution / workspace / index / cli）——OpenHandsRuntimeAdapter
  （openhands-sdk v1.42.0，pin 于 `UPSTREAM_COMPONENTS.yaml` 与 revision
  lock）、SQLite 持久化、MCP ToolProvider（mcp 1.29.0）、容器实验执行
  （docker-py 7.2.0）、EvidenceLedger/RetrievalIndex Fake+InMemory、
  Eval Gate CLI；
- `tests/`（domain / application / adapters / contracts / e2e /
  evals / architecture）——E2E 垂直切片含故障注入矩阵 F-01..F-12，
  M11 Evaluation Plane deterministic gates（CI eval-gate job，离线无
  LLM）。

M8-M17、SI-1、PA-1 与 PA-1R 已完成；PA-1R 的既有独立复审于
2026-09-06 判定 PASS。Research OS 现进入
[Usage-driven Development](docs/roadmap/USAGE_DRIVEN_IMPROVEMENT_TEMPLATE.md)：
等待真实使用问题或机会，先进入 Plan Mode，再执行一次最小范围改进。固定
Milestone 主线保持暂停；M18/M19 与 HPC Track 仅在
[权威路线](docs/roadmap/MILESTONES.md)定义的正式条件满足后发起重新立项评估，
不会自动开工。当前单卡 GPU 证据不得外推为 physically-remote、multi-GPU、
multi-node、Slurm 或 HPC 支持。已完成事项、Remaining Technical Debt 与候选能力
映射见 `BACKLOG.md`。

## 开发入口

1. `AGENTS.md`
2. `.cursor/README.md`
3. `docs/INDEX.md`
4. `docs/PRODUCT.md`
5. `docs/roadmap/COMPLETION_MATRIX_M0_M11.md`
6. `docs/roadmap/MILESTONES.md`（Post-M7 Roadmap）
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

**运行约束**：`m0`/`python` 全量门禁（含 Docker 容器 E2E、PostgreSQL、GPU、遥测时间对比）必须**串行执行且不与其它重负载并行**——同一窗口不要并发跑多个全量 pytest/mypy。标记为 `timing_sensitive` 的测试在并发负载下可能因时钟/容器竞态偶发失败；隔离复跑即通过，不代表产品回归。

本仓库不内置会话级自审次数、固定 reviewer 人数或数值自评分阈值。是否需要独立 reviewer，由变更风险和任务范围决定。
