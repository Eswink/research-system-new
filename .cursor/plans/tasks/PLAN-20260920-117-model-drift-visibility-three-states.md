---
id: PLAN-20260920-117
slug: model-drift-visibility-three-states
title: 漂移可见性三态：probe 返回的模型标识 vs 登记声明值（一致 / 漂移点名 / 未知）（EC-05）
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 4 = EC-05（漂移可见性）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（登记真实端点与模型、允许一次 live-gated 真实 run，最小必要次数）与 AGENTS.md §4（模型同名漂移必须可见：无法证明底层模型完全一致时必须标注「可重复配置」而非「完全模型可复现」）。本 PLAN 遵守：不改 Policy/eligibility、不引入依赖、默认门保持离线、真实端点调用最小必要次数；**凭据缺失时 live 分支如实 skip，skip 不是 PASS**。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-117-model-drift-visibility-three-states.md
memory_entries:
  - .cursor/memory/entries/MEM-20260920-090-unknown-must-not-render-as-none.md
---

# PLAN-20260920-117 — 漂移可见性三态（GOAL-008 cycle 4 = EC-05）

## 目标

把 AGENTS.md §4「模型同名漂移必须可见」从**原则**变成**可判事实**：

1. **三态可判**：probe 返回的模型标识与登记声明值比较后，读面必须落在
   **一致（MATCH）** / **漂移（DRIFT，点名两边的值）** / **未知（UNKNOWN，未探到）** 之一；
2. **「未知 ≠ 无漂移」**：未探测 / provider 没回模型名 / 探测失败 ⇒ `UNKNOWN`，
   读面**不得**渲染成「一致」或「无漂移」（这正是 §4「无法证明一致时必须标注」的读面落实）；
3. **比较规则写死且不装懂**：只做 `strip()` 后的**精确**比较；大小写等任何其他差异
   一律记 `DRIFT` 并**点名两个原值**——本仓无法证明它们指向同一底层模型，
   宽松归一化会变成「替 provider 打包票」；
4. **live 分支如实 skip**：本机无该端点凭据 ⇒ 真实 probe 不跑，记录 skip 事实；
   离线判据（域分类器 + API DTO + 页面三态渲染）仍须全绿。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **数据已有、比较没有**：`ModelProbeResult.returned_model_name`
   （`packages/domain/models.py:183`）由三条 relay 形态分别填（`chat_api.py:56`、
   `anthropic_api.py:137`、`responses_api.py:114`）；`probe.py:195` 把它带进结果；
   `ProbeResultDto.returned_model_name` 与页面 `ProbeSummary`
   （`apps/web/src/features/models/ModelDetails.tsx:123`）只把它**显示出来**，
   **全仓没有任何地方把它与 `ModelDefinition.model_name` 比较**（`rg "drift" packages/ services/ apps/web/src` 无命中）。
2. **指纹只在有 `system_fingerprint` 时构建**：`services/api/routers/models.py::_probe_fingerprint`
   在 `result.system_fingerprint is None` 时返回 `None` ⇒ 读面已有
   「provider fingerprint unavailable」这一条诚实分支（页面 `provider_fingerprint_available`）。
3. **探测失败路径**：`probe.py` 的失败分支不填 `returned_model_name`（保持 `None`）
   ⇒ 天然落 `UNKNOWN`。
4. **Fakes 的注入面**：`FakeModelGatewayOptions`（`adapters/fakes/model_gateway.py:20`）
   是唯一的注入参数对象；`_ok_probe()` 与 `complete()` 目前**硬编码**
   `returned_model_name="model-alpha"` ⇒ 要造「漂移」夹具必须先让它可配（默认值不变）。
5. **域模块体量**：`packages/domain/models.py` 272 行、`enums.py` 338 行（450 行硬上限在望，
   但都不宽裕）⇒ 分类器另起 `packages/domain/model_drift.py`，枚举进 `enums.py`（与
   `ThinkingIntensity` 同处）。
6. **OpenAPI 快照**：`docs/api/openapi.m13.json` 由 `tools/gen_openapi.py` 生成，
   `tests/contracts/test_openapi_snapshot.py` 是 drift 门 ⇒ DTO 加字段必须重生成。
7. **契约 schema**：`schemas/probe-result.schema.json` + `examples/contracts/probe_result.yaml`
   与 `model-runtime-fingerprint` 同族（`tests/tooling/`、`tests/loaders/` 有加载判据）。
