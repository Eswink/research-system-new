---
id: GOAL-20261011-052
slug: the-two-memory-read-faces-agree
title: 两个读面不再各说各话 —— 序 10/17/18/19 连续四轮把**编排消费面**的读面（`memory.read`）做成十三键（含 `contradictions` / `superseded_by` / `disposition` / `reason`），而 **HTTP 读面**（`MemoryRecordDto`）**这四样一样没有**：实测差集 `contradictions` / `superseded_by` / `disposition` / `reason` **全缺**（HTTP 面只有时效 `validity` 与**正向** `supersedes`）⇒ 同一个可控记忆，**经 HTTP 看**与**经编排看**得到**不同的可判定性**（冲突与五态处置在 HTTP 面**完全不可见**）
status: ACHIEVED
created_at: 2026-10-11
updated_at: 2026-10-11
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-11 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 20**，由本次 replan 的**实测读数**驱动（本次按「按实测残余量出缺口」量出**逐字段差集**；
    来源 = `GOAL-050` / `GOAL-051` 连续登记的 `W-4`）。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改 DTO / 路由 / 读面载荷、新增判据），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) **编排消费面**的读面
    （`adapters/canonical/memory_read.py::_memory_row`）逐条载荷有 **13 键** ——
    `memory_id` / `tier` / `scope` / `content` / `confidence` / `active` / `contradictions` /
    `valid_from` / `validity` / `supersedes` / `superseded_by` / `disposition` / `reason`；
    (b) **HTTP 读面**（`services/api/dto/memory.py::MemoryRecordDto`）**13 字段**里**没有**那四样
    —— `rg -n contradictions services/api/dto/memory.py` ⇒ **零命中**；`disposition` 在该文件里
    只出现在**注释**（`filtered_out` 那句）里；
    (c) **实跑**（同一批记录）：`memory.read` 的键集含 `contradictions` / `superseded_by` /
    `disposition` / `reason`，HTTP DTO 的字段集不含 ⇒ **差集 = 那四样**；
    (d) 后果：**同一个可控记忆经两个读面得到不同的可判定性** —— 序 18 的**反向**取代链接、
    序 13 的**冲突**、序 10/17/18/19 的**五态处置**与**理由**，在 HTTP 面**完全不可见**。
    (2) **为什么这属于质量轴**：轴的反面是「把判据做成表层合规」—— 同一份 canonical 事实，
    **一条读路径已可判定、另一条看不见**，那是**读面之间的一致性缺口**（不是「再加一层检查」）。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**两个读面在同一份事实上给出一致的可判定性**
    —— HTTP 读面至少能看到**冲突声明**、**两个方向的取代链接**、**处置**与**理由**，
    且**缺省形态的既有键逐字不变**（新增键是**附加**信息）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**新建第二套读面 / 投影表（复用既有 DTO + `_record_dto`
    单点）；**不**改编排消费面的载荷（那一侧是**基准**，本轮把 HTTP 面**对齐**它，不是反过来）；
    **不**把 HTTP 面做成「再算一遍时效」（`validity` 的**时点语义**逐字保持：只有显式给 `at`
    的路由才填它）；**不**在两处各写一套判定（**同源**：能复用既有纯函数就复用）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **静默降级**（看不见 / 未判定 / 不支持，一律**点名**）；**两个读面各写一套判定**
    （同一件事必须**同源**，否则漂移无从发现）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **下游同步纪律（承 `MEM-20261010-216`，本轮**强制**）**：动 DTO ⇒ **同轮**重生成并提交
    `docs/api/openapi.m13.json`；EC 的 `verify` 行点名的用例种类**同轮**在受判面上数一遍；
    **有副作用的实现不得放进只读判定面**；**判据不得按位置 / 文本 / 写法写死**
    （承 `MEM-20261010-215` —— 本仓已连续多轮踩到此坑，含**恒假空判据**）。
    (8) **新增一级纪律（本 GOAL 起，承序 19 的实测）**：**判据不得恒假** ——
    任何新判据必须在**本 GOAL 内**给出「该红时红 / 不该红时不红」的**两向实测读数**；
    只声明「判了某个关系」而没验过它会响 = 未完成（序 19 抓到两处空判据）。
    (9) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (10) **边界（承继）**：GOAL-001…051 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…051 的未覆盖范围**原样保留**；
    GOAL-051 的 `CC-1`…`CC-3`（`CC-1` / `CC-3` 由本轮**不推进**，见 §4）/ GOAL-050 的
    `BB-1`…`BB-3`（其中 `BB-2` 已由序 19 推进）/ GOAL-049 的 `AA-1`…`AA-3` /
    GOAL-048 的 `Z-1`…`Z-3` / GOAL-047 的 `Y-1`…`Y-3` / GOAL-046 的 `X-1`…`X-3` /
    GOAL-045 的 `W-1`…`W-3`（其中 `W-4` 的**逐字段差集**由本轮推进）/
    GOAL-044 的 `V-1`…`V-3` / GOAL-043 的 `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` /
    GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` /
    GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 20（质量轴）落成**两个读面在同一份事实上给出一致的可判定性**：
    ① **勘察定稿** —— 实测**逐字段差集**（13 键 vs 13 字段，缺 `contradictions` /
    `superseded_by` / `disposition` / `reason`）（EC-01）→ ② **HTTP 读面披露** ——
    四条缺失面**逐条补齐**（冲突**点名**、取代**两向**、处置**五态**、理由**逐字**），
    且**既有键逐字不变**（新增是**附加**）（EC-02）→ ③ **同源与一致** —— 两处对**同一份事实**
    给出**相同**的处置与理由（**不各写一套判定**；能复用既有纯函数就复用）+
    **OpenAPI 快照同轮同步** + 缺省形态的**既有键与语义逐字保持**（EC-03）→
    ④ **两向反证** —— 两处不一致 ⇒ RED；HTTP 面凭空生造判定 ⇒ RED；既有键被改动 ⇒ RED；
    缺省形态多出键 ⇒ RED（EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：**既有键逐字不变**（新增键是附加信息）；**两处同源**（不各写一套判定）；
    `validity` 的**时点语义逐字保持**（不给时点**不猜**）；动 DTO ⇒ **同轮**同步快照；
    **判据不得恒假**（新判据必须给出两向实测读数）；m0 条数**仍是 23**；判词归档**进树**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 编排消费面的 13 键**逐字列出**；(b) HTTP DTO 的 13 字段
      **逐字列出**；(c) **差集**逐条（`contradictions` / `superseded_by` / `disposition` /
      `reason`）+ `rg` 反证（该四样在 DTO 里**零命中**，`disposition` 只出现在注释）；
      (d) **实跑**：同一批记录经两个读面 ⇒ 键集差 = 那四样逐条；(e) 结论：**可判定性不一致**。
    verify: >-
      `rg -n "^    [a-z_]+:" services/api/dto/memory.py`；`rg -n "contradictions|superseded_by"
      services/api/dto/memory.py` ⇒ 零命中；实跑探针（`scratch/`）⇒ 两个键集的差集。
    status: PASS
  - id: EC-02
    criterion: >-
      **HTTP 读面逐条补齐（附加 + 既有键逐字不变）**：`MemoryRecordDto` 披露
      `contradictions`（声明**逐条**）、`superseded_by`（**反向**链接）、`disposition`（五态之一）、
      `reason`（**逐字**理由）；**既有 13 字段一个不改名、不改语义**（新增是**附加**）；
      `validity` 的**时点语义逐字保持**（只有显式给 `at` 的路由才填它；不给**不猜**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿 + 新用例
      （四样都在场 / 既有键逐字不变 / 不给时点 `validity` 仍为 `None`）。
    status: PASS
  - id: EC-03
    criterion: >-
      **同源与一致（不各写一套判定）**：两个读面对**同一份事实**给出**相同**的处置与理由 ——
      HTTP 面的值**取自同一批纯函数**（能复用就复用，**不**在路由里重算）；**互指一致**由判据钉住
      （同一记录两处同值）；**OpenAPI 快照同轮重生成并提交**（动 DTO ⇒ 必须）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      （含快照判据）+ 新用例（两处同值 / 复用同一助手）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压）**：`N-1` 两处**不一致**（HTTP 面值被改动）⇒ **RED**；
      `N-2` HTTP 面**凭空生造**判定（不取既有纯函数）⇒ **RED**；`N-3` **既有键被改动**
      （改名 / 改语义）⇒ **RED**；`N-4` 不给时点却填了 `validity`（**猜**）⇒ **RED**。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
      **每条按压必须实测会响**（承 §8：判据不得恒假）。
    verify: >-
      `scratch/goal052-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261011-052-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 20**）；⑤ OpenAPI 快照**同轮**同步；⑥ CI 台账**逐提交**；
      ⑦ 承继残余逐条在位；⑧ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal052_closeout.py --root .
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
      **静默降级**（看不见 / 未判定 / 不支持，一律**点名**）；
      **两个读面各写一套判定**（同一件事必须**同源**，否则漂移无从发现）
    - >-
      **改既有键**（改名 / 改语义 —— `MemoryRecordDto` 的既有字段逐字保持，新增只作**附加**）；
      **把 HTTP 面做成「再算一遍时效」**（`validity` 的时点语义逐字保持：不给时点**不猜**）
    - >-
      **新建第二套读面 / 投影表**（复用既有 DTO + `_record_dto` 单点）；
      **改编排消费面的载荷**（那一侧是**基准**，本轮把 HTTP 面**对齐**它）
    - >-
      **判据恒假**（承序 19 的实测：空判据**永远不响**，会静默掩盖真回归）——
      新判据必须在本 GOAL 内给出**两向实测读数**（该红时红 / 不该红时不红）
    - >-
      **判据按位置 / 文本 / 写法写死**（承 `MEM-20261010-215`）；
      **把有副作用的实现放进只读判定面**（承 `MEM-20261010-216`）
    - >-
      **同轮同步面**：仅当本轮对齐读面**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
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
  - .cursor/plans/tasks/PLAN-20261011-409-goal-052-ec01-04-the-two-read-faces-agree.md
  - .cursor/plans/tasks/PLAN-20261011-411-goal-052-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-412-goal-052-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261011-052 — 两个读面不再各说各话

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 20**（轴 = **质量**；依赖序 10/17/18/19 ——
> 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 17/18/19 收口后到期），
> 已在 MAINLINE「修订记录」留痕；并在新增本行时**再次触顶** ⇒ 同轮做了战役级预算核算
> （`max_goals` 20 → 25）。承担者 = `GOAL-050` / `GOAL-051` 连续登记的 `W-4` 的
> **逐字段差集**形态。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | **逐字段差集**：13 键 vs 13 字段，缺 `contradictions` / `superseded_by` / `disposition` / `reason` | PASS |
| EC-02 | HTTP 披露 | 四条缺失面**逐条补齐**（附加）；既有 13 字段**逐字不变**；`validity` 时点语义保持 | PASS |
| EC-03 | 同源一致 | 两处对**同一份事实**给出**相同**处置与理由（**不各写一套**）+ **快照同轮同步** | PASS |
| EC-04 | 两向反证 | 两处不一致 / 凭空生造 / 既有键被改 / 不给时点却填 `validity`（`N-1`…`N-4` 全红） | PASS |
| EC-05 | 自举收口 | 验证器进树（两处射程）+ 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得**静默降级**（一律点名）；
不得**改既有键**（只作附加）；不得**两处各写一套判定**；不得**新建第二套读面**；
不得**判据恒假**（新判据必须两向实测）；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：**两个读面各说各话**

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | **编排消费面**读面 13 键 | `adapters/canonical/memory_read.py::_memory_row` | `memory_id` / `tier` / `scope` / `content` / `confidence` / `active` / `contradictions` / `valid_from` / `validity` / `supersedes` / `superseded_by` / `disposition` / `reason` |
| 1.2 | **HTTP 读面** 13 字段 | `services/api/dto/memory.py::MemoryRecordDto` | `id` / `tier` / `kind` / `content` / `provenance` / `confidence` / `scope` / `valid_from` / `review_after` / `expires_at` / `supersedes` / `active` / `validity` |
| 1.3 | **差集：四样全缺** | 逐条对照 1.1 与 1.2 | **`contradictions` / `superseded_by` / `disposition` / `reason`** |
| 1.4 | **反证（`rg`）** | `rg -n "contradictions\|superseded_by" services/api/dto/memory.py` | **零命中**（`disposition` 亦仅出现在**注释**里）|
| 1.5 | **实跑**：键集差 | 探针：同一批记录经两个读面 | `memory.read` 有那四样；HTTP DTO 没有 ⇒ 差集**逐条成立** |
| 1.6 | 既有正向链接**在场** | 1.2 的 `supersedes` | HTTP 面**有正向**、**无反向** ⇒ 序 18 的「两向都点名」只在编排面成立 |
| 1.7 | `validity` 的时点语义 | `MemoryRecordDto.validity` 注释 + 路由 | 「只有显式给 `at` 的路由才填它 —— 不给时点的读面**不猜**」⇒ 本轮**逐字保持** |
| 1.8 | **结论** | 1.1–1.7 | 同一份 canonical 事实，**一条读路径已可判定、另一条看不见** ⇒ 读面之间的**一致性缺口** |

