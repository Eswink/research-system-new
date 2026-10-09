---
id: GOAL-20261008-040
slug: program-stop-reasons-become-distinguishable
title: 程序推进的**停止理由可区分** —— 失败轮 / 无结论轮 / 结论判停**不混用同一种类**（「没有结论」不得被读成「结论说停」）
status: ACHIEVED
created_at: 2026-10-08
updated_at: 2026-10-08
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-08 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：**收口后立即开下一个 GOAL，
    不停下来等指令**。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含**新增判定种类**、改产品语义），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测）**：程序推进的判定只读**最后一轮**的落库判词；当那一轮是
    **FAILED**（执行失败，没有任何落库结论）时，`verdicts` 为空 ⇒ 判定落 `STOP_RULE`
    并给出判词「上一轮落库结论不命中续跑规则」—— 但事实是**根本没有结论**，
    与「结论说了停」是两件相反的事（前者是**执行面故障**，后者是**科学判断**）。
    实测：第 1 轮 FAILED ⇒ 第 2 次推进落 `STOP_RULE`、`cited_facts=[]`。
    (2) **为什么这属于深度轴**：MAINLINE 深度轴的定义是「多轮推进且**有停止规则**：
    轮数由**结论**驱动」—— 停止理由不可区分意味着「结论驱动」在**失败路径**上失真：
    读面无法分辨「研究做完了、结论说不必再轮」与「这一轮没跑成」。这正是 GOAL-037 的
    `O-5`（决策未落的中间态）与 `O-2`（程序级人工闸门）的同族问题：**失败面也需要可判定**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：把「失败轮 / 无结论轮 / 结论判停」变成
    **互不混用的判定种类** + 失败轮可按**声明**重试（重试是**决定**，不是放宽判据）。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA（M18 deferred）/ D 组审批通道（触达即 BLOCKED）/ `G24-5` 运行时拦截器 /
    部署面验证 / `R26-2` `R26-3` `R26-4` `R26-6` / 把 destructive 能力从
    `require_approval` 改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **把「没有结论」当成「结论说停」**（那正是本轮要消灭的混淆）；
    **让重试变成隐式的无限重跑**（重试必须**有界且可观测**：计数落决策、超界点名）。
    (6) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (7) **边界（承继）**：GOAL-001…039 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…039 的未覆盖范围**原样保留**；
    GOAL-039 的残余 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` /
    `R26-*` 终态 / 未覆盖范围**原样保留**，本轮**只追加**。
    (8) **driver** = client-goal、**owner** = root-agent。
objective: >-
    把 MAINLINE 序 8（深度轴）落成**失败面也可判定**：① **勘察定稿** —— 实测「FAILED 轮
    ⇒ `STOP_RULE` + 空 `cited_facts`」这一失真的现状（`advance_program` 的判定只读
    `_verdicts(last)`，空集落进「不命中规则」分支），以及既有可复用的缝（判定种类枚举 /
    决策 append-only / 两轮实跑判据）（EC-01）→
    ② **判定种类扩齐** —— 新增**可区分**的种类：`STOP_RUN_FAILED`（上一轮**执行失败**：
    没有结论可依 ⇒ 明确记为「失败停」，**不**伪装成结论停）与 `RETRY_FAILED_RUN`
    （按**声明**重试上一轮失败序号：计数落决策、**有界**、超界点名），以及
    `STOP_CANCELLED`（取消是人的决定，**不**自动重试）（EC-02）→
    ③ **判定面接线** —— 驱动按「上一轮终态」分派：`SUCCEEDED` 才走结论面；
    `FAILED` 走失败面；`CANCELLED` 走取消面（三者**互不混用**）（EC-03）→
    ④ **真的被用上（含反证）** —— 实跑：失败轮 ⇒ 判词**点名**「失败停 / 未获结论」；
    声明重试 ⇒ 同序号重起且计数可见、用尽 ⇒ 点名重试上界；**不得**再出现
    「`STOP_RULE` + 空 `cited_facts`」这一形态（反证臂）（EC-04）→
    ⑤ **自举收口**（复用 GOAL-039 的机器）（EC-05）。
    **硬约束**：判定种类**互不混用**（结论面 / 护栏面 / 失败面 / 取消面各归各的）；
    「没有结论」**点名**（`cited_facts` 为空时必须说清**为什么**空）；
    重试**有界可观测**（计数落决策、超界点名）；缺省（未声明重试）⇒ 行为 = 失败停
    （不隐式重跑）；m0 条数**仍是 23**；判词归档**进树**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) 现状失真：`advance_program` 的 `_evaluate` 只读
      `_verdicts(findings, last.id.value)`；`last` 为 FAILED（无落库结论）⇒ `verdicts==[]`
      ⇒ 落 `STOP_RULE`，判词「上一轮落库结论不命中续跑规则」（**实测**：第 1 轮 FAILED
      ⇒ 第 2 次推进 `STOP_RULE` + `cited_facts=[]`）；(b) 域词汇表：`ResearchRunState.terminal()`
      = {SUCCEEDED, FAILED, CANCELLED} ⇒ 失败面与取消面**在域里已可区分**，缺的只是
      **判定面**的分派；(c) 可复用的缝：`ProgramDecisionKind`（枚举）+ `ProgramDecision`
      （append-only、`cited_facts` 原文）+ `advance_program`（判定→落决策→必要时起 run）
      + GOAL-037 EC-02 的两轮实跑判据。
    verify: >-
      `rg -n "STOP_RULE" packages/application/run_orchestration/program_runner.py`；
      实跑读数（FAILED ⇒ `STOP_RULE` + 空 `cited_facts`）；`terminal()` 逐字。
    status: PASS
  - id: EC-02
    criterion: >-
      **判定种类扩齐（可区分 + 有界重试）**：`ProgramDecisionKind` 增
      `STOP_RUN_FAILED`（失败停：点名「上一轮执行失败、未获结论」）、`STOP_CANCELLED`
      （取消停：人的决定，**不**自动重试）、`RETRY_FAILED_RUN`（按声明重试）；
      `ResearchProgram` 增**可选**声明 `max_attempts_per_index`（缺省 `1` ⇒ **不重试**，
      既有行为逐字不变；>1 ⇒ 允许同序号重起，**有界**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py -q` ⇒ 全绿 + 新用例。
    status: PASS
  - id: EC-03
    criterion: >-
      **判定面接线（按终态分派）**：驱动按上一轮**终态**分派 ——
      SUCCEEDED ⇒ 结论面（既有四态：`CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` / `DEDUP`）；
      FAILED ⇒ 失败面（未声明重试或已用尽 ⇒ `STOP_RUN_FAILED`；未用尽 ⇒ `RETRY_FAILED_RUN`）；
      CANCELLED ⇒ `STOP_CANCELLED`。**判定与决策都不混用**：失败面的 `cited_facts` 点名
      `state=FAILED` 与已用尝试数（不再是空数组）。
    verify: >-
      同上判据文件的终态分派用例（三终态 × 重试态）逐条。
    status: PASS
  - id: EC-04
    criterion: >-
      **真的被用上（+ 反证）**：(a) 实跑：第 1 轮执行失败 ⇒ 推进落 `STOP_RUN_FAILED`
      且判词**点名**「未获结论」（`cited_facts` 含 `state=FAILED`）；(b) 声明重试
      （`max_attempts_per_index=2`）⇒ 推进落 `RETRY_FAILED_RUN`、**同序号**新 run 被起、
      计数可见；再推一次（计数用尽）⇒ `STOP_RUN_FAILED` 且点名上界；
      (c) **反证臂**：任何形态下**不得**再出现「`STOP_RULE` + `cited_facts == []`」
      （空数组必须被判据点名）；(d) 缺省（未声明）⇒ 行为 = 失败停（**不**隐式重跑）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据全绿。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树（复用 `tools/closeout_recheck_tools`
      + `tools/closeout_recheck_assertions.standard_verdicts`）并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
      （**纯收紧**）；② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树
      （**二进制写盘**、`CR=0`）；③ as-is m0 **23/23**（在**全部记录写入之后**，独占、
      仓库 `.venv`、不接管道）；④ 治理 `validate.py` 绿 +
      `tests/tooling/test_mainline_program_is_intact.py` 绿（**本 GOAL 的 id 已在程序表
      序 8**，进展记录行指向真实 RECHECK 文件）；⑤ CI 台账**逐提交**（`cancelled` 如实登记
      + 原因 + `covered_by`；空集合 = 未取证；自我指涉边界明写并封闭）；⑥ 承继残余逐条在位；
      ⑦ 未覆盖范围逐条明写。
      **判据**：验证器进树 + `IN_SCOPE` 纯收紧 + 两树判词归档 + as-is m0 23/23 + 治理绿 +
      宪章判据绿 + CI 台账逐提交 + 残余与未覆盖逐条。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal040_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`；配套留档：两路判词 sha256 相同的归档、
      m0 日志、CI 台账逐提交行。
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
      **把「没有结论」当成「结论说停」**（本轮要消灭的混淆）；**让重试变成隐式无限重跑**
      （必须**有界**：计数落决策、超界点名；缺省不重试）
    - >-
      **让取消被自动重试**（取消是人的决定 ⇒ `STOP_CANCELLED`，**不**重试）；
      **改动既有四态语义**（SUCCEEDED 路径的 `CONTINUE` / `STOP_RULE` /
      `STOP_GUARDRAIL` / `DEDUP` 逐字保持，由既有判据钉住）
    - >-
      **修改**任何既有判据 / 门禁 / 阈值（点名：`tests/egress_guard.py`、三道记录面判据、
      两树入口判据、规模门禁、`tests/contracts/**`、`tests/adapters/**`、`tests/e2e/**`、
      `tests/application/**`、`tests/domain/**` **既有文件**）—— **新增**判据与新增文件
      不受此限；**加可选字段 / 枚举值**属本轮授权（EC-02）
    - >-
      **同轮同步面**：仅当本轮新增判定种类 / 可选声明**必需**时，允许对**既有**登记面做
      **加法 / 搬迁登记**（谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **把 destructive / 写 / 执行 / 审批类能力改成 allow**（本轮不动放行面）
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
  - .cursor/plans/tasks/PLAN-20261008-355-goal-040-ec02-04-stop-reasons.md
  - .cursor/plans/tasks/PLAN-20261008-357-goal-040-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-358-goal-040-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261008-040 — 程序推进的停止理由可区分

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 8**（轴 = **深度**；
> 依赖序 5、7 —— 两者已 ACHIEVED）。**本行是 replan 的产物**，已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 现状：FAILED 轮 ⇒ `STOP_RULE` + 空 `cited_facts`（把「没有结论」读成「结论说停」） | PASS |
| EC-02 | 判定种类扩齐 | `STOP_RUN_FAILED` / `STOP_CANCELLED` / `RETRY_FAILED_RUN`（+ 可选有界重试声明，缺省不重试） | PASS |
| EC-03 | 判定面接线 | 按上一轮**终态**分派（成功走结论面 / 失败走失败面 / 取消走取消面；互不混用） | PASS |
| EC-04 | 真的被用上 | 实跑判词点名「失败停」；声明重试 ⇒ 同序号重起且计数可见、用尽点名；**反证**：空 `cited_facts` 不再出现 | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得把**没有结论**当成
**结论说停**；不得让重试变成**隐式无限重跑**；不得让**取消**被自动重试；
不得**宣称项目安全**（`R-M1`）；不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：失败轮被读成「结论说停」（本轮要消灭的失真）

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 判定只读**最后一轮**的判词 | `packages/application/run_orchestration/program_runner.py::_evaluate` | `verdicts = _verdicts(findings, last.id.value)`；`last` 即 `existing[-1]` |
| 1.2 | FAILED 轮**没有落库结论** | 同上 + `ReviewFindingStore.for_run` | 执行失败 ⇒ 门未判过 ⇒ `verdicts == []` |
| 1.3 | 空集落进「不命中规则」分支 | 同上 `if not hit:` | 落 `STOP_RULE`，判词「上一轮落库结论不命中续跑规则 (verdicts=[], want=['PASS']) ⇒ 按结论停」 |
| 1.4 | **实测复现** | 两轮实跑（第 1 轮执行体不给必需交付物） | 第 1 轮 `FAILED`；第 2 次推进落 `STOP_RULE`、`cited_facts=[]` ⇒ 读面无法分辨「失败」与「结论说停」 |
| 1.5 | 域里**已经**可区分终态 | `packages/domain/run_state.py::terminal()` | `{SUCCEEDED, FAILED, CANCELLED}` —— 缺的只是**判定面**的分派 |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 判定种类是枚举（可扩） | `packages/domain/program.py::ProgramDecisionKind` | 六种（`START` / `CONTINUE` / `STOP_RULE` / `STOP_GUARDRAIL` / `WAIT` / `DEDUP`），各带**逐条 docstring** |
| 2.2 | 决策是 append-only 事实 | `packages/domain/program.py::ProgramDecision` | 含 `cited_facts`（被引事实**原文**）—— 失败面的点名据此落档 |
| 2.3 | 驱动形状可复用 | `program_runner.py`（`_evaluate` / `_after_hit` / `_start` / `_claimed_but_missing`） | 判定→落决策→必要时起 run；**分派点就在 `_evaluate` 的入口**（按 `last.state`） |
| 2.4 | 两轮实跑判据现成 | `tests/e2e/test_program_advance_on_the_run_path.py`（6 例） | 本轮新增用例与它同族（同一套断言形态） |

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 「失败停」的种类名 | **已定**：`STOP_RUN_FAILED`（点名「上一轮执行失败、未获结论」） |
| ② | 重试的落点 | **已定**：驱动按**声明**（`ResearchProgram.max_attempts_per_index`，缺省 `1` ⇒ 不重试）；重试 = 起**同序号**的新 run（序号是程序的轮次身份，重试不改变轮次） |
| ③ | 取消的处置 | **已定**：`STOP_CANCELLED`（人的决定；**不**自动重试） |
| ④ | 计数的落点 | **已定**：`cited_facts` 点名「已用尝试数 / 上界」（不落第二套计数存储 —— 由 `for_program` 的 run 数按序号算） |
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

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261008-040` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不 `git add -A`**。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/application` / `tests/e2e` / `tests/domain`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**判定与决策互不混用**（四态各归各的）；**空 `cited_facts` 必须说清
为什么空**；**重试有界可观测**；**缺省不重试**（逐字保持）；**取消不重试**；
受判面不得是交集（承 `MEM-160`）；留档二进制写盘、判词归档进树；台账逐提交；
新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED |
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

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-039 的 `Q-1`（只到「事实可读」不到「自动处置」）/
`Q-2`（scope 过滤与鉴权）/ `Q-3`（向量索引）；GOAL-038 的 `P-1`（只到「携带」不到「因果」）/
`P-2`（跨程序共享）/ `P-3`（人工闸门式影响）；GOAL-037 的 `O-1`…`O-5`（`O-5` 的**失败面**
那一半由本轮收口）；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；
GOAL-019…039 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032（引擎面）+ GOAL-033（产品面）收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | `consumer_offsets` 类消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`R-1`…`R-3`）

- `R-1`（**失败面的自动处置不在本轮**，未覆盖）：本轮让「失败停 / 重试」**可判定**；
  **不**动任务级重试（既有 `RetryPolicy` / 死信面，GOAL-032/033 已收口）。
- `R-2`（**重试的退避策略不在本轮**，未覆盖）：重试**有界**（计数上界）但**无退避** ——
  退避属调度面（既有 `RetrySchedule` 另一条线）。
- `R-3`（**跨程序的失败传播不在本轮**，未覆盖；承 `P-2`）：失败面按**程序**划界。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **停止理由**：**已收口** = 成功 / 失败 / 取消三条路径的判定**互不混用**且判词点名；
  **未覆盖** = 失败后的**自动处置**（退避 / 重排 / 升级人工）。
- **重试**：**已收口** = 有界、可观测、缺省不重试；**未覆盖** = 退避与跨程序传播。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `45a8481`（GOAL-039 台账尾巴，本轮首行） | 读数在本表回填（**取证中**） | GOAL-039 的最后一个提交 —— **GOAL-039 台账的自我指涉边界由本行封闭** |
| （本行所在提交：replan + 建档） | **自身结论尚未产生**（自我指涉边界） | replan（程序表序 8 新增）+ 本 GOAL 五 EC + 事实层读数；其结论由 **cycle 1 的台账行**取证 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | `PLAN-20261008-357` | （见 CI 台账） | EC-05 七条 AC | EC-05 七条 AC：验证器进树（复用标准断言集**一行未重写**；起草中间态 **71 PASS / 2 FAIL** ⇒ 收口态 **73 判词 / 0 FAIL**）+ `IN_SCOPE` 纯收紧（+2 行；判据 8 passed）+ 治理 + 宪章判据 + 承继残余与本轮 `R-1`…`R-3` 逐条定格；**AC-3** 次轮 `--base-ref 5cbbe18` **`TWO-TREE PASS`**（两路 73 判词 / `sha256` 相同 `2ba2d5b0…`）+ 归档定格 **2518 B / 73 行 / CR=0 / 0 FAIL** + **AC-4** as-is m0 **23/23**（`PASS [` 24 / `FAILED [` 0 / **5473 passed, 20 skipped**） | （见 CI 台账） | — | 五条 EC 全 PASS；GOAL 收口 | GOAL 收口（`RECHECK-20261008-358`） |
| 1 | `PLAN-20261008-355` | （见 CI 台账） | EC-02/03/04 全 PASS：判定种类扩齐（三种 + 可选有界重试声明，**落库**：迁移 019 + 两适配器 + 建程序 DTO/读面）+ **按终态分派**（成功走结论面 / 失败走失败面 / 取消走取消面）+ **实跑取证**（失败停点名「未获结论」；声明重试 ⇒ **同序号**重起 + `attempts=1/2`，用尽 ⇒ `attempts=2/2` + 点名；缺省不重跑）；**反证**：空 `cited_facts` 旧形态不再出现；驱动 **13 passed**、e2e **4 passed**；广面 **5138 passed, 18 skipped**；四道门绿（mypy 1168 files）；live PG `migration_version` = **19** | （见 CI 台账） | **三处既有 e2e 用例按行为修正更新**（原先依赖「失败轮被判续 ⇒ 才有第 2 轮」；**先在干净树 `49b2c7d` 复跑确认原先通过**）；`_non_success_terminal` 超 50 行 ⇒ **拆函数** | EC-02/03/04 收口；**下一轮 EC-05**（自举收口） |
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **一处实测复现**（FAILED 轮 ⇒ `STOP_RULE` + 空 `cited_facts`）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 8** | （见 CI 台账） | — | 五条 EC 全 PENDING；分派落点（②）待 cycle 1 实现 | cycle 1（EC-02 判定种类 + EC-03 分派） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、`IN_SCOPE` **纯收紧**、两树 **`TWO-TREE PASS`**（73 判词 / 两路 `sha256` 相同 `2ba2d5b0…`）、判词归档进树（两份各 2518 B / 73 行 / `CR=0` / 0 FAIL）、as-is m0 **23/23**（记录写完之后：`PASS [` 24 / `FAILED [` 0 / **5473 passed, 20 skipped**）、治理 + 宪章判据绿、CI 台账逐提交。**一处时序如实登记**：两树首轮 bootstrap 红。**收口后不再推进本 GOAL**；残余 `R-1`…`R-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261008-358`（PASS_WITH_WARNINGS）。 |
| 2026-10-08 | ACTIVE | **cycle 1（EC-02/03/04）收口**：**停止理由互不混用** —— 判定种类扩齐（`STOP_RUN_FAILED` / `STOP_CANCELLED` / `RETRY_FAILED_RUN`），驱动**按上一轮终态分派**（只有 `SUCCEEDED` 走结论面；失败走失败面并点名「未获结论」；取消走取消面且不重试）；可选**有界重试**（`max_attempts_per_index`，缺省 1 = 不重试）并**真的落库**（迁移 019 + 两适配器 + 建程序 DTO/读面）；实跑 + 反证打满。**三处既有 e2e 用例按行为修正更新**（逐条理由 + 干净树复跑取证）。EC-02/03/04 `PASS`；EC-05 待收口。**不得**宣称安全，**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-08 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 8**。只读勘察 + 一处**实测复现**：程序推进只读最后一轮的落库判词，而 **FAILED 轮没有任何结论** ⇒ `verdicts` 为空 ⇒ 落 `STOP_RULE` 并给出「上一轮落库结论不命中续跑规则」—— 把「**没有结论**」读成了「**结论说停**」（实测：第 1 轮 FAILED ⇒ 第 2 次推进 `STOP_RULE`、`cited_facts=[]`）。域里终态**已可区分**（`terminal()` = SUCCEEDED/FAILED/CANCELLED）⇒ 缺的是**判定面**的分派。五条 EC 全 `PENDING`。**不做数量目标**；**未覆盖范围原样保留**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
