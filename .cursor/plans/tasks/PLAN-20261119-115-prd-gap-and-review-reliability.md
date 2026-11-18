---
id: PLAN-20261119-115
slug: prd-gap-and-review-reliability
title: GOAL-115 子计划 —— 复检可靠性（硬门不动 + advisory 并存）+ 中转站切换 + PRD 差距分析
status: IN_PROGRESS
created_at: 2026-11-19
updated_at: 2026-11-19
parent_goal: GOAL-20261119-115
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20261119-115

## 背景与靶子

序 83。建档取证（2026-11-18 实查）：

- `dual_model_review_v1` **24 次 run 全 FAILED、零 SUCCEEDED**，但**全部来自
  2026-10-20 17:02:32–17:49:45 UTC 的单一 47 分钟窗口**，且**换站后一次都没重跑**
  （`openai/hy4flash-exp4` 在全部 `data/*.db` 出现 0 次）。
- 失败分四类，**一半不是"评审判负"**：16 次 `REVIEW_SCORE … GTE 0.8`（评审收到**空产物**
  打 0.0）、7 次 `'MessageEvent' object has no attribute 'content'`（author 崩溃）、
  4 次 `retry budget exhausted`、5 次空 outbox（manifest 拒冻，任务从未派发）。
- 「零成功」有一部分是**设计**：契约要求两位评审都打 ≥0.8，而
  `review_panel_judging.panel_rejection()` 对任何非 PASS 票即失败；
  离线 e2e `tests/e2e/test_two_models_judge_the_same_artifact.py:183`
  **断言 `FAILED` 才算绿**。
- 十一相链 31 次 FAILED 里 retrieval 9 / experiment 6 / plan 5 = 20/31（65%），
  主因上游文献 API 超时/5xx + `max_attempts: 1`。

## 交付面（checkbox）

- [ ] EC-01 换站落地：`llm_endpoints.yaml` 两个 `base_url` → opencode `/go/{openai,anthropic}/v1`；
      `models.yaml` 四个 `model_name` → 免费模型；新判据 `tests/loaders/test_free_model_only_policy.py`
- [ ] EC-02 旧站 pin 全清零：新判据 `tests/tooling/test_relay_pins_are_cleared.py`（白名单进源码）
- [ ] EC-03 四类失败模式各一条判据（`MessageEvent` / 重试策略 / 拒冻写事件 / `UNDER REVIEW` 段）
- [ ] EC-04 三次真实双评审读数 + 证据 JSON（`_EXPECTED_TARGETS` 同轮改为免费模型目标）
- [ ] EC-05 advisory 并存读面（硬门不动、`panel_rejection` 一行不改）
- [ ] EC-06 上游失败可重试性（两份契约的 `retry_policy` + 分类映射）
- [ ] EC-07 `docs/product/PRD_GAP_ANALYSIS.md` 落树 + `docs/INDEX.md` 登记
- [ ] EC-08 收口（`tools/verify_goal115_closeout.py` + 两树 + m0 witness + CI）

## 实施清单

### WP-A 换站（EC-01 + EC-02）

照 `MEM-20261014-218` 的「配置往返」配方，**只改该改的、别多改**：

1. `examples/config/llm_endpoints.yaml`
   - `main.base_url` → `https://opencode.ai/inference/go/openai/v1`
   - `main.discovery.allow_models` → 四个免费模型
   - `agnes-anthropic.base_url` → `https://opencode.ai/inference/go/anthropic/v1`
   - **endpoint id 刻意保稳**（`main` / `agnes-anthropic` 被 5+ 判据引用）
2. `examples/config/models.yaml`：四个 `model_name` + `display_name` + `context_window_tokens`
   （按 `GET /go/v1/models` 的 `limit` 填）。**能力声明按实测，不按声称**——
   尤其 `STRUCTURED_OUTPUT_NATIVE` 与 `TOOL_CALLING_NATIVE` 要逐模型实跑确认。
3. `.env`：`LLM_MAIN_KEY`（gitignored，唯一合法落点）。
4. **不用改**（实测零耦合）：`services/` / `packages/` / `adapters/` 全部产品代码。
5. **钉值判据要同轮改**：`tests/tooling/test_goal108_probe_readings.py:36`、
   `tools/goal108_closeout_assertions.py:29`、`tests/contracts/test_direction_to_report_v2_novelty.py:353`
   的 `FREE_MODELS` 元组；`test_two_models_judge_the_same_artifact_live.py:59` 的
   `_EXPECTED_TARGETS`。

**换站前必须先实测**（旧站有"默认只给 DSML 文本、要 `tool_choice: required`"的先例）：

```bash
# 四个免费模型各跑一次：/v1/models 在列、POST chat/completions 200、
# tool_choice: required ⇒ 标准 tool_calls、stream: true ⇒ SSE、usage 逐次回报
uv run --frozen --no-sync python -B tools/m12_relay_smoke.py
```

**若四个模型全部不支持标准 `tool_calls`** ⇒ 命中 `escalation_triggers` ⇒ BLOCKED 并留证据。

### WP-B 四类失败模式（EC-03）

