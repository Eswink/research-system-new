---
id: PLAN-20261120-116
slug: relay-switch-and-free-model-discipline
title: GOAL-115 cycle 1 —— 换站落地（opencode /inference/go）+ 免费模型纪律 + 会话头缝
status: IN_PROGRESS
created_at: 2026-11-20
updated_at: 2026-11-20
parent_goal: GOAL-20261119-115
owners:
  - root-agent
subagent_parallel_limit: 2
latest_recheck: null
memory_entries: []
---

# PLAN-20261120-116

## 背景

GOAL-115 的 EC-01（换站 + 免费模型纪律）与 EC-02（旧站 pin 全清零）是**同一件事的两面**：
不换站就没有「新站零价集合」可判；不清零就有两个站点同时"合法"。本 cycle 只做这两条，
因为它们**必须先于**任何真实 run（EC-04）与任何 advisory 读面（EC-05）。

**建档实测（2026-11-20 本窗口，全部实跑）**：

| 事实 | 证据 |
| --- | --- |
| `GET https://opencode.ai/inference/go/v1/models` ⇒ 32 模型，**零价恰 4 个** | `scratch/goal115/models_newkey.json`；脚本按 `cost.text.*.price` 全 0 判定 |
| 零价集合逐字 = 目标声明的四个 | `beam-free` / `iceman-contributor-free` / `longcat-2.5-free` / `hy4-flash-free` |
| 四个**都返回标准 `tool_calls`**（`tool_choice: required`） | 逐模型实测；`hy4-flash-free` 需 `max_tokens ≥ 2048`（reasoning 吃预算） |
| `stream: true` ⇒ SSE（四个都可，`longcat` 偶发 IncompleteRead，重试即过） | 逐模型实测 |
| **structured output 三有一无**：`iceman-contributor-free` 返回 `Structured response_format is not enabled` | 逐模型实测 ⇒ 它**不得**声明 `STRUCTURED_OUTPUT_NATIVE` |
| ★ **新站要求 `x-opencode-session` 头**：缺它 ⇒ `400 MissingSessionID`（**鉴权通过**时也拒） | 实测：有 key 无头 ⇒ 400；有 key 有头 ⇒ 200 |
| `GET /models` **不需要**该头（200） | 实测 |
| litellm 支持 `extra_headers` ⇒ 该缝在 OpenHands 腿上也成立 | 实测：无头 400 / `extra_headers` 带 ⇒ 200 |
| 旧站 `192.168.101.9:8798` **仍在线**（200） | 实测；换站是纪律选择，不是旧站故障 |
| `.env` 里原 `LLM_MAIN_KEY` 是**旧站**的 key（36 字符 `7f2f40…`） | 新站 key = `oc_sk_…`（51 字符），已落 `.env`（gitignored） |

**这一条是原 PLAN-115 没预见到的**：EC-01 的 `verify` 只要求「配置换过去 + probe 绿」，
但**光换配置必然 400** —— 产品两条腿（relay gateway、OpenHands/litellm）都不发该头。
所以本 cycle 的射程里**必须**包含一个新缝：endpoint 级可选 `extra_headers`。

## 交付面（checkbox）

- [ ] WP-1 `LLMEndpoint` 新增 `extra_headers`（域 + schema + loader + sqlite 往返 + DTO 只读投影）
- [ ] WP-2 两条腿真的发出该头：relay gateway / completions（全部 wire shape）+ OpenHands `build_llm`
- [ ] WP-3 `llm_endpoints.yaml` 换到新站（两个 `base_url` + `allow_models` 四个免费模型 + `extra_headers`）
- [ ] WP-4 `models.yaml` 九个 `model_name` 全部指向四个免费模型（按实测能力声明）
- [ ] WP-5 钉值判据同轮改：`test_goal108_probe_readings.py` / `goal108_closeout_assertions.py`（FREE_MODELS 从新站读数取）、`test_direction_to_report_v2_novelty.py` 注释、`_EXPECTED_TARGETS`
- [ ] WP-6 新判据 `tests/loaders/test_free_model_only_policy.py`（EC-01）
- [ ] WP-7 新判据 `tests/tooling/test_relay_pins_are_cleared.py`（EC-02，白名单进源码）
- [ ] WP-8 文档同步：`docs/integration/LLM_ENDPOINTS.md` / `LIVE_MODEL_RUNBOOK.md`

## 四模型分配（按实测 + 既有独立性约束求解）

约束（全部是**既有判据**，不是本 cycle 新加）：
① 写作组 ∩ 评审组 = ∅（`validate_bundle.py:609` + `test_the_factory_reviewer_and_producer_sit_on_different_underlying_models`）；
② `reviewer_a` ≠ `reviewer_b`（同上 ③ 逐对互不相同）；
③ 创新点作者 ∉ {写作组, 三位评审者}（`test_the_author_agent_is_bound_to_a_fifth_distinct_model`）；
④ 创新点评审 ∉ 写作组（`test_the_novelty_reviewer_is_not_on_the_writing_side`）。

