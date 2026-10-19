---
id: GOAL-20261018-088
slug: experiment-design-read-from-what-was-retrieved
title: 实验设计由**系统真的取回了什么**派生（第二个设计来源：检索证据）
status: ACHIEVED
created_at: 2026-10-18
updated_at: 2026-10-18
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）「科研能力阶梯」的**实验**域 `下一级是什么`
    逐字为「**实验设计本身由检索派生**（现参数与臂由**计划内容**派生且已被真跑消费；
    「设计直接读检索结果」仍无判据）」。GOAL-080 让设计可取自**计划产物**，而计划是**模型写的
    正文** ⇒ 「设计由检索派生」实际是「设计由**计划作者**派生」。**建档实测**：
    `services/api/experiment_support.py:101` 的 `DESIGN_SOURCE_PLAN = "plan"` 是**唯一**取值，
    未认得的来源**点名拒绝**；而「本 run 的系统取得证据（`TrustLabel.RETRIEVED`）」的 run
    作用域读取器**已经存在**（`retrieval_context._retrieved_evidence`，与覆盖门同一判据）
    ⇒ 缺的只是把设计来源接到它上面。故序 56 登记本 GOAL。承用户 2026-10-06 全部权限下放 +
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
    让「实验设计」的**来源**可以是**系统真的取回了什么**，而不只是「计划作者写了什么」：
    新增 `design_source="retrieval"` —— 臂与参数从**本 run 的 `TrustLabel.RETRIEVED` 证据**
    的制品内容里读出（run 作用域、确定性、零出网、fail-closed）。**性质维度不可伪造**：
    同一条内容若是「用户提供 / 模型自产」而非「系统取得」，**不算**检索派生（点名拒绝）。
    **两个来源互斥**：`retrieval` 与显式 `arms`、或与 `plan` 同时在场 ⇒ 点名拒绝（不猜）。

exit_criteria:
  - id: EC-01
    criterion: >-
      **设计由检索记录派生**：`design_source="retrieval"` ⇒ `_arms_for` 返回的臂**就是**
      本 run 系统取得证据里那一条记录的设计块里的臂（参数逐键）；换一份记录 ⇒ 换一套臂。
      读出的设计**点名它读的是哪条证据**（`arm_source_evidence`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_design_from_retrieval.py -q`
      ⇒ 全绿（10 条）；判据覆盖：臂来自记录 / 换记录换设计 / 来源可归因。
    status: PASS
  - id: EC-02
    criterion: >-
      **性质维度不可伪造 + run 作用域**：同一条内容若是 `USER_PROVIDED`（或任何非
      `RETRIEVED`）⇒ **不算**检索派生并点名；他 run 的记录**读不到**（同样点名）。
    verify: >-
      同一判据文件的第二组；成对断言（`RETRIEVED` 通过 / 其余拒绝）。
    status: PASS
  - id: EC-03
    criterion: >-
      **来源唯一且 fail-closed 逐条点名**：`retrieval` 与显式 `arms` 同时在场 ⇒ 点名
      「undecidable」；没有系统取得证据 / 记录里没有设计块 / **两份设计** / 参数越白名单
      各自点名（不静默回落、不猜「最后一条」）。**未声明 ⇒ 既有语义逐字不变**。
    verify: >-
      同一判据文件的第三组；外加既有 `tests/application/test_experiment_design_decides.py`
      与 `tests/e2e/test_experiment_design_from_the_plan.py` 全绿（零回归）。
    status: PASS
  - id: EC-04
    criterion: >-
      **两个来源真的不同**：`DESIGN_SOURCES` 恰为 `(plan, retrieval)` 且不相等；
      未认得的来源名仍点名拒绝；`plan` 来源的行为**逐字不变**（同一批既有判据）。
    verify: >-
      同一判据文件 + 既有实验判据（40 条）全绿。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**、**静止工作树**）+ 治理绿 + 凭据审计 + CI 台账**逐提交**
      （`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**；
      自我指涉边界**明写并封闭**）+ 残余与未覆盖范围逐条。**★ 并含阶梯记账（两个面）**：
      阶梯「实验」行的 `依据 GOAL` **与**宪章 `进展记录` 各收录本 GOAL。
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
      **让非 `RETRIEVED` 的内容冒充「检索派生」**：性质维度是**这一格的全部意义** ——
      用 `USER_PROVIDED` / 模型自产内容通过判据即越界
    - >-
      **静默回落**：读不到 / 多份设计 / 越白名单必须**点名**；回落到装配面声明的臂、
      回落到计划来源、或「取最后一条」都算越界
    - >-
      **改既有 `plan` 来源的行为**：`read_design_from_plan` 的语义逐字不变
      （本轮只**新增**第二个来源与一个公开的共享解析器入口）
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
    **需要改 `TrustLabel` 的语义或新增取值**（那会改 Canonical 的信任面）—— 停下登记；
    本 GOAL 只**读**既有取值

