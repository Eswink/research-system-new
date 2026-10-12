---
id: RECHECK-20261013-444
slug: goal-067-ec01-04-the-http-read-face-does-not-silently-ignore-the-author-filter
title: 独立复检：GOAL-20261013-067 cycle 1（EC-01…EC-04）—— HTTP 读面的作者筛选不再被静默忽略
plan_id: PLAN-20261013-443
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/routers/memory.py（路由接受并**交给 Port**）+ 三个响应形态
  - path: 独立重跑判据（HTTP 面 8 例 + 序 17 回归 + 查询面 10 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-067-press-two-way.txt
---

# RECHECK-20261013-444 — GOAL-20261013-067 cycle 1 独立复检

复检对象：`PLAN-20261013-443`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-http-author-filter.py` —— 四段读数与 GOAL 表逐条一致
（**改动后**）：

| # | 事实 | 独立读数（改动后） | 改动前 |
| --- | --- | --- | --- |
| 1 | `?proposed_by=` | `['m-x']` + 键 `['filtered_out','proposed_by','records','scope_note']` | 200 + **全量两条**、键只有 `['records','scope_note']`（**静默忽略**） |
| 2 | 对照 `?scope=` | 键含 `filtered_out` / `scope` | 同（序 17 形态） |
| 3 | 路由签名 | `(…, scope=None, **proposed_by=None**)` | 只有 `scope` |
| 4 | 先例（序 17 的披露形态） | 在树（本轮**照它对齐**） | 同 |

### 2. EC-02 HTTP 面按作者筛（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api/test_memory_author_filter_on_the_http_face.py -q`
⇒ **8 passed**。逐条复核：

- **传作者 ⇒ 只出那一位的**（`['m-x']`）+ **披露两键**（`proposed_by` / `filtered_out = 1`）；
- **缺省载荷逐字不变**（键只有 `records` / `scope_note` —— 一个不多）；
- **未知作者 ⇒ 空集**（**不猜**；`filtered_out` 报「全被筛掉」）；
- **`?scope=` 的既有语义一字不动**（回归臂：`scope` / `filtered_out` 照旧，且**不**追加作者键）；
- **两维可并存**（作者维优先，载荷如实报各自的值）。

### 3. EC-03 三形态与快照（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ **全绿**。逐条复核：

- **三个形态各自的键集**逐条点名（缺省 / 按范围 / 按作者）—— 本轮**实测**踩到过：
  并集里漏了新形态 ⇒ FastAPI 把载荷**收窄**回缺省形态、**静默抹掉** `filtered_out`；
- **专用形状** `MemoryAuthoredListViewDto` 在树（与范围形态**同一手法**）；
- **不**给路由开 `response_model_exclude_none`（序 17 实测会递归抹掉有意义的 `null`）；
- **快照同轮**（`+62 / -5`，含该形态）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal067_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（31 passed） |
| `Y-1` 路由忽略该参数（静默忽略） | **RED**（3 failed） |
| `Y-2` 缺省形态被改动（不传也筛） | **RED**（3 failed） |
| `Y-3` 不披露（筛了不报条数） | **RED**（2 failed） |
| `Y-4` 未知作者被当成全选 | **RED**（2 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。

### 5. 判据面自检（两处自纠，如实登记）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **`exclude_none` 判据首版按「短语是否出现」判** ⇒ 被本文件里**解释「为何不用它」的注释**
  命中 ⇒ **假红**（收口验证器当场抓到）⇒ 改判**调用形态**（`exclude_none=True`），不判散文；
- **格式门**：新断言集一条注释按**显示宽度**超 100（中文字符占两列）⇒ 缩短措辞（**不**放宽门）；
- 例数下界钉进收口断言集（8 / 10 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**HTTP 面按作者筛**（与 `?scope=` 同形）、
**披露两键**、**缺省载荷逐字不变**、**未知作者空集**、**序 17 的 `?scope=` 语义一字不动**、
**三形态并集**（少一个就静默丢键 —— 本轮实测过）。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：**未知查询参数**（既不是 `scope` 也不是 `proposed_by`）仍被
  **静默忽略** —— 本轮只把**已被吞掉的那个参数**接通；「**通用**的未知参数拒绝」是**全仓读面**
  的纪律改动面（需先定「哪些参数算已知」的口径）⇒ **登记为后续候选**，本 GOAL **不做**。
- **`W-2`（有意不做的边界）**：**不**做**作者鉴权**（筛是**选择**，不是 ACL —— 与 `scope`
  的边界**逐字同形**）；**不**做**通配 / 模糊匹配**（**精确**匹配）；两维**互斥**（同时传按
  `scope` 优先，作者维的值仍在载荷里如实报）。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
