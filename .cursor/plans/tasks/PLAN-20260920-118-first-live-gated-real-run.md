---
id: PLAN-20260920-118
slug: first-live-gated-real-run
title: 首次 live-gated 真实 run：门控、运行时指纹、usage 归账、制品与证据、结论口径「可重复配置」（EC-04）
status: IN_PROGRESS
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 5 = EC-04（首次真实 run）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（登记真实端点与模型 **anthropic 兼容型**、`base_url = https://apihub.agnes-ai.com`、模型 `agnes-2.5-flash`，并允许一次 live-gated 真实 run，最小必要次数，不跑压力/批量）、第 (3) 条（凭据只从环境变量或 Credential boundary 读取，由用户注入；不得写入仓库/数据库/CI/记录/日志/提示词，不得回显；本循环不得索取明文）与 AGENTS.md §4（无法证明底层模型完全一致时必须标注「可重复配置」而非「完全模型可复现」）。本 PLAN 遵守：默认 runtime 保持 Fake、默认门离线、真实 runtime 仅显式配置时启用、不新增依赖、不改 pin、不改 Policy/eligibility；**无凭据时 live 分支如实 skip，skip 不是 PASS**。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260920-118 — 首次 live-gated 真实 run（GOAL-008 cycle 5 = EC-04）

## 目标

把「一次真实 run」从**可期望**变成**可判、可 skip、且不会说谎**：

1. **门控可判且默认关**：live 分支只有在**凭据可解析**（环境变量或 Credential boundary）且
   runtime **显式配置**时才开门；门关闭时**不发起任何真实调用**，且这个「没出网」可判；
2. **skip 不是 PASS**：无凭据 ⇒ 产出**结构化**的 `NOT_VERIFIED` run 记录（点名缺哪一个
   `credential_ref`），用例如实 skip——**不得**留下任何看起来像「跑通了」的痕迹；
3. **结论口径是词表，不只是文案**：`REPEATABLE_CONFIGURATION` / `NOT_VERIFIED` 两态，
   **类型上无法表达「完全可复现」**；AGENTS.md §4 的「可重复配置」由此从口号变成可判事实；
4. **指纹诚实**：`ModelRuntimeFingerprint` 里取不到的字段必须进 `missing_fields` 并被点名
   （`NOT_VERIFIED` 或空值不得留白冒充「探了没问题」，沿用 GOAL-007 EC-01 的裁定）；
5. **live 分支如实 skip**：本机无凭据 ⇒ 真实 run **不发生**，记录 skip 事实；
   离线判据（词表 / run 记录 / 门 / 零出站 / 口径同源）仍须全绿。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **live 门控已存在，但只断言 usage**：`tests/e2e/test_ec03_real_runtime_offline_chain.py:398`
   的 `test_live_endpoint_is_exercised_only_when_credentials_are_configured`（`requires_live_llm`）
   只断言 `deps.budget.snapshot().entries` 非空 ⇒ **终态 / 运行时指纹 / 制品与证据读面**
   在 live 路径上**没有被判**。
2. **现有 live 用例吃的是操作者给的 URL，不是登记端点**：它取
   `RESEARCHOS_LIVE_E2E_ENDPOINT`（OpenAI 兼容形态）⇒ EC-03 登记进目录的
   **ANTHROPIC 端点**（`examples/config/llm_endpoints.yaml::agnes-anthropic`，
   `base_url=https://apihub.agnes-ai.com/v1`，`credential_ref=LLM_MAIN_KEY`）与
   `models.yaml::agnes_flash`（`agnes-2.5-flash`，声明 512000 / MAX）**尚未被 live 路径消费**。
3. **「可重复配置」只有文案、没有词表**：口径当前落在 `services/api/dto/models.py:92`
   的 docstring 与页面 `apps/web/src/features/models/ModelDetails.tsx:139-141`
   （`Configuration reproducible / provider fingerprint unavailable`）；
   `rg "REPEATABLE|Reproducib"` 全仓**只**命中 `packages/domain/reproducibility.py::ReproducibilityAudit`
   ——那是**实验**可复现审计，与**模型**可复现口径是两件事，不得混用（本轮不碰它）。
4. **probe 有 NOT VERIFIED 占位，run 没有**：`live_probe.py::not_verified_outcome` 给了
   **探测**的结构化 NOT VERIFIED；**一次 run** 的诚实 skip 没有对应结构 ⇒ 本轮补。
5. **指纹落点已存在**：`RunManifest.model_runtime_fingerprints` +
   `m12_composition::_relay_fingerprints()` 已把 `RelayProbeOutcome.to_manifest_payload()`
   冻进 manifest（`packages/application/m12_reference/clean_run.py:214`）⇒ 不需要新表、
   不需要新持久化，指纹沿用既有落点。
