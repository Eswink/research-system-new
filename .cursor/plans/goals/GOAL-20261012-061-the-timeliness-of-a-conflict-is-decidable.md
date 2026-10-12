---
id: GOAL-20261012-061
slug: the-timeliness-of-a-conflict-is-decidable
title: 冲突的时效性成为可判定 —— `contradictions` 可声明、可落库、可处置（五态）、可消解（序 19/22/26），但**一条很久以前声明的冲突是否仍算数**毫无面 —— **实测** `conflict_valid` / `contradiction_valid` / `conflict_review` **零命中**，`ConflictResolution` 只有（对端 / 消解者 / 时点）⇒ 冲突**一经声明永久算数**，与记忆自身的复核/过期机制（序 7 起的 `review_after` / `expires_at`）**不对称**
status: ACTIVE
created_at: 2026-10-12
updated_at: 2026-10-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-12 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 29**，由本次 replan 的**实测读数**驱动。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md、`.cursor/rules/` 20/21、`goals/README.md`
    的 GOAL 格式契约、本 frontmatter 的 forbidden / escalation_triggers）。**关键区分写死**：
    「权限下放」= **可以决定**，**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：`rg -n "conflict_valid|contradiction_valid|
    conflict_review" packages/ adapters/ services/` ⇒ **零命中**；`ConflictResolution` 的字段
    **逐个读出**只有 `other_id` / `resolved_by` / `resolved_at` ⇒ 没有任何「冲突声明本身
    是否仍算数」的面；而记忆自身的时效机制（`review_after` / `expires_at` + `validity_at`
    三态，序 7 起）**完整在树** ⇒ 两条时效链**不对称**。
    (2) **为什么属质量轴**：轴的反面是「只加计数或阈值」—— 本条让**冲突的可判定性**与记忆
    自身的时效**同一纪律**（该复核的说出来、该过期的别装新），不是加计数。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**冲突的时效**成为可读事实
    （按**调用方给的时点**判定，**不读挂钟**；三态互不混用且都**点名**）；缺省形态**逐字不变**；
    **不**自动消解（判定仍由**人**给 —— 序 26 立的边界**一字不动**）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / **D 组审批通道**（触达即 BLOCKED）/ `G24-5` 运行时拦截器 / 部署面验证 /
    `R26-2/3/4/6` / 把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不**做冲突的**自动消解**或**自动失效**（「谁对谁错」
    与「还算不算数」的判定**仍由人给**）；**不**做内容级语义比较。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿**：时效面零命中（`conflict_valid` / `contradiction_valid` / `conflict_review`）+
      `ConflictResolution` 字段逐个读出 + 记忆自身的时效机制逐条定位（可复用面）
      ⇒ 缺口 = **冲突声明的时效面**。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-conflict-timeliness.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: EC-02
    criterion: >-
      **实现面（本轮验收的主体）**：冲突的时效可判定（按调用方给的时点；三态互不混用且
      **点名**）；缺省形态**逐字不变**；坏时点**点名拒绝**；**不**自动消解 / **不**自动失效。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/application -q`
      ⇒ 全绿 + 新用例（缺省逐字不变 / 坏形态点名）。
    status: PASS
  - id: EC-03
    criterion: >-
      **读面 / 产品面接线**：两个读面（编排消费面 + HTTP 读面）**同源**披露冲突时效
      （既有键**逐字不变**）+ DTO 同轮（动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例。
    status: PASS
  - id: EC-04
    criterion: >-
      **两向反证（真按压，每条必须实测会响）**：`X-1` 过期冲突仍被判有效 ⇒ RED；
      `X-2` 未到期被判失效 ⇒ RED；`X-3` 未声明时效被当成已到期 ⇒ RED；
      `X-4` 缺省形态被改动 ⇒ RED。复原用**二进制读写**且 raw `sha256` 逐字节相同；
      **反证脚本带基线门**（未按压必须 GREEN，否则非 0 退出）；
      判词归档进树（`.cursor/plans/goals/evidence/`，`CR=0`）。
    verify: >-
      `scratch/goal061_press.py` 全 `RED` + `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）
      **与** `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` 的射程清单；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 29**）；⑤ EC 状态表与 frontmatter 同源；⑥ CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal061_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
budget:
  max_cycles: 6
  per_cycle_minutes: 90
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
  sync_set:
    - 既有判据**只**在「本轮的共用契约改动打到它」时才可同轮改签（逐条申报 + `git diff --numstat` 删除行读数）
    - 改既有判据一律**按关系**改（不按写法 / 位置），且**两向实测**（该红时红 / 不该红时不红）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 触达 D 组审批通道 / 真实外发 / 读面认证 / 多租户
  - 需要放开默认网络 / 需要真实凭据
