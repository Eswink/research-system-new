---
id: MEM-20261001-180
title: "SDK 工具 registry 是进程级且只增不减：注册名对后续用例仍可解析 ⇒ 「缺实现」的反证必须用专属名字，不能靠换实现表"
status: ACTIVE
created_at: 2026-10-01
updated_at: 2026-10-01
scope: repository
confidence: 0.95
review_after: 2027-04-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261001-267-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261001-268-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md
supersedes: []
tags: [openhands-sdk, tool-registry, test-order, refutation, goal-028, plan-267]
---

## 做了什么

GOAL-028 EC-01 的反证二要证「绑定指向**装配方没有实现**的工具名 ⇒ 会话创建点名失败」。
首版把它写成「同一份协议 + 把实现表换成只含新名字」⇒ **实测 run 到 `SUCCEEDED`**（判据红）。

## 为什么这样做

「换掉实现表」看似等价于「这个名字没有实现」，但它假定**registry 里没有残留**。实际相反：
`register_tool` 只写入、无撤销 ⇒ 先前用例注册过的名字对整个进程**永久可解析**。
于是那条反证判的其实是「用例执行顺序」，而不是「装配方有没有实现」——**判据与它想证的事
脱钩**了。判据必须只依赖被测事实本身，因此要换一种**与进程历史无关**的构造方式。

## 怎么做与复现

- **反证要证「某名字没有实现」时，用一个别处从不使用的专属名字**
  （本 EC 用 `workspace.read.unwired`，写在专属协议 `tool_binding_unwired_v1.yaml` 里），
  而不是在同一进程里换表。专属名字让失败是**确定的**，与顺序无关。
- **反证要证「某名字**未注册**」时，必须在用例里显式把它从 registry 摘掉**
  （`registry._REG.pop(name, None)`）：否则同进程里别的判据（如
  `test_ec03_real_runtime_offline_chain.py` 的 `map_tools=True` 路径）**已经**把它注册成
  惰性替身 ⇒ 断言「它未注册」会**假绿**。本 EC 单跑该用例时绿、**全量 m0 时红**，
  正是这条：单跑进程干净、全量跑前面已污染。
- 复现配方：`uv run --frozen --no-sync python -B -m pytest
  tests/e2e/test_tool_binding_on_the_default_assembly.py tests/e2e/test_ec03_real_runtime_offline_chain.py
  -q -p no:randomly`（**合跑**才暴露顺序依赖；单跑会骗过你）。
  对照实现见 `openhands.sdk.tool.registry.register_tool` / `resolve_tool`
  （`_REG` 是模块级 dict，重复注册只 `logger.warning` + 覆盖）。
- 相关陷阱（同族）：**同一文件被两个模块名导入**会让 `Action` 子类被定义两次 ⇒
  "Duplicate class definition"；**函数内局部类**（`<locals>`）会毒化同进程事件 round-trip。
  两者都记在 `tests/e2e/live_run_support.py`。本条补充第三类：**注册名字的进程级残留**
  ——它有两个方向：让「没有实现」假绿（换表式反证），与让「未注册」假绿（不清理式反证）。

## 适用边界

本仓 `tools/`、`adapters/`、`tests/` 中任何「注册到进程级 registry 再按名解析」的判据
（OpenHands SDK 工具名、MCP 工具名等）都适用。**不是**产品缺陷：产品只在一次会话装配
里注册它自己用到的名字，进程级残留只会影响**同一进程内先后跑多个装配的判据**。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261001-267-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261001-268-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md`
- 事实：`openhands.sdk.tool.registry.register_tool` / `resolve_tool`（`.venv/Lib/site-packages/`）