child_plans:
  - .cursor/plans/tasks/PLAN-20261018-529-goal-088-ec01-04-experiment-design-from-retrieval.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-531-goal-088-ec05-self-bootstrap-closeout.md
memory_entries: []
---

## 目标与退出标准

**一句话**：把「实验设计从哪来」的答案从「**计划作者**写了什么」扩展到
「**系统真的取回了什么**」—— 并且让「取回」这件事**按性质判定**（只有 `RETRIEVED` 算）。

**主线归属（宪章要求逐条声明）**：

- **轴** = **质量**（产出的可判定性：一个只从模型自述里取设计的实验，其「设计」没有
  外部依据）；
- **能力域** = **实验**（阶梯逐字：`实验设计本身由检索派生`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

1. **来源只有一种**：`services/api/experiment_support.py` 的 `DESIGN_SOURCE_PLAN = "plan"`
   是唯一取值；`if source != DESIGN_SOURCE_PLAN:` ⇒ **未认得的来源点名拒绝**。
2. **计划是模型正文**：`design_from_plan` 的 docstring 与读取器都按「模型写的正文」解析
   （`ENVELOPE_CONTENT_KEY = "content"`）⇒ 「设计由检索派生」今天实际是
   「设计由**计划作者**派生」。
3. **检索证据的读取面**早已存在：`retrieval_context._retrieved_evidence` 按
   `run_id` + `TrustLabel.RETRIEVED` + `tool-result:` 前缀过滤（与覆盖门同一判据）
   ⇒ 缺的只是把设计来源接到它上面。
4. **性质维度已有权威来源**：`SourceRecord.trust_label` 是唯一盖章点（`RETRIEVED` 由
   provider 声明的 network_domains 盖章）⇒ 「检索派生」的判据**有**可依赖的事实。

⇒ 后果：阶梯「实验」域的 `下一级` 今天只能靠**计划内容**近似，而计划内容是模型自述 ——
「设计站在检索上」这件事在产品上**没有被判定过**。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**第二个来源（`design_source="retrieval"`）与一个**公开的共享解析器入口**
  （`design_block_in`，两个来源同一份解析，不漂成两套口径）；
- **不改** `plan` 来源的任何行为；
- **不改** `TrustLabel` 的语义或取值（只读）；
- **不静默回落**：读不到 / 多份 / 越界逐条点名；
- **性质维度不可伪造**：非 `RETRIEVED` 的内容**不算**检索派生。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **性质纪律**：只认 `TrustLabel.RETRIEVED`（与覆盖门同一判据），不认前缀猜测；
- **来源唯一纪律**：两个来源与显式 `arms` 三者互斥，冲突即点名；
- **零回归纪律**：`plan` 来源与未声明来源的既有行为逐字不变；
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
- `W-2` —— **不判「检索内容里为什么会有设计块」**：本 GOAL 判的是「设计**从检索记录里
  读出来**」，不判「检索记录里该不该有设计」（那取决于 provider 与协议）。