**实测 18 组解**（`4` 个非写作模型里挑三个角色 + 作者）。取其中**按实测能力最保守**的：

| 角色 | 模型 | 依据 |
| --- | --- | --- |
| 写作组（`research_alpha` / `coding_beta` / `agnes_flash` / `scientific_editor_model`） | `hy4-flash-free` | `tool_calls` 需 2048 预算；写作相不吃工具；1M context |
| `reviewer_gamma`（`scout_b` 轻量面，非评审） | `longcat-2.5-free` | 1M context；`temperature` 不支持 ⇒ 不声明 |
| 评审 A（`reviewer_independent` = `critic_independent` primary） | `beam-free` | 1M+ context、`structured_output: true`、`tool_calls` |
| 评审 B（`kimi_k2_6`） | `longcat-2.5-free` | 1M context、`tool_calls`；**与 A 不同** |
| 创新点评审（`novelty_review_model`） | `beam-free` | 与评审 A 同（既有放宽面，逐字登记） |
| 创新点作者（`novelty_author_model`） | `iceman-contributor-free` | 唯一剩下的非写作模型；**非 ZDR** |

> `iceman-contributor-free` **不**声明 `STRUCTURED_OUTPUT_NATIVE`（实测被拒）与
> `TOOL_CALLING_NATIVE` 之外的能力；它的角色（`novelty_author`）硬要求只有 `CHAT` +
> `TOOL_CALLING_NATIVE`，两者都实测通过。

## 实施清单

### WP-1 域与持久化：`LLMEndpoint.extra_headers`

- `packages/domain/models.py`：`extra_headers: tuple[tuple[str,str], ...] = ()`（**tuple 不是
  dict**：域对象 frozen+slots，dict 不可哈希且 canonical digest 需要确定性序）。
  校验：名字非空、ASCII 小写或规范大小写均可但不得含 `:`/换行（防头注入）、
  **不得是 `authorization` / `x-api-key` / `anthropic-version`**（凭据只走 `credential_ref`）。
- `schemas/llm-endpoint.schema.json`：`extra_headers: {type: array, items: {type:object,
  required:[name,value], additionalProperties:false}}`。
- `adapters/contracts/models_loaders.py`：读 `[{"name":..,"value":..}]`。
- `adapters/sqlite/endpoint_store.py`：`_encode` / `_decode` 往返。
- `services/api/dto/endpoints.py` + `mappers/endpoints.py`：**本 cycle 不改读面**。
  理由（射程取舍，登记在此）：把 `extra_headers` 投影进 `LlmEndpointReadDto` 会连带
  OpenAPI 快照 + `web/src/types.ts` + e2e 夹具三处同步，而 EC-01 判的是**配置与出网**，
  不是读面可见性。读面缺口登记为残余 `W-3`（见 GOAL 残余节）。
- `services/api/mappers/endpoints.py:endpoint_config_digest` 消费方：**不改**语义，
  `extra_headers` 不进 M12 digest（那是冻结的；见 `fingerprint.py` 文档）。

### WP-2 两条腿发出该头

- `adapters/relay/protocols.py:request_headers(protocol, credential, extra_headers=())`：
  在既有头之上**追加**（冲突时点名拒绝，不静默覆盖）。
- `adapters/relay/transport.py:_default_headers` 路径（`_complete_chat` /
  `_complete_stream` / `_complete_responses` / `_complete_stream_responses`）必须
  也带上 —— **这是本轮最容易漏的一格**：chat 腿当前**不传** `headers=`，走的是默认头。
- `adapters/openhands/llm_factory.py:build_llm`：`extra_headers=dict(endpoint.extra_headers)`。
- 反证臂：把 `extra_headers` 摘掉 ⇒ 判据判红（用假 client 断言实际发出的头）。

### WP-3/WP-4 配置

- `examples/config/llm_endpoints.yaml`：`main.base_url` → `https://opencode.ai/inference/go/openai/v1`；
  `agnes-anthropic.base_url` → `https://opencode.ai/inference/go/anthropic/v1`；
  `allow_models` → 四个免费模型；两个端点各加 `extra_headers: [{name: x-opencode-session,
  value: research-os}]`（**值不是 secret**：它是会话路由标识，固定串即可）。
- `examples/config/models.yaml`：九个 `model_name` 按上表；`context_window_tokens` 按
  `/go/v1/models` 的 `limit.context`；能力声明**按实测**（`iceman` 不声明 structured）。

### WP-5 钉值判据同轮改

- `tests/tooling/test_goal108_probe_readings.py:36` 的 `FREE_MODELS` 与 `STATION_FACTS`
  → 新站读数（**它是 GOAL-108 台账的判据，判的是那本台账写对了没有**；台账本身是历史，
  **不改台账**，改的是它读的那两串常量 —— 否则它会去旧站名里找四个新模型名）。
