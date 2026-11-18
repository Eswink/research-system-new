---
id: GOAL-20261119-115
slug: review-reliability-and-product-gap
title: 复检在真实路径上第一次产出可归因读数（硬门不动 + advisory 并存），并落下 PRD 差距分析
status: ACTIVE
created_at: 2026-11-19
updated_at: 2026-11-20
owners:
  - root-agent
latest_recheck: null
budget:
  max_cycles: 24
  per_cycle_minutes: 180
  no_progress_stop_cycles: 2
authorization:
  source: user-request
  ref: >-
    序 83（GOAL 号 115）。用户 2026-11-18 四项拍板：
    ① 复检**两条都要** —— 先拿真实路径的可靠性读数，再把 advisory 面做成**并存的第二读面**，
    既有硬门（`REVIEW_SCORE ≥ 0.8` + `COMPLETE_THEN_JUDGE`）**语义一字不改**；
    ② 中转站**原地换 `main`**（不新增第二端点）；
    ③ 四个免费模型**全部可用**：`hy4-flash-free` / `longcat-2.5-free` / `beam-free` /
    `iceman-contributor-free`（后者非 ZDR，用户已知悉并授权）；
    ④ 本轮射程**含 PRD 缺口**（`docs/product/PRD_GAP_ANALYSIS.md`）。
    沿用用户 2026-10-29 全权限预授权；push-to-main-for-CI：只推 main、不 force、
    不重写历史、不推旁支；`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` /
    `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 逐命令传，**绝不写进 `.env`**。
  relay:
    base_url_openai: https://opencode.ai/inference/go/openai/v1
    base_url_anthropic: https://opencode.ai/inference/go/anthropic/v1
    credential_ref: LLM_MAIN_KEY
    free_models:
      - hy4-flash-free
      - longcat-2.5-free
      - beam-free
      - iceman-contributor-free
    free_model_policy: >-
      **只允许** `GET https://opencode.ai/inference/go/v1/models` 回报 cost 全零的模型出现在
      `examples/config/models.yaml`。收费模型名一律不得进配置（判据强制，见 EC-01）。
objective: >-
  让复检域在真实路径上第一次产出**可归因、有分歧、可复算**的双评审读数，并把它同时做成
  「硬门仍在」与「advisory 并存」两件可判事实；顺带把已经修好但**从未在真实链上复验**的
  四类缺陷钉死。
