---
id: RECHECK-20261004-276
slug: goal-029-ec01-session-tool-actually-executes
title: GOAL-029 EC-01（部分）复检 — F-6 会话工具求值 scope 缺陷已修（四向读数 + 两处按压 + 既有判据未改）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-04
updated_at: 2026-10-04
plan_id: PLAN-20261004-275
parent_goal: GOAL-20261004-029
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261004-275`（GOAL-20261004-029 的 cycle 1 子计划）—— 修 GOAL-029 建档轮实测到的
**F-6 策略面缺陷**：会话工具的求值 scope 曾用会话 id，使带 scope 的 `allow` 规则永不匹配
⇒ **每一条**会话工具调用都落 `default_effect: DENY`，工具 executor **一次也不会被触达**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | F-6 缺陷修复（两条执行期门读**同一张** scope 表） | **PASS** | `adapters/openhands/policy_enforcing_agent.py` 的 `_evaluate` 改用 `policy_scope_for(tool_name)`；`adapters/openhands/session_tool_invocation.py` 的桥复用**既有** `ScopedPolicy` 包装。**四向实测**（真实 `NativePolicyEvaluator(policy.yaml)`、同一装配只差一个字段）：① 已放行 `artifact.read` ⇒ `executor_reached=['hi']`（修复前为 `[]`）；② `workspace.read` ⇒ `['hi']`；③ `literature.search` ⇒ `['hi']`；④ 未放行 `claim.read` ⇒ `[]`、需审批 `external.publish` ⇒ `[]` |
| AC-2 | 既有判据逐字节未改且全绿 | **PASS** | `git diff` 对 `tests/adapters/openhands/test_policy_enforcement.py`、三份 e2e 绑定/多 role/离线链、`tests/application/preflight/**`、`tests/architecture/python/**` **均为空**；`tests/adapters/openhands/` **93 passed**、`tests/architecture/python/` **230 passed**、三份 e2e **22 passed / 1 skipped** |
| AC-3 | 新增判据（四向 + 两条门同源，受判面非空） | **PASS** | `tests/adapters/openhands/test_session_tool_reaches_executor.py` **7 passed**；判据读的是 **executor 是否真被触达**（不是 run 终态 —— 修复前的实测正是 `SUCCEEDED` 而 `executor_reached=[]`）；含 `test_the_declared_scope_table_is_the_only_source` 作受判面非空的正控制（三条能力各自断言其在出厂策略里的真实归属） |
| AC-4 | 本地门 | **PASS** | `ruff check` / `ruff format --check` 全绿；`mypy`（1083 files）`Success: no issues found`；规模门 **1100 passed**；`tests/architecture/python/` + `tests/tooling/` 连同 **1504 passed**；治理 `validate.py` 绿 |

## 按压（两处，各自独立、两向）

| # | 按压形态 | 结果 | 复原 |
| --- | --- | --- | --- |
| P-1 | 撤掉 agent loop 门的补齐（`scope=policy_scope_for(tool_name)` ⇒ `scope=self.policy_scope`） | **2 failed**：`test_a_granted_capability_tool_reaches_its_executor` + `test_the_agent_loop_gate_uses_the_declared_scope` | `sha256` **逐字节一致**（`bdc1f818776da0cb4794863ee307e8fc917a8708a79b302bc69005b9ca830293`）后复绿 |
| P-2 | 撤掉桥的补齐器（`execute_tool_call(..., scoped_policy, ...)` ⇒ `..., policy, ...`） | **1 failed**：`test_the_bridge_gate_uses_the_declared_scope` | `sha256` **逐字节一致**（`f629d3023d24a0f459a2103bfbee22e088e0c196ed6cf3785521442ea59e7c45`）后复绿 |

**两处按压各自 red 的是不同判据** ⇒ 两条门的覆盖不是互相顶替的（承 MEM-159：反证两向）。

## 复检发现（如实登记，未修）

- **`W-1`（本 PLAN 未收完的部分）**：EC-01 的 **(b) 装配面缺口**本轮**未修** ——
  两个组合根本体（`services/api/composition.py::_sqlite_orchestration`、
  `services/api/pg_composition.py::_build_pg_orchestration`）仍**没有**把
  `register_session_tools` 传给 `build_agent_runtime`。**因此「出厂即可跑」尚未成立**：
  本轮证的是「策略面不再无条件拒绝」，不是「生产装配下会话工具可用」。
- **`W-2`**：本轮**未**做 EC-01 要求的**两条反证合跑**（专属名字证「未注册 ⇒ 点名失败」+
  显式摘除证「有实现 ⇒ 能解析」）—— 那两条依赖接线完成（没有实现可摘除时，第二向无对象）。
- **`W-3`**：EC-01 的 (d)「默认装配实跑且工具 executor 真被触达」未做（同上依赖接线）。
- **`W-4`**：判据 `test_the_bridge_gate_uses_the_declared_scope` 里 Fake provider 不 spill 输出，
  桥在**执行面**会因此抛错（已被 `contextlib.suppress` 收敛）——本判据只钉策略面的 scope，
  **不**覆盖桥的完整成功路径（那条由既有 e2e 覆盖）。
- **`W-5`**：`policy_enforcing_agent` 的 `policy_scope` 字段**仍在**（`_queue_approval` 用它作
  `RuntimeEvent.session_id`，是会话身份的真相）—— 字段名与「求值 scope」的区分靠注释，
  **没有**类型级区分（同名字段仍可能被误用；本轮的判据钉住了行为）。

## 复检补充：CI 首跑判红（已修，判据侧）

`e52a82c` 的 M0 首跑 **`quality-ubuntu-latest` / `quality-windows-latest` 双红**，
失败签名是 `python/tests` 的
`tests/contracts/test_agent_runtime_contract.py::test_agent_runtime_fork_creates_new_lineage` /
`::test_agent_runtime_fork_applies_tool_set_change_under_a_revision` 报
`Local classes not supported! test_session_tool_reaches_executor._ProbeAction / _ProbeObservation`。

**根因（本 PLAN 自己引入的判据侧缺陷）**：新增判据里的探针 `Action` / `Observation` 子类起初定义在
**函数内**（`<locals>` 限定名）。SDK 会枚举它们的**具体子类**来构建判别联合 ⇒ **同进程后续所有
事件 round-trip** 直接抛错。这正是我在该文件 docstring 里**引用**过
`tests/e2e/live_run_support.py` 的同族教训，却在代码里**违反**了它。

**本地为何没抓住**：受影响的是**别的文件**的判据，且只在**全量收集**（`python/tests`）里暴露；
我本地只单跑了 `tests/adapters/openhands/`。

**修法**：把 `_ProbeAction` / `_ProbeObservation` / `_ProbeExecutor` 提到**模块级**（`__qualname__`
不再含 `<locals>`）。**两向取证**：
- 把**已提交的坏版本**（`git show e52a82c:...`）与 `tests/contracts/test_agent_runtime_contract.py`
  **合跑** ⇒ **2 failed**（复现 CI 签名，逐字相同）；
- 修好的版本合跑 ⇒ **121 passed / 7 skipped**。
- 另：`tests/adapters/openhands/` 全量 + 该合约文件合跑绿；`mypy` / `ruff` / `format` 绿。

**纪律更正（写入本 PLAN 的 WP-C）**：**新增判据若定义 SDK 的 `Action` / `Observation` 子类，
必须定义在模块级**；且**必须与 `tests/contracts/test_agent_runtime_contract.py` 合跑一次**验证。

## 结论

`PLAN-20261004-275` 的 **AC-1…AC-4 全 PASS**（F-6 缺陷已修、四向取证、两处按压两向、
既有判据未改）；`result = PASS_WITH_WARNINGS`（五条 `W-NN` 如实登记，**其中 `W-1`/`W-2`/`W-3`
是 EC-01 的剩余部分**，必须在后续 cycle 收完 EC-01 才能记 EC-01=PASS）。

**明确否认**：本轮**不**宣称项目安全（`R-M1` 未收口），**不**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
