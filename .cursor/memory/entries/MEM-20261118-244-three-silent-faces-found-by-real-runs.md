---
id: MEM-20261118-244
title: "真实 run 抓到的三个静默面：拒冻不落事件、相 id 不匹配静默跳过、assemble 缺 runtime 回落 Fake"
status: ACTIVE
created_at: 2026-11-18
updated_at: 2026-11-18
scope: repository
confidence: 0.93
review_after: 2027-05-18
source_plans:
  - .cursor/plans/tasks/PLAN-20261117-114-paired-ablation-readings.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261118-114-paired-ablation-readings.md
supersedes: []
tags: [preflight, freeze, phase-id, runtime-selection, live-run, goal114]
---

# 真实 run 抓到的三个静默面

## 做了什么

把配对消融推到真实 run 上（六次），六次**全部在 0.4–0.7 秒内 FAILED** 且读面读不到
原因。定位出三个互相独立的「失败被吞掉」形态，各自处置：

1. **拒冻不落事件**：`TOOL_HEALTH_UNPROVEN` 是 WARNING 且无接受通道 ⇒
   `freeze_manifest` 抛错 ⇒ 事件列表为空、`manifest_digest` 为 null。
2. **相 id 不匹配静默跳过**：出厂检索面把调用表钉在 `RETRIEVAL_PHASE = "retrieval"`，
   `planned_in_this_phase` 对不匹配的相返回 False。
3. **`assemble()` 缺 `agent_runtime` 回落 Fake**：Fake 只发 `analysis_report`。

另记一条**判据**缺陷：`read_plan_payload` 不传 `known_memory_ids` ⇒ `citation_count`
结构上恒为 0（不可能判红）。

## 为什么这样做

三条都不是「配置写错」，而是**产品面把失败藏起来了**：
- 冻结前失败 ⇒ **没有事件可读**（事件链是读面的唯一窗口）；
- 静默跳过 ⇒ 失败归因落在下游验收门（`minimum_retrieved_sources`），不是真实原因；
- 执行体回落 ⇒ 症状（交付物名不对）与「模型没写」不可区分。

判据缺陷之所以危险，是因为它**看起来正常**（0/0 的读数完全合理），且永远绿。

## 怎么做与复现

- 拒冻：直接调 `compile_and_preflight(...)` + `freeze_manifest(...)` 看异常，**不要**
  指望事件链；显式运维上下文用生产 `_live_preflight(deps, catalog, project)` 现算，
  只把 provider 声明 HEALTHY。
- 相 id：新协议若要用运行链检索，相 id 必须是 `retrieval`（`retrieval_wiring.RETRIEVAL_PHASE`）；
  判据可用 `tests/contracts/test_ablation_plan_probe_protocol.py::
  test_the_phase_id_is_the_one_the_shipped_retrieval_face_targets` 的形态钉住。
- 执行体：`assemble(ApiSettings(..., agent_runtime=OPENHANDS_RUNTIME))`；漏了它时
  交付物名会是 `analysis_report`（Fake 的缺省事实名）。
- 判据分母：`read_plan_payload(payload, known_memory_ids=...)`；分母必须来自**该臂的
  持久事实**（`present` 臂库里有那一行 ⇒ 分母是它；`absent` 是空集）。

## 适用边界

- 「拒冻不落事件」的处置是**显式运维上下文**（既有路径），不改门禁；`TOOL_HEALTH_UNPROVEN`
  仍然没有接受通道，这是既有缺口（`real_retrieval_research_v1.yaml` 已登记）。
- 相 id 那条**不是**建议改写 `RETRIEVAL_PHASE`：改它会同时影响全部既有协议的检索相位。
- 判据分母那条只对「按已知 id 集合计数」型判据成立；自由文本里的实体计数不适用。

## 来源

- `.cursor/plans/tasks/PLAN-20261117-114-paired-ablation-readings.md`
- `.cursor/plans/rechecks/RECHECK-20261118-114-paired-ablation-readings.md`
- `.cursor/plans/goals/evidence/GOAL-20261117-114-ablation-k3.json`
- 现场：六次 run 的墙钟 0.4–0.7 秒（失败）、196.4–306.7 秒（成功）
