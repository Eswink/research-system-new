---
id: GOAL-20261014-077
slug: research-report-and-the-end-to-end-research-arc
title: 端到端研究 + 人类可读研究报告（报告域 L0 → L1）
status: ACHIEVED
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
    status: PASS
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
    status: PASS
  - id: EC-04
    criterion: >-
      **真实中转站上跑通一次完整研究并留报告**：用**新站**（`discovery-api.intern-ai.org.cn` /
      `deepseek-v4-flash-vision`）+ 真实 runtime 跑完整协议到终态，报告落盘；
      run id / 报告 digest / §4 漂移事实（声明名 vs 返回名）记进本 GOAL 与回合报告。
    verify: >-
      live e2e 实跑（`requires_live_llm` + 显式开关）⇒ 终态 `SUCCEEDED` 且报告制品在位；
      **若模型侧不可用** ⇒ 按降级梯如实登记（② 会话面回退 Fake 但检索/实验/报告仍真；
      ③ 记 BLOCKED + 阻塞点明细），**不得**伪造成真实跑成功。
    status: PASS
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
    status: PASS
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
  - .cursor/plans/tasks/PLAN-20261014-466-goal-077-ec02-03-report-on-the-product-path.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-467-goal-077-ec02-03-report-on-the-product-path.md
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

## 残余与未覆盖范围（逐条明写）

**残余**（本轮**实测**到的、未做的）：

- `W-1` —— **本 GOAL 之外**：出厂会话工具绑定表只覆盖 canonical 读面，文献类会话工具
  （`literature.search` / `literature.read`）需要装配方另补一张实现表；这与
- `F-10`（产品组合根不自己接执行体缝）是同一家族的缺口。本轮以**判据侧装配方**身份
  补上（不改产品代码），**未**把它收进出厂形态。
- `W-2` —— 报告在 run **内**汇编 ⇒ 抬头是「**汇编时状态**」（那时 run 尚未到终态）；
  报告的读者要终态须另读 `GET /runs/{id}`。这是**如实边界**，不是缺陷。
- `W-3` —— 报告的来源标识同时含 PMID 与 DOI（工具结果里就有这两列）⇒ 同一篇文献可能
  以两个标识各出现一次；判据读的是「报告里的标识 ⊆ 证据读面里出现过的标识」。
- `W-4`…`W-6` —— 见 `RECHECK-20261014-468`（`R-M1` 未收口 / 只跑一次 run / 装配侧两表）。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**（M18 deferred）、**部署面验证**、
  **D 组审批通道**、`G24-5`、`R26-2/3/4/6` —— 均**不做**；
- 报告的**叙述性撰写**（模型写正文）—— 那是阶梯「报告」域的**再下一级**；
- **活检索结果进模型上下文** —— 那是阶梯「检索」域的**下一级**；本 GOAL 只保证
  「报告站在真检索上」（来源逐条入报告 + 覆盖两维判过）；
- 默认 runtime 改真（§11）—— 默认仍是 Fake（§11 的既定边界）；真实 run 由 live 判据
  在**显式开关下**跑。

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
| 1 | PLAN-20261014-466 | 见「CI 台账」（同一批提交） | e2e 7 passed（含 2 反证）；架构+工具面 1741 passed；应用/域/适配器/API 2739 passed；e2e/集成/合约 865 passed；架构 252 passed；m0 终态行 `PASS: profile=m0; 23 deterministic checks` | `d3a1d754`：M0 八 job 全 success + CodeQL 三 analysis 全 success | 6 次（见下） | EC-02 **PASS** / EC-03 **PASS**；**EC-04 / EC-05 仍 PENDING** | cycle 2 = EC-04（新站真实 run 跑完整协议 + 报告落盘） |
| 2 | PLAN-20261014-466（同一子 PLAN，续跑它的 EC-04 面） | `c0f793ad` | live 实跑 **1 passed in 151.89s**（新站、4 phase、报告落盘）；Ruff 零告警 | 见「cycle 2 台账」（轮询中） | 3 次（见下） | EC-04 **PASS**；**EC-05 仍 PENDING** | cycle 3 = EC-05（自举收口：验证器 + 两树 + m0 终态 + 治理 + 台账） |