8. **live 现状**：cycle 3 已核实本机候选环境变量全 absent、`endpoint:*` 命名环境变量 0 个
   ⇒ 真实 probe 的 live 分支本轮**只能 skip**（记录 skip，不记 PASS）。

## 口径（先写死，避免实施时漂移）

- **三态的定义**：`MATCH` = `declared.strip() == returned.strip()`；`DRIFT` = 两者都存在但不
  相等；`UNKNOWN` = `returned` 为 `None` 或空串（未探到）。**没有第四态**：
  「大小写不同」属 `DRIFT`（点名两值即可，由人判断），不做大小写折叠。
- **`UNKNOWN` 的读面文案必须自带反义**：中英都要写出「未知 ≠ 无漂移」
  （英文 `unknown is not the same as no drift`），否则「没探到」会被读成「没问题」。
- **`DRIFT` 的读面必须点名两个值**（declared + returned），不得只说「有漂移」。
- **不做的事**：不改 eligibility / capability 匹配（漂移是**可见性**，不是自动熔断）、
  不新增持久化字段（本轮读面 = probe 结果 DTO；把 returned name 落到行里是**另一个**决策，
  需先想清楚它与 `ModelRuntimeFingerprint` 的关系，列为残余）、不新增依赖、不改 Policy。
- **live 分支**：无凭据 ⇒ 不发起任何真实调用；在记录里写明 skip 的事实与判据（离线全绿 +
  真实 probe 未跑），**不得**把 skip 记成 PASS。

## 验收条件

- **AC-01 域分类器**：`assess_model_drift(declared, returned)` 三态可判，边界可判：
  `None` / 空串 / 全空白 ⇒ `UNKNOWN`；相同（含首尾空白差异）⇒ `MATCH`；
  仅大小写或任何其他差异 ⇒ `DRIFT` 且 detail 同时点名两个原值。
- **AC-02 API 读面**：`ProbeResultDto` 携带 `drift`（state + declared + returned + detail）；
  成功且同名 ⇒ `MATCH`；成功但异名 ⇒ `DRIFT`；失败 ⇒ `UNKNOWN`（且 `ok=false`）。
- **AC-03 页面三态**：`ProbeSummary` 渲染三态且互不混淆（`data-testid="probe-drift"`）；
  `UNKNOWN` 文案显式声明「未知 ≠ 无漂移」；`DRIFT` 文案点名两个值。
- **AC-04 反证**：
  - 把分类器的 `UNKNOWN` 分支改成 `MATCH` ⇒ 域判据红；
  - 把页面 `UNKNOWN` 分支渲染成 `MATCH` 文案 ⇒ e2e 判据红；
  - 从 DTO 摘掉 `drift` ⇒ API 判据红。
- **AC-05 诚实边界**：`docs/integration/MODEL_PROBE.md` 与 `LLM_ENDPOINTS.md` §8 写明三态、
  比较规则（精确比较，不折叠大小写）、以及「未知 ≠ 无漂移」；live probe 无凭据 ⇒ 记录 skip。
- **AC-06 门禁**：定向套件 + web `lint`/`typecheck`/e2e + OpenAPI 快照重生成 +
  规模门 + **m0 全量 23 项** + 治理 `validate.py`。

## 实施清单

### WP-A — 域分类器

- `packages/domain/enums.py`：`ModelDriftState`（三态，StrEnum）。
- `packages/domain/model_drift.py`：`ModelDriftAssessment` + `assess_model_drift`。
- 用例：`tests/domain/test_model_drift.py`（三态 + 边界 + 「大小写差异 = DRIFT」的决定）。
- 提交：`feat(domain): classify model drift in three states (match / drift / unknown)`

### WP-B — probe 结果读面（API）

- `services/api/dto/models.py`：`ModelDriftDto` + `ProbeResultDto.drift`。
- `services/api/routers/models.py`：`_probe_result_dto` 计算并带上 drift。
- `docs/api/openapi.m13.json` 重生成；`schemas/probe-result.schema.json`（若快照/契约判据要求）。
- 用例：`tests/api/test_models_api.py` 三条（同名 / 异名 / 失败）。
- 夹具：`FakeModelGatewayOptions.returned_model_name`（默认值不变）。
- 提交：`feat(api): expose the model drift verdict on the probe read face`

### WP-C — 页面三态