exit_criteria:
  - id: EC-01
    criterion: >-
      **换站落地**：`examples/config/llm_endpoints.yaml` 的 `main.base_url` =
      `https://opencode.ai/inference/go/openai/v1`、`agnes-anthropic.base_url` =
      `https://opencode.ai/inference/go/anthropic/v1`；`main.discovery.allow_models` =
      四个免费模型；`examples/config/models.yaml` 的四个 `model_name` 全部指向免费模型；
      `GET https://opencode.ai/inference/go/v1/models` 实查的零价集合与配置**逐字一致**。
      新判据 `tests/loaders/test_free_model_only_policy.py`：**只允许零价模型名**出现在
      `models.yaml`（收费名 ⇒ 判红并点名）。
    verify: >-
      `uv run --frozen --no-sync python -B tools/m12_relay_smoke.py` 在四个免费模型上各跑一次
      最小 probe（含 `tool_choice: required` 的 `tool_calls` 形态）；
      `uv run ... -m pytest tests/loaders/test_free_model_only_policy.py -q` ⇒ 全绿；
      `uv run ... python -B tools/credential_audit.py` 四面 `offenders=0`。
      **证据（2026-11-20 实跑）**：`tools/m12_relay_smoke.py` ⇒ probe ok=True、
      returned_model_name=hy4-flash-free、5 能力、0 失败；四个零价模型各跑一次
      `tool_choice: required` ⇒ 全返回标准 `tool_calls`；`test_free_model_only_policy.py`
      12 passed / 1 skipped（live 腿默认 skip，`RESEARCHOS_LIVE_E2E=1` 才比夹具）；
      `credential_audit.py` 四面 offenders=0。
    status: PASS
  - id: EC-02
    criterion: >-
      **旧站 pin 全清零**：`192.168.101.9` / `hy4free` / `hy4-preview-f` / `hy4flash-exp4`
      在**产品面与判据面**零命中。豁免面逐条列白名单（历史记录类：
      `.cursor/memory/entries/**`、`.cursor/plans/goals/evidence/**`、
      `.cursor/plans/rechecks/**`、`.cursor/plans/tasks/**` 与既收口 GOAL 的正文），
      白名单本身进判据源码。
    verify: >-
      `uv run ... -m pytest tests/tooling/test_relay_pins_are_cleared.py -q` ⇒ 全绿；
      白名单外的命中逐条点名（路径 + 行号）。
      **证据（2026-11-20 实跑）**：`test_relay_pins_are_cleared.py` 9 passed；
      受判面 200+ 文件、四个标记逐条注入反证臂全红；`docs/integration/` 两页与
      `examples/config/` 三份配置零命中。
    status: PASS
  - id: EC-03
    criterion: >-
      **四类真实失败模式各一条判据**（全部来自 24 次 FAILED 的实测画像）：
      ① `MessageEvent` 无 `content` ⇒ `adapters/openhands/event_mapping.py` 不再抛
      `AttributeError`（单测 + 该消息在真实 run 中不再出现）；
      ② `dual_model_review_deliverable.retry_policy.max_attempts ≥ 2` 且
      `retryable_categories` 非空（当前是 `max_attempts: 1` + 空表）；
      ③ **拒冻必须写事件**：`freeze_manifest` 抛出前落一条可读事件
      （当前 5 次 run 的 `outbox_events` 为空 ⇒ 读面表现为"秒失败无原因"）；
      ④ `UNDER REVIEW` 段在真实提示词里**在场且非空**（`content digest:` 标记 +
      `{task_id}:review_material` 制品）。
    verify: >-
      逐条定向套件 + 逐条**反证臂**：还原成直接属性访问 / `max_attempts` 改回 1 /
      摘掉事件写入 / 摘掉渲染段 ⇒ 各判红，按压后按 raw `sha256` 逐字节复原。
      ④ 另需一次真实 run 的提示词取证（落 `.cursor/plans/goals/evidence/`）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **连续三次真实双评审读数**：新中转站 + 真实 runtime 上跑 `dual_model_review_v1`
      **三次**（预先声明顺序，失败不补跑、不挑样本）。每次必须：2 条 `review_findings` 行；
      `reviewer_model` 是**两个不同**的免费模型目标；同一 `phase_id`、两个不同 `task_id`；
      `panel.voters == 2` 且 `independent is True`；判负则 `dissent` 非空；判词正文落盘。
      **run 终态无论 `SUCCEEDED` / `FAILED` 都算达标** —— 判的是评审读数，不是终态
      （「零成功」有一半是设计：`panel_rejection` 对任何非 PASS 票即失败，
      离线 e2e `test_two_models_judge_the_same_artifact.py:183` 断言 `FAILED` 才算绿）。
    verify: >-
      `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1` 跑
      `tests/e2e/test_two_models_judge_the_same_artifact_live.py` 三次（每 run 一个全新库）；
      证据 JSON 落 `.cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3.json`。
      **反证臂**：把两位评审指向同一模型 ⇒ 独立性判据判红。
      **`_EXPECTED_TARGETS` 必须同轮改为新的免费模型目标**（当前仍钉 `main/glm-5.3` /
      `main/kimi-k2.6`，换站后会假红）。
    status: PENDING
  - id: EC-05
    criterion: >-
      **advisory 并存面**：新增**只读**的"面板建议"读面（HTTP + 编排两级），
      返回聚合结论与逐票分歧。**`acceptance_criteria` 的 `REVIEW_SCORE ≥ 0.8` 一字不动、
      `review_panel_judging.panel_rejection()` 一行不改**。判据断言：同一份判词下，
      硬门仍判 `FAILED`，而 advisory 面**同时**可读到"1 负 1 过"。
      advisory **不产生 `Decision`**、**不动 `NOT_JUDGED` 五项**。
    verify: >-
      新增定向套件（读面 + 两向反证：把 advisory 结论接进 `panel_rejection` ⇒ 判红；
      摘掉 advisory 读面 ⇒ 判红）；一条 e2e 断言两级读面同源。
    status: PENDING
  - id: EC-06
    criterion: >-
      **上游失败的可重试性**（十一相链 31 次 FAILED 里 retrieval 9 / experiment 6 / plan 5
      = 20/31，主因文献 API 超时与 5xx）：`direction_to_manuscript` 与 `dual_model_review`
      两份会话契约的 `retryable_categories` 覆盖上游瞬时失败且 `max_attempts ≥ 2`；
      文献 API 的 timeout / 5xx 归入**可重试类别**并在 `FailureCategory` 闭集内留证。
      判据**只钉策略声明与分类映射**，**不**要求成功率提升。
    verify: >-
      定向套件断言两份契约的 `retry_policy` 形状 + 分类映射表；
      **反证臂**：把 `retryable_categories` 清空 ⇒ 判红。
    status: PENDING
  - id: EC-07
    criterion: >-
      **PRD 差距分析落树且被登记**：`docs/product/PRD_GAP_ANALYSIS.md` 存在、四节齐全
      （市面对照 / PRD 缺口 / 科研 agent 不足 / 优先级），每条结论带仓库内 `file:line`
      证据；`docs/INDEX.md` 登记该文档。
    verify: >-
      定向判据断言四节标题在场、至少 20 条 `file:line` 形态的引用、
      文末含「来源」节；`docs/INDEX.md` 有该路径。
      **证据（2026-11-20 实跑）**：`test_prd_gap_analysis_recorded.py` 9 passed；
      四节齐 + 去重 23 条 `file:line` + `## 6. 来源` 收尾 + INDEX 登记；
      非 ZDR 事实（`iceman-contributor-free` 的 prompt 会进训练）写进 §5.1。
    status: PASS
  - id: EC-08
    criterion: >-
      **全量门与收口**：as-is m0 = `PASS: profile=m0; 23 deterministic checks`
      （`PASS [` 24 行、0 FAILED、`tree changed during the run: False`）；
      `tools/verify_goal115_closeout.py` 断言集 0 FAIL；两树复检判词 `sha256` 相同；
      每提交 CI 八 job 至终态。
    verify: >-
      `uv run --frozen --no-sync python -B tools/run_m0_with_witness.py`；
      `uv run ... python -B tools/verify_goal115_closeout.py`；两树复检脚本。
    status: PENDING