### cycle 2 的修复记录（逐条如实）

1. **冻结被拒（实测抓到）**：只注册一件 REST provider 实例 ⇒ 另一件健康 `UNKNOWN` ⇒
   冻结门点名拒冻（判词逐字见 RECHECK-468）。补上第二件实例后冻结真发生。
2. **`KeyError: 'literature.search'`（我的代码写错**）：三元素元组
   `(工具名, provider_id, tool_id)` 被按 `(provider_id, _, _)` 解包 ⇒ 查表用错了键。
3. **`ToolDefinition 'literature…' is not registered`（实测抓到的装配缺口）**：出厂会话工具
   绑定表只覆盖 canonical 读面；本协议的文献会话工具由**装配方**补实现表（与 `W-1` 同类）。

### cycle 1 的修复记录（逐条如实）

1. **`report_task.py` 532 行 ⇒ 365 行**：初版把「读事实」与「准入」写在一个模块里 ⇒ 撞
   450 行硬上限。按全仓既有的「读面 vs 写面分列」把读面拆成 `report_facts.py`（240 行）。
2. **`phase_runner.py` 459 行 / `service.py` 453 行**：新增第三条执行体声明与它的装配关键字
   各让这两个文件越界 ⇒ 按既有先例（`experiment_task.py` 就是因 450 行被拆出来的）把
   **派发点**拆成 `task_dispatch.py`、把**装配**拆成 `runner_wiring.py`（均纯搬运、零语义变化）。
3. **报告抬头写「终态」**：报告在 run **内**汇编，那时 run 的终态**尚未产生** ⇒ 改标
   「**汇编时状态**」（把「汇编时的读数」冒充成「结论时刻的事实」是夸大）。
4. **指标来源与读面不一致**（实测抓到）：初版从「任何带 `metrics` 键的制品」取，而
   `GET /runs/{id}/experiments` 只读 `experiment_result.json` ⇒ 两处各读一份来源必然漂移。
   改为**同一份字节**（`RESULT_FILES` 后缀判），值按 JSON 逐字（`300.0` 不归一成 `300`）。
5. **e2e 长用例 71 行 ⇒ 拆成 3 个**（规模门的 50 行函数上限）。
6. **三份同源判据的字面量清单**：新协议声明了既有输入 id 与 run-chain / 绑定 ⇒
   登记进原判断（**扩面不是放宽**；谓词一条未改）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | ACTIVE | **建档**：用户指令「每轮迭代必须更近科研」+ 要求端到端实验（报告即可）。**定位** = 阶梯「报告」域 L0 → L1。同时**序 44 置 PAUSED**（API 卫生，离科研最远）。EC-01（报告汇编器 + 判据）已在建档同轮落地并实跑 7 passed。中转站已切到新站（`discovery-api.intern-ai.org.cn` / `deepseek-v4-flash-vision`），真实 run 冒烟通过（`1 passed`，258s）。 |
