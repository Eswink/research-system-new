---
id: PLAN-20261120-117
slug: four-failure-modes-and-upstream-retryability
title: GOAL-115 cycle 2 —— 四类失败模式各一条判据（EC-03）+ 上游可重试性（EC-06）
status: DONE
created_at: 2026-11-20
updated_at: 2026-11-20
parent_goal: GOAL-20261119-115
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261120-117-four-failure-modes-and-retryability.md
memory_entries: []
---

# PLAN-20261120-117

## 背景

GOAL-115 的 EC-03 要求「24 次 FAILED 的实测画像里四类失败模式**各一条判据**」，
EC-06 要求「上游瞬时失败在会话契约里可重试」。两条共享同一批受判面
（`event_mapping` / 会话合约 / 冻结路径 / 提示词拼装），且都**可离线验证** ——
这一点在本轮有决定性：EC-04 需要真实出网（当前不可用），EC-03/06 不需要。

**建档实测（2026-11-20，逐条读代码确认现状）**：

| # | 缺陷 | 现状 | 证据 |
| --- | --- | --- | --- |
| ① | `'MessageEvent' object has no attribute 'content'` | **已修**（`event_mapping.py` 用 `getattr(llm_message, "content", None)`），但**没有单测**钉住 | `adapters/openhands/event_mapping.py:88-95` |
| ② | `dual_model_review_deliverable` 无重试 | **未修**：`max_attempts: 1` + `retryable_categories: []` | `examples/contracts/task_contracts.yaml:713-715` |
| ③ | 拒冻不落事件 | **未修**：`freeze_manifest` 抛出 `ManifestFreezeError`，`start_run` 里**未捕获** ⇒ 无事件、无 `run.failed` | `service.py:147-153`；对照 `_fail_run` 走 `publish_failed_run` |
| ④ | `UNDER REVIEW` 段缺失 | **已修**（`_section_of` 认 `str` 已是渲染结果），但**没有判据**钉住「拼装顺序与合约措辞一致」 | `retrieval_prompt.py:142-156` |

**②的既有形态参照**：`multi_role_review`（`:248-258`）已是
`max_attempts: 2` + `retryable_categories: [MODEL_RELAY_UNAVAILABLE, MODEL_RATE_LIMIT, MODEL_TIMEOUT]`
+ `backoff_seconds: 30` —— 同一份文件里两种形态并存，本身就是「②是个漏配」的证据。

## 交付面（checkbox）

- [x] WP-1 ①单测：`MessageEvent` 无 `content` 属性时不抛（含 `llm_message is None`）
- [x] WP-2 ②改 `dual_model_review_deliverable.retry_policy`（照 `multi_role_review` 形态）
- [x] WP-3 ③拒冻落可读事件（`run.failed` 带 `missing` 清单）
- [x] WP-4 ④拼装顺序判据（`_section_of` 认 `str` + 段落顺序与合约措辞一致）
- [x] WP-5 EC-06 两份会话契约的 `retryable_categories` 覆盖上游瞬时失败
- [x] WP-6 四条反证臂（每条都要**按压判红**，按 raw `sha256` 逐字节复原）

## 实施清单

### WP-1 ①`event_mapping` 空 content

`_message_text` / `_deliverable_text` 取 agent 消息时走
`getattr(llm_message, "content", None)`。要钉的是**三种形态**：
`llm_message=None`、`llm_message` 无 `content` 属性、`content=None` ——
三者都不得抛 `AttributeError`，且都返回 `None`（不猜）。

判据：`tests/adapters/openhands/test_event_mapping_missing_content.py`。

### WP-2 ②重试策略

```yaml
    retry_policy:
      max_attempts: 2
      retryable_categories: [MODEL_RELAY_UNAVAILABLE, MODEL_RATE_LIMIT, MODEL_TIMEOUT]
      backoff_seconds: 30
```

照 `multi_role_review` 的形态（同一文件、同一语义）。**不改** `acceptance_criteria`
的 `REVIEW_SCORE ≥ 0.8`，**不改** `failure_policy.review_panel`。

