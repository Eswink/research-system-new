# Real Endpoint Runbook — 登记、凭据、重启边界、切换与回退

本文是**操作手册**：把一个真实 LLM 端点接进 Research OS、跑一次、再退回默认 Fake。
它是 [LLM_ENDPOINTS.md](LLM_ENDPOINTS.md)（数据面约定）与
[../security/SECRET_MANAGEMENT.md](../security/SECRET_MANAGEMENT.md)（凭据原则）之间的
**落地步骤**，不重复它们的规则。

每一节里出现的路径、变量名与命令都与代码**同源**：判据
`tests/architecture/python/test_runbook_same_source.py` 会逐个核对（改错一个字符就红）。

**默认仍是 Fake**（AGENTS.md §11）：不配置真实 runtime 时，系统跑的是 Fake——
本文的每一步都是**显式开**，并且每一步都有对应的**回退**。

---

## 1. 登记一个端点与模型

两条路径，**先想清楚用哪条**：

### 1.1 YAML 路径（示例 / 演示 · 仓库内）

- `examples/config/llm_endpoints.yaml`：每个端点一段，关键键 `protocol`、`base_url`、
  `credential_ref`、`request_timeout_seconds`、`max_retries`、`concurrency_limit`、
  `enabled`、`discovery`、`circuit_breaker`；
- `examples/config/models.yaml`：每个模型一段，关键键 `endpoint`、`model_name`、
  `capabilities`（声明值）；
- `examples/config/model_profiles.yaml`：把模型绑成 profile（`primary` / `fallback` /
  `hard_capabilities`）。

YAML 是**仓库内容**：改它等于改示例目录，走正常评审。**凭据值不写在这里**——
这里只写 `credential_ref`（一个**变量名**，如 `LLM_MAIN_KEY`）。

仓库里已登记的真实端点：`agnes-anthropic`（`protocol: ANTHROPIC`，
`base_url: https://apihub.agnes-ai.com/v1`，`credential_ref: LLM_MAIN_KEY`）；
模型：`agnes_flash`（`model_name: agnes-2.5-flash`，声明 `context_window_tokens: 512000`、
`thinking_intensity: MAX`）。

### 1.2 DB 路径（配置面 · 运行期）

控制面写入的是 SQLite 配置面（默认路径 `data/research-os-control.db`，
由 `services/api/settings.py` 的 `_DEFAULT_DB_PATH` 决定）：

- 表 `llm_endpoints`（`endpoint_id` / `endpoint_json` / `created_at`）——实现见
  `adapters/sqlite/endpoint_store.py`；
- 表 `models`（`model_id` / `model_json` / `created_at`）——实现见
  `adapters/sqlite/model_store.py`。

> **这个文件是运行期产物**：gitignored，clean checkout 里**不存在**，首次启动时才创建。
> 想从零开始就删掉它（见 `docs/` 的 DB 约定），下次启动重建。

写表不用手写 SQL——用既有 API：

```bash
# 登记端点（凭据值在同一次请求里给，见 §2；不落盘）
curl -X POST http://127.0.0.1:8000/llm-endpoints -H 'content-type: application/json' -d @endpoint.json

# 登记模型
curl -X POST http://127.0.0.1:8000/models -H 'content-type: application/json' -d @model.json

# 探一次（能力 + 返回的模型标识 + 漂移判定）
curl -X POST http://127.0.0.1:8000/models/<model_id>/probe
```

端点还有 `POST /llm-endpoints/{endpoint_id}/test`（连通性）与
`POST /llm-endpoints/{endpoint_id}/discover-models`（按 discovery 允许清单拉模型）。

---

## 2. 凭据：注入与轮换

**规则**（AGENTS.md §9 / 用户授权 (3)）：凭据只从**环境变量**或 **Credential boundary** 读取；
**不得**写入仓库、数据库、CI、记录、日志或提示词；不得回显。

两套面，对应两条注入方式：

| 面 | 怎么注入 | credential_ref 的形态 | 谁解析 |
| --- | --- | --- | --- |
| YAML 声明的端点 | 操作者导出环境变量（变量名 = YAML 里的 `credential_ref`，如 `LLM_MAIN_KEY`） | 变量名本身 | `adapters/relay/credential_resolver.py` 的 `EnvCredentialResolver` |
| API 登记的端点 | `POST /llm-endpoints` 请求体里带 key（`services/api/routers/llm_endpoints.py`） | `endpoint:<endpoint_id>` | `adapters/relay/registry_credential_resolver.py` 的 `RegistryCredentialResolver` |