child_plans:
  - .cursor/plans/tasks/PLAN-20261012-431-goal-061-ec01-05-the-timeliness-of-a-conflict-is-decidable.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-432-goal-061-ec01-04-the-timeliness-of-a-conflict-is-decidable.md
memory_entries: []
---

# GOAL-20261012-061 — 冲突的时效性成为可判定

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 29**（轴 = **质量**）。
> **本行是 replan 的产物**（`replan_every_goals: 3` 在序 24/25/26 收口后到期），
> 已在 MAINLINE「修订记录」留痕。承担者 = `GOAL-20261011-051` 登记的 `CC-3`（冲突时效性）。
> **建档时 status = ACTIVE；子 PLAN 在开 cycle 1 时派生。**

## 目标与退出标准

| EC | 标准（要点） | 验证命令 / 证据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿（时效面零命中 + 字段逐个读出 + 记忆自身时效面可复用） | **实跑**：`scratch/probe-conflict-timeliness.py` | **PASS** |
| EC-02 | 冲突时效可判定（三态互不混用且点名；缺省逐字不变；坏时点点名） | `pytest tests/domain tests/application -q` | **PASS** |
| EC-03 | 两读面**同源**披露 + 既有键逐字不变 + 快照同轮 | `pytest tests/api tests/adapters tests/contracts -q` | **PASS** |
| EC-04 | 两向反证 `X-1`…`X-4` 全红 + 基线门 + `sha256` 复原 | 归档 `.cursor/plans/goals/evidence/`（`CR=0`） | **PASS** |
| EC-05 | 自举收口（验证器 / 两树 / m0 23/23 / 治理 / 台账 / 残余在位） | 验证器 **64 判词 / 0 FAIL**；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5750 passed, 21 skipped**）| **PASS** |

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> **纪律**：起点事实**全部待复核** —— 下列读数由本 GOAL 的 EC-01 在**真实生产面**上重跑一次，
> 若与建档读数不符，以 EC-01 的实测为准并在迭代日志登记差异。

| # | 事实 | 复核命令 | 读数 |
| --- | --- | --- | --- |
| 1 | 冲突**时效面零命中** | `rg -n "conflict_valid\|contradiction_valid\|conflict_review" packages/ adapters/ services/` | **（零命中）** |
| 2 | `ConflictResolution` 字段**逐个读出**（无时效面） | `rg -n "class ConflictResolution" -A 12 packages/domain/memory.py` | 只有 `other_id` / `resolved_by` / `resolved_at` |
| 3 | 记忆自身的时效机制**在树**（可复用） | `rg -n "review_after\|expires_at" packages/domain/memory.py packages/application/memory/validity.py` | 两个字段 + `validity_at` 三态判定（序 7/10 起） |
| 4 | 五态处置**在树**（本轮**一字不动**） | `rg -n "^DISPOSITION_" packages/application/memory/disposition.py` | `USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED` |
| 5 | 消解记载**在树**（序 26，本轮**一字不动**） | `rg -n "class ConflictResolution\|def unresolved_conflicts" packages/domain/memory.py` | 两处都在 |

**结论**：**冲突的「有没有」可判定、「解决了没」可判定，但「还算不算数」毫无面** ——
一条三年前声明的冲突与今天声明的**同处置**（都 `CONFLICTED`）⇒ 与记忆自身的时效纪律
（`review_after` / `expires_at`，序 7 起）**不对称**。

## 决策登记（逐条状态）

| # | 决策 | 依据 | 状态 |
| --- | --- | --- | --- |
| D-1 | 时效判定与 `validity_at` **同一纪律**（时点由调用方给，**不读挂钟**） | 判定必须可复现（本战役一贯纪律） | 已定 |
| D-2 | 缺省形态**逐字不变**（未声明时效 ⇒ **不猜**，与 `validity_at` 的 `None` 同形） | 「缺省形态逐字不变」是本战役的一贯纪律 | 已定 |
| D-3 | 三态**互不混用**且都**点名** | 序 19/26 的既有形态（判词点得出是哪一种） | 已定 |
| D-4 | **不**自动消解 / **不**自动失效（判定仍由**人**给） | 序 26 立的边界**一字不动** | 已定 |
| D-5 | 冲突时效的**声明位**（谁给时点 / 声明在提案还是记录上）由 EC-01 读 `MemoryWriteProposal` 后定 | 涉及提案面契约 ⇒ 先量再定 | **待 EC-01** |

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
| (iii) 既有面连带 | 本轮的**共用契约**改动打到别的组合根 / 消费者（本 GOAL **高概率**：记忆域 + 两读面 + DTO）| 同轮修全部受影响面；逐条核对既有数据 |
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