- `W-3` —— **不判设计的科学质量**：臂名与参数是否合理不在射程（那是计划/评审的事）。
- `W-4` —— **真实检索 provider 的返回形态**：受控证据证的是读取与判定这条链；
  真 provider 返回里是否有设计块属 live 观察。
- `W-5` —— **只支持「一份记录带一份设计」**：多份 ⇒ 点名拒绝（不猜）；「多份设计合并」
  是另一件事，未实现。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **改 `TrustLabel` 语义 / 破坏性迁移** —— 需人工拍板（本 GOAL 只读）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01…EC-04 |
| 1 | PLAN-20261018-529 | `f45d9349` | 新判据 **10 条**；既有实验判据 **40 passed**；静态门全绿 | 见「CI 台账」 | 0（首轮自查修了 3 处 lint：函数 6 参数、1 处 101 列、import 排序/未用） | EC-01…EC-04 达成 | 收口（EC-05） |
| 2 | （收口 cycle，无新子 PLAN） | `2447fa60` + 收口提交 | 验证器 **68 条全绿**；两树逐行相同 + `sha256` 一致；as-is m0 **23/23**；治理通过；凭据四面 `offenders=0` | 见「CI 台账」 | 1（`RESIDUAL_MARKERS` 从模板继承的 `W-6` 与本文档登记的五条不符 ⇒ 清单按实际收窄，注释写明；少了任一条仍判红） | 无（EC 全达成） | **收口** |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档 + cycle 1（读取器 + 声明面 + 10 条判据 + 记录） | `f45d9349` | **零 run** | 中间提交 ⇒ 由 `3aa9d838` 的 run `covered_by`（代码面与判据面同批推送） |
| EC-05 收口资产（验证器 + 断言集 + 两处注册） | `2447fa60` | **零 run** | 同上 |
| 规模门修复（证据登记拆 `_register`） | `f2f6557a` | **零 run** | 同上 |
| EC-05 读数回填 + **tip** | `3aa9d838` | [M0 39182686242](https://github.com/Eswink/research-system-new/actions/runs/39182686242) / [Push 39182685977](https://github.com/Eswink/research-system-new/actions/runs/39182685977) | **M0 八 job 全 `success`**（`container-quality` / `quality-{ubuntu,windows}-latest` / `eval-gate` / `collector-quality` / `observability-overhead-{ubuntu,windows}-latest` / `console-frontend`）+ Push-on-main `success`；`run_attempt=1`、零 `cancelled`、零 rerun。本地 as-is m0：**`PASS: profile=m0; 23 deterministic checks`** |

**自我指涉边界（明写并封闭）**：受判的是**代码面**与**收口面**的 CI；只改 `.cursor/plans/**`
的记录提交，其 CI 照实登记但**不再**为它追加新行 —— 边界在「收口时的 tip 那一行」闭合。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **ACTIVE** | **建档**：承序 55 触顶核算后按阶梯 `下一级` 续推（序 56）。**建档实测四条**：① `DESIGN_SOURCE_PLAN = "plan"` 是唯一取值、未认得即点名拒绝；② 计划内容是**模型正文** ⇒ 今天「设计由检索派生」实为「由计划作者派生」；③ 检索证据的 run 作用域读取器**已存在**（`_retrieved_evidence`，同一判据面）；④ 性质维度的权威来源是 `SourceRecord.trust_label`。cycle 1 的读取器与 10 条判据已落地（见 PLAN-529）。 |
| 2026-10-18 | **ACHIEVED**（cycle 2 收口） | EC-01…EC-05 全部 `PASS`。EC-05：验证器本树 **68 条全绿**；两树逐行相同且 `sha256` 一致；as-is m0 **23/23**（在全部记录写入之后、静止工作树）；治理通过；凭据四面 `offenders=0`。阶梯「实验」行与宪章进展记录都由判词钉住；程序表序 56 ⇒ 预算 56/60。 |