**轮换**：换掉来源即可，没有别的地方要改。

1. 环境变量面：更新变量 → **重启 API**（§3）→ 新值生效；
2. API 注册面：用同 id 再 `POST` 一次（或重建端点）覆盖注册表里的值。

**读面只说存在性**：`GET /llm-endpoints` 回 `credential: configured | missing`
（`services/api/mappers/endpoints.py`），任何响应/日志/错误消息都不回显密钥。
「明文凭据不进仓库/记录/日志」由 `tools/credential_audit.py` 四面扫描把守。

---

## 3. 重启后重输的边界

**注册表活在进程内**：`RegistryCredentialResolver` 的 `_registry` 是内存字典，
进程结束即消失。因此：

- **重启后必须重新注入**（重新导出环境变量或重新 `POST`）；
- 重启**不会**让凭据「自动恢复」——它本来就没落盘；
- 本仓**不伪装** Secret Manager：没有加密存储层，也没有「凭据已保存」这种读面
  （判据：`tests/architecture/python/test_credential_boundary_wording.py` 的禁止面）。

端点的**非凭据配置**（`base_url` / `protocol` / 超时 …）在 DB 里，重启后仍在；
只有**凭据**需要重输。这两件事在 API 读面上是分开的（`credential: missing` ≠ 端点不存在）。

---

## 4. Fake ↔ 真实：切换与回退

**两个开关管两件事**——别把它们当成一个（D-11 之后，凭据**不再是充分条件**）：

| 开关 | 管什么 | 取值 |
| --- | --- | --- |
| `RESEARCHOS_AGENT_RUNTIME` | **装配哪一个 runtime**（`services/api/settings.py`） | 见下表 |
| `RESEARCHOS_LIVE_E2E` | **这一次要不要真的进 live run** | 恰为 `1` 才开；其余任何取值一律算**关** |

**runtime 开关**（`services/api/settings.py`）：

| 取值 | 行为 |
| --- | --- |
| 未设置 / 空串 | **默认 Fake**（`FAKE_RUNTIME`）——demo 输出，不出网 |
| `openhands` | 真实 Agent runtime（`OPENHANDS_RUNTIME`，OpenHands SDK adapter） |
| 其他任何值 | **装配期 fail-closed 并点名该取值**（不会静默回退 Fake） |

**live run 的门**（`packages/application/model_relay/live_run_gate.py`）在真正开跑前判**三条**，
任一不满足即关门、**逐条点名**未满足的条件：

1. **显式开关** `RESEARCHOS_LIVE_E2E` 恰为 `1`；
2. runtime **显式**配成 live runtime；
3. 端点凭据**可解析**（只问 `CredentialResolver.has`，**不物化明文**）。

门关着时**不发起任何真实调用**，并产出一条 `NOT_VERIFIED` 记录（`live_run_record.py`）——
**skip 不是 PASS**。**开关开着但凭据缺**的口径是**如实 skip 并点名缺哪个凭据**（既不是通过，
也不当成失败）——两种缺法（开关没开 / 凭据不可解析）在同一句理由里都能读到。

```bash
# 一次 live run 的最小命令形态（开关 + runtime + 凭据三样齐备；值只经环境变量）
set -a; . ./.env; set +a
RESEARCHOS_LIVE_E2E=1 RESEARCHOS_AGENT_RUNTIME=openhands \
  pytest tests/e2e/test_ec04_live_first_run.py -q -rs

# 回退到默认：去掉这两个变量即可（其余不动）
<启动 API 的命令>
```

**开关为什么是「值恰为 `1`」**：它必须能**一眼判**——`true` / `yes` / `0` 一律算**关**，
不做真值解析（与 `RESEARCHOS_REQUIRE_DOCKER` / `RESEARCHOS_REQUIRE_GPU` 同形态）。

**开关不得被持久化**：它**不许**出现在示例配置目录或 `.env*` 文件里，判据
`tests/architecture/python/test_live_switch_is_single_source.py` 会读这两处；否则「默认离线」
会被一份配置文件悄悄掀掉。环境读取点**全仓一个**（`tests/e2e/live_switch_support.py` 的
`live_e2e_switch_enabled`），产品层（`packages/application`）**零**环境读取——
开关由调用方作为**必填参数**传入，漏传即报错，不存在「忘了传就默认开门」。

跑一次的方式与判据见 [LLM_ENDPOINTS.md](LLM_ENDPOINTS.md) §11；live 用例是
`tests/e2e/test_ec04_live_first_run.py`（带 `requires_live_llm`，默认门只走 skip 路径）。

