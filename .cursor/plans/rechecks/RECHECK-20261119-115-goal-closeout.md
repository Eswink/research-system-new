---
id: RECHECK-20261119-115
slug: goal-closeout
title: GOAL-115 收口复检 —— 八条 EC 终态、硬门逐字未动、三次真实读数
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-20
updated_at: 2026-11-20
plan_id: PLAN-20261120-118
parent_goal: GOAL-20261119-115
owners:
  - root-agent
verify_paths:
  - examples/config/llm_endpoints.yaml
  - examples/config/models.yaml
  - packages/application/run_orchestration/panel_advice.py
  - packages/application/run_orchestration/manifest_freeze_events.py
  - adapters/openhands/event_mapping.py
  - tools/verify_goal115_closeout.py
  - tools/goal115_closeout_assertions.py
  - .cursor/plans/goals/evidence/GOAL-20261119-115-dual-review-k3-summary.json
---

# RECHECK-20261119-115

## 结论

**PASS_WITH_WARNINGS**。八条 EC 全 PASS 且各自有实跑证据；三条硬约束（零价模型、
`REVIEW_SCORE ≥ 0.8`、`panel_rejection()` 一行不改、`NOT_JUDGED` 五项）由**源码断言**
钉住而非口头承诺。警告见 `W-1`（`dissent` 三次都为空 —— 是读数不是缺失，但意味着
「一负一过」这个形态**没有在真实 run 上出现过**）。

## 检查结果

收口验证器 `tools/verify_goal115_closeout.py` = 本轮断言集 32 条 + 标准断言集 +
记录面；**实跑 63 条判词、0 FAIL**（`SUMMARY total=63 failed=0`）。

| # | EC | 判法 | 结果 |
| --- | --- | --- | --- |
| 1 | EC-01 换站 + 零价纪律 | 两个 `base_url` 是新站两张脸、都声明 `x-opencode-session`、不在 `/inference/v1` 那棵树；`models.yaml` 每个名字落在**离线夹具**的零价集合 | PASS |
| 2 | EC-02 旧站清零 | 配置面四个旧标记零命中（判据源码里那四个标记按片段拼出，避免判据自命中） | PASS |
| 3 | EC-03 四类失败模式 | 四条判据在树且各自带反证描述；四条反证臂逐条按压过 | PASS |
| 4 | EC-04 三次真实读数 | 三份证据 JSON + 汇总：每次 2 条可归因判词、两个不同目标、1 phase / 2 task、`voters=2`、`independent=true` | PASS |
| 5 | EC-05 advisory 并存 | `panel_advice` 在树且 **AST 判**不 import `Decision`；`panel_rejection` 判负行逐字；`threshold: 0.8` + `operator: GTE` 逐字 | PASS |
| 6 | EC-06 上游可重试 | 四份上游合约 `max_attempts ≥ 2` + 三个瞬时类别（类别对 `FailureCategory` 闭集） | PASS |
| 7 | EC-07 PRD 差距 | 四节 + 去重 `file:line` ≥ 20（实测 23）+ INDEX 登记 + 非 ZDR 事实 | PASS |
| 8 | EC-08 收口 | 本文件 + 验证器 + 断言集 + m0 witness（23/23，`tree changed: False`） | PASS |

## 三条硬约束的逐字守卫

| 约束 | 判据 | 结果 |
| --- | --- | --- |
| 只用零价模型 | 配置的每个 `model_name` ∈ 夹具零价集合（收费名 ⇒ 点名判红） | 通过 |
| `REVIEW_SCORE ≥ 0.8` 一字不改 | 源码文本断言 `operator: GTE` + `threshold: 0.8` | 通过 |
| `panel_rejection()` 一行不改 | 源码文本断言 `rejected = tuple(item for item in verdicts if item[1] != "PASS")` | 通过 |
| `NOT_JUDGED` 五项 | `len(NOT_JUDGED) == 5` | 通过 |
| advisory 不夺真相权 | **AST** 断言模块不 import `Decision`、不调 `fail`/`reject`、不写 store | 通过 |
| 凭据只在 `.env` | `tools/credential_audit.py` 四面 `offenders=0` | 通过 |

## 三次真实读数的如实登记

| run | 终态 | 判词 | 目标 | advisory |
| --- | --- | --- | --- | --- |
| k1 | FAILED | 2 | beam-free + longcat-2.5-free | REJECT |
| k2 | FAILED | 2 | 同上 | REJECT |
| k3 | SUCCEEDED | 2 | 同上 | PASS |

**`dissent` 三次都为空**：两位评审每次都**同向**（两次都判负、一次都判过）。
判据要求的是「判负则 dissent 非空」—— 这三次不是"一负一过"，所以空是正确形态。
但这也意味着：**「一负一过」这个形态只在合成判词上验过，没有在真实 run 上出现**。
这是 warning，不是缺陷。

## 本轮发现并修复的真实缺陷（四个）

| # | 缺陷 | 怎么发现的 |
| --- | --- | --- |
| D-1 | 新站推理面要求 `x-opencode-session`，产品两条腿都不发 ⇒ 纯配置换站必然 400 | 换站前实测 |
| D-2 | 没有 `content` 时把 `object repr` 当正文往下游流（不崩，但更难诊断） | 写 EC-03 ① 判据时判红 |
| D-3 | 拒冻接线第一版**重复发** `run.failed`（helper 单测全绿，只有跑通整条路径才暴露） | 跑真实编排服务 + 真 outbox |
| D-4 | 新读面未登记进**隐私路由表**与**前端路由覆盖表** | 全量 m0 抓到 |

## 警告

- **`W-1`**：`dissent` 在三次真实读数里都为空（两位评审同向）。「一负一过」的分歧形态
  目前只在合成判词上验过。要取到真实分歧，需要更多次 run 或更强的评审提示词差异。
- **`W-2`**：`LLMEndpoint.extra_headers`（本轮新增的产品缝）**未投影进 endpoint 读面**
  （GOAL 残余 `W-3`）。它进域对象、进 sqlite 往返、进两条出网腿，但 `LlmEndpointReadDto`
  里看不到 —— 一次 `400 MissingSessionID` 在控制面上仍看起来像"配置对而请求失败"。
- **`W-3`**：`plan_fallback` 仍是死缝（承接 GOAL-114 `W-2`，逐字未变）。

## 未覆盖

- **`U-1`**：三次真实 run 是**机制可用性**证据，不是评审稳定性证据（无方差刻画、
  无采样控制、三次恰好同向）。
- **`U-2`**：advisory 面只做**读**，不做"建议如何影响下一轮"—— 那属阶梯「复检」的
  下一级，被 GOAL-082 EC-04 的未决取舍卡住。

## 声称边界

- **`R-1`** 不宣称"评审判得对"：判的是两位不同模型各自产出了**可归因**判词、分歧可读。
- **`R-2`** 不宣称"项目安全"（`R-M1` 未收口）。
- **`R-3`** 不宣称"模型采纳了"任何内容：与 GOAL-082 EC-04 的未决取舍无关。

## 无可复用事实

本轮**没有**沉淀新的工程记忆条目：四条真实缺陷（`D-1`…`D-4`）都已在 GOAL 的
「实测发现」表与各子 PLAN 里逐条点名，且它们的形态（配置换站需要新缝 / repr 当正文 /
重复事件只有端到端可见 / 新读面要过两张登记表）属于**该 GOAL 的实测记录**，
不是跨项目通则。`D-1` 若在下一个中转站复现，再升格为记忆。
