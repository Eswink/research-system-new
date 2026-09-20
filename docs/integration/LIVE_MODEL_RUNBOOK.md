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

**开关是环境变量 `RESEARCHOS_AGENT_RUNTIME`**（`services/api/settings.py`）：

| 取值 | 行为 |
| --- | --- |
| 未设置 / 空串 | **默认 Fake**（`FAKE_RUNTIME`）——demo 输出，不出网 |
| `openhands` | 真实 Agent runtime（`OPENHANDS_RUNTIME`，OpenHands SDK adapter） |
| 其他任何值 | **装配期 fail-closed 并点名该取值**（不会静默回退 Fake） |

```bash
# 切到真实 runtime（凭据同时注入；只经环境变量）
RESEARCHOS_AGENT_RUNTIME=openhands LLM_MAIN_KEY=… <启动 API 的命令>

# 回退到默认 Fake：去掉这一个变量即可（其余不动）
<启动 API 的命令>
```

**live run 的门**（`packages/application/model_relay/live_run_gate.py`）在真正开跑前再判一次：
runtime 必须**显式**配成 live runtime，且端点凭据**可解析**（只问
`CredentialResolver.has`，**不物化明文**）。门关着时**不发起任何真实调用**，
并产出一条 `NOT_VERIFIED` 记录（`live_run_record.py`）——**skip 不是 PASS**。

跑一次的方式与判据见 [LLM_ENDPOINTS.md](LLM_ENDPOINTS.md) §11；live 用例是
`tests/e2e/test_ec04_live_first_run.py`（带 `requires_live_llm`，默认门只走 skip 路径）。

**回退要检查的三件事**：

1. `RESEARCHOS_AGENT_RUNTIME` 已去掉（`GET` 读面应回到 Fake runtime 的披露）；
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
| 漂移判定 | **一致**（实测返回标识 == 声明值）——见下「证明力边界」 |
| 终态 | `FAILED`（**设计内**：见下「判拒为什么不是缺陷」） |
| 口径 | `REPEATABLE_CONFIGURATION`（AGENTS.md §4；**不是**「完全模型可复现」） |
| usage 归账 | `MODEL_TOKENS` 1 条、合计 15219 tokens |
| 制品 | 1 条，id 以 `:session_message` 结尾 |
| 证据 | 1 条，`evidence:` 前缀 + 同一 `session_message` 后缀 |
| 如实缺口 | `system_fingerprint` 与 `safe_response_metadata` 缺失（记录里进 `missing_fields`，**不**留白冒充） |

**判拒为什么不是缺陷**：本示例协议的 task contract 要 `analysis_report`，而真实会话产出的是
`session_message`，于是 acceptance gate 按合约**判拒**——这正是登记链在正常工作。判据请对照
`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的 `_assert_deliverable_adjudicated`：
它把「`FAILED` + 点名 acceptance gate」固定为真实 runtime 路径的**期望**结果，并把
「出现 `carries no structured output`」当成判红条件（那才说明登记链被跳过）。
本次样本的制品 id 后缀恰好是 `:session_message`，与该路径一致。

**证明力边界（别过度解读）**：`一致` 只代表**这一次**一致——它**不**证明该中转站永不漂移，
也**不**证明底层模型与声明完全同一。单次样本**不能**把三态里的「一致」升级成永久结论；
按 AGENTS.md §4，结论口径**只能**停在「可重复配置」。

**未捕获的一项（如实登记）**：本次运行的**逐条失败消息**产生于该次进程内的 in-memory
事件库，进程结束即消失，因此**没有**留成文本。上面的归类依据是三条**收敛**证据
（制品 id 后缀为 `:session_message`、usage 已真实归账、probe 段已 `verified and ok`）
加上同路径离线判据对 `FAILED` 的既有期望——**不是**直接读到的失败字符串。
