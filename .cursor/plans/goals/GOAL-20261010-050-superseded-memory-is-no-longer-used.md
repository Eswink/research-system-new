---
id: GOAL-20261010-050
slug: superseded-memory-is-no-longer-used
title: 被取代的记忆不再是「照用」 —— `supersedes` 早已声明且**有写者**（`lifecycle.supersede_memory` 会 `deactivate` 旧记录），gate 也有引用完整性校验，但**读面从不披露该链接**，且 `disposition_of` **只看时效、不看 `active`** ⇒ **实跑**：一条被取代（`active=False`）的记忆经 `memory_read` 出来仍是 **`disposition=USE`**，而研究循环的时效门正是按 `disposition` 三态分派 ⇒ 被取代的知识**照样进下一步**，读者也无法回答「这条被谁取代 / 它取代了谁」
status: ACHIEVED
created_at: 2026-10-11
updated_at: 2026-10-11
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-11 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 18**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」；来源 = 序 17 收口勘察时量出的新缺口）。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改读面载荷、改处置分派、新增判定态），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) `MemoryRecord.supersedes: list[str]` 在域上
    声明，`packages/application/memory/lifecycle.py::supersede_memory` 走**正式 gate** 提交
    新记录并把**旧记录 `deactivate`** ⇒ 取代**有写者**、也有引用完整性校验
    （`packages/application/memory/gate.py`：`supersedes target {old_id!r} does not exist`）；
    (b) 但 `rg -n supersedes adapters/canonical/memory_read.py` ⇒ **零命中** —— 读面
    **两个方向都不披露**（既无 `supersedes`、也无 `superseded_by`）；
    (c) `disposition_of(state: ValidityState | None) -> str` 的签名**只吃时效状态**
    ⇒ **看不到 `active`** ⇒ 被取代的记录（`active=False`）与现行记录在**处置面上同值**；
    (d) **实跑**：把一条记忆 `deactivate` 之后经 `memory_read` 读回来 ⇒
    `active=False` 但 `disposition="USE"`、理由是「未声明时效或未到 ⇒ 照用（未声明不得被当成
    已到期）」；载荷里既无 `supersedes` 也无 `superseded_by`；
    (e) 消费端 `phase_capability_triggers.memory_gate_verdict` 按 `disposition` **三态分派**
    （只有 `SKIP` 才跳过整步）⇒ 被取代的知识**不会被跳过、也不会被标注**。
    (2) **为什么这属于质量轴**：轴的反面是「把判据做成表层合规」——
    本条让「**这条知识还算数吗**」在**读面**与**处置面**上**真的可判定**，
    而不是靠读者自己去比对 id 列表。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让「**已取代**」成为一种**可判定的处置**，
    且**两个方向**（被谁取代 / 取代了谁）都**点名**；缺省（无取代关系）**逐字不变**。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建存储 / 索引 / 第二套生命周期机制（复用既有
    `supersedes` + `deactivate`）；**不**做**自动**取代（谁取代谁始终是**声明**，不是推断）；
    **不**做传递闭包 / 链式取代的语义推断（只报**直接**链接）；**不**改既有 `SKIP`/`ANNOTATE`/`USE`
    三态的语义（**新增**第四态或**扩展**判据条件，二者择一由 cycle 1 定，但**不混用**）；
    **不**做范围的权限语义（`scope` 仍**不是** ACL）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **静默降级**（谁取代谁、为什么不算数，一律**点名**）；**把「已取代」与「已过期」混用**
    （两者是不同的不适用理由，判词必须可区分）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **下游同步纪律（承 `MEM-20261010-216`，逐条照做）**：改 DTO / 路由 / docstring 后
    **同轮**重生成并提交 `docs/api/openapi.m13.json`；EC 的 `verify` 行点名的用例种类**同轮**
    在受判面上数一遍；**有副作用的实现不得放进只读判定面**；**判据不得按位置/文本写死**
    （承 `MEM-20261010-215`：判关系不判位置）。
    (8) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (9) **边界（承继）**：GOAL-001…049 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…049 的未覆盖范围**原样保留**；
    GOAL-049 的 `AA-1`…`AA-3` / GOAL-048 的 `Z-1`…`Z-3` / GOAL-047 的 `Y-1`…`Y-3` /
    GOAL-046 的 `X-1`…`X-3` / GOAL-045 的 `W-1`…`W-3` / GOAL-044 的 `V-1`…`V-3` /
    GOAL-043 的 `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` /
    GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` /
    GOAL-037 的 `O-1`…`O-5`（其中 `O-4`「读到 ≠ 影响科学结论」与本条**相邻但不同**）/
    `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 18（质量轴）落成**被取代的记忆不再被照用**：① **勘察定稿** —— 实测
    「有写者、无读面、处置面看不见」的完整形状（EC-01）→ ② **读面披露** —— 载荷**两个方向**
    都点名（`supersedes` / `superseded_by`；无关系 ⇒ 空列表，**逐字不变**）（EC-02）→
    ③ **处置面** —— 「已取代」成为**可判定的不适用理由**（与「已过期」**可区分**），
    且研究循环的时效门**真的按它分派**（不是只写在载荷里）（EC-03）→ ④ **两向反证** ——
    被取代仍报 USE / 未取代被误报为已取代 / 两个方向混淆或缺失 / 与「已过期」混用（EC-04）→
    ⑤ **自举收口**（EC-05）。
    **硬约束**：无取代关系 ⇒ **逐字不变**；**不**新建存储 / 第二套生命周期机制；
    **不**做自动取代或链式推断；四态（含新增态若有）**互不混用**且**点名**；
    m0 条数**仍是 23**；判词归档**进树**；改 DTO ⇒ **同轮**同步 OpenAPI 快照；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) `supersedes` 在域声明面逐字在场 + **写者**（`supersede_memory`
      的「新记录 commit + 旧记录 deactivate」两步）；(b) gate 的**引用完整性**校验逐字；
      (c) `rg -n supersedes adapters/canonical/memory_read.py` ⇒ **零命中**（两向都不披露）；
      (d) `disposition_of` 的签名**只吃时效状态**（看不到 `active`）；
      (e) **实跑**：`deactivate` 之后该条仍 `disposition=USE` 且理由逐字；
      (f) 消费端按 `disposition` **三态分派**（只有 `SKIP` 跳过）。
    verify: >-
      `rg -n "supersedes" packages/domain/memory.py packages/application/memory/lifecycle.py
      packages/application/memory/gate.py`；`rg -n supersedes adapters/canonical/memory_read.py`
      ⇒ 零命中；实跑探针（`scratch/`）⇒ `active=False` 但 `disposition=USE` 的读数。
    status: PASS
  - id: EC-02
    criterion: >-
      **读面披露（两个方向都点名）**：`memory_read` 的逐条载荷**两个方向**都披露
      （`supersedes` = 它取代了谁；`superseded_by` = 谁取代了它）；**无取代关系 ⇒ 空列表**
      （是**声明性**的值，不是缺字段 —— 与「缺字段点名」的既有纪律一致）；
      既有的十个键**逐字保持**（新增键是**附加**信息）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical -q`
      ⇒ 全绿 + 新用例（两向披露 / 空列表 / 既有键逐字在场）。
    status: PASS
  - id: EC-03
    criterion: >-
      **处置面（与「已过期」可区分 + 真的被消费）**：被取代的记录在处置面上**不再报 `USE`**，
      且其**不适用理由可区分于「已过期」**（判词**点名**是哪一种、并点出**取代它的那条 id**）；
      **消费端**（研究循环的时效门）**真的按它分派**（不是只写在载荷里）；
      **无取代关系 ⇒ 处置与理由逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters/canonical -q`
      ⇒ 全绿 + 新用例（已取代 → 不适用 / 与已过期可区分 / 消费端分派 / 无关系逐字不变）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压）**：`L-1` 被取代仍报 `USE`（处置面没接上）⇒ **RED**；
      `L-2` **未**取代却被报为已取代（凭空）⇒ **RED**；`L-3` 两个方向**只给一个**（或被调换）
      ⇒ **RED**；`L-4` 把「已取代」与「已过期」**混用**（同一理由串）⇒ **RED**。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal050-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-050-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 18**）；⑤ OpenAPI 快照**同轮**同步（若动 DTO / 路由）；
      ⑥ CI 台账**逐提交**；⑦ 承继残余逐条在位；⑧ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal050_closeout.py --root .
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
      **静默降级**（谁取代谁、为什么不算数，一律**点名**）；
      **把「已取代」与「已过期」混用**（两者是不同的不适用理由，判词必须可区分）
    - >-
      **新建存储 / 索引 / 第二套生命周期机制**（复用既有 `supersedes` + `deactivate`）；
      **做自动取代**（谁取代谁始终是**声明**，不是推断）；**做链式取代的传递闭包**
      （只报**直接**链接）
    - >-
      **失去既有三态的语义**（`SKIP` / `ANNOTATE` / `USE` 逐字保持；新增态或扩展条件
      由 cycle 1 定，但四者**互不混用**）
    - >-
      **顺手改缺省路径**（无取代关系时的处置与理由必须**逐字不变**）
    - >-
      **把有副作用的实现放进只读判定面**（承 `MEM-20261010-216` 的实测）；
      **判据按位置或文本写死**（承 `MEM-20261010-215`：判关系不判位置）
    - >-
      **同轮同步面**：仅当本轮扩披露面**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
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
  - .cursor/plans/tasks/PLAN-20261010-401-goal-050-ec01-04-superseded-memory-is-no-longer-used.md
  - .cursor/plans/tasks/PLAN-20261010-403-goal-050-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-404-goal-050-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261010-050 — 被取代的记忆不再是「照用」

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 18**（轴 = **质量**；依赖序 10、13、17 ——
> 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 15/16/17 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = 序 17 收口勘察时量出的**新缺口**。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 「有写者、无读面、处置面看不见」的完整形状（含 `active=False` 仍 `USE` 的实跑） | PASS |
| EC-02 | 读面披露 | 两个方向都点名（`supersedes` / `superseded_by`）；无关系 ⇒ 空列表；既有十键逐字保持 | PASS |
| EC-03 | 处置面 | 被取代不再报 `USE`；理由**可区分于**「已过期」；**消费端真的按它分派**；无关系逐字不变 | PASS |
| EC-04 | 两向反证 | 仍报 USE / 凭空报取代 / 单向或调换 / 与过期混用（`L-1`…`L-4` 全红） | PASS |
| EC-05 | 自举收口 | 验证器进树（两处射程）+ 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**静默降级**（一律点名）；
不得把「已取代」与「已过期」**混用**；不得**自动取代**或做链式推断；不得**新建**存储 /
第二套生命周期机制；不得宣称项目安全（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：「有写者、无读面、处置面看不见」

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 域声明**在场** | `rg -n "supersedes" packages/domain/memory.py` | `MemoryRecord.supersedes: list[str]` 与 `MemoryWriteProposal.supersedes: list[str]` **各一行** |
| 1.2 | **有写者**（含旧记录 deactivate） | `packages/application/memory/lifecycle.py::supersede_memory` | 「新记录 commit 并记录 `supersedes=[old_id]`；**旧记录 deactivate**」+ 目标必须 active（inactive 不可被 supersede）|
| 1.3 | gate 有**引用完整性** | `packages/application/memory/gate.py` | `supersedes target {old_id!r} does not exist` ⇒ 引用未知 id 拒绝 |
| 1.4 | **读面两向都不披露** | `rg -n supersedes adapters/canonical/memory_read.py` | **零命中**（既无 `supersedes` 也无 `superseded_by`）|
| 1.5 | **处置面看不见 `active`** | `adapters/canonical/memory_read.py::disposition_of` | 签名**只吃 `ValidityState \| None`** ⇒ 被取代的记录与现行记录**同值** |
| 1.6 | **实跑**：被取代仍报照用 | 探针：`deactivate` 一条 ⇒ `memory_read` | `active=False` 但 **`disposition="USE"`**，理由逐字「未声明时效或未到 ⇒ 照用」；载荷无那两个键 |
| 1.7 | 消费端按 `disposition` 分派 | `phase_capability_triggers.memory_gate_verdict` | 三态：任一 `SKIP` ⇒ **整步跳过**；有 `ANNOTATE` ⇒ 执行但带标注；否则照用 ⇒ **被取代的知识不会被跳过也不会被标注** |
| 1.8 | **结论** | 1.1–1.7 | 「取代」**写进去了**（旧记录已 `active=False`），但**读者看不出、处置面也没接上** ⇒ 被取代的知识**照样进下一步** |

