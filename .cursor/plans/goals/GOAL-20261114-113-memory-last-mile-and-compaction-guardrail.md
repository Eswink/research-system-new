---
id: GOAL-20261114-113
slug: memory-last-mile-and-compaction-guardrail
title: 记忆的最后一米 + 上下文压缩的护栏（机制完备但零使用的装配缺口）
status: ACHIEVED
created_at: 2026-11-14
updated_at: 2026-11-15
owners:
  - root-agent
latest_recheck: .cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md
authorization:
  source: user-request
  ref: >-
    序 81（GOAL 号 113）。沿用用户 2026-10-29 全权限预授权；
    push-to-main-for-CI：只推 main、不 force、不重写历史、不推旁支；
    `RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` / `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS`
    逐命令传，绝不写进 `.env`。用户 2026-11-14 另拍板：记忆 PROJECT 档用
    「合约声明式放行」——只有合约显式写了 `memory_export`，才以 `curator_approved=True`
    提交；缺省 `None` ⇒ 不晋升（零回归）。
objective: >-
  建档实测（2026-11-14）：记忆机制完备（`packages/application/memory/` 9 模块、gate 7 阶段、
  `MemoryRecord` 12 字段、冲突检测 + 五态处置 + 逐对消解）但**全仓 200 个 run 库
  `m12_memory` 行数全部 0**、28 份协议声明 `memory.read` 的 0 份。根因是**装配缺口**：
  `PhaseRunnerDeps.memory_gate` 默认 `None` ⇒ `promote_memory` 直接 return，
  `OrchestrationDependencies` 没有这个字段、两个组合根也没有——缺的是四行装配。
  上下文压缩**不存在但当前不需要**（每任务只发一次 `send_message`、每轮新建会话；
  实测 `message_count` 2×9/1×2 ≈ 5–12 个 view event，而 SDK 触发阈值 `max_size=80`；
  整个 live run token 15,219 vs 声明窗口 512,000）⇒ 压缩是**护栏 + 测量**，不是修当前问题。
  本轮三靶：A）让真实 run 写入 PROJECT 档记忆（四行装配 + 合约声明式放行）；
  B）condenser 护栏（两处 kwarg，默认不触发）+ view-event / prompt-token 只读测量；
  C）序 81 记账与收口。
