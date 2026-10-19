---
id: GOAL-20261019-089
slug: direction-drives-question-drives-retrieval
title: 方向驱动问题、问题驱动检索、检索结果驱动下一轮（北极星三断点闭合）
status: ACHIEVED
created_at: 2026-10-19
updated_at: 2026-10-19
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-19 的北极星指令逐字：「用户只给一个**研究方向**，剩下的全部自动化 ——
    自动选题、自动设计实验、自动撰写、并**自我迭代**到下一个问题。」并**实测**指出三处断点：
    (1) **方向没有载体** —— `packages/domain/projects.py` 的 `ProjectDefinition` 只有
    `id` / `name` / `status`，用户无处表达「我要研究什么」；
    (2) **选题不由系统产生** —— 检索词来自 `examples/inputs/real-research-brief-v1.json` 的
    `retrieval.query`（经 `arguments_from_input` 读入），`research_plan` 产物在 run-chain
    侧从未被读过，且 run-chain 在会话之前执行 ⇒ 同一 phase 内做不到「先想问题再检索」，
    必须用跨相输入；
    (3) **迭代不自动** —— `ResearchProgram` 域与 `advance_program` 齐备，但只由
    `POST /programs/{id}/advance` 手动触发，`ScheduleJob` 词表里没有 program 推进作业。
    授权要点：(a) 全部决策权下放；只有「改产品边界 / 放宽任何判据 / 动冻结面」才登记
    BLOCKED 并停下。(b) 每一步必须有**机械判据**，不许只写散文。(c) 每轮必须让科研能力
    阶梯前进（`tests/tooling/test_mainline_research_ladder_advances.py` 强制）。
    (d) **不做**：默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA /
    D 组审批通道 / 部署面验证 / `R-M1` / destructive 能力改 allow / 为凑数扩承接面 /
    宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）。
    (e) push-to-main-for-CI（只推 `main`、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线（`RESEARCHOS_AGENT_RUNTIME` /
    `RESEARCHOS_LIVE_E2E` **不进 `.env`**）。
objective: >
    让「用户只给一句话方向」成为一条**机械可判的链**：方向落在 canonical（项目的新字段，
    不是 `name`）→ 上游会话**据方向提出研究问题**（`research_question`）→ 下游 run-chain
    检索**从该问题的 query 取词**（改问题 ⇒ 改检索词；摘掉上游 ⇒ 编译期点名失败）→
    相同的推进装配被**周期作业**自动调用（与手动端点同一条链，不建第二套）使程序在第 N 轮
    终态后无需人工进入第 N+1 轮（声明了闸门则停在闸门且理由可读）→ 在新中转站 + 真实 runtime
    上**真跑一次**并逐条记下 run id / 问题正文 / 检索词 / 真实标识 / 报告 digest。
