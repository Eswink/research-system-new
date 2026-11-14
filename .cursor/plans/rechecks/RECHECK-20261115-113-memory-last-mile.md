---
id: RECHECK-20261115-113
slug: memory-last-mile
title: GOAL-113 复检 —— 记忆的最后一米 + 压缩护栏与测量
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-15
updated_at: 2026-11-15
plan_id: PLAN-20261114-113
parent_goal: GOAL-20261114-113
owners:
  - root-agent
verify_paths:
  - packages/application/run_orchestration/dependencies.py
  - packages/application/run_orchestration/memory_promotion.py
  - services/api/memory_gate_support.py
  - packages/domain/tasks.py
  - adapters/openhands/session_builder.py
  - tests/application/run_orchestration/test_memory_export_declaration.py
  - tests/integration/test_ig1_phase_runner.py
  - tests/adapters/openhands/test_session_guardrail_and_readings.py
---

# RECHECK-20261115-113

## 复检范围

GOAL-20261114-113 的十条 EC 逐条取证。**两路以上**（`verify_paths` 每项都是独立取证路径）。

本轮的射程边界（写在前面，收口时逐条核对有没有越界）：

| 面 | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- |
| 记忆写面 | 四行装配 + 合约声明式放行 + 真实 run 写入 + 下一轮读得到 | **不**宣称「34 份合约都写」——只覆盖 `research_manuscript` 1 份（设计，其余 33 份刻意不带） |
| 记忆读面 | `prior_knowledge` 渲染行逐字可读 | **不**判「模型因此改变了立题」（GOAL-082 EC-04 未决取舍未动） |
| 门 | `gate.py` 一行不改（声明是编排层授权来源） | **不**宣称「声明绕过了 curator 门」——判据钉住门仍在咬 |
| 压缩 | 护栏（默认不触发）+ 只读测量 | **不**宣称性能优化——当前 shape 永不触发 |
| 安全 | 无 | condenser span output 出口无人看守（`W-1`，登记不修） |

## 真跑抓到的两个缺陷（本轮修复，各有判据）

### F-1 canonical 序列化拒绝 float（真跑判红）

第一版 `MemoryExportSpec.confidence: float = 0.8`。声明随 `TaskContract` 进
CompiledRunPlan 与 RunManifest ⇒ `manifest.digest()` 走 canonical 序列化 ⇒
`ValueError: float is not allowed in canonical serialization`（`domain/serialization.py:37`）
⇒ **十一相链整链判红**（离线 product-path 9 条全红、live 两次 FAILED 全相未启动、
run 无任何事件）。修法：`confidence: Decimal = Decimal("0.8")`（`Decimal` 是既有
canonical 词表的一员，`budget` 同型）；loader 用 `Decimal(str(...))` 换算；晋升边界
`float(memory_export.confidence)` 显式换算（门链提案面 `MemoryWriteProposal.confidence`
是 float，且提案不进 digest）。判据：断言集钉 `Decimal` 源码形态 + 离线链 9/9 复绿。

### F-2 白名单脚本 × 合约判据错配（live 判红）

live run 的计划（`design_source="plan"`）从白名单选了
`m12_reference_classification.py`，而合约 `experiment_execution` 要求
`ARTIFACT_EXISTS: artifact metrics`——三个白名单脚本里**只有**
`exact_match_index_benchmark.py` 产出独立的 `metrics` 制品（`artifact_refs: ["metrics"]`），
另两个只把指标写进 result payload 的 `metrics` **键** ⇒ 验收门点名拒绝
（`run.failed: task … rejected by acceptance gate (ARTIFACT_EXISTS: artifact metrics missing)`）。
这条错配是 GOAL-066（脚本由计划选择）把该路径变成可达后**一直存在的既有缺口**，
此前只靠「计划恰好选了默认脚本」掩盖。修法：`m12_reference_classification.py` 与
`sort_analysis_baseline.py` 各自把同一份摘要指标写成独立 `metrics` 文件并列入
`artifact_refs`（与默认脚本同形；result payload 其余键与字节形态不变）。
判据：四个脚本套件 **38 passed**（membership 断言容纳新增制品）。

## 检查结果

### EC-01 四行装配（PASS）

`OrchestrationDependencies` 新增 `memory_gate: Any | None = None`（缺省 `None` ⇒
不晋升，既有语义逐字不变）；两个组合根各经 `services/api/memory_gate_support.py`
的 `sqlite_memory_gate` / `pg_memory_gate` 注入 `MemoryGateDeps`（store 与
`memory.read` 读面**同一实例**）；`runner_wiring.py` 把 `deps.memory_gate` 传进
`PhaseRunnerDeps`。断言集按源码逐处按压（四行各自点名）。

### EC-02 声明面（PASS）

`TaskContract.memory_export` + `MemoryExportSpec(tier=PROJECT, kind=FACT,
confidence=Decimal("0.8"))`——**授权声明**而非执行体，不参与 `experiment`/`report`
排他校验。schema `memoryExport` 定义 + loader `_load_memory_export`（未知键点名拒绝）
同轮。实测：34 份合约加载不变、`research_manuscript` 带声明、`editorial_decision`
不带（零回归的机械形态）。

