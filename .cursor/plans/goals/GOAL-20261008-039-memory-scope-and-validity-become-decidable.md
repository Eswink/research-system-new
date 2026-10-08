---
id: GOAL-20261008-039
slug: memory-scope-and-validity-become-decidable
title: 记忆的**适用范围与时效成为可判定** —— `scope` 落库 + 声明式有效期 + 到期/待复核是**可观测事实**
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**对程序表做一次 replan
    并从实测残余里选一条真正推进轴的另立新 GOAL**，并授权本驱动自动化循环推进、
    **收口后立即开下一个 GOAL，不停下来等指令**。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的
    授权边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改产品语义、**加数据库列与迁移**、新增 ADR），**不等于**可以放宽**判据、门禁、
    阈值或断言**。
    (1) **replan 的产物与依据**（`replan_every_goals: 3` 到期；程序表序 5/6 已收口）：
    从 GOAL-037/038 的实测残余里选一条**推进质量轴**的：`O-1`（memory 的项目维度仍缺）
    与 `P-1`（「携带」≠「因果」）共同指向同一片未覆盖面 —— **记忆的适用范围与时效
    从来不可判定**（实测见「事实层结论」）。本 GOAL **只做这一条**（不做数量目标）。
    (2) **本 GOAL 与既有边界的关系（写死，防读成越界）**：**AGENTS.md §8 的 Memory 契约
    明文要求** Project/Organization Memory 必须「有适用范围」「有过期/复核策略」「可删除」
    「可重建索引」—— 本轮做的是**让前两条成为机械可检的事实**，**不是**新造记忆系统、
    **不是**做 M19 的 data governance、**不是**动门链的语义（仍是
    `MemoryWriteProposal → schema → provenance → policy → gate → commit`）。
    (3) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证 / `R26-2` `R26-3` `R26-4` `R26-6` / 把 destructive 能力从
    `require_approval` 改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (4) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**
    （含 skip / xfail / 条件跳过 / 降强度 / 把受判面写成交集或空集恒真）；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **用「加了计数或阈值」冒充质量**；**把「时效」做成只在测试里生效的旁路**
    （到期/待复核必须是**产品路径**上可观测的事实：读面会读、判定会用）。
    (5) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime 保持 **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10：记忆正文不进观测面）。
    (6) **边界（承继）**：GOAL-001…038 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…038 的未覆盖范围**原样保留**；
    GOAL-038 的残余 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态 / 未覆盖范围
    **原样保留**，本轮**只追加**。
    (7) **driver** = client-goal、**owner** = root-agent。