### 2. 可复用的缝（本轮**不**新造机制）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 读面投影是**单一构造点** | `memory_read._memory_row` | 逐条十键（含序 13/17 加的）⇒ 加两键是**附加**改动 |
| 2.2 | 处置是**纯函数** | `disposition_of(state)` | 时效 → 处置的映射；扩展它**不引入副作用** |
| 2.3 | 三态常量**集中** | `DISPOSITION_USE` / `DISPOSITION_ANNOTATE` / `DISPOSITION_SKIP` | 新增态或扩展条件都落在这里（**不散落**）|
| 2.4 | 消费端**已按处置分派** | `memory_gate_verdict`（序 10 建） | 「按读面给的 `disposition` 三态分派」的形态**现成** ⇒ 新态只需接进去 |
| 2.5 | 两条**链接方向**在存储里都可达 | `MemoryStore.query()` / `get` | 正向取自记录自身（`supersedes`）；反向需**扫同批记录**（无新查询面也做得到）|

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 读面判据 | `tests/adapters/canonical/test_memory_read_dispositions.py` | 既有**22 例**（序 10/13/17 的）|
| 3.2 | 生命周期判据 | `tests/application/memory/` | 既有（含 `test_gate_adversarial.py` 的 supersede 反证）|
| 3.3 | 消费端判据 | `tests/application/run_orchestration/` | 既有 `memory_gate_verdict` 三态用例 |
| 3.4 | 本轮**预期**改动面 | 读面投影 + 处置纯函数 + 消费端分派 + 判据 | 逐条枚举进 RECHECK（含 `numstat`）|