### EC-03 读声明 → 代表合约提交（PASS）

`promote_memory`（自 `task_phase_helpers.py` 迁入 `memory_promotion.py`）读本任务合约
的 `memory_export`：有声明 ⇒ tier/kind/confidence 取自声明、`curator_approved=True`
传给 `commit_memory`（编排层观察到的 `NEGATIVE_RESULT` 优先于声明的缺省 `FACT`）；
无声明 ⇒ 不晋升（不是拒绝）。**`gate.py` 一行不改**——断言集钉住其源码不含
`memory_export`、`_CURATOR_TIERS` 逐字保留。

### EC-04 四条判据（PASS）

`test_memory_export_declaration.py` 五条：① 正例（PROJECT 档、`scope="project"`、
provenance 指向本 run evidence、判词点名授权来自合约声明）；② 反证（合约不带 ⇒ 空）；
②b 反证（gate 未接 ⇒ 空）；③ 反证（`curator_approved=False` ⇒ 不写入且判词点名
curator 阶段——证明「声明即绕过门」不成立）；④ 下一轮 `prior_knowledge` 渲染行逐字
匹配 `- {memory_id}{marks}: {shown} (source: {provenance})`。
链级 ① 由 `test_ig1_phase_runner.py` 加严后钉住（tier/scope/provenance 三向断言）。

### EC-05 真实 run 写入（PASS）

`RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1
RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS=1` 下 `test_the_manuscript_chain_runs_live.py`
2/2 SUCCEEDED（十一相全绿）。直查该 run 自己的库：`m12_memory` **非空**，
`tier='PROJECT'`、`scope='project'`、provenance 指向本 run 的 evidence
（读数落盘 `evidence/GOAL-20261114-113-live-m12-memory.json`，先写盘再断言）。

### EC-06 condenser 护栏（PASS）

两处 `PolicyEnforcingAgent` 构造点都传 `condenser=_context_guardrail(llm)`；
`LLMSummarizingCondenser(llm=llm, max_size=80, keep_first=4)`；`max_tokens` 不设
（判据断言源码无 `max_tokens=`）；`max_message_chars` 不设（死字段）。
判据三向：装配真的在（`condenser.llm.usage_id == agent.llm.usage_id`——指纹面仍单值）；
当前 shape（12 事件）零触发理由；合成 81 事件 ⇒ `Reason.EVENTS` 触发、
`condensation_requirement == SOFT`、被摘要事件不含首 4 条（keep_first 承重）。
全程零出网（`get_condensation_reasons` / `_get_forgotten_events` 纯函数）。

### EC-07 只读测量（PASS）

`record_usage` 向注入 sink 采样 `research_os.session.view_events`（COUNTER，
终态 view 长度）与 `research_os.session.prompt_tokens_total`（COUNTER，逐 usage
累计）；sink 缺省 `None` ⇒ 不采样（既有语义逐字不变）。判据：注入 ⇒ 两 metric
在场且值 > 0；None ⇒ 零采样。**不设阈值、不改 `runtime_fingerprint`。**

### EC-08 文档同步（PASS）

`CONTEXT_ENGINE.md` §6.1（合约声明式导出 + 装配点）与 §9（压缩委派 SDK + 护栏
三参数逐条理由 + 只读测量 + `W-1` 出口登记）在树。

### EC-09 宪章记账（PASS）

程序表序 81 行（六格）；阶梯「迭代」行 `当前级` 收录「记忆的最后一米」+
`依据` 收录本 GOAL，**`下一级` 逐字不动**，其余六行逐字未动（断言集双臂）；
进展 / 修订两表各回 3 行（GOAL-110 行 / 序 78 行移入 `archive/` 新文件，指针在列）。

### EC-10 收口资产（PASS）

`tools/verify_goal113_closeout.py` + `tools/goal113_closeout_assertions.py`
登记进 `_VERIFIERS` 与 `IN_SCOPE`；验证器自跑断言（标准面 + 产品面 + 记录面）全 PASS。

## 残余 / 未覆盖 / 声称边界

- `W-1`：`LLMSummarizingCondenser` 的 `@observe` 有 `ignore_inputs` 但**没有
  `ignore_output`** ⇒ 摘要文本会作为 span output 上线；今天 SDK observability 未启用、
  `privacy_exit_census` 的 `PRODUCT_ROOTS` 不含 `.venv` ⇒ 该出口任何判据都看不见。
  归属上游面，登记不修。
- 未覆盖：记忆写入只覆盖 1/34 份合约（设计）；`memory.read` 声明面仍未出现在任何协议
  （`required_capabilities` 0 份——本轮只接了写面）。
- 声称边界：压缩护栏不改变当前行为；测量的回答是「有没有会话接近阈值」，不是性能结论。

## 结论

**PASS_WITH_WARNINGS**：十条 EC 全 PASS；真跑抓到并修复两个缺陷（F-1/F-2，各有判据
与复绿证据）；`W-1` 逐条登记为无人看守出口。
