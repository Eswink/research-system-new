---
id: MEM-20260921-103
title: "「模型不存在」没有专属失败类别（实测）；以及两类「按了不红」的假绿判据——文本子串判据被别名前缀骗过，让判据调用会 skip 的函数会把判据自己也变成 skip"
status: ACTIVE
created_at: 2026-09-21
updated_at: 2026-09-21
scope: repository
confidence: 0.9
review_after: 2027-09-21
source_plans:
  - .cursor/plans/tasks/PLAN-20260921-130-runtime-fingerprint-on-read-face.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260921-130-runtime-fingerprint-and-model-absence.md
supersedes: []
tags:
  - model-relay
  - failure-taxonomy
  - live-sample
  - press-tests
  - goal-010
---

# 「模型不存在」的类别面与两类假绿判据（GOAL-010 EC-04 实测）

## 做了什么

两条 EC-04 的判据面事实：① provider 面对**不存在的 model 标识**时的真实行为（用一次最小真实
调用实测，样本 `tests/e2e/test_live_model_absence.py`）；② 新增「样本必须预置条件式」判据时，
**按压**抓出并修好了两个「看起来很严、其实恒绿」的判据形态。

## 为什么这样做

- **「模型不存在」的类别面此前只有装配层推断**（`RECHECK-124` W-2）。中转站完全可能把未知
  model **静默映射**到别的模型（AGENTS.md §4 要防的同名漂移），所以「provider 会拒绝」这句话
  **不能推断，只能实测**。
- **判据不按压就是未知**：本 cycle 的「预置条件式」判据第一版**按压后仍绿**——说明它根本不判
  它声称要判的东西。只有「构造失败 ⇒ 看它红」才能把这种判据抓出来。

## 怎么做与复现

1. **类别面（实测，2026-09-21，端点 `agnes-anthropic`，请求 `research-os-absent-model-v1`）**：
   - 连通性 `GET /models` **通过**（`ok: true`）⇒ 端点与凭据都正常；
   - 那次 chat 被拒，`error_category = MODEL_RELAY_UNAVAILABLE` —— 该类别由 **5xx** 映射
     （`packages/application/ports/model_gateway.py::failure_category_of_http_status`）；
   - 错误正文**点名**了请求的标识；`returned_model_name = null` ⇒ **零回退、无静默映射**。
   - **结论**：`MODEL_RELAY_UNAVAILABLE` 与「中转站故障」**同类别**，且该类别**在可重试集合里**
     （`adapters/relay/transport.py::_RETRYABLE_CATEGORIES`）⇒ **按类别读会读错**；唯一能区分
     两者的读数是**消息里有没有点名模型标识**（而读面今天不解析错误正文）。
   - 复现（预置条件式，默认 skip）：`RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1 LLM_MAIN_KEY=<值>
     uv run --frozen --no-sync python -B -m pytest tests/e2e/test_live_model_absence.py -s`。
     想改类别口径 = 动 `docs/reliability/FAILURE_MODEL.md`，属口径变更，不要顺手做。
2. **两类「按了不红」的假绿判据（可复用）**：
   - **文本子串判据被前缀骗过**：`assert "<开关名>" in 源文件文本` 看着像「样本用了这个开关」，
     把源文件里的开关名改成 `<开关名>_PRESSED` **仍绿**（被断言的字符串是别名的**前缀**）。
   - **让判据调用会 skip 的函数 ⇒ 判据自己也 skip**：成对判据若直接调 `_require_case()`，
     开关被改名时它抛 `pytest.skip.Exception`，pytest 把**判据本身**记为 skipped ——
     **skip 不是红**，整组又「恰好绿」。
   - **正确形态**：断言**行为**（`with pytest.raises(pytest.skip.Exception): …` 判「没开关就跳过」；
     判「有开关就运行」时把 skip **转成 `pytest.fail`**）+ **等价性断言**（样本的开关常量
     `==` 判据里的开关名）。改完**再压一次**确认它是 `FAILED`（不是 skip、不是 passed）。
     落地样例：`tests/architecture/python/test_live_failure_paths_same_source.py` 的
     `TestTheModelAbsenceRowPointsAtAMeasuredSample`。

## 适用边界

- 第 1 条是**单次观测**：**不**声称该 provider 对**所有**未知模型都如此、**不**声称所有中转站
  都这么表现；样本走的是 **endpoint test（probe）** 路径，**不**替代 run 执行路径的失败语义。
- 第 2 条只针对**本次新增**的判据做过按压；仓库里可能仍有「按字符串子串判在场」的判据，
  本次**未**做全仓扫描。

## 来源

- `.cursor/plans/tasks/PLAN-20260921-130-runtime-fingerprint-on-read-face.md`（WP3 落地 / 按压抓出的判据缺陷）
- `.cursor/plans/rechecks/RECHECK-20260921-130-runtime-fingerprint-and-model-absence.md`（W-1 / W-9）
- `docs/integration/LIVE_MODEL_RUNBOOK.md` §7 第 4 条边界；`tests/e2e/test_live_model_absence.py`
