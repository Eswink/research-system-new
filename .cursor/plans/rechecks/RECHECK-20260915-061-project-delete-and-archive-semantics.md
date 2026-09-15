---
id: RECHECK-20260915-061
plan_id: PLAN-20260915-061
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-002-cycle7
baseline_ref: 692ef19
checked_head: 692ef19+worktree
---

# RECHECK-20260915-061 — 项目删除语义（GOAL-002 cycle 7 / EC-06）

## 检查范围

PLAN-20260915-061 声称的交付面：`ProjectStore` / `ProjectSettingsStore` 的删除方法、
`DELETE /projects/{project_id}` 的判定顺序与引用聚合、OpenAPI 快照与写方法断言、
前端删除动作与 `pageSupport` 收敛、stub/live e2e、`portfolio-projects` 设计基线、
文档两处同步。其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 无引用即删除 | `test_delete_unreferenced_project_removes_row_and_settings`：DELETE 204 → `GET /projects` 不含该 id、`GET /projects/{id}/settings` 404（注册行与设置行一起消失） | PASS |
| **被引用即拒绝，不级联** | 4 条用例分别用 runs（store 与 run_registry 两条路径）、协议草稿、ops 记录制造引用：DELETE **409** 且 detail 形如 `project <id> still references: runs=1`；断言删除失败后 `runs_store.list_runs(project_id)` 等**仍有数据** | PASS |
| 默认项目不做静默 no-op | `test_delete_refuses_default_project`：DELETE `example-project` → **409 `Project Reserved`**（不是 204 假装成功，也不是 404 假装不存在） | PASS |
| 未知 id / 未装配 | `test_delete_requires_store`（`deps.project_store=None` → 503）；幽灵 id → 404；`delete_project` 对 rowcount=0 抛 `KeyError` → 路由转 404（读时在、删时没了不伪装成功） | PASS |
| 存储层不做级联决策 | `ProjectStore.delete_project` 只执行 `DELETE FROM projects WHERE project_id=?` + `_record`；`ProjectSettingsStore.delete` 幂等（rowcount 记进事件）；"是否允许删"与原因全在路由层 | PASS |
| 引用聚合只报能证实的项 | `_references()` 仅枚举项目作用域存储（runs/drafts/experiment_queue/library/ops_rules/ops_incidents），run 的从属事实由 `runs=N` 代表，刻意不重复计数（路由 docstring 写明） | PASS |
| OpenAPI 快照一致 | `python -B tools/gen_openapi.py` 重生成：**+34 行，仅新增 `/projects/{project_id}` 的 delete 操作**（无既有路径/DTO 改动）；快照自恰测试通过 | PASS |
| EC-06 验证项落成断言 | 新增 `test_openapi_contains_project_delete_method`：路径 + 写方法子集（`/projects` get/post、`/projects/{project_id}` patch/delete），并断言 delete 的 schema 描述里含 `409` 与 `级联` 字样（口径写在契约里，不只写在记录里） | PASS |
| 前端能删且会拒绝 | stub e2e 4 用例：默认项目按钮 `disabled` + title 说明；引用项目确认后 409 detail（`still references: runs=2, drafts=1`）**呈现在行内且行保留**；无引用项目删除后行消失（列表真的重新加载）；删除活动项目后 `localStorage['ros.active-project']` 回退为默认项目 | PASS |
| 真实装配面同性质 | live e2e `live-project-registry.spec.ts` 2 用例（真实 uvicorn HTTP）：默认项目 409 `Project Reserved`；新建项目挂草稿后 DELETE 409（detail 含 `drafts=1`）且设置面仍 200；空项目 DELETE 204 → 设置面 404 → 再删 404 | PASS |
| 替身与后端同因果 | `stub-routes-projects.ts` 接管 `GET/POST/PATCH/DELETE /projects`（原静态三条删除）：创建真的进列表、归档真的改状态、删除真的移出、`proj-funded-study` 带引用清单必 409、默认项目 409、未知 404；`resetProjectsStub()` 每用例复位 | PASS |
| 清单单一来源仍成立 | 新增 live spec 只改 `tests/e2e/live-specs.ts` 一处；`--list` 复核 stub **59 tests / 15 files**、live **31 tests / 9 files** | PASS |
| 全量回归 | `pytest tests/api -q` → **361 passed**；契约 **359 passed, 56 skipped**；stub e2e **59 passed（15 files）**；live e2e **31 passed（9 files）**；web 单测 **76 passed** | PASS |
| 设计基线 | `portfolio-projects` 的 win32（本地）与 linux（pinned noble 容器）重生成并目检：两行项目各带归档/删除动作、默认项目删除按钮呈禁用态、无溢出/裁列 | PASS |
| 前端门禁 | 根 `npx eslint .` = 0 error（1 条既有 soft warning：`live-api-workflow.spec.ts` 400 行）；web `tsc --noEmit` 通过；`ProjectDeleteAction` 首次报 60 行超 50 上限 → 抽出 `useProjectDeletion.ts`（hook 文件名与导出同名，过命名门禁） | PASS（先失败后修复） |
| Python 门禁 | 本地 m0 首跑 `FAILED [framework/validate]`：`工程记忆来源不存在: MEM-20260915-037`（本轮先写记忆条目、后写计划/复检文件）→ 补齐 PLAN-061 + RECHECK-061 后复跑 = `profile=m0; 23 deterministic checks` | PASS（先失败后修复） |
| 轮内自证的边界（第三次复现） | `scratch/cycle7-baseline-drift/measure.py` 按 Playwright 判据量化"HEAD 基线 vs 重生成后"：win32 **0.48%**、linux **0.47%**，低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁不会报警（见 W-1） | PASS（含告警） |