fix_policy:
  same_signature_retries: 3
  cycle_fix_retries: 10
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 把 `acceptance_criteria` 的 `REVIEW_SCORE ≥ 0.8` 改松或删掉（硬门语义不动）
    - 把 advisory 结论接进 `panel_rejection`（并存面不许夺真相权）
    - 为了让三次真实 run 通过而改判据阈值或挑样本/补跑
    - 改 `NOT_JUDGED` 五项
    - 把凭据值写进任何被跟踪文件（只在 gitignore 的 `.env` 的 `LLM_MAIN_KEY`）
    - 使用任何非零价模型（收费模型一律禁止）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 新中转站配额耗尽（429 / 月度上限）且本轮窗口内不重置
  - 四个免费模型**全部**不可用或全部不支持标准 `tool_calls`
  - 三次真实 run 都没落出 2 条可归因判词（那是机制缺口，不是读数）
child_plans:
  - .cursor/plans/tasks/PLAN-20261119-115-prd-gap-and-review-reliability.md
memory_entries: []
---

# GOAL-20261119-115 — 复检在真实路径上第一次产出可归因读数

## 目标与退出标准

EC 表见 frontmatter `exit_criteria`。

**建档取证（2026-11-18，全部实查，这是本 GOAL 的立论基础）**：

