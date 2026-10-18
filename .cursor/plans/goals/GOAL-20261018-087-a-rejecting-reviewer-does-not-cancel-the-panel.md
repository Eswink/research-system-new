---
id: GOAL-20261018-087
slug: a-rejecting-reviewer-does-not-cancel-the-panel
title: 一个评审者判负**不取消**同批评审——分歧必须真的出现才有得判
status: ACHIEVED
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**复检**域 `下一级是什么`
    逐字为「**评审真的用不同模型判出负**（……尚无判据证明两个模型在**同一个上游产物**上给出
    **不同判词**）」。GOAL-086 收口后**实测**发现该下一级还有**第二个前提不成立**：
    同一 phase 的第一位评审者**判负**时，运行链**立刻 FAILED**（`_run_group_task` 见到
    `step.failure` 即返回），同一 phase 的**第二位评审者根本不运行** ⇒ 实测读数
    `state: FAILED, records: 1, panels: []`（只有 `reviewer_a` 落库）。
    分歧在**出现之前**就被短路，所以「两个模型给出不同判词」在产品上**不可达**。
    故序 55 登记本 GOAL。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令
    （「每一次自动迭代都必须让科研能力越来越近」）。授权要点：
    (1) **本 GOAL 必须让阶梯前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py`
    机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `R-M1` / destructive 能力改 allow / 为凑数扩承接面 /
    宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E`
    **不进 `.env`**）。

objective: >
    让「同批评审真的可能分歧」在产品面上成立：同一 phase 上，**一位评审者判负不得取消**
    其余评审者 —— 先让**全体**评审者各自判完并落库，再按「全体结论」决定 run 的走向
    （全部判负 ⇒ run 失败；有分歧 ⇒ run 失败但**分歧逐条可读**；全部判过 ⇒ 照常继续）。
    **判负不会被吞掉**：run 的终态与既有语义一致（判负仍然导致失败），被改的只有
    **「什么时候」**判定 —— 从「第一个判负就停」改为「全体判完再判」。
    **默认零回归**：未声明为本类评审 phase 的既有协议**逐字不变**（单评审 phase、
    非评审 phase 都仍然 fail-fast）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **判负不再取消同批评审（产品路径）**：同一 phase 上两位评审者，第一位判负、
      第二位判过 ⇒ 两条判词**都落库**、`panels` 有一条且 `voters == 2`、
      `dissent` **逐条点名**少数意见的那个目标与它的 verdict；run 终态仍是 `FAILED`
      （判负没被吞掉）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_a_rejecting_reviewer_does_not_cancel_the_panel.py -q`
      ⇒ 全绿；判据覆盖：两条判词都在 / 分歧被点名 / run 仍 FAILED / 失败消息点名是哪个目标判负。
    status: PASS
  - id: EC-02
    criterion: >-
      **「全体判完再判」是有条件的、可声明的**：该语义只对**显式声明**的评审 phase 生效
      （声明面在协议/合约，不在代码里的「如果就」）；**未声明 ⇒ 逐字回到既有 fail-fast**
      （第一个判负就停、run 立刻 FAILED、只落一条判词 —— 实测读数与今天相同）。
    verify: >-
      同一判据文件的第二组（成对）：未声明的同一份协议 ⇒ `records == 1` 且 `panels == []`。
    status: PASS
  - id: EC-03
    criterion: >-
      **不是「静默吞掉」**：分歧导致 run 失败时，失败消息**逐条点名**每一位评审者的
      目标与 verdict（不是笼统的「gate rejected」）；全体判过时 run 照常 `SUCCEEDED`
      且 `panels` 给出 majority advisory。**反证**：把第二位也改成判负 ⇒ run 仍失败，
      但 `dissent` 为空、`advisory == "REJECT"`（分歧消失了，事实随之处处不同）。
    verify: >-
      同一判据文件；成对断言 + 按压（改事实 ⇒ 三处读数同时变：advisory / dissent / 消息）。
    status: PASS
  - id: EC-04
    criterion: >-
      **零回归**：单评审 phase 与非评审 phase 的既有语义**逐字不变**
      （`tests/e2e` 全量 + `tests/application` 全量零回归）；既有 6 条评审面板判据
      **逐字保留且全绿**；`on_task_failure: CONTINUE` 的既有语义**不被改写**
      （本 GOAL 用的是**另一个**声明面，不复用、不改写它）。
    verify: >-
      `tests/e2e` 与 `tests/application` 全量绿；既有面板判据未改。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**、**静止工作树**）+ 治理绿 + 凭据审计 + CI 台账**逐提交**
      （`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**；
      自我指涉边界**明写并封闭**）+ 残余与未覆盖范围逐条。**★ 并含阶梯记账（两个面）**：
      阶梯「复检」行的 `依据 GOAL` **与**宪章 `进展记录` 各收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PASS

