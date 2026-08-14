# Engineering Experience Index

轻量工程经验条目索引。本索引供 `sessionStart` 摘要注入（最近 ≤5 条）与 agent 问题检索使用。

## 生命周期

- `ACTIVE`：当前可复用。
- `SUPERSEDED`：被新条目取代，保留历史。
- `RETIRED`：不再适用，保留 provenance。

## Entries

| ID | Status | Confidence | Scope | Review After | Summary |
| --- | --- | --- | --- | --- | --- |
| [EXP-20260813-008](entries/EXP-20260813-008.md) | ACTIVE | 0.5 | repository | 2026-11-11 | test_python_source_limits 300 行/50 行超限 → 拆模块与提取辅助函数，不做豁免 |
| [EXP-20260813-007](entries/EXP-20260813-007.md) | ACTIVE | 0.5 | repository | 2026-11-11 | pytest 收集失败：同名测试模块 import file mismatch 需重命名；fixture 从定义模块导入 |
| [EXP-20260813-006](entries/EXP-20260813-006.md) | ACTIVE | 0.5 | repository | 2026-11-11 | Read 工具读取目录路径失败时改用 Ls 列出目录 |
| [EXP-20260813-005](entries/EXP-20260813-005.md) | ACTIVE | 0.5 | repository | 2026-11-11 | OpenHands 相关 pytest 失败诊断：`-q --tb=line` + 输出落盘/过滤，避免 SDK 可视化 stdout 淹没 |
| [EXP-20260813-004](entries/EXP-20260813-004.md) | ACTIVE | 0.5 | repository | 2026-11-11 | OpenHands SDK 测试脚手架：pydantic 判别联合的 Action/Observation 必须用具体子类 |
| [EXP-20260813-003](entries/EXP-20260813-003.md) | ACTIVE | 0.5 | repository | 2026-11-11 | PatchEdit 报 "historical edit error" 时重新 Read 文件后再编辑 |
| [EXP-20260813-002](entries/EXP-20260813-002.md) | ACTIVE | 0.5 | repository | 2026-11-11 | lint-imports 不可用致架构测试失败：首选 uv run --frozen --no-sync，备选注入 venv Scripts PATH |
| [EXP-20260813-001](entries/EXP-20260813-001.md) | ACTIVE | 0.5 | repository | 2026-11-11 | Python 测试/探针必须经 uv run --frozen --no-sync 或 .venv python 执行，不用系统 python |
| [EXP-20260812-003](entries/EXP-20260812-003.md) | ACTIVE | 0.5 | repository | 2026-11-10 | ruff lint 作用域必须按 CI 定义，禁止全仓 `ruff check .`（豁免区误报） |
| [EXP-20260812-002](entries/EXP-20260812-002.md) | ACTIVE | 0.5 | repository | 2026-11-10 | Windows PowerShell 下命令写法：`;` 分隔替代 `&&`、`git commit -F` 替代 heredoc、cmd 开关需 `cmd /c` 包裹（`dir /b` 会被解析为路径） |
| [EXP-20260812-001](entries/EXP-20260812-001.md) | ACTIVE | 0.5 | repository | 2026-11-10 | 经验库闭环端到端回归方法（失败→观察→提示→沉淀→注入） |

## 注入说明

`session_context.py` 读取本表 `Summary` 列最近 ≤5 条（按 Review After 倒序），注入会话上下文；读取失败静默跳过，不影响会话启动。

## 去重

写入新条目前先按 ID 与 Summary 关键词查本表；同源问题复用 `supersedes` 关联历史条目，禁止静默覆盖。