---
id: PLAN-20260914-049
slug: memory-capability-policy
title: Memory capability policy（G16）：memory.write 入 policy.yaml 镜像契约 + 运行时门 + 可见性
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 9（/goal 持续循环迭代指令）；范围=EC-04「memory capability policy（G16）」一项；实验队列属后续 cycle"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-049-memory-capability-policy.md
memory_entries:
  - MEM-20260915-026
---

# PLAN-20260914-049 — Memory capability policy（cycle 9，EC-04 第四批）

## 目标

把 G16 的诚实缺口（"capability policy 面不含 memory.write，policy 槽位显式 None"）
换成**真实可治理的能力策略面**：

- `memory.write` 成为一等 capability：`policy.yaml` 声明 + `capabilities.yaml` 注册 +
  `_CAPABILITY_SCOPE` 镜像契约覆盖（新增多 scope 门链能力的镜像常量）；
- 运行时门生效：API 装配真实 `PolicyEvaluator`，Memory 门链的 policy 阶段
  **不再恒 ALLOW**——运维可在 policy.yaml 对某 tier 收紧（deny / require_approval）；
- 可见性：`GET /policy/capabilities` 只读投影 + govern/audit 页展示，让"能力策略"
  在控制面可查（而不是只存在于磁盘上的 YAML）。

## 诚实边界

- **默认不改变既有写入行为**：repo 默认 policy.yaml 对四个 tier 都是 allow（PROJECT/
  ORGANIZATION 的 curator 门保持不变，不做第二套审批语义）；收紧只能由运维显式改规则。
- **不建第二套 permission model**：门链 policy 阶段复用 `PolicyEvaluator` Port
  （capability="memory.write"、action="commit"、scope=tier）。
- 无 principal/多项目授权（M18 deferred）：`GET /policy/capabilities` 是**全局策略文档
  投影**，不假称按项目/主体过滤。
- 实验队列仍属后续 cycle（G14 的 queue/schedule 保持禁用）。

## 范围

- 包含：
  - WP-A policy 镜像契约：`examples/config/{policy,capabilities}.yaml`、
    `policy_check.py` 多 scope 门链能力常量、镜像一致性测试更新（同样严格：集合相等）。
  - WP-B 运行时接线：ApiDeps 增加 policy/policy_evaluator（SQLite + PG 两条装配）；
    `routers/memory.py` 注入 policy；门链 policy 阶段回传可读 reason。
  - WP-C 可见性：`GET /policy/capabilities`（规则/默认效果/版本）+ console 面板 +
    pageSupport/CONSOLE_PAGE_MAP G16 同步 + openapi 再生。
  - WP-D 测试与收口：应用层 policy 门用例、API 用例、m0、RECHECK-049。
- 不包含：实验队列/调度、按项目或主体细分的策略、策略热加载/远程配置。

## 验收条件

- [x] AC-01（WP-A）：policy.yaml 声明 memory.write 的 SESSION/RUN/PROJECT/ORGANIZATION
  allow 规则；capabilities.yaml 注册该能力；镜像一致性测试以"两常量并集 == 声明对"锁死。
- [x] AC-02（WP-B）：装配注入真实 evaluator 后，deny 规则使提案在 policy 阶段被拒
  （422/stage=policy，reason 可读）；require_approval 规则在无 curator 输入时拒绝；
  默认策略下四个 tier 行为与接线前一致（回归）。
- [x] AC-03（WP-C）：`GET /policy/capabilities` 返回规则集（含 memory.write 四条）与
  版本/默认效果；store 未配置以外的情形不伪造；web 门全绿。
- [x] AC-04（WP-D）：m0 全绿 + 定向用例；push 后 quality-ubuntu 与 console-frontend
  全绿；RECHECK-049 回填。

## 实施清单

- [x] WP-A policy 镜像契约
- [x] WP-B 运行时接线
- [x] WP-C 可见性 API + console
- [x] WP-D 测试 + 收口

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest -q tests/application/test_m2_audit.py`（并集相等镜像断言）= 16 passed | PASS |
| WP-B | `pytest -q tests/application/memory` = 60 passed（新增 `test_policy_wiring.py` 8 例：四 tier 默认放行、curator 门保持、deny scope 特异性、require_approval 双向） | PASS |
| WP-C | `pytest -q tests/api/test_policy_view_api.py` = 4 passed；`pytest -q tests/contracts/test_openapi_snapshot.py` = 2 passed（openapi 再生 +157 行）；`npx playwright test policy-capabilities` = 2 passed；全量 stub e2e 36/36 | PASS |
| WP-D | m0 = 23/23 PASS（全量 pytest 3333 passed / 6 skipped / 0 failed）；ruff + mypy（294 files）绿；CI run #67 五 job SUCCESS（collector-quality 为同 2 项既有 flake） | PASS |

## 已知风险

- `_CAPABILITY_SCOPE` 是 `dict[str, str]`（一能力一 scope），memory.write 的一能力多
  scope 需要第二个常量；镜像测试必须重写为并集相等（不得放宽为子集）。
- 镜像测试还断言能力可在 `capabilities.yaml` 溯源：新增能力必须同步注册。
- API 装配出现 policy 后，任何"默认 DENY 但未声明 allow"的能力会被拒绝——
  必须确认 memory.write 四个 tier 都有显式规则，否则会把既有写入打回 422。
- PG 装配与 SQLite 装配都要注入 policy，避免"开发路径对了、PG 路径还是 None"。

## 状态历史

- 2026-09-15 由 GOAL cycle 9 派生（EC-04 第四批），进入执行。
- 2026-09-15 WP-A~WP-C 落地（`14e6c4f`）；WP-D 完成 m0 + CI 验证；RECHECK-20260915-049 判定 PASS_WITH_WARNINGS，转 DONE。

## 影响报告

- 改动：policy.yaml（memory.write 四 tier allow）+ capabilities.yaml 注册；preflight
  多 scope 门链常量 + 镜像测试重写（并集相等，未放宽）；memory 门链 policy 阶段
  回传可读 reason；`services/api/assembly.py::policy_bindings()` 统一装配；SQLite/PG
  两套组成 + e2e 夹具注入真实求值器；新增 `GET /policy/capabilities`（DTO + router）；
  console 策略面板（govern/audit Memory Tab）；docs 两处 + openapi 再生。
- lint/typecheck/test：ruff check/format 绿；mypy 294 files 绿；eslint 0 error（2 既有
  soft warning）；m0 23/23 PASS；全量 pytest 3333 passed / 6 skipped / 0 failed。
- Domain/API/schema：新增 1 个只读端点（openapi 快照 +157 行）；无 Domain 类型变更；
  无 migration。
- 安全/凭据：无新凭据面；策略文件为仓库内只读配置（无热加载、无规则 CRUD）；
  默认策略显式放行四 tier（不改变既有写入行为），收紧只能由运维改 YAML。
- 兼容性/迁移风险：无迁移；`memory.write` 若在某 tier 被收紧，既有写入路径会在
  422/policy 阶段被拒——这是预期的治理行为，已在 CONTROL_PLANE_API.md 说明。
- 上游版本影响：无新增上游依赖。
- 下一项任务：cycle 10（EC-06 收口：最终 RECHECK + 安全扫描处置 + 残留缺口诚实登记）。