| 事实 | 证据 |
| --- | --- |
| `dual_model_review_v1` 24 次 run **全部 FAILED、零 SUCCEEDED** | 24 个 `data/goal091-*.db`，每库一条 run |
| **全部来自 2026-10-20 17:02:32–17:49:45 UTC 的单一 47 分钟窗口** | `runs.created_at` 逐条 |
| **换站后一次都没重跑** | `openai/hy4flash-exp4` 在全部 `data/*.db` 出现 **0** 次 |
| 失败分四类，**一半不是"评审判负"** | 16 次 `REVIEW_SCORE … GTE 0.8`（评审收到**空产物**打 0.0）· 7 次 `'MessageEvent' object has no attribute 'content'`（author 崩溃）· 4 次 `retry budget exhausted` · 5 次空 outbox（manifest 拒冻，任务从未派发） |
| 空产物的根因已修但**从未在真实路径复验** | `packages/application/run_orchestration/retrieval_prompt.py:142-155`（已渲染 `str` 被二次渲染 ⇒ `UNDER REVIEW` 段静默丢弃） |
| 「零成功」有一部分是**设计** | `review_panel_judging.panel_rejection()` 对任何非 PASS 票即失败；离线 e2e `tests/e2e/test_two_models_judge_the_same_artifact.py:183` **断言 FAILED 才算绿** |
| 十一相链失败集中在**前三相** | retrieval 9 · experiment 6 · plan 5 = 20/31（65%）；主因上游文献 API 超时/5xx + `max_attempts: 1` |
| 新中转站可用 | `GET https://opencode.ai/inference/go/v1/models` ⇒ 37 模型；零价 4 个 |
| 精确 base URL | OpenAI 兼容 `…/inference/go/openai/v1`；Anthropic `…/inference/go/anthropic/v1` |

**如实登记（不得读成已完成）**：

- **`SUCCEEDED` 不是本 GOAL 的目标。** 「两位评审都打 ≥0.8」是**内容的**判定，
  不是机制的判定；本 GOAL 判的是「两位不同的模型各自产出了可归因的判词，且分歧可读」。
  EC-04 的达标条件**明确接受 `FAILED` 终态**。
- **advisory 是建议，不夺真相权。** EC-05 新增的读面**不**参与验收门、
  **不**产生 `Decision`、**不**动 `NOT_JUDGED`。
- **三次不是功效检验**：n=3 只证明"机制在真实路径可用"，不证明"评审稳定"。
- **`iceman-contributor-free` 非 ZDR**：prompt 会用于改进模型。用户已授权，
  但**研究与手稿正文会进训练数据**这一事实必须在 PRD 文档里写明（EC-07）。
- **`plan_fallback` 仍是死缝**（GOAL-114 `W-2` 逐字未变）：`fallback.py` 有实现、
  preflight 的独立性判据读 `ModelProfile.fallback`，但**运行期从不按 fallback 切模型**。
  它牵涉评审独立性的穷举结论 ⇒ 本 GOAL **只登记不修**。
- **PRD 缺口里的大部分不做**：见「不进入循环 / 需人工拍板」。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的幂等恢复六条，以「迭代日志最后一行 + 工作树实况 +
远端实况」判定续点。任何一步完成**立即**回写本文件。禁止凭记忆假设上一轮状态。

## 单 cycle SOP

① derive：从剩余 EC + 上一轮「剩余差距」圈定最小可独立验收主题 → 写子 PLAN
（`.cursor/plans/tasks/`，frontmatter 带 `parent_goal` 并投影 `ALL_PLAN`）→
② 执行：按 WP 推进，每 WP 独立 commit，**只加显式路径** →
③ 本地验证：实现完成后先自查**规模门禁**（50 行函数 / 450 行文件）与**快照类门禁**
（OpenAPI / 设计基线），再跑全量 m0 + 受影响定向套件 + web 门 →
④ commit（子 PLAN 收口：RECHECK 完成后 DONE）→
⑤ push + CI（push 前 `git pull --ff-only origin main`；只推 main；轮询到终态）→
⑥ 失败分类纠错（见下表）→
⑦ 回写（EC 状态 / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史），
**收尾前必须完成回写**。

**记录顺序纪律**（GOAL-019 起适用）：写记录 → 记录面判据 → **最后**跑
`tools/run_m0_with_witness.py` → 之后**不改树**。

