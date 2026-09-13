---
id: RECHECK-20260912-041
plan_id: PLAN-20260912-041
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-13
completed_at: 2026-09-13
reviewer: independent-review-agent + root-agent-gate-evidence
baseline_ref: 4b5283d
checked_head: 57feb37
---

# RECHECK-20260912-041 — 项目注册表与上下文切换独立复检

GOAL-20260912-001 cycle 1 派生计划的独立复检。复检代理对抗性核查（不采信
实现声明；实跑定向套件 + 逐路由 diff + 前端 grep 验证），根级收口门禁由主代理
以实际命令输出补全。判定 PASS_WITH_WARNINGS；两项 WARNING（F-1 收口时序、
F-2 AC 文案）在收口 commit 处置，无 BLOCKER。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260912-041-project-registry-and-switcher.md`
  （`parent_goal: GOAL-20260912-001`，EC-01）。
- 变更范围：`b55df92`（WP-A/WP-B 后端）、`9ba606e`（WP-C 前端 + 2 张
  design-fidelity 基线）、`57feb37`（命名门禁重命名 + 50 行函数拆分）。
- 边界：M18（成员/RBAC/租户隔离）零触碰；项目删除不提供（归档终态）；
  agents/memory/experiments 数据面保持全局并在 G2/CONTROL_PLANE_API 如实标注。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 域/Port/Store 实现完整（有界校验、KeyError、upsert）；默认项目 epoch 排序首位、PATCH 保 created_at；POST 自动落默认设置行；无 DELETE 路由；幽灵 404、归档幂等 200 | `pytest test_project_store + test_projects_api` = 13 passed；复检逐行核对 projects.py:28,43,71-74,93-107 | PASS |
| AC-02（WP-B） | runs 双路径（store/registry 回退）按项目过滤；settings 按项目精确（仅默认允许 examples 回退）；drafts create/list 归属路径项目、跨项目不可见有断言；`del project_id` 残留仅剩真实全局资源（memory/experiments/agents） | `pytest test_projects_api` 隔离断言全过；grep 复核 + docs 文案一致性 | PASS |
| AC-03（WP-C） | 6 client 无 PROJECT 硬编码（仅 activeProject 默认值）；security scan 字面 `localStorage.setItem` 门通过（preferences 同风格惰性访问器）；presentationPolicy 强制分支移除；恰 2 张基线重录（projects 翻面 + run-timeline 顶栏切换器）；死 fixture/旧命名文件清零 | `pnpm lint/typecheck` 干净、`pnpm test` 73/73、`test_security_scan` 6 passed、`git show --stat 9ba606e` 核对 | PASS |
| AC-04（WP-D） | openapi 再生零漂移（快照含 /projects×3 且复检复跑无 diff）；CONTROL_PLANE_API/CONSOLE_PAGE_MAP 与代码逐路由一致；m0 分组全绿（python 6：全量 pytest exit 0、0 failed；typescript 9；framework 8）；stub e2e 30/30、live e2e 11/11（含项目注册表链）；naming/source-limits 复跑 805 passed | 各输出见计划「证据」节；收口 commit 含快照与文档 | PASS |

## 警告与处置

1. **F-1（WARNING，收口时序）** 复检时 WP-D 产物（再生快照/文档/PLAN/GOAL）仍在
   工作树未提交——首个 push（→57feb37）单独会令 main 的 openapi 漂移门失败。
   处置：收口 commit 与修正一并提交后立即二次 push，以 GitHub Actions 终态为
   CI 权威判定（迭代日志记录 run 结论）。
2. **F-2（WARNING，AC 文案）** AC-01 原写「409 归档幂等」而实现为幂等 200
   （重复归档仅前移 updated_at）——文案已在收口修正为与实现一致；不为此加 409。
3. **F-3（INFO，已修）** project_settings_store 模块 docstring 残留「单条记录/
   只有 example-project」——收口更新为按项目精确读取语义。
4. **F-4（INFO，记录）** security_scan 门为字面串扫描，消息「不得持久化状态到
   localStorage」宽于其实现（preferences.ts 先例同为惰性访问器）；本批遵循既有
   模式，未改门禁措辞。
5. **F-5/F-6（INFO，正面）** 归属真实性与注册表语义逐行核对无误伤；文档无高估。
6. **环境** 全量组合下 tests/adapters/execution/test_gpu_oom_e2e 与 OTLP 4318
   存在既有顺序性 flake（单跑均通过；记忆配方在册），非本批产品缺陷；GHA
   （Linux、无操作员 .env）为 CI 权威。

## 结论

PLAN-20260912-041 AC-01~AC-04 全部满足；F-1/F-2/F-3 处置闭环。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-01 → PASS（待 CI run
终态盖章），cycle 2 输入：EC-02（reports/integrations/全局血缘经既有
deliverable/tool_plane/跨 run 投影的 HTTP 面 + 页面翻 live）。