- `apps/web/src/api/types.ts` + `ModelDetails.tsx::ProbeSummary` 三态渲染 + 诚实文案。
- 自带 stub e2e（`apps/web/tests/e2e/models-drift-visibility.spec.ts`）：三态各一条。
- 提交：`feat(web): render the three drift states, with unknown never shown as no-drift`

### WP-D — 文档与 live skip 登记

- `docs/integration/MODEL_PROBE.md` / `LLM_ENDPOINTS.md` §8：三态 + 比较规则 + 「未知 ≠ 无漂移」。
- live skip 事实记入 RECHECK（无凭据 ⇒ 真实 probe 未跑）。
- 提交：`docs(integration): document the three drift states and the exact-match rule`

### WP-E — 反证、记录与收口

- 逐条反证（先红后复原）+ RECHECK + 子 PLAN 收口 + GOAL 回写（EC-05）。
- 提交：`docs(goals): close GOAL-008 cycle 4 -- EC-05 ...`

## 证据

逐条 AC 与 F1–F3 的注入/观察/复原对照见
`.cursor/plans/rechecks/RECHECK-20260920-117-model-drift-visibility-three-states.md`。摘要：

- **AC-01**：`tests/domain/test_model_drift.py` **9 passed**；反证 F1（`UNKNOWN` 改判 `MATCH`）**3 red**。
- **AC-02**：`tests/api/test_models_api.py` **15 passed**（含新增 3 条漂移判据）+
  `tests/architecture/python/test_protocol_vocabulary.py` **5 passed**（词表同源）+
  `test_openapi_snapshot.py`（快照 +47 行）；反证 F2（摘掉 `drift`）**3 red**。
- **AC-03**：`apps/web/tests/e2e/models-drift-visibility.spec.ts` **4 passed**；
  web `lint`/`typecheck`/unit 绿；反证 F3（UNKNOWN 用 MATCH 文案）**1 red**。
- **AC-04/AC-05**：三处注入均逐字节还原（`git diff --quiet` 复核）；
  文档两处 + 页面中英文案同源；live 无凭据 ⇒ **如实 skip**（RECHECK 有专节，
  **skip 不是 PASS**，真实 probe 未跑）。
- **AC-06**：`design-fidelity` 2 passed 且基线零 diff（漂移块只在探测后渲染 ⇒ 对设计门不可见）；
  `docs_consistency_check` / `validate_bundle` 绿；**m0 全量 23 项**计数见 GOAL 迭代日志 cycle 4 行。

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 4 = EC-05）：`status: IN_PROGRESS`。
  只读勘察确认 8 条事实（数据已有比较没有 → 指纹只在有 fingerprint 时构建 →
  失败路径天然 UNKNOWN → Fakes 的 returned name 硬编码 → 域模块体量与拆分决定 →
  OpenAPI 快照 drift 门 → 契约 schema 族 → live 无凭据只能 skip）。

## 影响报告

- **Domain/API/schema 变化**：新增域枚举 `ModelDriftState` 与纯函数 `assess_model_drift`；
  `ProbeResultDto` 增 `drift` 块（**新增字段**，不改既有字段语义）⇒ OpenAPI 快照重生成；
  `FakeModelGatewayOptions` 增一项（默认值不变 ⇒ 既有用例行为不变）。
- **安全/凭据变化**：无。drift detail 只含两个模型标识（都是配置面/响应里的非敏感值），
  **不含**凭据、不含 provider 原始响应体。
- **兼容性/迁移风险**：读面**新增**字段，旧客户端忽略即可；不新增持久化列/键，
  不触碰配置面 JSON blob 的既有键。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：EC-05 收口后取 **EC-04（首次真实 run）**——本机仍**无凭据**，
  按判定细则「skip 不是 PASS」处置；EC-06（文档与 runbook）随后。

- 2026-09-20 实施与复检（WP-A…WP-E）：`status: DONE`，`latest_recheck` 指向
  RECHECK-20260920-117（**PASS_WITH_WARNINGS**，W-1…W-6）。三态在域/API/页面三面落地，
  「未知 ≠ 无漂移」由域层与页面**两处独立**钉住；F1–F3 全部先红后复原。
  live 分支因**本机无凭据**如实 skip（真实 probe 一次未跑，skip 不记 PASS）；
  残余 6 条中 W-1 是能力边界，W-2/W-3（fingerprint 未纳入判定、drift 未持久化）是已知缺口。