## CI 失败分类与纠错

| 分类 | 识别 | 处置 |
| --- | --- | --- |
| (i) 判据实现缺陷（自己的判据错） | 判据在正确代码上判红 / 按压不红 | 改判据并在迭代日志点名；**不改产品迁就判据** |
| (ii) 环境资源型 | 超时 / 并发 flake / OTLP teardown race / `evolution_state.json` WinError 5 | `rerun-failed-jobs`；**绝不动阈值** |
| (iii) 产品真缺陷 | pytest/playwright 断言指向产品代码 | 修复 + 反向按压；新 commit 点名 `goal115` |
| (iv) 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 ⇒ BLOCKED |
| (v) 治理/安全门禁 | validator / Mimosa 命中新增项 | 按处置文档修或登记误报；**不得绕过**；不得宣称安全 |

## 终止与收口

- **ACHIEVED**：八条 EC 全 PASS + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  全量 m0 witness 绿（`PASS [` 24、0 FAILED、`tree changed: False`）+
  两树复检 `sha256` 相同 + CI 八 job 全绿 + 本文件收口（`latest_recheck` 指向真实文件）。
- **BLOCKED**：连续 2 轮零 EC 推进；或命中 `escalation_triggers` 任一条。
- **ABORTED**：用户叫停。

## 不进入循环 / 需人工拍板

以下来自 `docs/product/PRD_GAP_ANALYSIS.md`，**都改产品边界，需单独拍板**：

| # | 事项 | 为什么不能自动做 |
| --- | --- | --- |
| 1 | 真实投稿端点 / 期刊对接 | 决定外部世界互动，需产品决策 |
| 2 | `journals.yaml` 真实化（真 ISSN / 影响因子） | 涉及对外声明，且"不是评分"是刻意的 |
| 3 | RBAC / 多租户 / `access_control.yaml` 接通 | M18 整块，改 Canonical State 边界 |
| 4 | `AUTHORED` 脚本默认开启 | 安全面扩大，§9 默认 deny 姿态 |
| 5 | `retmax` **出厂默认值**提高（机制已在：四级回落、上限 100；见 `PRD_GAP_ANALYSIS.md` §3.3） | 影响成本与检索语义，需拍板取值 |
| 6 | 假设发散（`HypothesisSet` 域概念） | 新域概念，改 Canonical State |
| 7 | 长时程 / 分支探索语义 | 重写编排语义，代价远大于收益 |
| 8 | 读面认证 | 与既有「读面永不认证」的设计相悖 |
| 9 | `plan_fallback` 接线 | 要重算评审独立性的穷举结论 |

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | 见「CI 台账」 | 治理 `validate.py` 绿；记录面判据绿 | 见「CI 台账」 | — | EC-01…08 全 PENDING | cycle 1 = EC-01（换站落地 + 免费模型纪律） |
| 1 | `PLAN-20261120-116`（换站 + 零价纪律 + 会话头缝） | `aad730b3` 静态路由头两条腿 / `a262323a` 换站 + 两个新判据 + 钉值判据同轮改 / `ad550bff` PRD 判据 + goal098 口径修正 / `727659b1` 记录 / `2757edd8` 判据不自豁免 / `d7ad8547` RECHECK + 首批门修复 / `28b2e65c` live 开关单源 + 工具清单登记 | `tests/adapters/{relay,openhands}` + `tests/loaders` 227 绿；`tests/{architecture,application/preflight,api}` 1102 passed / 4 skipped；`verify_goal108` 87/0；`verify_goal098` 104/0；**全量 m0 = `PASS: profile=m0; 23 deterministic checks`（exit 0，`tree changed during the run: False`，head `28b2e65c`）**；新判据反证臂逐条咬合 | 见「CI 台账」 | — | **EC-01 PASS**（四模型 `tool_calls` 实测 + probe ok=True + 零价判据 + 双反证）；**EC-02 PASS**（旧站标识在产品/判据面零命中，白名单逐条给理由）；**EC-07 PASS**（四节 + 23 条去重 `file:line` + INDEX 登记 + 非 ZDR 事实） | cycle 2 = EC-03（四类失败模式各一条判据） |

