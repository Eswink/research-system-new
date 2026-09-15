---
id: PLAN-20260914-050
slug: ec05-ec06-closeout
title: EC-05/EC-06 收口：33 路由能力声明守卫 + 密封扫描处置 + 最终复检
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 10（/goal 持续循环迭代指令，10 次）；范围=EC-05（33 路由 live-capable 判定）+ EC-06（收口 RECHECK + 密封安全扫描处置）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-050-ec05-ec06-closeout.md
memory_entries:
  - MEM-20260915-027
---

# PLAN-20260914-050 — EC-05/EC-06 收口（cycle 10，末轮）

## 目标

把 GOAL 剩余的两个退出标准从"待判定"变成**可机检 + 有处置记录**：

- EC-05：33 条规范路由的"live-capable / 诚实锁定"不是靠人工清点，而是由守卫测试
  锁死——每条路由必须有显式支持等级、非 full 必须给出可读原因、gap 级只允许非业务页；
- EC-06：密封安全扫描（Mimosa deep）**有一次完整的处置记录**（seal + 逐条处置），
  并把"CI 全 job 成功"这一条的**真实状态**如实登记（含长期失败的根因分析）。

## 诚实边界

- 本轮**不宣称项目安全**：扫描 coverage=partial、runStatus=inconclusive、
  依赖 advisory 未联网复核；处置记录只等于"逐条人工确认"。
- **不为了让 collector-quality 变绿而改动断言/超时**：该 job 的 2 项失败已定位到
  环境/子进程语义（见 RECHECK-050），修复面触及 worker 关闭语义与 OTel 证据链，
  属治理面/跨模块，本轮**登记为已知失败 + 人工决策点**，不伪装成 flake。
- EC-04 的实验队列（G14 queue/schedule）**不假装交付**：保持 pageSupport 禁用 +
  CONSOLE_PAGE_MAP 诚实标注。

## 范围

- 包含：
  - WP-A（EC-05）：`apps/web/tests/unit/page-support-coverage.test.ts` 三条守卫；
    EC-05 证据清点（33 路由 = 10 full / 22 partial / 1 gap，gap 仅 `ops/matrix`）。
  - WP-B（EC-06）：Mimosa 密封深扫 + 处置记录追加到
    `docs/audits/PA1_MIMOSA_REVIEW.md`；HIGH `yaml.load` 误报升级为**可证伪测试锁定**
    （`!!python/*` 标签必须解析失败 + loader 源码检查）。
  - WP-C：最终 RECHECK-050 + GOAL 收口判定 + MEM 沉淀。
- 不包含：实验队列实现、worker 关闭语义改造、OTel 证据链修复、workflow 修改。

## 验收条件

- [x] AC-01（WP-A）：守卫测试三条全绿，且对"缺条目/无原因/业务页 gap"三条回归可证伪。
- [x] AC-02（WP-B）：扫描 seal 记录 + 逐条处置表；HIGH 误报有测试锁定；不出现任何
  "安全"结论。
- [x] AC-03（WP-C）：RECHECK-050 覆盖 EC-01~EC-06 判定；GOAL 迭代日志/状态历史/续点
  与实况一致；本地 m0 全绿 + CI run 终态记录。

## 实施清单

- [x] WP-A 路由能力声明守卫 + EC-05 证据
- [x] WP-B 密封扫描处置 + 反序列化防线测试
- [x] WP-C 最终复检 + GOAL 收口

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A（EC-05） | `pnpm test`（apps/web）= 76 passed（+3 守卫）；`tsc --noEmit` 绿；eslint 0 error；分布实测 33 = 10 full / 22 partial / 1 gap（gap 仅 ops/matrix） | PASS |
| WP-B（EC-06） | Mimosa deep scan `scan-2026-09-15T04-43-03.726Z-4bad20180460`（seal `sha256:bfeaf946…c5f2db31`，36 findings，coverage partial / inconclusive / verdictEffect none）逐条处置入 `docs/audits/PA1_MIMOSA_REVIEW.md`；`pytest -q tests/application/protocol_authoring/test_draft_service.py` = 13 passed（+4 反序列化防线） | PASS |
| WP-C | RECHECK-20260915-050（PASS_WITH_WARNINGS）；GOAL 收口判定与人工决策点登记；本地 m0 见表格；CI run #68 记账（5 job 绿 + collector-quality 持续失败） | PASS |

## 已知风险

- 守卫测试读的是源码文本（正则匹配条目键），重构 pageSupport 结构时需要同步调整；
  这是有意的——它锁的是"显式登记"这一事实。
- 扫描覆盖 partial 意味着"未发现"不等于"不存在"；处置记录必须带 coverage 口径。

## 状态历史

- 2026-09-15 由 GOAL cycle 10 派生（末轮收口），进入执行。
- 2026-09-15 三个 WP 落地；RECHECK-20260915-050 = PASS_WITH_WARNINGS；转 DONE。
  GOAL 因预算用尽 + EC-04/EC-06 阻塞项转 BLOCKED（人工决策点见 GOAL「终止与收口」）。

## 影响报告

- 改动：新增 `apps/web/tests/unit/page-support-coverage.test.ts`（EC-05 守卫 3 例）与
  `tests/application/protocol_authoring/test_draft_service.py` 4 例（`!!python/*` 标签
  拒绝 + loader 源码检查）；`docs/audits/PA1_MIMOSA_REVIEW.md` 追加收口扫描处置节；
  GOAL/ALL_PLAN/PLAN/RECHECK/MEM 治理记录。
- lint/typecheck/test：web unit 76/76、tsc 绿、eslint 0 error；python ruff check/format +
  mypy 绿；authoring 套件 13 passed；m0 23/23 PASS；全量 pytest 3336 passed / 6 skipped。
- Domain/API/schema：无 Domain/API/schema 变更（纯测试 + 文档 + 治理记录）。
- 安全/凭据：无凭据面变更；密封扫描处置**不宣称安全**（coverage partial、依赖 advisory 未复核）。
- 兼容性/迁移风险：无迁移。
- 上游版本影响：无新增依赖。
- 下一项任务：无（GOAL 转 BLOCKED；恢复条件由人工决策，见 GOAL「终止与收口」）。