| 2026-10-14 | ACTIVE | **cycle 1 落地**（PLAN-466）：报告经**产品路径**产出（`report: {}` 声明 ⇒ 编排派发 ⇒ 汇编器读持久事实 ⇒ `{run_id}:research_report.md` 落 canonical，内联 `text/markdown`）；新协议 `research_report_chain_v1`（4 phase）跑通；立题格的两维覆盖判据在同一次实跑上判过（`3 >= 1 sources; 2 >= 1 retrieved`）。**EC-02 / EC-03 → PASS**（RECHECK-467 = PASS）。两条反证各自点名。**EC-04 / EC-05 仍 PENDING**（cycle 2 / cycle 3）。 |
| 2026-10-14 | ACTIVE | **cycle 2 落地**（EC-04）：**新站**（`discovery-api.intern-ai.org.cn` / `deepseek-v4-flash-vision`）上的**一次真实 run**（run `02c0adf5-b59c-4726-ac12-73f8d7ef4cc4`）跑完整 4 phase 链到 **`SUCCEEDED`**，报告落盘
`scratch/goal077-ec04-02c0adf5-b59c-4726-ac12-73f8d7ef4cc4.md`：含**活检索**取得的真标识（`42781891` / `10.12688/f1000research.180013.2` / `10.31234/osf.io/w7xpq_v2`）与真标题、**真容器**的 8 条实测指标、**真实评审**的逐字判词。**EC-04 → PASS**（RECHECK-468 = PASS）。装配侧补两处执行体（provider 实例 / 文献会话工具实现表），**不注入判词**，两处都有实测的失败形态。**EC-05 仍 PENDING**（cycle 3）。 |
| 2026-10-14 | **ACHIEVED** | **cycle 3 收口**（EC-05）：收口复检本树 **70 条判词全 PASS**；**两树复检 `TWO-TREE PASS`**（两树各 70 条、逐行相同、`sha256` 一致）；四向按压全红且逐字节复原；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；治理通过；凭据审计四面 `offenders=0`；**CI 台账逐提交**（tip `a99d8123` M0 八 job 全 success + CodeQL 三条 success；`c0f793ad` 的**真红**与其三处修复、`912d0667` 的**零 run** 与 `covered_by` 均如实登记）。**五 EC 全 PASS** ⇒ 阶梯「报告」域 **L0.5 → L1**。 |

## CI 台账