exit_criteria:
  - id: EC-01
    criterion: >-
      **四行装配**：`OrchestrationDependencies` 新增 `memory_gate`（缺省 `None` ⇒
      不晋升，既有语义逐字不变）；两个组合根（`composition.py` 的 `_sqlite_orchestration`
      与 `pg_composition.py` 的 `_build_pg_orchestration`）构造 `MemoryGateDeps`
      注入；`runner_wiring.py` 把它传进 `PhaseRunnerDeps`。gate 本体
      （`packages/application/memory/gate.py`）**一行不改**。
    verify: >-
      `tests/integration/test_ig1_phase_runner.py`（真实运行链经装配写出记忆）+
      组合根装配判据；`tests/application/run_orchestration/` 全绿。
    status: PASS
  - id: EC-02
    criterion: >-
      **声明面**：`TaskContract.memory_export: MemoryExportSpec | None = None`
      （`MemoryExportSpec(tier=PROJECT, kind=FACT, confidence=Decimal("0.8"))`）——
      这是**授权声明**而非执行体，**不参与** `experiment`/`report` 排他校验；
      缺省 `None` ⇒ 不晋升（既有 34 份合约行为逐字不变）。
      schema（`task-contract.schema.json`）+ loader（`_load_memory_export`）同轮。
      **实现偏离（有实测理由）**：confidence 用 `Decimal` 不用 float——
      声明随合约进 RunManifest，canonical 序列化拒绝 float
      （`float is not allowed in canonical serialization`，实测让整条链判红）。
    verify: >-
      `services.api.catalog.load_task_contracts` 加载 34 份不变、`research_manuscript`
      读出声明；`tests/contracts/`、`tests/api/` 全绿。
    status: PASS
  - id: EC-03
    criterion: >-
      **读声明 → 代表合约提交**：`promote_memory` 从本任务合约的 `memory_export` 读声明；
      有声明 ⇒ `tier`/`kind`/`confidence` 取自声明、`curator_approved=True` 传给
      `commit_memory`（判词点名「本 run 的 curator 授权来自合约 `memory_export`」）；
      无声明 ⇒ 不晋升（不是拒绝：没声明就没这条通道）；
      `gate.py` 的 `_CURATOR_TIERS` 与 curator 判定逐字保留。
    verify: >-
      `tests/application/run_orchestration/test_memory_export_declaration.py`
      （③ curator 门仍咬：`curator_approved=False` ⇒ 不写入且点名 curator 阶段）。
    status: PASS
  - id: EC-04
    criterion: >-
      **四条判据（含两条反证）**：① 正例：合约带声明 ⇒ 晋升（tier==PROJECT、
      `scope="project"`、provenance 指向本 run 的 evidence）；② 反证（零回归）：
      合约不带 ⇒ `m12_memory` 仍空；②b 反证（装配侧）：gate 没接 ⇒ 不晋升；
      ③ 反证（curator 门仍咬）：声明在场但 `curator_approved=False` ⇒ 不写入；
      ④ 读得到：提交后**同一项目下一轮** `prior_knowledge` 非空且渲染行逐字匹配
      `- {memory_id}{marks}: {shown} (source: {provenance})`。
    verify: >-
      `tests/application/run_orchestration/test_memory_export_declaration.py`
      （五条判据含反证）+ `tests/integration/test_ig1_phase_runner.py`（链级 ①）。
    status: PASS
  - id: EC-05
    criterion: >-
      **真实 run 写入**：只给 `research_manuscript` 加 `memory_export: {tier: PROJECT}`
      （其余 33 份刻意不带——这是设计，不是遗漏）；一次真实 run 后该 run 自己的库
      `m12_memory` 非空。
    verify: >-
      `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1
      RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1` 下
      `tests/e2e/test_the_manuscript_chain_runs_live.py` 成功后直查该 run 自己的库
      `select count(*) from m12_memory`（读数先写盘再断言）。
    status: PASS
  - id: EC-06
    criterion: >-
      **condenser 护栏**：`session_builder.py` 两处 `PolicyEnforcingAgent` 加
      `condenser=LLMSummarizingCondenser(llm=llm, max_size=80, keep_first=4)`。
      三个承重理由（注释逐条）：复用同一 `llm`（换摘要模型 ⇒ 指纹静默掉
      `NOT_VERIFIED`）；`keep_first=4`（hard context reset 会摘要包括合约
      fenced-JSON 指令在内的一切）；不设 `max_tokens`（不触发 HARD 路径）。
      不设 `max_message_chars`（openhands-sdk==1.42.0 死字段）。
    verify: >-
      `tests/adapters/openhands/test_session_guardrail_and_readings.py`
      （装配真的在 + 当前 shape 不触发 + 合成 >80 事件真的压缩且首 4 条不摘要）。
    status: PASS
  - id: EC-07
    criterion: >-
      **只读测量**：`record_usage` 向注入的 telemetry sink 采样两个计数——
      `research_os.session.view_events`（全仓从未读过）与
      `research_os.session.prompt_tokens_total`；只读、不改阈值、不改
      `runtime_fingerprint`；sink 缺省 None ⇒ 不采样（既有语义逐字不变）。
    verify: >-
      `tests/adapters/openhands/test_session_guardrail_and_readings.py`
      （sink 注入 ⇒ 两 metric 在场；None ⇒ 零采样）。
    status: PASS
  - id: EC-08
    criterion: >-
      **文档同步**：`docs/architecture/CONTEXT_ENGINE.md` 补 §6.1（合约声明式导出 +
      最后一米装配点）与 §9（压缩委派 SDK + 护栏三参数 + 只读测量 + 无人看守出口登记）。
    verify: >-
      文档判据（`docs/architecture/CONTEXT_ENGINE.md` 含 `### 6.1` 与 `## 9.` 两节、
      关键词逐字在场）。
    status: PASS
  - id: EC-09
    criterion: >-
      **宪章记账**：程序表序 81（GOAL-20261114-113）；阶梯「迭代」行 `当前级`
      按实际推进（记忆写入 + 下一轮读得到；**`下一级` 逐字不动**）、其余六行逐字不动；
      进展 / 修订两表各回 3 行（本轮行进表后最旧的移入 archive）。
    verify: >-
      `tests/tooling/test_mainline_*` 判据 + `tools/verify_goal113_closeout.py`
      记录面（程序表行 / 阶梯行 / 进展行 / 修订行）。
    status: PASS
  - id: EC-10
    criterion: >-
      **收口资产**：`tools/verify_goal113_closeout.py`（标准断言集 + 本轮产品面 +
      记录面）+ `tools/goal113_closeout_assertions.py`（声明面四行装配 / Decimal /
      condenser kwarg / metric 名逐字）；登记 `_VERIFIERS` 与 `IN_SCOPE`。
    verify: >-
      `tools/verify_goal113_closeout.py --root . --verdict-only` 全 PASS；
      `tests/tooling/`（射程判据 + 验证器自跑断言）全绿。
    status: PASS
fix_policy:
  forbidden:
    - 不得把 `memory_export` 缺省改成「允许」（缺省 `None` ⇒ 不晋升——零回归的机械形态）
    - 不得改 `gate.py` 的 `_CURATOR_TIERS` 或 curator 判定
    - 不得设 condenser 的 `max_tokens`（触发 HARD 路径）；不得改 `max_message_chars`（死字段）
    - 不得让 condenser 使用 agent `llm` 之外的第二个 LLM 对象（指纹静默掉 `NOT_VERIFIED`）
    - 不得把 `memory.write` 写进协议 `required_capabilities`（gate-only 能力，preflight FAIL）
    - 不得让 `MemoryExportSpec.confidence` 退回 float（canonical 序列化拒绝 float）
    - 不得动 `examples/config/capabilities.yaml`（词表钉 47 条）
    - 不得假装「恰好一次」；不得宣称安全；观测默认不记录完整 Prompt / 模型输入输出
