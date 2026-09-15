---
id: PLAN-20260915-058
slug: workspace-snapshot-tree-and-file-diff
title: 工作区快照文件树与文件级 Diff（G8）：按 digest 寻址的只读控制面
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 4 = EC-03（G8 workspace 文件树 + 文件级快照 Diff）。授权来源同 GOAL-20260915-002：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-058-workspace-snapshot-tree-and-file-diff.md
memory_entries:
  - MEM-20260915-034-digest-addressed-snapshot-read-surface
---

# PLAN-20260915-058 — 工作区快照文件树与文件级 Diff（GOAL-002 cycle 4 / EC-03）

## 目标

把 `run/workspace` 页的最后一条诚实缺口（"工作区文件树与文件级快照 Diff 无 API"）变成真实能力：
新增**按快照 digest 寻址**的只读控制面——run 已记录的快照清单、单个快照的文件树、两个快照之间的
**文件级** diff（新增/删除/内容变化，带两侧大小与 sha256）——并在页面上接入。

## 背景（已核实的事实，决定了本计划的形状）

- `WorkspaceBackend` Port（`packages/application/ports/workspace_backend.py`）只有
  create/lease/snapshot/restore/merge/bundle，**没有枚举或读取能力**。
- `FileWorkspaceBackend`（`adapters/workspace/file_backend.py`）的快照是**内容寻址**的：
  `root/.snapshots/<digest 的 hex>/`，digest 就是 `bundle.tree_digest()` 的 `sha256:<hex>`；
  `restore()`/`merge()` 用同一个字符串解析；**没有任何清理逻辑删除快照**（保留即可枚举）。
- run 侧唯一被持久化的是**快照 digest 字符串**：`Evidence.workspace_snapshot_before/after`、
  `ExperimentRunResult.workspace_snapshot_before/after`。**没有** run→workspace 实例的持久绑定，
  所以"某个 run 的工作区目录"不可从记录还原；能还原的是"这个 run 记录过哪些快照 digest"。
- 控制面（`ApiDeps`）当前**完全没有** workspace 接缝：不构造任何 workspace backend，
  `workspace_backends` 配置只进展示用 catalog。既有先例：artifact store 未配置 → 503。

## 口径（诚实边界，先写清楚再写代码）

1. **只按 digest 寻址，不接受路径**：路径参数只有 digest，且必须匹配 `^sha256:[0-9a-f]{64}$`
   才触碰文件系统——控制面不提供"读宿主任意目录"的面。
2. **只能读保留中的快照**：未被保留（磁盘上没有该 digest 目录）→ 404 + `NOT_RETAINED`，
   不凭空重建、不用工作区当前内容冒充快照。
3. **不猜 run→工作区**：`GET /runs/{id}/workspace-snapshots` 只返回**该 run 记录过的 digest**
   （before/after，含来源）与每个 digest 的 `retained` 状态；不推断"这一定是它执行时的工作区"。
4. **文件级 diff 只比元数据**：路径 + 大小 + sha256 → ADDED/REMOVED/CHANGED；**不做内容行级 diff**
   （内容 diff 已由制品侧 `GET /artifacts/{a}/diff/{b}` 提供，两者不混用、不互相冒充）。
5. **超限如实标注**：文件数超过上限 → `truncated=true`（不静默截断成"完整清单"）。
6. 未配置快照根 → 503 + 原因（与 artifact store 未配置同口径）；不伪装空树。

## 范围

- 应用（纯函数）：`packages/application/workspace/snapshot_tree.py`（树枚举 + 快照间文件级 diff）。
- Port：`packages/application/ports/workspace_snapshot.py`（`WorkspaceSnapshotReader` 独立能力协议，
  不改动既有 `WorkspaceBackend` 契约）。
- 适配器：`adapters/workspace/snapshot_reader.py`（`FileSnapshotReader`：root/.snapshots/<hex>，
  digest 白名单 + 根目录包含性 + symlink 拒绝）。
- API：`services/api/dto/workspace_snapshots.py`、`services/api/mappers/workspace_snapshots.py`、
  `services/api/routers/workspace_snapshots.py`、`services/api/composition.py`（装配 reader）、
  `services/api/settings.py`（`RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`）、`services/api/app.py` 注册。
- 前端：`apps/web/src/features/workspace/WorkspaceSnapshotPanel.tsx` + `WorkspaceView.tsx` 接线、
  `apps/web/src/api/{types,operationsClient,client}.ts`、`pageSupport.ts`（`GAPS.fileBrowse` 收敛、
  `run/workspace` 的 disabledOperations 清空）。
