---
id: GOAL-20261010-049
slug: memory-scope-becomes-selectable
title: 记忆的「适用范围」成为**可选择的** —— `MemoryRecord.scope` 早已声明（缺省 `project`）且读面**逐条披露**，但 `MemoryStore.query` 的签名**只有 `tier` 一个维度**（实测传 `scope=` ⇒ `TypeError`），全仓三个调用点**都只传 tier 或不传** ⇒ 调用方看得见一条记忆属于哪个范围，却**无法按范围选**；而 `memory.read` 的载荷已逐条列出 `scope` ⇒ 缺的是**选择面**（「只给我这个项目的知识」）
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 17**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」；来源 = `GOAL-037` 的实测残余 `O-1`（「memory 的项目维度仍缺」））。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含扩 Port 签名、改读面载荷、新增判据），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) `packages/domain/memory.py` 的
    `scope: str = "project"` 在 `MemoryRecord` 与 `MemoryWriteProposal` 上**都有**（声明确实在场）；
    (b) `MemoryStore.query` 的签名**只有一个维度**（`tier`）—— 实测传 `scope=` ⇒
    `TypeError: unexpected keyword argument 'scope'`；(c) 全仓 `query(` 的调用点**只有三处**
    （`services/api/routers/memory.py` ×2 与 `adapters/canonical/memory_read.py` ×1），
    **都只传 `tier` 或不传** ⇒ 没有一处能按范围取；(d) 读面**逐条披露** `scope`
    （`memory_read.py` 的载荷含 `"scope": str(record.scope)`）⇒ **「看见」已成立、「按它选」不存在**。
    (2) **为什么这属于深度轴**：轴的反面是「只在单个点、单个回合上加状态」——
    本条让**同一条调用**能按范围**取用**知识（而不是把全部范围拉回来自己筛），
    是既有机制**向内**的加深：同一条 `memory.read`，在**同一个时点**上能回答
    「**这个范围**内现在有哪些知识是有效的」。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**适用范围成为可选择的一维** ——
    查询面能按范围筛（缺省不筛 ⇒ **逐字不变**），且**筛掉什么要点名**（不静默丢）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建记忆存储或第二套索引（复用既有 Port 与三适配器）；
    **不**做向量检索 / 语义相似度（那是 `Q-3` 的 derived index 面，且需要新的依赖与边界论证）；
    **不**做跨项目的**权限**判定（`scope` 是**声明的范围**，不是 ACL —— 授权面仍属未覆盖）；
    **不**改既有读面载荷的**字段名**（只**加**可选入参与计数摘要）；**不**做自动清理 / 迁移。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **静默丢弃**（筛掉多少、为什么筛，都要**点名**）；**把范围当权限**（未经论证的越权面）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **下游同步纪律（承 `MEM-20261010-216`，逐条照做）**：改 DTO / 路由 / docstring 后
    **同轮**重生成并提交 `docs/api/openapi.m13.json`；EC 的 `verify` 行点名的用例种类**同轮**
    在受判面上数一遍；**有副作用的实现不得放进只读判定面**。
    (8) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (9) **边界（承继）**：GOAL-001…048 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…048 的未覆盖范围**原样保留**；
    GOAL-048 的 `Z-1`…`Z-3` / GOAL-047 的 `Y-1`…`Y-3` / GOAL-046 的 `X-1`…`X-3` /
    GOAL-045 的 `W-1`…`W-3` / GOAL-044 的 `V-1`…`V-3` / GOAL-043 的 `U-1`…`U-3` /
    GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` /
    GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5`
    （其中 `O-1` 由本轮**推进**）/ `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 17（深度轴）落成**记忆范围可选**：① **勘察定稿** —— 实测「看得见选不着」的
    完整形状（声明确在场 / 签名单一维度 / 三个调用点都只传 tier / 读面已逐条披露）（EC-01）→
    ② **查询面** —— `MemoryStore.query` 支持按 `scope` 筛（缺省不筛 ⇒ **既有行为逐字不变**；
    **三适配器同契约**；范围值**非法 / 不存在** ⇒ **点名**而不是静默空集）（EC-02）→
    ③ **消费面** —— `memory.read` 可传 `scope` 且载荷**点名**「筛掉了多少条」（不静默丢）；
    HTTP 读面同样可选（EC-03）→ ④ **两向反证** —— 筛了却不生效 / 没筛却筛掉 / 非法范围静默空集 /
    缺省路径被改动（EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：不传 `scope` ⇒ **逐字不变**；**不**新建存储 / 索引；**不**做语义检索；
    **不**把范围当权限；**不**改既有字段名（只加**可选**入参与计数）；筛掉要**点名**；
    m0 条数**仍是 23**；判词归档**进树**；改 DTO ⇒ **同轮**同步 OpenAPI 快照；
    有副作用的实现**不得**放进只读判定面；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) `scope` 在域声明面逐字在场（`MemoryRecord` 与提案）；
      (b) `MemoryStore.query` 的签名逐字（**只有 `tier`**）+ **反证**：传 `scope=` ⇒ `TypeError`；
      (c) 全仓 `query(` 调用点逐条（三处，都只传 tier 或不传）；
      (d) 读面**已披露** `scope`（逐字给出那一行）⇒ 「看见已成立、按它选不存在」的判定链闭合。
    verify: >-
      `rg -n "scope: str" packages/domain/memory.py`；
      `rg -n "def query" packages/application/ports/memory_store.py adapters/*/memory_store.py`；
      `rg -n "\.query\(" services packages adapters`（逐条列出调用点）；
      `rg -n "\"scope\"" adapters/canonical/memory_read.py`；
      反证：`python -c "MemoryStore.query(scope=...)"` ⇒ `TypeError`。
    status: PASS
  - id: EC-02
    criterion: >-
      **查询面（可选维度 + 三适配器同契约 + 非法点名）**：`MemoryStore.query` 可**按 `scope` 筛**；
      **缺省不筛 ⇒ 既有行为逐字不变**；**三个适配器**（SQLite / PG / Fake）**同契约**；
      范围值**非法**（空串 / 未知范围）⇒ 依声明如实处理：**未知范围 ⇒ 点名**（不是静默空集，
      也不静默返回全部）；`scope=None` 与不传**等同**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters
      tests/postgres -q` ⇒ 全绿 + 新用例（三适配器各一组：筛 / 缺省 / 未知范围点名）。
    status: PASS
  - id: EC-03
    criterion: >-
      **消费面（点名筛掉多少）**：`memory.read` 可传 `scope`；载荷**点名**「按该范围筛掉了多少条」
      （计数摘要；**不**静默丢）；HTTP 读面同样可选该入参；既有的 `tier` 维**逐字保持**（两维可并存）；
      **缺省路径**（不传 `scope`）的载荷与改动前**逐字相同**（含既有键与计数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical tests/api
      tests/application -q` ⇒ 全绿 + 新用例（筛 / 计数点名 / 缺省逐字不变 / 与 tier 并存）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压）**：`K-1` 传了范围却**不生效**（返回全部）⇒ **RED**；
      `K-2` **没传**范围却筛掉了（缺省被改动）⇒ **RED**；`K-3` **未知范围**静默返回空集（不点名）
      ⇒ **RED**；`K-4` 筛掉的条数**不点名**（静默丢）⇒ **RED**。复原用**二进制读写**且
      raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal049-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-049-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 17**）；⑤ OpenAPI 快照**同轮**同步（若动 DTO / 路由）；
      ⑥ CI 台账**逐提交**；⑦ 承继残余逐条在位；⑧ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal049_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
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
      **静默丢弃**（按范围筛掉多少、为什么筛，都必须**点名**）；**把范围当权限**
      （`scope` 是**声明的范围**，不是 ACL；授权面仍属未覆盖）
    - >-
      **新建记忆存储或第二套索引**（复用既有 Port 与三适配器）；**做向量检索 / 语义相似度**
      （属 `Q-3` 的 derived index 面，需另做边界论证）；**改既有读面字段名**（只加**可选**入参与计数）
    - >-
      **顺手改缺省路径**（不传 `scope` 的载荷必须与改动前**逐字相同**）
    - >-
      **把有副作用的实现放进只读判定面**（承 `MEM-20261010-216` 的实测）
    - >-
      **同轮同步面**：仅当本轮扩查询面**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
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
  - .cursor/plans/tasks/PLAN-20261010-397-goal-049-ec01-04-memory-scope-becomes-selectable.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261010-049 — 记忆的「适用范围」成为**可选择的**

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 17**（轴 = **深度**；依赖序 10、13 ——
> 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 14/15/16 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = `GOAL-037` 的实测残余 `O-1`。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 「看得见选不着」的完整形状：声明确在场 / 签名单一维度 / 三调用点只传 tier / 读面已披露 | PASS |
| EC-02 | 查询面 | 可按 `scope` 筛；缺省逐字不变；三适配器同契约；未知范围**点名** | PASS |
| EC-03 | 消费面 | `memory.read` 可传 `scope` + **点名筛掉多少**；既有 `tier` 维逐字保持；缺省载荷逐字相同 | PASS |
| EC-04 | 两向反证 | 筛了不生效 / 没筛却筛掉 / 未知范围静默空集 / 筛掉数不点名（`K-1`…`K-4` 全红） | PASS |
| EC-05 | 自举收口 | 验证器进树（两处射程）+ 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**静默丢弃**（筛掉多少要点名）；
不得**把范围当权限**；不得**新建存储 / 索引**或做**语义检索**；不得改既有读面字段名；
不得宣称项目安全（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：「看得见，选不着」

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | **声明在场**（域） | `rg -n "scope: str" packages/domain/memory.py` | `MemoryRecord` 与 `MemoryWriteProposal` **各一行**，缺省 `"project"` |
| 1.2 | 校验也在场 | 同文件 `__post_init__` | `memory scope must not be empty`（序 13 加的）|
| 1.3 | **查询面只有一维** | `rg -n "def query" packages/application/ports/memory_store.py adapters/*/memory_store.py` | 三处签名**逐字相同**：`query(self, tier: MemoryTier \| None = None)` ⇒ **无 `scope` 维度** |
| 1.4 | **反证：传了会崩** | 实测 `store.query(scope="project")` | `TypeError: query() got an unexpected keyword argument 'scope'` |
| 1.5 | 调用点逐条 | `rg -n "\.query\(" services packages adapters` | **三处**：`services/api/routers/memory.py:93` / `:146`（**不传**）、`adapters/canonical/memory_read.py:150`（**只传 tier**）|
| 1.6 | 读面**已披露** | `rg -n '"scope"' adapters/canonical/memory_read.py` | 载荷逐条含 `"scope": str(record.scope)` + docstring 列出该键 ⇒ **看得见** |
| 1.7 | **结论** | 1.1–1.6 | 「看见」已成立（逐条披露）、「**按它选**」**不存在**（签名无该维度）⇒ `O-1` 的可机读形态 |

### 2. 可复用的缝（本轮**不**新造机制）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | Port 是既有形状 | `packages/application/ports/memory_store.py` | `query(tier)` 是**唯一**读面；扩成可选参**不改**其语义 |
| 2.2 | 三个适配器 | `adapters/{sqlite,postgres,fakes}/memory_store.py` | 序 13 实测过「三适配器同契约」是**既有纪律**（`MEM-20261010-214`）|
| 2.3 | `tier` 面的先例 | `adapters/canonical/memory_read.py` 的 `_tier_of` | 「字符串 ⇒ 枚举，非法 ⇒ 点名」的形态**现成** ⇒ `scope` 可照此 |
| 2.4 | 载荷有计数摘要先例 | 同文件的 `dispositions` | 「不解析数组就能看出有没有被跳过」的形态**现成** ⇒ 「筛掉多少」照此 |
| 2.5 | 两库的列 | `adapters/*/memory_store.py` 的 schema | `scope` **已在表上**（序 13 落库）⇒ **无需迁移** |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 读面判据 | `tests/adapters/canonical/test_memory_read_dispositions.py` | 既有**18 例**（序 10/13 的）|
| 3.2 | 存储判据 | `tests/adapters/sqlite/test_memory_scope_and_validity.py` | 既有（序 13 建的）|
| 3.3 | 域判据 | `tests/domain/test_memory_declaration_fields.py` | 既有（序 13 建的）|
| 3.4 | 本轮**预期**改动面 | Port（+1 可选参）+ 三适配器 + `memory_read` + HTTP 读面 + 判据 | 逐条枚举进 RECHECK（含 `numstat`）|

### 4. 本轮**不**碰的面（逐条明写）

- 授权 / 权限面：`scope` 是**声明的范围**，**不是** ACL —— 读面认证 / 多租户 / RBAC / BOLA·BFLA
  仍属未覆盖（承 M18 deferred）；本条**只**做「选择面」，**不**声称任何隔离保证；
- 语义检索 / 向量索引（`Q-3` 的 derived index 面）：需另做边界论证，本 GOAL **不做**；
- 记忆的冲突处置（`W-1`）/ 冲突检测算法（`W-2`）：仍属未覆盖；
- 自动清理 / 迁移 / 容量治理：**不做**。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | `scope` 的取值域 | **待 cycle 1 定**：候选 = **自由字符串**（现状）或**枚举**（收紧）。判据：**不**破坏既有行为（既有记录里已有 `"project"` 等值）+ 未知值**点名**而非拒绝 |
| ② | 未知范围的处理 | **待 cycle 1 定**：候选 = 返回空集 + **点名**「该范围无记录」vs **直接点名拒绝**。倾向**后者更诚实**（「你要的范围不存在」与「该范围当前没有记录」是两件事）|
| ③ | 筛掉的条数怎么披露 | **待 cycle 1 定**：候选 = 载荷加**计数**（照 `dispositions` 的形态）+ **点名**是否发生过滤 |
| ④ | 要不要迁移 | **待 cycle 1 复核**：`scope` **已在表上**（序 13）⇒ 预期**无新迁移**；需实测确认两库的列名一致 |
| ⑤ | 承接面 | **不动**（复用既有 Port / 三适配器 / 读面，不新增能力）|

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
   - **分列纪律**：有副作用的实现**不进**只读判定面（承 `MEM-20261010-216`）。
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
GOAL-037 的 `O-2`…`O-5`（**`O-1` 由本轮推进**）；GOAL-036 的 `M-1`…`M-5`；
GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint
与无机器门的旧脚本；GOAL-019…048 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（**收口时**逐条定格；`AA-1`…`AA-3`）

- `AA-1`（**范围不是权限，未覆盖**）：`scope` 是**声明的范围**；「谁**有权**读哪个范围」
  **不在**本轮（读面认证 / 多租户 / RBAC / BOLA·BFLA 仍属未覆盖）。**不得**据本条
  宣称任何隔离保证。
- `AA-2`（**语义检索 / 相似度不在本轮**，未覆盖；承 `Q-3`）：按**声明值**筛，
  **不**做 embedding / 相似度 / 模糊匹配。
- `AA-3`（**范围的治理面不在本轮**，未覆盖）：自动过期 / 清理 / 容量 / 跨范围迁移**不在**。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **记忆的范围面**：**已收口（序 13）** = `scope` 可**声明**、可**落库**、读面**逐条披露**；
  **本轮争取** = 可**按范围选**；**未覆盖** = 范围的**权限**语义（`AA-1`）与治理面（`AA-3`）。
- **记忆的读面**：**已收口** = 时效被消费（序 10）/ 冲突与生效起点可判定（序 13）；
  **未覆盖** = 语义检索（`AA-2`）与自动处置（`W-1`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` / `failure` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `3fcc19d`（replan + 序 17 建档） | **无自己的 run**（同批推送）⇒ `covered_by 38063354230` | 序 17 新增 |
| `e9761b4`（cycle 1 = EC-01…EC-04 = **本批 HEAD**） | `38063354230` **M0 success**（**8 job 全 success**）；`38063354068` **Push on main / CodeQL success**（3 job 全 success）| **实测取证**：查询面 + 消费面 + 四向反证 |
| （待建档提交） | — | — |


### 台账封闭（自我指涉边界）

**本台账行自身所在的提交**不产生可引用的 CI 结论 —— 以「**末条有 run 的提交**」+ 覆盖说明封闭：
本批**唯一**带 run 的提交是 `e9761b4`，`38063354230` **M0 success**（8 job 全 success）覆盖
`3fcc19d` 的**全部代码面**（同批推送，tip 的 tree 包含它）；**不得**循环引用台账提交自身。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261010-397` | `e9761b4` | EC-01…EC-04 全 PASS：**记忆范围可选** —— ① 查询面`MemoryStore.query(tier=None, scope=None)`（两维**可并存**、都缺省 ⇒ 全部；**三适配器同契约** —— SQLite / PG / **Fake** 一并带上，承 `MEM-20261010-214`）；② 消费面 `memory_read` 可传 `scope` ⇒ 载荷**点名**范围与 **`filtered_out`**（与 `dispositions` 同一披露形态），**未知范围 ⇒ 点名**，**缺省载荷逐字相同**（那两键**不出现**）；③ HTTP 读面可选 `?scope=`，用**两个显式 DTO 形态**（继承复用）而不是给路由开 `response_model_exclude_none`（那会**递归**抹掉别的读面上有意义的 `null` —— 实测踩到）；④ **四向反证 K-1…K-4 全红**（1/3/1/1 例）+ 二进制复原 raw `sha256` 一致；⑤ 判据 +7（读面 4 / SQLite 1 / PG 1 / API 1，既有 33 例**一字未动**）；⑥ 定向套件 **4937 passed**；四道门全绿；**无迁移**（列早已在表上）；**OpenAPI 快照同轮重生成** | （见 CI 台账）| **两处真缺陷当场抓住并修好**：`K-2` 反证臂**假绿**（判据数据单一 tier ⇒ 区分不了两件事，修法是判据加第二个 tier）；`response_model_exclude_none` **递归**抹掉 validity 的 `null` （改两个显式 DTO 形态）| EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **七条实测读数**（域声明两处在场 / 查询面签名逐字一维 / 传 `scope=` 实测 `TypeError` / 三个调用点逐条 / 读面已逐条披露 / 两库列已在（无迁移）/ 计数摘要形态现成）⇒ 定位 `O-1` 形态；五条 EC 全 PENDING；MAINLINE 程序表**新增序 17** | （见 CI 台账） | — | 五条 EC 全 PENDING；取值域（①）与未知范围处理（②）待 cycle 1 落 | cycle 1（EC-02 查询面 + EC-03 消费面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | DRAFT | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 17**（承担者 = `O-1`「memory 的项目维度仍缺」）。只读勘察 + **七条实测读数**：(a) `scope: str = "project"` 在 `MemoryRecord` 与提案上**各一行在场**；(b) `MemoryStore.query` 的签名**逐字只有 `tier` 一个维度**（三适配器同形）；(c) **反证**：`store.query(scope=...)` ⇒ `TypeError: unexpected keyword argument`；(d) 全仓 `query(` **只有三个调用点**，都只传 tier 或不传；(e) 读面**已逐条披露** `scope`（看得见）；(f) `scope` **已在两库表上**（序 13 落的）⇒ 预期**无新迁移**；(g) 「计数摘要（不解析数组就能看出有没有被过滤）」的形态**现成**（`dispositions`）⇒ 筛掉多少照此披露。**结论**：「看见已成立、按它选不存在」。五条 EC 全 PENDING。**不做数量目标**；**不**新建存储 / 索引；**不**做语义检索；**不**把范围当权限；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**记忆的适用范围成为可选择的** —— 查询面两维可并存 + 三适配器同契约；消费面点名范围与筛掉的条数、未知范围点名、缺省载荷逐字不变；HTTP 读面两个显式 DTO 形态。**四向反证全红**；判据 +7（既有 33 例一字未动）；定向套件 4937 例绿；四道门绿；无迁移；快照同轮。**两处真缺陷如实登记并修好**（假绿的反证臂 / 递归的 `exclude_none`）。独立复检：`RECHECK-20261010-398`（PASS_WITH_WARNINGS）。EC-05 待收口。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
