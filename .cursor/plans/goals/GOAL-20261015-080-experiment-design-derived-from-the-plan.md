---
id: GOAL-20261015-080
slug: experiment-design-derived-from-the-plan
title: 实验设计由计划派生（计划/实验域 → 下一级）
status: ACTIVE
created_at: 2026-10-15
updated_at: 2026-10-15
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    战役宪章（`.cursor/plans/goals/MAINLINE.md`）的「科研能力阶梯」有**两行**逐字指向
    同一件事：**计划**域的 `下一级是什么` =「**计划驱动实验**（现由协议静态声明实验，
    模型不参与实验设计）」；**实验**域的 `下一级是什么` =「**实验设计本身由检索/立题派生**
    （现为「参数由计划声明 + 多臂/对照」；尚无判据证明实验设计本身由检索/立题产出派生）」。
    承用户 2026-10-06 全部权限下放 + 2026-10-14 方向指令（「每一次自动迭代都必须让科研
    能力越来越近」）。authorization 要点：
    (1) **本 GOAL 的定位** = 阶梯「计划」与「实验」两域的**同一个下一格**；它**必须让阶梯
    前进**（由 `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    (3) **来源与授权口径**：push-to-main-for-CI（只推 `main`、不 force、不重写历史、
    不推旁支）；默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**，只在单条命令上显式传）。

objective: >
    让实验的**设计**（跑几个臂、每臂什么参数）**从计划产物派生**：`experiment` phase
    把计划阶段产出的制品声明为自己的**输入**、从它的**内容**里确定性地读出设计
    （白名单校验、缺设计**点名拒绝**而不是回落装配常量），且「设计因计划而不同」是
    可判定的 —— 换计划内容 ⇒ 设计跟着变。

exit_criteria:
  - id: EC-01
    criterion: >-
      **计划产物成为实验的声明输入**：`experiment` phase（协议层）声明
      `research_plan` 为其输入制品，且该声明经既有缝（`phase.inputs` →
      `spec_context.declared_input_artifacts` → 结果注册面）**真的到达执行体**。
      判据成对：**声明在**（协议 + 装配面都指出同一份制品）+ **到达在**（装配上下文里
      能看到它）；反证：摘掉协议里的 `inputs` 声明 ⇒ 判据红。
    verify: >-
      离线判据：`tests/e2e/test_experiment_design_from_the_plan.py` ⇒ 声明到达装配上下文；
      `tests/application/test_experiment_design_reader.py` ⇒ 读取器成对判据全绿。
    status: PENDING
  - id: EC-02
    criterion: >-
      **设计由计划产物的内容派生**：确定性读取器从计划产物**内容**里读出实验设计
      （臂名 + 参数集），逐键过**既有白名单**（`ALLOWED_PARAMETERS`，不新开口子）；
      **缺设计 ⇒ 点名拒绝**（不是静默回落装配常量 —— 那会让「计划驱动」变成一句空话）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_experiment_design_reader.py -q`
      ⇒ 全绿；判据覆盖：合法设计逐键读出 / 白名单外键点名拒绝 / 缺设计块点名拒绝 /
      畸形设计点名拒绝。**反证**：让读取器对缺失回落缺省 ⇒ 判据红。
    status: PENDING
  - id: EC-03
    criterion: >-
      **「设计因计划而不同」可判定**：一次 run 的实验设计**由计划内容决定** ——
      两份不同的计划内容 ⇒ 两套不同的臂/参数；同一份 ⇒ 同设计（确定性）；且真实 run 上
      实验记录里的臂与参数**就是**计划里那套（逐条可溯源），不再来自装配常量。
    verify: >-
      离线 e2e：`tests/e2e/test_experiment_design_from_the_plan.py` ⇒ run `SUCCEEDED`；
      读面逐臂给出计划里声明的那些臂与参数；**反证**：装配面声明臂与计划声明臂不同 ⇒
      判据如实判否并点名（设计来源必须唯一）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次**：真实模型会话写出的计划产物**驱动**该 run 的实验臂与参数，
      读数记档（run id / 计划产物 digest / 派生的设计 / 各臂指标）。**若模型侧不可用
      或模型不产出设计块** ⇒ 按降级梯如实登记（记 PENDING + 点名阻塞点），**不得**伪造。
    verify: >-
      live 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且设计读数在树。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23
      （**在全部记录写入之后**）+ 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 +
      原因 + `covered_by`；**空集合 = 未取证**；自我指涉边界**明写并封闭**）+
      残余与未覆盖范围逐条。**★ 并含阶梯记账**：向宪章 `进展记录` 追加本行
      （**能力域 = 计划**），使阶梯的「计划」域 `依据 GOAL` 收录本 GOAL
      （「实验」域如有推进亦同轮收录）。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING

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
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**（记录 / GOAL / PLAN /
      `examples/**` / 测试 / 文档）—— **只在 gitignored 的 `.env` 落位**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - >-
      让「设计由计划派生」靠**静默回落**成立（缺设计块 ⇒ 回落装配常量）——
      那会把「计划没写」伪装成「计划驱动」；缺设计必须**点名拒绝**
    - >-
      绕开参数白名单：设计块里的键必须逐键过 `ALLOWED_PARAMETERS`；
      读取器**不得**接受白名单外的键（§9 默认 deny）
    - 为让「计划驱动」成立而**放宽**既有的实验参数 / 臂 / 对比判据（GOAL-079 的判据一字不动）
    - 改沙箱镜像 / 镜像 pin（既有安全面；需要即 BLOCKED 留人工拍板）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）

escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **新站不可用**（连通 / 协议面 / 工具调用任一不通）且无替代路径 —— 记 BLOCKED，
    逐条写明阻塞点（**不得**为此放宽任何判据或伪造成功）
  - >-
    需要**改动沙箱镜像或镜像 pin** 才能成立 —— 立即 BLOCKED，留人工拍板
    （镜像 pin 是既有安全面，不得自行改）

