---
id: GOAL-20261010-045
slug: memory-conflicts-and-valid-from-become-decidable
title: 记忆的**冲突**与**生效起点**成为可判定 —— `MemoryRecord` 上这两个字段**没有任何写者**（提案无该字段 / SQLite 静默丢弃 / PG 硬编码 `[]`），且**没有任何消费面**按冲突判定
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 13**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改产品语义、新增判定种类），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) `dataclasses.fields(MemoryWriteProposal)`
    = `['id','tier','kind','content','provenance','confidence','scope','proposed_by',
    'supersedes','review_after','expires_at']` —— **没有** `contradictions` / `valid_from`
    ⇒ 提案方**无从声明**冲突与生效起点；(b) 而 `dataclasses.fields(MemoryRecord)` **有**这两个
    字段 ⇒ 类型上有、**写者零**；(c) `adapters/sqlite/memory_store.py::commit` 从提案构记录时
    **只带** `supersedes=list(proposal.supersedes)`（`scope`/`review_after`/`expires_at` 于
    GOAL-039 补上）⇒ 冲突**静默丢弃**；(d) `adapters/postgres/memory_store.py` 写
    `contradictions` 时的源码注释逐字写着 `empty at commit` ⇒ **两库一致地把它丢成空**；
    (e) **消费面同样为零**：全仓（排除 `tests/`）除域定义与两适配器的读写外，
    **没有任何地方按冲突做判定** ⇒ 「有冲突」既**写不进**也**读不出**。
    (2) **为什么这属于质量轴**：轴定义是「产出的**可判定性**：结论有来源支持 / 实验可复现 /
    覆盖充分，且与评审联动」。**「这条记忆与既有结论冲突」**是来源支持面最需要**看得见**的一类
    事实 —— AGENTS.md §8 明文要求记忆「**有来源、有置信度、有适用范围、有过期/复核策略**」，
    而**冲突与生效起点**是「来源可信」的组成部分（一条与既有结论矛盾却被当成独立证据的记忆，
    会让下游的「来源支持」判断**系统性偏乐观**）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**冲突与生效起点可声明、可落库、可读**，
    且「有冲突」在**至少一条研究路径**上成为**可观测事实**（点名）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / D 组审批通道 / `G24-5` 运行时拦截器 / 部署面验证 / `R26-2/3/4/6` /
    把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**自动消解冲突（不自动挑一方、不自动删除、不自动降权 ——
    那属 `Q-1`/`T-1` 的自动处置面）；**不**做冲突检测算法（「谁和谁冲突」是**声明**，
    不是本 GOAL 去推断）；**不**改 recall / 向量索引（AGENTS.md §6：索引是 derived）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让声明被静默丢弃**（那正是本轮要消灭的形态 —— 声明了却落不进去）；
    **自动消解冲突**（冲突是**事实**，处置是**决定**）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (8) **边界（承继）**：GOAL-001…044 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…044 的未覆盖范围**原样保留**；
    GOAL-044 的 `V-1`…`V-3` / GOAL-043 的 `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` /
    GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` /
    GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**，
    本轮**只追加**。
objective: >-
    让 MAINLINE 序 13（质量轴）落成**冲突与生效起点可判定**：① **勘察定稿** —— 实测
    「两个字段有类型、零写者、零消费者」的完整形状（提案字段表 / SQLite 构记录逐字段 /
    PG 的 `empty at commit` / 全仓消费面普查）（EC-01）→ ② **声明与落库** —— 提案可**声明**
    `contradictions` / `valid_from`（缺省不变：不声明 ⇒ 与既有行为**逐字相同**），
    两库（SQLite / PG）**真的落库并往返一致**（含缺省 `None` / `[]` 的既有语义）（EC-02）
    → ③ **判定与读面** —— **至少一条**研究路径按冲突**点名**（「这条记忆声明与 X 冲突」
    必须可观测；读面**逐条披露**冲突与生效起点）（EC-03）→ ④ **真的被用上（含反证）** ——
    实跑：声明冲突 ⇒ 读面/判词**点名**该冲突与生效起点；**反证**：未声明的记忆**不得**
    凭空出现冲突（`[]` 与 `None` 的语义各归各的：`[]`＝已判定无冲突 / `None` 不适用，
    **互不混用**）；缺字段 / 形态非法 ⇒ **点名**（EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：不声明 ⇒ **逐字不变**；**不**自动消解冲突；**不**做冲突检测算法；
    两库**同契约**（往返一致）；m0 条数**仍是 23**；判词归档**进树**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 提案字段表**无** `contradictions` / `valid_from`
      （逐字列出）而记录字段表**有**；(b) SQLite `commit` 的 `MemoryRecord(...)` 逐字段对照
      （`supersedes` 在场、`contradictions` 缺席）；(c) PG 侧 `contradictions` 的
      `empty at commit` 注释与写入值；(d) **消费面普查**：全仓（排除 `tests/`）除域定义与
      两适配器读写外**零命中**；(e) **反证复现**：`MemoryWriteProposal(**. , contradictions=[...])`
      ⇒ `TypeError`（证明**声明路径根本不存在**）。
    verify: >-
      `uv run --frozen --no-sync python -B -c "import dataclasses; …print(fields)"` ⇒ 两份字段表；
      `rg -n "supersedes=list|empty at commit" adapters/{sqlite,postgres}/memory_store.py`；
      `rg -n "contradictions" --glob '!tests/**' --glob '!scratch/**'` ⇒ 只到域与两适配器；
      构造带 `contradictions=` 的提案 ⇒ `TypeError`。
    status: PENDING
  - id: EC-02
    criterion: >-
      **声明与落库（两库同契约）**：`MemoryWriteProposal` 增**可选** `contradictions` /
      `valid_from`（缺省 `[]` / `None` ⇒ 既有行为**逐字不变**）；SQLite 与 PG 的 `commit`
      都把它们**真的写进去**，`query` / `get` **往返一致**；缺省路径（不声明）在**两库**上
      与修正前**逐字相同**（`[]` / `None`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite
      tests/postgres -q` ⇒ 全绿 + 新用例（两库各一组）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **判定与读面（点名）**：**至少一条**研究路径在记忆**声明了冲突**时**点名**它
      （「与 X 冲突」必须可读，不是只把数组塞进载荷）；读面（既有 `memory.read`）
      **逐条披露** `contradictions` 与 `valid_from`（**不**只披露时效）。
      判定**不读挂钟**（与既有读面同一纪律：`now` 由调用方给）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/adapters/canonical/test_memory_read_dispositions.py -q` ⇒ 全绿 + 新用例
      （冲突在场 ⇒ 点名；`[]` / `None` 语义可分）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **真的被用上（+ 反证）**：(a) 实跑：一条**声明了冲突**的记忆 ⇒ 读面载荷**逐字**带该冲突
      标识与 `valid_from`；(b) **反证臂①**：**未声明**冲突的记忆 ⇒ `contradictions == []`
      **且**读面/判词**不得**凭空出现「有冲突」；(c) **反证臂②**：`valid_from=None`
      **不得**被读成某个具体时点（**不猜**）；(d) 缺字段 / 形态非法（非字符串列表）⇒ **点名**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 13**，进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**；⑥ 承继残余逐条在位；⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal045_closeout.py --root .
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
      **让声明被静默丢弃**（声明了却落不进去 —— 那正是本轮要消灭的形态）；
      **自动消解冲突**（不自动挑一方 / 不自动删除 / 不自动降权：冲突是**事实**，处置是**决定**）；
      **做冲突检测算法**（「谁和谁冲突」是**声明**，不是本 GOAL 去推断）
    - >-
      **把 `[]` 与 `None` 混用**（`[]`＝已判定无冲突 / `None`＝不适用或未声明，语义**互不混用**）；
      **让缺省路径改变**（不声明 ⇒ 与既有行为**逐字相同**）
    - >-
      **动向量索引 / recall 策略**（AGENTS.md §6：索引是 derived）；
      **改任何写 / 执行 / 审批类能力的放行面**
    - >-
      **同轮同步面**：仅当本轮新增可选字段**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
      （谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **改既有判据的申报纪律（承 `MEM-20261009-210`，逐条自证）**：任何对**既有**
      判据 / 测试文件的改动必须 ① **逐条枚举**改动面；② 用
      `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；③ **逐条比对谓词是否
      等同**（不得只写「强度未降」—— 那是一句**需要自证**的断言）；④ **收窄受判面必须
      显式申报**（写明收窄了什么与理由），**不得**称「强度不变」；⑤ 属**同轮同步集之外**
      的形态 ⇒ 命中 `escalation_triggers`，在 RECHECK 里**如实登记**。
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20261010-045 — 记忆的冲突与生效起点成为可判定

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 13**（轴 = **质量**；依赖序 10、12 ——
> 均已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 10/11/12 收口后到期），
> 已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | `contradictions` / `valid_from` **有类型、零写者、零消费者**（提案无字段 / SQLite 丢 / PG 硬编码 `[]`；构造即 `TypeError`） | PENDING |
| EC-02 | 声明与落库 | 提案可**声明**；两库**真的落库**且往返一致；缺省**逐字不变** | PENDING |
| EC-03 | 判定与读面 | **至少一条**路径按冲突**点名**；读面逐条披露冲突与生效起点 | PENDING |
| EC-04 | 真的被用上 | 实跑带出冲突与 `valid_from`；**反证**：未声明不得凭空有冲突、`None` 不得被猜成时点 | PENDING |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PENDING |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**让声明被静默丢弃**；
不得**自动消解冲突**；不得把 `[]` 与 `None` **混用**；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：两个字段**有类型、零写者、零消费者**

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | **提案无该两个字段** | `dataclasses.fields(MemoryWriteProposal)` | `['id','tier','kind','content','provenance','confidence','scope','proposed_by','supersedes','review_after','expires_at']` —— **无** `contradictions` / `valid_from` |
| 1.2 | **记录有该两个字段** | `dataclasses.fields(MemoryRecord)` | 含 `contradictions` 与 `valid_from` ⇒ 类型上有、**写者零** |
| 1.3 | **SQLite 静默丢弃** | `adapters/sqlite/memory_store.py::commit` | 构记录时逐字段给了 `scope` / `review_after` / `expires_at` / `supersedes=list(proposal.supersedes)`，**没有** `contradictions` / `valid_from`（两者落回缺省） |
| 1.4 | **PG 硬编码 `[]`** | `adapters/postgres/memory_store.py` | 写 `contradictions` 处的源码注释逐字：`_json([]),  # contradictions (empty at commit)` |
| 1.5 | **消费面为零** | `rg -n "contradictions" --glob '!tests/**' --glob '!scratch/**'` | 只命中域定义（`packages/domain/memory.py`）与两适配器的读写（sqlite/pg）；**没有任何地方按冲突做判定** |
| 1.6 | **反证复现（声明路径不存在）** | 构造 `MemoryWriteProposal(..., contradictions=["x"])` | **`TypeError: unexpected keyword argument 'contradictions'`** |
| 1.7 | 与序 7 同病 | GOAL-039 的立题（`scope` / `review_after` / `expires_at` 此前**从不落库**） | 序 7 修了那三个；**这两个是同一张表上剩下的两个**（本轮靶子） |
| 1.8 | 与序 10 的关系 | GOAL-042（时效**被消费**） | 序 10 让时效被消费；本条让**冲突与生效起点**成为可判定事实 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 提案→记录的同构映射已存在 | 两适配器的 `commit` | 逐字段复制（`scope` / `review_after` / `expires_at` 已在 GOAL-039 补上）⇒ 本条照同一手法补两个 |
| 2.2 | 读面已逐条披露记忆字段 | `adapters/canonical/memory_read.py::_memory_row` | 已披露 `scope` / `validity` / `disposition` / `reason` ⇒ 本条加两个字段同形 |
| 2.3 | 既有判据面 | `tests/adapters/sqlite/test_memory_scope_and_validity.py`（11 例）/ `tests/postgres/test_memory_scope_pg.py`（2 例）/ `tests/adapters/canonical/test_memory_read_dispositions.py`（15 例） | 本轮新增用例与它们**同族** |
| 2.4 | 迁移惯例 | `adapters/postgres/migrations/018_memory_scope_and_validity.sql` | 两列已在表上（`valid_from` 有列、`contradictions` 有列）⇒ **预期无新迁移**（待 cycle 1 复核） |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 域契约 | `MemoryWriteProposal.__post_init__` / `MemoryRecord.__post_init__` | 各自校验必填与置信度范围 ⇒ 新字段必须**可选**且不破坏既有校验 |
| 3.2 | 两库的读面 schema | `adapters/sqlite/memory_store.py::_MEMORY_COLS` / PG `migrations/018` | 两列**都在表上**（`valid_from` / `contradictions`）⇒ 目标可能是**纯代码修复** |
| 3.3 | 本轮**预期**改动面 | 域 +2 可选字段 + 两适配器 `commit` + 读面 2 字段 + 判据 | 逐条枚举进 RECHECK（含 `numstat`） |