**回退要检查的三件事**：

1. `RESEARCHOS_AGENT_RUNTIME` 与 `RESEARCHOS_LIVE_E2E` 都已去掉（`GET` 读面应回到 Fake runtime 的披露）；
2. 端点 `credential` 显示 `missing`（凭据不再可解析——这是**预期**，不是故障）；
3. 重启后 **usage 不再新增** `MODEL_TOKENS`（没有任何真实调用）。

---

## 5. 哪些面仍是 demo

默认组合根里仍是 Fake 的面（AGENTS.md §11 要求这些 Fake **保留**：它们是契约与离线 CI 的
基础设施，「删 Fake」不是接入真实端点的路径；方向是**可配置**）：

- `FakeAgentRuntime`（`adapters/fakes/agent_runtime.py`）——默认 runtime；
- `FakeModelGateway`（`adapters/fakes/model_gateway.py`）——模型调用的离线替身；
- `FakeToolProvider`（`adapters/fakes/tool_provider.py`）——工具面；
- `FakeWorkspaceBackend`（`adapters/fakes/workspace_backend.py`）——工作区；
- `FakeWorkflowEngine`（`adapters/fakes/workflow_engine.py`）——工作流引擎；
- `FakeBudgetLedger`（`adapters/fakes/budget_ledger.py`）——预算账；
- `FakeMemoryStore`（`adapters/fakes/memory_store.py`）——工程记忆；
- `FakeCredentialResolver`（`adapters/fakes/credential_resolver.py`）——测试侧凭据解析；
- `FakeArtifactStore`（`adapters/fakes/artifact_store.py`）——制品存储；
- `FakeEvidenceLedger`（`adapters/fakes/evidence_ledger.py`）——证据账；
- `FakeExecutionBackend`（`adapters/fakes/execution_backend.py`）——执行后端；
- `FakeWorkerRegistry`（`adapters/fakes/worker_registry.py`）——worker 注册表；
- `FakeModelStore`（`adapters/fakes/model_store.py`）——配置面模型的读侧替身。

**已经接通的真实件**（对照着看，别把两者搞混）：

- 真实 runtime：`adapters/openhands/runtime_adapter.py`（`RESEARCHOS_AGENT_RUNTIME=openhands` 时装配）；
- 真实 relay 客户端：`adapters/relay/gateway.py`（`OpenAIChatGateway`，含 ANTHROPIC 形态）；
- 配置面真身：`data/research-os-control.db` 的 `llm_endpoints` / `models` 两张表；
- 真实端点与模型：见 §1.1 的 `agnes-anthropic` / `agnes_flash`。

**仍未验证的面**（如实登记，别在 runbook 里假装已知）：真实端点上的**一次 run 到终态**
**已经发生过**（见 §6 的实测样本），但它的**终态是 FAILED**——那是**协议设计内的
acceptance gate 判拒**，**不是** SUCCEEDED，也**不是**端点/协议/装配缺陷（判定依据见 §6）。
截至 GOAL-008 收口时该 run 尚未发生，当时的如实 skip 记录见
`.cursor/plans/rechecks/RECHECK-20260920-118-first-live-gated-real-run.md` 的 W-1。

---

## 6. 首次 live 样本（实测记录）

本节的数字来自 **2026-09-20 GOAL-009 cycle 1** 的**唯一一次**真实调用序列
（`PLAN-20260920-121`；授权口径：**次数取最小必要**、不压测、不批量、不重复重跑）。
**本节不含凭据值或片段**——只出现键名 `LLM_MAIN_KEY`。

| 项 | 值 |
| --- | --- |
| 命令 | `RESEARCHOS_AGENT_RUNTIME=openhands` 内联前缀 + `tests/e2e/test_ec04_live_first_run.py` |
| 结果 | **1 passed, 1 skipped**（live 用例 PASSED；关门用例走 skip 分支＝门已开） |
| run id | `142f7e77-cd4d-4044-a953-79296509fd54` |
| 用时 | 28.69s（含 probe 段） |
| 端点 | `agnes-anthropic` 的 `base_url`，实际走 `main` 绑定（见下「面」一栏） |
| probe 段 | `verified and ok` |
| 返回 model 名 | `agnes-2.5-flash` |
| 声明 model 名 | `agnes-2.5-flash`（`examples/config/models.yaml` 的 `agnes_flash.model_name`） |
| 漂移判定 | **`MATCH`**（一致）——实测返回标识 == 声明值；由 `assess_model_drift` **重算**得出，判据见 `tests/architecture/python/test_live_drift_sample_same_source.py` |
| 终态 | `FAILED`（**设计内**：见下「判拒为什么不是缺陷」） |
| 口径 | `REPEATABLE_CONFIGURATION`（AGENTS.md §4；**不是**「完全模型可复现」） |
| usage 归账 | `MODEL_TOKENS` 1 条、合计 15219 tokens |
| 制品 | 1 条，id 以 `:session_message` 结尾 |
| 证据 | 1 条，`evidence:` 前缀 + 同一 `session_message` 后缀 |
| 如实缺口 | `system_fingerprint` 与 `safe_response_metadata` 缺失（记录里进 `missing_fields`，**不**留白冒充） |

