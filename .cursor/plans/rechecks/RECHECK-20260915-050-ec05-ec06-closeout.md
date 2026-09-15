---
id: RECHECK-20260915-050
plan_id: PLAN-20260914-050
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-closeout
baseline_ref: 0afce9c
checked_head: 0afce9c
---

# RECHECK-20260915-050 — EC-05/EC-06 收口复检（GOAL-20260912-001 末轮）

GOAL-20260912-001 的第 10 个（末个）cycle。本轮不新增业务能力，把两个"待判定"退出标准
变成**可机检结论 + 处置记录**，并如实登记无法达成的部分。与既往 cycle 最大的不同：
本轮对 `collector-quality` 做了**跨 8 次 run 的取证**，纠正了此前把它记作"flake"的口径。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-050-ec05-ec06-closeout.md`
  （`parent_goal: GOAL-20260912-001`）。
- 变更范围：`apps/web/tests/unit/page-support-coverage.test.ts`（新增守卫 3 例）；
  `tests/application/protocol_authoring/test_draft_service.py`（新增 4 例：3 个
  `!!python/*` 载荷拒绝 + loader 源码检查）；`docs/audits/PA1_MIMOSA_REVIEW.md`
  （收口扫描处置节）；GOAL/ALL_PLAN/PLAN/RECHECK/MEM 治理记录。
- 边界：实验队列（G14 queue/schedule）不实现、不假装交付；worker 关闭语义与
  OTel 证据链不在本轮修复；`.github/workflows/*` 不改（治理面）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A/EC-05） | 33 路由能力声明守卫三条（显式条目 / 非 full 必有 reason / gap 仅非业务页），且带**反证断言**（未登记键确实落到默认 gap → 断言非空） | `pnpm test`（apps/web）= 76 passed（新增 3）；`npx tsc --noEmit` 绿；eslint 0 error。分布实测：33 路由 = 10 full / 22 partial / 1 gap（gap 仅 `ops/matrix` 界面状态说明页，不消费后端能力） | PASS |
| AC-02（WP-B/EC-06） | 密封深扫 seal + 逐条处置表；HIGH 误报升级为可证伪测试；全程不出现"安全"结论 | `security_scan_start/status`：scanId `scan-2026-09-15T04-43-03.726Z-4bad20180460`，seal `sha256:bfeaf946…c5f2db31`，36 findings / 2504 parsed files / 182 packages，coverage **partial**、runStatus **inconclusive**、`verdictEffect: none`；处置表入 `docs/audits/PA1_MIMOSA_REVIEW.md`；`pytest -q tests/application/protocol_authoring/test_draft_service.py` = 13 passed | PASS |
| AC-03（WP-C） | 末轮复检 + GOAL 记账 + 本地全门 | m0 = 23/23 PASS（全量 pytest **3337 passed / 6 skipped / 0 failed**，DSN 固化，412s）；`pnpm test` 76/76、tsc/eslint 绿；stub e2e 36/36；governance validate PASS；CI 记账见下；GOAL 迭代日志/状态历史/续点与「终止与收口」与实况一致 | PASS |

## 关键发现（本轮纠正的口径）

**F-1（重要）`collector-quality` 是持续失败，不是 flake。** 取证：run #61–#68（含本轮
收口前的 #68）**每一次**都是该 job 失败，且失败测试**每次完全相同**：

1. `tests/observability/test_collector_evidence.py::test_collector_persists_research_os_spans`
   —— collector 可达（否则模块级 fixture 会以"not reachable"失败），但 file exporter
   在 45s 轮询窗口内没有落盘 marker span。
2. `tests/distributed/test_scenarios.py::test_scenario_d_network_partition_no_old_authority`
   —— `subprocess.TimeoutExpired ... 'd-partitioned' ... after 10 seconds`。**根因已定位**：
   该 worker 用 `RESEARCHOS_WORKER_EXECUTE_DELAY_SECONDS=25` 执行确定性后端，teardown
   `partitioned.terminate()` 发 SIGTERM，而 worker 只装 drain 处理器（`_STOP["flag"]=True`），
   仅在循环迭代之间退出 → 25s 执行中无法在 10s 内退出。Windows 本地 `terminate()` 走
   TerminateProcess 立即结束，故本地永不复现——**失败发生在断言之后的 teardown**。
   场景本身的断言（无旧权威）在失败前已全部通过。

因此此前 RECHECK-042…049 的"timing flake"表述不准确（复现是确定的，只是本地平台
掩盖）。按 fix_policy **不调整超时/不断言让步**：修复面分别是 worker 关闭语义
（产品行为）与 OTel 证据链（基础设施），属跨模块/治理面，本轮登记为**人工决策点**。

## 警告与处置

1. **W-1（WARNING，持续失败，非本 cycle 引入）** 上述 F-1；EC-06 的"每 cycle 全 job
   成功"**未达成**，任一 run 的 conclusion 均为 failure（5/6 job 绿）。
2. **W-2（WARNING，既有 flake 类）** 本地 m0 首跑（`/tmp/m0_cycle10.log`）出现
   `tests/distributed/test_scenarios.py::test_scenario_g_drain_stops_claims` 失败：
   `_wait_until(registry.get is not None)` 之后、`if reg_before.state == "REGISTERING"`
   之间 worker 已完成握手，check-then-act 竞态触发 `InvalidTransitionError('READY',
   'HANDSHAKE_OK')`；隔离重跑 10 passed，复跑 m0 见终态。**同类为负载敏感，不是本
   cycle 变更引入**（本轮 python 侧只新增一个测试文件的用例）。
3. **W-3（INFO）** 安全扫描覆盖口径：`coverage=partial`、`runStatus=inconclusive`、
   `verdictEffect=none`、依赖 advisory 1 条**未联网复核** ⇒ 处置记录只等于"逐条人工
   确认"，**不构成安全结论**。
4. **W-4（INFO）** EC-04 仍余实验队列（G14 queue/schedule）：`pageSupport` 保持
   `disabledOperations: ["queue","schedule"]`，CONSOLE_PAGE_MAP 保持"无域支撑"标注——
   不因收口而改口径。
5. **W-5（INFO）** 预算：GOAL frontmatter 原 `max_cycles: 8`，用户在 cycle 6 之后给出
   更新授权"持续循环迭代，迭代10次"，本轮按 10 记账并在状态历史登记该变更来源；
   不修改任何验收口径。

## 结论

PLAN-20260914-050 AC-01~AC-03 满足（WP-A/EC-05 与 WP-B/EC-06 处置面），判定
**PASS_WITH_WARNINGS**。GOAL-20260912-001 末轮判定见
`GOAL-20260912-001` 状态历史与「终止与收口」节：EC-01/EC-02/EC-03 **PASS**、
EC-05 **PASS**、EC-04 **PARTIAL**（余 G14 实验队列）、EC-06 **未达成**
（collector-quality 持续失败，人工决策点）。按 GOAL README"预算触顶即 BLOCKED"的
规则，GOAL 终态记为 **BLOCKED**（非失败，而是"预算用尽 + 存在需人工决策的阻塞项"），
可恢复点与所需决策逐条列在 GOAL 收口节。