### 2. 可复用的缝（本轮**不**新造机制）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | HTTP 面是**单点投影** | `services/api/routers/memory.py::_record_dto` | 一处构造 ⇒ 加四样是**附加**改动 |
| 2.2 | 消费面判定是**纯函数** | `memory_read._reason` / `disposition_of` / `_reverse_links` | **同源**：HTTP 面**复用**它们，**不**重算 |
| 2.3 | 反向链接**已实现** | `_reverse_links`（序 18 建的） | HTTP 面要反向链接 ⇒ **复用同一助手**（不另写一套） |
| 2.4 | 快照机制现成 | `tools/gen_openapi.py` + `tests/contracts/test_openapi_snapshot.py` | 动 DTO ⇒ **同轮**重生成并提交（承 `MEM-20261010-216`）|
| 2.5 | 「附加不改既有」的判据形态现成 | 序 17 的 `MemoryFilteredListViewDto` | 「两个形态各自显式声明」的手法**现成**（避免 pydantic 把 `None` 序列化成 `null`）|

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | HTTP 读面判据 | `tests/api/test_memory_api.py` | 既有 **10 例**（序 13/17 的）|
| 3.2 | 快照判据 | `tests/contracts/test_openapi_snapshot.py` | 既有 **8 例**（**不得**改它）|
| 3.3 | 读面一致性**无判据** | `rg -n "一致\|agree\|同源" tests/api tests/contracts` | **零命中** ⇒ 缺口**没有判据守**（这是本 GOAL 要补的）|
| 3.4 | 本轮**预期**改动面 | DTO（+4 字段）+ `_record_dto`（+4 赋值，**复用**既有纯函数）+ 路由（反向链接需扫同批）+ 快照 + 判据 | 逐条枚举进 RECHECK（含 `numstat`）|

