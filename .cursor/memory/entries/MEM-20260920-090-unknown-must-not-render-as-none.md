---
id: MEM-20260920-090
title: "三态判定必须把「未知」与「无/一致」在**文案**上分开：只给中性标签会让「没探到」被读成「没问题」——域层与渲染层各需一条判据"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-117-model-drift-visibility-three-states.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-117-model-drift-visibility-three-states.md
supersedes: []
tags:
  - drift
  - honesty
  - three-state
  - read-face
  - agenets-md-section-4
---

# 「未知 ≠ 无漂移」：三态判定的第二态与第三态必须在读面上分开（GOAL-20260920-008 / cycle 4）

## 做了什么

AGENTS.md §4 要求「模型同名漂移必须可见」，而改动前本仓**没有任何地方**把 probe 返回的
模型标识与登记声明的 `model_name` 比较——读面只把两者并排显示。落地为三态：

- 域：`packages/domain/model_drift.py::assess_model_drift`（纯函数，唯一比较点）
  + `ModelDriftState`（`MATCH` / `DRIFT` / `UNKNOWN`）；
- API：`ProbeResultDto.drift`（state / declared / returned / detail）；
- 页面：`probe-drift` 块三套文案（中英各一套），`DRIFT` 点名两个值，
  `UNKNOWN` 自带反义「**未知不等于无漂移**」；
- 文档：`MODEL_PROBE.md` 漂移判定节 + `LLM_ENDPOINTS.md` §8。

## 为什么这样做（可复用结论）

1. **「未知」是最容易被美化的一态**：实现总是倾向把「没拿到数据」渲染成「没问题」——
   一次失败的探测、一个不返回 `model` 字段的中转站、一个被跳过的检查，都会变成
   「看起来没事」。所以 `UNKNOWN` 必须是**独立枚举值**（不是 `None`/空串）、
   必须有**自己的文案**，而且文案里要**明写它不是「无」**。
2. **一条事实需要两条判据**：域层判据（F1：把 `UNKNOWN` 改判 `MATCH` ⇒ 3 red）保证判定不退化；
   渲染层判据（F3：把 `UNKNOWN` 的文案换成 `MATCH` 那句 ⇒ 1 red）保证**显示**不退化。
   只做前者，页面仍可能把未知画成一致；只做后者，DTO 里可能压根没有第三态。
3. **刻意的严格比聪明的归一化诚实**：只做 `strip()`，大小写差异、日期后缀一律 `DRIFT`。
   归一化（折叠大小写、剥后缀）在真实中转站上会少很多噪声，但那是**替 provider 打包票**——
   本仓无法证明 `model-a` 与 `MODEL-A` 是同一底层模型。噪声的代价写在文档里，由人判。
4. **可见性 ≠ 熔断**：`DRIFT` 不自动禁用模型、不改 eligibility。判据只要求「把差异摆出来」；
   自动处置是策略决策，需要另外的授权与记录。
5. **三态判据的既有同族**：`provider_fingerprint_available` 的 true/false
   （页面必须渲染 unavailable，禁止美化）与 `CapabilitySource`
   的 `PROBED`/`USER_DECLARED`/`DISCOVERED` 是同一种「来源可见性」建模。

## 怎么做与复现

```sh
# 域：三态 + 边界（None/空串 ⇒ UNKNOWN；大小写差异 ⇒ DRIFT）
uv run --frozen --no-sync pytest -q tests/domain/test_model_drift.py

# API：三态可达（含「失败 ⇒ UNKNOWN 且 != MATCH」）；词表同源
uv run --frozen --no-sync pytest -q tests/api/test_models_api.py tests/architecture/python/test_protocol_vocabulary.py

# 页面：三态渲染 + UNKNOWN 反义文案（含反向断言：不得出现 Match/agree）
pnpm --dir apps/web exec playwright test models-drift-visibility --reporter=line

# 反证（先红后复原）：域 UNKNOWN→MATCH / DTO 摘掉 drift / 页面 UNKNOWN 用 MATCH 文案
```

## 适用边界

- 适用于**任何「取不到就看起来没事」的判定**：漂移、指纹、探针、覆盖率、凭据存在性。
  做法是把「未知」升为独立状态并在文案里显式反义，而不是靠 `None` 兜底。
- 三态判定的**严格口径是本仓的决定**，不是通用事实：别的系统可能选择大小写不敏感比较；
  换口径时，域判据与文档要一起改（判据里写死了「大小写差异 ⇒ DRIFT」）。
- drift 目前**不持久化**（只在 probe 响应里）：跨会话回看、跨次 fingerprint 比较都还做不到；
  要落地需要先想清楚它与 `ModelRuntimeFingerprint` 的关系（见 RECHECK-117 W-2/W-3）。
- live 语义**未实测**（无凭据）：真实 provider 究竟回什么标识、会不会带渠道后缀，
  仍是没有样本的空白。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-117-model-drift-visibility-three-states.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-117-model-drift-visibility-three-states.md`（F1–F3、W-1…W-6）
- 代码：`packages/domain/model_drift.py`、`packages/domain/enums.py`（`ModelDriftState`）、
  `services/api/dto/models.py`（`ModelDriftDto`）、
  `apps/web/src/features/models/ModelDetails.tsx`（`ModelDriftNotice`）、
  `docs/integration/MODEL_PROBE.md`（漂移判定节）
- 相关：[[MEM-20260920-089]]（读面谎言要用措辞判据钉）、[[MEM-20260920-088]]（新渲染分支可能落在设计门盲区）
