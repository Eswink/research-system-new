# Research OS Cursor Engineering Framework v0.4.0

Repository version: **0.4.0**。版本唯一来源：`VERSION`。

`.cursor/` 是 Cursor coding-agent 的工程控制层，不是 Research OS 产品运行时。

## 权威顺序

1. 根 `AGENTS.md` + Accepted ADR
2. Research OS architecture/security/governance docs
3. `.cursor/rules/`
4. 当前已批准 Plan
5. 已验证 `.cursor/memory/`
6. `.cursor/knowledge/`
7. `.cursor/skills/`

## Cursor 原语职责

```text
AGENTS.md  = 跨工具仓库契约
Rules      = 稳定、简洁、作用域化约束
Skills     = 动态按需加载的可复用流程
Subagents  = 独立 context / 并行调查 / 独立验证
Hooks      = 机器级观测与防御性门禁（非 Sandbox）
Knowledge  = Cursor 官方规范、兼容性 caveat、研究证据
Memory     = 经验证的本仓库工程经验
Experience = 低置信度工程经验缓冲（问题→原因→解法），不直接当作事实
```

## Subagent

- 简单任务不委派。
- 每一波并行 fan-out 最多 3 个子代理。
- 不设置“整个用户任务累计最多 3 个”的全局预算。
- 前一波完成并整合后，可以因新的独立必要工作启动下一波。
- 子代理不得再委派子代理。
- Custom reviewer 使用前台模式，降低当前 Cursor background `subagentStop` 兼容性问题造成的 active-count 漂移。

## Runtime Profile

- `ide_local`：本框架完整 Hook/安全回归的主要验证目标。
- `cloud_agent`：条件支持；当前官方 Hook 支持面不同，敏感 MCP/credential 工作流不能依赖 IDE-only `beforeMCPExecution`。详见 `.cursor/knowledge/CLOUD_AGENT_COMPATIBILITY.md`。

## 自学习

```text
Observation → Experience Entry → Proposal → Consolidate → Replay → Deterministic Validation → Scoped Approval when needed → Promote
```

经验条目（`.cursor/experience/`）是低置信度缓冲层，单次观察 `confidence ≤ 0.5`；跨会话重复 ≥2 次才升级为 LEARN proposal。

不设置固定审核轮数、固定 reviewer 人数或数值评分要求。

高风险变更按范围选择 reviewer：
- 架构边界 → `architecture-reviewer`
- validator/runtime correctness → `verification-reviewer`
- hook/secret/MCP/permission → `security-governance-reviewer`

## M0 Quality Gate

冻结安装与完整门禁从仓库根执行：

```bash
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

`framework`、`python`、`typescript` profile 可单独执行。普通质量检查只读校验发布资产；不会调用 release/package 脚本或刷新 Manifest/Evidence。

## Release

Release truth 来自确定性 validator/eval，而不是历史自评分。

先读取根 `VERSION`，将下面的 `<VERSION>` 替换为该值。发布会重建 Manifest/Evidence，只能在显式发布任务中执行。

### POSIX shell

```bash
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
python -B .cursor/skills/framework-release/scripts/release_cursor_framework.py --version <VERSION>
python -B .cursor/skills/framework-release/scripts/verify_cursor_framework_release.py --version <VERSION>
python -B .cursor/skills/framework-release/scripts/package_cursor_framework.py --version <VERSION> --output ../system-specification-cursor-framework-v<VERSION>.zip
```

### PowerShell

```powershell
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
python -B .cursor/skills/framework-release/scripts/release_cursor_framework.py --version <VERSION>
python -B .cursor/skills/framework-release/scripts/verify_cursor_framework_release.py --version <VERSION>
python -B .cursor/skills/framework-release/scripts/package_cursor_framework.py --version <VERSION> --output ../system-specification-cursor-framework-v<VERSION>.zip
```

机器发布证据位于 `.cursor/releases/`。
