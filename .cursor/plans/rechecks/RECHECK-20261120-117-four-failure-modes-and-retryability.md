---
id: RECHECK-20261120-117
slug: four-failure-modes-and-retryability
title: GOAL-115 cycle 2 复检 —— 四类失败模式各一条判据 + 上游可重试性
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-20
updated_at: 2026-11-20
plan_id: PLAN-20261120-117
parent_goal: GOAL-20261119-115
owners:
  - root-agent
verify_paths:
  - adapters/openhands/event_mapping.py
  - packages/application/run_orchestration/manifest_freeze_events.py
  - packages/application/run_orchestration/service.py
  - examples/contracts/task_contracts.yaml
  - tests/adapters/openhands/test_event_mapping_missing_content.py
  - tests/application/run_orchestration/test_manifest_freeze_refusal_event.py
  - tests/application/run_orchestration/test_under_review_segment_is_present.py
  - tests/contracts/test_upstream_failures_are_retryable.py
---

# RECHECK-20261120-117

## 结论

**PASS_WITH_WARNINGS**。EC-03 的四类失败模式各有判据且**逐条按压过**；EC-06 的
可重试性由判据覆盖。两条 warning：`W-1` ④ 的「真实 run 提示词取证」未取（需出网，
本轮网络曾整段中断），`W-2` ① 的「该消息在真实 run 中不再出现」同样只说「代码路径已改
且有判据」，未在真 run 上复验。

## 检查结果

| # | 失败模式 | 判据 | 反证臂（实跑） | 结果 |
| --- | --- | --- | --- | --- |
| ① | `'MessageEvent' object has no attribute 'content'` | `test_event_mapping_missing_content.py`：三种缺失形态走**真实映射入口**都不抛、不泄漏 repr | 直接属性访问同一替身 ⇒ `AttributeError`；替身确实没有该属性 | PASS |
| ② | 重试策略 `max_attempts: 1` + 空类别 | `test_upstream_failures_are_retryable.py`：四份上游合约 `max_attempts ≥ 2` + 三个瞬时类别 + `backoff_seconds` | 把配置按回空 `retryable_categories` ⇒ 判据点名三个缺失类别 | PASS |
| ③ | 拒冻不落事件 | `test_manifest_freeze_refusal_event.py`：**真实编排服务 + 真实 outbox**，拒冻 ⇒ **恰好一条** `run.failed` 带 `reason=manifest_freeze_refused` | 不调用发布 ⇒ 记录为空（复现 5 次空 outbox 的形态）；正控制证明替身不是哑的 | PASS |
| ④ | `UNDER REVIEW` 段被静默丢弃 | `test_under_review_segment_is_present.py`：已渲染 `str` 原样出现在提示词里；六段顺序与文档一致；空段不加标题 | `monkeypatch` 换成"只认视图对象" ⇒ 正文消失、提示词退化为 purpose | PASS |
| EC-06 | 上游瞬时失败可重试 | 同 ② 的判据（四份合约）；类别逐条对 `FailureCategory` 闭集 | 同上 | PASS |

## 本轮**发现并修复**的两个真实缺陷（不只是加判据）

| # | 缺陷 | 怎么发现的 | 修法 |
| --- | --- | --- | --- |
| D-1 | 没有 `content` 时 `_message_text` 回落成 `str(llm_message)` —— 一条 **Python repr** 被当成正文往下游流 | 写 ① 的「不得编造正文」判据时判红 | 改为返回空串；**空不是缺陷，编造才是** |
| D-2 | 拒冻接线第一版 `publish_freeze_refusal(...)` + `_fail_run(...)` ⇒ **一次拒冻落两条 `run.failed`** | 跑通**整条路径**（helper 单测全绿） | helper 自己返回 `RunOutcome`，分支里不再调 `_fail_run`；判据钉「恰好一条」且钉「分支里无 `_fail_run`」 |

D-2 是这一轮最有价值的一格：**helper 的单测不可能发现它** —— 只有真编排服务 + 真 outbox
才看得见重复。

## 开工时的现状纠正（建档实测 vs 原 PLAN 假设）

| 项 | 原 PLAN-115 的说法 | 实际 |
| --- | --- | --- |
| ① | 「已用 `getattr`，需补单测」 | 对，但**回落分支本身就是缺陷**（repr 当正文） |
| ③ | 「`freeze_manifest` 抛出前落事件」 | 抛出点是领域函数；**正确落点是 `start_run` 的捕获**（那里才有 `_publish`） |
| ④ | 「`retrieval_prompt.py:142-155` 已修」 | 对，但**无判据**；本轮补上并加了顺序维 |

## 硬门未动（逐字可核）

- `acceptance_criteria` 的 `REVIEW_SCORE ≥ 0.8`：`git diff` 无该行改动；
- `failure_policy.review_panel: COMPLETE_THEN_JUDGE`：未改（只在其上方加了注释）；
- `NOT_JUDGED` 五项：未触碰。

## 警告

- **`W-1`** ④ 的 `verify:` 要求「一次真实 run 的提示词取证（落 `.cursor/plans/goals/evidence/`）」
  —— 本轮**未取**。取证需要真实出网 run，而本轮网络整段中断（GitHub / opencode.ai /
  pypi 全部不可达，持续约两小时）。判据已把「拼装层不再丢弃该段」钉死；**真实 run 的
  `content digest:` 与 `{task_id}:review_material` 制品**仍未取，记为 PENDING 而非 PASS。
- **`W-2`** ① 的 `verify:` 要求「该消息在真实 run 中不再出现」。本轮只证明**代码路径**
  不再产生 repr 且判据咬合；**没有**再做一次真实 run 统计该错误的出现次数。

## 未覆盖

- EC-04（三次真实双评审读数）与 ④ 的真实提示词取证都需要出网，本轮不冒充。
- EC-05（advisory 并存面）未开始。

## 无可复用事实

本轮**没有**沉淀新的工程记忆条目：四类失败模式的形态已在 GOAL 建档取证里，
`D-2`（重复事件）虽然是个好教训，但它属于「同一批改动里的一次性接线错误」，
写进记忆会把个案当通则。若 EC-04 的真跑复现同类问题，再沉淀。