（逐 run 逐 job；`cancelled` 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| cycle 1（报告经产品路径 + 协议 + 判据） | `d3a1d754` | [M0 38583663672](https://github.com/Eswink/research-system-new/actions/runs/38583663672) / [Push 38583663565](https://github.com/Eswink/research-system-new/actions/runs/38583663565) | **M0 八 job 全 `success`**（container-quality / collector-quality / eval-gate / quality-ubuntu / quality-windows / console-frontend / observability-overhead × 2）+ Push-on-main 三条 CodeQL（python / actions / javascript-typescript）全 `success`；两 run 均 `run_attempt=1`，**零 cancelled、零重跑** |
| cycle 2（EC-04 live 判据） | `c0f793ad` | [M0 38586633161](https://github.com/Eswink/research-system-new/actions/runs/38586633161) / [Push 38586633747](https://github.com/Eswink/research-system-new/actions/runs/38586633747) | 🔴 **`M0` 真红**：`quality-ubuntu-latest` = `failure`、`quality-windows-latest` = `failure`（其余六 job success；Push 三条 CodeQL 全 success）。**分类 = 产品测试失败 / typecheck，三处都在判据文件自身**（与产品代码无关）：① `python/typecheck` —— live 判据里 `deps.artifacts` / `deps.runs` 是可选类型而未收窄；② `test_live_switch_is_single_source` 的两条**显式清单**未登记新 live 模块；③ `_live_deps` 58 行超 50 行函数门。**处置** = 同轮修复（提交 `912d0667`），逐条判词见 `RECHECK-468` 的 `W-7` |
| cycle 2 修复（判据自身三处） | `912d0667` | **无 CI run（如实登记）** | 该提交**没有** CI run：它在 `c0f793ad` 的 run 仍在飞时被推送，随后 `a99d8123` 又在**约 2 分钟内**推送 ⇒ `head_sha` 查询实测 `total_count=0`（快速连续推送下这一条从未成为 tip）。**`covered_by = a99d8123`**：该提交的全部改动都**包含在** tip 里（tip = 它 + 仅两个判词归档文件）⇒ 由 tip 的 run 覆盖。**不是**跳过取证：这是 `MEM: m0-ci-concurrency-batch-push` 记录的同一形态（一个 cycle 攒成一次推送）；本轮**没攒**，因此把这条如实登记为**零 run** 而不是记绿 |
| cycle 3（EC-05 收口资产 + 两树判词归档） | `a99d8123`（**tip**） | [M0 38594072553](https://github.com/Eswink/research-system-new/actions/runs/38594072553) / [Push 38594071618](https://github.com/Eswink/research-system-new/actions/runs/38594071618) | **M0 八 job 全 `success`**（observability-overhead × 2 / eval-gate / quality-windows / quality-ubuntu / collector-quality / console-frontend / container-quality）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |
| cycle 3 收口（GOAL ACHIEVED + 台账回填） | `8cbfcc6e`（**最终 tip**） | [M0 38601739870](https://github.com/Eswink/research-system-new/actions/runs/38601739870) / [Push 38601739564](https://github.com/Eswink/research-system-new/actions/runs/38601739564) | **M0 八 job 全 `success`**（collector-quality / observability-overhead × 2 / console-frontend / container-quality / eval-gate / quality-ubuntu / quality-windows）+ Push-on-main 三条 CodeQL 全 `success`；`run_attempt=1`、**零 cancelled** |

### cycle 2 台账（`c0f793ad`）

| 项 | 读数 |
| --- | --- |
| live 实跑 | **1 passed in 151.89s**（`tests/e2e/test_research_report_chain_live.py`） |
| run id | `02c0adf5-b59c-4726-ac12-73f8d7ef4cc4` |
| 协议 / 终态 | `research_report_chain_v1_0_0` / **`SUCCEEDED`**（`manifest_digest` 在场） |
| 报告制品 | `{run_id}:research_report.md`（`GET /artifacts/{id}/content` ⇒ 200 + `text/markdown`） |
| 报告落盘 | `scratch/goal077-ec04-02c0adf5-b59c-4726-ac12-73f8d7ef4cc4.md`（2341 字节） |
| 活检索真标识 | `42781891` / `10.12688/f1000research.180013.2` / `10.31234/osf.io/w7xpq_v2`（各带真标题） |
| 真容器指标 | 8 条（`agreement=true`、`comparison_reduction_ratio=7990.0`、`pairwise_comparisons=319600` …） |
| §4 漂移事实 | 声明名 `deepseek-v4-flash-vision` ≠ 返回名 `dsv4-flash-vision`（既有登记，本 run 同站同模型） |
| CI run | 见上表 `c0f793ad` 行（真红 + 处置）与 `a99d8123` 行（全绿） |

### cycle 3 台账（EC-05 收口，tip `a99d8123`）

| 项 | 读数 |
| --- | --- |
| 收口复检（本树） | `tools/verify_goal077_closeout.py --root . --verdict-only` ⇒ **70 条判词全 PASS** |
| 两树复检 | `tools/two_tree_recheck.py --script tools/verify_goal077_closeout.py --root . --base-ref HEAD --script-mode shared` ⇒ `TREE current exit=0 verdicts=70` / `TREE clean exit=0 verdicts=70` / `COMPARE identical=True` / **`TWO-TREE PASS`**，两树 `sha256=da5adf2aadf864290306db4101de77bf174d278a842e597ddab818fdc6f6cfbe`（**一致**） |
| 判词归档 | `.cursor/plans/goals/evidence/GOAL-20261014-077-verdict-current.txt` / `…-verdict-clean.txt`（各 2918 字节、`CR=0`、**逐行相同**） |
| 四向按压 | `.cursor/plans/goals/evidence/GOAL-20261014-077-press-two-way.txt`：`BASELINE 未按压全绿=True` + `V7-1…V7-4` 逐条 `按压 RED=True` + `sha 复原一致=True` + `all_red_and_restored=True`（`CR=0`） |
| m0 终态行 | **`PASS: profile=m0; 23 deterministic checks`**（本机、仓库 `.venv`、`uv run --frozen --no-sync python -B`、独占） |
| 治理 | `validate.py` ⇒ `Cursor 治理验证通过` |
| 凭据审计 | `tools/credential_audit.py` ⇒ 四面 `offenders=0`（tracked / records / config_db / logs） |
