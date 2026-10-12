---
id: RECHECK-20261012-438
slug: goal-064-ec01-04-references-to-a-deleted-record-are-no-longer-silent
title: 独立复检：GOAL-20261012-064 cycle 1（EC-01…EC-04）—— 引用被删的记录不再是静默的
plan_id: PLAN-20261012-437
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/memory/disposition.py（`dangling_reference_index`）
  - path: 独立重跑判据（披露面 10 例 + 序 31 回归 10 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-064-press-two-way.txt
---

# RECHECK-20261012-438 — GOAL-20261012-064 cycle 1 独立复检

复检对象：`PLAN-20261012-437`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-dangling-reference.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 悬空面**零命中** | 三组候选标识符在三个产品根 **（零命中）** |
| 2 | **实跑**（改动前形态） | `m-b` 被删后 `m-a` 照旧 `contradictions=['m-b']` / `supersedes=['m-b']`；**`terminal` 报 `CURRENT`**；载荷里**无**悬空键 |
| 3 | **写面对照** | `supersedes target` / `contradiction target` / `does not exist` **三处都在** gate |
| 4 | **先例**在树 | `TERMINAL_OUT_OF_VIEW` **在** |

### 2. EC-02 悬空引用可读（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_dangling_reference_read_faces.py -q`
⇒ **10 passed**。逐条复核：

- 悬空索引**两个方向各自报**（`supersedes` / `contradictions` 分开成两列表）；
- **被删 ⇒ 读面逐条点名**（改动前完全静默）；
- **既有键一字不动**：`supersedes` / `contradictions` 逐字保留（历史事实）、
  `terminal` **仍报 `CURRENT`**（本轮**不**改它的取值 —— 悬空信号**另键**）；
- **反证臂**：未删 ⇒ 两键都空；干净记录 ⇒ 两键都空（缺省形态逐字不变）；
- **跨范围不猜**：被引的那条在 `organization` 而按 `project` 筛 ⇒ **如实**报它
  （「本批看不到」是对的读数，**不**假装它一定被删）；
- **删除语义一字不动**：被删的真的不在，别人的字段**不被自愈**。

### 3. EC-03 两读面同源（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/api/test_memory_api.py tests/application/memory -q`
⇒ **全绿**。逐条复核：

- **两读面同源**（**判关系**）：两处**都引用** `dangling_reference_index`；
- **两个悬空键都在**（另键披露，两方向不混用）；
- **快照同轮**（`+14 / -0`）；HTTP DTO 同轮披露两个键。

### 4. EC-04 两向反证（独立重跑 `scratch/goal064_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（33 passed） |
| `V-1` 悬空表被摘掉（悬空引用又静默） | **RED**（3 failed） |
| `V-2` 存在性判空（全都算悬空） | **RED**（3 failed） |
| `V-3` 缺省形态被改动（干净也报悬空） | **RED**（3 failed） |
| `V-4` 两个方向混用（键串了） | **RED**（1 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- EC-02 的判据按**关系**判（两个方向**各自算** / 存在性按**本批**判），不钉字面写法；
- 例数下界钉进收口断言集（10 / 10 / 10 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**悬空引用可读**（两方向各自点名）、
**既有键一字不动**（`terminal` 取值不变）、**缺省形态逐字不变**、**跨范围不猜**。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：悬空判定**只在同一批记录内**做 ⇒ **分不清**「被删」与
  「在本批之外」（按 `scope` 筛过 / 分页）—— 返回值是**候选**，由读者按
  「看不见 ≠ 不存在」解读（与序 21 的 `OUT_OF_VIEW` **同一纪律**）。**本 GOAL 不**新增
  「已删除」的一等标记（那需要删除侧的留痕，属另一条面）。
- **`W-2`（有意不做的边界）**：**不**级联删除 / **不**自愈 / **不**阻断删除 ——
  删除是不可逆动作，本轮只让**后果可读**（引用字段**不**被改写：历史事实保留）。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
