# Engineering Experience Index

轻量工程经验条目索引。本索引供 `sessionStart` 摘要注入（最近 ≤5 条）与 agent 问题检索使用。

## 生命周期

- `ACTIVE`：当前可复用。
- `SUPERSEDED`：被新条目取代，保留历史。
- `RETIRED`：不再适用，保留 provenance。

## Entries

| ID | Status | Confidence | Scope | Review After | Summary |
| --- | --- | --- | --- | --- | --- |
| [EXP-20260812-001](entries/EXP-20260812-001.md) | ACTIVE | 0.5 | repository | 2026-11-10 | 经验库闭环端到端回归方法（失败→观察→提示→沉淀→注入） |

## 注入说明

`session_context.py` 读取本表 `Summary` 列最近 ≤5 条（按 Review After 倒序），注入会话上下文；读取失败静默跳过，不影响会话启动。

## 去重

写入新条目前先按 ID 与 Summary 关键词查本表；同源问题复用 `supersedes` 关联历史条目，禁止静默覆盖。