---
id: GOAL-20261018-085
slug: review-verdict-names-its-model-and-resolves-a-panel
title: 评审判词点名**它的模型**，且多评审真的聚合成一条结论（修正阶梯「复检」的下一级）
status: ACHIEVED
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**复检**域 `下一级是什么`
    在 GOAL-084 收口后逐字为「**评审真的用不同模型判出负**（现只判「配置上的目标不相交」；
    尚无判据证明两个模型在**同一个上游产物**上给出**不同判词**）」；同文件「程序表」序 53
    已登记本 GOAL（**建档实测**驱动）。承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令
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
    让「评审」在产品面上成为**可归因且可聚合**的事实：每一条落库的验收判词都要点名
    **它是哪个模型判的**（`ModelDefinition.model_name` + endpoint，而不是 agent 名），
    多评审实例的独立判词要能被**聚合**成一条**建议性**结论并**逐票可读**
    （票数、少数意见、是否独立）。判据成对：**同模型多实例 ⇒ 不可称独立** +
    **异模型多实例 ⇒ 可称独立且聚合结论点名逐票**。

exit_criteria:
  - id: EC-01
    criterion: >-
      **判词可归因到模型**：落库的 `ReviewFinding` 带**评审者模型身份**
      （`(endpoint_id, model_name)` 的稳定串形，与 GOAL-084 的解析面同源），
      由**运行链**在构造判词时填入 —— 不是由测试、也不是由读面补。
      **无模型可归因 ⇒ 点名**（finding 带明确理由，不静默留空）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_review_attribution.py -q`
      ⇒ 全绿；判据覆盖：判词带模型身份 / 身份取**解析后的目标**（非 agent 名）/
      解析不了 ⇒ 点名 / 既有 `reviewed_by` 语义逐字不变。
    status: PASS
  - id: EC-02
    criterion: >-
      **多评审可聚合成一条结论**：一个 phase 上**多于一个**评审 agent 时，它们的独立判词
      经**确定性聚合**（多数票；平票与全票失败**分开点名**）产出一条**建议性**结论，
      并把**逐票**（谁、哪个模型、判了什么）一并落库可读。
      **聚合不夺取真相权**：`Decision` 仍由既有验收门给出，聚合结论标为 advisory。
    verify: >-
      `tests/application/test_review_panel_aggregation.py` ⇒ 全绿；判据覆盖：
      两票一致 / 两票相反（平票点名） / 一票失败一票通过（部分失败不折算成通过）/
      单评审 ⇒ 不聚合（既有语义逐字不变）。
    status: PASS
  - id: EC-03
    criterion: >-
      **独立性可判且与 GOAL-084 同源**：聚合结论里必须能读出**评审者之间是否独立**
      （按解析后的 `(endpoint, model_name)` 判，与 `check_heterogeneity` 同一判据面）；
      **同模型两个实例 ⇒ `independent=false` 并点名**；异模型 ⇒ `independent=true`。
      **反证**：把第二个评审者指回与第一个相同的模型 ⇒ 结论翻转。
    verify: >-
      同一判据文件；成对断言；判词**点名**重复的那个目标。
    status: PASS
  - id: EC-04
    criterion: >-
      **接进产品路径且默认零回归**：上述能力在**运行链**上生效（不是只在测试里）；
      **单评审协议 ⇒ 逐字不变**（既有 1500+ 判据零回归）；多评审协议上
      **真实 run** 可读出逐票 + 聚合 + 独立性。
    verify: >-
      `tests/e2e/test_review_panel_on_the_run_path.py` ⇒ 全绿；
      **按压**：关掉聚合 ⇒ 该 run 的读面只剩单票、聚合缺席（可判）；
      既有 `tests/` 全绿。
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
      **用 agent 名当模型身份**：判词必须点名**解析后的 `(endpoint, model_name)`**；
      写 `agent:<id>` 或 profile 名一律**不算**可归因
    - >-
      **让聚合结论夺取真相权**：`Decision` 仍由验收门给出；把 advisory 聚合写成
      `Decision` 或改它的判词即越界
    - >-
      **把「设施失败」折算成「判负」**：`ReviewerFinding.failure` 非空必须是结构化失败，
      不得映射成被评对象的 FAIL/PASS
    - >-
      为让判据变绿而**改出厂目录**制造差异（真需第二个模型时走既有 `glm-5.3` /
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
  - .cursor/plans/tasks/PLAN-20261018-520-goal-085-verdict-names-its-model-and-panel-aggregates.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-522-goal-085-ec05-self-bootstrap-closeout.md
memory_entries: []
---

## 目标与退出标准

**一句话**：让「评审」从**一条由验收门顺手生成的判词**，变成**可归因到模型、可聚合成
建议性结论、且独立性可判**的事实 —— 阶梯「复检」域的 `下一级`。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：一个**说不出自己是谁判的**评审，其「通过」不构成
  可复核的证据；多评审若不聚合，等于只有一票）；
- **能力域** = **复检**（阶梯逐字：`评审真的用不同模型判出负`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **落库判词不带模型身份**：`packages/domain/evidence.py:127` 的 `ReviewFinding` 只有
   `id` / `review_type` / `verdict` / `findings` / `reviewed_by` / `reviewed_at` ——
   **没有** `model_identity`；SQLite 表 `review_findings` 的列逐个读出亦无该列
   （`adapters/sqlite/review_finding_store.py:20-33`）。
2. **`reviewed_by` 装的是 agent 名**：`task_phase_helpers.py:244` 逐字
   `reviewer=f"gate:{tctx.spec_context.agent.id}"` ⇒ 读者只能知道**哪个 agent 实例**
   走了验收门，**不知道它跑在哪个模型上**（而 GOAL-084 已证明 agent 名与底层模型可以
   完全脱钩）。
3. **评审小组从不聚合**：`packages/application/evaluation/panel.py` 的 `run_panel` /
   `_majority_verdict` / `PanelResult` 在产品代码里**零构造点**
   （`rg "run_panel\(" --glob '!tests/**'` 只命中定义处）；`LlmReviewer(` 与
   `ReviewAssignment(` 同样**零构造点**。⇒ **多评审 = 多条互不相干的判词**。
4. **`ReviewerFinding` 其实早有 `model_identity`**（`packages/domain/eval_result.py:68`），
   但它是 **eval 面**（M11 离线评测）的类型，运行链走的是 `evidence.ReviewFinding`
   ⇒ 同一个概念在两条链上**一个有一个没有**。

⇒ 后果：阶梯说的「评审真的用不同模型判出负」在产品上**不可判** ——
不是「没证明」，而是**判词里根本没有模型这一格**。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**：判词的模型归因（新列 / 新并列结构）、聚合的建议性结论、独立性标记。
  **不改** `ReviewFinding` 既有六列的**语义**（`verdict` / `reviewed_by` 的写法逐字不变）；
- **聚合是 advisory**：`Decision` 仍由验收门给；聚合结论**不得**变成 `Decision`；
- **设施失败不折算**：`failure` 非空 ⇒ 结构化失败，不映射成 PASS/FAIL；
- **单评审协议零变化**：没有第二个评审者时**不聚合**，读面逐字不变。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **归因纪律**：模型身份取**解析后的目标** `(endpoint_id, model_name)`，与
  `packages/application/preflight/review_independence.py` **同一处**取值 —— 不另造一套；
- **聚合纪律**：确定性（同票同结论）、平票与全失败**分开点名**、advisory 明写；
- **零回归纪律**：单评审协议上读面与判词**逐字不变**（有专门反证用例）；
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
- `W-2` —— **聚合只是建议性**：多数票不等于「对」；本 GOAL 判的是**可归因与可聚合**，
  不判「哪一票更对」。
- `W-3` —— **只判模型身份是否相同**：不判「两个模型是否同质化」（那需要任务级质量对比，
  射程外；与 GOAL-084 的 `W-2` 同一条边界）。
- `W-4` —— **不改既有 `reviewed_by` 的写法**：要在**新增**的并列结构里放模型身份；
  既有读面字段逐字不变。
- `W-5` —— **两个评审实例的 `task_id` 必须相同才会被聚成一票**：这是有意的（不同任务评的是不同产物），但意味着「跨任务的评审小组」**不在射程**。
- `W-6` —— `panels` 里**没有**「哪一票来自哪个 phase」这一格：阶段归属要从 `reviews[].task_id` 反查；「按阶段看小组」属新增读面字段，不在本轮。

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
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01/02（归因 + 聚合） |
| 1 | PLAN-20261018-520 | 待本 cycle 推送后回填 | 新判据 **29 条**（归因 10 / 聚合 13 / 运行路径 6）；application **1201**；含 e2e 宽面 **3086 passed / 94 skipped**；静态门 `ruff` / `format` / `mypy`（1279 files）全绿；as-is m0 **23/23** | 见「CI 台账」 | 0（首轮 m0 抓到三处自查缺陷：两个函数参数 >5、e2e 判据 5 处 mypy 错 —— 均已修） | EC-01…EC-04 达成；**EC-05 待做** | **已收口**：EC-05 达成（`RECHECK-20261018-522`） |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1 落地（归因 + 聚合 + 独立性 + 读面） | `941752a1`（**tip**） | [M0 39138987866](https://github.com/Eswink/research-system-new/actions/runs/39138987866) / [Push 39138987152](https://github.com/Eswink/research-system-new/actions/runs/39138987152) | **M0 八 job 全 `success`**（`container-quality` / `quality-ubuntu-latest` / `quality-windows-latest` / `eval-gate` / `collector-quality` / `observability-overhead-{ubuntu,windows}-latest` / `console-frontend`）+ Push-on-main 三条 CodeQL `success`；`run_attempt=1`、零 `cancelled`、零 rerun。本地 as-is m0：**`PASS: profile=m0; 23 deterministic checks`** |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承 GOAL-084 收口后按阶梯 `下一级` 续推（序 53）。**建档实测四条**：① `evidence.ReviewFinding` 无 `model_identity`，SQLite 表也无该列；② `reviewed_by` 逐字是 `gate:<agent id>`（agent 名，不是模型）；③ `run_panel` / `LlmReviewer` / `ReviewAssignment` 在产品代码**零构造点** ⇒ 多评审互不相干；④ `eval_result.ReviewerFinding` 有 `model_identity`，但那是另一条链 ⇒ 同一概念一有一无。 |
| 2026-10-18 | **ACTIVE**（cycle 1 落地） | EC-01…EC-04 达成：判词带 `reviewer_model`（`endpoint/model_name`，与 GOAL-084 的解析面同源）、多票确定性聚合（平票与无身份者**分开点名**、advisory **不夺真相权**）、独立性与 GOAL-084 同源（同目标两个实例 ⇒ 不独立并点名）、读面与落库链都带归因。新判据 **29 条**；零回归 **1201 + 3086**；as-is m0 **23/23**。**EC-05（自举复检）待做**。 |
| 2026-10-18 | **ACHIEVED**（cycle 2 收口） | EC-01…EC-05 全部 `PASS`。EC-05：验证器本树 **67 条判词全绿**；两树逐行相同且 `sha256` 一致；as-is m0 **23/23**；治理通过；凭据四面 `offenders=0`；CI 台账逐提交（`941752a1` 八 job 全 `success`）。阶梯两个面（阶梯行 + 进展记录）都由判词钉住。 |
