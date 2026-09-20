---
id: RECHECK-20260920-114
plan_id: PLAN-20260920-114
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle1
baseline_ref: 167bdd3
checked_head: 0a04520
---

# RECHECK-20260920-114 — ANTHROPIC 协议执行路径（EC-01 独立复检）

## 检查范围

不采信实施叙述：按 EC-01 的判据逐条在**当前树**上真跑，并对三条关键判据做**先红后复原**的
反证；门禁以**完整 m0（23 项）**为准而不是"定向套件绿"。检查面：

- 正向：`protocol=ANTHROPIC` 的端点经**真实** `OpenAIChatGateway` + `httpx.MockTransport`
  收到的请求形态（路径 / 鉴权头 / body）与响应解析结果；
- 回归：`protocol=OPENAI_COMPATIBLE` 的线上形态**逐字节未变**（含**不含** `max_tokens` 键）；
- fail-closed：未知协议 / 缺 `max_tokens` / 流式 / `response_format` ⇒ 点名拒绝且**出站 0**；
- 词表同源：域枚举 / 契约 JSON schema / API DTO 三处声明一致，且执行侧无协议字面量；
- 跨层：OpenHands `llm_factory` 前缀按协议选择；probe 层只对 Messages 形态显式给 `max_tokens`。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 词表同源 | `tests/architecture/python/test_protocol_vocabulary.py`（3 条）：schema enum == DTO Literal == `LLMProtocol`；执行侧（`adapters/relay`、`adapters/openhands`）AST 取字符串常量，**零**协议字面量 | PASS |
| AC-02 按协议选路（正向） | `tests/adapters/relay/test_anthropic_messages.py`：路径 `/api/v1/messages`、`x-api-key` 存在且 **`authorization` 不存在**、`anthropic-version` 存在、body 含 `max_tokens`；`content[]` 文本合并；`tool_use` ⇒ ToolCallDraft；usage 映射 `input/output/total`；`system_fingerprint is None` | PASS |
| AC-03 回归对照 | 同文件 `TestOpenAiShapeRegression`：仍 `POST /chat/completions` + `Authorization: Bearer`、`x-api-key` 不存在、**`max_tokens` 键不存在**；`api_style=responses` 仍走 `/responses`（既有用例） | PASS |
| AC-04 fail-closed | 同文件 `TestFailClosed` 4 条，均用**记录型 transport** 证明 `seen == []`（出站 0）：未知协议（绕过域校验构造）、缺 `max_tokens`、`stream=True`、`response_format` 非空 | PASS |
| AC-05 前缀按协议 | `tests/adapters/openhands/test_llm_relay.py::TestProtocolPrefix`（5 条）：`ANTHROPIC` ⇒ `anthropic/`；`OPENAI_COMPATIBLE` ⇒ `openai/`（原断言未动）；带 `/` 名透传；未知协议 `ValueError`；`build_llm` 从 endpoint 取协议 | PASS |
| AC-06 文档同源 | `docs/integration/LLM_ENDPOINTS.md` §1 协议表 + 缺口登记；`MODEL_GATEWAY.md` §3 指向该表；`gateway.py` 模块/类 docstring 不再自称 OpenAI-only | PASS |
| 跨层 | `tests/application/test_probe_protocol_requests.py`（3 条）：记录每个 `CompletionRequest` 证明 **ANTHROPIC ⇒ `PROBE_ANTHROPIC_MAX_TOKENS`**、**OPENAI_COMPATIBLE ⇒ `None`** | PASS |

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | `resolve_runtime_model_name` 的 ANTHROPIC 分支短路 | **2 failed**（`test_anthropic_endpoint_gets_anthropic_prefix`、`test_build_llm_takes_the_prefix_from_the_endpoint`） | 绿 |
| F2 | `complete_any` 的 Messages 分派短路 | 与 F1 合并执行为 **9 failed**；失败日志显示请求实际落到 `/chat/completions`（分派即路由本身） | 绿 |
| F3 | 未知协议改为**静默回退** OpenAI 形态 | **2 failed**（`DID NOT RAISE RelayHTTPError` ×2，含「出站为 0」那条） | 绿 |

复原后：`tests/adapters/relay + tests/adapters/openhands + tests/architecture/python/test_protocol_vocabulary.py`
**168 passed**（同一命令）。

### 复检**实测出的门禁失败**（m0 暴露，均按缺陷修，未动断言/门禁）

| # | 门禁 | 触发 | 处置 |
| --- | --- | --- | --- |
| G1 | `python/format-check` | 3 个新测试文件未格式化 | `ruff format`；断言未动 |
| G2 | `python/typecheck` | `anthropic_api.messages_result` 用布尔量收窄 token 求和（mypy 不跟随）；新测试助手返回标注写成 `object` | 改成显式 `is not None` 收窄；助手返回标注改为 `OpenAIChatGateway` |
| G3 | `tests/tooling/test_python_source_size_limits.py` | `request_with_retries` 因新增 headers 分支涨到 **57 行 > 50** | 抽出 `_execute_request` / `_default_headers`（控制流不变：重试循环与 `with attempt:` 原样），**不放松门禁** |
| G4 | `framework/validate_bundle` | 本轮本地工具 `scratch/ci_poll.py` 的 TEST-NET-1 网段字面量命中**旧版本号正则** | 改为「显式网段 + 地址分类兜底」，反**更严**（TEST-NET-1 地址现在判红），并保留代理 fake-IP 段豁免 |

