---
id: RECHECK-20261008-314
slug: goal-033-ec02-dead-letter-run-coordination
title: 独立复检：GOAL-033 cycle 2（EC-02）死信恢复 ↔ run 续跑的协同
plan_id: PLAN-20261008-313
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-314 — GOAL-033 cycle 2（EC-02）独立复检

复检对象：`PLAN-20261008-313`。**复检独立于实施**：下列逐条重跑判据与按压，不引用
PLAN 的结论当证据。

## 检查结果

### 1. 三面实测独立重跑（用探针 + 判据两条路各跑一次）

| 面 | 复检读数 | 与 PLAN 一致？ |
| --- | --- | --- |
| run 状态（默认契约） | run = `FAILED`；任务面 = `['DEAD_LETTER']` | 一致 |
| run 状态（容忍契约） | run = `DEGRADED`（非终态）；任务面含 `DEAD_LETTER` | 一致 |
| 派发方 | 死信 run **不被考虑**；改 `PAUSED` ⇒ **被考虑** | 一致 |
| 任务面（worker） | `requeue` 后 `claim_next` **直接取到** | 一致 |
| 任务面（编排） | `claim_next` = `None`；`acquire_lease` 成功 | 一致 |
| 机制边界 | `FAILED --RESUME-->` ⇒ `InvalidTransitionError` | 一致 |

**复检结论**：三面读数在**两条独立路径**（探针脚本 / 判据文件）上一致 ⇒ 不是
单一路径的产物。

### 2. 判据重跑

```
tests/e2e/test_dead_letter_run_coordination_matrix.py ...... [100%]  6 passed
```

### 3. 按压独立重跑（**这是本轮的复检重点**）

```
BASELINE_GREEN 6 passed
P1_RED exit=1 1 failed, 5 passed
RESTORED True scheduler.py 90562a9d9c3d->90562a9d9c3d
FINAL_MATCHES_BASELINE True 6 passed
```

- **复检确认了那条返工**:首版按压**没判红**(我复现过：把状态过滤放开后
  `dispatched` 仍是 0）⇒ 原判据被掩蔽；改为 spy 读数后同一次按压**判红**。
- `RESTORED True` 的 sha 相同 ⇒ 二进制安全写盘生效（首版是文本模式 ⇒ 归因不可得）。
- 留档 `scratch/goal033-cycle2/press-matrix.log`（CR=0）。

### 4. 既有判据零改动核查

`git status --short` 对 `tests/**`：**唯一变化是新增**一个 e2e 文件；
`services/api/scheduler.py` 两次按压后 `git status` **零条目**（逐字节复原）。

### 5. 门

| 门 | 读数 |
| --- | --- |
| `ruff check`（新文件） | 绿 |
| `ruff format --check`（新文件） | 绿 |
| `mypy`（新文件） | **首跑 1 error**（`dict[str, str]` 不变性与 `dict[str, str \| bool \| int \| list[str]]` 不符）⇒ 按类型签名修正 ⇒ 绿 |
| 规模门 | **首跑 1 failed**（worker 面那条用例 **52 行** > 50 行硬上限 —— 门在正常工作）⇒ 把造死信那段提为 `_worker_face_dead_letter` 助手 ⇒ 绿（1132 passed）；**断言一条未改**（只搬动了构造代码） |
| 受判面套件（api+contracts+domain+adapters/sqlite+tooling+observability+e2e） | **3465 passed / 92 skipped / 0 failed** |

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-6 独立重跑成立；**无产品缺陷**。

### Warnings

- **W-1（本 EC 的核心里程碑：判据自身的假绿被复检抓出）**：首版 ③ 的
  `dispatched == 0` 断言**无法被单变量证伪**（三重掩蔽）⇒ 属**判据缺陷**而非产品缺陷。
  返工为 spy 读数 + 正向对照后按压判红。**这条记在本节而不是「无缺陷」里**：
  它是"判据也可能假绿"的实例（承 `MEM-20260928-160` 的同类）。
- **W-2（A/B 的 B 是「登记」不是「实现」）**：run 级自动继续**未实现**，边界如实登记：
  需要**改 run 级状态机**（`FAILED` 是终态 ⇒ 改语义须 ADR）**或**新增扫非 `PAUSED` run 的
  派发面。**下一轮输入**（GOAL 残余节已登记）。
- **W-3（worker 面的"已存在"只覆盖 EXECUTION）**：worker 面的自动再交付对
  `kind=EXECUTION` 成立；编排面任务（`AGENT_SESSION`）不属该面 —— 别把前者读成后者。
- **W-4（容忍契约的 `DEGRADED` 语义未进一步展开）**：本轮只量出「死信可与非终态 run 同现」，
  **未**实现「`DEGRADED` run 上的死信任务该怎么继续」（`DEGRADED` 有 `RESUME` 出边 ⇒
  技术上可行，但属新机制）。如实登记。
- **W-5（未覆盖范围照旧）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
