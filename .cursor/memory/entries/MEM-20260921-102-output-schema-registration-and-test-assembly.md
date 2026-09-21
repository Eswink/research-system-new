---
id: MEM-20260921-102
title: "新 output_schema 的登记路径（文件 + validate_bundle 注册表行同提交）；以及测试装配分工——判据必须放在能测到它的装配上"
status: ACTIVE
created_at: 2026-09-21
updated_at: 2026-09-21
scope: repository
confidence: 0.9
review_after: 2027-09-21
source_plans:
  - .cursor/plans/tasks/PLAN-20260921-129-real-protocol-availability.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260921-129-real-protocol-availability.md
supersedes: []
tags:
  - contracts
  - json-schema
  - validate-bundle
  - test-assembly
  - goal-010
---

# 新 schema 的登记路径与测试装配分工（GOAL-010 EC-03 实测）

## 做了什么

新增一条**产品侧合约** `real_research_deliverable`（协议 `real_research_task_v1.yaml` 用它）。
合约 schema（`schemas/task-contract.schema.json`）要求 `output_schema` **必填**且匹配
`^[a-z][a-z0-9_]*_v[0-9]+$` ⇒ 只能新起一个名字 `real_research_deliverable_v1`，
于是必须决定：这个名字怎么落地才**不说谎**。同时把 WP3 的身份判据从默认装配搬到 `run_ready` 装配。

## 为什么这样做

- **`output_schema` 在产品代码里是惰性的**：实测 `rg output_schema`（排除 tests/schemas）只有
  三处——loader 读入（`adapters/contracts/tasks_loaders.py`）、Domain 字段
  （`packages/domain/tasks.py`）、序列化（`adapters/sqlite/serialization.py`）；
  **没有任何生产代码注入 `schema_check`**（`packages/domain/acceptance.py::_evaluate_schema_valid`
  的 `schema_check` 恒为 `None` ⇒ `SCHEMA_VALID` 永远判「validator unavailable」）。
  所以名字与文件的耦合**不靠运行时**保证，只靠仓库约定 + `validate_bundle` 的注册表。
- **注册表是双向一致检查**：`validate_bundle.py::check_json_schemas` 拿 `schemas/*.json` 的集合与
  硬编码 `expected_schema_files` 做**对称差** ⇒ 只加文件不登记、或只登记不加文件，**都**红。
- **仓库既有的维护路径就是「同提交加文件 + 注册行」**：先例 `4156238`（M9）在一次提交里同时加入
  `export_bundle_v1.schema.json`、`reproducibility_audit_v1.schema.json` **与其注册表行**。
  按这条路走**不是**放宽判据：校验逻辑一字未改，且删行即红（可反证）。
- **判据要放在能测到它的装配上**：`make_base_deps`（默认 `client`）**不带** `runs_store`，
  run 读面会回落到内存注册表；`make_run_ready_deps`（`run_ready_client`）带 `runs_store`，
  但按设计只冻结 Manifest、**不跑到达成**（恒 `FAILED`）。把「身份」与「可达性」写在同一个装配上，
  会让其中一半**静默失效**（实测：混着写时 `run_ready` 装配两条都 `FAILED`）。

## 怎么做与复现

1. **新 `_vN` output_schema**：`schemas/<name>.schema.json`（`additionalProperties: false` +
   显式 `required`，`validate_bundle` 对 object 节点两样都查）**并且**在同一提交把
   `"<name>.schema.json"` 加进 `.cursor/skills/system-spec-check/scripts/validate_bundle.py`
   的 `expected_schema_files`（按字母序插入）。
2. **反证**：删掉该行 ⇒
   `.venv/Scripts/python.exe .cursor/skills/system-spec-check/scripts/validate_bundle.py`
   报 `JSON Schema 注册表不一致: ['<name>.schema.json']`；复原 ⇒ `验证通过`。
3. **判据分工**：
   - 身份/持久化（`protocol_id`、`protocol_body_digest`、库里 `protocol_body.text`）⇒
     `run_ready_client` + `run_ready_deps`（store-backed）；
   - 可达性（终态 `SUCCEEDED` + 交付物用声明名）⇒ 默认 `client`；
   - **默认装配没有 artifact store**：`GET /runs/{id}/artifacts` 如实 `503`，
     要用 `GET /runs/{id}/evidence` 的 `source_ref` 判产物名字。

## 适用边界

- 只适用于**产品侧**合约的 `output_schema`。`output_schema` 惰性意味着这份 schema 是**声明**，
  不是**被执行**的约束：它不会让任何 run 失败，也不会保护任何东西——别把它当成门禁。
- 注册表登记行是**受治理文件**改动：改动理由只应是「新 schema 需要登记」；**不得**借机改
  `check_object_boundaries` 之类的校验逻辑（那会从「登记」变成「放宽」）。
- 装配分工是 `tests/api/conftest.py` 的**现状**：若将来给 `make_base_deps` 补上 `runs_store`，
  身份判据不会自动变强——分工本身没有门禁把守。
- 本节结论基于 `:memory:` SQLite 测试装配；生产组合根（`services/api/composition.py` /
  `pg_composition.py`）带 `runs_store`，读面同样是 store 优先。

## 来源

- 实现：`examples/contracts/task_contracts.yaml`（`real_research_deliverable`）、
  `schemas/real_research_deliverable_v1.schema.json`、
  `.cursor/skills/system-spec-check/scripts/validate_bundle.py::check_json_schemas`。
- 判据：`tests/api/test_real_protocol_identity.py`（4 用例）、
  `tests/e2e/test_real_protocol_run_live.py`。
- 记录：`RECHECK-20260921-129`（W-1/W-2/W-5/W-6 即本节边界的出处）。
- 先例提交：`4156238`（M9，同提交加 schema 文件 + 注册行）。