G3 / G4 说明这两道门在本轮**确实拦住了东西**（不是走过场）。

## Warnings（不阻断，如实登记）

- **W-1 真实端点面未实测**：本机 **无凭据**（`.env` 中 `DEV_LLM_API_KEY` 存在但为空串，
  进程环境无该端点变量）⇒ 不对真实端点发起任何调用；「该端点是否真在 `{base_url}/messages`
  提供 Messages 面」**未验证**，属 EC-03/EC-04 的 live 分支待答。本轮证明的是**执行路径存在且
  离线可判**，不是"真实端点已验证"。
- **W-2 流式未实现**：`stream=True` 点名拒绝（不降级、不套 OpenAI SSE 解析）。后果如实：
  probe 的 `streaming` 步对 Messages 端点记为 capability failure，**不写 SUPPORTED 断言**。
- **W-3 `response_format` 无对应参数**：非空即拒绝 ⇒ 该形态下 `structured_output` 能力
  同样只能记为 failure（Anthropic 的等价做法是工具调用，本轮未做）。
- **W-4 `max_tokens` 成为 Messages 形态的必填**：probe 侧由 `PROBE_ANTHROPIC_MAX_TOKENS`（256）
  显式提供；**产品流量目前没有调用方传它**（relay 的 complete 路径今天只被 probe / 测试使用）。
  agent 真实运行走的是 OpenHands SDK（litellm）而不是本 relay 路径 ⇒ 该缺口不影响 EC-04。
- **W-5 `system_fingerprint` 恒为 `None`**：Messages 无等价字段 ⇒ 该端点的
  `SYSTEM_FINGERPRINT` 能力（AGENTS.md §4 的七件事之一）将**永远观测不到**；这是诚实边界，
  但也是漂移可见性的覆盖缺口（EC-05 只能依赖 `returned model name` 对比）。
- **W-6 示例端点仍未入库**：`examples/config/llm_endpoints.yaml` 的 `agnes-anthropic` 只是示例；
  真实登记（DB 行 + 凭据纪律 + URL 策略）属 EC-03，本轮**未做**，因此"声明与事实一致"只到
  执行路径这一层。
- **W-7 历史记录未改写**：`docs/references/upstream/M5_CORRECTIONS_LOG.md:62` 仍写「MVP 唯一协议
  OPENAI_COMPATIBLE」——它是**上游历史更正日志**，按仓库惯例不追改；此处点名以免被读成现行口径。
- **W-8 域值名仍含厂商词**：`LLMProtocol.ANTHROPIC` / `OPENAI_COMPATIBLE` 是**本轮之前**就已被
  域接受的取值（`LLMEndpoint.__post_init__` 原本就允许），本轮只是让它们真正生效；协议名指线协议族
  而非模型厂商绑定。EC-02 的「厂商中立」约束针对**新增的模型参数字段**，不追溯这两个既有取值。
- **W-9 工具调用映射的边界**：`tool_use.input` 非 dict 时 `json.dumps` 仍可序列化，但**无用例**
  覆盖该形态（现有用例只覆盖 dict input）。

## 门禁

- `python/format-check` / `python/product-lint` / `python/typecheck`（945 files）：PASS。
- `tests/tooling/test_python_source_size_limits.py`：PASS（G3 修复后）。
- 定向：`tests/adapters/relay` + `tests/adapters/openhands` + 词表判据 **168 passed**；
  `tests/application/test_probe_protocol_requests.py` **3 passed**。
- **本地 m0（profile=m0）**：**PASS: profile=m0; 23 deterministic checks**，测试计数器
  **4072 passed / 11 skipped**（冻结树 `0a04520` 上的最终一次运行；此前两次运行分别暴露 G1–G2、
  G3–G4 并据此修复）。
- 治理 `validate.py`：绿（记录提交前）。

## 结论

**PASS_WITH_WARNINGS**。EC-01 的可判部分全部成立且有反证：

1. `protocol` 不再是"只被持久化/DTO 读取的字符串"——relay 网关与 OpenHands `llm_factory`
   都**按协议选路**，且两侧各自有一条**回归对照**证明 `OPENAI_COMPATIBLE` 的行为未变；
2. **未知协议 fail-closed**（含"出站 0"的可观测证明）——静默回退这条"让配置与事实脱钩"的
   路径被用例钉死；
3. Messages 形态的三处**不伪造**（缺 `max_tokens` 拒绝、流式拒绝、`system_fingerprint`/usage
   不编造）都有独立判据；
4. m0 在本轮**真的拦下了四处缺陷**（含 50 行函数门与词表/版本扫描），修复均未触碰断言与门禁。

**未完成即未声称完成**：W-1（真实端点面）、W-2/W-3（流式与结构化输出缺口）、W-6（端点未入库）
是 EC-01 之外或需 live 凭据才能回答的面，已如实登记，并在 GOAL-008 的 EC-01 evidence 里逐条点名；
**EC-04 / EC-05 的 live 分支在本机只能走「如实 skip」**（无凭据），这一事实不因本复检 PASS 而改变。
