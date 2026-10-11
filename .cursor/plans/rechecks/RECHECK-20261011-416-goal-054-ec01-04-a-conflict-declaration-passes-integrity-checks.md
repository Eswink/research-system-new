---
id: RECHECK-20261011-416
slug: goal-054-ec01-04-a-conflict-declaration-passes-integrity-checks
title: 独立复检：GOAL-20261011-054 cycle 1（EC-01…EC-04）—— 冲突声明与被引 id 的完整性校验
plan_id: PLAN-20261011-415
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/memory/gate.py（`_contradiction_check` 两侧对齐）
  - path: 独立重跑判据（新用例 4 条 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-054-press-two-way.txt
---

# RECHECK-20261011-416 — GOAL-20261011-054 cycle 1 独立复检

复检对象：`PLAN-20261011-415`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-conflict-integrity.py` —— 探针**两条路径都跑**：

| 路径 | `supersedes` 悬空 | `contradictions` 悬空 | `contradictions` 自指 |
| --- | --- | --- | --- |
| A：`store.commit`（适配器直写，**绕过门链**）| ACCEPTED | ACCEPTED | ACCEPTED |
| B：`commit_memory`（**产品路径**，门链）| **`accepted=False stage=contradiction`** | （修复前）`accepted=True` / （修复后）**`accepted=False`** | （修复前）`accepted=True` / （修复后）**`accepted=False`** |

**一处实测更正（如实登记，不抹掉）**：建档初版用**路径 A** 测量 ⇒ 把对照面读成
「`supersedes` 也接受」⇒ **差异恰为门链**。以**产品路径 B** 为准 ⇒ **不对称成立**
（`supersedes` 早就有校验，`contradictions` 没有）。探针现在**两条路径都跑**，
差异本身就是结论的一部分。

### 2. EC-02 gate 对齐（独立重跑）

`_contradiction_check` 现在对 `contradictions` 加**存在性** + **不得自指**两维校验；
`supersedes` 那一侧**判词逐字未动**（`supersedes target {old_id!r} does not exist`）。
新用例 4 条逐条对四件事：悬空拒绝**点名** / 自指拒绝**点名** / 正常通过 / `supersedes` 回归锚。
**四条放在一起**才证明校验判的是**存在性**（而不是「有没有 `contradictions`」）。

### 3. EC-03 读面一致与**连带面**（独立重跑）

`tests/api tests/adapters` **1207 passed, 7 skipped**；
**连带面**（收紧 gate 的**必然后果**，本 GOAL 的 `escalation_triggers` 第 6 条正是为此先写死处置）：
`tests/`（除 e2e / postgres）**5100 passed, 114 skipped / 零 FAILED**
⇒ **既有测试数据没有一条被新校验拒掉** ⇒ **无需登记受判面收窄**。

### 4. EC-04 两向反证（独立重跑 `scratch/goal054_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（4 passed） |
| `Q-1` 悬空被接受（摘掉整段存在性校验）| **RED**（2 failed）|
| `Q-2` **自指**被接受（只摘自指那一支）| **RED**（1 failed）|
| `Q-3` 校验**误伤正常声明**（判据反转）| **RED**（2 failed）|
| `Q-4` `supersedes` 既有校验被**放宽** | **RED**（1 failed）|
| 复原 | 四条 `sha 复原一致=True`（二进制读写）|

归档：`.cursor/plans/goals/evidence/GOAL-20261011-054-press-two-way.txt`
（**732 B / 15 行 / `CR=0`** / `sha256 232ebbb5d135b65f…`）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| （**无**）| — | 本轮**未改任何既有判据文件** —— `gate.py` 是**产品面**，新用例是**新增文件** | — | `0` |

**射程分类（逐条）**：① 本轮**没有**改动既有判据断言；② **无一处收窄受判面**；
③ `packages/application/memory/gate.py` 的改动是**产品行为**（收紧新提案的校验），
其**后果面**已在 §3 逐条核对（零 FAILED）。

### 6. 收口面（EC-05，待本轮随后回填）

收口验证器 + 断言集进树；两处射程纯收紧；两树复检 + 归档；as-is m0 23/23（记录写完之后）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察读数与 GOAL 表逐条一致
（含**一处实测更正**）；gate 两侧**同一条纪律**且 `supersedes` 面**逐字未动**；
连带面**零 FAILED**；四向反证**基线绿 + 全红 + 复原一致**。

### Warnings

- **W-1（探针路径口径 —— 本轮最重要的教训）**：`store.commit`（适配器直写）**绕过门链**；
  「直写」与「走门链」是**两个面**。探针初版用错了面 ⇒ 把对照面读反。
  **将来测「产品会不会拒」这类问题，必须走 `commit_memory`**。
- **W-2（只做声明面完整性）**：本轮**不**做**内容级**冲突检测（读 `content` 比语义）——
  那是 `W-2` 的**另一半**，仍未做。
- **W-3（不回溯历史）**：收紧只对**新提案**生效；库里若已有悬空 / 自指的声明，
  **不**被迁移或清洗（`escalation_triggers` 已写明不做不可逆动作）。
- **W-4（`CC-1` 仍未做）**：冲突**消解**（谁对谁错）仍由人决定；本轮只保证**声明本身**可查。
- **W-5（承继残余原样保持）**：`W-1` / `W-3` / `CC-1`…`CC-3` / `BB-3` / `Z-1` / `Z-3` /
  `DD-1`…`DD-3` / `AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` /
  `P-*` / `O-1`·`O-3`·`O-4`·`O-5` / `R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