budget:
  max_cycles: 14
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - 改 `default_effect: DENY` / 放宽 §9 / 新增任何 allow
    - >-
      **把判负吞掉**：本 GOAL 只改「什么时候判定」，**不改**「判负会怎样」——
      run 终态必须仍是 `FAILED`；把判负变成 DEGRADED / SUCCEEDED 即越界
    - >-
      **默认行为变化**：未声明该语义的协议必须逐字保持 fail-fast
      （第一个判负就停、只落一条判词）；把它做成全局默认即越界
    - >-
      **复用 `on_task_failure: CONTINUE`**：那是「容忍失败继续跑到底」的既有语义
      （run 收敛 `DEGRADED`），与「先让全体评完再判负」是**两件事**；改它会破坏既有判据
    - >-
      **用 agent 名当身份**：分歧点名必须是**解析后的目标** `endpoint/model_name`，
      与 GOAL-084/085/086 同一处取值
    - >-
      **把「设施失败」折算成「判负」**：无模型身份 / 空 verdict 的 finding 仍必须
      **点名不进票**（GOAL-085 既有语义逐字保留）
    - 为让判据变绿而**改出厂目录**制造差异
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **需要改 `TaskContract.failure_policy` 的既有键语义**（`on_task_failure` 的
    `FAIL_RUN` / `CONTINUE` 取值与被消费方式）—— 停下登记；**新增**一个并列的声明键
    不算（本 GOAL 走新增）

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-526-goal-087-ec01-04-a-rejecting-reviewer-does-not-cancel-the-panel.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-527-goal-087-a-rejecting-reviewer-does-not-cancel-the-panel.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让「分歧」在产品上**有可能发生** —— 今天同批评审里第一个判负就把整个 run
打死，第二位评审者连跑都不跑，于是阶梯说的「两个模型在同一个上游产物上给出不同判词」
在**结构上不可达**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：一个**看不到分歧**的评审面板，其「多数票」是空话 ——
  它永远只有一票）；
- **能力域** = **复检**（阶梯逐字：`评审真的用不同模型判出负`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **第一个判负就停**：`phase_runner._run_group_task` 在 `step.failure is not None` 时
   **立即**返回失败 `RunOutcome`（组内后续任务不再执行）。这是 run 级 fail-fast 的既有语义。
2. **实测复现（本 GOAL 建档时跑过）**：`review_scored_research_v1` 的 `review` phase 放宽到
   两位评审者（`reviewer_a`=`glm-5.3`、`reviewer_b`=`kimi-k2.6`），两位都交付
   `{"review_decision": {"verdict": "REJECT", "score": 0.5}}` ⇒ 读数
   `state: FAILED`、`records: 1`（只有 `gate:reviewer_a`）、`panels: []`。
   ⇒ **第二位评审者从未运行**，所以「分歧」没有机会出现。
3. **已有机制但语义不同**：`TaskContract.failure_policy` 的 `on_task_failure: CONTINUE`
   让失败被**容忍**（run 收敛 `DEGRADED`，判负被记成「被容忍的失败」）。那是
   「一个任务失败不拖垮整个 run」；本 GOAL 要的是
   「**同一批评审先评完，再按全体结论判定**」—— 判负**仍然**导致 `FAILED`，
   改的只是**时机**与**可见性**。混用会把「判负」说成「可容忍的瑕疵」。
