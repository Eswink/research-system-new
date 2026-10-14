---
id: PLAN-20261014-466
slug: goal-077-ec02-03-report-on-the-product-path
title: GOAL-077 cycle 1 — 报告经产品路径产出（EC-02）+ 立题由检索派生（EC-03）
status: DONE
created_at: 2026-10-14
updated_at: 2026-10-14
parent_goal: GOAL-20261014-077
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-467-goal-077-ec02-03-report-on-the-product-path.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-220-who-executes-is-a-contract-declaration-not-a-contract-id.md
---

# PLAN-20261014-466 — GOAL-077 cycle 1

## 验收条件

- [x] EC-03 新协议 `research_report_chain_v1`（4 phase：plan 自带运行链检索 + experiment + review + report）
- [x] EC-02 报告经**产品路径**产出（`report: {}` 声明 + 报告汇编器缝 + canonical markdown 制品）
- [x] 判据 7 例全绿（含**两条反证**：摘检索接线 / 摘汇编器缝）
- [x] 复合执行体声明的**互斥**由域拒绝（两个声明同时在场 ⇒ 构造即拒）
- [x] 既有协议 / 合约判据**零放宽**（架构与工具面判据 1741 passed）

## 实施清单（收口读数）

1. **域声明**（WP-A）：`TaskContract.report: ReportAssemblySpec | None`（新增类型，
   与 `experiment` 同形同层）+ schema `reportAssembly` + 两个 decoder 往返
   （`adapters/contracts/tasks_loaders._load_report` /
   `adapters/sqlite/serialization._decode_report`）+ **互斥**校验。
2. **读面单列**（WP-B）：`report_facts.py` —— 四条读法各对应一个既有读面
   （run 实体 / 证据 relation 投影 / `experiment_result.json` 的 metrics / 评审结论），
   指标来源**与 `GET /runs/{id}/experiments` 是同一份字节**。
3. **派发与准入**（WP-C）：`report_task.py` —— `dispatch_report`（缺装配 ⇒ 点名拒绝）+
   `execute_report_task`（读事实 → 汇编 → 准入）+ `register_and_gate_report`（登记 + 门）。
4. **派发点单列**（WP-C）：`task_dispatch.py`（`phase_runner.py` 已卡 450 行硬上限）+
   `runner_wiring.py`（`service.py` 同因）。
5. **装配面**（WP-C）：`OrchestrationDependencies.report_task` + `services/api/report_support.py`
   （与 `experiment_support.py` 同形同层）。
6. **协议**（WP-D）：`examples/protocols/research_report_chain_v1.yaml`（4 phase）+
   `research_report_deliverable` 加 `report: {}` 声明（**既有合约加声明，不新增合约**）。
7. **判据**（WP-E）：`tests/e2e/test_research_report_arc_offline.py`（7 例）。
8. **记录 + 门**（WP-F）：本文件 + RECHECK-467 + GOAL-077 回写 + ALL_PLAN 同提交。