- 测试：`tests/application/test_snapshot_tree.py`、`tests/adapters/workspace/test_snapshot_reader.py`、
  `tests/api/test_workspace_snapshots_api.py`、`tests/contracts/test_openapi_snapshot.py` 断言、
  stub e2e `apps/web/tests/e2e/workspace-snapshots.spec.ts`、live e2e
  `apps/web/tests/e2e/live-workspace-snapshots.spec.ts`（+ `live-specs.ts` 登记，验证上一轮的单一来源）。
- 文档/基线：`docs/api/openapi.m13.json` 重生成、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `run/workspace` 路由的 win32 + linux 设计基线。

## 验收条件

- [x] AC-01：纯函数口径正确——树枚举只含常规文件（symlink 不跟随）、按路径排序；
      文件级 diff 给出 ADDED/REMOVED/CHANGED 且两侧 sha256/大小齐备；相同内容不算变化；
      超上限置 `truncated`。`tests/application/test_snapshot_tree.py` 全绿（8 passed + 1 skipped）。
- [x] AC-02：读取器安全边界——非法 digest（非 `sha256:<64hex>`）拒绝、不存在的 digest 明确
      `NOT_RETAINED`、快照目录内的 symlink 被拒绝、根目录之外的路径不可达、工作区目录不可读。
      `tests/adapters/workspace/test_snapshot_reader.py` 全绿（12 passed + 1 skipped）。
- [x] AC-03：API 交付——`GET /workspace-snapshots`（能力/计数或未配置原因）、
      `GET /workspace-snapshots/{digest}/files`（404 = 未保留）、
      `GET /workspace-snapshots/{left}/diff/{right}`、`GET /runs/{run_id}/workspace-snapshots`
      （run 已记录 digest + `retained` 状态 + 来源）。未配置 → 503。`tests/api/test_workspace_snapshots_api.py` 11 passed。
- [x] AC-04：OpenAPI 快照含四条新路径（重生成 +436 行 + 契约断言；`tests/contracts` 383 passed）。
- [x] AC-05：前端 `run/workspace` 渲染 run 快照清单、文件树与文件级 diff；未配置/未保留显示原因；
      `GAPS.fileBrowse` 收敛且 `disabledOperations` 清空；stub e2e 4 用例、live e2e 4 用例绿。
- [x] AC-06：`run/workspace` 设计基线 win32 + linux 重生成并目检。
- [x] AC-07：本地 m0 = `profile=m0; 23 deterministic checks`（首跑红于 ruff 行长，修复后复跑）。

## 实施清单