### 4. 本轮**不**碰的面（逐条明写）

- 授权 / 权限面：`scope` 仍**不是** ACL；读面认证 / 多租户 / RBAC / BOLA·BFLA 仍属未覆盖；
- 向量 / 语义检索（`AA-2` / `Q-3`）：本条只按**声明的链接**判定，**不**推断相关性；
- 冲突面（`W-1` / `W-2`）：`contradictions` 的**处置**仍属未覆盖（本条只做 `supersedes` 的处置）；
- 自动清理 / 容量 / 跨范围迁移（`AA-3`）：**不做**。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 「已取代」怎么进处置 | **待 cycle 1 定**：候选 = **新增第四态**（如 `SUPERSEDED`）vs **复用 `SKIP` 并点名理由**。判据是「与已过期**可区分**」+「既有三态语义逐字保持」+「消费端**真的按它分派**」 |
| ② | 反向链接怎么取 | **待 cycle 1 定**：候选 = 读面在**同一批记录**内扫 `supersedes` 建反查（**不**新增 Port 方法）或新增一个**只读** Port 方法。倾向前者（改动面最小、不动 Port 契约） |
| ③ | 是否动 DTO | **待 cycle 1 复核**：HTTP 读面（`MemoryRecordDto`）是否同轮披露那两向链接 —— 若动 ⇒ **同轮**同步 OpenAPI 快照 |
| ④ | 消费端要不要新理由面 | **待 cycle 1 定**：新态进 `memory_gate_verdict` 后，「跳过 / 标注」的既有两臂**逐字保持**，新态**点名**（不静默） |
| ⑤ | 承接面 | **不动**（复用既有 `supersedes` / `deactivate` / 三态常量 / 消费端分派）|

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
   - **分列纪律**：有副作用的实现**不进**只读判定面；判据**不按位置/文本**写死。
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
| 真红（既有资产） | 既有收口断言集报「本树有判负」 | **先判归属**：实现错 ⇒ 修实现；判据按位置 / 文本写死 ⇒ 改成**判关系**（承 `MEM-20261010-215`）|
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；
GOAL-047 的 `Y-1`…`Y-3`；GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；
GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint
与无机器门的旧脚本；GOAL-019…049 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（**收口时**逐条定格；`BB-1`…`BB-3`）