**判拒为什么不是缺陷**：本示例协议的 task contract 要 `analysis_report`，而该次真实会话产出的是
`session_message`，于是 acceptance gate 按合约**判拒**——这正是登记链在正常工作。
**（2026-09-21 更新，GOAL-010 EC-01）**：这条**历史样本**描述的是**改动之前**的行为；
此后交付物的**键名由合约声明决定**（声明恰一个 artifact 名 ⇒ 用该名），本路径的**期望**
因此分成**两个分支**，同一文件里的
`_assert_deliverable_adjudicated`（声明对齐 ⇒ gate PASS ⇒ `SUCCEEDED`）与
`_assert_deliverable_rejected`（声明不唯一 ⇒ adapter **不猜** ⇒ gate REJECT ⇒ `FAILED`，
本样本所属的那一支）。两条都把「出现 `carries no structured output`」当成判红条件
（那才说明登记链被跳过）。**样本本身不改写**——它是**当时**的观测记录。

**证明力边界（别过度解读）**：`一致` 只代表**这一次**一致——它**不**证明该中转站永不漂移，
也**不**证明底层模型与声明完全同一。单次样本**不能**把三态里的「一致」升级成永久结论；
按 AGENTS.md §4，结论口径**只能**停在「可重复配置」。

**另一条边界（本节的样本与它无关，但必须一起读）**：漂移判定**不持久化**——
读面（模型探测结果里的 `drift` 字段）只在**执行过那次探测的那个进程**里存在；
重启后读面不会「记得」这次 `MATCH`。所以本节表格是**这次观测的记录**，
不是读面会自动复述的缓存。

**未捕获的一项（如实登记）**：本次运行的**逐条失败消息**产生于该次进程内的 in-memory
事件库，进程结束即消失，因此**没有**留成文本。上面的归类依据是三条**收敛**证据
（制品 id 后缀为 `:session_message`、usage 已真实归账、probe 段已 `verified and ok`）
加上同路径离线判据对 `FAILED` 的既有期望——**不是**直接读到的失败字符串。

### 6.1 第二次真实 run（GOAL-010 EC-01）：**契约被满足，终态 `SUCCEEDED`**

上表那次之后，交付物的**键名改由合约声明决定**（见 §6 的更新注与
`docs/integration/OPENHANDS_ADAPTER.md`），**验收门一字未改**。同一路径上的第二次真实 run：

| 项 | 值 |
| --- | --- |
| run id | `f1710564-855c-43f7-9fdd-84966a878cf9` |
| 终态 | **`SUCCEEDED`**（**不是** `FAILED`——这是与上表最关键的区别） |
| 失败消息 | **空**（`failures: []`；无 acceptance gate 判拒） |
| 制品 | 2 条，**都以合约声明的 `:analysis_report` 结尾** |
| 交付物载荷 | `declared_artifact = analysis_report`、`fact_name = session_message`、`contract_id = console_demo_deliverable` |
| 判据 | `tests/e2e/test_real_deliverable_contract_live.py`（**`1 passed`**；默认门下**如实 skip**） |
| 调用次数 | **2**（同形态、同判据、都 `SUCCEEDED`；第 2 次为**取回 run id 与记录**，如实登记） |

**判据**：终态**恰为 `SUCCEEDED`** + `failures` 为空 + 交付物按合约声明的名字登记。
**「门 PASS」是代码路径推出的蕴含关系**：`task_phase_helpers.register_and_gate` 在门未通过时
**必然**写 `failure_step("… rejected by acceptance gate")` ⇒ `FAILED`；逐条 criterion 的 reason
文本活在进程内、**未**取回（与上表「未捕获的一项」同一类限制）。