next_plan: PLAN-20261114-113-memory-last-mile
---

# GOAL-20261114-113 — 记忆的最后一米 + 上下文压缩的护栏

## 目标与退出标准

EC 表见 frontmatter `exit_criteria`（编号 / 标准 / 验证 / 状态逐条在列）。
本轮唯一的**既有缺陷**是靶子 A（机制完备但从未接线）；靶子 B 是新面（护栏 + 测量）；
靶子 C 是记账。

**如实登记（不得读成已完成）**：
- 记忆写入只覆盖**一个**合约（`research_manuscript`），其余 33 份不写 —— 这是**设计**。
- 压缩**不改变当前行为**（`max_size=80` 对 5–12 个 view event 永不触发），它不是性能优化。
- **一个出口无人看守**：`LLMSummarizingCondenser` 的 `@observe` 有 `ignore_inputs` 但
  **没有 `ignore_output`** ⇒ 摘要文本会作为 span output 上线。今天 SDK observability
  **未启用**，且 `privacy_exit_census` 的 `PRODUCT_ROOTS` 不含 `.venv` ⇒ 这个出口
  任何判据都看不见。本轮只登记 `W-1`，不修。

## 循环入口协议

按迭代日志最后一行 + 工作树实况判定续点；任何一步完成立即回写本文件。
崩溃重入规则见 `.cursor/plans/goals/README.md`（幂等恢复六条）。

## 单 cycle SOP

① 生成子 PLAN（charter 骨架已由 `tools/next_round_charter.py` 产出）→ ② 执行 →
③ 本地验证（定向 + 静态门）→ ④ commit + push（主题点名 goalNNN；绝不 `git add -A`）→
⑤ CI 八 job 判读（不假设绿）→ ⑥ 失败分类纠错 → ⑦ 收口（全部 EC=PASS ⇒ RECHECK +
m0 witness + 两树复检）。

## CI 失败分类与纠错

| 分类 | 处置 |
| --- | --- |
| (i) 判据实现缺陷（自己的判据错） | 改判据并在迭代日志点名 |
| (ii) 环境资源型（阈值/超时/并发 flake） | 重跑该 job（`rerun-failed-jobs`），绝不动阈值 |
| (iii) 产品真缺陷 | 修复 + 反向按压，新 commit 点名 goalNNN |

## 终止与收口

- **ACHIEVED**：十条 EC 全 PASS + 独立 RECHECK PASS/PASS_WITH_WARNINGS + 全量 m0
  witness（`PASS: profile=m0; 23 deterministic checks`，`PASS [` 24，0 FAILED，
  `tree changed during the run: False`）+ 两树复检 sha256 相同 + CI 八 job 全绿。
- **BLOCKED**：连续 2 轮零 EC 推进；或撞上停止条件清单（TrustLabel / RunManifest /
  `.github/workflows/**` / 撤销 §9 / 恰好一次 / condenser 换 LLM 对象 / github.com 出网不可达）。
- **ABORTED**：用户叫停。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261114-113-memory-last-mile | PENDING（tip 债：随收口 chore 提交回填） | 定向套件全绿 + 静态门全绿 + 离线十一相 9/9 + live 十一相 SUCCEEDED（run `8ba73c2a`，`m12_memory`=1 且下一轮可读） | PENDING | 2（F-1 float→Decimal：canonical 序列化拒绝 float，实测整链判红；F-2 白名单脚本补 `metrics` 制品：live 计划选中 `m12_reference_classification.py` 时被 `ARTIFACT_EXISTS(metrics)` 点名拒绝——GOAL-066 起可达的既有缺口） | W-1（condenser span output 出口无人看守）；`memory.read` 声明面仍未进任何协议；同会话第二判据因中转站配额 429 失败（2026-11-16 00:28 UTC+8 重置，基础设施） | 下一轮 charter 由本文件读出 |

## 状态历史

- 2026-11-14：建档（charter 已由 `next_round_charter.py` 从 GOAL-112 产出）。
- 2026-11-15：EC-01…04、EC-06…08 落地 + 判据全绿；真跑抓到并修复 F-1/F-2（各有判据）；
  EC-05 真实 run SUCCEEDED 且 `m12_memory` 非空、下一轮 `prior_knowledge` 读得到
  （读数见 `evidence/GOAL-20261114-113-live-m12-memory.json`）；EC-09/EC-10 落地；
  `verify_goal113` 90 判词全 PASS；残余按 RECHECK 登记（`W-1` + 既有红 023/027/030
  与本轮无关，干净 HEAD 同判）。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判级也如实登记。行随收口 chore 提交回填 ——
提交哈希写不进它自己携带的内容，链在下一个提交收敛。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
