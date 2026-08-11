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

## 当前阶段

当前仍是 docs-first specification 与 Cursor engineering framework。M0 Repository Foundation Quality Gate 已落地冻结 Python/TypeScript 工具链、lint、strict typecheck、双语言依赖边界负测、测试入口和 Windows/Linux CI 定义。

M0 不伪造 Domain、Compiler、OpenHands、数据库或 UI 业务实现。`packages/domain`、`packages/application`、`adapters`、`services`、`apps/web` 只在首个真实职责模块进入时创建；当前依赖方向由 `tests/architecture/` 中可放行、可拒绝的双语言夹具证明。

## 开发入口

1. `AGENTS.md`
2. `.cursor/README.md`
3. `docs/INDEX.md`
4. `docs/PRODUCT.md`
5. `docs/architecture/SYSTEM_ARCHITECTURE.md`
6. `docs/architecture/DOMAIN_MODEL.md`
7. `.cursor/knowledge/INDEX.md`
8. `BACKLOG.md`

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