6. **runtime 显式配置面已存在**：`services/api/settings.py:144` 读
   `RESEARCHOS_AGENT_RUNTIME`（默认空串 = 未配置）；`tests/api/test_runtime_selection_surface.py`
   已判「非法取值装配期 fail-closed、绝不静默回退 Fake」⇒ 直接复用，不新增配置面。
7. **形态与 URL 拼装已有判据**：`adapters/relay/protocols.py`（ANTHROPIC ⇒
   `anthropic_messages`、`x-api-key` + `anthropic-version: 2023-06-01`）与 `gateway.py`
   的 `join_url(base_url, "/messages")`，由 `tests/adapters/relay/test_anthropic_messages.py`
   判 `/api/v1/messages` ⇒ live 路径不写新的形态代码。
8. **本机无凭据**（本轮实跑复核，只看存在性、未读值）：`LLM_MAIN_KEY` / `DEV_LLM_API_KEY` /
   `RESEARCHOS_LIVE_E2E_KEY` / `RESEARCHOS_LIVE_E2E_ENDPOINT` / `OPENAI_API_KEY` /
   `ANTHROPIC_API_KEY` **全 absent** ⇒ live 分支本轮只能走如实 skip。

## 口径（先写死，避免实施时漂移）

- **两态词表**：`REPEATABLE_CONFIGURATION`（端点+模型+配置已被真实探测/运行确认，
  但**底层模型是否完全一致不可证明**——§4 的准用结论）与 `NOT_VERIFIED`
  （**什么都没证明**：无凭据 / 门关闭 / 探测或运行失败）。**没有第三态，也没有
  「完全可复现」**：把两个枚举成员穷举在判据里，任何新增成员必须先过一轮判据。
- **skip ≠ PASS**：`NOT_VERIFIED` 记录**不得**出现在任何「通过」判定的位置；
  用例的 skip 事实与「离线判据全绿」必须分开写（skip 只说明 live 分支没跑）。
- **指纹诚实**：取不到的字段（`system_fingerprint` / 白名单响应头 / probe suite digest …）
  必须进 `missing_fields` 并被点名；**留白不等于干净**。
- **零出站**：门关闭（无凭据）时，harness 跑完**不得**发生任何 HTTP 调用——
  以「gateway 零调用」为判据，并以「门打开 + stub 端点 ⇒ 有调用」作正控。
- **口径判据判肯定式，不判话题**：禁止的是**肯定式宣称**「完全可复现 / fully reproducible」；
  既有的**诚实否定句**（AGENTS.md「而非『完全模型可复现』」、docstring「禁止美化为一律
  fully reproducible」、M12 记录「无法证明『完全模型可复现』」）必须豁免 ⇒
  判据形态 = 「出现该短语的**行**必须同时含否定标记（禁止/不得/而非/不是/无法/未/not/never），
  否则判红」。
- **不做的事**：不改 Policy / eligibility、不改 `RESEARCHOS_AGENT_RUNTIME` 的语义、
  不把真实 runtime 设为默认、不新增依赖或 pin 变更、不新增持久化表/列、
  不把凭据写进任何落盘面；**本循环不索取明文凭据**。

## 验收条件

- **AC-01 词表**：`ModelReproducibilityVerdict` 两态（`REPEATABLE_CONFIGURATION` /
  `NOT_VERIFIED`）可判；成员集合**恰好**是这两个（多一个或改字面量 ⇒ 判据红）。
- **AC-02 run 记录**：`LiveRunRecord` 携带 run_id / terminal_state / verdict / 指纹字段
  （endpoint_config_digest / returned_model_identifier / system_fingerprint /
  probe_suite_digest / safe_response_metadata）/ `missing_fields` / usage（model_tokens + 归账条数）/
  artifact 与 evidence ids / reason；`build_live_run_record` 与 `not_verified_live_run_record`
  两入口可判：无凭据 ⇒ `NOT_VERIFIED` + `missing_fields` 点名缺失指纹项。
- **AC-03 live 用例与门**：`tests/e2e/test_ec04_live_first_run.py`（`requires_live_llm`）
  消费**目录里登记的** `agnes-anthropic` 端点 + `agnes_flash` 模型 + `RESEARCHOS_AGENT_RUNTIME=openhands`
  跑一次到终态；有凭据时的判据 = usage 真归账（`MODEL_TOKENS` 正向）+ 制品/证据可读 +
  指纹摘要可判；无凭据 ⇒ `pytest.skip` 并记录 skip 事实。
- **AC-04 离线可判（默认门，无网络）**：门控决策函数可离线判（无凭据 ⇒ skip 决策，
  reason 点名 `credential_ref`）；**零出站**（门关闭时 gateway 零调用；正控：门打开 + stub ⇒ 有调用）；
  `NOT_VERIFIED` 记录不被任何判据当作 PASS。