## 结论

result: **PASS_WITH_WARNINGS**

EC-06 的判定标准成立：`docs/api/openapi.m13.json` 里有真实的 `DELETE /projects/{project_id}`
写方法（新增断言把它与"409/不级联"的口径一起锁定在契约里），项目页的
`disabledOperations: ["delete"]` 已删除、`GAPS.multiProject` / `GAPS.delete` 收敛为
"删除只对无引用项目可用"，且这一页真的能删——替身与 live 两条链都验证了
"被引用 409（列出引用）+ 无引用 204（列表真的变化）+ 默认项目 409 + 再见 404"。

本轮的关键判断是**删除的默认答案是拒绝**：控制面能删的是**注册行**，删不掉的是
用户的研究数据。因此 `_references()` 只枚举能证实的项目作用域存储并逐项计数，
存储层不级联、路由层给出原因；对合成行（`example-project`）不接受"删了也还在"的
静默成功，而是 409 + 说明。这三点合起来让"有删除"不会退化成"多了个能删数据的按钮"。

门禁先红后绿一次（治理校验拦下"记忆来源文件缺失"），原因是本轮先把记忆条目写进树、
计划与复检文件在其后落盘；不是门禁本身的问题，如实记录。

## 告警

- W-1（**设计门禁的容差盲区**，第三次实测）：`portfolio-projects` 新增整行项目与逐行
  删除动作后，旧基线只差 0.48%（win32）/ 0.47%（linux），阈值 2% ⇒ 门禁不会变红。
  与 cycle 3（1.73%）、cycle 5（1.02%/0.93%）、cycle 6（0.79%/0.66%）同类；
  "页面改动必须主动重生成基线并目检"仍是流程要求。量化脚本：
  `scratch/cycle7-baseline-drift/measure.py`（从 `git show HEAD:` 取旧基线）。
- W-2（**替身守不住 Idempotency-Key**，本轮做了反证）：`DELETE` 属 mutating 方法，
  中间件要求 `Idempotency-Key`（缺失 422），但 `tests/e2e/stub-api.ts` 只按
  `method + path` 匹配、不校验请求头。反证：把 `projectsClient.remove` 的
  `{ idempotencyKey }` 去掉后 `project-delete.spec.ts` **4 passed**（随后已还原并复跑 4 passed）
  ⇒ 该约束只有 live 套件（真中间件）能守；新增 mutating 调用时不能只看 stub 结果。
- W-3（引用计数有上限）：草稿计数走 `_DRAFT_SCAN_LIMIT = 200`（`list()` 是分页接口），
  项目草稿超过 200 时清单里的数字封顶；"是否 409"的判定不受影响（>0 即拒绝），
  但 detail 的数字不能当作精确计数。
- W-4（不做跨项目引用检查）：引用枚举全部按 `project_id` 过滤；若将来出现跨项目引用
  （共享数据集/共享提示词），需要新的引用面。本轮不预置，避免猜边。
- W-5（活动项目回退是前端行为）：后端无"当前项目"概念；在另一个标签页删掉当前活动
  项目时，本标签页上下文仍指向已删 id（读面 404，不会静默返回别的项目数据）。
- W-6（继承，未处理）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）、
  RECHECK-060 W-2/W-3/W-4（capabilities 非授权边界 / pin 只校验形态 /
  健康复核无 schema 漂移比对）仍开放。
- W-7（live 套件文件规模）：`live-api-workflow.spec.ts` 逼近 450 行硬上限，本轮把项目链
  拆到 `live-project-registry.spec.ts`；后续新增 live 用例优先新开文件并只在
  `live-specs.ts` 登记一处（否则 stub 套件会把 live 文件收进来去连真实后端）。

## 复现

```
# 域 / API / 契约
python -m pytest tests/api/test_projects_api.py -q                      # 13 passed（7 条删除语义）
python -m pytest tests/api -q                                           # 361 passed
python -B tools/gen_openapi.py && python -m pytest tests/contracts -q    # 359 passed, 56 skipped
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm exec playwright test --list                          # 59 tests in 15 files
cd apps/web && pnpm exec playwright test --list --config playwrightLive.config.ts  # 31 tests in 9 files
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live               # 59 / 31 passed
cd apps/web && pnpm test                                                # 76 passed
# 设计基线（portfolio-projects；linux 在 pinned noble 容器内重生成）
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/portfolio-projects-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh portfolio-projects
# 门禁漂移量化（HEAD 基线 vs 重生成，Playwright 判据）
python scratch/cycle7-baseline-drift/measure.py                          # 0.48% / 0.47% ⇒ 不报警
# 本地门
sh scratch/run-m0-cycle12.sh                                             # profile=m0; 23 deterministic checks
```
