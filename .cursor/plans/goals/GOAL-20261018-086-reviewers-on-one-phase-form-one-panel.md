---
id: GOAL-20261018-086
slug: reviewers-on-one-phase-form-one-panel
title: 同一批评审者**真的判同一件东西**——评审小组按「被评对象」而非「任务」聚合
status: ACHIEVED
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**复检**域 `下一级是什么`
    逐字为「**评审真的用不同模型判出负**（现判「配置上不相交」+「判词可归因、可聚合」；
    尚无判据证明两个模型在**同一个上游产物**上给出**不同判词**）」。GOAL-085 收口实测发现
    该下一级的**前置条件在产品面上不成立**：`review_read` 的 `panels` 按 `task_id` 分组，
    而 `resolve_sessions` 对**每个评审 agent 各生成一个独立 `ResearchTask`**
    （`session_resolution.py:192-197`，幂等键 `{run}:{phase}:{agent}`），判词 id 又是
    `finding:{task_id}:gate` ⇒ **同一任务上永远只有一条判词** ⇒ 多评审阶段
    （`ai_ml_research_v0_4_0.yaml` 的 `peer_review`，`scientific_reviewer` `min_instances: 2`）
    的 `panels` **恒为空**。实测复现：两条判词分别挂 `task:reviewer_a` / `task:reviewer_b`
    ⇒ `count: 2, panels: 0`。故序 54 登记本 GOAL。承用户 2026-10-06 全部权限下放 +
    2026-10-14 方向指令（「每一次自动迭代都必须让科研能力越来越近」）。授权要点：
    (1) **本 GOAL 必须让阶梯前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py`
    机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `R-M1` / destructive 能力改 allow / 为凑数扩承接面 /
    宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E`
    **不进 `.env`**）。

