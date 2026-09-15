---
id: RECHECK-20260915-058
plan_id: PLAN-20260915-058
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-002-cycle4
baseline_ref: d350e8e
checked_head: d350e8e+worktree
---

# RECHECK-20260915-058 — 工作区快照文件树与文件级 Diff（GOAL-002 cycle 4 / EC-03）

## 检查范围

PLAN-20260915-058 声称的交付面：按 digest 寻址的只读快照读取（能力面/文件树/文件级 diff/
run 记录面）、读取器的安全边界（digest 白名单、根目录包含性、symlink 拒绝、未保留 404）、
未配置时 503、前端 `run/workspace` 的快照面板与标注收敛、`run-workspace` 设计基线。
其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 树枚举口径 | `tests/application/test_snapshot_tree.py`：只含常规文件、按路径排序、带大小与 sha256；symlink 不跟随（Windows 无权限时跳过而非假通过） | PASS |
| 不静默截断 | 同上：超过 `limit` 时 `truncated=True` 且只给前缀 | PASS |
| 文件级 diff 口径 | 同上：ADDED/REMOVED/CHANGED/unchanged 计数正确、按路径排序；**同长度改写也算 CHANGED**（按 sha256 而非 size）；相同快照 `identical=True` 且无 changes | PASS |
| 结构校验 | `SnapshotFile` 拒绝绝对路径与 `..`；`SnapshotChange` 要求 ADDED 只带右侧、REMOVED 只带左侧、CHANGED 两侧都存在且不同 | PASS |
| 读取器安全边界 | `tests/adapters/workspace/test_snapshot_reader.py`：7 种非法 digest（空、`sha256:` 空 hex、`../escape`、62/大写 hex、md5、路径穿越）全部 `InvalidInputError`；未保留 digest 拒绝；快照内 symlink → `PermanentPortError`；**只读 `.snapshots`，工作区目录内容读不到** | PASS |
| 未配置即 503 | `tests/api/test_workspace_snapshots_api.py`：能力面 `configured=false` + 原因；`/files` 503 且 detail 指明快照根 | PASS |
| 未保留不是空树 | 端点：未知 digest → 404 `Snapshot Not Retained`（不是 200 + 空清单）；非法 digest → 404 | PASS |
| run 面诚实口径 | 端点：只报 evidence 记录过的 digest + `EVIDENCE_BEFORE/AFTER` 来源 + `retained` 状态；同一 digest 两侧出现时只报一次且两个来源都在；未知 run → 404；响应带 `run-to-workspace binding` 注记 | PASS |
| 文件级（非内容）diff | 端点：`comparison=WORKSPACE_SNAPSHOT_METADATA`，changes 只含路径/kind/两侧 sha256 与大小，note 指向制品内容 diff | PASS |
| OpenAPI 快照一致 | `tools/gen_openapi.py` 重生成（+436 行）；`tests/contracts` **383 passed / 56 skipped**；新增四条路径断言 | PASS |
| 诚实标注同步 | `ArtifactDiffDto.note` 不再说"控制面没有文件系统快照 diff 面"，改为指向 `/workspace-snapshots/{left}/diff/{right}`；`REPRODUCTION_NOTE` 同步；`pageSupport.GAPS.fileBrowse` 收敛且 `run/workspace` 去掉 `disabledOperations`；`CONSOLE_PAGE_MAP` 的页面级与 G8 行同步 | PASS |
| 前端真的渲染这些事实 | stub e2e `workspace-snapshots.spec.ts` 4 用例：记录/保留计数与来源标签、文件树（路径/大小/2 files/352 B）、文件级差异（+1 / ~1 / unchanged 1，path/kind 都在）、未配置时显示原因且**不渲染空树** | PASS |
| 真实装配面同性质 | live e2e `live-workspace-snapshots.spec.ts` 4 用例（真实 uvicorn + 受控快照根）：能力面 configured/retained=2；run 记录的 digest → 文件树（路径与 total_bytes 自洽）；两快照 diff = 1 ADDED + 1 CHANGED + 1 unchanged；未保留 digest 404、未知 run 404 | PASS |
| 清单单一来源仍成立 | 新增 live spec 只改 `tests/e2e/live-specs.ts` 一处；`--list` 复核 stub **45 tests / 12 files**、live **25 tests / 6 files** | PASS |
| 设计基线 | `run-workspace` 的 win32（本地）与 linux（pinned noble 容器）重生成；两张基线目检：页面文案已含"工作区快照按 digest 只读（文件树 + 文件级 Diff）"，无裁列/溢出；design-fidelity 33 路由全绿 | PASS |
| 前端门禁 | 根 eslint 0 error（2 条既有 soft warning）；web lint/typecheck 通过；单测 76 passed；stub e2e **45 passed**；live e2e **25 passed** | PASS |
| Python 门禁 | 首跑 FAIL（`python/product-lint`：`tests/api/test_workspace_snapshots_api.py` 两行 101/102 字符）→ 修复后 **m0 = `profile=m0; 23 deterministic checks`** | PASS（先失败后修复） |
| 共享替身默认表的维护性 | 全量 stub 套件暴露 `workspace-diff.spec.ts` 的未替身请求（新面板必然调用 run 快照面）⇒ 默认路由补进 `stub-routes-workspace.ts`，而不是逐用例补丁 | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

