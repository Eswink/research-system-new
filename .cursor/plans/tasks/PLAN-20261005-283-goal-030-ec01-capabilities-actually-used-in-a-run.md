---
id: PLAN-20261005-283
slug: goal-030-ec01-capabilities-actually-used-in-a-run
title: GOAL-030 cycle 1（EC-01）：承接能力进入真实 run —— 三条已放行读能力的运行链调用 + 调用证据 + 下游消费 + 反证点名
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-284-goal-030-ec01-capabilities-actually-used.md
memory_entries: []
parent_goal: GOAL-20261005-030
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261005-030 的 **EC-01**。授权沿用该 GOAL 的 `authorization.ref`：
    「把承接能力**接进真实 run 的 phase**（协议声明 + 装配接线）」+「修实现过程中发现的
    **真缺陷**」+「新增判据 / 夹具（落 `tests/**`）」+ push-to-main-for-CI 口径
    （**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面；**不动**
    `policy.yaml` / `default_effect` / `_CAPABILITY_SCOPE`；**不让任何未放行能力变为协议可达**；
    **不改** `PRODUCT_ROOTS` / m0 条数（终态行仍 `23`）/ 作业结构；**零**新依赖；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 GOAL-029 建成的承接面从「**接上了**」推到「**真的被用**」：让一次默认装配的 run
    真的用上多条承接读能力，并让「被使用」有**调用证据 + 下游消费证据 + 反证点名 + 实跑终态**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **三条已放行承接读能力由运行链确定性执行**（`artifact.read` / `evidence.read` /
      `workspace.read`），且**每条都有调用证据**（工具证据的 `tool_refs` 逐条点名
      `("m12_artifact", <tool_id>)`）—— 受判面 = **三条逐条**（缺哪条点名哪条）。
    status: PASS
  - id: AC-2
    criterion: >-
      **产出可复核**：三条工具证据各指向一个 `tool-result:` 内容寻址制品，
      `content_digest` / `source_origin` 在场，读面取得到**内容**。
    status: PASS
  - id: AC-3
    criterion: >-
      **下游消费**（本 EC 的核心）：`review` phase 的 `evidence_read` **返回内容**里含有
      `probe` phase 三条工具证据的 id —— 证明「调了但没人用」不成立。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证点名**：不给 provider 实例（声明照旧）⇒ run **失败**且失败消息**点名**
      provider / 能力 / 工具（`has no registered instance`）；复原 ⇒ 绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **实跑终态**：默认装配离线链跑到 `SUCCEEDED`，`manifest_digest` 在场
      （冻结真的发生）+ 两个 phase 各三条工具证据齐备。
    status: PASS
  - id: AC-6
    criterion: >-
      **修掉实现过程中发现的真缺陷**：一次 run 的两个 phase 调同一工具时
      `register_tool_evidence` 的 evidence id **相撞**（`conflicting evidence registration`）
      —— 根因是 id 省略了 `result.task_id`（而 `source_origin_for` 与 `_spilled_artifact_id`
      都带它）。修法：id 与另两者**同粒度**。按压（撤回修复）⇒ 判红且点名；复原 ⇒
      raw `sha256` 逐字节相同。
    status: PASS
  - id: AC-7
    criterion: >-
      **不改既有判据 / 门禁**：`tests/application/preflight/**`（含差集与逐条放行两条）
      **逐字节未改**且全绿；`tests/architecture/python/**`、`tests/loaders/**`、
      `tests/tooling/**` 全绿。
    status: PASS
---

# PLAN-20261005-283 — GOAL-030 cycle 1（EC-01）

## 它解决了什么

GOAL-029 把承接面扩到 17/46 并让「出厂即可跑」机械化，但**承接面 ≠ 被使用**：建档勘察
逐条分类实测 GOAL-029 承接的五条读能力**使用面 = 0**，已放行的三条**只在会话面上
「可能被模型调用」**、**从无「产出被下游消费」的证据**。

本 PLAN 让一次 run **确定性**地用上三条已放行的承接读能力，并把「用到了」变成可复核证据。

## 改动（显式路径）

| 文件 | 改动 |
| --- | --- |
| `packages/application/run_orchestration/phase_capabilities.py` | `RunChainCall` 新增取参来源 `run_id_argument`（**执行期才存在**的 run 标识：协议/装配方无从写死）+ `_StepInputs.run_id` + `_arguments` 注入 + 缺它时点名拒绝；缺 provider 实例的失败消息**扩到点名能力与工具** |
| `packages/application/evidence/tool_evidence.py` | **真缺陷修复**：evidence id 补 `result.task_id`（与 `source_origin_for` / `_spilled_artifact_id` 同粒度）—— 否则同一 run 的两个 phase 调同一工具时相撞 |
| `examples/protocols/capabilities_used_in_a_run_v1.yaml` | 新增协议：两个 phase 均为 `capability_execution: run_chain`，声明三条已放行读能力 |
| `examples/contracts/task_contracts.yaml` | 新增 `capabilities_used_probe` / `capabilities_used_review` 两份契约 |
| `tests/e2e/test_capabilities_really_used_in_a_run.py` | 新增判据（8 passed）：调用证据 / 产出可复核 / **下游消费** / 反证点名 / 判据自检 |

## 如实边界（不夸大，也不缩小）

- **只用已放行的三条**：另五条（`claim.read` / `budget.read` / `deliverable.read` /
  `experiment.read` / `experiment_plan.read`）在 `policy.yaml` 无 `allow` ⇒ 写进
  `required_capabilities` 会同时打红既有两条差集判据（实测），消红必须改既有判据
  ⇒ 属 `D-02(b)` **待拍板**。受限面逐条登记在 GOAL 记录，**不以「已承接」冒充「已跑通」**。