objective: >
    让「同一批评审者评同一件东西」在产品面上成为**可判定且恒成立**的事实：
    同一个 phase 里被派发的多个评审 agent，它们的判词必须被聚合成**一个**评审小组
    （而不是因为「各拿一个任务」而永远聚不起来）；聚合必须按**被评对象**
    （phase × 合约）分组，且该分组键要**逐条可读**（落库带 phase 身份）；
    **单评审协议逐字不变**；**同模型多实例仍判不独立**（与 GOAL-085 同源）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **同一 phase 的多位评审者被聚成一个小组（产品路径）**：多评审 phase 上，
      评审者的判词按**被评对象**（phase × 合约）聚合，`review_read` 的 `panels`
      **非空**且 `voters` = 该 phase 上可归因的评审者数。
      **反证**：把两位评审者放到不同 phase ⇒ 不聚合（各一票，`panels` 各为 `None`）。
      **判据必须在运行链上成立**，不是只在手写 `ScopedReviewFinding` 上成立。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_reviewers_on_one_phase_form_a_panel.py -q`
      ⇒ 全绿；判据覆盖：同 phase 两评审 ⇒ `panels` 一条且 `voters == 2` /
      不同 phase ⇒ 不聚合 / 读面逐票点名两位评审者的**模型目标**。
    status: PASS
  - id: EC-02
    criterion: >-
      **分组键可读**：落库的评审结论带**phase 身份**（`phase_id`），读面逐条露出它；
      每个小组**明写自己用的是哪个键**（`scope` ∈ `PHASE` / `TASK`）—— 用了 phase 的
      小组覆盖**同一 phase 的全部评审者**，用了 task 的只覆盖单个任务。
      **不静默混两种键**：一条记录有 `phase_id` 就按 phase 分组，没有就按 task 分组
      （= 迁移前的既有语义），读面据 `scope` 让调用方**看得出**这次聚合的射程。
    verify: >-
      同一判据文件的第二组；外加 `tests/contracts/test_review_finding_store_contracts.py`
      的往返判据（`phase_id` 存进去、读出来逐字相同；缺省 `None` 往返）。
    status: PASS
  - id: EC-03
    criterion: >-
      **同模型两个实例仍判不独立**：同一 phase 上两位评审者落在**同一个**执行目标
      `(endpoint, model_name)` ⇒ 聚合结论 `independent=False` 并**点名**那个重复目标；
      落到**不同**目标 ⇒ `independent=True`。**按压**把第二位指回第一位的目标 ⇒ 翻转。
    verify: >-
      同一判据文件；成对断言 + 按压（改事实 ⇒ 结论翻转），不只看正向。
    status: PASS
  - id: EC-04
    criterion: >-
      **单评审零回归**：只有一位评审者的 phase 上 `panels == []` 且既有字段逐字不变；
      `phase_id` 为 `None` 的既有记录其读面形态**只多出**这个可空键。
    verify: >-
      `tests/e2e/test_review_panel_on_the_run_path.py` 既有 6 条判据**逐字保留且全绿**；
      新增的反证用例证明「缺 phase 身份不参与聚合」。
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
      **把「聚合不起来」写成「没有小组」**：多评审 phase 上 `panels == []` 必须是
      **被点名的缺陷**，不得被读成「本 run 只有一票」的正常事实
    - >-
      **用 agent 名当分组键**：分组键必须是**被评对象**（phase × 合约）或解析后的执行目标；
      写 `agent:<id>` / profile 名一律**不算**
    - >-
      **让聚合结论夺取真相权**：`Decision` 仍由验收门给出；把 advisory 聚合写成
      `Decision` 或改它的判词即越界
    - >-
      **把「设施失败」折算成「判负」**：无模型身份 / 空 verdict 的 finding 必须
      **点名不进票**，不得映射成 PASS/FAIL
    - 为让判据变绿而**改出厂目录**制造差异（真需第二个模型时走既有 `glm-5.3` /
      `kimi-k2.6`，不新造假副本）
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
    **需要改 `ReviewFinding` / `ScopedReviewFinding` 的既有列语义**（那会让既有
    canonical 记录的含义改变，属 Canonical State 边界）—— 停下登记；
    **新增**列 / **新增**并列结构不算（本 GOAL 只做新增）

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-523-goal-086-ec01-04-panel-groups-by-the-object-under-review.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-525-goal-086-ec05-self-bootstrap-closeout.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让阶梯「复检」的下一格（「两个模型在**同一个上游产物**上给出**不同判词**」）
**先具备成立的前提** —— 今天同一 phase 的两位评审者**根本没有被聚到一起**，
因为聚合的键是「任务」而每个评审者各拿一个任务。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：两个评审者的判词若永不聚合，则「多数票」在产品上
  不存在，评审联动是空话）；
- **能力域** = **复检**（阶梯逐字：`评审真的用不同模型判出负`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **聚合键是任务，而每个评审者一个任务**：`adapters/canonical/review_read.py:56-77` 的
   `_panel_rows` 按 `(task_id, contract_id)` 分组；`session_resolution.py:192-197` 对
   `assigned_agents(assignment)` 里**每个 agent** 生成一条 `ResearchTask`，幂等键
   `{run}:{phase}:{agent_id}` ⇒ 同一 phase 的两个评审者 = **两个不同 task_id**。
2. **判词 id 也按任务派生**：`evaluation_gate.py:217` 逐字
   `id=f"finding:{task.id.value}:gate"` ⇒ 一个任务**只有一条**验收判词 ⇒ 任何
   `task_id` 分组下**至多一条** finding ⇒ `aggregate_panel` 的
   `len(findings) < 2` ⇒ 返回 `None` ⇒ 该组不出现。
3. **实测复现（本 GOAL 建档时跑过）**：两条判词分别挂 `task:reviewer_a` /
   `task:reviewer_b`（同 run、同合约、模型 `main/glm-5.3` 与 `main/kimi-k2.6`）⇒
   读面读数 `count: 2, panel_count: 0, panels: []`。这正是 GOAL-085 `W-5` 那行
   （「两个评审实例的 `task_id` 必须相同才会被聚成一票」）在**真实产品路径上恒不成立**：
   产品路径从不给两个评审者同一个 task_id。
4. **多评审 phase 真的存在于出厂目录**：`examples/protocols/ai_ml_research_v0_4_0.yaml:66`
   的 `peer_review` 声明 `scientific_reviewer` `min_instances: 2`；`team_templates.yaml`
   的 `standard` 模板同样 `{min_instances: 2, max_instances: 4}`，而 `project.yaml` 的
   `team_template` 逐字是 `standard` ⇒ 这不是测试专用形状。
5. **既有判据没有咬住它**：`tests/e2e/test_review_panel_on_the_run_path.py` 的「同任务两份
   判词 ⇒ 一条 panel」用手写 `ScopedReviewFinding` 构造，`task_id` 由测试**显式给成同一个**
   ⇒ 判据在替产品做出产品从不做的假设（这是**假绿的形态**，不是判据写错）。

⇒ 后果：阶梯「复检」的下一个要求是「两个模型在同一个上游产物上给出不同判词」，
而**今天连「它们在同一个小组里」都不成立** —— 先补这个前提，否则下一轮的判据
只能继续在测试里手搭场景。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**：`phase_id`（可空列 + 迁移）、按被评对象分组、读面新键。
  **不改** `ReviewFinding` 既有列的**语义**，**不改** `finding:{task}:gate` 的 id 形态；
- **聚合仍是 advisory**：`Decision` 仍由验收门给；
- **设施失败不折算**：无模型身份者点名不进票（GOAL-085 既有语义**逐字保留**）；
- **单评审协议零变化**：没有第二个评审者时不聚合；
- **不为了让判据变绿而把两位评审者塞进同一个任务**：那会改动任务幂等键与续跑对齐语义
  （`round_loop` 与 `resolve_sessions` 的既有不变量），是本 GOAL **明确不做**的事。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **分组纪律**：分组键 = **被评对象**（`phase_id` × `contract_id`）；`phase_id` 缺席 ⇒
  该记录**不参与**聚合且读面点名（不并组、不丢弃）；
- **零回归纪律**：单评审协议上读面与判词**逐字不变**；`panels == []` 的既有语义保留；
- **判据纪律**：新判据必须走**运行链**（不是手写 `ScopedReviewFinding`）；
  既有 6 条面板判据**逐字保留**，新增用例只加不改；
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
- `W-2` —— **聚合只是建议性**：多数票不等于「对」；本 GOAL 判的是**同一小组真的成立**，
  不判「哪一票更对」。
- `W-3` —— **仍不判「两个模型是否同质化」**（需要任务级质量对比，射程外；与 GOAL-084
  的 `W-2`、GOAL-085 的 `W-3` 同一条边界）。
- `W-4` —— **跨 phase 的评审不聚合**：不同 phase 评的是不同阶段的产物，混票会让
  「多数票」失去对象；这是**有意保留**的边界。
- `W-5` —— **不改任务幂等键**：本 GOAL 不给两个评审者同一个任务（那会破坏续跑对齐）；
  聚合在**读面**按被评对象完成。
- `W-6` —— **`phase_id` 的既有行为**：迁移前落库的行 `phase_id` 为 `NULL`，它们**不参与**
  聚合；本 GOAL 不做数据回填（回填需要从 task 反查 phase，而 task 行不含 phase 列 ——
  那是另一件事）。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **改 `ReviewFinding` 既有列语义**或**破坏性迁移** —— 需人工拍板（本 GOAL 只新增）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01/02/03/04 |
| 1 | PLAN-20261018-523 | 待本 cycle 推送后回填 | 新判据 **11 条**（运行链 3 / 读面 8）+ 落库往返 **5 条**；application+api+contracts **2411 passed / 77 skipped**；e2e **360 passed / 17 skipped**；静态门全绿；as-is m0 **23/23** | 见「CI 台账」 | 0（首轮自查修了 3 处：e2e 判据 4 个 mypy 错、1 处 104 列行宽、1 处格式化） | EC-01…EC-04 达成；**EC-05 待做** | 下一轮 = 收口（EC-05） |
| 2 | （收口 cycle，无新子 PLAN） | `fcd42593` / `6f0704ae` | 验证器 **66 条全绿**；两树同结论；as-is m0 **23/23**；治理通过；凭据四面 `offenders=0` | 见「CI 台账」 | 首次 m0 **判红两处**（PLAN 未勾选项 + GOAL-085 断言集锚点迁移）—— 均已修并**逐条申报** | 无（EC 全达成） | **收口** |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1 落地（分组键 + phase_id + 迁移 029 + 两处断言修正） | `a0c60b89` | **零 run** | 同一推送内的中间提交 ⇒ 由 `6f0704ae` 的 run `covered_by`（产品面与判据面同批推送） |
| cycle 1 记录（序 54 建档 + PLAN + RECHECK-524） | `68016a13` | **零 run** | 同上（记录提交） |
| EC-05 收口资产（验证器 + 断言集 + 两处注册 + 阶梯记账） | `fcd42593` | **零 run** | 同上 |
| EC-05 收口（两树判词归档 + RECHECK-525 + GOAL 终态）**tip** | `6f0704ae` | [M0 39160852998](https://github.com/Eswink/research-system-new/actions/runs/39160852998) / [Push 39160853687](https://github.com/Eswink/research-system-new/actions/runs/39160853687) | **M0 八 job 全 `success`**（`container-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `collector-quality` / `observability-overhead-{ubuntu,windows}-latest` / `console-frontend`）+ Push-on-main `success`；`run_attempt=1`、零 `cancelled`、零 rerun。本地 as-is m0：**`PASS: profile=m0; 23 deterministic checks`** |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-085 收口后按阶梯 `下一级` 续推（序 54）。**建档实测五条**：① `_panel_rows` 按 `(task_id, contract_id)` 分组；② `resolve_sessions` 对每个评审 agent 各生成一个 task（幂等键 `{run}:{phase}:{agent}`）；③ 判词 id 逐字 `finding:{task_id}:gate` ⇒ 一个任务至多一条判词；④ **实测复现** `count: 2, panel_count: 0`；⑤ 多评审 phase 在出厂目录里真实存在（`ai_ml_research_v0_4_0` + `standard` 模板 + `project.yaml`）。⇒ 阶梯「复检」的下一个要求**前提不成立**，先补它。 |
| 2026-10-18 | **ACTIVE**（cycle 1 落地） | EC-01…EC-04 达成。**关键读数**：运行链上两位评审者（`glm-5.3` / `kimi-k2.6`）在同一 phase ⇒ `panels` 一条、`scope="PHASE"`、`voters=2`、`independent=True`；按压同模型 ⇒ `independent=False` 并点名 `main/glm-5.3`；不同 phase ⇒ `panels == []`。`phase_id` 落库（SQLite 增量列 + PG `029`）并逐字往返，**既有库补列**亦实测。零回归：application+api+contracts **2411 passed / 77 skipped**、e2e **360 passed / 17 skipped**、as-is m0 **23/23**。**EC-05（自举收口）待做**。 |
| 2026-10-18 | **ACHIEVED**（cycle 2 收口） | EC-01…EC-05 全部 `PASS`。EC-05：验证器本树 **66 条全绿**；两树逐行相同且 `sha256` 一致（`2f357b6c…`）；as-is m0 **23/23**（**在全部记录写入之后**、静止工作树）；治理通过；凭据四面 `offenders=0`；CI 八 job 全 `success`（`6f0704ae`，`run_attempt=1`、零 cancelled）。阶梯两个面都由判词钉住；程序表序 54 登记、预算 55 未触顶。 |
