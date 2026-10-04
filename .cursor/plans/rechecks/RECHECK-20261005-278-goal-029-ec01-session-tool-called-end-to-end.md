---
id: RECHECK-20261005-278
slug: goal-029-ec01-session-tool-called-end-to-end
title: GOAL-029 EC-01 复检（cycle 2）— 会话工具在默认装配下真被调用（action 平铺缺陷已修 + 两条反证合跑 + 端到端实跑）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-277
parent_goal: GOAL-20261004-029
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261005-277`（GOAL-20261004-029 的 cycle 2 子计划）—— 收 cycle 1 遗留的
`W-2`（两条反证未合跑）与 `W-3`（默认装配端到端实跑未做）。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | action 参数平铺（修实测到的真缺陷） | **PASS** | `SessionToolAction` 的 `model_json_schema()` 现为 `additionalProperties: true` 且 `properties` 只剩判别键 `kind`（**无** `arguments` 包装）；平铺 `{"artifact_id": "x"}` 可构造。修复前实测：模型平铺发调用 ⇒ `Error validating tool 'artifact.read': Extra inputs are not permitted`（调用到了桥、schema 处被拒） |
| AC-2 | 端到端真跑（`W-3`） | **PASS** | mock 端点发出真实 `tool_calls`（离线环回）⇒ executor 触达记录 **逐字等于** `[{'artifact_id': 'run-goal029:deliverable.json'}]`；SDK 事件含 `ActionEvent` + `ObservationEvent`；第二轮请求里出现 `role=tool` 的观察且内容含桥返回的 `"ok"` |
| AC-3 | 两条反证合跑（`W-2`） | **PASS** | `TestBothRefutationsRunInOneProcess` 三条同进程：「有实现 ⇒ 能解析」/「未注册 ⇒ 点名 `ToolDefinition '<名>' is not registered`」各自带**显式摘除**（`registry._REG.pop`）；`test_the_first_refutation_left_its_mark` 断言前一条注册仍在（合跑是机械事实，不是叙述） |
| AC-4 | 缺口取证 | **PASS** | `test_the_repo_has_no_other_tool_call_emitting_fixture` 断言本文件是仓内**唯一**含 `"tool_calls"` + `finish_reason` 的测试夹具（实测既有 e2e mock 一律只回文本 ⇒ 该落差此前无覆盖） |
| AC-5 | 本地门与既有判据 | **PASS** | `ruff check` / `ruff format --check` / `mypy`（1089 files）全绿；`tests/e2e + tests/adapters + tests/api` **1276 passed / 20 skipped**；新增判据 **12 passed**；既有判据 `git diff` 为空；治理 `validate.py` 绿 |

## 按压（两向）

| # | 按压形态 | 结果 | 复原 |
| --- | --- | --- | --- |
| P-1 | 把 `arguments: dict` 包装字段放回（action 退回旧形状） | **5 failed**：`test_the_tools_executor_is_reached` / `test_the_result_travels_back_to_the_model` / `test_the_declared_schema_has_no_arguments_wrapper` / `test_flat_arguments_validate` / `test_the_bridge_receives_them_unwrapped` | 恢复 `ConfigDict(extra="allow", frozen=True)` 后 **12 passed** |

## 复检发现（如实登记，未修）

- **`W-1`（本轮新发现，已修但需登记）**：EC-01 的 `W-3` 之所以长期开着，是因为**仓内没有
  会发工具调用的夹具** —— 「会话起得来」被当成了「工具跑得动」。本轮补上该夹具后，
  action 的包装字段缺陷立刻显形。这提示一条通用教训：**判据的存在性本身要取证**
  （AC-4 那条断言就是为此）。
- **`W-2`**：端到端那半用**出厂已放行**的能力名（`artifact.read`）—— 这是**策略面决定的**：
  专属名没有 `allow` 规则 ⇒ `default_effect: DENY` ⇒ 根本到不了 executor（实测：
  `Error: policy denied tool execution: denied by Research OS policy`）。
  ⇒ 本判据证的是「**已放行**能力的会话工具真被调用」，**不**证「任意能力都能被调用」
  （后者取决于策略面，不取决于本机制）。
- **`W-3`**：`SessionToolAction.arguments` 从**字段**变成**方法** —— 语义不同（属性读取会拿到
  绑定方法）。仓内**无**按属性读它的调用点（`rg` 实测仅桥内一处，已同步改用方法调用），
  但这是**对外形状的变化**，如实登记。
- **`W-4`**：端到端判据不驱动 run 编排（它直接起会话读 executor 触达），
  **不**覆盖「工具调用如何进 run 的事件链 / 结果如何进验收门」—— 那是既有 e2e 的射程。
- **`W-5`**：本判据的 mock 端点两轮固定（工具调用 → 文本收尾），**不**覆盖多轮工具调用、
  工具失败重试、并行工具调用等会话语义；那些属会话语义面，不在 EC-01 射程内。
- **`W-6`**：EC-01 的 **(b) 装配面缺口**在 cycle 1 已修（两组合根都接线），但**本 cycle 未重新按压**
  那一处（cycle 1 按压过：删 wiring ⇒ 1 failed）。两轮的按压各自独立、不互相顶替。

## 结论

`PLAN-20261005-277` 的 **AC-1…AC-5 全 PASS**（action 平铺缺陷已修、端到端 executor 真被触达、
两条反证合跑、缺口取证、本地门全绿）；`result = PASS_WITH_WARNINGS`
（六条 `W-NN` 如实登记，**其中 `W-2`/`W-3`/`W-4`/`W-5` 是射程边界**，`W-1` 是方法论提示）。

**EC-01 的判定**：EC-01 的四条要求（(a) 声明式 / (b) 实现注册 / (c) 两条反证合跑 /
(d) 默认装配实跑）**在本轮全部成立**。**但** EC-01 的原始表述里「A 组**≥5 条**读能力接成
会话工具」这一条**尚未满足**：本轮承接的是 3 条（`artifact.read` / `evidence.read` /
`workspace.read`），且 A 组的**执行**受策略面放行约束（6 条 A 组读能力里只有
`artifact.read` / `evidence.read` / `workspace.read` 属出厂已放行或可承接）——
**给其余 A 组读能力放行需用户拍板**（`D-02(b)`）。⇒ **EC-01 记 PARTIAL，不记 PASS**；
转入 EC-02 时以「承接面机械化 + 射程逐条分类」把这条边界写清。

**明确否认**：本轮**不**宣称项目安全（`R-M1` 未收口），**不**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
