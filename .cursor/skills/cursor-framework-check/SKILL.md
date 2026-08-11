---
name: cursor-framework-check
description: 校验 Cursor 工程、M0 Python/TypeScript 工具链和安全 hard gate，并运行确定性回归。
disable-model-invocation: true
---
# Cursor Framework Check

统一入口 `scripts/run_all_checks.py` 只编排校验，不安装依赖，也不生成或刷新发布证据。

先在仓库根目录准备冻结环境：

```bash
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
```

执行完整 M0 门禁：

```bash
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

按职责定位失败：

```bash
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile framework
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile python
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile typescript
```

需要单独定位 Cursor framework 子门禁时，可执行：

```bash
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/validate_cursor_framework.py
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_cursor_hook_evals.py
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_cursor_framework_evals.py
```

`framework` profile 聚合 system-spec、governance、Cursor framework、Hook 和 learning 的七项校验。`python` 与 `typescript` profile 负责 lint、format check、strict typecheck、依赖边界和正反向测试。任一命令失败都禁止准入或发布。