## 证据（逐条可复核）

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 新判据（主 + 2 反证） | **7 passed** | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_research_report_arc_offline.py -q` |
| 报告经产品路径产出 | 报告制品 `{run_id}:research_report.md` 在 `GET /runs/{id}/artifacts` 上；`GET /artifacts/{id}/content` ⇒ 200 + `text/markdown` | 同上的主干用例 |
| 报告四节齐全 + 每数字可溯源 | 四条 `SECTION_HEADINGS` 在位；真 PMID（39284801 / 40601758）与真标题逐字出现；指标值与 `GET /runs/{id}/experiments` **逐字相同**；digest 由内容**重算** | 同上 |
| 立题由检索派生 | plan phase 的覆盖判词读作 `EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`（**两维都在**） | 同上（`TestEC03…`） |
| 反证 A（检索） | 摘运行链检索 ⇒ run `FAILED` 且判词点名 `retrieved sources` | 同上 |
| 反证 B（汇编器） | 摘汇编器缝 ⇒ run `FAILED`、判词点名 `no report assembler is wired`、**无报告制品** | 同上 |
| 架构/工具面判据（含规模门） | **1741 passed**（此前 1740；新增 1 例是本 PLAN 的 e2e 模块过规模门） | `uv run --frozen --no-sync python -B -m pytest tests/architecture/python tests/tooling -q` |
| 产品应用层 / 域 / 适配器 / API | **2739 passed, 8 skipped** | `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain tests/adapters tests/api -q` |
| e2e / 集成 / 合约 | **865 passed, 85 skipped** | `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/integration tests/contracts -q` |
| 汇编器既有判据 | **7 passed**（抬头措辞改动后仍绿） | `uv run --frozen --no-sync python -B -m pytest tests/application/test_research_report_assembler.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | cycle 1 建档（EC-02/EC-03 的靶子与设计）。 |
| 2026-10-14 | DONE | WP-A…WP-F 全部落地：新协议 + 报告汇编器接产品路径 + 7 例判据（含 2 反证）；记录面同轮。 |

## 影响报告（收口实测）

- **产品代码**：新增 5 个模块 —— `report_task.py`（365 行）/ `report_facts.py`（240 行）/
  `task_dispatch.py`（59 行）/ `runner_wiring.py`（82 行）/ `services/api/report_support.py`
  （63 行）；**改** 5 处：`TaskContract`（新增 `report` 字段 + 互斥校验）、
  `SessionSpecContext`（新增 `run`）、`phase_runner` / `service`（各一行委派）、
  `session_resolution`（透传 run）、`task_executor`（新增 `report_outcome` 字段）。
  **零行为变化**：三个新字段全缺省 ⇒ 既有装配与会话语义逐字节不变。
- **契约面**：`task_contracts.yaml` 的 `research_report_deliverable` **加一行声明**
  （`report: {}`）；合约总数**不变**（24）；**不新增合约**（早先试过新增
  `research_report_assembly`，因会成为孤儿合约而撤回）。
- **协议面**：`examples/protocols/` **新增 1 份**（`research_report_chain_v1.yaml`）；
  既有 21 份一字不动。
- **判据面**：新增 1 个 e2e 模块（7 例、410 行、无超 50 行函数）；**改** 3 份同源判据的
  **字面量清单**（**扩面，不是放宽**）：`test_declared_input_sources.py`（本协议声明
  既有输入 id ⇒ 加进等号判据的名单）、`test_run_chain_capability_exposure.py`
  （立题格写进 `_RUN_CHAIN`，能力集逐条取自**文档原文**）、
  `test_session_tool_bindings_exposure.py`（评审格写进 `_BOUND` + `_EXPECTED_DECLARED`）。
  **谓词一条未改**：只把**新的受判对象**登记进原本就存在的判断里 —— 若本协议真的
  声明错了（输入 id 不在制品表 / 绑定越界 / 声明与文档不符），这三条会**当场判红**
  （实测：把 `_BOUND` 加进去后先跑了一轮，18 例全绿；把协议里的绑定删一行即红）。
  `test_declared_input_sources` 的「控制面组合根必须种入」判据不受影响（组合根集合未变）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化**。

## 残余与未覆盖

- EC-04（新站真实 run）与 EC-05（自举收口）**不在本 cycle**：cycle 2 / cycle 3。
- 报告的**叙述性撰写**（模型写正文）明确不做 —— 那是阶梯「报告」域的**再下一级**。
- **检索内容不进模型上下文** —— 那是阶梯「检索」域的下一级；本 cycle 只保证
  「报告站在真检索上」（来源逐条入报告 + 覆盖两维）。
- **报告在 run 内汇编** ⇒ 抬头标「汇编时状态」（那时 run 尚未到终态）；
  run 的最终终态不在这份报告里。这是如实边界，不是缺陷。