**cycle 1 的实测发现（写进记录，不得只留在会话里）**：

| # | 事实 | 影响 |
| --- | --- | --- |
| D-1 | 新站 `/inference/go` 的推理面**要求 `x-opencode-session`**，缺它 400（鉴权通过也拒） | 纯配置换站**不可能**成功 ⇒ 本轮必须新增 `LLMEndpoint.extra_headers` 缝 |
| D-2 | `adapters/relay/completions.py` 的 chat / responses 腿**从不传 headers**（走 transport 默认头） | 静态头只有 Anthropic 腿会发出去；四条腿统一到 `_headers()` 才修好 |
| D-3 | 零价恰四个，但 `iceman-contributor-free` **不支持** `structured_output` | 它**不**声明 `STRUCTURED_OUTPUT_NATIVE`（按实测声明） |
| D-4 | `hy4-flash-free` 是 reasoning 模型：`max_tokens=256` + `tool_choice: required` ⇒ `finish_reason: length`、`tool_calls` 空 | 给它工具面时预算 ≥ 2048；写进模型配置注释与端点文档 |
| D-5 | `tools/goal098_closeout_assertions.py` 断言「作者必须落在 `deepseek-v4-pro-0813`」 | 那是把运营数据写成判据（GOAL-108 已总结过的同一教训）⇒ 改成用产品解析器判**目标不相交**，分文件以守 450 行门 |
| D-6 | `tests/tooling/test_goal108_probe_readings.py` 读的是 GOAL-108 台账（历史记录） | 它对旧模型名**不豁免**会自相矛盾 ⇒ 白名单给它一条**精确文件**豁免 + 理由，当前零价纪律由 EC-01 判据判 |
| D-7 | 旧站 `192.168.101.9:8798` **仍在线**（实测 200） | 换站是**纪律选择**，不是旧站故障；记录不得写成"旧站不可用" |

## 状态历史

- 2026-11-19：建档。取证见上表（24/24 全来自单一 47 分钟窗口、换站后未重跑、
  四类失败中一半不是判负）；用户四项拍板写进 `authorization.ref`；
  PRD 差距调研交付物 `docs/product/PRD_GAP_ANALYSIS.md` 同轮落树。
- 2026-11-20：cycle 1 收口（`PLAN-20261120-116`）。**EC-01 / EC-02 / EC-07 PASS**。
  换站落地在**新增一条产品缝**之后才成立：新站的推理面要求 `x-opencode-session`
  （缺它 400，鉴权通过也拒），而产品两条腿都不发 ⇒ `LLMEndpoint.extra_headers`
  + `request_headers(..., extra_headers)` + `build_llm(extra_headers=...)`。
  四个零价模型实测都返回标准 `tool_calls`（escalation 未命中）；
  `iceman-contributor-free` 实测**不支持** `structured_output` ⇒ 不声明该能力。
  残余：`W-3`（`extra_headers` 未投影进 endpoint 读面）。

## 残余与未覆盖范围

（每轮收口时追加。`tools/next_round_charter.py` 从这里读出下一轮 charter。）

### 残余

- `W-1`（承接 GOAL-114）**采集器仍是判据侧驱动**：产品面没有"从 run 库自动汇总 k×2"的命令。
- `W-2`（承接 GOAL-114）**`plan_fallback` 是死缝**：有实现、被 preflight 读、运行期从不切。
- `W-3`（cycle 1 新增）**`LLMEndpoint.extra_headers` 未投影进 endpoint 读面**：
  它进域对象、进 sqlite 往返、进两条出网腿，但 `LlmEndpointReadDto` 里看不到。
  缺它的代价是「一个 400 MissingSessionID 在控制面上看起来像配置对而请求失败」。
  没做的理由：投影会连带 OpenAPI 快照 + `web/src/types.ts` + e2e 夹具三处同步，
  而 EC-01 判的是配置与出网。**这是缺口不是成就**。

### 未覆盖范围