- `tools/goal108_closeout_assertions.py:29/33` 同上（`FREE_MODELS` / `LAN_HOST`）——
  **注意**：它判的是「换站落地」这一事实，换站后旧值必红；本轮把它改成新站事实，
  并在文件头逐字登记「为什么改」（GOAL-108 的收口资产随站点演进而更新，不是放宽）。
- `tests/e2e/test_two_models_judge_the_same_artifact_live.py:59` 的 `_EXPECTED_TARGETS`
  → `{"main/beam-free", "main/longcat-2.5-free"}`。
- `tests/contracts/test_direction_to_report_v2_novelty.py` 的文档串（注释里点名旧免费模型）
  → 新四个。

### WP-6 `tests/loaders/test_free_model_only_policy.py`（EC-01）

判三件（两向）：
① `models.yaml` 的每个 `model_name` ∈ 零价集合（集合从 `GET /go/v1/models` 的
`cost.text.*.price` 全 0 推出）；**反证臂**：塞一个收费名（如 `deepseek-v4-pro`）⇒ 判红并点名。
② 端点 `base_url` 是 `/inference/go/{openai,anthropic}/v1`（不是旧站、不是 `inference` 根树）。
③ 判据自带**离线夹具**（`tests/fixtures/free_models_catalog.json`，从实测响应裁剪），
**不联网**；同时有一个 `@pytest.mark.requires_live_llm` 的真查用例（默认 skip，显式开关跑）。

### WP-7 `tests/tooling/test_relay_pins_are_cleared.py`（EC-02）

- 受判面 = 产品面（`packages/` `services/` `adapters/` `examples/` `schemas/`）+ 判据面
  （`tests/` `tools/`）。
- 豁免白名单**进源码**：`.cursor/memory/entries/**`、`.cursor/plans/goals/evidence/**`、
  `.cursor/plans/rechecks/**`、`.cursor/plans/tasks/**`、`.cursor/plans/goals/GOAL-2026*.md`
  （历史记录类）+ `.cursor/plans/goals/MAINLINE.md` 与 `archive/**`（宪章与归档是历史）。
- 逐条点名（路径 + 行号 + 命中串）；**反证臂**：往 `examples/config/` 临时写一行旧地址 ⇒ 判红。

### WP-8 文档

`docs/integration/LLM_ENDPOINTS.md` 与 `LIVE_MODEL_RUNBOOK.md` 的站点表、模型分工表、
「private IP 需要开关」的整段（新站是公网域名 ⇒ 那段不再成立，改成「公网 ⇒ 默认放行；
会话头是新的必填项」）。

## 验证

```bash
# 1. 换了 key 之后四个模型各跑一次（真出网，手动）
uv run --frozen --no-sync python -B tools/m12_relay_smoke.py
# 2. 定向
uv run --frozen --no-sync python -B -m pytest tests/loaders tests/tooling tests/adapters/relay tests/adapters/openhands -q
uv run --frozen --no-sync python -B -m pytest tests/application tests/api -q
# 3. 全量门
uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
```

## 验收条件

- 新站四个免费模型各自 probe 绿（含 `tool_calls`）；
- `tests/loaders/test_free_model_only_policy.py` 绿 + 反证臂红；
- `tests/tooling/test_relay_pins_are_cleared.py` 绿 + 反证臂红；
- 全量 m0 `PASS [` 24 行、0 FAILED、`tree changed: False`；
- CI 八 job 至终态。

## 状态历史

- 2026-11-20：建档。本 cycle 从 PLAN-115 的 WP-A 切出，**并加一格原计划没有的
  `extra_headers` 缝**（新站 400 实证）；四模型分配按实测能力与既有独立性约束求解。

## 影响报告

- **Domain/API/schema**：`LLMEndpoint.extra_headers` 新增（只读投影进 `LlmEndpointReadDto`）；
  JSON schema 放开一个字段；sqlite 往返多一列内容（无 migration：仍存 JSON blob）。
  OpenAPI 快照与 `web/src/types.ts` 需同步（新字段出现在 endpoint 读面）。
- **安全/凭据**：`extra_headers` **禁止**承载凭据头（`authorization` / `x-api-key` /
  `anthropic-version` 在域构造期点名拒绝）；值不是 secret，但仍按"路由身份"处理。
  新 key 只落 gitignored `.env` 的 `LLM_MAIN_KEY`。
- **兼容性/迁移**：旧 endpoint JSON 无 `extra_headers` ⇒ 缺省空元组，逐字节兼容。
- **上游版本影响**：新站是外部服务，模型目录会漂移；EC-01 的判据读的是**配置里的名字
  是否落在当时实测的零价集合**，不是"名字永远存在"。