### 4. 本轮**不**碰的面（逐条明写）

- 冲突**消解**（自动挑一方 / 删除 / 降权）—— 属 `Q-1`/`T-1` 的自动处置面；
- 冲突**检测算法**（「谁和谁冲突」是**声明**）；
- 向量索引 / recall 策略（`Q-3` / AGENTS.md §6）；
- 读面认证 / 多租户 / 部署面 / D 组审批通道 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 两个字段的**缺省语义** | **已定**：`contradictions` 缺省 `[]`（＝已判定**无**冲突）；`valid_from` 缺省 `None`（＝**不适用/未声明**，**不猜**） |
| ② | 要不要新迁移 | **待 cycle 1 复核**：两列**似已在表上**（`migrations/018`）⇒ 预期**纯代码**；若需迁移 ⇒ 只加列 |
| ③ | 「至少一条路径点名」落在哪 | **待 cycle 1 定**：候选 = 既有 `memory.read` 的**处置面**（`ANNOTATE`/`SKIP` 旁新增冲突标注）或运行链的既有门 |
| ④ | 冲突的**校验** | **已定**：`contradictions` 必须是**字符串列表**（非列表 / 非字符串元素 ⇒ **点名**）|
| ⑤ | 承接面 | **不动**（不需要新能力） |