- [x] WP-A 纯函数（树 + 文件级 diff）+ 单测
- [x] WP-B Port + FileSnapshotReader + 适配器用例
- [x] WP-C DTO/mapper/router/settings/composition + API 用例 + OpenAPI 快照
- [x] WP-D 前端面板与接线 + stub/live e2e + live-specs 登记 + 共享替身默认路由
- [x] WP-E 文档、设计基线、RECHECK-058、GOAL/ALL_PLAN/记忆记账、m0、CI

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/application/test_snapshot_tree.py -q` → **8 passed / 1 skipped**（含"同长度改写也算 CHANGED""超限置 truncated""ADDED 只带右侧"） | PASS |
| WP-B | `pytest tests/adapters/workspace/test_snapshot_reader.py -q` → **12 passed / 1 skipped**（7 种非法 digest、未保留、symlink 拒绝、工作区目录不可读） | PASS |
| WP-C | `pytest tests/api/test_workspace_snapshots_api.py -q` → **11 passed**（503/404/200 三态、来源标签、retained 状态、metadata-only diff） | PASS |
| WP-C | `tools/gen_openapi.py` 重生成（+436 行）；`pytest tests/contracts -q` → **383 passed / 56 skipped** | PASS |
| WP-D | stub e2e：`workspace-snapshots.spec.ts` 4 用例通过；全量 stub 套件 **45 passed**（同时暴露并修复 `workspace-diff.spec.ts` 的未替身请求） | PASS |
| WP-D | live e2e：`live-workspace-snapshots.spec.ts` 4 用例通过（真实 uvicorn + 受控快照根）；全量 live 套件 **25 passed** | PASS |
| WP-D | 根 `pnpm exec eslint .` = 0 error；web lint/typecheck 通过；web 单测 76 passed | PASS |
| WP-E | 基线：`run-workspace` win32（本地）+ linux（pinned noble）重生成并目检；design-fidelity 33 路由全绿 | PASS |
| WP-E | 本地 m0 首跑 **FAIL**（`python/product-lint` 两行超 100 字符）→ 修复后 = `profile=m0; 23 deterministic checks`；RECHECK-058 = PASS_WITH_WARNINGS | PASS |

## 已知风险

- 控制面首次接触宿主文件系统：靠"只接受 digest + 内容寻址根 + 包含性/符号链接拒绝"收窄，
  但仍需在 RECHECK 里明确这是**配置开启**的能力（未配置即 503）。
- run→工作区不可还原：本计划只交付"记录过的 digest 可枚举/可比"，不假装能回答
  "这个 run 的工作区长什么样"。
- 快照无保留策略：磁盘增长不受控（历史事实，本计划不改 retention；登记为告警）。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 4，取 EC-03（G8）。
- 2026-09-15 WP-A/WP-B 完成：纯函数（树 + 文件级 diff）8 passed、读取器 12 passed；
  安全边界（digest 白名单 / 根包含性 / symlink 拒绝 / 未保留 404）逐条有用例。
- 2026-09-15 WP-C 完成：DTO/mapper/router/settings/composition 装配；API 11 passed；
  OpenAPI 快照重生成 +436 行，契约 383 passed；`ArtifactDiffDto.note` 与
  `REPRODUCTION_NOTE` 的"无快照 diff 面"表述同步收敛。
- 2026-09-15 WP-D 完成：`WorkspaceSnapshotPanel` 接入 `run/workspace`；stub 4 用例 +
  live 4 用例绿（live 侧由 `console_api_app` 建临时快照根与受控 run）；live 清单仅在
  `tests/e2e/live-specs.ts` 加一项。
- 2026-09-15 WP-D 修复：全量 stub 套件暴露 `workspace-diff.spec.ts` 未替身的新请求
  ⇒ 默认路由进 `stub-routes-workspace.ts`（共享替身表，不是逐用例补丁）。
- 2026-09-15 WP-E 完成：文档与 G8 行收敛；`run-workspace` 双平台基线重生成并目检；
  m0 首跑红于 ruff 行长（测试文件两行）→ 修复后 23/23；RECHECK-058 = PASS_WITH_WARNINGS。

## 影响报告

- 改动：新增 `packages/application/workspace/snapshot_tree.py`、
  `packages/application/ports/workspace_snapshot.py`（独立能力协议，不改既有 Port 契约）、
  `adapters/workspace/snapshot_reader.py`（+ `adapters/workspace/__init__` 导出）、
  `services/api/{dto,mappers,routers}/workspace_snapshots.py`、
  `apps/web/src/api/workspaceSnapshotClient.ts`、
  `apps/web/src/features/workspace/{WorkspaceSnapshotPanel.tsx,workspaceSnapshotColumns.tsx}`、
  `apps/web/tests/e2e/{workspace-snapshots.spec.ts,live-workspace-snapshots.spec.ts,
  stub-routes-workspace.ts}`、5 组 Python 用例；修改 `services/api/settings.py`
  （`workspace_snapshot_root` / `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`）、
  `services/api/composition.py`（ApiDeps + 装配）、`services/api/app.py`（注册路由）、
  `services/api/dto/artifacts.py` 与 `routers/experiments.py`（诚实标注收敛）、
  前端 `api/{client,types}.ts`、`WorkspaceView.tsx`、`navigation/pageSupport.ts`、
  `tests/e2e/{stub-routes.ts,live-specs.ts}`、`tests/api/console_api_app.py`（live fixture）、
  `docs/api/openapi.m13.json`、`docs/frontend/CONSOLE_PAGE_MAP.md`、`run-workspace` 基线 ×2 平台。
- lint/typecheck/test：Python m0 全量 23/23（首跑红于 ruff 行长，修复后复跑）；
  纯函数 8 + 读取器 12 + API 11；契约 383 passed；前端 lint/typecheck 通过、
  单测 76 passed、stub e2e 45 passed、live e2e 25 passed；design-fidelity 33 路由绿。
- Domain/API/schema 变化：**新增四条只读端点**（`GET /workspace-snapshots`、
  `/workspace-snapshots/{digest}/files`、`/workspace-snapshots/{left}/diff/{right}`、
  `GET /runs/{run_id}/workspace-snapshots`）+ 新设置项 `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`。
  无数据库迁移；既有响应形状未变（仅 `ArtifactDiffDto.note` / `reproduction_note` 文案更新）。
- 安全/凭据变化：控制面首次读取宿主目录——收窄为"只接受 `sha256:<64hex>` digest、
  只在 `<root>/.snapshots` 内解析、symlink 一律拒绝、未配置即 503"；无新凭据面。
- 兼容性/迁移风险：未配置 `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT` 的部署行为不变（503）；
  配置后方可读快照存储；快照目录无 retention（既有事实，登记为 RECHECK-058 W-2）。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 5 = EC-04（G7 ops 写面：告警规则 CRUD + incident
  declare/assign/close），子 PLAN 编号 = PLAN-20260915-059。
