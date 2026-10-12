---
id: RECHECK-20261012-432
slug: goal-061-ec01-04-the-timeliness-of-a-conflict-is-decidable
title: 独立复检：GOAL-20261012-061 cycle 1（EC-01…EC-04）—— 冲突声明的时效成为可判定
plan_id: PLAN-20261012-431
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/memory/validity.py（`ConflictTimelinessState` + `conflict_timeliness_at`）
  - path: 独立重跑判据（域 11 + 披露面 7 + PG 1 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-061-press-two-way.txt
---

# RECHECK-20261012-432 — GOAL-20261012-061 cycle 1 独立复检

复检对象：`PLAN-20261012-431`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-conflict-timeliness.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 冲突**时效面零命中** | 六组候选标识符在 `packages/`·`adapters/`·`services/` **（零命中）** |
| 2 | `ConflictResolution` 字段**逐个读出** | `['other_id', 'resolved_by', 'resolved_at']` —— **无**时效面 |
| 3 | 记忆自身的时效机制**在树**（可复用） | `valid_from` / `review_after` / `expires_at` + `validity_at` |
| 4 | 五态处置**逐条读出** | `USE` / `ANNOTATE` / `SKIP` / `SUPERSEDED` / `CONFLICTED` —— **无**「冲突已不再算数」 |

### 2. EC-02 冲突时效可判定（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/domain/test_conflict_timeliness.py -q`
⇒ **11 passed**。逐条复核：

- 两个声明位（`conflict_review_after` / `conflict_expires_at`）在**记录与提案**上各一份
  （缺省 `None` ⇒ 既有行为逐字不变）；
- 三态**互不混用**：`STALE`（失效，**更强**）/ `REVIEW_DUE`（该复核）/ `None`（未到期
  **或未声明** —— **不猜**）；界的**闭区间**与 `validity_at` **逐字同一口径**；
- **没有冲突声明** ⇒ 也 `None`（没有冲突就没有「冲突时效」可言）；
- 两条坏形态**点名拒绝**：**声明了时效却没有任何冲突**（否则永远不生效 = 看不见的故障）；
  `conflict_expires_at` **早于** `conflict_review_after`（那种组合下「该复核」永不到来）；
- **两维互不顶替**（反证臂）：记录**过期**而冲突**未声明时效** ⇒ 冲突时效仍 `None`。

### 3. EC-03 两读面同源 + 三适配器同契约（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_conflict_timeliness_read_faces.py tests/postgres/test_memory_conflict_timeliness_pg.py -q`
⇒ **8 passed**。逐条复核：

- 编排面逐条披露 `conflict_timeliness`（失效 ⇒ `STALE`）；**未到期** ⇒ `None`；
- **未声明逐字不变**（`None`）+ **既有键逐条仍在**（`memory_id` / `content` / `validity` /
  `disposition` / `reason` / `contradictions` / `conflict_resolutions`）；
- **两读面同源**（**判关系**）：编排面与 HTTP 面**都引用**同一个纯函数
  `conflict_timeliness_at`（少一处 ⇒ 两处可能各写一套，漂移无从发现）；
- **三适配器同契约**：SQLite 往返 + **Fake** 同契约 + **PG 真库**往返（迁移 `026` 只加两列）；
- **快照同轮**（`+11 / -0`）；HTTP DTO 同轮披露该键。

### 4. EC-04 两向反证（独立重跑 `scratch/goal061_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（19 passed） |
| `X-1` 失效判成有效（`STALE` 支被摘） | **RED**（5 failed） |
| `X-2` 未到期判成失效（界比较反向） | **RED**（6 failed） |
| `X-3` 未声明被当成已到期（「不猜」被破坏） | **RED**（4 failed） |
| `X-4` 缺省形态被改动（未到期/未声明也判失效） | **RED**（5 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**两处如实登记（复检时的自纠）**：① `X-4` 首版打的是 `if not record.contradictions` 那道
守卫，而它是**防御性的**（域层让「无冲突却有声明」不可构造）⇒ 该臂**不可观测**、按压按 GREEN
⇒ 改打**可观测**的缺省支后全红；② 断言集里的「不猜」判据首版按**文件末尾形态**判
（`rstrip().endswith("return None")`）⇒ 被任何末尾重排假红 ⇒ **改判关系**（AST 读：
返回具名状态的分支里**不得**出现「未声明」形态），并对**四种**「未声明 ⇒ 某状态」写法
**逐条两向实测**（基线真、四条按压假）。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- 「不猜」判据的**两向实测**见 §4 ②（四种写法各自判负）；
- 例数下界钉进收口断言集（11 / 7 / 1 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：冲突时效**三态可判**
（`STALE` / `REVIEW_DUE` / `None`，各自点名且**不猜**）、**两读面同源**、
**三适配器同契约**、**缺省形态逐字不变**。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：`X-4` 首版按压**不可观测**（守卫是防御性的）⇒
  该轮的反证臂一度失效；已按纪律改打可观测面（见 §4 ①）。
- **`W-2`（有意不做的边界）**：`STALE` **只点名**、**不**自动消解、**不**自动失效
  —— 「谁对谁错」与「还算不算数」的判定**仍由人给**（序 26 立的边界**一字不动**）；
  本轮**不**做内容级语义比较。
- **`W-3`（未覆盖）**：**真实外发**（邮件 / webhook / IM）未做；**投递保证 / 重试 / 去重**
  未做。**投递语义不是「恰好一次」**（口径只能是 at-least-once + idempotency + deduplication）。
- **`W-4`（承继）**：`Z-1` 的混合式已由序 28 收口，但更复杂组合 / `W-2` 的内容级检测 /
  `BB-3` 等残余**原样保留**；本 GOAL **不**推进其中任何一条。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）。