- **本轮推进**：`CC-3`（冲突的**时效性** —— 一条很久以前声明的冲突是否仍算数）。
- **`R26-*` 终态（逐条保持，不改写）**：`R26-1`（读面认证）/ `R26-2` / `R26-3` / `R26-4` /
  `R26-5` / `R26-6` —— 六条**原样保留**（本轮**不**推进其中任何一条；`R26-2/3/4/6` 属
  「明确不做」清单，触达即 BLOCKED）。
- **本轮不推进（原样保留）**：`W-2` 的**内容级**检测；`CC-2`；`BB-3`；`Z-1` 的混合式；
  `Z-3` 的通知外发 / 升级链；`DD-1`…`DD-3`；`AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` /
  `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` / `O-1`…`O-5`。
- **未覆盖范围（逐条明写）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器。
- **明确否认**：投递语义**不是**「恰好一次」（口径只能是 at-least-once + idempotency +
  deduplication）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**（并写明 `covered_by`）；`cancelled` / `failure` 如实登记
> + 原因 + `covered_by`。**自我指涉边界**：台账提交自身不产生可引用的 CI 结论
> （明写并以「末条提交 + 覆盖说明」封闭，**不得循环引用**）。

| 提交 | CI run / 结论 | 覆盖的 WP |
| --- | --- | --- |
| （待开 cycle 1 后回填） | （待轮询） | — |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | —（replan + 建档） | `9715151`（归档检查）、`f0ce872`（derive） | 只读勘察（0 改动）+ 实测读数（见「事实层结论」） | （见 CI 台账） | — | 五条 EC 全 PENDING | cycle 1（EC-02 时效 + EC-03 披露） |
| 1 | `PLAN-20261012-431`（WP-1…WP-5） | `1a903fa`（时效三态 + 三适配器 + 两读面 + 迁移 026）、`dc50ef6`（判据 19 例 + 按压归档）、`d7dbb88`（收口面） | **EC-01/02/03/04 PASS**：① 四段读数；② 三态互不混用且**不猜**（未声明 ⇒ `None`）+ 两条坏形态点名；③ **两读面同源**（都引用同一纯函数）+ 三适配器同契约 + 快照同轮；④ **四向反证** `X-1`…`X-4` 全红 + 基线绿 + 复原一致 | （见 CI 台账） | 三处如实登记：① `X-4` 首版按压**不可观测**（域层让「无冲突却有声明」不可构造）⇒ 改打可观测面；② 断言集「不猜」判据首版**按文件末尾形态**判 ⇒ **改判关系**（AST）+ 四种写法逐条两向实测；③ HTTP 面的时点 `now` 可为 `None` ⇒ mypy 抓到 ⇒ 加守卫；④ PG `commit` 规模门触顶 ⇒ 抽 `_record_from_proposal`（语义一字未动）。**EC-05 PASS**（验证器 **64 判词 / 0 FAIL**；两树 **`TWO-TREE PASS`**；as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5750 passed, 21 skipped** / `EXIT=0`；独占、仓库 `.venv`、不接管道、**记录写完之后**）；治理 + 宪章判据绿） | （见 CI 台账） | 无 | 无（本 GOAL 已收口） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | **ACHIEVED** | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS，收口依据**全部实测**。① 收口验证器判词全 `PASS`；② 两树 `TWO-TREE PASS`（两路判词 / `sha256` 相同）；③ **as-is m0 23/23**（在**全部记录写入之后**）；④ 治理 + 宪章判据绿。**三处如实登记**（`X-4` 不可观测 / 「不猜」判据改判关系 / mypy 抓到 `now` 守卫）。**残余**：`STALE` 只点名（不自动消解/失效）/ 内容级检测 / 真实外发 / `BB-3` 等 + 未覆盖范围原样保留。独立复检：`RECHECK-20261012-432`（PASS_WITH_WARNINGS）。**不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-12 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 29**（**轴 = 质量**），并写修订记录行（只追加）。实测读数见「事实层结论」表（命令与读数同在）。五条 EC 全 PENDING。残余与未覆盖范围**原样保留**；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