- 三条读的是**本次 run 自己的 canonical 状态**（声明输入制品 / 证据投影 / 工作区视图），
  **不是外部检索** —— 本 PLAN **不**声称做过文献检索，也**不**声称读结果影响了交付物的
  科学结论（验收门只判产物存在与来源覆盖）。
- 装配走 run-ready 夹具（`preflight_override` + 装配方声明的运行链步），与 GOAL-011/027/029
  全部离线判据同一条路径；它证的是**链路与判据**。

## 按压记录（两处，各自独立，全部逐字节复原）

1. **撤回缺陷修复**（evidence id 去掉 `task_id`）⇒ **2 failed**，判词逐字复现缺陷签名
   `conflicting evidence registration: evidence:<run>:artifact_read`；复原后
   `sha256sum -c` 三文件全 `OK`。
2. **协议改回会话语义**（`review` phase 去掉 `capability_execution: run_chain`）⇒ **4 failed**
   （含判据自检那条，点名「声明面变了」）；复原 ⇒ 8 passed。

## 本地验证

- `tests/e2e/test_capabilities_really_used_in_a_run.py` ⇒ **8 passed**；
- `tests/application/preflight + tests/architecture/python + tests/loaders + tests/tooling +
  tests/application/evidence + tests/application/run_orchestration` ⇒ **1746 passed**；
- `tests/e2e + tests/api` ⇒ **770 passed / 17 skipped**（无回归）；
- `ruff check` / `ruff format --check` 绿；`mypy` 绿（两个改动文件）。

## 剩余差距

- b 组（EC-02）与科研动作深度（EC-03）、判据射程自查（EC-04）、自举收口（EC-05）未做；
- 五条未放行读能力仍**不可协议可达**（待 `D-02(b)` 拍板）。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7）。

## 实施清单

- [x] **WP-A（产品）**：`RunChainCall.run_id_argument` 取参来源 + `_StepInputs.run_id` +
      `_arguments` 注入 + 缺 run id 时点名拒绝；缺 provider 实例的判词扩到点名能力与工具。
- [x] **WP-B（真缺陷修复）**：`register_tool_evidence` 的 evidence id 补 `result.task_id`
      （与 `source_origin_for` / `_spilled_artifact_id` 同粒度）。
- [x] **WP-C（协议 + 契约）**：`capabilities_used_in_a_run_v1.yaml` +
      `capabilities_used_probe` / `capabilities_used_review`。
- [x] **WP-D（判据）**：`tests/e2e/test_capabilities_really_used_in_a_run.py`（8 passed）。
- [x] **WP-E（按压两处）**：撤回修复 ⇒ 2 failed；协议改回会话 ⇒ 4 failed；均逐字节复原。
- [x] **WP-F（记录）**：本 PLAN + `RECHECK-20261005-284` + `ALL_PLAN` 投影 + GOAL 回写。

## 证据

- **判据**：`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_capabilities_really_used_in_a_run.py -q`
  ⇒ **8 passed**。
- **受判面**：`tests/application/preflight` + `tests/architecture/python` + `tests/loaders` +
  `tests/tooling` + `tests/application/evidence` + `tests/application/run_orchestration`
  ⇒ **1746 passed**；`tests/e2e` + `tests/api` ⇒ **770 passed / 17 skipped**。
- **调用证据**：三条能力的 `tool_refs` = `("m12_artifact", artifact_read|evidence_read|workspace_read)`，
  **逐 phase** 各三条齐备。
- **下游消费证据**：`review` 的 `evidence_read` 返回内容含 `probe` 三条工具证据 id。
- **反证判词**：`has no registered instance ... (capability ..., tool ...)` + provider 名。
- **按压 sha256**：`scratch/goal030-recon/press-before.sha256`，复原后 `sha256sum -c` 三文件全 `OK`。
- **质量门**：`ruff check` / `ruff format --check` / `mypy` 绿。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 1 derive）并执行 WP-A…WP-C。 |
| 2026-10-05 | DONE | WP-A…WP-F 收口；判据 8 passed；两处按压逐字节复原；`RECHECK-20261005-284` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：产品 2 文件（`phase_capabilities.py` 取参来源 + `tool_evidence.py` 缺陷修复）+
  配置 2 文件（新协议 + 两份契约）+ 判据 1 文件。
- **Domain/API/schema 变化**：无 DTO / OpenAPI 变化；evidence id 形态**变化**
  （`evidence:{run_id}:{task_id}:{operation_key}`）—— 见 `W-4`/`RECHECK` 的残余登记。
- **安全/凭据变化**：无新增凭据面；`policy.yaml` **未动**；默认 deny 不变。
- **兼容性/迁移风险**：evidence id 形态变化影响**依赖该 id 字面量**的既有读面消费者 ——
  实测既有测试全绿（判据按 `tool_refs` / `source_ref` 取样，不按 evidence id 字面量）。
- **上游版本影响**：无。

## 无可复用事实

本 PLAN 的产出是**产品接线 + 判据**，不含新的跨 GOAL 工程约定；本轮的通用教训
（「判据侧按单键索引会在同名工具下掩蔽上/下游」）已写进判据 docstring 与
`RECHECK-20261005-284` 的 `W-1`，**不另立 `MEM`**（同一形态在 `MEM-20260922-160`
已有更一般的表述）。
