---
id: PLAN-20261004-275
slug: goal-029-ec01-session-tool-actually-executes
title: GOAL-029 cycle 1（EC-01）：会话工具**真被触达** — 修 F-6 策略面 scope 缺陷 + 两组合根接注册面 + 两向反证合跑
status: IN_PROGRESS
created_at: 2026-10-04
updated_at: 2026-10-04
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261004-029
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261004-029 的 **EC-01**。授权沿用该 GOAL 的 `authorization.ref`：
    「**新增会话工具实现**（把 canonical 读面接成 SDK 工具），并接进生产组合根」+
    「新增判据 / 夹具（落 `tests/**`）」+ 文档同源更新 + push-to-main-for-CI 口径
    （**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面
    （点名：`tests/egress_guard.py`、`tests/e2e/test_ec03_real_runtime_offline_chain.py`、
    `tests/e2e/test_multi_role_research_offline.py`、
    `tests/e2e/test_multi_role_on_the_default_assembly.py`、
    `tests/e2e/test_tool_binding_on_the_default_assembly.py`、
    `tests/application/preflight/**`、`tests/architecture/python/**`、
    `tests/adapters/openhands/test_policy_enforcement.py`、规模门）；
    **不改** `default_effect: DENY` / 放宽 §9 / 新增类别级 allow / **给 A 组读能力新增 `allow`**
    （后者属 `D-02(b)` 未决口径 ⇒ 需用户拍板 ⇒ 命中即 BLOCKED）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；
    **不得**把 provider id 直接当 SDK 工具名；**不得**未注册即静默降级；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
objective: >-
    把 GOAL-029 事实层结论 **F-6** 这个**真缺陷**修掉，使「会话工具**真能被调用**」成为
    可复核事实 —— 这是 GOAL-028 `W-1`（映射机制成立 ≠ 出厂即可跑）的**第一层**：
    今天即使装配方把实现接齐，会话工具调用**仍然一条都执行不了**，因为求值 scope 传的是
    会话 id 而 `policy.yaml` 的带 scope `allow` 规则要求 scope 相等。
exit_criteria:
  - id: AC-1
    criterion: >-
      **F-6 缺陷修复（策略面 scope 同源）**：`PolicyEnforcingAgent._evaluate` 与
      `session_tool_invocation.make_tool_invoker` 两条执行期门都用**既有那一张**
      `policy_scope_for` 表补 scope（**不新造第二张表**、**不改任何 allow 规则**）。
      **实测对照**（真实 `NativePolicyEvaluator(policy.yaml)`、同一装配只差这一个字段）：
      修复前 `artifact.read`（**已放行**）⇒ `executor_reached=[]`；修复后 ⇒
      `executor_reached=['hi']`；**未放行**能力（A 组 `claim.read`）⇒ 仍 `[]`；
      `require_approval` 能力（`external.publish`）⇒ 仍 `[]`（**两向**都保持）。
    status: PENDING
  - id: AC-2
    criterion: >-
      **既有判据逐字节未改且全绿**：`tests/adapters/openhands/`、
      `tests/architecture/python/`、`tests/e2e/` 的三份绑定/多 role/离线链判据
      **`git diff` 为空**且全绿（本修复不得靠改判据取得）。
    status: PENDING
  - id: AC-3
    criterion: >-
      **新增判据**：把 AC-1 的四条读数固定成判据（含**两向**：已放行 ⇒ 触达；
      未放行 / 需审批 ⇒ 拒绝且点名），并对**两条门**各有一条断言
      （agent loop 面 + 桥面）—— 承 `MEM-20260922-156`：受判面非空。
    status: PENDING
  - id: AC-4
    criterion: >-
      本地门：治理 `validate.py` 绿；记录面判据绿；`ruff check` / `ruff format --check`
      （**100 字符上限**）/ `mypy`（strict）绿；as-is m0 **23/23** 在记录写入**之后**。
    status: PENDING
