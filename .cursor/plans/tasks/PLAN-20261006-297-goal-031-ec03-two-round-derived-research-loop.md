---
id: PLAN-20261006-297
slug: goal-031-ec03-two-round-derived-research-loop
title: GOAL-031 cycle 3（EC-03）：科研真成环 —— 声明式派生（触发/跳过）+ 两轮链 + 两臂实测 + 两向反证
status: DONE
created_at: 2026-10-06
updated_at: 2026-10-06
latest_recheck: .cursor/plans/rechecks/RECHECK-20261006-297-goal-031-ec03-two-round-derived-research-loop.md
memory_entries: []
parent_goal: GOAL-20261006-031
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 **EC-03**（本轮主干，非「授权开工」三项之一，属 GOAL 既有
    objective 的第三段）。授权原文见该 GOAL 的 `authorization.ref`：「用户 2026-10-06 明确
    下放全部权限给驱动」+「**可以有界放宽 allow**、**不得**放宽判据/断言/门禁/阈值」+
    push-to-main-for-CI 口径（只推 `main`、不 force、不重写历史；push 前
    `git pull --ff-only origin main`）。**本 PLAN 专属边界**：本 EC **不放宽任何面**
    —— 它新增的是**声明字段**与**可观测事实**（`RunChainCall` 的
    `requires_previous_ids` / `phase_id` / `artifact_from_previous`；`CapabilityStepOutcome.skipped`
    → `TaskOutcome.skipped` → `run.completed` 载荷），既有四类取参语义与缺省行为**逐字节不变**；
    零新依赖；零真实凭据进树；默认门离线；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once +
    idempotency + deduplication）。
objective: >-
    让一次 run 含**两轮**研究，且**第二轮的问题由第一轮的结果派生**：① 派生是**声明的**
    （第二轮读哪一个制品、从哪个路径取标识、什么时候跳过，全部是 `RunChainCall` 的声明
    字段，应用层无「如果就」）；② **两条臂都实测且判据能区分**（触发 ⇒ 真跑第二轮且输入
    逐条可追到第一轮产出；不触发 ⇒ 读取步**带理由跳过**并逐字点名）；③ 迭代留痕落
    canonical（artifact / evidence，走既有 `register_session_result` 路径），且第二轮**经
    读面**读到第一轮的结论（`evidence.read` 的投影 + `artifact.read` 读回同一份字节，
    不是内存传递）；④ 两向反证（派生规则改坏 ⇒ 判红并点名路径；读面抓手摘掉 ⇒ 第二轮判负）。
    为承接 ①②，在既有运行链上补两个**声明字段**与一条**phase 级过滤**，缺省行为逐字节不变。