- `BB-1`（**链式取代不在本轮**，未覆盖）：只报**直接**链接；A→B→C 的传递闭包**不做**。
- `BB-2`（**冲突的处置仍不在**，未覆盖；承 `W-1`）：本条只做 `supersedes`（**已取代**）；
  `contradictions`（**冲突**）的处置仍是另一件事。
- `BB-3`（**自动取代 / 推荐取代不在本轮**，未覆盖）：谁取代谁是**声明**，**不**推断。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **取代关系**：**已收口（既有）** = 可**声明**、可**落库**、有**引用完整性**校验、
  旧记录**会 deactivate**；**本轮争取** = 读面两向披露 + 处置面**可判定**且被消费；
  **未覆盖** = 链式（`BB-1`）与自动取代（`BB-3`）。
- **记忆的「不适用」**：**已收口** = 时效三态（序 10）；**本轮争取** = **已取代**成为第四种
  可判定的不适用理由；**未覆盖** = 冲突的处置（`BB-2`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` / `failure` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （待建档提交） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `PLAN-20261010-403` | （见 CI 台账） | EC-05 五条 AC 全 PASS：收口验证器 **64 判词 / 0 FAIL**（标准断言集**一行未重写**）+ 两处射程**纯收紧**（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 19→20）+ **两树 `TWO-TREE PASS`**（两路 **64 判词** / `sha256` 相同 `01ab4af0…`）+ 归档定格（两份各 **2369 B / 64 行**、`CR=0`、0 FAIL）+ 治理 + 宪章判据 + 定向套件 **4945 passed** + **as-is m0 23/23**（`PASS [` 24 / `FAILED [` 0 / **5600 passed, 21 skipped**）| （见 CI 台账）| **判据自纠一处**（把源码**字面折行**写进判据 ⇒ 折行即假红 ⇒ 改判关系，承 `MEM-20261010-215`）| 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261010-404`）|
| 1 | `PLAN-20261010-401` | （见 CI 台账） | EC-01…EC-04 全 PASS：**被取代不再照用** —— ① 读面逐条 **+2 键**（`supersedes` / `superseded_by`，**两向都点名**；无关系 ⇒ 空列表）；② 新增**第四态** `SUPERSEDED`（与「已过期」**理由可区分**；两者皆有时**都点名**；优先级固定 = 已取代先于时效）；③ **消费端真的分派**（`memory_gate_verdict` 处置同为「跳过」但**判词分开点名**；未知态仍 fail closed）；④ **四向反证 L-1…L-4 全红**（3/7/1/2 例）+ 二进制复原 raw `sha256` 一致；⑤ 判据 +8（读面 5 / 消费端 3）；⑥ **一处既有判据假红按关系修正**（`goal045` 把调用式**逐字写死** ⇒ 加关键字实参即假红，改成判关系并**两向实测**）⑦ **未动 DTO** ⇒ 快照无需重生成 | （见 CI 台账）| —— | EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **八条实测读数**（域声明两向在场 / `supersede_memory` 两步写者 / gate 引用完整性 / 读面**零命中** / `disposition_of` 只吃时效 / **实跑** `active=False` 仍 `USE` / 消费端三态分派 / 结论「有写者、无读面、处置面看不见」）⇒ 定位新缺口；五条 EC 全 PENDING；MAINLINE 程序表**新增序 18** | （见 CI 台账） | — | 五条 EC 全 PENDING；新态形态（①）与反查取法（②）待 cycle 1 落 | cycle 1（EC-02 披露 + EC-03 处置面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | DRAFT | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 18**。只读勘察 + **八条实测读数**：(a) `supersedes` 在 `MemoryRecord` 与 `MemoryWriteProposal` 上**各一行在场**；(b) `lifecycle.supersede_memory` 是**真写者**（新记录 commit + **旧记录 deactivate**，且 inactive 不可被 supersede）；(c) gate 有**引用完整性**（未知 id 拒绝）；(d) `rg -n supersedes adapters/canonical/memory_read.py` ⇒ **零命中**（两向都不披露）；(e) `disposition_of` 的签名**只吃 `ValidityState`** ⇒ 看不见 `active`；(f) **实跑**：`deactivate` 之后该条仍 `disposition="USE"`、理由「未声明时效或未到 ⇒ 照用」；(g) 消费端 `memory_gate_verdict` **按 `disposition` 三态分派**（只有 `SKIP` 跳过整步）⇒ 被取代的知识**不会被跳过也不会被标注**；(h) **结论**：**有写者、无读面、处置面看不见**。五条 EC 全 PENDING。**不做数量目标**；**不**新建存储 / 第二套生命周期；**不**做自动取代 / 链式推断；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
| 2026-10-11 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**被取代的记忆不再被照用** —— 读面两向披露取代关系、新增第四态 `SUPERSEDED`（与已过期可区分）、消费端真的按它分派。**四向反证全红**；判据 +8；四道门绿；未动 DTO（快照无需重生成）。**一处既有判据假红按关系修正**（`goal045` 的调用式逐字比对 ⇒ 加关键字实参即假红；已改为判关系并两向实测 —— 承 `MEM-20261010-215`）。独立复检：`RECHECK-20261010-402`（PASS_WITH_WARNINGS）。EC-05 待收口。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-11 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、**两处射程纯收紧**、两树 **`TWO-TREE PASS`**（两路 **64 判词** / `sha256` 相同 `01ab4af0…`）、判词归档进树（两份各 2369 B / 64 行 / `CR=0`）、治理 + 宪章判据绿、定向套件 4945 例绿、CI 台账逐提交。**一处判据自纠如实登记**（把源码**字面折行**写进判据 ⇒ 折行即假红 ⇒ 改判**关系** —— 与 cycle 1 修的 `goal045` **同一类**「按写法写死」；承 `MEM-20261010-215`）。**一处时序**：两树首轮红（bootstrap：归档在提交之后才存在）。**收口后不再推进本 GOAL**；残余 `BB-1`…`BB-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261010-404`（PASS_WITH_WARNINGS）。 |