### WP-3 ③拒冻写事件

`start_run` 里 `freeze_manifest(...)` 抛 `ManifestFreezeError` 时必须：
① 把 run 转 `FAILED`；② 发一条 `run.failed`（或专用 `manifest.freeze_refused`）
**带 `missing` 清单**；③ 再把异常继续抛/返回失败结局。

已有一条**同形的既有路径**可参照：`_fail_run` → `publish_failed_run`。
落点优先复用 `run_terminals.publish_failed_run`（不新开一条发布通道）。

反证臂：把事件发布摘掉 ⇒ 判据判红。

### WP-4 ④`UNDER REVIEW` 段

两件：
① `_section_of` 认 `str`（已修）—— 判据钉住「传入已渲染 `str` ⇒ 该段**非空**」；
② **段落顺序**与合约措辞一致（`compose_prompt` 的拼装序 == 合约里描述的顺序）。

反证臂：让 `_section_of` 只认视图对象 ⇒ 判据判红（复现真实缺陷）。

### WP-5 EC-06 上游可重试性

`direction_to_manuscript` 与 `dual_model_review` 两份会话契约
（以及 WP-2 改的那份交付物契约）的 `retryable_categories` 覆盖
`MODEL_RELAY_UNAVAILABLE` / `MODEL_RATE_LIMIT` / `MODEL_TIMEOUT` 且 `max_attempts ≥ 2`。
判据**只钉策略声明与分类映射**，不要求成功率提升（EC-06 原文）。

反证臂：清空 `retryable_categories` ⇒ 判红。

## 验证

```bash
uv run --frozen --no-sync python -B -m pytest tests/adapters/openhands tests/application/run_orchestration tests/loaders -q
uv run --frozen --no-sync python -B -m pytest tests/application/preflight -q
uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
```

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | ① | test | `test_event_mapping_missing_content.py` | 9 passed；三种缺失形态不抛、不泄漏 repr；反证臂咬合 |
| EV-02 | ② | config | `dual_model_review_deliverable.retry_policy` | `max_attempts: 2` + 三类别 + `backoff_seconds: 30` |
| EV-03 | ③ | test + 反证 | 真实服务 + 真 outbox | 8 passed；**恰好一条** `run.failed`（第二版修掉了重复发布） |
| EV-04 | ④ | test + 反证 | `_section_of` 认 `str` + 段落顺序 | 7 passed；反证臂换成"只认视图" ⇒ 正文消失 |
| EV-05 | EC-06 | test | 四份上游合约的 `retry_policy` | 21 passed；配置按回空表 ⇒ 点名三个缺失类别 |

## 验收条件

- 四类失败模式各一条判据，且**每条都有按压后判红的反证臂**；
- EC-06 两份契约的策略声明与分类映射被判据覆盖；
- `REVIEW_SCORE ≥ 0.8` 与 `panel_rejection()` 逐字未动（`git diff` 可核）；
- 全量 m0 绿。

## 状态历史

- 2026-11-20：建档。cycle 1 因出站 HTTPS 全断而**未能 push 最后一个提交**
  （`18a0668f`）；本轮先做**不需出网**的 EC-03/EC-06，push 一恢复即补推并记账。
- 2026-11-20：**DONE**。网络恢复后先补推 `18a0668f`（CI run `44423270174`），
  随后四个提交落 cycle 2：`b8c2f293` ①、`08330fd8` ③、`8e0fd15a` ②+EC-06、
  `7a0d5d74` ④。本轮**发现并修复两个真实缺陷**（repr 当正文 / 拒冻重复发事件），
  后者只有跑通整条路径才看得见。

## 影响报告

- **Domain/API/schema**：无新域对象；`retry_policy` 是既有 YAML 字段改值。
  ③ 新增一条事件类型（若用专用类型）或复用 `run.failed` —— 优先复用，避免扩事件词表。
- **安全/凭据**：无变化。
- **兼容性/迁移**：重试策略放宽只影响失败路径的重试次数（`max_attempts: 1→2`），
  不改成功路径语义。
- **上游版本影响**：无。