**证明力边界（别过度解读）**：两次 `SUCCEEDED` 说明**这两次**契约被满足；它**不**证明真实模型
**稳定**产出可用交付物——`ARTIFACT_EXISTS` 只判**存在**、**不判内容是否合格**，交付物内容仍是
自由文本。**证据链另说**：该 run 的 `EVIDENCE_COVERAGE` 仍由**模型自述**满足
（数的是交付物自己）——那是 GOAL-010 **EC-02** 的靶子，**尚未**解决。

## 7. 失败路径的诚实语义

三类情形各自的**期望**写死在这里。判据
`tests/architecture/python/test_live_failure_paths_same_source.py` 按**固定标签**读这张表，
并核对表里每一条「证据在哪」的说法**仍然成立**——改坏任意一格即判红。
表的**目的**是让「失败时该发生什么」不必靠记忆或猜。

| 情形 | 期望语义 | 证据在哪 |
| --- | --- | --- |
| 无效凭据 | 门**开**（`has()` 只问存在性，**不**问有效性）⇒ **发起**调用 ⇒ **明确失败**并落终态，点名鉴权；**不**静默成功、**不**无限重试 | `tests/e2e/test_live_failure_paths.py` 的 `test_live_invalid_credential_fails_loudly_without_leaking`（live，需显式预置条件：live 开关 `RESEARCHOS_LIVE_E2E=1` + 该样本自己的预置条件）；门的语义由 `tests/architecture/python/test_live_failure_paths_same_source.py` 钉住 |
| 端点拒绝 | URL 策略是**门链第一环且先于触网**：拒 localhost / 环回 / 私有 / 保留时 **零出站**，且**点名策略**；链**短路**（同 endpoint 上不再派生 health / credential 的拒绝） | `tests/api/test_runtime_egress_gate.py`（既有套件，**不重复实现**） |
| 模型不存在 | **明确失败**并落记录（**点名模型标识**），**不**回退到别的模型 | 实测样本：`tests/e2e/test_live_model_absence.py`（live，需显式预置条件：live 开关 `RESEARCHOS_LIVE_E2E=1` + 样本自己的预置条件）。**2026-09-21 实测**（`agnes-anthropic` + 一个不存在的标识）：连通性 `GET /models` **通过** ⇒ 那次 chat 被中转站以 **5xx** 拒（⇒ `MODEL_RELAY_UNAVAILABLE`）且**错误正文点名**了请求的标识，返回 model 名为 `null`——**没有**静默映射。装配侧：`adapters/openhands/llm_factory.py` 只接收**一个** `ModelDefinition`；run 的 LLM 装配路径**不消费** fallback（判据：`tests/architecture/python/test_live_failure_paths_same_source.py`） |

**五条必须一起读的边界**：

1. **「门开」≠「凭据有效」**。门答的是「**此刻能不能发起**」，不是「**会不会成功**」。
   把门改成校验有效性会是行为变更（本仓明文不做）；因此**无效值也开门**是**设计内**的语义，
   不是缺陷——它把「值错了」这件事**推迟到调用结果**里如实暴露。
   （D-11 之后门的条件从两条变三条：**显式开关** / runtime / 凭据。这一条讲的是**凭据那一格**，
   开关没开时门根本不开——那是另一格，见 §4。）
2. **重试是**有界**的**：`num_retries` 来自 `endpoint` 的 `max_retries`
   （示例配置 = `2`），不是 SDK 默认、也不是无上限——所以「不重试到超时」是**配置保证**，
   不是「恰好没重试」。
3. **本仓**有** fallback 概念**（`ModelProfile.fallback` / `plan_fallback`），
   但**会话中途不切换模型**：run 的 LLM 装配路径只消费被绑定的那**一个**模型。
   「不回退」指的是**这条路径**的行为，不是「仓库里没有 fallback」。
4. **「模型不存在」的失败类别不唯一**（**实测**）：中转站用它自己的 5xx 表达这次拒绝，
   于是这一类失败与「中转站故障」共用 `MODEL_RELAY_UNAVAILABLE`，而该类别**在可重试集合里**
   （`adapters/relay/transport.py`）。所以判定细则里的「**点名模型标识**」不是修饰语，
   而是这一格**唯一**能把它与「中转站挂了」区分开的读数面——按类别读会读错。

## 8. 凭据生命周期：注入 / 轮换 / 撤销 / 可弃用额度

§2 与 §3 讲的是**怎么配**与**重启边界**；本节把四件事的**语义**写死，判据
`tests/architecture/python/test_live_credential_lifecycle_same_source.py` 按**固定标签**读这张表。

