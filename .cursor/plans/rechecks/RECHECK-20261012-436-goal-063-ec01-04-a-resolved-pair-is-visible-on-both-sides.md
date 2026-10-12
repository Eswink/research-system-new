---
id: RECHECK-20261012-436
slug: goal-063-ec01-04-a-resolved-pair-is-visible-on-both-sides
title: 独立复检：GOAL-20261012-063 cycle 1（EC-01…EC-04）—— 已消解的一对在两端都看得见
plan_id: PLAN-20261012-435
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/memory/disposition.py（`resolved_pair_index`）
  - path: 独立重跑判据（披露面 10 例 + 序 30 回归 7 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-063-press-two-way.txt
---

# RECHECK-20261012-436 — GOAL-20261012-063 cycle 1 独立复检

复检对象：`PLAN-20261012-435`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-resolved-pair-face.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 消解的反向面**零命中** | 三组候选标识符在三个产品根 **（零命中）** |
| 2 | **实跑**（改动前形态） | **A 侧 `resolutions=1` / `USE`**；**B 侧 `resolutions=0` / `conflicted_by=['m-a']` / `CONFLICTED`** ⇒ **两端不一致** |
| 3 | **先例**在树 | `def conflicted_by_index` + `for other_id in record.contradictions`（同一手法） |
| 4 | 记载读法**仍是单向** | `record.resolutions` 仍在读面（`True`） |

### 2. EC-02 对端可读 + 扣减（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_resolved_pair_read_faces.py -q`
⇒ **10 passed**。逐条复核：

- `resolved_pair_index` **按被消解方索引、值为记载方**（扫同批记录）；
- **两端处置一致**：一对被消解 ⇒ **A 与 B 都是 `USE`**（改动前 B 是 `CONFLICTED`）；
- **对端看得见**：`resolved_with == ['m-a']` 且 `conflicted_by == []`（**不静默消失**）；
- **反证臂**：未消解 ⇒ B 仍 `CONFLICTED` 且 `resolved_with == []`；
- **缺省形态逐字不变**：没有消解记载 ⇒ 两键都空且处置 `USE`；
- **逐对**：只消解一对 ⇒ 其余声明方仍算数（`conflicted_by == ['m-b']` 且仍 `CONFLICTED`）；
- **记载方**的既有读法一字不动（`conflict_resolutions` 仍是它的记载）。

### 3. EC-03 两读面同源（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api/test_memory_api.py tests/application/memory/test_reverse_conflict_read_faces.py -q`
⇒ **全绿**。逐条复核：

- **既有键逐条仍在**（九个键逐个点名）；
- **两读面同源**（**判关系**）：两处**都引用** `resolved_pair_index`；
- **记载读法一字不动**（两处仍是 `record.resolutions`）；
- **快照同轮**（`+7 / -0`）；HTTP DTO 同轮披露 `resolved_with`。

### 4. EC-04 两向反证（独立重跑 `scratch/goal063_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（30 passed） |
| `Z-1` 反向消解表被摘掉（对端读不到） | **RED**（4 failed） |
| `Z-2` 处置面不扣已消解（对端仍冲突） | **RED**（3 failed） |
| `Z-3` 缺省形态被改动（无消解也有非空键） | **RED**（3 failed） |
| `Z-4` 逐对被破坏（只消解一对却整条抹掉） | **RED**（1 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**复检时的一处如实登记**：`Z-3` 首版锚点写成**空操作**（`declarers = declarers`）⇒
该臂**不可观测**（按压按 GREEN）⇒ 改打**可观测**的缺省支（`resolved_with` 的非空形态）后全红。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- EC-02 的判据按**关系**判（索引扫**消解记载** / 扣减保留**差集** / 扣掉的**另键点名**），
  不钉字面写法；
- 例数下界钉进收口断言集（10 / 7 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**一对被消解 ⇒ 两端处置一致**、
**对端看得见那一对**（不静默消失）、**逐对**（只消解一对 ⇒ 其余仍算数）、
**缺省形态逐字不变**。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：`resolved_with` 是**派生事实**（扫同批记录算），
  **不落库** —— 与 `conflicted_by`（序 30）/ `superseded_by`（序 18）**同一形态**；
  代价是**跨范围**时读不到（如实返回空表，调用方按「看不见 ≠ 不存在」点名）。
- **`W-2`（有意不做的边界）**：**不**自动消解 / **不**自动失效（判定仍由**人**给）；
  `CONFLICTED` 仍是「照用但标注」（**不**阻断）—— 与序 19/30 的口径**逐字一致**。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
