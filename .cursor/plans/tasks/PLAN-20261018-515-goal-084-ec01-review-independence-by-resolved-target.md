---
id: PLAN-20261018-515
slug: goal-084-ec01-review-independence-by-resolved-target
title: GOAL-084 cycle 1 — 评审独立性的解析面与判定面（EC-01…EC-04）
status: CANCELLED
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-084
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-516-goal-084-ec01-review-independence-by-resolved-target.md
memory_entries: []
---

# PLAN-20261018-515 — GOAL-084 cycle 1

## 验收条件

- [x] **EC-01**：一个 agent 的**全部可能执行目标**（primary + **每个** fallback）解析成
      `(endpoint, model_name)` 集合；解析不了 ⇒ **点名**（不静默空集）；确定性
- [x] **EC-02**：判定比较**解析后的目标**（出厂目录下 `research_strong` 与 `reviewer_gamma`
      **相交**）；**按压**：换不同 `model_name` ⇒ 不相交
- [x] **EC-03**：fallback 路径一并覆盖（`research_strong.fallback` 含 `reviewer_gamma`、
      `critic_independent.fallback` 含 `research_alpha`）；**反证**：清空 fallback ⇒ 相交消失
- [x] **EC-04**：接进既有 `check_heterogeneity`（`check_team` → `run_preflight` 的必经之路）；
      命中 ⇒ 点名目标与两侧角色；**按压**：关掉目标解析 ⇒ 回落 id 口径 ⇒ 变绿
- [x] 零回归（application + loaders + contracts **1735 passed**）
- [x] **EC-05 不在本 cycle 的射程**（如实登记：它是收口 cycle 的交付物；本 PLAN 只做 EC-01…EC-04）

## 目标

让「评审**独立于**生产者」从**声明上的名字差异**变成**可判的解析事实**。

## ★ 建档实测（为什么这是缺口）

1. 出厂目录**四个** ModelDefinition（`agnes_flash` / `research_alpha` / `coding_beta` /
   `reviewer_gamma`）**全部** `model_name: deepseek-v4-flash-vision` + `endpoint: main`；
2. agent 绑定看着不同（`MODEL_PROFILE research_strong` vs `EXPLICIT_MODEL reviewer_gamma`），
   但解析到**同一个底层模型**；
3. `research_strong.fallback = [reviewer_gamma]`、`critic_independent.fallback = [research_alpha]`
   ⇒ 名字就叫「独立评审者」的 profile 可回落到生产者模型；
4. `check_heterogeneity` **已存在**但比的是 **model id** ⇒ id 不同 ⇒ 判绿。

## 实施清单

1. **WP-A**（解析）：`packages/application/preflight/review_independence.py` ——
   `resolve_agent_targets` / `resolve_targets_by_role` / `describe_target`（纯函数、零出网）。
2. **WP-B**（判定）：`role_checks._panel_role_map` 的模型集合改装**解析后的目标**；
   解析不了 ⇒ **回落 model id**（既有口径，不比原来更松）。
3. **WP-C**（判据）：`tests/application/test_review_independence.py`（13 条）+
   `tests/application/preflight/test_review_independence_gate.py`（5 条，含按压）。

## 影响报告

- **产品代码**：新增一个纯函数模块；`role_checks.py` 的 `_panel_role_map` 改判定面
  （+ 回落路径）。`check_heterogeneity` 的**语义收紧**（同 `model_name` 不同 id ⇒ 违规）。
- **受判面**：`test_m4_heterogeneity.py` **一条用例收紧 + 一条反证新增**（逐条申报：
  `test_heterogeneity_allows_distinct_models` 的 `model-2` 改为不同 `model_name`；
  新增 `test_a_model_with_the_same_underlying_name_is_not_distinct`）。
  **其余一字未动**（既有 `test_heterogeneity_rejects_shared_writer_reviewer_model` 等全绿）。
- **读面 / DTO / 路由 / 快照**：零改动。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**
- **出厂目录**：**一字未改**（`examples/config/**` 未动 —— `forbidden` 明确禁止靠改目录制造差异）。

## 残余与未覆盖

见 GOAL：`W-2`（只判模型是否同一个）、`W-3`（不采购第二个模型）、`W-4`（只判声明的评审关系）。

## 工程记忆

**无可复用事实**（本轮口径写进本 PLAN 与 RECHECK-516；判据文件即事实面）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01/02/03 | **13 passed** | `uv run --frozen --no-sync python -B -m pytest tests/application/test_review_independence.py -q` |
| EC-04（含按压） | **5 passed** | `... tests/application/preflight/test_review_independence_gate.py -q` |
| 异构门（含收紧与反证） | **5 passed** | `... tests/application/test_m4_heterogeneity.py -q` |
| 零回归 | **1735 passed, 73 skipped** | `... -m pytest tests/application tests/loaders tests/contracts -q` |
| 静态门 | ruff 绿 / mypy **1272 files no issues** | — |
| 规模门 | **1282 passed** | `... tests/tooling/test_python_source_limits.py -q` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | IN_PROGRESS | cycle 1 建档（解析 + 判定 + fallback）。 |
| 2026-10-18 | DONE | EC-01…EC-04 全 PASS（23 条判据）；一条既有用例**随语义收紧**并新增反证；出厂目录零改动。 |

## 回退说明（**以本节为准**）

本 PLAN 的实现已 `git revert 77577728` 回退：接入产品路径后，`m12_reference_research_v1`
等出厂协议因 writer/reviewer 同模型被 preflight 判 `HETEROGENEITY_VIOLATION` ⇒ **freeze 拒冻**
⇒ 一批既有 API 测试红。三条出路都撞到「需拍板」，详见 GOAL 的「cycle 1 的取舍记录」。

**上面的验收条件与证据只代表「实现期读数」**，不代表产品可用性；本 PLAN 记为取消。