| # | 缺陷 | 落点 | 修法 |
| --- | --- | --- | --- |
| ① | `'MessageEvent' object has no attribute 'content'` | `adapters/openhands/event_mapping.py:89-95` | 已用 `getattr(llm_message, "content", None)`；需补**单测**钉住「无 `content` 属性时不抛」 |
| ② | 无重试 | `examples/contracts/task_contracts.yaml` 的 `dual_model_review_deliverable.retry_policy`（`:713-716`，现 `max_attempts: 1` + 空表） | 改 `max_attempts: 2` + 显式 `retryable_categories` + `backoff_seconds`（照 `multi_role_review` 的既有形态 `:248-258`） |
| ③ | 拒冻不落事件 | `freeze_manifest` / `rebuild_readiness.py` | 抛出前落一条可读事件（含 `missing` 清单） |
| ④ | `UNDER REVIEW` 段缺失 | `retrieval_prompt.py:142-155`（已修） | 补**真实路径**取证：`content digest:` 标记 + `{task_id}:review_material` 制品 |

每条的判据必须带**反证臂**（按 raw `sha256` 逐字节复原）。

### WP-C 三次真实 run（EC-04）

- 顺序**预先声明**（不挑样本、失败不补跑）。
- 每 run 一个全新 SQLite 库（照 `paired_ablation_live_support` 的形态）。
- **终态不是判据**：`SUCCEEDED` / `FAILED` 都收；判的是 2 条判词 + 目标互异 + 分歧可读。
- 证据 JSON 落 `.cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3.json`。
- **反证臂**：两位评审指向同一模型 ⇒ 独立性判据判红。

### WP-D advisory 并存面（EC-05）

- 新增**只读**读面（HTTP + 编排两级），复用既有 `evaluation/panel_verdict.py` 的聚合结果。
- **硬门不动**：`acceptance_criteria` 与 `panel_rejection()` 一行不改。
- 判据断言「同一份判词 ⇒ 硬门 FAILED 且 advisory 同时可读 1 负 1 过」。

### WP-E 上游可重试性（EC-06）

- 两份契约的 `retryable_categories` 覆盖 `TOOL_TIMEOUT` / `MODEL_*` 瞬时类。
- 只钉策略声明与分类映射，**不**要求成功率提升。

### WP-F PRD 文档（EC-07）

- `docs/product/PRD_GAP_ANALYSIS.md`（本窗口已落，另一窗口补证与登记）。
- `docs/INDEX.md` 登记。

## 验证

```bash
uv run --frozen --no-sync python -B tools/m12_relay_smoke.py
uv run --frozen --no-sync python -B -m pytest tests/loaders tests/tooling -q
uv run --frozen --no-sync python -B -m pytest tests/adapters tests/application/run_orchestration -q
RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
  uv run --frozen --no-sync python -B -m pytest tests/e2e/test_two_models_judge_the_same_artifact_live.py -q
uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
uv run --frozen --no-sync python -B tools/verify_goal115_closeout.py
```

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-00 | 建档 | survey | 24 个 `data/goal091-*.db` + `runs.created_at` | 全来自 2026-10-20 单一 47 分钟窗口；换站后未重跑 |
| EV-01 | EC-01 | command | `tools/m12_relay_smoke.py` | 待填 |
| EV-02 | EC-01 | test | `tests/loaders/test_free_model_only_policy.py` | 待填 |
| EV-03 | EC-02 | test | `tests/tooling/test_relay_pins_are_cleared.py` | 待填 |
| EV-04 | EC-03 | test | 四条反证臂 | 待填 |
| EV-05 | EC-04 | live | `test_two_models_judge_the_same_artifact_live.py` ×3 | 待填 |
| EV-06 | EC-04 | evidence | `.cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3.json` | 待填 |
| EV-07 | EC-05 | test | advisory 读面 + 两向反证 | 待填 |
| EV-08 | EC-06 | test | 两份契约的 `retry_policy` | 待填 |
| EV-09 | EC-07 | doc | `docs/product/PRD_GAP_ANALYSIS.md` | 本窗口已落：4 节 + 来源节 |
| EV-10 | EC-08 | verifier | `tools/verify_goal115_closeout.py` | 待填 |

## 验收条件

- 八条 EC 全部 PASS（EC-04 的达标是**读数**而非终态）；
- `REVIEW_SCORE ≥ 0.8` 与 `panel_rejection()` **逐字未动**；
- `NOT_JUDGED` 五项逐字未动；
- 只有零价模型出现在 `models.yaml`；
- 全量 m0 witness 绿 + 两树复检 `sha256` 相同 + CI 八 job 全绿。

## 状态历史

- 2026-11-19：建档（PLAN + GOAL-115 + PRD 差距分析同轮落树；执行在另一窗口）。

## 影响报告

- **Domain/API/schema**：预期新增一条**只读** HTTP 读面（advisory 面板建议）；
  不改 `acceptance_criteria`、不改 `panel_rejection`。换站只动配置，不动产品代码。
- **安全/凭据**：无新凭据面；凭据仍只从环境读、只落 gitignored `.env`。
  **`iceman-contributor-free` 非 ZDR** —— 它的 prompt 会进训练数据，需在 PRD 文档写明。
- **兼容性/迁移**：换站后旧的 run 库仍可读（`reviewer_model` 是历史事实，不回填）。
- **上游版本影响**：新中转站的模型目录是外部事实，会漂移；AGENTS.md §4 的
  「可重复配置 ≠ 完全模型可复现」口径照旧适用。
