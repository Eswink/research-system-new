---
id: RECHECK-20261012-434
slug: goal-062-ec01-04-a-conflict-declaration-is-no-longer-one-way
title: 独立复检：GOAL-20261012-062 cycle 1（EC-01…EC-04）—— 冲突声明不再是一扇单向门
plan_id: PLAN-20261012-433
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/memory/disposition.py（`conflicted_by_index` + 两成因判词）
  - path: 独立重跑判据（域/处置面 9 + 披露面 7 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-062-press-two-way.txt
---

# RECHECK-20261012-434 — GOAL-20261012-062 cycle 1 独立复检

复检对象：`PLAN-20261012-433`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-reverse-conflict.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 反向面**零命中** | 四组候选标识符在三个产品根 **（零命中）** |
| 2 | **实跑**（改动前形态） | A 侧 `contradictions=['m-b']` / **B 侧 `[]` 且反向键不存在 / `disposition=USE`** |
| 3 | **先例**在树 | `def superseded_by_index` + `for old_id in record.supersedes`（同一手法） |
| 4 | 正向读法**仍是一向** | 两处都是 `list(record.contradictions)`（`True`） |

### 2. EC-02 反向索引与分派（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_reverse_conflict_link.py -q`
⇒ **9 passed**。逐条复核：

- `conflicted_by_index` **扫同批记录**算（与序 18 的 `superseded_by_index` **同一手法**：
  正向链接写在**声明方**身上 ⇒ 被声明方读不出来）；**多个声明方逐个收集**；
- **处置面按它分派**：`if conflicted or conflicted_by:` ⇒ 被声明方落 `CONFLICTED`
  （改动前是 `USE` **照用**）；
- **两种成因同类不同因**：`声明与 m-b 冲突` vs `被 m-a 声明与它冲突` —— 受判面 = **两个形态**；
  **不重复**（自己已声明时不追加反向句）；反向列表为空时不凭空追加；
- **缺省参数** `conflicted_by: bool = False` ⇒ 既有调用点逐字不变；
- **优先级未变**（反证臂）：已取代 / 已过期仍**先于**冲突。

### 3. EC-03 两读面同源（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_reverse_conflict_read_faces.py tests/api/test_memory_api.py -q`
⇒ **全绿**。逐条复核：

- 编排面**逐条披露** `conflicted_by`；**被声明方**不再是 `USE`；**声明方**的正向读法**一字不动**；
- **缺省形态逐字不变**（没人声明 ⇒ `conflicted_by == []` 且处置仍是 `USE`）；
- **既有键逐条仍在**（`memory_id` / `content` / `validity` / `disposition` / `reason` /
  `contradictions` / `conflict_resolutions` / `conflict_timeliness`）；
- **两读面同源**（**判关系**）：两处**都引用** `conflicted_by_index`；
- **跨范围如实**（看不见 ≠ 不存在）：声明方移出本批 ⇒ 反向表为空（**不**假装它不存在）；
- **快照同轮**（`+7 / -0`）；HTTP DTO 同轮披露该键。

### 4. EC-04 两向反证（独立重跑 `scratch/goal062_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（29 passed） |
| `Y-1` 反向链接被摘掉（被声明方读不到） | **RED**（1 failed） |
| `Y-2` 处置面不按反向分派（仍照用） | **RED**（2 failed） |
| `Y-3` 缺省形态被改动（没人声明也判冲突） | **RED**（2 failed） |
| `Y-4` 两种成因混用（反向句无条件追加） | **RED**（1 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **受判面非空且非写法清单**：EC-02 的判据按**关系**判（索引扫**声明**字段 / 两条成因**并列**进同一支 /
  新参数**有缺省**），不钉字面写法；
- 例数下界钉进收口断言集（9 / 7 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**被声明方**读得出（反向链接）、
**处置面**按其分派（同类不同因）、**缺省形态逐字不变**（没人声明 ⇒ 与改动前相同）、
**正向读法一字不动**。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：`conflicted_by` 是**派生事实**（扫同批记录算），
  **不落库** —— 与 `superseded_by`（序 18）**同一形态**；代价是**跨范围**时读不到
  （如实返回空表，由调用方按「看不见 ≠ 不存在」点名 —— 本 GOAL **不**新增 `OUT_OF_VIEW` 一类）。
- **`W-2`（有意不做的边界）**：**不**自动消解 / **不**自动失效（判定仍由**人**给）；
  `CONFLICTED` 仍是「照用但标注」（**不**阻断）—— 与序 19 的口径**逐字一致**。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
