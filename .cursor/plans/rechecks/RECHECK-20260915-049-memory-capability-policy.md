---
id: RECHECK-20260915-049
plan_id: PLAN-20260914-049
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-gate-evidence
baseline_ref: a940ac7
checked_head: 14e6c4f
---

# RECHECK-20260915-049 — memory capability policy 独立复检

GOAL-20260912-001 cycle 9（EC-04 第四批）派生计划的复检。本 cycle 的关键语义决定是
**策略面不新增第二套判定**：记忆门链的 policy 阶段复用控制面运行期的同一个
`PolicyEvaluator`（`NativePolicyEvaluator` + `examples/config/policy.yaml`），且
repo 默认策略把 `memory.write` 的四个 tier 全部显式放行——**接线不改变既有写入
行为**，只是让"某 tier 收紧为 deny/require_approval"从此真实生效且可查。复检以
「可证伪断言（含收紧/放行双向对照）+ 本地全门 + CI 终态」为权威证据。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-049-memory-capability-policy.md`
  （`parent_goal: GOAL-20260912-001`，EC-04 第四批）。
- 变更范围：`examples/config/{policy,capabilities}.yaml`；
  `packages/application/preflight/policy_check.py`（多 scope 门链能力常量 +
  `gate_capability_scopes()`）；`packages/application/memory/gate.py`（policy 阶段
  回传可读 reason）；`services/api/assembly.py`（`policy_bindings()` 单一装配助手）；
  `services/api/{composition,pg_composition,catalog,app}.py`；`services/api/dto/policy.py`
  与 `services/api/routers/policy.py`（新端点）；`services/api/routers/memory.py`
  （注入求值器）；前端 `api/{types,client,policyClient}.ts`、
  `features/governance/{GovernancePage,PolicyPanel}.tsx`、`navigation/pageSupport.ts`；
  夹具 `tests/api/run_fixtures.py`；docs 两处；openapi 再生；新增测试 14（8 应用层 +
  4 API + 2 stub e2e）。
- 边界：不做按项目/主体细分的策略、不做策略热加载或远程配置、不做规则 CRUD；
  实验队列（G14 queue/schedule）仍属后续 cycle。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | policy.yaml 四 tier allow 规则 + capabilities.yaml 注册 + 镜像测试并集相等（未放宽） | `pytest -q tests/application/test_m2_audit.py` = 16 passed；`pytest -q tests/application/memory/test_policy_wiring.py -k tier` 含 `test_mirror_declares_every_memory_tier`（声明集合 == `MemoryTier` 全集） | PASS |
| AC-02（WP-B） | 真实 evaluator 注入后：deny → policy 阶段拒绝且 reason 可读；require_approval 无 curator 时拒绝、有 curator 通过；默认策略四 tier 回归 | `pytest -q tests/application/memory` = 60 passed（新增 8 例含 SESSION/RUN 放行、PROJECT/ORGANIZATION 仍走 curator 门、deny 的 scope 特异性对照）；`pytest -q tests/api/test_policy_view_api.py` = 4 passed（默认策略下 201/ALLOW） | PASS |
| AC-03（WP-C） | `GET /policy/capabilities` 快照（规则/版本/默认效果/逐 scope 判决）；policy 未加载 → 503；console 面板 + 门全绿 | `pytest -q tests/api/test_policy_view_api.py` = 4 passed；`pytest -q tests/contracts/test_openapi_snapshot.py` = 2 passed（快照已再生，+157 行）；`npx playwright test policy-capabilities` = 2 passed（含"收紧后呈现 DENY"对照）；全量 stub e2e 36/36；eslint 0 error | PASS |
| AC-04（WP-D） | 本地全门 + m0 + CI 终态 | m0 = 23/23 PASS（全量 pytest 3333 passed / 6 skipped / 0 failed，DSN 固化）；ruff check/format + mypy（294 files）绿；CI run #67（34928371669，14e6c4f）：quality-ubuntu / quality-windows / console-frontend / container-quality / eval-gate 全 SUCCESS，collector-quality FAIL（同 2 项既有 flake，日志实测确认：2 failed / 85 passed） | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** CI `collector-quality` 仍是 RECHECK-042…048
   登记的**同 2 项** timing flake，本 cycle 的两次 run 均逐条日志实测确认
   （`test_collector_persists_research_os_spans`：collector file exporter marker 未
   落盘；`test_scenario_d_network_partition_no_old_authority`：worker 子进程 10s
   超时），各 2 failed / 85 passed，其余 5 job 全 SUCCESS：run #66（a940ac7，cycle 8
   收口提交）与 run #67（14e6c4f，本 cycle 交付提交）。按 fix_policy 不放宽断言、
   不 skip、不改 workflow（治理面）。
2. **W-2（WARNING，既有 flake 类）** 本轮 m0 第一次运行出现 1 例
   `tests/distributed/test_scenarios.py::test_scenario_f_scheduler_restart_keeps_state`
   失败（负载下 worker 接管未在等待窗口内落库）；隔离重跑 `pytest -q tests/distributed/test_scenarios.py`
   = 10 passed，随后完整 m0 复跑 0 失败。与既有记录同侧（负载下 timing 类），
   未针对它改动任何断言或超时。
3. **W-3（INFO）** 记忆门链的 policy 阶段此前恒 ALLOW（reason 为 `"policy deny"` 常量
   文案）；本 cycle 改为回传求值器理由（如 `"policy deny: matched deny rule"`）。
   既有断言只检查 `stage`，无断言依赖旧文案；API 422 detail 因此更具可读性。
4. **W-4（INFO）** `policy.yaml` 缺失/不可解析时 evaluator 为 None：`/policy/capabilities`
   诚实 503，记忆门链退回 provenance + curator 兜底（不伪造默认策略、也不静默全放开）。
   该分支由 `test_snapshot_is_503_when_policy_is_not_loaded` 锁定。
5. **W-5（INFO）** 装配助手 `services/api/assembly.py::policy_bindings()` 让 SQLite / PG
   两套组成与 e2e 夹具共用同一来源（避免"开发路径注入了、PG 路径还是 None"）。
   `tests/api/run_fixtures.py` 因此恰好 300 行（软阈值边界，未超）。
6. **W-6（INFO）** 安全扫描口径：本次 commit/push 时 Mimosa 未返回完整扫描结论
   （`scanner_enobufs`），按既有兼容策略继续且**不宣称项目安全**；完整性审计待专门
   运行（GOAL EC-06 已列）。
7. **W-7（INFO）** `services/api/composition.py` 359 行、`apps/web/tests/e2e/stub-routes.ts`
   412 行等既有软阈值警告在本次 m0 输出中仍在（均为**改动前既有**；composition 由
   347→356 行使该警告持续存在，未新增警告文件）。

## 结论

PLAN-20260914-049 AC-01~AC-04 全部满足；W-1/W-2 为既有 flake 类且已实测复现口径一致，
W-3~W-7 为范围说明与诚实边界（非伪装实现）。判定 **PASS_WITH_WARNINGS**，计划 DONE。
GOAL-20260912-001 EC-04 仍为**部分交付**（本批交付 memory capability policy；
实验队列 G14 queue/schedule 未交付），转入 cycle 10（EC-06 收口）。