## 循环入口协议（幂等重入）

驱动方进入时，按「迭代日志」最后一行 + 工作树/远端实况判定续点（与 `goals/README.md`
同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件；**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**。

## 单 cycle SOP

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261010-045` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/adapters` / `tests/postgres` / `tests/domain` / `tests/e2e`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**不声明 ⇒ 逐字不变**；`[]` 与 `None` **语义互不混用**；**不**自动消解冲突；
两库**同契约**；**改既有判据必须走自证清单**（`MEM-20261009-210`）；受判面不得是交集
（承 `MEM-160`）；留档二进制写盘、判词归档进树；台账逐提交；新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 / **Docker registry 5xx 或限流** | 等窗口重跑 1 次；仍败 → 记录三条取证后 BLOCKED |
| 治理/安全门禁 | validator / Mimosa / 记录面判据 | 修或登记；**不得绕过** |
| 资源阈值型偶发 | CI 上 RSS 类阈值偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类 | **按生成器重新生成** |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS` + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  本文件收口；收口动作照 `MEM: goal-closeout-procedure` 并声明 `verify_paths` ≥ 2 路、
  **用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers` 或 `budget.max_cycles` 触顶（20）。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；GOAL-034…032 的 `W-*`；
历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；GOAL-019…044 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`W-1`…`W-3`）