- `U-1` 三次真实 run 是**机制可用性**证据，不是评审稳定性证据（无方差刻画、无采样控制）。
- `U-2` advisory 面只做**读**，不做"建议如何影响下一轮"——那属阶梯「复检」的下一级，
  被 GOAL-082 EC-04 的未决取舍卡住。

### 声称边界

- `R-1` **不宣称"评审判得对"**：判的是两位不同模型各自产出了可归因判词、分歧可读。
- `R-2` **不宣称"项目安全"**（`R-M1` 未收口）。
- `R-3` **不宣称"模型采纳了"任何内容**：与 GOAL-082 EC-04 的未决取舍无关。

## CI 台账

（逐提交逐 job。**零 run ≠ cancelled**；判红也如实登记。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| （建档提交） | 待回填 | 待回填 | GOAL-115 建档 + PLAN-115 + PRD 差距分析 + MAINLINE 序 83 + 归档 |
| `aad730b3`…`d6dff1e8`（9 个提交，push 为一个批次） | [`44380740088`](https://github.com/Eswink/research-system-new/actions/runs/44380740088) | **success（8/8 job）** | cycle 1：换站 + 会话头缝 + 两判据 + PRD 判据 + 两轮门修复 + m0 见证刷新 |

**CI 八 job 结论（run `44380740088`，head `d6dff1e8`，全部 `completed / success`）**：

| job | 结论 |
| --- | --- |
| `quality-ubuntu-latest` | success（23/23 m0） |
| `quality-windows-latest` | success（23/23 m0） |
| `observability-overhead-ubuntu-latest` | success |
| `observability-overhead-windows-latest` | success |
| `eval-gate` | success |
| `container-quality` | success |
| `collector-quality` | success |
| `console-frontend` | success |

**如实登记**：九个提交是**一次 push**（批次推送），所以那次 CI 只覆盖了**末态树**
（`d6dff1e8`）。中间提交（`aad730b3`…`9aaea0d1`）**没有各自的 CI run** ——
它们的正确性只由「末态树包含它们且末态绿」间接保证，加上 push 前本地 m0 在同一末态
上的 23/23。不把它们写成"逐提交全绿"。

**记账提交 `e5b3bcf9` 的 CI 判红（如实登记，不藏）**：

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `e5b3bcf9`（CI 台账本身） | [`44384030299`](https://github.com/Eswink/research-system-new/actions/runs/44384030299) | **failure** | `quality-{ubuntu,windows}` 在 `test_m0_witness_matches_the_tree` 判红：**改记录 ⇒ 见证失效**。另 6 个 job 全绿 |

**归因（类别 i/ii 的交界，但责任在流程而非产品）**：这一条**不是产品缺陷**，
也不是环境 flake —— 它是本仓既有的**记录顺序纪律**：写记录 → 跑门 → 不再改树。
我把台账提交放在 m0 之后，于是见证绑定的是**旧**树。修法与判据消息逐字一致：
把记录推到最后一个动作，再跑一次 m0，之后不再改树（见下一行）。

**本地门读数（2026-11-20，head `28b2e65c`，全部实跑）**：

| 面 | 读数 |
| --- | --- |
| 全量 m0 | `PASS: profile=m0; 23 deterministic checks`；`exit_code=0`；`tree changed during the run: False` |
| 受影响定向套件 | `tests/adapters/{relay,openhands}` + `tests/loaders` 227 passed |
| 架构 / 预检 / API | 1102 passed / 4 skipped |
| 收口资产 | `verify_goal108` 87/0；`verify_goal098` 104/0 |
| 凭据审计 | `tools/credential_audit.py` 四面 `offenders=0` |
| lint / format / mypy | `ruff check` 0；`ruff format --check` 1462 files clean；mypy 1452 files clean |

**两轮门修复的如实登记**：首轮 m0 判红 5 条（lint / format / mypy / pytest / framework-validate），
**全部来自本 cycle 自己的新文件**，与换站无关；修完第二轮只剩 `python/tests` 的 5 条，
同样全部是新的（单源开关被绕过 / 拆出的工具脚本未登记 / 两处格式）。第三轮 23/23。