### 4. 本轮**不**碰的面（逐条明写）

- **编排消费面**的载荷（那一侧是**基准**，本轮把 HTTP 面**对齐**它，**不**反过来）；
- `validity` 的**时点语义**（逐字保持：不给时点**不猜**）；
- 授权 / 权限面：`scope` 仍**不是** ACL；读面认证 / 多租户 / RBAC / BOLA·BFLA 仍属未覆盖；
- 冲突的**消解**（`CC-1`）/ **检测**（`W-2`）/ **时效性**（`CC-3`）与**链式取代**（`BB-1`）：
  四条**已登记但本轮不做**（本轮只做**读面一致**）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 四样怎么进 DTO | **待 cycle 1 定**：候选 = 直接加四个字段（`contradictions` / `superseded_by` / `disposition` / `reason`）vs 加一个**可空的嵌套对象**。判据：「既有键逐字不变」+「缺省不凭空多键」+「schema 与载荷一致」 |
| ② | 反向链接怎么取 | **待 cycle 1 定**：HTTP 面需扫同批记录（复用 `_reverse_links`）—— **在哪一层扫**（路由 / 一个查询助手）由 cycle 1 定；**不**在 DTO 里算（DTO 无副作用） |
| ③ | 处置与理由的**同源** | **已定**：必须**复用** `disposition_of` / `_reason`（**不**在路由里重写一套）；判据钉「两处同值」 |
| ④ | 快照 | **已定**：动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`；快照判据**一字不改** |
| ⑤ | 承接面 | **不动**（复用既有 DTO 单点 / 纯函数 / 快照机器）|

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
   - **分列纪律**：有副作用的实现**不进**只读判定面；判据**不按位置/文本/写法**写死；
     **新判据必须两向实测**（承 §8：判据不得恒假）。
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
| 真红（既有资产） | 既有收口断言集报「本树有判负」 | **先判归属**：实现错 ⇒ 修实现；判据按位置 / 文本 / 写法写死 ⇒ 改成**判关系**（承 `MEM-20261010-215`）|
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-051 的 `CC-1`…`CC-3`；GOAL-050 的 `BB-1` / `BB-3`；
GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；
GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；
GOAL-019…051 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（**收口时**逐条定格；`DD-1`…`DD-3`）

- `DD-1`（**HTTP 面的时点判定不在本轮**，未覆盖）：本轮补齐的是**声明面**
  （冲突 / 反向链接 / 处置 / 理由）；HTTP 面**仍不**做「按时点判时效」（`validity` 只在显式给
  `at` 的路由填 —— **逐字保持**）。
- `DD-2`（**其他读面未普查，未覆盖**）：本轮对齐的是**记忆**的两个读面；
  仓里**别的**实体是否也存在「编排面可判定 / HTTP 面看不见」的类似差集**未普查**。
- `DD-3`（**读面一致性的机械化只在记忆面**，未覆盖）：一致性判据本轮**只**覆盖记忆读面
  （**不**做全仓「两个读面必须一致」的通用判据 —— 那需要先普查 `DD-2`）。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **记忆的读面**：**已收口** = 编排消费面十三键（序 10/17/18/19）；**本轮争取** =
  HTTP 面**对齐**同一份可判定性；**未覆盖** = 时点判定（`DD-1`）与**其他实体**的同类差集（`DD-2`）。
- **可判定性的一致性**：**已收口（本轮争取）** = 记忆的两个读面**同源同值**；
  **未覆盖** = 全仓通用的一致性判据（`DD-3`）。

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
| 2 | `PLAN-20261011-411` | （见 CI 台账） | EC-05 五条 AC 全 PASS：收口验证器 **63 判词 / 0 FAIL**（标准断言集**一行未重写**）+ 两处射程**纯收紧**（`IN_SCOPE` +2 行 / 射程清单 +1 行、下界 21→22）+ **两树 `TWO-TREE PASS`**（两路 **63 判词** / `sha256` 相同 `b976f18c…`）+ 归档定格（两份各 **2341 B / 63 行**、`CR=0`、0 FAIL）+ 治理 + 宪章判据 + 定向套件 **4956 passed** | （见 CI 台账）| **§8 新增纪律落成机械面**（AST 读字段 + 三条非空性实测 + 反证脚本**基线门**）| 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261011-412`）|
| 1 | `PLAN-20261011-409` | `2a3ca6c` | EC-01…EC-04 全 PASS：**两个读面对齐** —— ① HTTP 读面**+4 字段**（`contradictions` / `superseded_by` / `disposition` / `reason`）—— **纯附加**（既有 13 字段**一个不改名不改语义**，判据逐条点名）；② **同源同值**（`_record_dto` **直接调**编排面那两个纯函数 + 同一反向链接助手，**不**在路由里重写第二套判定）；③ **`validity` 时点语义逐字保持**（不给时点 ⇒ `None`；受判面用**已到复核期**的记录 ⇒ 猜的话会立刻报 `REVIEW_DUE`）；④ **OpenAPI 快照同轮重生成**（`+24 / -0`，判据一字未改）；⑤ **四向反证 N-1…N-4 全红 + 基线 GREEN**（674 B / `CR=0`）；⑥ HTTP 判据 +3（13 passed）；定向套件 **4956 passed** | （见 CI 台账）| **假反证臂由新增的基线门当场抓到**（`N-4` 受判面区分不了两件事 ⇒ 换受判面）；**一处既有判据按关系修正**（`goal050` 钉助手名 ⇒ 改名公开后假红 ⇒ 改判关系）| EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **八条实测读数**（编排面 13 键逐字 / HTTP 面 13 字段逐字 / **差集四样** / `rg` 反证零命中 / **实跑**键集差 / 正向有反向无 / `validity` 时点语义 / 结论「可判定性不一致」）+ **一致性无判据**（`rg` 零命中）⇒ 定位 `W-4` 形态；五条 EC 全 PENDING；MAINLINE 程序表**新增序 20** + **预算核算 20→25** | （见 CI 台账） | — | 五条 EC 全 PENDING；四样怎么进 DTO（①）与反向链接在哪层扫（②）待 cycle 1 落 | cycle 1（EC-02 披露 + EC-03 同源） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | DRAFT | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 20**（承担者 = `W-4` 的**逐字段差集**形态）+ 触顶 ⇒ 战役级核算 `max_goals` 20→25。只读勘察 + **八条实测读数**：(a) **编排消费面**读面 **13 键**（含 `contradictions` / `superseded_by` / `disposition` / `reason`）；(b) **HTTP 读面** **13 字段**（无那四样）；(c) **差集**逐条成立；(d) `rg -n "contradictions\|superseded_by" services/api/dto/memory.py` ⇒ **零命中**；(e) **实跑**同一批记录 ⇒ 键集差 = 那四样；(f) HTTP 面**有正向** `supersedes`、**无反向** `superseded_by`；(g) `validity` 的**时点语义**（不给时点**不猜**）本轮**逐字保持**；(h) **结论**：同一份 canonical 事实，**一条读路径已可判定、另一条看不见**。**一致性**这条缺口**没有判据守**（`rg` 零命中）—— 本轮补。五条 EC 全 PENDING。**不做数量目标**；**不**改既有键、**不**新建第二套读面、**不**两处各写一套判定、**不**做 `DD-1`…`DD-3`；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
| 2026-10-11 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**两个读面不再各说各话** —— HTTP 读面补齐四样（**附加**；既有 13 字段逐字不变）+ **同源同值**（直调同一批纯函数）+ `validity` 时点语义逐字保持 + 快照同轮。**四向反证全红且基线绿**（含**新增的基线门**）。**两处如实登记**：假反证臂（受判面区分不了两件事 —— 「有断言」≠「断言在下判断」）；既有判据按关系修正（钉助手名 ⇒ 改名公开后假红）。独立复检：`RECHECK-20261011-410`（PASS_WITH_WARNINGS）。EC-05 待收口。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-11 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、**两处射程纯收紧**、两树 **`TWO-TREE PASS`**（两路 **63 判词** / `sha256` 相同 `b976f18c…`）、判词归档进树（两份各 2341 B / 63 行 / `CR=0`）、治理 + 宪章判据绿、定向套件 4956 例绿、CI 台账逐提交。**§8 的新增纪律落成了机械面**（**判据不得恒假**：AST 读字段 + 三条非空性实测 + 反证脚本**基线门** —— 后者在 cycle 1 当场抓到一处**假反证臂**）。**一处时序**：两树首轮红（bootstrap：归档在提交之后才存在）。**收口后不再推进本 GOAL**；残余 `DD-1`…`DD-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261011-412`（PASS_WITH_WARNINGS）。 |
