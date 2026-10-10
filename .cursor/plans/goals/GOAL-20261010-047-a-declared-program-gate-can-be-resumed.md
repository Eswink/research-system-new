---
id: GOAL-20261010-047
slug: a-declared-program-gate-can-be-resumed
title: 声明的程序级人工闸门**能被人接回** —— 序 14 让程序**可声明**「到第 N 轮停下等人」，但实测那条闸门**只停得住、接不回**：程序面对 `register(` 零命中（判定面只读 `list_for_run`），产品面上唯一注册审批的落点是 **phase 边界**（`pause_for_human_gate`），而 `decide` 要求 run 处于 `WAITING_FOR_APPROVAL`（程序推进只写决策、不改 run 状态）⇒ 实跑里 `GET /runs/{id}/approvals` 返回空、程序恒停该轮
status: ACHIEVED
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 15**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」；来源 = `GOAL-20261010-046` 的残余 `X-1` 的**收窄可机读形态**）。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改产品语义、新增判定种类、接线既有 Port），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) 程序面三文件（`program_runner.py` /
    `program_waiting.py` / `program_retry.py`）对 `register(` **全为 0**，而 `list_for_run`
    在 `program_waiting.py` 命中 **5** 次 ⇒ 判定面**只读、无写者**；(b) 全仓**产品码**里唯一
    注册审批的落点是 `phase_pause.pause_for_human_gate`（**phase 边界**，`risk="HUMAN_GATE"`，
    `phase_runner.py` 调用），**程序面没有对应落点**；(c) `POST /approvals/{id}/decide` 的
    准入条件是 **run 处于 `WAITING_FOR_APPROVAL`**（`services/api/approvals.py`），而程序推进的
    闸门**只写一条决策**、**不改 run 状态** ⇒ 声明的闸门**无法被裁决**；
    (d) **实跑反证**：声明 `human_gate_at_index=1` ⇒ 第 1 轮跑完后推进落 `WAIT_FOR_APPROVAL`，
    `GET /runs/{run_id}/approvals` ⇒ **`[]`**、`GET /approvals` ⇒ **0** 条、`run_count` 恒 **1**
    ⇒ **产品面上没有任何东西能满足该闸门**。
    (2) **为什么这属于连续性轴**：轴定义是「研究可中断、可恢复、可交接：**中断后能接回**，
    恢复不重复已发生的副作用，交接不丢上下文」。**能停不能接回 = 中断不可恢复** ——
    这正是该轴的**反面**；序 14 把「中断可声明」做成了，本轮补「中断可接回」。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让声明的人工闸门**在既有审批面上可被满足**、
    满足后**推进照常继续**（且**不重复**已发生的副作用 —— 幂等面承序 9）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建第二套审批存储或第二套闸门机制（复用既有
    `ApprovalStore` 与 `phase_pause` 的**同一**注册语义）；**不**改 phase 面闸门语义（逐字保持）；
    **不**做自动批准 / 自动放行 / 自动超时（人没拍板就是没拍板）；**不**做催办 / 升级 / 通知
    （那是 `X-1` 的其余部分，仍属未覆盖）；**不**把闸门做成「额外一层检查」。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让程序绕过自己声明的人工闸门**；**静默跳过闸门**（跳过 / 等待必须**点名**）；
    **把「等人拍板」与「还在跑」混用**（承序 12）；**自动批准 / 自动放行 / 自动超时**。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **下游同步纪律（承 `MEM-20261010-216`，本轮新增的申报项）**：改 DTO / 路由 /
    docstring 后必须**同轮**重生成并提交 `docs/api/openapi.m13.json`（该判据会自我修复 ⇒
    只看本地看不见漂移）；EC 的 `verify` 行点名的用例种类必须**同轮**在受判面上数一遍。
    (8) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (9) **边界（承继）**：GOAL-001…046 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…046 的未覆盖范围**原样保留**；
    GOAL-046 的 `X-1`…`X-3`（其中 `X-1` 的**「接回」这一半**由本轮推进，「催办 / 升级 / 超时」
    这一半**仍保留**）/ GOAL-045 的 `W-1`…`W-3` / GOAL-044 的 `V-1`…`V-3` / GOAL-043 的
    `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` / GOAL-040 的
    `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` / GOAL-037 的
    `O-1`…`O-5` / `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 15（连续性轴）落成**声明的程序级人工闸门能被人接回**：① **勘察定稿** ——
    实测「只停不回」的完整形状（程序面 `register(` 零命中 / 唯一注册落点在 phase 边界 /
    `decide` 的准入条件 / 实跑取证 `[]` 与 `run_count` 恒 1）（EC-01）→ ② **接回面** ——
    闸门在**既有审批面**上**注册一条待决审批**（复用 `phase_pause` 的**同一**语义：注册 +
    发 `APPROVAL_REQUESTED` + 落等待态；**不**新建第二套存储），且**判词点名**该审批标识
    （EC-02）→ ③ **真的接得回** —— 该审批被裁决后，同一推进**照常继续**（不重复副作用），
    **未决时仍停**、**缺审批面时仍点名**（EC-03）→ ④ **两向反证** —— 未裁决不得续跑 /
    已裁决必须续跑 / 只读面不得替代注册面 / 重复注册可幂等（EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：不声明 ⇒ **逐字不变**；**不**新建第二套审批 / 闸门机制；phase 面语义**逐字保持**；
    **不**自动批准 / 跳过 / 超时；等待与接回都要**点名**；m0 条数**仍是 23**；判词归档**进树**；
    改 DTO ⇒ **同轮**同步 OpenAPI 快照；EC 点名的用例**同轮**在受判面上数一遍；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 程序面三文件对 `register(` **零命中**、`list_for_run`
      命中数（只读面无写者）；(b) 全仓**产品码**里注册审批的**唯一落点**（`phase_pause`）
      与其调用方（`phase_runner` 的 phase 边界）；(c) `decide` 的准入条件逐字
      （run 须处于 `WAITING_FOR_APPROVAL`）；(d) **实跑反证**：声明闸门的程序 ⇒
      `GET /runs/{run_id}/approvals` 与 `GET /approvals` 的读数 + `run_count`（停在原地）；
      (e) 结论：闸门**只停不回**的判定链闭合。
    verify: >-
      `rg -c "register\(" packages/application/run_orchestration/program_{runner,waiting,retry}.py`
      ⇒ 全 0；`rg -n "\.register\(" packages/application/run_orchestration/phase_pause.py`；
      `rg -n "WAITING_FOR_APPROVAL" services/api/approvals.py`；
      实跑探针（`scratch/`）⇒ `[]` / 0 条 / `run_count=1`。
    status: PASS
  - id: EC-02
    criterion: >-
      **接回面（复用既有审批面，不新建第二套）**：声明闸门在**该轮跑完之后**的推进里
      **注册一条待决审批**（经既有 `ApprovalStore.register`，语义与 phase 面**逐字同源**：
      `risk` / `action` / `context` / `policy_source` 逐项可比），并**发
      `APPROVAL_REQUESTED` 事件**（既有事件类型，不新增事件）；返回的判词**点名**
      该审批标识；**重复推进不重复注册**（幂等：同一声明点只留一条待决）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration tests/api -q` ⇒ 全绿 + 新用例
      （注册发生 / 点名标识 / 幂等去重 / 未声明不注册）。
    status: PASS
  - id: EC-03
    criterion: >-
      **真的接得回**：该待决审批**被裁决后**（经既有 `POST /approvals/{id}/decide` 或
      等价审批面），同一推进**照常继续**（该轮**不重跑** —— 已发生的副作用不重复；
      续跑落在该轮**之后**的序号）；**未裁决 ⇒ 仍停**且点名；**缺审批面 ⇒ 仍点名**
      （承序 14 的 fail-closed，不得静默放行）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿 + 新用例
      （裁决前停 / 裁决后续 / 该轮不重跑 / 缺面点名）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证**：(a) **未裁决**时把推进改成「照常续」⇒ 判据**判红**；
      (b) **已裁决**时把推进改成「仍停」⇒ 判据**判红**；(c) 把注册面**撤掉**（只留只读面）
      ⇒ 判红点名（不允许「只读面冒充接回面」）；(d) 重复注册（同一推进跑两次）⇒ 待决**不增**；
      (e) **未声明**闸门 ⇒ 注册面**零调用**（缺省路径逐字不变）。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal047-press.txt` 各行全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-047-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 15**）；⑤ OpenAPI 快照**同轮**同步（若动 DTO/路由）；
      ⑥ CI 台账**逐提交**；⑦ 承继残余逐条在位；⑧ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal047_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **让程序绕过自己声明的人工闸门**；**静默跳过闸门**（跳过 / 等待 / 接回都必须**点名**）；
      **把「等人拍板」与「还在跑」混用**（承序 12）
    - >-
      **新建第二套审批存储或第二套闸门机制**（复用既有 `ApprovalStore` / `phase_pause` 的
      同一注册语义）；**改 phase 面闸门语义**（逐字保持）；
      **自动批准 / 自动放行 / 自动超时**（人没拍板就是没拍板）
    - >-
      **催办 / 升级 / 通知**（`X-1` 的其余部分仍属未覆盖）
    - >-
      **同轮同步面**：仅当本轮新增接线**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
      （谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **改既有判据的申报纪律（承 `MEM-20261009-210`，逐条自证）**：任何对**既有**
      判据 / 测试文件的改动必须 ① **逐条枚举**改动面；② 用
      `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；③ **逐条比对谓词是否
      等同**（不得只写「强度未降」—— 那是一句**需要自证**的断言）；④ **收窄受判面必须
      显式申报**（写明收窄了什么与理由），**不得**称「强度不变」；⑤ 属**同轮同步集之外**
      的形态 ⇒ 命中 `escalation_triggers`，在 RECHECK 里**如实登记**。
    - >-
      **下游同步漏项（承 `MEM-20261010-216`）**：改 DTO / 路由 / docstring 后**不**同轮
      重生成并提交 `docs/api/openapi.m13.json`；或在 EC 的 `verify` 行点名某类用例却
      **不在受判面上数一遍**（文本在场 ≠ 行为被断言）。
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
child_plans:
  - .cursor/plans/tasks/PLAN-20261010-389-goal-047-ec01-04-the-gate-can-be-resumed.md
  - .cursor/plans/tasks/PLAN-20261010-391-goal-047-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-392-goal-047-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261010-047 — 声明的程序级人工闸门**能被人接回**

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 15**（轴 = **连续性**；依赖序 14 ——
> 已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 12/13/14 收口后到期），
> 已在 MAINLINE「修订记录」留痕；并在新增本行时**触顶** ⇒ 同轮做了战役级预算核算
> （`max_goals` 15 → 20，三条轴各有实测差距）。承担者 = `GOAL-046` 的实测残余 `X-1`
> 的**收窄可机读形态**。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 「只停不回」的完整形状：程序面无写者 + 唯一注册落点在 phase 边界 + `decide` 准入 + 实跑取证空审批 | PASS |
| EC-02 | 接回面 | 闸门在**既有**审批面注册一条待决（语义与 phase 面同源）+ 点名标识 + 幂等去重 | PASS |
| EC-03 | 真的接得回 | 裁决后照常继续（该轮不重跑）；未裁决仍停；缺面仍点名 | PASS |
| EC-04 | 两向反证 | 未裁决不得续 / 已裁决必须续 / 只读面不得冒充 / 重复注册不增 / 未声明零调用 | PASS |
| EC-05 | 自举收口 | 验证器进树（两处射程）+ 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**绕过或静默跳过**声明的人工闸门；
不得把「等人拍板」与「还在跑」**混用**；不得**自动**批准 / 放行 / 超时；不得**新建第二套**
审批或闸门机制；不得宣称项目安全（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：声明的闸门**只停得住**，**接不回**

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 程序面**没有写者** | `rg -c "register\(" packages/application/run_orchestration/program_{runner,waiting,retry}.py` | **全 0**（三个文件） |
| 1.2 | 判定面**只读** | `rg -c "list_for_run" packages/application/run_orchestration/program_waiting.py` | **5**（只读面用得很足） |
| 1.3 | 全仓产品码里**唯一**注册审批的落点 | `rg -n "\.register\(" packages/application/run_orchestration/phase_pause.py` | `phase_pause.py:65`（`risk="HUMAN_GATE"`；由 `phase_runner.py` 在 **phase 边界**调用） |
| 1.4 | 程序面**没有**对应落点 | 同 1.1 | 证明 1.1 的零命中不是「名字不同」而是**这条缝不存在** |
| 1.5 | `decide` 的准入条件 | `rg -n "WAITING_FOR_APPROVAL" services/api/approvals.py` | run 须处于 `WAITING_FOR_APPROVAL`（否则 409） |
| 1.6 | 程序推进**只写决策**、**不改 run 状态** | `rg -n "transition\|save_run" packages/application/run_orchestration/program_runner.py` | 命中落在「起新 run」路径上；**闸门分支**只返回 `_Evaluation` |
| 1.7 | **实跑反证** | 探针：声明 `human_gate_at_index=1` ⇒ 跑完第 1 轮 ⇒ 推进 | 落 `WAIT_FOR_APPROVAL`；`GET /runs/{id}/approvals` ⇒ **`[]`**；`GET /approvals` ⇒ **0** 条；`run_count` 恒 **1** |
| 1.8 | **结论** | 1.1–1.7 | 声明的闸门**无法被任何产品路径满足** ⇒ 程序**永远**停在那一轮（**能停不能接回**） |

### 2. 可复用的缝（本轮**不**新造机制）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 审批存储是既有 Port，**写面齐备** | `packages/application/ports/approval_store.py` | `register` / `list_pending` / `list_for_run` / `get` / `replace` 五个方法都在 |
| 2.2 | phase 面的注册语义**可逐字对照** | `phase_pause.pause_for_human_gate` | 三步：注册 `ApprovalSpec` + 发 `APPROVAL_REQUESTED` + 落等待态 |
| 2.3 | 事件类型是既有枚举 | `packages/domain/events.py` | `APPROVAL_REQUESTED` 已在（**不**新增事件类型）；`approval_event_payload` 也已在 |
| 2.4 | 裁决入口是既有路由 | `POST /approvals/{approval_id}/decide` | 三态校验（已裁决 409 / If-Match / 状态机）已实现 |
| 2.5 | 判定面**已经在点名**待审批 | `program_waiting.pending_approval` | 序 14 起的三种形态（缺面 / 查错 / 查不到）各自点名 ⇒ **接回面只需补「注册」这一半** |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 等待面的既有用例 | `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | **14 例**（序 12 的 7 + 序 14 的 7）；本轮的注册 / 接回用例与它们**同族** |
| 3.2 | 程序面实跑的既有用例 | `tests/e2e/test_program_advance_on_the_run_path.py` | **9 例**（含序 14 补的两例） |
| 3.3 | 审批面的既有用例 | `tests/api/test_approval_registration_api.py` / `test_approvals_api.py` | 已有（**只读**引用，不重复） |
| 3.4 | 本轮**预期**改动面 | 程序面（注册 + 接回）+ 可能的状态面（若需把 run 落到可裁决态）+ 判据 | 逐条枚举进 RECHECK（含 `numstat`） |

### 4. 本轮**不**碰的面（逐条明写）

- phase 面的人工闸门语义（逐字保持）；
- D 组审批通道本身（触达即 BLOCKED）：不放开任何 destructive 能力的放行；
- 催办 / 升级 / 超时取消（`X-1` 的**其余部分**，仍属未覆盖）；
- 条件式 / 多点闸门（`X-2`，仍属未覆盖）；
- 读面认证 / 多租户 / 部署面 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 接回形态 | **待 cycle 1 定**：候选 = 在推进的闸门分支**注册**待决审批（复用 `ApprovalStore.register`）；判据是「可点名 + 可裁决 + 幂等 + 未声明零调用」 |
| ② | 是否要把 run 落到 `WAITING_FOR_APPROVAL` | **待 cycle 1 复核**：`decide` 要求该状态 ⇒ 需实测「不改 run 状态能否经既有面裁决」；**若必须改**，改动面要最小且不重复 phase 面的副作用 |
| ③ | 事件发布口径 | **待 cycle 1 定**：与 `phase_pause` **同一** `APPROVAL_REQUESTED`（**不**新增事件类型） |
| ④ | 幂等键 | **待 cycle 1 定**：同一声明点重复推进**不得**重复注册（用既有自然键或显式去重查询，**不**新建表） |
| ⑤ | 承接面 | **不动**（复用既有审批面，不新增能力） |

## 循环入口协议（幂等重入）

驱动方进入时，按「迭代日志」最后一行 + 工作树/远端实况判定续点（与 `goals/README.md`
同一条协议）：

1. 读本文件 frontmatter 的 `status`（`DRAFT` ⇒ 先转 `ACTIVE` 并写状态历史一行）；
2. 读「迭代日志」最后一行 ⇒ 取「下一轮输入」列作为续点；
3. **复核工作树与远端**：`git status --porcelain`（**只**相信自己要动的路径）+
   `git log --oneline origin/main..HEAD`（未推送的提交即未取证）；**并发工作树**里
   不属于本 GOAL 的改动**不碰、不 stage**；
4. 若上一 cycle 的提交**未推送** ⇒ 先按「单 cycle SOP ⑤」推送并读到 CI 终态；
5. 若「上一轮输入」清单为空且五条 EC 全 PASS ⇒ 走「终止与收口」。

**幂等约束**：同一 cycle 重复进入**不得**改写已完成 cycle 的记录（只追加）；EC 状态只**升级**
（`PENDING` → `PASS` / `BLOCKED`），**不**回退（回退必须在状态历史里写明理由）。

## 单 cycle SOP

1. **派生**：一个 cycle = 一个 `PLAN-*`（含 `parent_goal`，同轮投影进 `ALL_PLAN.md`）；
2. **执行**：按 WP 拆提交，**显式路径**（**禁止** `git add -A`；并发工作树）；
3. **本地验证**（顺序固定：**先写记录** → 记录面判据 → **全量 m0**）：
   - 记录先落地（`.cursor/plans/**`），再跑治理 `validate.py` 与
     `tests/tooling/test_mainline_program_is_intact.py`；
   - m0 按组跑、**独占**（不并发任何**会改工作树**的动作）、仓库 `.venv`、
     `uv run --frozen --no-sync python -B`、**不接管道**（否则 `$?` 是管道的）；
   - **下游同步**：动了 DTO / 路由 ⇒ **同轮** `tools/gen_openapi.py` 并提交；
     EC 的 `verify` 点名的用例 ⇒ **同轮**在受判面上数一遍；
4. **commit**：一个 cycle 可拆多个提交（每个 WP 一个）；提交信息写清**立题（实测）**与**交付**；
5. **push + CI**：批量推送（一个 cycle 攒一次）；`git pull --ff-only` 后再推；
   推完用 `scratch/poll_ci_all.sh <sha>` **遍历该 sha 的全部 run + `/jobs`** 读到终态；
6. **纠错**：按「CI 失败分类与纠错」表处置；**同一失败签名**超过 `same_signature_retries` ⇒
   本 GOAL 记 `BLOCKED`；
7. **回写**：EC 状态 / 迭代日志 / 状态历史 / `latest_recheck` / `child_plans` / `memory_entries`。

## CI 失败分类与纠错

| 分类 | 形态 | 处置 |
| --- | --- | --- |
| 真红（产品面） | 测试断言失败且指向本轮改动 | **修产品面**；**不得**改判据 / 放宽阈值 |
| 真红（记录面） | 治理 / 宪章 / 记录面判据红 | 改记录（措辞 / 登记 / 链接），**不**改判据 |
| 时序红（bootstrap） | 资产类断言在「资产写入之前」的提交上红 | 如实登记为**时序**；资产提交后复取证 |
| 基础设施红 | registry 限流 / 5xx / 镜像拉取失败 | 三条证据（注解 / 时间戳 / 状态页）⇒ 等窗口重跑；**绝不动阈值** |
| `cancelled` | 同 ref 后推取消在飞的 run | 写**原因** + `covered_by`（用时间戳取证） |
| 快照漂移 | OpenAPI / 结构签名类 | **按生成器重新生成**；判据**一字不改** |
| 依赖面 | 上游版本 / pin 变更 | 命中 `escalation_triggers` ⇒ `BLOCKED` |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS` + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  本文件收口；收口动作照 `MEM: goal-closeout-procedure` 并声明 `verify_paths` ≥ 2 路、
  **用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers` 或 `budget.max_cycles` 触顶（20）。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-046 的 `X-1`（**「接回」这一半由本轮推进**；
「催办 / 升级 / 超时」这一半**仍保留**）/ `X-2` / `X-3`；GOAL-045 的 `W-1`…`W-3`；
GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint
与无机器门的旧脚本；GOAL-019…046 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（**收口时**逐条定格；`Y-1`…`Y-3`）

- `Y-1`（**催办 / 升级 / 超时取消不在本轮**，未覆盖；承 `X-1` 的其余部分）：本轮让闸门
  **可被满足**（注册 + 点名 + 裁决后续跑）；**不**做「没人拍板怎么办」。
- `Y-2`（**条件式 / 多点闸门不在本轮**，未覆盖；承 `X-2`）：本轮仍按**单序号**声明。
- `Y-3`（**通知 / 提醒面不在本轮**，未覆盖）：审批注册**不**伴随任何对外通知。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **闸门接回**：**本 GOAL 争取收口** = 声明的闸门在**既有审批面**上可被满足，满足后推进
  照常继续且该轮不重跑；**未覆盖** = 没人拍板时的催办 / 升级 / 超时（`Y-1`）与通知面（`Y-3`）。
- **人在环**：**已收口（序 14）** = 可声明 / 可判定 / 可点名；**本 GOAL 争取** = 可裁决 / 可接回；
  **未覆盖** = D 组审批通道本身（`X-3`）与审批的用户体验面。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （待建档提交） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `PLAN-20261010-391` | （见 CI 台账） | EC-05 五条 AC 全 PASS：收口验证器 **70 判词 / 0 FAIL**（标准断言集**一行未重写**）+ 两处射程**纯收紧**（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 16→17）+ **两树 `TWO-TREE PASS`**（两路 **70 判词** / `sha256` 相同 `a2ba7fa0…`）+ 归档定格（两份各 **2600 B / 70 行**、`CR=0`）+ 治理 + 宪章判据 + **as-is m0 23/23**（**5576 passed, 21 skipped**）| （见 CI 台账）| **CI 真红**：注册实现曾落进**只读判定面** ⇒ `goal044`/`goal046` 各一条判负（**判据对、实现错**）⇒ 按 `phase_pause` 手法单列注册模块；另规模门两处抽查 ⇒ 搬迁；`goal046` 一条判据由「定义行」改判「求值顺序」| 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261010-392`）|
| 1 | `PLAN-20261010-389` | （见 CI 台账） | EC-01…EC-04 全 PASS：**声明的闸门接得回** —— ① 判定②由**五条实测读数**落定（run 停在 `SUCCEEDED` / `decide` ⇒ 409 即使记录**真的**存在 / 状态机无终态入边⇒ 靠挪状态接回不了）；② **注册面**经**既有** `ApprovalStore.register`（`risk=HUMAN_GATE` / `policy_source=program-gate` / `action` 用**本 GOAL 自己的**前缀 `program-gate:`）+ **点名**标识 + **幂等**（同 action 在场不重注册）+ 只读面 / 注册失败 / 查询失败**三种形态各自点名**；③ **裁决准入两分支**（`program-gate:` ⇒ run **终态**；其余**逐字保持**）且**窄**（同一个 `SUCCEEDED` run 上前缀决定 200 还是 409）；④ **实跑回路**：拦住 → 产品面有那条待决 → `decide` 200 → 推进 `CONTINUE`、该轮**不重跑**、序号 `[1, 2]`；⑤ **五条反证 H-1…H-5 全红**（5/3/1/3/6 例）+ 二进制复原 raw `sha256` 一致 + 归档 **523 B / `CR=0`**；⑥ 判据 +10 例（判定面 6 / e2e 2 / API 2，既有 33 例**一字未动**）；⑦ 定向套件 **1534 passed, 12 skipped**；四道门全绿；**OpenAPI 快照无需同步**（未动 DTO / 路由形状）| （见 CI 台账）| 规模门抓到 `decide_approval` **53 行** ⇒ 抽 `_require_admissible` 后过 | EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **四条实测读数**（程序面 `register(` 全 0 / 唯一注册落点 `phase_pause.py:65`（phase 边界）/ `decide` 要求 run 处 `WAITING_FOR_APPROVAL` / **实跑**：声明闸门后 `GET /runs/{id}/approvals` ⇒ `[]`、`GET /approvals` ⇒ 0 条、`run_count` 恒 1）⇒ 定位 `X-1` 的「接回」形态；五条 EC 全 PENDING；MAINLINE 程序表**新增序 15** + **预算核算 15→20** | （见 CI 台账） | — | 五条 EC 全 PENDING；接回形态（①）与 run 状态面（②）待 cycle 1 落 | cycle 1（EC-02 注册面 + EC-03 接回） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | DRAFT | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 15**（承担者 = `GOAL-046` 的 `X-1` 收窄形态）+ 触顶 ⇒ 战役级核算 `max_goals` 15→20。只读勘察 + **四条实测读数**：程序面三文件对 `register(` **全 0**；全仓产品码唯一注册落点 = `phase_pause.py:65`（phase 边界）；`decide` 准入 = run 须处 `WAITING_FOR_APPROVAL`；**实跑反证** —— 声明 `human_gate_at_index=1` 的程序在第 1 轮跑完后推进落等待态，而 `GET /runs/{id}/approvals` = **`[]`**、`GET /approvals` = **0** 条、`run_count` 恒 **1** ⇒ **闸门只停不回**。五条 EC 全 PENDING。**不做数量目标**；**不**自动放行；**不**催办 / 通知；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **cycle 1 开工**（`PLAN-20261010-389`）：决策②已由**五条实测读数**落定 —— 闸门触发后 run 停在 **`SUCCEEDED`**；对 `SUCCEEDED` 的 run 走 `decide` ⇒ **`409 Invalid Transition`**（即使审批记录**真的存在**也一样 ⇒ 卡的是**状态准入**）；状态机**没有**「终态 ⇒ `WAITING_FOR_APPROVAL`」的边 ⇒ 不能靠挪 run 状态接回；采纳形态 = 程序级闸门用**自己的 action 前缀**（`program-gate:`）+ `decide` 新增分支（既有分支逐字不变，其 18 例用例是回归网）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**声明的程序级人工闸门接得回** —— 登记「只停不回」的完整形状（程序面 `register(` 全 0 / 唯一落点在 phase 边界 / `decide` 准入 / 实跑 `[]` 与 `run_count` 恒 1），并补齐接回面：**注册**（既有 Port + 点名 + 幂等 + 三种点名形态）+ **裁决准入两分支**（新前缀走「run 终态」，其余逐字保持；**同一 run 上前缀决定 200/409** ⇒ 窄）+ **实跑回路**（裁决后 `CONTINUE`、该轮不重跑）。**五条反证全红**；判据 +10（既有 33 例一字未动）；定向套件 1534 例绿；四道门绿；快照无需同步。独立复检：`RECHECK-20261010-390`（PASS_WITH_WARNINGS）。EC-05 待收口。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、**两处射程纯收紧**、两树 **`TWO-TREE PASS`**（两路 **70 判词** / `sha256` 相同 `a2ba7fa0…`）、判词归档进树（两份各 2600 B / 70 行 / `CR=0`）、as-is m0 **23/23**（5576 passed, 21 skipped；记录写完之后）、治理 + 宪章判据绿、CI 台账逐提交。**一处真红如实登记并修好**：注册实现曾落进只读判定面 ⇒ 两条既有断言集判负（**判据对、实现错**）⇒ 单列注册模块后复原（GOAL-043 立的判据**第三次兑现**）。**一处时序**：两树首轮红（bootstrap：归档在提交之后才存在）。**收口后不再推进本 GOAL**；残余 `Y-1`…`Y-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261010-392`（PASS_WITH_WARNINGS）。 |
