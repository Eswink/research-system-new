---
id: PLAN-20261005-277
slug: goal-029-ec01-session-tool-called-end-to-end
title: GOAL-029 cycle 2（EC-01 收口）：会话工具**在默认装配下真被调用** — 修 action 平铺缺陷 + 两条反证合跑 + 端到端实跑
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-278-goal-029-ec01-session-tool-called-end-to-end.md
memory_entries: []
parent_goal: GOAL-20261004-029
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261004-029 的 **EC-01**（收 cycle 1 遗留的 `W-2`/`W-3`）。授权沿用该 GOAL 的
    `authorization.ref`：「新增会话工具实现（把 canonical 读面接成 SDK 工具）」+
    「新增判据 / 夹具（落 `tests/**`）」+「修实现过程中发现的真缺陷」+ push-to-main-for-CI 口径
    （**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面；**不改**
    `default_effect: DENY` / 不放宽 §9 / **不给 A 组读能力新增 `allow`**（属 `D-02(b)` 未决口径，
    需用户拍板 ⇒ 命中即 BLOCKED）；**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；
    **零**新依赖；**不得**把 provider id 直接当 SDK 工具名；**不得**未注册即静默降级；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 EC-01 从「策略面不再无条件拒绝 + 实现接进了组合根」推进到「**模型真的调了这个工具，
    且它的 executor 真的跑了**」：修掉 action 的包装字段缺陷（它让任何真实工具调用在 schema
    处被拒），补上仓内**唯一**会发 `tool_calls` 的端到端判据，并把 EC-01(c) 的两条反证
    **合跑再证一次**（承 MEM-20261001-180：registry 进程级只增不减）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **action 参数平铺（修实测到的真缺陷）**：`SessionToolAction` 的模型可见 schema
      **不再有** `arguments` 包装字段、且为 `additionalProperties: true`；平铺参数
      （`{"artifact_id": "x"}`）能通过校验。**实测对照**：修复前模型平铺发调用 ⇒
      `Error validating tool '...': Extra inputs are not permitted`（调用到了桥、schema 处被拒）；
      修复后 ⇒ executor 被触达。
    status: PASS
  - id: AC-2
    criterion: >-
      **端到端真跑（`W-3`）**：mock 端点发出**真实** `tool_calls`（离线环回）⇒ 工具的
      executor **被触达**、收到的参数**逐字等于**模型发出的平铺参数、结果经 `tool` 角色的
      消息**回到模型**。判据读的是「executor 被调用」这一事实（不是 run 终态 —— cycle 1
      已证终态绿不蕴含工具运行）。
    status: PASS
  - id: AC-3
    criterion: >-
      **两条反证合跑（`W-2`）**：同一次运行里既有「有实现 ⇒ 能解析」也有
      「未注册 ⇒ SDK 点名 `ToolDefinition '<名>' is not registered`」，且带**显式摘除**
      （`registry._REG.pop`）使断言与用例执行顺序无关；另有「合跑证据」断言把
      「两条确实跑在一次运行里」变成机械事实。
    status: PASS
  - id: AC-4
    criterion: >-
      **缺口取证**：断言本文件是仓内**唯一**会发 `tool_calls` 的 e2e 夹具 —— 这条同时是
      「为什么 `W-3` 此前没被覆盖」的事实陈述（既有 e2e mock 一律只回文本）。
    status: PASS
  - id: AC-5
    criterion: >-
      本地门与既有判据：`ruff check` / `ruff format --check` / `mypy` 绿；
      `tests/e2e + tests/adapters + tests/api` 全量绿；既有判据**逐字节未改**；
      治理 `validate.py` 绿。
    status: PASS
implementation:
  - id: WP-A
    title: 修 action 包装字段（参数平铺）
    files:
      - adapters/openhands/session_tools.py
  - id: WP-B
    title: 端到端判据（唯一发 tool_calls 的夹具 + 两向反证合跑）
    files:
      - tests/e2e/test_session_tool_call_on_the_default_assembly.py
