---
id: RECHECK-20261010-390
slug: goal-047-ec01-04-the-gate-can-be-resumed
title: 独立复检：GOAL-20261010-047 cycle 1（声明闸门接得回 —— 注册面 / 裁决准入两分支 / 两向反证）
plan_id: PLAN-20261010-389
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-390 — GOAL-20261010-047 cycle 1 独立复检

复检对象：`PLAN-20261010-389`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | 程序面**无写者**（修前） | `rg -c "register\("` 在 `program_runner.py` / `program_waiting.py` / `program_retry.py` ⇒ **全 0** |
| 1.2 | 判定面**只读**（修前） | `list_for_run` 在 `program_waiting.py` 命中 **5** 次 |
| 1.3 | 唯一注册落点 | `phase_pause.py:65`（phase 边界，`risk="HUMAN_GATE"`，由 `phase_runner.py` 调用）|
| 1.4 | `decide` 准入（修前） | run 须处 `WAITING_FOR_APPROVAL`（否则 409）|
| 1.5 | **实跑反证**（修前） | 声明闸门 ⇒ `GET /runs/{id}/approvals` = **`[]`**、`GET /approvals` = **0** 条、`run_count` 恒 **1** |
| 1.6 | **状态机无终态入边**（决策②的依据） | `_TRANSITIONS` 只有 `(RUNNING, REQUEST_APPROVAL) → WAITING_FOR_APPROVAL` ⇒ **不能**靠挪 run 状态接回 |
| 1.7 | **真记录也 409**（决策②的判据） | 注册一条**真**审批后再裁决（run 仍 `SUCCEEDED`）⇒ 同样 `409` ⇒ 卡的是**状态准入**而非「有没有记录」|

### 2. 接回面（AC-2/AC-3，独立重跑）

**实跑回路**（经既有 HTTP 面，与 `tests/e2e/test_program_advance_on_the_run_path.py` 的
新用例同形）：

| 步 | 动作 | 读数 |
| --- | --- | --- |
| 1 | 建程序（`human_gate_at_index=1`）+ 推进 | `START` + `started_run_id` 在场 |
| 2 | 再推进 | `WAIT_FOR_APPROVAL`，`cited_facts` 含 `approval_id=<...>` |
| 3 | `GET /runs/{id}/approvals` | **1** 条，状态为「待决」，`risk=HUMAN_GATE` |
| 4 | 再推进一次（幂等） | 待决**仍 1** 条（不堆积） |
| 5 | `POST /approvals/{id}/decide` | **200** + `status=APPROVED` |
| 6 | 再推进 | **`CONTINUE`** + `started_run_id`；`run_count` **2**；序号 `[1, 2]` |

**准入**：`_require_admissible` 按 `action` 前缀两分支。**独立反证其窄性**（同一个 `SUCCEEDED`
run，只差前缀）：`program-gate:` ⇒ **200**；`human-gate:` ⇒ **409** `Invalid Transition`。

**只读面**：`register` 不可调用 ⇒ **点名**（不静默当成已注册），且**不**点名任何凭空的
`approval_id`。

### 3. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `H-1` | 未裁决也照常续（去掉拦住） | **RED**（5 例） |
| `H-2` | 已裁决仍停（与 phase 面语义不一致） | **RED**（3 例） |
| `H-3` | 只读面冒充注册面（不点名） | **RED**（1 例） |
| `H-4` | 重复注册（幂等面失效） | **RED**（3 例） |
| `H-5` | 准入被放宽（非前缀也接受终态 run） | **RED**（6 例） |

五条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261010-047-press-two-way.txt`（523 B / `CR=0`）。

### 4. 门链与记录面

四道门全绿（`ruff check` / `ruff format --check`（1001 files）/ `mypy` strict（**1179** files）/
规模门：改动文件 ≤ 450 行、函数全 ≤ 50 —— `decide_approval` 曾到 **53** 行，已把准入抽成
`_require_admissible` 才过）；定向套件 `tests/{api,application,e2e,domain}`
**1534 passed, 12 skipped**。**OpenAPI 快照无需同步**（未动 DTO / 路由形状；快照判据
8 passed 且工作树无差异）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/api/test_approvals_api.py` | **追加** 2 例（既有 10 例**一字未动**） | — | `+90 / -0` | **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | **追加** 6 例（既有 14 例一字未动） | — | `+123 / -0` | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例（既有 9 例一字未动） | — | `+61 / -0` | **0** |
| `services/api/approvals.py` | 准入抽成 `_require_admissible`（**两分支**：新前缀 + 既有逐字） | **既有那条逐字保留**（`cannot decide approval in run state {run.state}` 同串同行） | `+41 / -7` | 7 行 = 既有准入**搬到新函数**（含 docstring 改写），**判定串一字未改** |
| `packages/application/run_orchestration/program_waiting.py` | 判定面接上注册面 | 判定**分派不变**（先注册再判）；`declared_gate_pending` 的语义与三条点名**逐字保留** | `+70 / -2` | 2 行 = 调用点改写（`last.program_index` → 局部 `index`）与事实元组改写 |
| `services/api/routers/approvals.py` | `program-gate:` 前缀**提前返回** | 既有路径**逐字保留**（仅在上方插入一个 if） | `+8 / -0` | **0** |

**收窄受判面？** 无。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：声明的闸门现在**可被满足**
（注册 + 点名 + 幂等 + 裁决 + 续跑），准入分支**窄**（同 run 上前缀决定 200 还是 409），
五条反证打满。

### Warnings

- **W-1（`program-gate:` 是一条**新增的准入例外**，本文如实登记）**：`decide` 的准入此前
  只有一条规则（「非等待态不得裁决」）；本轮为程序级闸门加了**第二个分支**。**收窄依据**：
  只有**程序自己注册**的闸门（前缀 + run 终态）走新分支，其余路径逐字不变，且由
  `test_a_non_program_gate_approval_on_a_terminal_run_is_still_refused` 与既有
  `test_decide_requires_waiting_state` **两侧**钉住。**不**声称「准入面已完整论证」——
  它是一处**有界例外**，理由与边界都写在 `_require_admissible` 的 docstring 里。
- **W-2（催办 / 升级 / 超时 / 通知不在本 GOAL）**：本轮让闸门**可被满足**；
  **不**做「没人拍板怎么办」（`Y-1` / `Y-3`，承 `X-1` 的其余部分）。
- **W-3（条件式 / 多点闸门不在本 GOAL）**：仍按**单序号**声明（`Y-2`，承 `X-2`）。
- **W-4（D 组审批通道本身不在本 GOAL；触达即 BLOCKED）**：闸门用的审批面是**既有**实例；
  不放开任何 destructive 能力的放行（承 `X-3`）。
- **W-5（`has_waiting_context` 面不适用本前缀）**：phase 面裁决 approve 时要求「可恢复执行
  上下文」，程序闸门**不**走那条路（`_resume_after_approval` 对本前缀是 no-op）—— 因此
  它**不**受 503「上下文丢失」影响，也**不**产出 run 状态迁移。这是**设计差异**，如实登记。
- **W-6（承继残余原样保持）**：GOAL-046 的 `X-1`（**「接回」这一半由本轮推进**，「催办 /
  升级 / 超时」仍保留）/ `X-2` / `X-3`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