exit_criteria:
  - id: EC-01
    criterion: >-
      **方向 → 问题 → 检索**：新协议 phase A 是会话（读方向、写出 `research_question` JSON），
      phase B 声明 `inputs: [A:research_question]` 且 `capability_execution: run_chain`，
      检索 query 由 `arguments_from_input: ["research_question.query"]` 取。
      **双向判据**：(i) 改 A 的产出 ⇒ B 实际发给 provider 的 query **随之改变**（同一 run
      内两个变体，逐字比对 provider 收到的参数）；(ii) 把 A 从协议里摘掉 ⇒ **编译期**点名
      失败（`CROSS_PHASE_INPUT_INVALID`，不是运行期静默用默认值）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_run_chain_reads_cross_phase_material.py -q`
      ⇒ 全绿；判据覆盖：材料来自上游 / 换产出换 query / 摘上游编译期红 / 无声明零回归。
    status: PASS
  - id: EC-02
    criterion: >-
      **方向进 canonical**：`ProjectDefinition` 新增**可选** `direction` 字段（缺省 `None`
      ⇒ 既有行逐字不变），sqlite 编码往返 + PG 迁移（非破坏性）同轮；写面
      `POST /projects` / `PATCH /projects/{id}` 可设/清，读面 `GET /projects` 与
      `GET /projects/{id}` 披露；OpenAPI 快照 + `apps/web/src/api/types.ts` +
      隐私清单（`tests/observability/read_face_route_registry.py`）三处**同轮**同步。
      **不得**把方向塞进 `name`（那是改名语义，`renamed()` 的判据仍逐字成立）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api/test_project_direction.py tests/observability/test_privacy_read_face_canary.py -q`
      ⇒ 全绿；外加 `tests/contracts/test_openapi_snapshot.py` 与 web `tsc --noEmit`。
    status: PASS
  - id: EC-03
    criterion: >-
      **迭代自动起来**：`ScheduleJob` 新增 `program_advance`（受控词表 + 内置定义 +
      `JOB_PURPOSE`），执行体**调用与 `POST /programs/{id}/advance` 同一条装配链**
      （同一个 `advance_program` 调用点与同一组 Port/resolver，不建第二套）。
      判据：程序在第 N 轮终态后**无需人工**进入第 N+1 轮（作业 pass 一次 ⇒ `run_count`
      增一、决策种类 `CONTINUE`、新 run 落库且 `program_index = N+1`）；声明了闸门 ⇒
      停下且理由可读（既有三种闸门语义**不动**：`WAIT_FOR_APPROVAL` / 判词条件式 / 多点）；
      无 program store 时不假装有执行体（`executor_attached=False`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/ops/test_program_advance_job.py tests/api/test_ops_schedules_api.py -q`
      ⇒ 全绿；`ScheduleJob` 词表读数含 `program_advance`。
    status: PASS
  - id: EC-04
    criterion: >-
      **真跑一次**：新中转站 + 真实 runtime（`RESEARCHOS_AGENT_RUNTIME=openhands`、
      `RESEARCHOS_LIVE_E2E=1` 逐命令传），方向只给**一句话**，运行新协议并记录：
      run id、模型**自己提出**的问题正文、检索词、命中的真实标识（PMID/DOI）、
      报告 digest —— 逐条写进本 GOAL 的「真跑读数」小节。模型侧不可用 ⇒ 记 PENDING 且
      点名阻塞点（**不伪造**）。
    verify: >-
      `tests/e2e/test_direction_to_question_to_retrieval_live.py` 在 live 开关下
      `passed`；读数落盘于 `.cursor/plans/goals/evidence/GOAL-20261019-089-live-run.txt`。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口**：验证器进树（复用 `tools/closeout_recheck_assertions` 标准断言集）+
      两树复检（判词归档**进树**、二进制写盘、CR=0）+ as-is m0 23/23（**在全部记录写入
      之后**、**静止工作树**）+ 治理绿 + 凭据审计 `offenders=0` + CI 台账**逐提交**
      （`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`）+ 残余与未覆盖范围逐条。
      **★ 并含阶梯记账（两个面）**：阶梯「检索」与「迭代」行的 `依据 GOAL` **与**宪章
      `进展记录` 各收录本 GOAL。
    verify: >-
      验证器本树 `--verdict-only` 全 PASS；`tools/two_tree_recheck.py` 两树判词逐行相同 +
      `sha256` 相同；m0 终态行 `PASS: profile=m0; 23 deterministic checks`；
      `validate.py` = `Cursor 治理验证通过`；台账逐 run 逐 job（含 `run_attempt`）。
    status: PASS
budget:
  max_cycles: 16
  per_cycle_minutes: 150
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
      **把方向塞进 `name`**：`ProjectDefinition.renamed()` 是改名语义；方向必须是
      自己的字段（塞进 name 会让「改名」与「改方向」不可区分）
    - >-
      **静默回落**：上游问题读不到 / query 缺失 / 无程序推进面，必须**点名**；
      回落到 `retrieval.query` 的缺省值、回落到上一轮问题、或「取最后一条」都算越界
    - >-
      **另建第二套推进链**：作业必须调用与 `POST /programs/{id}/advance` **同一个**
      `advance_program` 装配（第二套 = 第二套语义）
    - >-
      **改既有三种闸门语义**（`WAIT_FOR_APPROVAL` / 判词条件式 / 多点 / 混合式）：
      本轮只让推进**自动被调用**，不新增/改动闸门判定
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
    **需要新增 `TrustLabel` 取值或改其语义**（那会改 Canonical 的信任面）—— 停下登记
  - >-
    **需要给 `ProjectDefinition` 加必填字段**（会让既有行不可读 = 破坏性迁移）——
      只允许可选字段 + 缺省 `None`；否则 BLOCKED
child_plans:
  - .cursor/plans/tasks/PLAN-20261019-089-goal-089-ec01-05-direction-drives-question.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261019-089-goal-089-direction-drives-question-drives-retrieval.md
memory_entries: []
---

## 目标与退出标准

**一句话**：把「用户给一句话方向」接到「系统自己提出问题、自己检索、自己写、自己进入
下一轮」这条链上，并且每一步都有**机械判据**。

**主线归属（宪章要求逐条声明）**：

- **轴** = **深度**（研究能多轮推进且有停止规则：轮数由结论驱动）+ **质量**（产出的
  可判定性：检索词由系统自己提的问题决定，而不是由操作者预填的简报决定）；
- **能力域** = **检索**（阶梯逐字：`检索改变下一轮问题`）与 **迭代**（阶梯逐字：
  `迭代改变下一轮问题`）。

## 为什么这一条更近科研（**建档实测**，逐条带读数）

用户本轮给出三处断点，本 GOAL 的全部设计都从它们出发（**不重新推导**，逐条复核到位）：

1. **方向没有载体**：`packages/domain/projects.py` 的 `ProjectDefinition` 字段逐个读出
   ——`id` / `name` / `status` / `created_at` / `updated_at`，**没有**任何方向位。
   `services/api/dto/projects.py` 的 `ProjectCreateDto` 只有 `name`；
   `ProjectUpdateDto` 只有 `name` / `status`。⇒ 用户只能选一个名字，不能表达「研究什么」。
2. **选题不由系统产生**：`tests/e2e/live_run_support.py:340` 的 `arguments_from_input=("retrieval.query",)`
   是产品面上 query 的**唯一来源**，而那个路径来自 `examples/inputs/real-research-brief-v1.json`
   （`services/api/demo.py` 的 `DECLARED_INPUTS` 把它种进 ArtifactStore）。
   `research_plan` 在 `packages/` 的 run-chain 侧**零消费**。
   **更硬的一条（本轮实测发现）**：`phase_capabilities._input_material` 只扫
   `spec.declared_input_artifacts`（**本地**声明输入）—— 跨相输入
   （`CompiledPhase.cross_phase_inputs`）**不进**参数材料，只进证据链
   （`cross_phase_evidence` 只 `register` 证据）。⇒ 即便协议写了
   `inputs: [A:research_question]`，今天 B 的 run-chain 调用**读不到** A 的产出。
   这就是 EC-01 必须打开的那道缝。
3. **迭代不自动**：`packages/domain/schedules.py` 的 `ScheduleJob` 值逐个读出 ——
   `lease_recovery` / `outbox_relay` / `retention` / `worker_reaper` / `retry_dispatch`，
   **没有** program 推进作业；`advance_program` 的唯一产品调用点是
   `services/api/routers/programs.py:295`（`POST /programs/{id}/advance`）。

⇒ 三条断点合起来就是一句话：系统的「研究什么」完全由**操作者预填的简报**决定，并且必须
由**人**推动下一轮。本 GOAL 把这条链接上。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**：项目方向字段（可选、缺省 None）、跨相材料 → run-chain 参数的第二条读取
  入口、一个调度作业、一份新协议、一组判据；
- **不改**：`advance_program` 的判定语义、三种闸门语义、`ResearchRun` 状态机、
  `TrustLabel` 取值、`ProjectDefinition.renamed()` 的改名语义；
- **不静默回落**：上游问题读不到 / query 缺失 / 无推进面必须点名；
- **真跑**：EC-04 必须在**新中转站 + 真实 runtime** 上跑，读数逐条落盘。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **判据先行**：每条 EC 的判据必须在**实现之前**写出可观测差异（改动前后读数不同）；
- **双向按压**：EC-01 必须有两个方向（换产出 ⇒ 换 query；摘上游 ⇒ 编译期红），
  单方向不足以证明「query 真的来自 A」；
- **零回归纪律**：未声明跨相材料的协议，其 run-chain 参数面**逐字不变**；
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
- `W-2` —— **不判「问题提得好不好」**：本 GOAL 判的是「检索词来自问题」，不判问题的
  科学价值（那需要人评或评审面，属后续）。
- `W-3` —— **程序推进作业只做「调用既有推进」**：不新增闸门语义、不做跨进程仲裁
  （多实例同时推进的互斥仍依赖既有 `DEDUP` 决策与 run 面去重）。
- `W-4` —— **方向字段的读面是「配置面」**：不做检索、不做语义解析、不驱动模型；
  「方向 → 问题」的语义转换在会话里（由模型完成）。
- `W-5` —— **真实 run 的模型质量不受判**：真跑证明的是链跑通且读数可核，不证明
  提出的问题达到了人类研究者的水平。
- `W-6` —— **`producer_trust_label` 的推导过宽（本轮实测发现，未修）**：
  `question` 格必须声明 `capability_execution: run_chain` 才能把文献 provider 排除出
  它的**会话工具面**（生产装配的注册表只有 `m12_artifact` / `openhands_workspace`，
  不做这个排除 ⇒ 会话面含 `literature.*` 而无实现 ⇒ SDK 点名
  `ToolDefinition 'europe_pmc' is not registered`，本轮实测）。而
  `producer_trust_label`（`packages/application/protocol_compile/cross_phase_inputs.py:201`）
  只看「声明了 run_chain + 能力面落在带 `network_domains` 的 provider 上」⇒ 把**模型写的**
  `research_question` 标成 `RETRIEVED`。后果：检索格的 `EVIDENCE_COVERAGE`
  性质维可被**这条跨相边单独满足**，模型即使不检索也能过门。

  **为什么本轮不修**：改它等于改 `TrustLabel` 的推导语义（本 GOAL 的
  `escalation_triggers` 明写「需要新增 `TrustLabel` 取值或改其语义 ⇒ 停下登记」），
  而既有判据 `tests/application/run_orchestration/test_cross_phase_inputs.py::test_b_*`
  正把这个推导**连同按压**钉住 —— 那是上一轮（`GOAL-20261016-081 EC-04`）的受判面。

  **补偿判据（本轮在位的，不依赖那个标签）**：
  `tests/e2e/test_direction_to_question_to_retrieval.py`（受控执行体）与
  `tests/e2e/test_direction_to_question_to_retrieval_live.py`（真实 run）都从
  **provider 收到的请求参数**逐字取证「检索词 == 模型写下的 query」，并且都要求
  检索命中真实标识 —— 「检索真的发生了」因此仍可机械判定。

  **下一步（需拍板）**：让 `producer_trust_label` 区分「该 phase 真的执行了
  run-chain 调用」与「只是用 run_chain 排除会话工具面」——两种修法都动既有语义
  （新增声明字段 / 改推导），须先由用户拍板。

**未覆盖范围**（逐条明写；本 GOAL **不声称**已解决）：

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均**不做**；
- 默认 runtime 改真（§11）—— 默认仍是 Fake；
- `R-M1` 未收口 ⇒ **不得**宣称项目安全；投递语义**不是**「恰好一次」（**明确否认**）。

## 不进入循环 / 需人工拍板

- 默认 runtime 改真（§11）/ 读面认证 / 多租户·RBAC·BOLA·BFLA / D 组审批通道 /
  部署面验证 —— **均不做**；
- **给 `ProjectDefinition` 加必填字段 / 破坏性迁移 / 改 `TrustLabel`** —— 需人工拍板。

## 真跑读数（EC-04）

**真跑过一次**（2026-10-19，新中转站 `discovery-api.intern-ai.org.cn` + 真实 runtime
`openhands`，方向只给一句话）。证据文件：
[`evidence/GOAL-20261019-089-live-run.txt`](evidence/GOAL-20261019-089-live-run.txt)。

| 项 | 读数 |
| --- | --- |
| run id | `07f339e2-2845-4df0-bb3b-4d9fa3146a04` |
| protocol | `direction_to_question_v1_0_0` |
| 终态 | `SUCCEEDED` |
| 一句话方向（输入） | `retrieval augmentation for scientific hypothesis generation` |
| 模型自己提出的问题 | 「To what extent does retrieval augmentation — grounding a language model in relevant scientific literature and structured knowledge retrieved at inference time — improve the novelty and validity of hypotheses generated for scientific discovery, and what remains unmeasured by current evaluations?」（`research_question` 制品 `sha256:e3b56a66…`，题块全文见证据文件） |
| 检索词（来自问题块） | `retrieval-augmented generation scientific hypothesis discovery` |
| 发给 provider 的参数制品 | `tool-args:360d2038-1b93-4dcd-8813-922e34ed4276:literature_search`（`sha256:94ccaaf0…`） |
| 命中的真实标识 | `41408154`, `41743026`, `42160738`（`literature_read` 的 `source_ref` 末段） |
| 检索步证据 digest | `sha256:f93236f8d5b5d654fd67a0354fa65e99856b1e537ad39588046dc0b170493493` |
| 读取步证据 digest | `sha256:269960f97cae6af58b21d8dc615e957926f18a01cc13e2999b582903bea578dc` |
| 检索报告 digest | `sha256:c736c6a2a323531901a423c22037d477880571a19ba4578edf50084f43349493` |

**判据边界**：这份读数证明「发给 provider 的检索词**逐字等于**模型自己写下、并落库为
`research_question` 的 `query`」这一条机械事实；它**不**判问题提得好不好（`W-2`），
也不声称报告叙述质量。

**本轮实测到的两个真缺陷（已修，不是判据放宽）**：

1. **参数取证面选错了**（`W-3` 的正面）：`tool-args:` 制品**不挂 claim relation** ⇒
   不出现在 `GET /runs/{id}/artifacts`；而运行链步在 `engine.submit` **之前**执行 ⇒
   检索零命中时那条 run 是 `FAILED` 且**没有任务行** ⇒ 按 `task_identities` 取会空手
   而归。判据改为**制品面枚举**（`list_refs` 的 `classification` + id 后缀）。
2. **问题契约对 query 形态的约束不足**：模型给出的 8–9 词 query 在 PubMed 上 AND 连接
   后返回 `count: 0`（`literature_read` 因此无 id 可读，run `FAILED`）。契约正文补上
   「三到六个高信号词、不加同义词/限定词、超长 query 常零命中」的规则 ——
   **改的是提示词，不是判据**；覆盖门（`EVIDENCE_COVERAGE`）保留零命中即红。

**收口补齐（2026-10-20）**：`2dc324d8` 的 M0 run `39324938465` 已到终态 **success**（8/8 job）；既有判据改动的 `numstat` + 谓词比对逐条写进 RECHECK；本记录之后的最后一轮全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`、`PASS [` **24 行**、`FAILED` **0 行**。