- `W-1`（**冲突的自动处置不在本轮**，未覆盖；承 `T-1`/`Q-1`）：本轮让冲突**可声明、可落库、
  可点名**；**不**自动挑一方 / 删除 / 降权。
- `W-2`（**冲突检测算法不在本轮**，未覆盖）：「谁和谁冲突」是**声明**；本条**不**推断
  （推断需要语义比对，属另一条线）。
- `W-3`（**`supersedes` 的判定面不在本轮**，未覆盖）：`supersedes` 已在落库面（序 7），
  但「被取代后是否影响判定」**不动**。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **冲突面**：**已收口** = 冲突可**声明**、可**落库**、可**点名**（两库同契约、缺省逐字不变）；
  **未覆盖** = 冲突的**检测**（`W-2`）与**处置**（`W-1`）。
- **生效起点面**：**已收口** = `valid_from` 可**声明**、可**落库**、读面**逐条披露**
  （`None` 不猜）；**未覆盖** = 「在某个时点上是否**已生效**」的判定（本轮只落事实，不做时效外推）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `cd45d38`（replan，本 GOAL 建档所在批） | 待取证 | replan（序 13 新增）+ 建档（五 EC + 事实层读数） |
| （后续逐条填） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **四条实测读数**（提案字段表无该两字段 / SQLite 构记录只带 `supersedes` / PG 注释 `empty at commit` / 全仓消费面零命中）+ **反证** `TypeError`；五条 EC 全 PENDING；MAINLINE 程序表**新增序 13** | （见 CI 台账） | — | 五条 EC 全 PENDING；迁移是否存在（②）与「点名落在哪条路径」（③）待 cycle 1 落 | cycle 1（EC-02 声明与落库 + EC-03 判定与读面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 13**。只读勘察 + **四条实测读数**：(a) `MemoryWriteProposal` **无** `contradictions` / `valid_from` 字段（提案**无从声明**）；(b) `MemoryRecord` **有**这两个字段 ⇒ **有类型、零写者**；(c) SQLite `commit` 从提案构记录时**只带 `supersedes`**（`contradictions` 落回缺省）；(d) PG 写 `contradictions` 处源码注释逐字 `empty at commit` ⇒ **两库一致地把冲突丢成空**；(e) **消费面为零**（全仓排除 tests 只命中域定义与两适配器读写）。**反证**：构造带 `contradictions=` 的提案 ⇒ **`TypeError`**（声明路径根本不存在）。与序 7（同类：字段从不落库）与序 10（时效被消费）同族。五条 EC 全 `PENDING`。**不做数量目标**；**不**自动消解冲突；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