交付面成立且可复核：快照只能按内容寻址 digest 读取，读不到就 404、没配置就 503，
文件级 diff 只谈路径/大小/sha256；run 面只回答"记录过哪些 digest、哪些还留着"，
不假装知道"该 run 的工作区长什么样"。前端把 digest、保留状态、文件树与差异原样呈现，
未配置时显示原因而不是空树。

本轮复核-修复循环又一次是**先红后绿**：m0 首跑被 `ruff` 拦下（测试文件两行超 100 字符），
全量 stub 套件被严格替身守卫拦下（新面板引入未替身请求）⇒ 前者改行、后者把默认路由补进
共享替身表。两处失败都如实记录，未掩盖。

## 告警

- W-1（无 run→工作区绑定）：持久面只有快照 digest 字符串（`Evidence.workspace_snapshot_before/after`），
  因此 run 面不能回答"这个 run 的工作区内容"，只能回答"它记录过哪些 digest"。想要更强的
  语义需要新增域记录（run↔workspace/lease 绑定），属独立决策。
- W-2（快照无保留策略）：`FileWorkspaceBackend` 不清理 `.snapshots/`，磁盘随运行增长；
  控制面读面把这一点暴露得更明显，但没有 retention 机制。属既有事实，本计划未改。
- W-3（digest 依赖执行链）：只有真正调用过 `snapshot()` 的执行链才会产出可读快照；
  Fake/演示链不产出 → 页面在演示数据上显示"该运行没有记录工作区快照 digest"（正确但空）。
- W-4（共享替身表接近硬上限）：`apps/web/tests/e2e/stub-routes.ts` 已 403 行（soft 300 /
  hard 450），本轮又加了 4 行；下次新增页面级默认路由前应先拆分该文件。
- W-5（继承，未处理）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）仍开放。

## 复现

```
# 纯函数 / 读取器 / 端点 / 契约
python -m pytest tests/application/test_snapshot_tree.py -q          # 8 passed（1 skipped: Windows symlink 权限）
python -m pytest tests/adapters/workspace/test_snapshot_reader.py -q # 12 passed（1 skipped: 同上）
python -m pytest tests/api/test_workspace_snapshots_api.py -q        # 11 passed
python -B tools/gen_openapi.py && python -m pytest tests/contracts -q # 383 passed
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm exec playwright test --list                       # 45 tests in 12 files
cd apps/web && pnpm exec playwright test --list --config playwrightLive.config.ts  # 25 tests in 6 files
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live            # 45 / 25 passed
# 设计基线（run-workspace；linux 在 pinned noble 容器内重生成）
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/run-workspace-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh run-workspace
# 本地门
sh scratch/run-m0-cycle12.sh                                          # profile=m0; 23 deterministic checks
```