**两树复检**（`tools/two_tree_recheck.py`）：本树与干净 checkout 判词**逐行相同**、
`sha256` 相同（`67894073…55ab`，89 条）；归档在
`evidence/GOAL-20261019-089-verdict-current.txt` / `-verdict-clean.txt`。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 建档提交同批推送 | 见「状态历史」 | 见「CI 台账」 | — | EC-01…EC-05 待达成 | cycle 1 = EC-01 |
| 1 | PLAN-20261019-089 | `99f9a642`…`dc5646fe` | m0 **23/23**（24 行 `PASS [`、0 FAILED）；两树 **89 条**判词 `sha256` 相同；治理 `Cursor 治理验证通过`；凭据四面 `offenders=0` | `dc5646fe` ⇒ M0 **8/8 success** | 上述「真跑读数」小节里的两条真缺陷 + 三处清单登记 | **EC-01…EC-05 全达成** | 战役层下一步（`W-6` 需拍板） |

## CI 台账

（逐 run 逐 job；`cancelled` / **零 run** 如实登记 + 原因 + `covered_by`；**空集合 = 未取证**。）

| 推送 | 提交 | run | job 结论 |
| --- | --- | --- | --- |
| 批 1（一次推送：`3f763fd5..dc5646fe`） | `99f9a642` | **零 run** | `covered_by=39312496694`（同一批推送里 GitHub 只为分支最新提交创建 workflow run；该提交的时代码由那次 M0 全量门覆盖） |
| 批 1 | `c806691f` | **零 run** | `covered_by=39312496694`（同上） |
| 批 1 | `dbec2c38` | **零 run** | `covered_by=39312496694`（同上） |
| 批 1 | `493020b8` | **零 run** | `covered_by=39312496694`（同上） |
| 批 1 | `d91daec0` | **零 run** | `covered_by=39312496694`（同上） |
| 批 1 | `dc5646fe` | **39312496694** / **39312495592** | `M0 Quality Gates` **success**（attempt 1）：`container-quality`、`console-frontend`、`observability-overhead-windows-latest`、`quality-windows-latest`、`quality-ubuntu-latest`、`observability-overhead-ubuntu-latest`、`collector-quality`、`eval-gate` **8/8 success**；`Push on main` success |
| 批 2（一次推送：`dc5646fe..43ca33dc`） | `43ca33dc` | **39318206267** / **39318207666** | `M0 Quality Gates` **success**（attempt 1）：8/8 job success（`container-quality` / `console-frontend` / `observability-overhead-windows-latest` / `quality-windows-latest` / `quality-ubuntu-latest` / `observability-overhead-ubuntu-latest` / `collector-quality` / `eval-gate`）；`Push on main` success |
| 批 3（一次推送：`43ca33dc..0645bd08`） | `0645bd08` | **39321868670** / **39321870140** | `M0 Quality Gates` **success**（attempt 1）：8/8 job success；`Push on main` success。本行是**自指边界**：该提交只改记录（台账批 2），它自己那次 run 的结论写入时已经跑完，但**写下**这个结论这个动作本身没有经过任何门 —— 如实登记，不假装闭合。 |
| 批 4（一次推送：`0645bd08..2dc324d8`） | `2dc324d8` | **39324938465** / **39324938696** | `M0 Quality Gates` **success**（attempt 1）：`console-frontend`、`collector-quality`、`quality-windows-latest`、`eval-gate`、`quality-ubuntu-latest`、`observability-overhead-ubuntu-latest`、`observability-overhead-windows-latest`、`container-quality` **8/8 success**；`Push on main` success。**自指边界**：本行与后续「收口补齐」的台账写入提交，其自身那次 run 的结论由**下一提交**记录；链条在「最后一个台账提交」处停止 —— 那里如实写明边界，不假装闭合。 |
| 收口补齐（一次推送：`2dc324d8..` 本文件所在提交） | **本文件所在提交**（结构性指称，不写死 hash） | **未轮询（自指边界）** | 该提交只改记录（`2dc324d8` 的 CI 到终态 + `numstat` 申报 + 最后一轮 m0 读数），**它自己那次 run 的结论不外推**：台账在「读过它」之前就结束 —— 这是显式边界，不是遗漏。**指称不写死 hash**：写死会让「改 hash」本身又产生一个提交（自指环）。此前每个提交都有 run 结论或 `covered_by`；本地最终 m0 终态行为 `PASS: profile=m0; 23 deterministic checks`（24 行 `PASS [`、0 FAILED）。 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-19 | **ACTIVE** | **建档**：承用户北极星指令的三处断点（方向无载体 / 选题不由系统产生 / 迭代不自动）。**建档实测第四条**（本轮新发现）：`phase_capabilities._input_material` 只扫本地声明输入，**跨相输入不进 run-chain 参数材料** ⇒ 即协议写了 `inputs: [A:research_question]` 也读不到，这是 EC-01 必须打开的缝。程序表序 57 ⇒ 预算 57/60。 |
| 2026-10-19 | **ACHIEVED** | 五 EC 全 PASS；真跑 `SUCCEEDED`（3 条真实 PMID）；两树 89 条判词 `sha256` 相同；CI M0 8/8 success；残余 `W-6` 如实登记。 |