| 事项 | 语义 | 依据 |
| --- | --- | --- |
| 注入 | 只经**环境变量**：`set -a; . ./.env; set +a`（POSIX 形态） | `adapters/relay/credential_resolver.py` 的 `EnvCredentialResolver` |
| 轮换 | 换来源 ⇒ **新构造**的解析器看到新值；**已构造的实例是快照** | `adapters/relay/credential_resolver.py`（实测见下） |
| 撤销 | 清空或删除来源 ⇒ **新构造**的解析器 `has()` 为 `False` ⇒ 门 **fail-closed** 关闭并**点名**该凭据 | `packages/application/model_relay/live_run_gate.py` |
| 可弃用额度 | 本 key 为**免费可弃用额度**（泄露风险由操作者明示接受）；这**不**降低凭据纪律 | 本仓凭据纪律（§2 首段） |

**撤销只关掉三条件里的一格**（D-11 之后门的条件是：显式开关 / runtime / 凭据）：
上表说的「门 fail-closed」是**凭据那一格**；开关与 runtime 两格不受轮换/撤销影响，
所以「清空凭据」**不会**让一个本来就不该跑的 live run 变成可跑——两件事互不顶替。

**注入（两种形态，选一种即可）**：

```bash
# A. 显式导出（最可移植；适用于任何 shell 与任何启动方式）
set -a; . ./.env; set +a          # set -a 让 source 进来的键自动导出

# B. 单条命令内联前缀（临时、最小面；不进任何文件，见 §4 的开关写法）
RESEARCHOS_AGENT_RUNTIME=openhands LLM_MAIN_KEY=… <启动 API 的命令>
```

**本机是 A 可省的**：pytest 进程里凭据已经可见（由导入栈的 dotenv 加载，判据是
`EnvCredentialResolver().has('LLM_MAIN_KEY')` 为 `True`），所以**跑 live 用例不必手工导出**；
但**显式导出是更可移植的形态**，CI 与别的机器上不要指望自动加载。

**轮换的边界（实测，别再按旧假设做）**：解析器**不是在每次调用时读环境**，所以
**「同一进程内改环境变量即生效」是错的**。精确语义按**构造方式**分三种（实测 2026-09-21）：

| 构造方式 | 来源之后变化时 | 说明 |
| --- | --- | --- |
| `EnvCredentialResolver()`（**生产路径**，无参） | **看不到**——构造时已拷贝环境 | 已构造的实例是**快照** |
| `EnvCredentialResolver(environment=…)` | **看得到**——传入的映射是**按引用**持有 | 测试/注入路径，别拿它推断生产 |
| `RegistryCredentialResolver(environment=…)` | **看不到**——构造时 `dict(...)` 拷贝 | 另有独立的内存注册表（见下） |

| 动作 | 已构造的**生产**实例 | 新构造的实例 |
| --- | --- | --- |
| 换掉来源（轮换） | 仍按**旧**结论回答 | 看到**新**值 |
| 清空/删除来源（撤销） | **仍报 `has()` 为 `True`** | `has()` 为 `False` |

⇒ **生效边界是「新构造 resolver 的时机」**（新进程、或每次新建实例的路径）。
API 面因此仍按 §3 处理：**重启后重输**。

**名字必须逐字一致**：端点的 `credential_ref` 要与环境变量名**逐字**相同。`os.environ` 在
Windows 上按**大小写不敏感**查找，但解析器把它拷贝成**普通字典**，那里是**大小写敏感**的 ⇒
大小写写错会静默变成「凭据不可解析」（门关，不报错）。

**撤销的两条边界**：
1. **环境变量面**：清空或删除 ⇒ **新构造**的解析器 `has()` 为 `False` ⇒
   `packages/application/model_relay/live_run_gate.py` 的门**自动关闭**（fail-closed），
   理由**点名**该凭据不可解析；
2. **注册表面**：若该 ref 已经 `register()` 进内存注册表，**注册表命中优先于环境变量** ⇒
   撤销环境变量**不**关这个面的门，必须 `unregister()`（机制见 §3）。

**可弃用额度（如实）**：本 key 是**免费可弃用额度**——它的泄露风险**由操作者明示接受**。
但这**只降低追责口径，不放松纪律**：值仍然**不得**写入任何 tracked 文件、数据库、记录
（PLAN / RECHECK / MEM / GOAL）、日志或命令回显；扫描面见 `tools/credential_audit.py`。


