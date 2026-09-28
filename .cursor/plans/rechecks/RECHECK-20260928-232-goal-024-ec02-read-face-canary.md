---
id: RECHECK-20260928-232
slug: goal-024-ec02-read-face-canary
title: GOAL-024 EC-02 复检（读面一半）：68 条读路由逐条分区 + canonical 非空真 + 声明载体正控制 + 零命中 + 两向反证与按压
plan_id: PLAN-20260928-231
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-232 — GOAL-024 EC-02 读面复检

**复检口径**：不复用 PLAN 叙述；每条结论给出**可复核的观察面**（命令 / 数值 / 源码位置）；
**未实跑的不记通过**；警告逐条留位，不改产品代码来"消警告"。

## 检查结果

### 1. 分区与上下界（AC-1）
- `read_routes(app)` 走**应用自己的路由树**（FastAPI 新版把 `include_router` 包成
  `_IncludedRouter`，必须递归 `original_router`）⇒ **68** 条 GET 叶子。
- 清单 `read_face_route_registry.py` 逐条登记：**声明载体 15 / 零命中 53**，路径集合与树**逐条对齐**。
- 四条判红（未分类 / 重复 / 陈旧 / 理由为空）+ 两条上下界（声明面 ≤ 15、零命中面 ≥ 45）
  都在 `partition_findings` 里；`test_a_stale_registry_entry_is_red` /
  `test_unclassified_path_is_red` / `test_an_unregistered_read_route_is_red`（**真实应用**上
  新增 `/__press-probe`）三条按压逐条实跑判红。
- **观察**：`unclassified` 那条按压若把新路由也登记进清单就会变绿 —— 所以上界是关键：
  只要有人想靠"把它标成声明内容"消红，`len(DECLARED_CONTENT) > 15` 立刻判红。

### 2. 零命中与空真防护（AC-2）
- **先证 canonical 有内容**：直接读存储对象（草稿记录 / 制品 store / ledger claim）⇒
  `prompt` / `artifactbody` / `evidencebody` 三种金丝雀**都在**；不满足则判据判红。
- 零命中实取：**51 / 53** 条取到非空响应（另 2 条 `workspace-snapshots` 无对象 ⇒ 逐条登记）；
  实测**零越界**。
- 值得一提的三条硬观察：`/projects/{project_id}/protocol-drafts`（契约明文"不含正文"）零命中；
  `/runs/{run_id}/artifacts`（制品**列表**只给 id/digest/size）零命中；`/runs/{run_id}` 详情
  只有 digest 与判词、**没有**冻结正文 ⇒ 零命中。

### 3. 声明载体正控制（AC-3）
- 9 条声明载体（草稿视图 / 草稿修订 ×2 / 制品正文 / 制品 diff / claims / export /
  run 级 lineage / 项目级 lineage）**逐条实取并看到**它声明的内容 ⇒ 白名单没有说谎。
- 6 条声明载体本轮**没有正控制**（模板目录与模板详情 / 记忆 / 交付物 / 库列表与库详情）：
  夹具里没有这些对象。**逐条登记**在清单 `note` 里，不静默。

### 4. 两向反证与七源登记（AC-4）
- 零命中路由出现金丝雀 ⇒ `verify_route` 判红并打印 `路径 + 命中 kind`（合成输入实跑）。
- 声明载体看不到声明内容 ⇒ 同样判红（白名单不能靠"什么都不返回"过关）。
- 七源注入面**逐条登记**：`prompt_text` / `artifact_body` / `evidence_body` **注入**；
  `task_input` / `tool_arguments` / `tool_output` / `failure_message` **在默认离线链上没有注入面**
  （理由见判据源码 `CANARY_SOURCE_INJECTION`）。

### 5. 门与既有判据（AC-5）
- `ruff check` = `All checks passed!`；`ruff format --check` = 3 files already formatted；
  规模 = 294 / 294 / 200 行，最长函数 35 / 11 / 22 行；`mypy` = `Success: no issues found in 3 source files`。
- 既有隐私判据**逐字节未改**（`test_privacy_canary.py` / `canary_source_support.py` /
  `test_privacy_exit_census.py` 均只读复用）；`tests/observability/` 全目录实跑见 GOAL 迭代日志。
- as-is m0 与 CI 台账见 GOAL-024 迭代日志 cycle 3 行（**记录写入之后**跑的终态行）。

## 结论

**PASS_WITH_WARNINGS**。读面这一半补齐了：68 条读路由**逐条分区**、canonical 有内容的前提下
**零越界**、9 条声明载体**真的看得到内容**、两向反证与两向按压都有牙。EC-02 的读面
`NOT_YET_OBSERVED` 登记就此关闭。

**警告（逐条留位，不在本轮"消警告"）**：

- `W-1` **`label` 字段名与内容语义不一致**：`/runs/{run_id}/lineage` 与
  `/projects/{project_id}/lineage` 的 `LineageNodeDto.label` **实测**取自 claim statement
  （正文）。本轮据实登记为**声明载体**；但字段名（`label`）不表达"这是内容"，
  将来若有人按字段名推断"label 不含内容"，这两条会被误判为零命中面。**未改产品代码**。
- `W-2` **四个源在默认离线链上没有注入面**（`tool_arguments` / `tool_output` /
  `failure_message` / `task_input`）⇒ 这四个源的"不出现在非 canonical 出口"**未验证**
  （不是判绿，而是**没有可注入的载体**）。真实 runtime / 工具面一旦启用，需要重新取证。
- `W-3` **6 条声明载体本轮无正控制**（模板 / 记忆 / 交付物 / 库）：内容面未观测。
- `W-4` **3 条路由本轮取不到**（2 条零命中：workspace 快照文件树与快照 diff；1 条声明载体：
  `/library/{resource_id}`）——逐条登记，不算通过。
- `W-5` **扫描面只覆盖响应体文本**：响应头（`Content-Disposition` 文件名、`ETag` 等）不在面上；
  本轮没有观测到头部携带内容的路径，但也**没有**机械证明头部不含内容。
- `W-6` **白名单是人工判定 + 机械自审**，不是从契约自动推导：语义错漏靠"上下界 + 字段名反例
  （W-1）"部分兜住，**不能**宣称覆盖所有语义可能。
- `W-7` 端到端自举（两树复检 / 收口验证器进树）仍待 **EC-04**。
- `R-M1` **仍未收口**：本文件不对项目整体安全性作任何声明。
