---
id: GOAL-20261014-077
slug: research-report-and-the-end-to-end-research-arc
title: 端到端研究 + 人类可读研究报告（报告域 L0 → L1）
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-14 用户会话指令：**「计划归档必须让每一次自动迭代『科研能力』都必须越来越近」**，
    并要求跑一次端到端实验（自己检索问题 → 思考 → 计划 → 实验 → 复检 → 结果 → 报告），
    本次**不要求论文、报告即可**；同时授权切换中转站（新站 + 新 key，**特例允许明文出现**，
    但只在 gitignored 的 `.env` 落位）。authorization 要点：
    (1) **本 GOAL 的定位** = 宪章「科研能力阶梯」的**报告域 L0 → L1**，即阶梯上
    「报告」一行的 `下一级是什么`（人类可读研究报告）与「检索」一行的第一步
    （活检索产出**进报告**）。**它必须让阶梯前进**（由
    `tests/tooling/test_mainline_research_ladder_advances.py` 机械强制）。
    (2) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA（M18 deferred）/
    D 组审批通道 / 部署面验证 / `G24-5` / `R26-2/3/4/6` / 把 destructive 能力改 allow /
    为凑数扩承接面 / 宣称项目安全（`R-M1`）/ 宣称「恰好一次」（**明确否认**）。
    (3) **并行授权**：序 44（`GOAL-20261014-076`，API 卫生）**置 PAUSED**（用户指令：
    每轮必须更近科研），其子 PLAN-461 保持 `IN_PROGRESS` 留待将来。
    (4) 来源与授权口径：push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E`
    **不进 `.env`**，只在单条命令上显式传）。
objective: >
    把「一次完整研究」跑到有**人类可读报告**为止：**立题由检索产出派生**（不是模型凭空写）→
    真检索取真标识 → 真容器实验出真指标 → 评审真判负 → **report phase 汇编**出
    `research_report.md`（四节 + 每个数字可溯源）。交付两条判据 +
    一次**真实中转站上的实跑**（报告落盘、run id 与 digest 记档）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **报告汇编器在树且其判据成对**：`packages/application/deliverable/research_report.py`
      提供 `build_research_report(ReportInputs) -> str`，四条判据各自可判：
      **(a) 四节齐全**（`SECTION_HEADINGS` 逐条在位）；**(b) 事实逐字来自输入**
      （来源标识 / 指标值 / 判词逐字出现在报告里，报告**不重算不编造**）；
      **(c) 缺事实要说明不得省略**（检索 / 实验 / 评审缺席时该节仍在且写明「无 + 原因」）；
      **(d) 确定性**（同输入 ⇒ 逐字节相同）；**(e) 空 `run_id` 点名拒绝**；
      **(f) 局限节自陈**（汇编而非撰写 + 缺来源/缺指标时明写「无外部证据 / 无实验支持」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/test_research_report_assembler.py -q`
      ⇒ **全绿**；`SECTION_HEADINGS` 四条标题逐一在报告里出现；`REPORT_ARTIFACT_NAME`
      以 `.md` 结尾且 `REPORT_MIME == "text/markdown"`（制品名与类型是合约的一部分）。
    status: PASS
  - id: EC-02
    criterion: >-
      **报告经产品路径产出**：report phase 的制品是**真落 canonical 的 markdown**，
      且**其内容可复核**——每一节的数字 / 标识能追回本 run 的持久事实。
    verify: >-
      实跑读到 `research_report.md` 制品（`GET /artifacts/{id}/content` 内联预览为
      `text/markdown`）；报告中出现的来源标识与 `GET /runs/{run_id}/evidence` 读面逐条一致；
      指标值与 `GET /runs/{run_id}/experiments` 的落库值**逐字相同**；
      报告 digest 由内容重算（内容寻址）。**本机若无法完成 ⇒ 记 PENDING + 点名阻塞点**，
      不得假绿。
    status: PENDING
  - id: EC-03
    criterion: >-
      **立题由检索产出派生**（承阶梯「计划」行的第一步）：plan phase 的交付物声明它
      **消费了**上一 phase 的检索产出（经既有 `EVIDENCE_COVERAGE: minimum_retrieved_sources`
      的**性质维**），且该声明**在场**——覆盖里至少一条**系统取得**的来源。
    verify: >-
      新协议 `research_report_chain_v1` 的 plan phase 引用合约 `research_report_plan`
      （其 `acceptance_criteria` 含 `minimum_retrieved_sources: 1`）；
      **反证**：把 plan phase 的 `inputs` 声明摘掉 ⇒ 该 phase 判拒并点名（与
      `multi_role_research_v1` 的评审反证同形）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次完整研究并留报告**：用**新站**（`discovery-api.intern-ai.org.cn` /
      `deepseek-v4-flash-vision`）+ 真实 runtime 跑完整协议到终态，报告落盘；
      run id / 报告 digest / §4 漂移事实（声明名 vs 返回名）记进本 GOAL 与回合报告。
    verify: >-
      live e2e 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且报告制品在位；
      **若模型侧不可用** ⇒ 按降级梯如实登记（② 会话面回退 Fake 但检索/实验/报告仍真；
      ③ 记 BLOCKED + 阻塞点明细），**不得**伪造成真实跑成功。
    status: PENDING
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_tools` + 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23（**在全部记录写入之后**）
      + 治理绿 + CI 台账**逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；
      **空集合 = 未取证**；自我指涉边界**明写并封闭**）+ 残余与未覆盖范围逐条。
      **★ 并含阶梯记账**：向宪章 `进展记录` 追加本行（**能力域 = 报告**），
      使阶梯的「报告」域 `依据 GOAL` 收录本 GOAL —— 这是
      `test_mainline_research_ladder_advances.py` 的核心不变式，**必须成立**。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PENDING
budget:
  max_cycles: 20
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
  - 未经 pin 的 provider / D 组通道 / 真实外发 —— 立即 BLOCKED
child_plans:
  - .cursor/plans/tasks/PLAN-20261014-464-goal-077-research-report-assembler-and-arc.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-465-goal-077-research-report-and-the-end-to-end-research-arc.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-219-every-round-must-advance-the-ladder-and-that-is-a-judged-convention.md
---

## 目标与退出标准

**一句话**：把「一次完整研究」跑到**有人类可读报告**为止 —— 报告域 **L0 → L1**。

**主线归属（宪章要求逐条声明）**：
- **轴** = **质量**（产出的可判定性）；
- **能力域** = **报告**（阶梯上那一行：当前级「仅结构化交付物」→ 下一级「人类可读研究报告」）；
- **同时推进**「检索」域的第一步（活检索产出**进报告**的逐条来源）；
- **间接推进**「计划」域的第一步（立题**由检索产出派生**，而非模型凭空写）。

**为什么这一条更近科研**（对照阶梯）：宪章读数显示序 35…44 **十个 GOAL** 的 `能力域`
全为 `—`（API 卫生）⇒ 阶梯十轮没动。本 GOAL 是**新规则下的第一轮**，且它直接补上
阶梯上最显眼的空格：**系统至今没有任何人类可读的研究报告**——会话交付物截断 500 字符、
`deliverable.json` 是 JSON、唯一的 markdown 写入者是沙箱脚本写进容器的中间产物。

**本 GOAL 不加新能力、不放宽任何判据。** 若新判据**证明**某处是真缺陷 ⇒ 在授权内修产品代码；
若某条**本机无法验证** ⇒ **登记为 PENDING** 并点名阻塞点，**不得**记 PASS。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **凭据纪律**：key 只在 `.env`；每一批提交前跑 `tools/credential_audit.py` 自证 `offenders=0`。
- **live 运行姿势**：`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` **逐命令传**，
  **不写进 `.env`**（否则污染默认门）。
- **降级梯（诚实登记）**：① 全 phase live；② 若模型侧不可用 ⇒ 会话面回退 Fake
  （**明确标注「非真实推理」**）但检索 / 实验 / 报告**仍真**；③ 仍不行 ⇒ 记 BLOCKED + 阻塞点，
  **不伪造**。

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

## 不进入循环 / 需人工拍板

- 序 44（`GOAL-20261014-076`）**已置 PAUSED**（用户指令）⇒ 本 GOAL **不**继续它；
- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 / `G24-5` / `R26-2/3/4/6` / destructive 能力改 allow —— **均不做**；
- 真实外发（邮件 / webhook / IM）—— 不做；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交与 PLAN-464 同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01 **PASS**（汇编器 + 7 例判据）；EC-02/03/04/05 PENDING | cycle 1 = EC-03（新协议 `research_report_chain_v1`：plan phase 由检索派生 + report phase 汇编） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | ACTIVE | **建档**：用户指令「每轮迭代必须更近科研」+ 要求端到端实验（报告即可）。**定位** = 阶梯「报告」域 L0 → L1。同时**序 44 置 PAUSED**（API 卫生，离科研最远）。EC-01（报告汇编器 + 判据）已在建档同轮落地并实跑 7 passed。中转站已切到新站（`discovery-api.intern-ai.org.cn` / `deepseek-v4-flash-vision`），真实 run 冒烟通过（`1 passed`，258s）。 |

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | 八 job 结论 |
| --- | --- | --- | --- |
| 换站 + 真实 run 冒烟 | `855aef5a` | 见回合报告 | 见回合报告 |
