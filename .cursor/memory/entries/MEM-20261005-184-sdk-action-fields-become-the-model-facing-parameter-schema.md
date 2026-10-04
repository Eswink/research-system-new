---
id: MEM-20261005-184
title: "SDK 把 action 的字段渲染成模型可见的参数 schema ⇒ 自由形状工具必须平铺参数（包装字段会让真实工具调用撞 extra=forbid）"
status: ACTIVE
created_at: 2026-10-05
updated_at: 2026-10-05
scope: repository
confidence: 0.95
review_after: 2027-04-05
source_plans:
  - .cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261005-278-goal-029-ec01-session-tool-called-end-to-end.md
supersedes: []
tags: [openhands-sdk, tool-schema, session-tools, silent-reject, goal-029, plan-277]
---

## 做了什么

GOAL-029 cycle 2 实测到：`SessionToolAction` 原声明一个 `arguments: dict` **包装字段**，
于是 SDK 渲染出的**模型可见**参数 schema 是 `{"arguments": {...}, "kind": {...}}` ⇒
模型必须把真实参数嵌进那一层；而任何按常理构造的工具调用（`{"artifact_id": "x"}` 平铺）
都撞 base `Schema` 的 `extra="forbid"`，得到
`Error validating tool 'artifact.read': Extra inputs are not permitted` ——
**工具调用到达了桥，却在校验处被拒**（失败形态是 `AgentErrorEvent`，会话照常收尾 ⇒
run 终态仍是 `SUCCEEDED`）。

## 为什么这样做

SDK 把 `ToolDefinition.action_type` 的字段当作**该工具的参数声明**（`model_json_schema()`
的 `properties` 直接成为模型看到的 arguments）。因此「一个 dict 收全部参数」这种在 Python
里很自然的写法，在工具面就变成「模型被告知有一个叫 `arguments` 的对象参数」——
与真实模型的工具调用约定（参数平铺）不一致。SDK 自己的内建工具一律平铺：
`ThinkAction.thought` / `FinishAction.message` / `InvokeSkillAction.name`。

## 怎么做与复现

- 自由形状（参数由 provider 契约决定）的工具写法：
  `model_config = ConfigDict(extra="allow", frozen=True)` + 用 `model_extra` 读参数。
  实测 schema 随之变成 `additionalProperties: true` 且无包装字段。
- 复现：`uv run --frozen --no-sync python -B -m pytest
  tests/e2e/test_session_tool_call_on_the_default_assembly.py -q -p no:randomly`；
  按压（把包装字段放回）⇒ 5 failed。
- **判据的存在性本身要取证**：这条缺陷长期不可见的原因是**仓内没有任何会发 `tool_calls`
  的夹具**（既有 e2e mock 一律只回文本）⇒「会话起得来」被当成了「工具跑得动」。
  本轮新增的判据里有一条专门断言「本文件是仓内唯一发工具调用的夹具」，出现第二个即判红。
- 想看到工具的**真实调用失败**，必须读 SDK 的原始事件（`conversation.state.events` 里的
  `AgentErrorEvent`），**不能**只看 run 终态或 adapter 投影的事件种类。

## 适用边界

本仓所有经 OpenHands SDK 暴露的工具（会话工具、未来经 `Tool` 装配的其他实现）都适用。
**不**适用于纯 Python 侧调用（那里 `arguments` 是个普通字段）。
注意 `SessionToolAction.arguments` 现在是**方法**而非字段 —— 按属性读取会拿到绑定方法。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261005-278-goal-029-ec01-session-tool-called-end-to-end.md`
- 事实：`openhands.sdk.tool.schema.Schema`（`model_config = ConfigDict(extra="forbid")`）、
  `openhands.sdk.tool.builtins.{think,finish,invoke_skill}` 的 action 形状、
  `adapters/openhands/session_tools.py` 的 `SessionToolAction`
