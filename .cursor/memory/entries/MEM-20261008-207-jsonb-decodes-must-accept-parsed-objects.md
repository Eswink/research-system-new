---
id: MEM-20261008-207
title: "psycopg 把 jsonb 列回成已解析对象：解码必须接住两种形态（str(dict) 是伪 JSON）"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-337-goal-037-ec01-canonical-program-skeleton.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-338-goal-037-ec01-canonical-program-skeleton.md
supersedes: []
tags: [postgres, jsonb, adapters, goal-037]
---

## 做了什么

新加 `PostgresProgramStore` 时，读 JSONB 列我按 SQLite 的习惯写了
`json.loads(str(row["continue_rule_json"]))`。**live PG 上直接炸**：

```
json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2
```

原因：**psycopg 的 jsonb 行工厂把列回成已解析的 Python 对象**（dict / list），
`str(dict)` 产出的是**单引号伪 JSON**（`{'verdict_in': [...]}`），`json.loads` 自然拒绝。

## 为什么这样做

这是**驱动差异**，不是书写风格问题：同一段解码代码在 SQLite（TEXT 列）下完全正确，
在 PG（JSONB 列）下必炸。判据面（`tests/postgres/**`，live PG）才是能咬住它的地方 ——
只跑 SQLite 口径的判据会给出**假绿**（我在本地先跑 SQLite 判据全绿，切到 PG 才现形）。

正确的写法是**两种形态都接住**（本仓既有先例：`adapters/postgres/run_store.py::_json_of`）：

```python
def _json_object(value: object) -> object:
    if isinstance(value, str):
        return json.loads(value)
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value))   # 已解析对象 → 文本 → 统一解析路径
    return json.loads(str(value))
```

**连带的一条**（同一轮实测）：给 Port 加一个方法（这里给 `RunStore` 加 `for_program`）
会让**所有**测试假实现失去一致性 ⇒ `mypy` 以 `arg-type` 逐处点名
（实测 3 个文件 7 处）。处置是**补假实现**（各 4 行），不是给 Port 加默认实现或
`# type: ignore` —— 后两者会让「假实现漏掉了新方法」这件事永远不可见。

## 怎么做与复现

```bash
# 复现（必须 live PG；SQLite 单跑不会暴露）：
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/postgres/test_program_store_pg.py -q
# 旧写法 ⇒ JSONDecodeError；改成 _json_object 后 ⇒ 2 passed
```

## 适用边界

- 适用于**所有**读 PostgreSQL JSONB 列的适配器（本仓 `*_json` 列先例一致）。
- 不适用于 TEXT 列（SQLite 面）：那里 `str()` 是对的，但**同构适配器共用解码函数**时
  要按上面的写法一次接住两种，避免两个适配器各写一份产生漂移。
- `skip` 计数会随 DSN 环境变化（未设 DSN ⇒ postgres 标记的用例整批跳过）⇒ 读数比对时
  必须连同 DSN 环境一起记，否则「passed/skipped 变了」会被误读成回归。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-337-goal-037-ec01-canonical-program-skeleton.md`
- `.cursor/plans/rechecks/RECHECK-20261008-338-goal-037-ec01-canonical-program-skeleton.md`