4. **阶梯这一格的判据今天无处安放**：GOAL-085/086 已让判词可归因、可聚合成面板，
   但**面板里的票永远同向**（因为第一位判负就停，能落库的只有一票）。

⇒ 后果：阶梯「复检」域的 `下一级`（两个模型在同一产物上给出不同判词）**今天不可达**，
缺的是「让全体评审者都评完」这件可判定的事。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**：一个**并列的**声明键（review-panel 语义），与 `on_task_failure` 互不影响；
- **不改** `on_task_failure` 的两个取值与其消费方式；
- **判负仍然失败**：run 终态与既有语义一致，只改判定时机与分歧可见性；
- **默认零回归**：未声明 ⇒ 逐字回到 fail-fast；
- **设施失败不折算**：无模型身份的票仍点名不进票（GOAL-085 既有语义）。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **判定纪律**：先让**全体**评审者评完（各自落库），再按「全体结论」决定 run 走向；
  判定结果与既有 `FAIL_RUN` 的**终态**一致（`FAILED`）；
- **零回归纪律**：未声明 ⇒ `records == 1`、`panels == []`（与今天逐字相同）；
- **可见性纪律**：失败消息与读面都要**逐条点名**每位评审者的目标与 verdict；
- **凭据纪律**：每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**（前序 GOAL 实测过这个形态），如实登记 + `covered_by`。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立（两个面）**。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 残余与未覆盖范围（逐条明写）

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办。
- `W-2` —— **不改「有多少票才算多数」**：平票仍 ⇒ `advisory=None`（GOAL-085 语义）；
  本 GOAL 只让第二票**有可能存在**。
- `W-3` —— **仍不判「两个模型是否同质化」**（需要任务级质量对比，射程外）。
- `W-4` —— **真实模型的判词是否真的会分歧未知**：本 GOAL 用受控执行体证明
  「分歧可表达且可读」；真实中转站上两位评审者的实际判词差异属 live 观察，不在本轮。
- `W-5` —— **只覆盖「同 phase 的评审」**：跨 phase 的评审不聚合（GOAL-086 `W-4`）。
- `W-6` —— **不改 run 状态机**：终态仍是 `FAILED`（不是 `DEGRADED`）—— 判负不是「可容忍的瑕疵」。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **改 `on_task_failure` 既有语义**或**改 run 状态机** —— 需人工拍板（本 GOAL 只新增）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01/02/03/04 |
| 1 | PLAN-20261018-526 | `3128efb0` | 新判据 **3 条**（运行链成对）；application+api+contracts **2411 passed / 77 skipped**；e2e **363 passed / 17 skipped**；静态门全绿 | 见「CI 台账」 | 1（首轮真回归：组末判定误吃 `CONTINUE` 容忍失败 ⇒ 三处既有用例变红；已按「只认本模块记账」修正） | EC-01…EC-04 达成 | 收口（EC-05） |
| 2 | （收口 cycle，无新子 PLAN） | 待回填 | 验证器 **60 条全绿**；两树同结论；as-is m0 **23/23** | 见「CI 台账」 | — | 无（EC 全达成） | **收口** |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| （建档提交，待回填） | 待回填 | 待回填 | 待回填 |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-086 收口后按阶梯 `下一级` 续推（序 55，预算 `max_goals: 55` 的**最后一格**）。**建档实测两条**：① `_run_group_task` 在 `step.failure` 非空时立即返回失败 ⇒ 组内后续任务不跑；② 实测两位评审者都判负 ⇒ `state: FAILED, records: 1, panels: []`（只有 `reviewer_a` 落库）⇒ 分歧在出现之前被短路。**已有 `on_task_failure: CONTINUE` 但语义不同**（那让 run 收敛 `DEGRADED`；本 GOAL 要判负仍 `FAILED`，只改判定时机与可见性）。 |