- **AC-05 口径同源**：`tests/architecture/python/test_reproducibility_wording.py` 扫面
  （DTO docstring / 页面文案 / `docs/integration/LLM_ENDPOINTS.md` / 本 GOAL+PLAN 记录）：
  要求「可重复配置」类措辞存在，且**不存在**无否定标记的肯定式「完全可复现 / fully reproducible」。
- **AC-06 反证**（先红后复原）：
  - F1：把 `not_verified_live_run_record` 的 verdict 改成 `REPEATABLE_CONFIGURATION` ⇒ 判据红；
  - F2：让 `missing_fields` 不再点名缺失指纹项（留空）⇒ 判据红；
  - F3：门改成「无凭据也放行」⇒ 门判据 / 零出站判据红；
  - F4：把某条文档的否定句改成肯定句 ⇒ 口径判据红。
- **AC-07 门禁**：定向套件 + **m0 全量 23 项** + 治理 `validate.py` / `validate_bundle` /
  `docs_consistency_check`。

## 实施清单

### WP-A — 词表与 run 记录（域 + 应用）

- `packages/domain/enums.py`：`ModelReproducibilityVerdict`（两态 StrEnum，docstring 写明 §4 语义）。
- `packages/application/model_relay/live_run_record.py`：`LiveRunRecord` +
  `build_live_run_record` + `not_verified_live_run_record`。
- 用例：`tests/domain/test_reproducibility_verdict.py`（成员集合恰好两态）+
  `tests/application/model_relay/test_live_run_record.py`（诚实规则 + 两入口）。
- 提交：`feat(model-relay): add the reproducibility verdict and the live-run record`

### WP-B — live 门、live 用例与离线判据

- 门：应用层的 live 门决策（凭据可解析？runtime 是否显式配置？）——可离线判、无网络。
- `tests/e2e/test_ec04_live_first_run.py`（`requires_live_llm`）：登记端点 + `agnes_flash` +
  `RESEARCHOS_AGENT_RUNTIME=openhands`；无凭据 ⇒ skip 并记录。
- 离线判据：`tests/e2e/test_ec04_live_gate_offline.py`（门决策 + 零出站 + 正控 + skip ≠ PASS）。
- 提交：`feat(model-relay): gate the first live run and make the skip provable offline`

### WP-C — 口径同源判据与文档

- `tests/architecture/python/test_reproducibility_wording.py`（REQUIRED + 否定豁免的 FORBIDDEN）。
- `docs/integration/LLM_ENDPOINTS.md`：新增「首次真实 run（live-gated）：门控 / 结论口径 /
  如实 skip」一节。
- 提交：`docs(integration): document the live-run gate and the repeatable-configuration wording`

### WP-D — 反证、记录与收口

- 逐条反证（F1–F4，先红后复原）+ RECHECK-118 + 子 PLAN 收口 + GOAL 回写（EC-04）+ MEM 条目。
- 提交：`docs(goals): close GOAL-008 cycle 5 -- EC-04 ...`

## 证据

逐条 AC 与 F1–F4 的注入/观察/复原对照见
`.cursor/plans/rechecks/RECHECK-20260920-118-first-live-gated-real-run.md`。

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 5 = EC-04）：`status: IN_PROGRESS`。
  只读勘察确认 8 条事实（live 用例只断言 usage → live 端点是操作者 URL 而非登记端点 →
  「可重复配置」只有文案没有词表 → probe 有 NOT VERIFIED 占位而 run 没有 →
  指纹落点（manifest）已存在 → runtime 显式配置面已存在 → 形态/URL 拼装已有判据 →
  本机六项候选凭据环境变量全 absent ⇒ 只能 skip）。

## 影响报告

- **Domain/API/schema 变化**：新增域枚举 `ModelReproducibilityVerdict` 与
  `LiveRunRecord`（应用层，不落库、不进 DTO）⇒ **不改 OpenAPI、不改 DTO、不新增表/列**。
- **安全/凭据变化**：无新凭据面；live 门只做「可解析性」判断，不读值、不回显、不落盘；
  判据里不出现任何凭据值形态。
- **兼容性/迁移风险**：纯新增（枚举 + 记录类型 + 测试 + 文档），既有读面与门不受影响；
  默认门保持离线（live 用例带 `requires_live_llm`，CI 只走 skip 路径）。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：EC-04 收口后取 **EC-06（文档与 runbook：登记步骤 / 凭据注入与轮换 /
  重启重输边界 / Fake↔真实切换与回退 / 「哪些面仍是 demo」清单 + `docs/INDEX.md`）**。
