---
id: RECHECK-20261013-446
slug: goal-068-ec01-04-unknown-query-parameters-are-no-longer-silently-swallowed
title: 独立复检：GOAL-20261013-068 cycle 1（EC-01…EC-04）—— 未知查询参数不再被静默吞掉（记忆读面）
plan_id: PLAN-20261013-445
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/routers/memory.py（`_reject_unknown_query_params` + 已知集常量）
  - path: 独立重跑判据（未知面 8 例 + 序 35 回归 8 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-068-press-two-way.txt
---

# RECHECK-20261013-446 — GOAL-20261013-068 cycle 1 独立复检

复检对象：`PLAN-20261013-445`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-unknown-query-param.py` —— 五段读数与 GOAL 表逐条一致
（**改动后**）：

| # | 事实 | 独立读数（改动后） | 改动前 |
| --- | --- | --- | --- |
| 1 | 未知参数 | **422** + 正文 `unknown query parameter(s): definitely_not_a_param (known: at, proposed_by, scope)` | **200** + 键只有 `['records','scope_note']`（**静默吞掉**） |
| 2 | 对照（已知） | `?scope=` / `?proposed_by=` **筛 + 披露** | 同 |
| 3 | 零命中（三组标识符） | （零命中） | 同 |
| 4 | 射程 | 记忆读面**两个 GET** | 同 |
| 5 | 全仓 GET 计数 | **65**（**不**扩散 = 有意边界） | 同 |

### 2. EC-02 未知参数点名拒绝（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api/test_memory_unknown_query_params_are_named.py -q`
⇒ **8 passed**。逐条复核：

- **未知 ⇒ 422 + 正文点名**（并给出**已知**集供自纠）；
- **两个 GET 都受判**（`/memory` 与 `/memory/validity`）；
- **多个未知 ⇒ 逐个点名**（`alpha` / `beta` 都在正文里）；
- **已知参数一字不动**（`?scope=` / `?proposed_by=` / `?at=` 都照旧）；
- **缺省载荷逐字相同**（键只有 `records` / `scope_note`）；
- **对照组**：守卫**不**装成全局（其他路由不受影响 —— 射程有意收窄）；
- **已知集与签名一致**（判**关系**：签名里的查询参数必须都在集合里 —— 漏一个就误拒）；
- **写面不受影响**（反证臂：提交照旧 201）。

### 3. EC-03 射程如实（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ **全绿**（621 passed）。

- **不**装成全局中间件（`add_middleware` 在该路由文件里**不出现**）；
- 既有两个已知参数的**披露形态逐字仍在**（序 17 / 35 的判据全绿 ⇒ 无回归）；
- **本轮不动 DTO** ⇒ `docs/api/openapi.m13.json` **零 diff**（参数校验面**不进** schema ——
  如实登记为「快照不变」的**理由**，不是遗漏）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal068_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（29 passed） |
| `Z-1` 未知参数被忽略（静默吞掉） | **RED**（4 failed） |
| `Z-2` 已知参数被误拒（拒绝面过宽） | **RED**（10 failed） |
| `Z-3` 缺省形态被改动（不传也报错） | **RED**（18 failed） |
| `Z-4` 多个未知只报第一个 | **RED**（1 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。

### 5. 判据面自检（两处自纠，如实登记）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **收口断言集首版按 AST 字面量判 `join(unknown)`** ⇒ 它在 f-string 里是 `FormattedValue`
  （**不是** `Constant`）⇒ **假红**（`test_every_named_assertion_set_reports_no_negative_on_this_tree`
  当场抓到）⇒ 改判**源码文本**里的那个取值形态；
- 例数下界钉进收口断言集（8 / 8 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**未知参数点名拒绝**（422 + 逐个）、
**已知参数与缺省形态一字不动**、**射程如实**（只那两个 GET，对照组照旧）。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：**全仓 65 条 GET** 的未知参数**仍被静默吞掉** ——
  本轮**有意**只覆盖记忆读面那两条（全仓口径「哪些参数算已知」**未定**，扩散会撞出大量
  未定义行为）⇒ **登记为后续候选**。
- **`W-2`（有意不做的边界）**：**写面**的请求体额外字段仍走 pydantic 的既有校验面
  （那是**另一面**，本轮**不**动）；**不**做参数值的语义校验（只判**名字是否已知**）。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