objective: >-
    把 MAINLINE 序 7（质量轴）落成**一片真正缺的东西**：记忆的**适用范围与时效可判定**。
    ① **勘察定稿** —— 实测：`MemoryWriteProposal.scope` 存在但**从不落库**（无列 / PG 忽略）；
    `review_after` / `expires_at` 在域类型与两库 schema 里都在，但**从不被写**
    （PG 硬编码 `None`）、**从不被读来做判定**（`query` 无时效过滤）；`MemoryRecord` 无
    `scope` 字段；AGENTS.md §8 明文要求「有适用范围」「有过期/复核策略」（EC-01）→
    ② **适用范围落库** —— `scope` 成为 canonical 的一等字段（迁移 + 两适配器 + 读面 + DTO），
    且**读写往返一致**（EC-02）→
    ③ **声明式时效** —— 提案可声明 `review_after` / `expires_at`（DTO + 域 + 两适配器；
    缺省不变 ⇒ 既有行为逐字保持），**产品路径**上产生真实值（EC-03）→
    ④ **到期/待复核是可观测事实** —— 查询面按**显式时点**给出「已过期 / 待复核」的判定
    （由调用方给 `now`，**不读挂钟** ⇒ 判定可复现），读面逐条披露；反证：未到期不报、
    到期必报、无时效声明的记录**不**被误报（EC-04）→
    ⑤ **自举收口**（复用 GOAL-038 的机器）（EC-05）。
    **硬约束**：时效判定**不得**读挂钟（调用方给时点 ⇒ 可复现）；缺省字段一路保持
    `None`（既有行为**逐字不变**，由判据钉住）；**点名而非静默**（无时点的记录不猜）；
    m0 条数**仍是 23**；判词归档**进树**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) `MemoryWriteProposal.scope` 在域里（缺省 `"project"`），
      但 `m12_memory` 表**无 scope 列**、PG 的 `_to_row` 不写它 ⇒ **从不落库**；
      (b) `review_after` / `expires_at` 在 `MemoryRecord` 与两库 schema 里都在，但
      gate / promotion **从不设置**（`rg` 零命中设置点），PG 硬编码 `None`；
      (c) `MemoryStore.query` **无时效过滤**（只有 tier 过滤）⇒ 过期记录照常返回；
      (d) **契约依据**：AGENTS.md §8 明文要求 Project/Organization Memory「有适用范围」
      「有过期/复核策略」「可删除」「可重建索引」；(e) 可复用的缝：既有迁移机制
      （`adapters/postgres/migrations/`）、`MemoryStore` 端口、既有读面
      `GET /projects/{id}/memory`、既有判据（`tests/api/test_memory_api.py` 等）。
    verify: >-
      `rg -n "review_after|expires_at|scope" packages/domain/memory.py
      adapters/{sqlite,postgres}/memory_store.py packages/application/memory/` 逐条读数；
      `rg -n "scope" adapters/postgres/memory_store.py` ⇒ 零命中（从不落库）。
    status: PENDING
  - id: EC-02
    criterion: >-
      **适用范围落库（canonical 一等字段）**：`MemoryRecord` 增 `scope` 字段（缺省
      `"project"` ⇒ 既有记录读出同一语义）；`m12_memory` 增列（**新迁移**
      `018_memory_scope_and_validity.sql`，含 `scope` / 既有两时效列的就位说明）；
      SQLite / PG 两适配器**读写往返一致**；读面 DTO 逐条披露；PG 侧**不再**硬编码 `None`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿；
      新判据：往返（写 `scope` ⇒ 读出同值）+ 旧行（无列值）读出缺省。
    status: PASS
  - id: EC-03
    criterion: >-
      **声明式时效（缺省不变）**：提案面（DTO）可声明 `review_after` / `expires_at`
      （**可选**，缺省 `None`）；gate 把它们带进 canonical（**不新造门链**：仍是既有
      schema → provenance → policy → curator → commit）；两适配器写入真实值；
      **未声明的路径逐字保持既有行为**（判据钉住）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/memory tests/api -q`
      ⇒ 全绿；新判据：声明 ⇒ 落库为真实值；未声明 ⇒ `None`（既有语义）。
    status: PASS
  - id: EC-04
    criterion: >-
      **到期/待复核是可观测事实（+ 两向反证）**：查询面按**调用方给出的时点**（`now`，
      **不读挂钟**）给出逐条判定：`expired`（`expires_at <= now`）/ `review_due`
      （`review_after <= now`）/ `None`（两者皆未到或未声明）；读面
      `GET /projects/{id}/memory` 逐条披露该判定 + 原始两时点。反证①：未到期 ⇒ 不报；
      反证②：到期 ⇒ 必报；反证③：未声明时效的记录 ⇒ **不**被误报（不得把「未声明」
      当成「已到期」）。**时点由调用方给** ⇒ 同一份数据同一时点判定必相同（可复现）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/application -q` ⇒
      全绿；新判据文件全绿（三态 + 三反证）。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      + `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树
      （**二进制写盘**、`CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、
      仓库 `.venv`、`uv run --frozen --no-sync python -B`、不接管道）；④ 治理 `validate.py`
      绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已在程序表
      序 7**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled` 如实登记
      + 原因 + `covered_by`；空集合 / 空字段 = 未取证；自我指涉边界明写并封闭）；
      ⑥ 承继残余逐条在位（GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` / `R26-*`
      终态 / 未覆盖范围逐条保持 + 理由）；⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      MAINLINE 宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal039_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；治理 `validate.py` 绿；配套留档：
      两路判词 sha256 相同的归档、m0 日志、CI 台账逐提交行。
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
      **把「时效」做成只在测试里生效的旁路**（到期/待复核必须是**产品路径**上可观测的
      事实：读面会读、判定由产品代码算）；**读挂钟做判定**（时点必须由调用方给 ⇒
      同一数据同一时点判定必相同）
    - >-
      **把「未声明时效」当成「已到期」**（缺席一律点名或不报，**不**猜）；
      **改既有门链的语义**（仍是 schema → provenance → policy → gate → commit）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**`、
      `tests/domain/**`、`tests/application/**`、`tests/api/**` **既有文件**）——
      **新增**判据与新增文件不受此限；**新增迁移**属本轮授权（EC-02）
    - >-
      **同轮同步面**：仅当本轮新增字段 / 新读面**必需**时，允许对**既有**登记面做
      **加法 / 搬迁登记**（谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**；
      枚举之外的既有判据仍禁改，触达即 BLOCKED。**新读面 / 新 DTO 字段**按既有纪律同步
      （OpenAPI 快照 + `types.ts` + 隐私读面登记 + 出口普查，由既有判据决定）。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮不动放行面）
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作（**加列 + 回填缺省**不属破坏性；删改既有列的数据属）
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
  - 需要对既有记忆记录做**破坏性**改写（本轮只加列与缺省；不改既有行的语义）
child_plans:
  - .cursor/plans/tasks/PLAN-20261008-351-goal-039-ec02-04-memory-scope-and-validity.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-352-goal-039-ec02-04-memory-scope-and-validity.md
memory_entries: []
---

# GOAL-20261008-039 — 记忆的适用范围与时效成为可判定

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 7**（轴 = **质量**；
> 依赖序 5、6 —— 两者已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3`
> 到期 + 由 GOAL-037/038 的实测残余驱动），已在 MAINLINE 的「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | `scope` 从不落库、两时效列从不被写/被判定、`query` 无时效过滤、§8 明文要求 | PENDING |
| EC-02 | 适用范围落库 | `scope` 成为 canonical 一等字段（迁移 018 + 两适配器往返 + 读面披露） | PASS |
| EC-03 | 声明式时效 | 提案可声明两时点；缺省路径**逐字不变**（判据钉住） | PASS |
| EC-04 | 到期可观测 | 按**调用方给的时点**逐条判定（expired / review_due / None）+ 三反证 | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**读挂钟做判定**；
不得把**未声明时效**当成**已到期**；不得改既有门链语义；不得**宣称项目安全**（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。主树零改动（只读勘察）。

### 1. 「适用范围」：域里有、库里没有、读面读不出（三处断裂）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 提案**有** `scope` 字段 | `packages/domain/memory.py::MemoryWriteProposal` | `scope: str = "project"`（缺省在场） |
| 1.2 | 记录**没有** `scope` 字段 | `packages/domain/memory.py::MemoryRecord` | 字段表里**无** `scope`（只有 tier / kind / content / provenance / confidence / 三时点 / supersedes / contradictions / active） |
| 1.3 | 表**没有** scope 列 | `adapters/sqlite/memory_store.py::_SCHEMA`、`adapters/postgres/memory_store.py` | 两库 DDL 均**无** scope / project 列 |
| 1.4 | PG **忽略**它 | `adapters/postgres/memory_store.py::_to_row` | 逐列写：`None, # valid_from` / `None, # review_after` / `None, # expires_at` —— **scope 连参数都没有** |
| 1.5 | 唯一的 scope 用法是**事件载荷** | `packages/application/memory/gate.py` | `scope=proposal.tier.value`（发事件时用）—— 与落库无关 |

### 2. 「时效」：两列全仓存在、却从不被写、从不被判定

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 域类型**有**两时点 | `packages/domain/memory.py::MemoryRecord` | `review_after: Timestamp \| None` / `expires_at: Timestamp \| None`（**可空**，缺省 `None`） |
| 2.2 | 两库 schema **有**两列 | 两适配器的 `_SCHEMA` / 迁移 | SQLite DDL 与 PG 表定义都在 |
| 2.3 | gate **从不设置** | `packages/application/memory/gate.py`（`rg` 零命中设置点） | `commit_memory` 只做 sanitize / evaluate / allow_source / commit / verify / publish —— **没有任何时点赋值** |
| 2.4 | promotion **从不设置** | `packages/application/run_orchestration/memory_promotion.py` | 构造 `MemoryWriteProposal` 时只给 id / tier / kind / content / provenance / confidence / scope / proposed_by |
| 2.5 | PG **硬编码 `None`** | `adapters/postgres/memory_store.py::_to_row` | 三行注释即证据：`None, # valid_from` / `None, # review_after` / `None, # expires_at` |
| 2.6 | 查询**无时效过滤** | `adapters/sqlite/memory_store.py::query` | 只有 `tier` 过滤（`WHERE tier=?`）或不滤；**没有**任何时点参数 |
| 2.7 | 读面只**转述**两时点 | `services/api/routers/memory.py::_record_dto` | `review_after=... if record.review_after else None` —— 有就转，没就 `None`；**没有任何判定** |

### 3. 契约依据与可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | **§8 明文要求** | AGENTS.md §8 | Project/Organization Memory 必须：有来源 / 有置信度 / **有适用范围** / **有过期/复核策略** / 可删除 / 可重建索引 —— 前两条的**后两条**（范围 / 时效）目前不可判定 |
| 3.2 | 迁移机制现成 | `adapters/postgres/migrations/`（001…017） | 加列 + 缺省回填是既有做法（017 是上一个） |
| 3.3 | 端口现成 | `packages/application/ports/memory_store.py` | `commit` / `get` / `query` / `deactivate` / `delete` / `allow_source` |
| 3.4 | 读面现成 | `services/api/routers/memory.py` | `GET /projects/{id}/memory`（带 `scope_note` 的诚实边界） |
| 3.5 | 既有判据 | `tests/api/test_memory_api.py`、`tests/adapters/sqlite/...`、`tests/postgres/...` | 本轮的**新增**判据要与它们**同轮同步**（夹具 / 计数由既有判据决定） |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 「时效判定」的形态 | **已定**：`expired` / `review_due` / `None` **三态**；**时点由调用方给**（`now`）⇒ **不读挂钟**（同一数据同一时点判定必相同，可复现） |
| ② | 判定的落点 | **已定**：`MemoryStore` 端口上的**显式查询**（新方法或参数化），产品读面调用它；**不**在 DTO 层算（DTO 只转述事实） |
| ③ | `scope` 的取值域 | **已定（收口时复核）**：沿用提案面的既有缺省 `"project"` 语义；**不新造枚举**（值域保持字符串，既有写入不变） |
| ④ | 迁移形态 | **已定**：**只加列**（含 `review_after` / `expires_at` 的就位说明）+ **缺省回填**（既有行读出 `None` / `"project"`）⇒ 既有语义逐字保持；**不删改**任何既有列的数据 |
| ⑤ | 承接面 | **不动**（不需要新能力；本轮只让**既有**读面多两列事实与一条判定） |

## 循环入口协议（幂等重入）

驱动方（会话 / cron / 客户端 goal 模式）进入时，按「迭代日志」最后一行 + 工作树/远端实况
判定续点（与 `goals/README.md` 同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件（迭代日志 / 状态历史 / EC 状态），保证任意时刻崩溃后重入可续；
**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**。

## 单 cycle SOP

- **① derive**：从剩余 EC 圈定一个可独立验收的最小主题；写子 PLAN
  （frontmatter 含 `parent_goal: GOAL-20261008-039` 并投影 `ALL_PLAN`）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**只用显式路径**，
  **绝不 `git add -A`**）。
- **③ 本地验证**：**先写记录 → 立刻跑治理 → 记录面判据 → 全量门**（治理校验器是
  `governance-check/scripts/validate.py`）；m0 按组、**独占**、仓库 `.venv`、
  `uv run --frozen --no-sync python -B`、**不接管道**；受影响的定向套件
  （`tests/domain` / `tests/adapters` / `tests/application` / `tests/api` / `tests/contracts`
  / `tests/postgres`）。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main` → 轮询该
  `head_sha` 的**全部** run。**一个 cycle 攒成一次推送**（同批推送只有 HEAD 产生 run）。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；未达终态 → 回到 ①。

**本轮特有纪律**（逐条在位）：

- **时间由调用方给**（不读挂钟）⇒ 判定可复现；
- **缺省一路保持 `None`**（既有行为**逐字不变**，由判据钉住）；
- **缺席不猜**（未声明时效 ⇒ 不报「已到期」）；
- **迁移只加列 + 缺省回填**（不改既有行的语义）；
- **受判面不得是交集**（承 `MEM-160`）；
- **先复核再依赖**：本 GOAL 的起点事实全部待复核；出入以实测为准；
- **留档二进制写盘**（`newline=""`，CR=0）；判词归档**进树**；
- **台账逐提交**；**批量推送**；进程卫生（`taskkill /T /F`）；记录自洽（同提交）；
- **新记录落地后立刻跑治理**（承 `MEM-20261008-197` / `MEM-20261008-206`）。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP DNS、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 组合跑顺序） | 按既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED |
| 治理/安全门禁 | validator / Mimosa / 记录面判据命中新增项 | 按处置文档修或登记；**不得绕过** |
| 资源阈值型偶发 | 例如 CI 上 RSS < 128MiB 类阈值判据偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类判据红 | **按生成器重新生成**，**不得手改** JSON |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS`（有证据）+ 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS`
  + 本文件收口（`latest_recheck` 指向该 RECHECK + 迭代日志/状态历史回写 + AC/残余/未覆盖
  逐条明写）；收口动作照 `MEM: goal-closeout-procedure` 并声明 `verify_paths` ≥ 2 路、
  **用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers` 或 `budget.max_cycles` 触顶（20）。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-038 的 `P-1`（只到「携带」不到「因果」）/
`P-2`（跨程序共享）/ `P-3`（人工闸门式影响）；GOAL-037 的 `O-1`（memory 项目维度 ——
**本轮补其「适用范围」那一半**，标记保留以见来源）/ `O-2`（程序级人工闸门）/
`O-3`（跨程序共享）/ `O-4`（读到 ≠ 影响；已由 GOAL-038 收其可判定面）/ `O-5`
（决策未落的中间态）；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；
GOAL-019…038 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（随 cycle 增补）

- （建档时登记）**「时效」只到「事实可读」，不到「自动处置」**：本轮让到期/待复核成为
  **可观测事实**（读面披露 + 判定可复核）；**不**自动删除 / 自动降权 / 自动重建索引
  （AGENTS.md §8 的另外两条由既有 `deactivate` / `delete` 承担）。
- （建档时登记）**跨项目 / 跨组织的 scope 语义不在本轮**：`scope` 落库并往返一致，
  但「按 scope 过滤查询」「scope 的鉴权含义」不动（多租户 deferred）。
- （建档时登记）**向量索引侧不在本轮**：索引是 derived（§6），本轮不动它。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **适用范围**：**已收口** = `scope` 落库且读写往返一致；**未覆盖** = 按 scope 过滤与鉴权。
- **时效**：**已收口** = 到期/待复核是**可观测事实**且判定可复现；**未覆盖** = 自动处置
  （删 / 降权 / 重建索引）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ 以 `git credential fill` 取已存令牌走 REST API，按 `head_sha`
> **遍历该 SHA 的全部 run** + `/jobs`；**空集合 / 空字段 = 未取证**；`cancelled` 如实登记
> + 原因 + `covered_by`；现成脚本 `scratch/poll_ci_all.sh <sha>`。**自我指涉边界**：本节的
> 「回顾性台账」提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」封闭，
> **不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `b8c96e3`（GOAL-038 台账尾巴，本轮首行） | 读数在本表回填（**取证中**） | GOAL-038 的最后一个提交（仅 `.cursor/**` 记录改动）—— **GOAL-038 台账的自我指涉边界由本行封闭** |
| （本行所在提交：replan + 建档） | **自身结论尚未产生**（自我指涉边界） | replan（程序表序 7 新增）+ 本 GOAL 五 EC + 事实层读数；其结论由 **cycle 1 的台账行**取证 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261008-351` | （见 CI 台账） | EC-02/03/04 全 PASS：**`scope` 落库**（域 + 迁移 018 只加列 + 三实现同契约 + 读面披露；判据 11 例）+ **声明式时效**（声明 ⇒ 真实值 / 未声明 ⇒ None）+ **到期可观测**（三态纯函数**不读挂钟** + 边界含等号 + `GET .../memory/validity?at=` 读面；三反证）；广面 **4379 passed, 179 skipped**；隐私读面 **133 passed, 2 skipped**；四道门绿（mypy 1166 files） | （见 CI 台账） | **三处真红并修**：① SQLite `INSERT` 硬编码 12 个占位符（加列后 13 列）⇒ 按列数生成；② 新路由首版 POST ⇒ 写面告警线 63→64，复核后判定它是**读面** ⇒ 改 GET（写面回 63）；③ 读面登记首版放错「声明内容」档 ⇒ 撞上界（16>15）⇒ 更正为零命中档 | EC-02/03/04 收口；**下一轮 EC-05**（自举收口） |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 7**（replan 留痕） | （见 CI 台账） | — | 五条 EC 全 PENDING；判定落点（②）与迁移形态（④）待 cycle 1 实现 | cycle 1（EC-02 落库 + EC-03 声明式时效） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACTIVE | **cycle 1（EC-02/03/04）收口**：记忆的**适用范围与时效**从「字段存在但从不落库/从不判定」推到**可判定事实** —— `scope` 成 canonical 一等字段（迁移 018 只加列 + 三实现同契约 + 读面披露）、提案可**声明式**给两时点（缺省路径逐字不变）、到期/待复核按**调用方给的时点**判三态（**不读挂钟** ⇒ 可复现）并经新 GET 读面逐条披露，三反证打满。**三处真红并修**（硬编码占位符 / POST 误入写面 / 读面登记放错档）。EC-02/03/04 `PASS`；EC-05 待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **replan + 建档（cycle 0）**：`replan_every_goals: 3` 到期 ⇒ 对 MAINLINE 程序表做 replan（序 7 **新增**一行，修订记录留痕）；从 GOAL-037/038 的实测残余（`O-1` / `P-1`）里定题 —— **记忆的适用范围与时效从未被判定**。只读勘察三条读数：① `MemoryWriteProposal.scope` 存在但**从不落库**（两库无列、PG 的 `_to_row` 连参数都没有）；② `review_after` / `expires_at` 在域与两库 schema 里都在，但 gate/promotion **从不设置**、PG **硬编码 `None`**、`query` **无时效过滤**（过期记录照常返回）；③ 读面只**转述**两时点、无任何判定。五条 EC 全 `PENDING`。**不做数量目标**；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