child_plans: []
latest_recheck: null
memory_entries: []
---

## 目标与退出标准

**一句话**：把「实验设计」从**装配常量**推进到**由计划产物派生** —— 阶梯「计划」域与
「实验」域的**同一个下一格**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进）与**质量**（产出的可判定性）**同时**受益：
  设计的来源从「装配面写死」变成「计划产物里写着」，实验才有「因研究而不同」的资格；
- **能力域** = **计划**（阶梯逐字：`计划驱动实验`（现由协议静态声明实验，模型不参与实验设计））
  且**同时**推进**实验**（阶梯逐字：`实验设计本身由检索/立题派生`）；
- **两者是同一格**：计划域说的「模型/计划参与实验设计」与实验域说的「设计由立题派生」
  在今天指向同一件事 —— 计划产物的**内容**里带着设计，实验读它。

**为什么这一条更近科研**（对照阶梯，**建档实测**）：

- **实测 ①**：`examples/protocols/research_report_chain_v1.yaml` 的 `experiment` phase
  **没有 `inputs:` 声明**（`inputs:` 只出现在 `plan` / `review` / `report` 三处）⇒
  计划产物**从未被声明**为实验的输入 —— 也就是说协议层「实验与立题无关」是**字面事实**；
- **实测 ②**：全仓 `research_plan` 在 `packages/` 与 `services/` 下**零命中**
  （只出现在 `examples/` 的协议与合约里）⇒ 计划制品在**产品代码里没有任何消费者**；
- **实测 ③**：臂与参数今天由**装配常量**给出 —— live run 里就是
  `tests/e2e/test_research_report_chain_live.py` 的 `_LIVE_ARMS = {"control": {}, "treatment": {"n_items": 120}}`
  ⇒ **设计是测试作者写的**，不是计划写的；
- **实测 ④**：`ExperimentPlan` 的字段逐个读出（`id` / `name` / `hypothesis` /
  `task_contract_ref` / `input_spec_digest` / `state` / `created_at` / `updated_at`）——
  **仍然没有参数位**（GOAL-079 建档时如此，现在仍如此）。

⇒ 缺口**不是**参数能不能进容器（GOAL-079 已通），而是「**设计是谁写的**」——
今天写它的是装配面的人；本轮要让它是**计划产物**。

**本 GOAL 不加新依赖、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修
产品代码；若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **设计面纪律**：读取器是**确定性**的（不建会话、不出网），逐键过 `ALLOWED_PARAMETERS`；
  **缺设计 ⇒ 点名拒绝**（fail-closed）。
- **来源唯一性**：设计**只能**有一个来源。装配面若同时声明臂，判据必须**点名冲突**
  （「哪个说了算」不可判定是最坏形态）。
- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用**或模型不产设计块** ⇒
  记 PENDING + 点名阻塞点；**不伪造**。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证
（逐 job annotation / 同时终止时刻 / 状态页 incident），与 `cancel-in-progress`
（`run conclusion=cancelled`）形态区分。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS 且有实跑证据 + 独立 RECHECK + 本文件收口
  （`latest_recheck` 为**仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条
  + **阶梯记账成立**（本 GOAL 被某个域的 `依据 GOAL` 收录）。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 残余与未覆盖范围（逐条明写）

**建档时已知的残余**（将在各 cycle 如实更新）：

- `W-1` —— **EC-05 本身**在收口复检跑之前仍是待办（它的判词由本 GOAL 的收口验证器产出）。
- `W-2` —— **计划的「写法」不在射程内**：本轮判的是「设计**从计划产物读出来**」；
  模型怎么写计划（提示词质量 / 是否真的推理过设计）**无人判**（承 GOAL-079 `W-5` 的另一半）。
- `W-3` —— **参数仍受既有白名单约束**（`seed` / `n_items` / `duplicate_pairs`）：
  设计块能表达的**参数空间**就这三个键；扩容需同轮加白名单与脚本读取（承 GOAL-079 `W-3`）。
- `W-4` —— **臂数 > 2 与择优不在射程内**（承 GOAL-079 `W-2`）。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**（M18 deferred）、**部署面验证**、
  **D 组审批通道** —— 均**不做**；
- **改沙箱镜像 / 镜像 pin**（既有安全面）—— **需人工拍板**，本轮一字未动；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；真实 run 由 live 判据在**显式开关下**跑；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- **改沙箱镜像 / 镜像 pin** —— 需人工拍板（既有安全面）；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 PENDING | cycle 1 = EC-01（计划产物成为实验的声明输入） |

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 建档（序 48） | 见「状态历史」 | 见「状态历史」 | **待 cycle 1 首次推送后回填**（建档提交与 cycle 1 同批推送时并入该行） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | **ACTIVE** | **建档**：承 GOAL-20261015-079 收口后宪章「第四件」（收口后立即开下一个）。**定位** = 阶梯「计划」域与「实验」域的**同一个下一格**（两行逐字都指向「设计由计划/立题派生」）。**建档实测**（四条）：① `experiment` phase **没有 `inputs:` 声明**（`research_report_chain_v1.yaml` 里 `inputs:` 只在 plan/review/report 三处）⇒ 计划产物从未被声明为实验的输入；② 全仓 `research_plan` 在 `packages/`·`services/` **零命中** ⇒ 产品代码里没有消费者；③ 臂与参数由**装配常量**给出（live 就是 `_LIVE_ARMS`）⇒ 设计是测试作者写的；④ `ExperimentPlan` 字段逐个读出，**仍无参数位**。这四条就是本 GOAL 的靶子与可行性依据。 |