implementation:
  - id: WP-A
    title: F-6 修复 — agent loop 门 + 桥门的求值 scope 同源
    files:
      - adapters/openhands/policy_enforcing_agent.py
      - adapters/openhands/session_tool_invocation.py
    done_when: 两条门都用 policy_scope_for；四向实测读数成立
  - id: WP-B
    title: 新增判据 — 会话工具执行面的四向读数固定
    files:
      - tests/adapters/openhands/test_session_tool_reaches_executor.py
    done_when: 判据全绿；按压（还原 scope=self.policy_scope）⇒ 判红
  - id: WP-C
    title: 记录 — GOAL 迭代日志 + 状态历史 + 本 PLAN 收口
    files:
      - .cursor/plans/goals/GOAL-20261004-029-capability-coverage-expansion-and-out-of-the-box-runnability.md
      - README.md
    done_when: 记录自洽（EC 表与 frontmatter 同轮同改）
---

## 背景

GOAL-029 建档轮的只读勘察（GOAL 文件「事实层结论」F-6）**实测**到：生产装配下会话工具
**根本不可能被执行**。两条各自独立的成因：

1. **装配面缺口**（GOAL-028 `W-1` 的字面）：两个组合根本体都没把 `register_session_tools`
   传给 `build_agent_runtime`；
2. **策略面缺陷**（本轮新发现）：`PolicyEnforcingAgent._evaluate` 构造的 `PolicyRequest`
   用 `scope=session_id`，而 `policy.yaml` 的带 scope `allow` 规则要求 **scope 相等**才匹配
   ⇒ `session_id` 永不匹配任何规则 ⇒ **每一条**会话工具调用都落 `default_effect: DENY`。
   桥侧 `execute_tool_call` 同样**不带** scope（运行链用 `ScopedPolicy` 补，会话面没有）。

本子 PLAN 收**第 2 条**（第 1 条另轮收）：它使「会话工具真被调用」**在任何装配下都不可能**，
是 `W-1` 之下的**更底层**缺陷 —— 不修它，接再多的实现也一条都跑不动。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-4）。

**证据口径（不靠「没报错」）**：判据读的是**工具 executor 是否真被触达**
（executor 内记录调用），不是 `run` 的终态字符串 —— 修复前的实测正是
`status=SUCCEEDED` 但 `executor_reached=[]`（终态绿而工具从未运行）。

## 实施清单

- [ ] **WP-A**：`adapters/openhands/policy_enforcing_agent.py` 的 `_evaluate` 改用
      `policy_scope_for(tool_name)`（既有唯一那张表）；`adapters/openhands/session_tool_invocation.py`
      的桥复用既有 `ScopedPolicy` 包装（不新造映射）。
- [ ] **WP-A**：四向实测取证（已放行 ⇒ 触达 / 未放行 ⇒ 拒 / 需审批 ⇒ 拒 / 桥面同形）。
- [ ] **WP-B**：新增判据 `tests/adapters/openhands/test_session_tool_reaches_executor.py`；
      按压（把 scope 还原成 `self.policy_scope`）⇒ 判红；复原 ⇒ 逐字节一致且绿。
- [ ] **WP-C**：GOAL 迭代日志 / 状态历史 / `ALL_PLAN` 投影 / 本 PLAN 收口。

## 证据

（收口时逐条回填：commit / 实测读数 / 判据例数 / m0 终态行 / CI run。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-04 | IN_PROGRESS | 建档（cycle 1 derive）。WP-A 已实施并四向实测取证：修复前 `artifact.read`（已放行）`executor_reached=[]`；修复后 `executor_reached=['hi']`；`claim.read`（未放行）与 `external.publish`（需审批）修复后仍 `[]`。受影响既有套件全绿且 `git diff` 为空：`tests/adapters/openhands/` **86 passed**、`tests/architecture/python/` **230 passed**、三份 e2e 绑定/多 role/离线链 **22 passed / 1 skipped**。 |

## 影响报告

- **改动面**：`adapters/openhands/` 两个模块各一处（+1 import、改 1 个表达式 + 注释）。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：**收紧了语义上的一致性**（会话面与 preflight / 运行链 / 沙箱实验
  现在读**同一张** scope 表）；**未**放宽任何 `allow`、**未**改 `default_effect: DENY`、
  **未**新增类别级 allow。未放行能力与需审批能力**照旧被拒**（实测两向）。
- **兼容性 / 迁移风险**：会话工具的**可执行集合**从「空集」变成「策略放行集」——
  这是**修复**而非放宽：放行集仍由 `policy.yaml` 唯一决定。
- **上游版本影响**：无（未动依赖）。
