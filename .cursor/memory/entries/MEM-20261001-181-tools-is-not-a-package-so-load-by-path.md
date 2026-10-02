---
id: MEM-20261001-181
title: "`tools/` 不是包：静态 `tools.` 导入会让同一文件有两个模块身份（mypy 实测报 Source file found twice）⇒ 按路径加载是仓内既定做法"
status: ACTIVE
created_at: 2026-10-01
updated_at: 2026-10-01
scope: repository
confidence: 0.95
review_after: 2027-04-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261001-269-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261001-270-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md
supersedes: []
tags: [tools-dir, mypy, module-identity, in-scope-gate, goal-028, plan-269]
---

## 做了什么

GOAL-028 EC-02 给自建 MCP server 加一条活检索路：新模块落
`tools/research_mcp_live.py`，server 里用 `from tools.research_mcp_live import ...` 引用它。
`tests/tooling/test_tooling_scripts_meet_product_gates.py::test_in_scope_scripts_pass_mypy`
**实测判红**：

```text
tools\research_mcp_live.py: error: Source file found twice under different module names:
  "research_mcp_live" and "tools.research_mcp_live"
```

## 为什么这样做

`tools/` 目录里**没有 `__init__.py`** ⇒ 它不是一个包。mypy 对同一个 `.py` 见到两个
模块身份（顶层 `research_mcp_live` 与 `tools.research_mcp_live`）时直接报错并停止检查。
这不是「加个 `__init__.py` 就好」的问题：把 `tools/` 变成包会改变**所有**历史脚本的
导入语义与射程分类，代价远大于收益。判据要的是「这个脚本自身能过 mypy」，
而不是「换一种目录结构」。

## 怎么做与复现

- **按路径加载**（仓内既有先例，直接照抄形态）：`importlib.util.spec_from_file_location`
  + `module_from_spec` + `sys.modules[name] = module` + `exec_module`。
  见 `tools/verify_goal027_closeout.py::load_standard` 与
  `tools/research_mcp_server.py::_load_live_module`（后者还做了**幂等**：先查
  `sys.modules`，加载失败则 `pop` 回滚）。
- **给动态模块定形**：按路径加载拿到的是 `ModuleType`，mypy 看不到属性 ⇒ 会报
  `object has no attribute 'live_search'` 与 `no-any-return`。用 `typing.Protocol`
  把该模块的**结构面**写出来，再 `cast` 到它（本 EC 用 `_LiveModule`）。
- **另一条错路（别走）**：`tools/` 整目录 `ruff check` 会撞 **73 条历史 lint 错误**
  （`tools/` 的历史脚本多数不在 `IN_SCOPE`，承 GOAL-023 `W-1` 的有界射程）
  ⇒ 只能按 `IN_SCOPE` 清单**逐文件**跑四道门。
- 复现配方：`uv run --frozen --no-sync python -B -m pytest
  tests/tooling/test_tooling_scripts_meet_product_gates.py -q`（新脚本未进 `IN_SCOPE`
  时先红在 `test_scope_partitions_every_tools_script_explicitly`）。

## 适用边界

任何在 `tools/` 下**新增脚本**并在**另一个 `tools/` 脚本**里引用它的场合（本仓的
`IN_SCOPE` 清单会把新脚本纳入四道门 ⇒ 上面两条必踩）。**不适用于**：
① 测试从 `tools.X` 导入（`tests/` 在包内，`import tools.x` 只有一种身份 —— 但注意
`tests/contracts/test_mcp_research_server_loopback.py` 就是这么导入 `CORPUS` 的）；
② `tools/` 脚本引用 `packages/` / `adapters/`（那是真包，普通导入即可）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261001-269-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261001-270-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md`
- 先例：`tools/verify_goal027_closeout.py::load_standard`、`tools/research_mcp_server.py::_load_live_module`
