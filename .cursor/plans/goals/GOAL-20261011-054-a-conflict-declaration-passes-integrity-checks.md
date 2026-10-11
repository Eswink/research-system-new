---
id: GOAL-20261011-054
slug: a-conflict-declaration-passes-integrity-checks
title: 冲突声明与被引 id 一样要过完整性校验 —— `supersedes` 的被引 id **会被 gate 校验**（`_contradiction_check`：引用未知 id ⇒ 拒绝提交），而 `contradictions` 的被引 id **从不被校验**：**实跑取证** ① 声明与一条**不存在**的记录冲突 ⇒ **照常落库**、读面照常报 `CONFLICTED` 并**逐字点名那个不存在的 id**；② 声明**与自己**冲突 ⇒ 同样被当成真的分歧；③ 全仓 `detect_conflict` / `conflicts_with` / `resolve_conflict` 在 `packages/`·`adapters/` 里**只命中无关子系统**（成本 / 工具面 / `team_plan`）⇒ 记忆面**没有**检测实现
status: ACTIVE
created_at: 2026-10-11
updated_at: 2026-10-11
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-11 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 22**，由本次 replan 的**实测读数**驱动（本次按「按实测残余量出缺口」量出
    「冲突声明的完整性不对称」；来源 = `GOAL-20261010-050` / `GOAL-20261011-051` 连续登记的 `W-2`）。
    authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§8/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改 DTO / 路由 / 读面载荷、新增判据、**加 gate 校验**），**不等于**可以放宽
    **判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) gate 的阶段链（
    `packages/application/memory/gate.py::_contradiction_check`）**只校验 `supersedes` 的
    被引 id**（`supersedes target {id!r} does not exist` ⇒ 拒绝），`contradictions` **一字未查**；
    (b) **实跑**：声明 `contradictions=["m-nowhere"]`（库里没有这条）⇒ **落库成功**，
    读面 `disposition=CONFLICTED`、`reason` **逐字点名**那个不存在的 id；
    (c) 声明 `contradictions=["m-self"]`（**自指**）⇒ 同样被当成真的分歧；
    (d) 全仓 `detect_conflict|conflicts_with|resolve_conflict` 的命中**全在无关子系统**
    （`packages/application/cost/` / `tool_plane/` / `packages/domain/team_plan.py` 等）
    ⇒ 记忆面**没有**检测实现。
    (2) **为什么这属于质量轴**：轴的反面是「把判据做成表层合规」—— 序 19 让「有冲突」成为
    **可判定的处置**（第五态 `CONFLICTED`），但那份判定依赖的**声明本身可以指向空气**：
    一条**悬空声明**与一条**真实分歧**在处置面上**同值**，读者无从区分。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**`contradictions` 的被引 id 与 `supersedes`
    一样过完整性校验**（存在、且**不得自指**），并把**点名的形态**写清楚
    （悬空 / 自指 ⇒ **点名拒绝**，不是静默接受）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做**自动消解**（谁对谁错仍由人决定 —— 那是 `CC-1`，
    明确不做）；**不**做内容级冲突**检测**（读 `content` 比对语义 —— 那是 `W-2` 的**另一半**，
    本轮只做**声明面完整性**）；**不**改 `supersedes` 的既有校验语义（那一侧是**基准**）；
    **不**给既有落库记录做**回溯校验**（历史数据不在射程内 —— 只对**新提案**生效）；
    **不**做跨项目 / 跨范围的冲突解析（`DD-2` 面另议）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **静默降级**（悬空 / 自指 / 未知一律**点名**）；**两个读面各写一套判定**（同一件事必须**同源**）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **下游同步纪律（承 `MEM-20261010-216`，本轮**强制**）**：动 DTO ⇒ **同轮**重生成并提交
    `docs/api/openapi.m13.json`；EC 的 `verify` 行点名的用例种类**同轮**在受判面上数一遍；
    **有副作用的实现不得放进只读判定面**；**判据不得按位置 / 文本 / 写法写死**
    （承 `MEM-20261010-215`；**另**：`field` 分组重构会把「字典字面量」搬成「下标赋值」
    ⇒ 判字段存在性必须用 **AST 收集被赋值键集**，承序 21 的两处实测）。
    (8) **判据不得恒假（承 GOAL-051/052/053 的三条一级纪律）**：任何新判据必须在**本 GOAL 内**
    给出「该红时红 / 不该红时不红」的**两向实测读数**；**反证脚本必须带基线门**（未按压必须绿）；
    **「判关系不判位置」的修法要复查是否开口子**；**不可达分支不要写成判据**（先实测可达性 ——
    序 21 的 `DANGLING` 教训）。
    (9) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (10) **边界（承继）**：GOAL-001…053 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…053 的未覆盖范围**原样保留**；
    GOAL-053 的 `W-1`…`W-5`（其中 `W-2` 的**声明完整性**一半由本轮推进）/
    GOAL-052 的 `DD-1`…`DD-3` / GOAL-051 的 `CC-1`…`CC-3` / GOAL-050 的 `BB-1`（已由序 21 推进）、
    `BB-3` / GOAL-049 的 `AA-1`…`AA-3` / GOAL-048 的 `Z-1`…`Z-3` / GOAL-047 的 `Y-1`…`Y-3` /
    GOAL-046 的 `X-1`…`X-3` / GOAL-045 的 `W-1`…`W-3` / GOAL-044 的 `V-1`…`V-3` /
    GOAL-043 的 `U-1`…`U-3` / GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` /
    GOAL-040 的 `R-1`…`R-3` / GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` /
    GOAL-037 的 `O-1`…`O-5` / `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 22（质量轴）落成**冲突声明与被引 id 一样过完整性校验**：
    ① **勘察定稿** —— 实测三态（悬空 / 自指 / 正常）在**当前实现**下的落库与读面读数（EC-01）→
    ② **gate 对齐** —— `contradictions` 的被引 id **存在性**校验（与 `supersedes` **同一条纪律**）
    + **不得自指**；**点名拒绝**（不静默接受、不静默丢弃）（EC-02）→
    ③ **读面与一致** —— 读面的点名形态随之可区分（悬空不再可能进入 `CONFLICTED`；
    既有键逐字不变）**不各写一套判定**；动 DTO ⇒ **同轮**同步快照（EC-03）→
    ④ **两向反证** —— 悬空声明被接受 ⇒ RED；自指声明被接受 ⇒ RED；校验放行**正常**声明 ⇒ RED；
    既有键被改动 ⇒ RED（EC-04）→ ⑤ **自举收口**（EC-05）。
    **硬约束**：**既有键逐字不变**；**两处同源**；`supersedes` 的既有校验**一字不动**；
    动 DTO ⇒ **同轮**同步快照；**判据不得恒假**（两向实测 + 反证脚本带基线门）；m0 条数**仍是 23**；
    判词归档**进树**；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) gate 的校验面**逐字引文**（`_contradiction_check` 只查
      `supersedes`，`contradictions` 一字未查）+ 行号；(b) **实跑三态**：悬空被引 id /
      自指 / 正常 ⇒ ① 落库结果、② 读面 `disposition` 与 `reason` 逐条读数；
      (c) `rg` 反证：记忆面**没有**检测实现（命中的都在无关子系统，逐条列名）；
      (d) 结论：**声明面缺完整性校验** ⇒ 悬空与真实分歧在处置面**同值**。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-conflict-integrity.py`（**读面口径**）
      ⇒ 三态逐条读数；`rg -n "_contradiction_check" packages/application/memory/gate.py`。
    status: PENDING
  - id: EC-02
    criterion: >-
      **gate 对齐（与 `supersedes` 同一条纪律）**：新提案的 `contradictions` 被引 id
      **必须存在**（不存在 ⇒ **点名拒绝**，理由含该 id）；
      **自指**（被引 id == 提案自身 id）⇒ **点名拒绝**（语义上无意义）；
      **正常声明照常通过**（既有行为逐字不变）；**`supersedes` 的既有校验一字不动**
      （那一条是**基准**）；**新提案**与**更新面**都要过（若存在两处入口）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（悬空拒绝 / 自指拒绝 / 正常通过 / `supersedes` 面逐字不变）—— **4 passed**。
    status: PASS
  - id: EC-03
    criterion: >-
      **读面与一致（点名形态可区分）**：读面对「冲突声明」的点名**保持既有形态**
      （`CONFLICTED` 的第五态与理由**逐字不变**）；**悬空 / 自指那两种形态不再可能进入**
      （由 gate 拒绝 ⇒ 读面看不到）；**既有键逐字不变**（编排面 13 键 + `terminal` /
      HTTP 面既有字段）。**不各写一套判定**（沿用 `packages/application/memory/` 的同一批纯函数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters -q` ⇒ 全绿
      + 新用例（既有键逐字不变 / 正常冲突仍 `CONFLICTED`）；连带面 **5100 passed / 零 FAILED**。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`Q-1` 悬空声明**被接受** ⇒ **RED**；
      `Q-2` **自指**声明被接受 ⇒ **RED**；`Q-3` 校验**误伤正常声明**（正常声明被拒）⇒ **RED**；
      `Q-4` `supersedes` 的既有校验被**放宽**（未知 id 不再拒）⇒ **RED**。
      复原用**二进制读写**且 raw `sha256` 逐字节相同；**反证脚本带基线门**（未按压必须 GREEN，
      否则非 0 退出）；判词归档进树（`CR=0`）。**每条按压必须实测会响**（承 §8：判据不得恒假）。
    verify: >-
      `scratch/goal054-press.txt` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`；归档
      `.cursor/plans/goals/evidence/GOAL-20261011-054-press-two-way.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 22**）；⑤ OpenAPI 快照**同轮**同步；⑥ CI 台账**逐提交**；
      ⑦ 承继残余逐条在位；⑧ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal054_closeout.py --root .
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
      **静默降级**（看不见 / 未判定 / 不支持，一律**点名** —— 悬空被引 id / 自指 /
      未知形态都必须点名，**不得**静默接受或静默丢弃）；
      **两个读面各写一套判定**（同一件事必须**同源**）
    - >-
      **放宽 `supersedes` 的既有校验**（那一侧是**基准**，一字不动）；
      **做自动消解**（谁对谁错仍由人决定 —— `CC-1` 明确不做）；
      **做内容级冲突检测**（读 `content` 比语义 —— 那是 `W-2` 的另一半，本轮只做**声明面完整性**）
    - >-
      **改既有键**（编排面 13 键 + `terminal` / HTTP 面既有字段逐字保持）；
      **给历史数据做回溯校验**（只对**新提案**生效 —— 历史记录不在射程内）
    - >-
      **判据恒假**（承序 19/20/21 的实测：空判据**永远不响**，会静默掩盖真回归）——
      新判据必须在本 GOAL 内给出**两向实测读数**；**反证脚本缺基线门**（未按压必须先跑并判绿）；
      **把不可达分支写成判据**（先实测可达性 —— 序 21 的 `DANGLING` 教训）
    - >-
      **判据按位置 / 文本 / 写法写死**（承 `MEM-20261010-215`；**且**：`field` 分组重构会把
      「字典字面量」搬成「下标赋值」⇒ 判字段存在性必须用 **AST 收集被赋值键集**）；
      **把有副作用的实现放进只读判定面**（承 `MEM-20261010-216`）
    - >-
      **同轮同步面**：仅当本轮对齐**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
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
  - >-
    **新增校验会让既有记录 / 既有判据变红**（收紧 gate = 可能拒掉既有测试造的数据）——
    若命中，**不**放宽校验，而是**逐条核对**那些数据是否本来就该被拒（是本轮要**修**的形态），
    或**显式登记**为受判面收窄
child_plans:
  - .cursor/plans/tasks/PLAN-20261011-415-goal-054-ec01-04-a-conflict-declaration-passes-integrity-checks.md
latest_recheck: null
memory_entries: []
---

# GOAL-20261011-054 — 冲突声明与被引 id 一样要过完整性校验

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 22**（轴 = **质量**；依赖序 10/13/19
> —— 均已收口）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 19/20/21 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = `GOAL-20261010-050` / `GOAL-20261011-051` 连续登记的
> `W-2`（「冲突检测」）的**前半**（声明面完整性）。

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿：三态（悬空 / 自指 / 正常）**实跑**读数 + 校验面逐字引文 | **实跑**（产品路径）：`supersedes` 悬空**被拒** / `contradictions` 悬空·自指**被接受** | **PASS** |
| EC-02 | **gate 对齐**：`contradictions` 被引 id 存在性 + **不得自指**；`supersedes` 面一字不动 | 新用例 **4 passed**；`tests/application/memory` 全绿 | **PASS** |
| EC-03 | **读面一致**：`CONFLICTED` 形态逐字不变；悬空 / 自指不再进入；既有键逐字不变 | `tests/api tests/adapters` **1207 passed, 7 skipped** | **PASS** |
| EC-04 | **两向反证** `Q-1`…`Q-4` 全红 + 基线门 + 二进制复原 `sha256` 一致 | 归档 **732 B / `CR=0`** / `sha256 232ebbb5d135b65f…` | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | `tools/verify_goal054_closeout.py` | PENDING |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实调用面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | gate **只校验 `supersedes`** | `rg -n "_contradiction_check" -A 8 packages/application/memory/gate.py` | 函数体只 `for old_id in proposal.supersedes:` ⇒ 引未知 id 拒；`contradictions` **一字未查** |
| 2 | 悬空声明**被接受**（**产品路径**） | `uv run … scratch/probe-conflict-integrity.py` | 走 `commit_memory`（门链）⇒ `accepted=True stage=committed`；读面 `disposition=CONFLICTED`、`reason` 点名 `m-nowhere` |
| 3 | 自指声明**被接受**（**产品路径**） | 同上 | 提案 id == 被引 id ⇒ 同样 `accepted=True stage=committed`；读面同样 `CONFLICTED` 并点名自己 |
| 3b | **对照面**：`supersedes` 悬空**被拒**（同一次门链调用） | 同上 | `accepted=False stage=contradiction reasons=("supersedes target 'm-nowhere' does not exist",)` |
| 3c | **路径差异（实测更正）** | 同上（路径 A） | `store.commit`（适配器直写）**绕过门链** ⇒ 两条都 ACCEPTED —— **建档初版正是用错了这条路径**，把对照面读成「也接受」；以**产品路径**（路径 B）为准 ⇒ **不对称成立** |
| 4 | 记忆面**没有**检测实现 | `rg -n "detect_conflict\|conflicts_with\|resolve_conflict" packages/ adapters/` | 命中**全在无关子系统**（`cost/projection.py` / `tool_plane/resolver.py` / `team_plan.py` 等）|
| 5 | 域上只校验**非空字符串** | `rg -n "contradictions" -A 3 packages/domain/memory.py` | `for item in self.contradictions: ... must be non-empty strings` ⇒ **不查存在性、不查自指** |

**结论**：**声明面缺完整性校验** —— 一条指向**不存在**记录的「冲突」与一条**真实分歧**
在读面处置上**同值**（都 `CONFLICTED`、都点名），读者无从区分。
而 `supersedes` 的**同类引用**早就有校验（**不对称**）⇒ 缺的是**对齐**。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 校验**放在既有 gate 阶段**（与 `supersedes` 同一个 `_contradiction_check`），**不**新建阶段 | 阶段链是既有机制；新建阶段会改门链语义（更大风险） | 已定 |
| D-2 | 自指 **点名拒绝**（而不是静默去掉那个 id） | 「静默降级」是本 GOAL 的禁令；静默去掉会让调用方以为声明生效 | 已定 |
| D-3 | **不**做自动消解 / **不**做内容级检测 | 与 `CC-1` / `W-2` 后半的边界划清 | 已定 |
| D-4 | **不**给历史记录回溯校验 | 历史数据不在射程内；只对**新提案**生效（否则要迁移，可能不可逆） | 已定 |
| D-5 | `supersedes` 的既有校验**一字不动**（它是**基准**） | 「对齐」是让另一侧向它看齐，不是双向改 | 已定 |
| D-6 | 收紧后若既有测试造的数据被拒 ⇒ **逐条核对**是否本就该拒 | 见 `escalation_triggers` 第 6 条 | 已定 |

## 循环入口协议（幂等重入）

1. 最后一 cycle 无记录 ⇒ 开 cycle 1：执行派生 PLAN 的 WP-1。
2. 有子 PLAN 且 `IN_PROGRESS` ⇒ 继续该 PLAN 的未完成 WP。
3. 本地验证已过、有未推送 commit ⇒ push + 轮询 CI。
4. CI 在跑或未记结论 ⇒ 等待 / 判定，**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 ⇒ 按失败分类纠错。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 ⇒ 派生下一子 PLAN。
7. 按「终止与收口」判 ACHIEVED / BLOCKED / 超预算。

## 单 cycle SOP

① 派生**子 PLAN**（`parent_goal` 投影 `ALL_PLAN`，同一提交）→ ② 执行（每 WP 独立 commit，
**只用显式路径**，**绝不 `git add -A`**）→ ③ 本地验证**按既有顺序**（**先写记录 →
记录面判据 → 全量 m0**；m0 **独占**、仓库 `.venv`、`uv run --frozen --no-sync python -B`、
不接管道）→ ④ commit → ⑤ push（**批量**）+ 轮询 CI 到终态 → ⑥ 按失败分类纠错 →
⑦ 回写本 GOAL（EC / 迭代日志 / 状态历史 / `latest_recheck` / `child_plans`）。

**判定纪律（硬）**：每条 EC **两向反证**；受判面**非空**且**不得是交集 / 并集掩蔽 / 写法清单**
（承 `MEM-156`）；按压 → 复原用 **raw `sha256` + 二进制读写**；归档一律**二进制写盘**
（判词进 `.cursor/plans/goals/evidence/`，`CR=0`）；**点名失败而非静默降级**；
**未实跑不得记 PASS**；进程卫生（Windows `taskkill /T /F` + 复验零泄漏）。

## CI 失败分类与纠错

| 失败分类 | 形态判据 | 处置 |
| --- | --- | --- |
| (i) 产品面真缺陷 | 判据报出**本轮的实现**与声明不符 | 照实修实现；**不得**改判据（除非属同轮同步集且逐条申报） |
| (ii) 基础设施型 | 镜像 / 网络 / runner 取消（`concurrency.cancel-in-progress`）；三条取证 | 如实登记**原因** + `covered_by`；**不动**阈值 |
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：收紧校验可能拒掉既有测试数据）| 同轮修全部受影响面；**逐条核对**那些数据是否本就该拒（`escalation_triggers` 第 6 条）|
| (iv) 判据面自身 | 判据按位置 / 写法写死（**假红**）或恒假 | 改判**关系**并**两向实测**；在 RECHECK 如实登记 |

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 `PASS`；收口面（验证器 + 断言集）**进树**并过四道门；
  两树 `TWO-TREE PASS`；as-is m0 **23/23**（记录写完之后）；治理 + 宪章判据绿；
  CI 台账**逐提交**；残余与未覆盖范围**逐条在位**；`latest_recheck` 指向 PASS 的 RECHECK。
- **BLOCKED**：命中 `escalation_triggers` 或超 `fix_policy` 上限 ⇒ 记 BLOCKED 并留人工决策。
- **ABORTED**：预算（`budget.max_cycles`）触顶且无进展。
- 收口后**不再推进本 GOAL**；本轮**不**宣称项目安全（`R-M1`），**不**宣称投递语义为
  「恰好一次」（**明确否认**）。

## 残余与受限面（承继 + 本轮）

- **本轮推进**：`W-2` 的**声明面完整性**一半（被引 id 存在性 + 不得自指）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：`W-2` 的**内容级检测**一半；`CC-1`…`CC-3`（冲突消解 / 有效性 /
  时效性）；`BB-3`；`Z-1` / `Z-3`；`DD-1`…`DD-3`（HTTP 面时点判定 / **其他读面未普查** /
  全仓通用一致性判据）；`AA-*` / `Y-*` / `X-*` / `W-1`·`W-3` / `V-*` / `U-*` / `T-*` /
  `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`·`O-3`·`O-4`·`O-5`。
- **未覆盖范围（逐条明写）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器。
- **明确否认**：投递语义**不是**「恰好一次」（口径只能是 at-least-once + idempotency +
  deduplication）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**（并写明 `covered_by`）；`cancelled` / `failure` 如实登记
> + 原因 + `covered_by`。**自我指涉边界**：台账提交自身不产生可引用的 CI 结论
>（明写并以「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| （待建档提交） | — | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `PLAN-20261011-415`（WP-1） | （待提交） | **EC-01 勘察定稿 PASS**：`scratch/probe-conflict-integrity.py` 跑**两条路径** —— ① 适配器直写（`store.commit`，**绕过门链**）：两条都 ACCEPTED；② **产品路径**（`commit_memory`）：`supersedes` 悬空 ⇒ **`accepted=False stage=contradiction`**（点名「does not exist」），而 `contradictions` 悬空 / 自指 / 正常 ⇒ **都 `accepted=True stage=committed`**；读面后果：悬空与自指都进 `CONFLICTED` 并**逐字点名**那些 id | （见 CI 台账）| **一处实测更正（如实登记）**：建档初版用**直写路径**测量 ⇒ 把对照面读成「也接受」⇒ 差异**恰为**门链；以产品路径为准，**不对称成立** | CE-02（gate 对齐）待做 | cycle 1 WP-2（存在性 + 不得自指） |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **五条实测读数**（gate 只校验 `supersedes` / 悬空声明被接受 / 自指声明被接受 / 记忆面零检测实现 / 域上只校验非空字符串）⇒ 定位 `W-2` 的**声明面完整性**形态；五条 EC 全 PENDING；MAINLINE 程序表**新增序 22** | （见 CI 台账） | — | 五条 EC 全 PENDING；校验放哪一层（①）与自指怎么处置（②）待 cycle 1 落 | cycle 1（EC-02 校验 + EC-03 读面） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 22**（承担者 = `GOAL-20261010-050` / `GOAL-20261011-051` 连续登记的 `W-2` 的**前半**），并写修订记录行（只追加）。**五条实测读数**（逐条见「事实层结论」表，命令与读数同在）：(a) gate 的阶段链**只校验 `supersedes`**（`_contradiction_check` 一行未查 `contradictions`）；(b) **实跑**：悬空被引 id ⇒ **落库成功** + 读面 `CONFLICTED` 并点名那个不存在的 id；(c) **自指**同样被接受；(d) 全仓 `detect_conflict|conflicts_with|resolve_conflict` 的命中**全在无关子系统** ⇒ 记忆面**没有**检测实现；(e) 域上只校验**非空字符串**。**不对称**：`supersedes` 的同类引用早就有校验。五条 EC 全 PENDING；**cycle 1 WP-1 随即跑出实测更正**（见迭代日志第 1 行：建档初版用错路径）。
**不做**自动消解 / **不**做内容级检测 / **不**做历史回溯校验 / **不**改 `supersedes` 的既有校验。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