---

## 背景

cycle 1 把 EC-01 推进到「策略面不再无条件拒绝 + 实现接进两个组合根」，但留了两条残余：
`W-2`（两条反证未在默认装配实跑里合跑）与 `W-3`（默认装配下端到端实跑未做）。

cycle 2 的勘察发现：**全仓 e2e 的 mock 端点没有一处会发 `tool_calls`**（实测检索：
`tests/e2e/` 下无一处含该 wire 形状）⇒「会话起得来」与「工具跑得动」之间的落差
**从未被任何东西看着**。这正是 `W-3` 一直开着的原因：既有判据验的是会话语义，
不是工具面语义。补上这条之后，**第五个真缺陷**立刻显形（见下）。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-5）。

## 证据

- **commit**：`f64a1cf`（WP-A + WP-B 同提交；显式路径）。
- **缺陷与实测对照（AC-1）**：`SessionToolAction` 原声明 `arguments: dict` 包装字段 ⇒
  `model_json_schema()` 的 `properties` 是 `{"arguments": {...}, "kind": {...}}` ⇒
  模型按常理平铺发 `{"artifact_id": "x"}` 撞 base `Schema` 的 `extra="forbid"` ⇒
  `Error validating tool 'artifact.read': Extra inputs are not permitted`（**调用到了桥、
  却在校验处被拒**）；改 `ConfigDict(extra="allow", frozen=True)` 后 schema 为
  `additionalProperties: true` 且无包装字段，executor 被触达。
- **端到端读数（AC-2）**：mock 端点两轮（第一轮 `finish_reason=tool_calls` + 平铺参数、
  第二轮收尾）⇒ `executor 触达记录 == [{'artifact_id': 'run-goal029:deliverable.json'}]`
  （逐字相等）；SDK 事件含 `ActionEvent` + `ObservationEvent`；第二轮请求里出现
  `role=tool` 的观察且内容含桥返回的 `"ok"`。
- **合跑（AC-3）**：`TestBothRefutationsRunInOneProcess` 三条用例同进程；
  「有实现 ⇒ 能解析」与「未注册 ⇒ 点名」各自带**显式摘除**；
  `test_the_first_refutation_left_its_mark` 断言前一条注册仍在（把合跑变成机械事实）。
- **判据例数**：新增 `tests/e2e/test_session_tool_call_on_the_default_assembly.py`
  **12 passed**；`tests/e2e + tests/adapters + tests/api` 合计 **1276 passed / 20 skipped**。
- **按压**：把包装字段放回 ⇒ **5 failed**（executor 未触达 + schema 有包装 + 平铺不可校验）；
  复原后 12 passed。
- **既有判据**：`git diff` 对既有 e2e / 适配器判据为空。
- **CI**：见 GOAL「CI 台账」（本提交 `f64a1cf` 的行）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 2 derive）并执行 WP-A/WP-B。 |
| 2026-10-05 | DONE | WP-A/WP-B 收口：action 改参数平铺；新增端到端判据 12 passed（含两条反证合跑 + 缺口取证）；按压两向取证；`RECHECK-20261005-278` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：`adapters/openhands/session_tools.py`（action 的形状 + 参数读取）+ 新增判据一份。
- **Domain / API / schema 变化**：无（改的是 SDK 侧工具契约的形状，不进 Domain）。
- **安全 / 凭据变化**：**未**放宽任何放行面；未触碰 `policy.yaml`；策略面照旧按能力名裁决
  （本判据里未放行的专属名**仍被拒** —— 那是策略面在正常工作的证据，见 RECHECK 的 W-NN）。
- **兼容性 / 迁移风险**：`SessionToolAction.arguments` 从**字段**变成**方法** ⇒ 任何外部
  按属性读它的代码会拿到绑定方法（仓内无此类调用点，实测 `rg` 确认）。
- **上游版本影响**：无（未动依赖）。
