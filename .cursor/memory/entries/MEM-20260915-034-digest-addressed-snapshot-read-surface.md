---
id: MEM-20260915-034
title: 按 digest 寻址的只读宿主目录面：控制面读工作区快照的安全收窄
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2027-09-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-058-workspace-snapshot-tree-and-file-diff.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-058-workspace-snapshot-tree-and-file-diff.md
supersedes: []
tags:
  - workspace
  - snapshot
  - security-boundary
  - console
---

# 控制面读取宿主文件的收窄方式：只按内容寻址 digest

## 做了什么

`GET /workspace-snapshots/{digest}/files` 与 `/{left}/diff/{right}`（+ 能力面
`GET /workspace-snapshots`、run 面 `GET /runs/{id}/workspace-snapshots`）由
`adapters/workspace/snapshot_reader.py` 的 `FileSnapshotReader` 支撑：它只读
`<root>/.snapshots/<digest 的 hex>/`，把目录枚举成 (路径, 大小, sha256) 清单，
两份清单再经 `packages/application/workspace/snapshot_tree.py` 比成文件级差异。

## 为什么这样做

- 这是控制面**第一次**接触宿主文件系统。直接开"给我路径我读文件"的面等于开任意读；
  改成"只接受 `sha256:<64 hex>`、只在内容寻址目录里解析"后，调用方无法表达路径，
  路径穿越面从根上不存在。
- 快照存储是**内容寻址 + 不清理**的（`FileWorkspaceBackend.snapshot()` 写
  `root/.snapshots/<hex>/`，restore/merge 用同一字符串解析，没有任何删除逻辑），
  所以"digest → 目录"是稳定映射，读侧不需要 lease（读不写工作区）。
- 快照目录内出现 symlink 一律拒绝（`POLICY_DENIED`）：快照由拒绝 symlink 的写入侧
  产出，出现 symlink 即存储被污染，跟随链接就会读出宿主文件。
- 未配置根目录 → 端点 503（`RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT`），不猜默认路径、
  不用空树冒充"没有文件"。

## 怎么做与复现

```
python -m pytest tests/adapters/workspace/test_snapshot_reader.py -q   # 12 passed
python -m pytest tests/application/test_snapshot_tree.py -q            # 8 passed
python -m pytest tests/api/test_workspace_snapshots_api.py -q          # 11 passed
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live            # 45 / 25 passed
```

判据要点：非法 digest（非 `sha256:<64hex>`）与未保留 digest 都 404；只读 `.snapshots`
（工作区目录内容读不到）；文件级 diff 只比路径/大小/sha256（内容行级 diff 在制品侧）。

## 适用边界

- **没有 run→工作区绑定**：持久面只有 `Evidence.workspace_snapshot_before/after` 这类
  digest 字符串，所以 run 面只能回答"记录过哪些 digest、哪些仍保留"，不能回答
  "这个 run 的工作区长什么样"。
- 快照无保留策略（磁盘增长不受控）；空目录树 digest 与"未保留"是两回事，前者 200 + 空清单。
- 文件数超上限置 `truncated=true`（不静默截断成完整清单）。
- 想让页面看到文件级变化，前提是执行链真的产出了快照（`snapshot()/restore()`），
  而不是改进控制面。

## 来源

- PLAN-20260915-058 / RECHECK-20260915-058（GOAL-20260915-002 cycle 4 / EC-03）。
- 相关：[[MEM-20260915-033]]（同一"没有记录面就如实说"的收敛方式）、
  [[MEM-20260915-032]]（未连边清单同理）。
