# Quality Gates v0.4.0

## M0 Engineering Gate

M0 准入使用冻结环境和单一只读编排入口：

```text
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

`m0` 聚合 Python、TypeScript 和 Cursor framework profile，覆盖 format/lint、strict typecheck、依赖边界、正反向测试及治理 validator。普通 CI 不生成或验证发布 Manifest/Evidence。

行尾由根 `.gitattributes` 固定为 `eol=lf`。Windows runner 默认 `core.autocrlf=true`，若不固定则同一提交在 Windows 上会 checkout 成 CRLF，导致 formatter gate 失败且发布摘要按平台漂移；该不变量由 Cursor framework validator 强制。

## Gate Result

```text
PASS
PASS_WITH_WARNINGS
REVISE
BLOCK
```

## Gate Examples

### Preflight

- Model eligibility；
- Tool/credential；
- budget；
- workspace；
- protocol validity。

### Evidence

- claim coverage；
- source identity；
- contradictory evidence handled。

### Experiment

- code/environment/input digest；
- expected metrics；
- exit status；
- statistical checks。

### Deliverable

- verified claim mapping；
- citation mapping；
- no fabricated metric；
- target requirements。

## Score

分数只用于排序和可视化。

任何 Hard Invariant 失败时，即使总分高也必须 BLOCK。