exit_criteria:
  - id: AC-1
    criterion: >-
      **派生是声明的**：第二轮的三步（读面取投影 → 按声明后缀选中第一轮制品 → 从该制品
      **内容**的声明路径取标识）全部由 `RunChainCall` 的字段表达；协议文档**自己**写了两轮与
      `capability_execution: run_chain`（判据读 YAML 原文）；触发判定只看**声明字段的在
      场性**（非空列表 ⇒ 执行；空/缺席 ⇒ 跳过），应用层不出现领域能力名。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_research_loop_second_round_derived.py::TestTheDerivationIsDeclared -q`
      ⇒ 全绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **两臂实测且判据能区分**：① 触发臂（检索响应非空）⇒ 第二轮真跑，读取步的工具证据
      `artifact_id` / `source_ref` **逐字带着第一轮返回的 PMID**；② 不触发臂（**同一协议、
      同一装配**，只把检索响应换成零命中）⇒ `run.completed` 的 `skipped` 逐字点名工具与
      字段、该步**零请求零证据**；③ 单次读数上两组断言**互斥**（`literature_read` 证据
      在场 / 不在场；`skipped` 空 / 非空）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_research_loop_second_round_derived.py -q` ⇒ 13 passed。
    status: PASS
  - id: AC-3
    criterion: >-
      **迭代留痕 + 读面可读**：两轮的交付物落 canonical（`round_one_findings` /
      `round_two_followup`）；第二轮的 `artifact.read` 返回**内容**与第一轮检索制品的字节
      相等（经读面读到第一轮结论）；第二轮的 `evidence.read` 投影里含第一轮工具证据的 id。
      为此 `CanonicalReadProvider._project_run` 的证据条目**增** `artifact_id` 一列
      （与 HTTP 读面 DTO 同源同列；既有键不动）——工具读面此前少这一列，而派生链的
      「选中第一轮产物」需要它。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_research_loop_second_round_derived.py tests/adapters/canonical -q` ⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证两向**：① 把派生规则改坏（`ids_from_previous` 指到 `content.no_such_field`）⇒
      run `FAILED` 且判词**点名那条路径**、零 `efetch` 请求；② 把读面抓手摘掉
      （`artifact_from_previous` 指到选不中的后缀）⇒ 第二轮**判负**（run `FAILED`，判词
      点名「选中数 ≠ 1」并列出候选）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_research_loop_second_round_derived.py::TestTheJudgeItselfBites -q`
      ⇒ 全绿；判词原文归档
      `.cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt`。
    status: PASS
  - id: AC-5
    criterion: >-
      **既有语义零改动**：`RunChainCall` 的既有四类取参（`arguments_from_input` /
      `fixed_arguments` / `ids_from_previous` / `run_id_argument`）与
      `execute_run_chain_capabilities` 的缺省级行为**逐字节不变**（既有判据一字未改且绿）；
      `run.completed` 载荷**无跳过 ⇒ 不带 `skipped` 键**（既有载荷形状不变）；
      为守住 450 行硬上限，把两个 parking 路径与声明式触发判定分别拆到
      `phase_pause.py` / `phase_capability_triggers.py`（语义逐行搬运）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration tests/application/test_pause_coordination.py
      tests/application/test_phase_spans_m15.py -q` ⇒ 全绿；
      定向回归 `tests/application tests/adapters tests/architecture tests/loaders
      tests/contracts` ⇒ 2125 passed / 73 skipped。
    status: PASS
---

# PLAN-20261006-297（GOAL-031 cycle 3 / EC-03）：科研真成环

## 验收条件

见 frontmatter `exit_criteria`（AC-1 … AC-5，逐条 verify 命令与状态）。

## 实施清单

- [x] ① `RunChainCall` 追加三个**声明字段**（缺省 ⇒ 既有行为逐字节不变）：
      `requires_previous_ids`（触发面：True ⇒ 缺 id 失败；False ⇒ 缺 id 跳过）、
      `phase_id`（过滤细化到 phase 级：两个 phase 声明同一 provider 的不同调用时不再互相跑掉）、
      `artifact_from_previous`（派生面：按**声明后缀**从上一读面结果里选中制品）。
- [x] ② 新模块 `packages/application/run_orchestration/phase_capability_triggers.py`
      （纯判定：过滤 / 取字段 / 跳过判定 / 制品选择 / 跳过判词；`lookup` 注入自
      `phase_capabilities._lookup`，点分路径**唯一取法**未复制）。
- [x] ③ 新模块 `packages/application/run_orchestration/phase_pause.py`（两个 parking 路径
      从 `phase_runner` 逐行搬出；`phase_runner` 449 → 402 行）。
- [x] ④ 跳过事实贯通到**既有读面**：`CapabilityStepOutcome.skipped` →
      `PhaseStep.skipped` → `TaskOutcome.skipped` → `run.completed` 的 `skipped` 载荷
      （无跳过 ⇒ 不带该键）。
- [x] ⑤ `CanonicalReadProvider._project_run` 的证据条目**增** `artifact_id` 一列
      （与 HTTP 读面 DTO 同源同列；既有键不动）。
- [x] ⑥ 新协议 `examples/protocols/two_round_research_loop_v1.yaml`（两个 run-chain phase）
      + 两份契约（追加到 `examples/contracts/task_contracts.yaml`）。
- [x] ⑦ 判据 `tests/e2e/test_research_loop_second_round_derived.py`（13 例）+ 支持件
      `tests/e2e/two_round_loop_support.py`（373 行；规模门禁）。
- [x] ⑧ 判词归档进树（二进制写盘、CR=0）：
      `.cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt`
      （由 `scratch/goal031-cycle3/gen_ec03_evidence.py` **实跑**生成）。

## 证据

- 判据：`tests/e2e/test_research_loop_second_round_derived.py` **13 passed**（每条 verify 见
  frontmatter；两向反证在 `TestTheJudgeItselfBites`）。
- 归档读数（触发臂）：`round2_read_artifact=tool-result:…:literature_read:39000001+39000002:literature_read`
  —— 读取步的 operation key **逐字**带着第一轮检索返回的两个 PMID。
- 归档读数（不触发臂）：`round2_tools=['artifact_read','evidence_read']`（**无** `literature_read`）、
  `http_endpoints=['esearch.fcgi']`（读取步零请求）、
  `skipped=[{"reasons": ["run-chain tool literature_read skipped: previous step carried no
  'content.ids' ids and this call declares requires_previous_ids=False"]}]`。
- 归档读数（反证①）：`state=FAILED`，判词含
  `previous step's result carries no 'content.no_such_field'`。
- 归档读数（反证②）：`state=FAILED`，判词含
  `expected exactly one evidence artifact_id ending with 'no_such_artifact', found []`。
- 定向回归：`tests/application tests/adapters tests/architecture tests/loaders tests/contracts`
  ⇒ **2125 passed / 73 skipped**。
- `ruff check` / `ruff format --check` / `mypy` 对本轮全部改动文件 ⇒ 全绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-06 | DONE | cycle 3 落地：声明字段三个 + phase 级过滤 + 跳过贯通到 `run.completed` + 读面增列 + 两轮协议与两份契约 + 13 例判据（含两向反证）+ 判词归档。AC-1…AC-5 全 PASS。 |

## 影响报告

- **Domain / API / schema**：域层**零改动**（无新实体、无新事件类型 —— 事件词表仍 38 条；
  `run.completed` 只在**有跳过**时多一个 `skipped` 键，属**附加载荷**）。API 面**零路由改动**；
  读面 `CanonicalReadProvider` 的证据投影增 `artifact_id` 一列（工具面，非 HTTP 面）。
- **安全 / 凭据**：零新凭据、零新依赖、零出网（判据全离线，NCBI 走 `httpx.MockTransport`）；
  默认门仍离线。**不声称**项目安全（`R-M1`）、**不声称** exactly-once（明确否认）。
- **兼容性 / 迁移风险**：三个新字段**全部有缺省值**且缺省即既有行为（`requires_previous_ids=True`
  / `phase_id=None` / `artifact_from_previous=None`）；`run.completed` 的 `skipped` 是**可选键**；
  读面增列是**纯追加**。既有判据文件**一字未改**（`git diff` 逐文件核对）。
- **上游版本影响**：无（未动依赖）。
- **下一项任务**：cycle 4 = EC-04（`LineageNodeDto.label` 改名 + 四处同步 + 旧名零命中 + 兼容性实测）。

## 无可复用事实

**无**（产出全部可复用：三个声明字段 + 触发/跳过判定模块 + `read_projection` 拆分 +
两轮协议与契约 + 13 例判据 + 判词归档都在树内；`phase_pause` 的 parking 搬运不引入新语义）。
`memory_entries` 在 GOAL 层回填。
