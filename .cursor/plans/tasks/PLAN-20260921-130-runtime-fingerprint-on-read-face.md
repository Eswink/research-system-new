---
id: PLAN-20260921-130
slug: runtime-fingerprint-on-read-face
title: 运行时指纹四要素落读面，并把「模型不存在」的样本面如实收口（GOAL-010 EC-04）
status: DONE
created_at: 2026-09-21
updated_at: 2026-09-21
parent_goal: GOAL-20260921-010
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260921-010 cycle 4 = EC-04（漂移与指纹样本补全）。授权来源：2026-09-21 用户 goal 模式指令
    frontmatter `authorization.ref`——(1) live-gated 真实调用授权（**次数取最小必要**；provider 侧样本
    若跑，能复用既有 session 就不另发）；(5) push-to-main-for-CI（只推 main、不 force、不重写历史）。
    **本 PLAN 明文不做**：改验收门判定语义使其变松、改 validator/门禁/快照、skip 或降低任何断言强度、
    新增依赖、改上游 pin、把真实 runtime 设为默认、把凭据写进 CI、把「装配层推断」写成 provider 侧观测。
    照抄 EC-04 判定细则的两条**不得**：**不得**把「没观测到漂移」写成「无漂移」；
    **不得**把「没看到 system_fingerprint」冒充「模型可复现」。**触到 Domain / Canonical State
    边界（例如给 Run 加新的域字段）即 BLOCKED**，留人工拍板。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260921-130-runtime-fingerprint-and-model-absence.md
memory_entries:
  - .cursor/memory/entries/MEM-20260921-103-model-absence-taxonomy-and-false-green-judges.md
---

# PLAN-20260921-130 — 运行时指纹四要素落读面（GOAL-010 EC-04）

## 目标

GOAL-010 EC-04 的两件事，各自可判：

1. **指纹四要素落读面**：真实 run 的**返回 model 名 / 端点头 / probe 版本 / 兼容性结论**
   必须能从**既有读面**取到，而**不是只活在测试的 `tmp_path` 里**（GOAL-009 EC-01 的落盘位置）。
   口径停在 `REPEATABLE_CONFIGURATION`（AGENTS.md §4）；`system_fingerprint` 缺失是**诚实缺口**
   （记进「缺哪几项」），**不**降级判定、**也**不用它冒充「模型可复现」。
2. **「模型不存在」的样本面收口**：现状只有**装配层**判据（固定标签表 + 「run 的 LLM 装配只消费
   一个模型」的结构判据）。要么补一条 **provider 侧真实样本**（点名模型标识的失败 + **零回退**到
   别的模型），要么**如实登记为未实测并写明代价**——**不得**把装配层推断写成 provider 侧观测。

## 验收条件

- **AC-1 读面可取四要素**：真实 run 的读面能取到（或**如实点名缺哪几项**）返回 model 名、
  端点头（endpoint config digest）、probe 版本（suite digest）、兼容性结论；四种取值**都是可判的状态**，
  不含编造值。
- **AC-2 口径不越界**：结论仍是 `REPEATABLE_CONFIGURATION` / `NOT_VERIFIED` 两态**穷举**
  （GOAL-008 EC-04 已把它做成类型上不可表达「完全可复现」）；缺项存在 ⇒ 不许报
  `REPEATABLE_CONFIGURATION`。
- **AC-3 反证成对**：把真实 run 的指纹事实**摘掉**（或把必填项挖空）⇒ 读面必须**点名缺项**并
  给出 `NOT_VERIFIED`；复原 ⇒ 复绿。**先红后绿**两向都留证据。
- **AC-4 「模型不存在」有结论**：要么 provider 侧真实样本（含**零回退**证据），
  要么如实登记为未实测 + 代价。**两者都不许含糊**。
- **AC-5 不改口径强度**：不得为了让读面好看而放宽任何断言；不得把「未观测」写成「无漂移」。
- **AC-6 门禁与记录**：规模门禁自查（50 行函数 / 450 行文件）→ 定向套件 →
  `make validate-all`（m0 全量 23/23）→ 治理 `validate.py` 绿 → 独立 RECHECK（含 W 列表）+
  GOAL 回写（EC-04 状态 / 迭代日志 / `child_plans` / `latest_recheck`）。

## 实施清单

- [x] WP1 **定案（承重墙，先审后改）**：在下面的**候选面表**上定案——四要素在**读时刻**
  分别从哪里来、DTO 长什么样、缺项怎么表达、`REPEATABLE_CONFIGURATION` 由谁判。
  产出：定案 + 代价 + 回退路径 + **不做**边界。**先落记录再改代码**。
- [x] WP2 **按定案落读面**：DTO/映射/回填源 + 读面判据（含 AC-3 的按压）+ OpenAPI 快照与
  web 类型（若 DTO 变化，按仓库配方同步）。
- [x] WP3 **「模型不存在」样本**：按 AC-4 二选一落地（真实调用取最小必要，或如实登记 + 代价）。
- [x] WP4 **门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。

## 证据（derive 阶段实测；**只读代码/配置，未发起任何真实调用**）

| # | 事实 | 核对方式 | 对 EC-04 的含义 |
| --- | --- | --- | --- |
| E-1 | run 级读面的指纹槽**只有三个字段**：`RuntimeFingerprintDto{status, substrate, reason}` | `services/api/dto/runs.py:104`；`RunExecutionDto.runtime_fingerprint` | 四要素**今天的读面上物理上放不下**（多给的键会被 pydantic 拒） |
| E-2 | 该槽的**唯一来源**是冻结 payload 的 `runtime_fingerprint` 键 | `services/api/run_execution_view.py:20-51` | 读面 = 冻结事实的回放，不是实时探测；要补四要素就得先有**冻结事实** |
| E-3 | 冻结 payload 里的这个键 = `manifest.model_runtime_fingerprints` | `packages/application/run_orchestration/eventing.py:78` | 名字是「**model** runtime fingerprints」，内容却不是模型的 |
| E-4 | 该 manifest 槽由 `runtime_fingerprints(deps)` 填，**内容恒为状态记录**：`{"substrate", "status": "NOT_VERIFIED", "reason"}` | `services/api/preflight_support.py:64-67` + `services/api/runtime_support.py:69-90` | **实测的缺口**：即使真实 runtime 跑过一次真实会话，读面仍写「runtime selected but no model probe fact was collected for this run」 |
| E-5 | 四要素的**承载类型已存在**：`LiveRunRecord{endpoint_config_digest, returned_model_identifier, system_fingerprint, probe_suite_digest, safe_response_metadata, missing_fields, verdict, model_tokens, usage_entries, artifact_ids, evidence_ids}` | `packages/application/model_relay/live_run_record.py:40` | 形状、口径、缺失项语义**都已经写好**，缺的是**接进产品链** |
| E-6 | `build_live_run_record` 的调用者**只有测试**；GOAL-009 EC-01 的 live 判据把它写进 `tmp_path/live-run-record.json` | `rg build_live_run_record`（仅 `tests/`）+ `tests/e2e/test_ec04_live_first_run.py:164-166` | 正是 EC-04 点名的「只活在测试的 `tmp_path` 里」 |
| E-7 | 模型级读面**已经有**富字段 DTO：`ModelRuntimeFingerprintDto{endpoint_config_digest, probe_suite_digest, returned_model_identifier, system_fingerprint, observed_capabilities}` + 产品侧 builder `build_fingerprint` | `services/api/dto/models.py:33`、`services/api/mappers/models.py:92`、`packages/application/model_relay/fingerprint.py:61` | 「形状」与「builder」都不缺；缺的是**「这一次 run」**这一层 |
| E-8 | 「模型不存在」今天只有**装配层**判据：固定标签表（无效凭据 / 端点拒绝 / 模型不存在）+ 「run 的 LLM 装配路径只消费**一个**模型」的结构判据；live 失败样本只有**无效凭据 ⇒ 401** 一条 | `tests/architecture/python/test_live_failure_paths_same_source.py:37/133/181`；`tests/e2e/test_live_failure_paths.py:117` | EC-04 verify 的**零回退**那一半**已有结构判据**；缺的是 provider 侧**样本** |
| E-9 | 冻结门的必填锚点里，指纹只要求「**非空**」（NOT_VERIFIED 占位也算） | `packages/application/run_orchestration/m12_composition.py:158-175`（注释写明「未配置 = NOT VERIFIED 诚实占位，不视为缺口」） | 补四要素**不会**顺手改变冻结门的强度；但**也不要**借机加严（那是另一个 EC 的事） |
| E-10 | **四要素的现成来源是一次 `run_live_probe`**：GOAL-009 的 live 判据正是从 `probe.endpoint_config_digest` / `probe.returned_model_identifier` / `probe.probe_suite_digest` / `probe.system_fingerprint` 取这四项，再从 run 读面取 usage/制品/证据 | `tests/e2e/test_ec04_live_first_run.py:126-138`；`packages/application/model_relay/live_probe.py`；`packages/application/model_relay/probe.py:107/195`（`returned_model_name` 由 probe 的 **chat** 调用取得） | 「落读面」的**接线**有现成材料；但**provenance 必须如实**：probe 事实来自**那次 probe 调用**，不是本次 run 的响应（取舍 #1 的实质） |
| E-11 | adapter 今天记的是**请求**的 model id，**不是响应返回的 model 名**：`UsageContext(model_id=entry.spec.model.id …)`，注释明写「缺目标时保持 None——不猜、不回填别的 model」 | `adapters/openhands/session_builder.py:148-167` | 「本次 run 的响应里返回了哪个 model」**今天没有被采集**；要拿到它得改 adapter（摸 SDK 事件树）**或**走 probe（额外一次真实调用）——这是 WP1 必须正面回答的那一刀 |
| E-12 | `MODEL_PROBED` / `MODEL_RESOLVED` / `MODEL_DRIFT_DETECTED` 三个事件类型**已声明但产品代码里无人发出**（`rg` 只命中定义处） | `packages/domain/events.py:26-28` | 承载面「有坑位没接线」；**复用既有枚举成员**不触 Domain，但也要如实说明「此前从未被发出」 |
| E-13 | **「本次 run 的返回 model 名」可零额外调用拿到**：SDK 的 `Metrics extends MetricsSnapshot`，而 `MetricsSnapshot.model_name` 就是「Name of the model」；adapter 已经在读**同一个** `ConversationStats`（`usage_to_metrics: dict[str, Metrics]`）做记账 | `.venv/.../openhands/sdk/llm/utils/metrics.py:76-92,113`；`conversation/conversation_stats.py:13-20`；`adapters/openhands/session_builder.py:148-167`） | **定案的决定性一条**：不必改 adapter 的 SDK 交互面、不必加 probe 调用——同一对象多读一个字段即可（取舍 #1 **不需要**再花钱） |
| E-14 | `MetricsSnapshot.model_name` **有默认值 `"default"`** | 同上（`Field(default="default", …)`） | 诚实边界：取到 `"default"` 只能当**缺项**处理（它不是模型名），**不得**当已观测值写进四要素 |

### 已知的**不可回避**取舍（定案必须在其中做出选择并写明代价）

1. **「读时刻」决定一切**：`returned model name` 与「兼容性结论」**只在一次真实调用之后**才存在，
   而 manifest 是**调用之前**冻结的 ⇒ 「在读面看见它们」必然要求**调用后**再产生一份 canonical 事实
   （或把结果补进已冻结的事实——后者会破坏「冻结即不可变」的语义）。**这是本 EC 的承重墙**。
2. **两态穷举 vs 四要素**：口径只有 `REPEATABLE_CONFIGURATION` / `NOT_VERIFIED`，
   而现实至少四态（全有 / 缺 provider 侧项 / 无 probe / 没跑真实执行体）⇒ 缺项必须由
   `missing_fields` 表达，**不得**为了表达现实而扩枚举（扩枚举 = 改口径语义，触 Domain 即 BLOCKED）。
3. **provider 侧样本的代价与含义**：拿一个**不存在**的模型标识去调端点，能得到「provider 拒绝」
   的观测，但**能不能**得到它取决于中转站行为（它可能把未知模型静默映射到别的模型——那正是
   AGENTS §4 要防的漂移）。所以这一条**必须实测**，不能推断；若实测结果模糊，就**如实登记模糊**。

### 候选面（WP1 在此表上定案，逐条写明代价）

| 候选 | 形态 | 代价 | 已知风险 |
| --- | --- | --- | --- |
| (a) 扩 `RuntimeFingerprintDto` | 在 run 级 DTO 上加四要素 + `missing_fields`，回填源 = 冻结后写入的 canonical 事实 | DTO 变更 ⇒ OpenAPI 快照 + web 类型 + e2e 夹具同步 | 冻结**之后**的事实从哪来必须答清楚，否则变成「读面编数」 |
| (b) 复用模型级读面 + run 只放指针 | run 读面给 endpoint/model 标识，四要素去模型详情页看 | 产品面改动最小 | **不满足** EC-04 的「**这一次 run** 的指纹落读面」——模型级读面是**登记面**的事实，与某次 run 无关 |
| (c) 新增独立 run 级指纹路由 | 新端点专供指纹 | 新路由 ⇒ OpenAPI/前端/设计基线三处耦合 | 与既有 `execution` 面重复度高；「零 DTO 变更」的既有惯例被打破 |

## WP2 落地（**已完成**）

### 做了什么（一条事实一行）

| # | 事实 | 位置 |
| --- | --- | --- |
| W2-1 | 会话结果带回**观测**：`AgentSessionResult.observed_model_identifiers`（Port 加性字段，默认空 = 没观测） | `packages/application/ports/agent_runtime.py` |
| W2-2 | 观测量取自 adapter **已经在读**的 `ConversationStats`：`observed_model_names(stats)`；SDK 默认哨兵 `"default"` **不算观测**（E-14） | `adapters/openhands/usage_mapping.py` |
| W2-3 | 会话终态时把观测随结果带出；读不到（stats 缺失/异常）⇒ **空手而归**，不冒充已观测 | `adapters/openhands/session_builder.py`、`runtime_adapter.py` |
| W2-4 | 观测 = 「这次会话实际用到的端点 digest」+「provider 侧报告的 model 名」；没有 model 名 ⇒ **不产生观测**（无空观测） | `packages/application/model_relay/observation.py`（新） |
| W2-5 | 执行循环把观测交回 service（`on_observation`，与既有 `on_pause` 同形）；默认不注入 = 不收集 | `packages/application/run_orchestration/phase_runner.py`、`service.py` |
| W2-6 | run 返回前把观测落成 **`MODEL_PROBED`**（此前只声明、从未发出）；**没有观测 ⇒ 不发事件** | `packages/application/run_orchestration/runtime_fingerprint.py`（新） |
| W2-7 | 读面在冻结占位之外合并实测记录并标明来源（`source`）；缺项由 `missing_fields` **逐项点名** | `services/api/dto/runs.py`、`run_execution_view.py` |
| W2-8 | 快照/类型/夹具同步：`openapi.m13.json` 重生成、`apps/web/src/api/types.ts`、stub 夹具、live e2e spec（新增"占位必须点名四项"断言） | 见 diff |
| W2-9 | 文档回写：`CONTROL_PLANE_API.md`（读面两份事实的合成口径）、`EVENT_MODEL.md`（`model.probed` 真的会发了） | docs |
| W2-10 | 判据：单元 6 条 + adapter 3 条 + HTTP 成对 3 条（含**先红后绿**） | `tests/application/run_orchestration/test_runtime_fingerprint_fact.py`、`tests/adapters/openhands/test_model_observation.py`、`tests/api/test_run_fingerprint_read_face.py` |

### 对 WP1 定案的两处**有界偏离**（逐条写明理由，均已落进模块 docstring）

1. **payload 少发布四个记录键**（`model_tokens` / `usage_entries` / `artifact_ids` /
   `evidence_ids`）：本层拿不到「这条 run 的」usage 与制品真值，而记录里这四个的默认值是
   0/空 —— 发一份带 0 的记录等于把一个**没测过**的数写成实测值（usage 的真值面是 cost/usage
   读面）。**只减不增**。
2. **payload 多带一个实测键**（`observed_model_identifiers`）：单值槽位表达不了「一次 run
   观测到多个不同 model 名」，藏起来等于把「观测到不一致」读成「没观测到」。多值本身是
   **观测结果**，原样带上；单值槽位仍留 `None`（缺项 ⇒ 结论必为 `NOT_VERIFIED`，**不挑一个**）。

### 判据的射程（**不声称**的部分）

- 离线三条 HTTP 判据用**受控执行体报告 provider 侧 model 名**驱动链路：它判的是**接线**
  （观测 → canonical 事件 → 读面），**不**声称「真实 provider 真的报告了什么」——那是 WP3。
- `system_fingerprint` 给不给取决于 provider：缺失**只点名、不降级**（记录自报缺项里还会
  含 `safe_response_metadata`；DTO 不以字段形式呈现它，但如实转述）。
- `model.probed` **不**进通知白名单（`services/api/routers/notifications.py`）⇒ 不产生用户
  可见通知；这是有意的（指纹事实不是通知事件）。
- 控制台**未**新增渲染分支（EC-04 的判据在 HTTP 读面；类型面已同步）⇒ **不**触发设计基线
  重生成。

### 门禁证据（本轮全部在本机实跑）

- `m0`：**`PASS: profile=m0; 23 deterministic checks`**（`python/tests` = 4301 passed / 16 skipped）。
- 定向：`ruff check` / `ruff format --check` / `mypy` 在产品根（apps/services/packages/adapters/tests）全绿。
- 前端：stub e2e **96 passed**；live e2e（`live-run-substrate-disclosure`，真 app + Playwright）**1 passed**。
- 治理：`governance-check/validate.py`、`docs_consistency`、`validate_bundle.py` 全绿。

## WP3 落地（**已完成**：走 AC-4 的**第一条**——provider 侧**真实样本**，不登记为未实测）

### 样本形态

`tests/e2e/test_live_model_absence.py`（`requires_live_llm`，**预置条件式**：未声明
`RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1` ⇒ SKIP 并点名；默认门禁下不跑）。

- **只调一次** `run_endpoint_test`（连通性 `GET /models` + 一次 chat），指向已登记真实端点
  `agnes-anthropic`，用一个**不可能存在**的 model 标识（`research-os-absent-model-v1`）。
- `url_policy` **不覆盖** ⇒ 走产品默认策略（拒 localhost / 环回 / 私有 / 保留），本样本不放松任何门。
- 包一层 `_StepRecorder` 在真网关外面记录**每一步**的结果面（ok / 类别 / 消息是否点名模型，
  **没有正文**）——产品代码一行不改。
- 观测结果原样打到 stdout 并写进 `tmp_path`（全脱敏：只有布尔与标识）。

### 实测事实（2026-09-21，本机，`-s` 实跑，逐字取自样本自报的 JSON）

| # | 事实 | 读数 |
| --- | --- | --- |
| W3-1 | **连通性那一步过了** | `{"step": "connectivity", "ok": true}` ⇒ 端点与凭据都没问题，**这次拒绝不可能是「中转站的 /models 挂了」** |
| W3-2 | **拒的是那次 chat** | `{"step": "chat", "ok": false, "request_model": "research-os-absent-model-v1"}` |
| W3-3 | **失败类别 = `MODEL_RELAY_UNAVAILABLE`** | 该类别由 **5xx** 映射而来（`failure_category_of_http_status`）⇒ **中转站用自己的 5xx 表达这次拒绝** |
| W3-4 | **错误正文点名了请求的标识** | `message_names_the_absent_model: true` ⇒ 判定细则里「点名模型标识」**有实测支撑**，不是修饰语 |
| W3-5 | **没有静默映射**（AGENTS §4 的漂移反证） | `returned_model_name: null`、`returned_name_differs_from_requested: false`、`ok: false` |
| W3-6 | 凭据未泄漏 | 断言 `credential not in error_message` 通过 |
| W3-7 | 快拒，非超时 | 全程 ~8.2s ⇒ 不是「重试到超时」 |

### 由 W3-3 得到的**新增诚实边界**（已写进 RUNBOOK §7，成为第 4 条）

「模型不存在」**没有专属失败类别**：它与「中转站故障」共用 `MODEL_RELAY_UNAVAILABLE`，
而该类别**在可重试集合里**（`adapters/relay/transport.py` 的 `_RETRYABLE_CATEGORIES`）。
所以：**按类别读会读错**——这一格唯一能把两者分开的读数面是**消息是否点名模型标识**。
这条是**实测出来的**，不是推理出来的；它把「点名模型标识」从措辞升级成**判据的必要条件**。

### 文档与判据同步

- `docs/integration/LIVE_MODEL_RUNBOOK.md` §7：「模型不存在」一格补上**实测样本出处 + 实测读数**；
  边界从三条扩为**四条**（新增上条）。**保留** `adapters/openhands/llm_factory.py`（装配侧那一半）。
- `tests/architecture/python/test_live_failure_paths_same_source.py`：新增
  `TestTheModelAbsenceRowPointsAtAMeasuredSample`（4 条）——那一格**必须同时**指到装配层 builder
  **与**实测样本；样本必须 `requires_live_llm` + 预置条件式。任一侧被摘掉即判红（防止
  「样本没了但行文照旧」）。

### 按压抓出的**判据缺陷**（本 cycle 自己造成并修好的一条）

第一版的「预置条件式」两条是**文本**判据（`assert "pytest.skip(" in text` +
`assert 开关名 in text`）。按 WP4 的纪律**按压**（把样本里的开关名改成 `…_CASE_PRESSED`）⇒
**仍然 20 passed**。原因：被断言的开关名是别名的**前缀**，子串判定不区分。

**改成行为判据**（成对）：删掉开关 ⇒ 样本抛 skip（`pytest.raises(pytest.skip.Exception)`）；
声明开关 ⇒ **必须不 skip**。第二版第一次写出来仍不红——`_require_case()` 抛的 skip 会把
**判据自己**变成 skip，而 **skip 不是红**。最终形态加两条防线：
`样本的开关常量 == 判据里的开关名`（等价性断言）+ 把 skip **转成 `pytest.fail`**。
**再压**（同一个改名）⇒ **RED（真失败，不是 skip）**；复原 ⇒ 复绿。

### 判据的射程（**不声称**的部分）

- **单次观测**只覆盖**这一次**调用：**不**声称「该 provider 对所有未知模型都如此」，
  也**不**声称「所有中转站都这么表现」。（这一句同时写在模块 docstring 里。）
- 样本走的是 **endpoint test**（probe）路径，**不是** run 执行路径：它证明的是
  「provider 面对未知模型会拒绝并点名」，**不**替代 run 侧的失败语义（那由装配层结构判据钉住）。

### 门禁证据（本轮实跑）

- 样本本身：`1 passed`（预置条件声明时）；**未声明时 `1 skipped`**（默认门禁姿态）。
- 架构判据：`tests/architecture/python/test_live_failure_paths_same_source.py` **21 passed / 1 skipped**
  （skip 的那条是样本自己）；**按压**（改开关名）⇒ 真 RED，复原 ⇒ 复绿。
- `ruff check` / `ruff format --check` / `mypy`：两个文件全绿。

### 门禁自己抓出来的一条（**收口树首跑红**，已修）

把 PLAN 置 `DONE` 后跑**收口树**全量 m0 ⇒ `FAILED: 1 check(s): framework/validate=1`（治理
`validate.py`），两条都点名本 PLAN：

1. `DONE 任务缺少 latest_recheck: PLAN-20260921-130`——`latest_recheck` 此前是 `null`；
2. `DONE 任务既无工程记忆引用，也未声明无可复用事实: PLAN-20260921-130`——`memory_entries` 此前是空表。

**处置**（不改校验逻辑、不放宽任何东西）：补 `latest_recheck`（**仓库相对路径**，非裸 ID——
GOAL-009 收口时抓过的同一类漏改）+ 落一条工程记忆
`MEM-20260921-103-model-absence-taxonomy-and-false-green-judges.md`（本 cycle 的两条可复用事实：
「模型不存在」无专属类别；两类「按了不红」的假绿判据）+ 在 `.cursor/memory/INDEX.md` 登记。
**这条红是本 cycle 自己造成、自己修好的第三条**，如实登记——**首跑红不记成绿**。

## WP1 定案（**已完成**：取 (a) 的「调用后 canonical 事实 + 读面合并」形态）

### 逐条回答四个问题

1. **四要素在「读时刻」分别从哪里来**（E-10…E-14 实测支撑）：
   - **返回 model 名** ← `ConversationStats.usage_to_metrics[*].model_name`（SDK 的 `Metrics` 继承
     `MetricsSnapshot`，含 `model_name`）。**这是本次 run 自己的度量**，来源就是 adapter 已在读的
     那个对象 ⇒ **零额外调用**。取到哨兵值 `"default"` 时按**缺项**处理（E-14）。
   - **端点头** ← `endpoint_config_digest(endpoint)`（产品侧可算，不触网）。
   - **probe 套件版本/digest** ← `default_probe_suite()` + `probe_suite_digest(...)`（同上，不触网）。
   - **兼容性结论** ← `build_live_run_record(...)` 的既有两态规则（E-5）：终止状态 + 必填项齐全 ⇒
     `REPEATABLE_CONFIGURATION`；缺任一项 ⇒ `NOT_VERIFIED` 并**点名缺哪几项**。
2. **DTO 长什么样（不编造）**：`RuntimeFingerprintDto` 在保留 `status/substrate/reason` 的基础上
   增加**可选**四要素字段 + `missing_fields`；**取值只能来自上面的实测源**，取不到就是缺项，
   **绝不**用默认值/占位符填。
3. **`REPEATABLE_CONFIGURATION` 由谁判**：仍由 `build_live_run_record` 判（既有语义、既有测试），
   读面**只呈现** `record.verdict.value`——**不新造第二个判据**、**不扩枚举**。
4. **承载面**：**复用既有事件链**——run 终止后把 `record.to_payload()`（已脱敏、字段封闭）
   作为 **`MODEL_PROBED`**（E-12：已声明、从未发出、语义贴合「模型被观测到」）的 payload 落进
   canonical 事件链；读面 `run_execution_dto` 在既有冻结占位之外**读该事实并优先呈现**
   （冻结事实不可变，占位保持原样；**读面负责合并**，语义写清「占位 vs 实测」两态）。

### 被否的候选与理由

- **(b) 复用模型级读面 + run 只放指针**：模型级读面是**登记面**的事实（E-7），与「这一次 run」
  无关；用它顶替会违反 EC-04 verify 的「该 run 的指纹」。
- **(c) 新增独立 run 级指纹路由**：与既有 `execution` 面重复，且打破本仓反复使用的
  「读面走既有路由、零路由变更」惯例（GOAL-006 EC-06 的原话）。
- **改 adapter 去摸 SDK 事件树的响应体**：E-13 表明**不需要**——同一 `ConversationStats` 已带
  model 名；摸事件树只会引入 SDK 内部耦合（AGENTS §5 的上游策略：adapter 优先，但能不改就不改）。
- **probe-derived（E-10 那条路）**：可与本方案并存为**降级源**（当 usage 度量里拿不到 model 名时），
  但**必须标注 provenance**（「来自该端点最近一次 probe，非本次 run 的响应」），
  且**不**为它另发调用（调用纪律）。

### 代价与回退

- 代价：run 级 DTO 变更 ⇒ OpenAPI 快照 + web 类型 + e2e 夹具同步（影响报告里的耦合面）；
  终止路径多一次事件写入（**同事务**语义与既有 `run.completed` 一致，不新增迁移）。
- 回退：撤 DTO/映射/事件写入与快照 ⇒ 读面回到今天的 `NOT_VERIFIED` 占位。
  **不涉及** Domain / Canonical State 字段 / 数据迁移。

### 诚实边界（写死，WP2 不得越过）

- 四要素里 **`system_fingerprint` 仍可能缺**（provider 是否给不取决于我们）⇒ 落 `missing_fields`，
  **不降级**结论（承 `RECHECK-121` W-5），**也绝不**把缺项写成「无漂移」。
- 「返回 model 名」取自**本次 run 的 usage 度量**，不是原始响应头；读面措辞必须与这个来源一致
  （不得写成「provider 声明的响应头」）。
- 结论只有两态：`REPEATABLE_CONFIGURATION` / `NOT_VERIFIED`；**不得**出现「完全可复现」类表述。

## 影响报告

### 为什么承重墙是 WP1（先审后改）

EC-01/EC-02/EC-03 的判据都落在**一次 run 之内**（交付物名、来源计数、协议身份），而 EC-04 的判据
落在**一次 run 的产物能不能被后人读到**——它天生要穿过**冻结边界**：manifest 在**调用之前**冻结，
而「返回的 model 名」「兼容性结论」**只在调用之后**存在。于是「落读面」这件事有三种截然不同的实现面：

- 若选择**在冻结时**填四要素 ⇒ 那时只有端点头与 probe 套件 digest 存在，model 名与兼容性结论
  **必然编造**（这正是 AGENTS §4 与 EC-04 的**明文禁区**）；
- 若选择**调用后补写冻结事实** ⇒ 破坏「冻结即不可变」的语义（`manifest.frozen` 是重建入口）；
- 若选择**新增一份调用后的 canonical 事实** ⇒ 要么落在既有事件/载荷形态里（不触 Domain 边界），
  要么给 Domain 加字段（**触 boundary ⇒ BLOCKED，留人工拍板**）。

这三条路的差别**决定了这个 EC 是不是在做一件诚实的事**，所以定案必须先于任何代码改动。

### 与已达成 EC 的边界

- **EC-01/EC-02/EC-03 的判据不依赖本 EC**：它们各自的证据（交付物名、来源集合、协议身份）都已落
  RECHECK-127/128/129，且**不读指纹面**。本 EC 改读面**不得**顺手改它们的判据文件。
- **GOAL-008 EC-04 的成果必须复用而不是重造**：两态穷举的 `ModelReproducibilityVerdict` 与
  「缺项必须点名」的 `LiveRunRecord` 语义（E-5）已是既有资产；本 EC 的活是**接线**，
  不是新造一套指纹模型。若定案发现需要**改**这两个既有类型的语义 ⇒ 说明定案选错了路。
- **GOAL-007 EC-01 的 `NOT_VERIFIED` 槽位语义保留**：状态记录本身没错（默认 demo 执行体确实
  一件事实都没有），缺的是**真实 run 之后**把它换成实测记录的那一步（E-4 的 docstring 里写着
  「真实事实由出网门链与离线全链在拿到 probe 结果后**替换**」——那一步**今天没有实现**）。

### 耦合面（改动要逐个点名处理，不手改基线数字）

- **OpenAPI 快照**：run 级 DTO 若变 ⇒ `docs/api/openapi.json`（或等价快照）+ `apps/web` 的类型面
  必须同提交更新（仓库既有配方），否则门禁红——**不得**只改快照不改语义、也**不得**反过来。
- **设计基线**：若 run 详情页新增渲染分支 ⇒ 按既有配方**重新生成**像素/结构基线（不手改数字）。
- **web e2e 夹具**：run 详情夹具若缺新字段会像 EC-02 的 R-2 一样被 `typescript/typecheck` 抓出来
  （那是**正确**的拦阻，夹具要按产品语义补齐，不是删断言）。

## 不做（写死，防扩边）

- **不**给 `Run`/`RunManifest` 加**新的域字段**（触 Canonical State 即 BLOCKED）。
- **不**扩 `ModelReproducibilityVerdict` 枚举、**不**新增「完全可复现」任何形态的表述。
- **不**改冻结门的必填锚点强度（E-9：现在只要求非空）。
- **不**把 live 调用接进默认路径；provider 侧样本只在 live-gated 模块里跑。
- **不**为了让读面好看而把 `missing_fields` 隐藏或改成空。

## 回退路径（写明）

纯读面 + 记录面改动：回退 = 撤销 DTO/映射/判据与对应快照，**不涉及** Domain / Canonical State /
数据迁移；已冻结的历史 run 事实不变（读面回退后只是**看不见**，不会**看错**）。

## 状态历史

- 2026-09-21 WP3 **落地**（provider 侧真实样本，走 AC-4 第一条）：
  `tests/e2e/test_live_model_absence.py` 以**一次**最小真实调用实测「不存在的 model 标识」，
  读数逐字留在上表 W3-1…W3-7。**本次共 3 次真实调用**（第 1 次验判据可跑通；第 2 次把观测
  打出来；第 3 次补**步骤轨迹**）——第 3 次是必要的：前两次的记录**分不清**是连通性那步还是
  chat 那步拒的，而这两件事语义完全不同，不区分就可能把「中转站挂了」写成「provider 拒了
  未知模型」。**新增实测边界**：这一类失败**没有专属类别**（与中转站故障共用
  `MODEL_RELAY_UNAVAILABLE`，且**可重试**）⇒ 「点名模型标识」是唯一的区分读数面。
  文档 + 架构判据同步（§7 第四格与第 4 条边界；4 条新判据两侧都钉住）。
  **按压抓出并修好一条判据缺陷**：第一版「预置条件式」是文本子串判据，改开关名仍绿 ⇒
  改成**行为成对** + 等价性断言 + **skip 转 fail**；再压 ⇒ 真 RED，复原 ⇒ 复绿（详见上「按压抓出」）。
- 2026-09-21 WP2 **落地**（按 WP1 定案接线，见上「WP2 落地」）：
  四要素从「只活在测试的 `tmp_path`」变成**产品路径上的 canonical 事实**——会话观测
  （零额外调用，来源是 adapter 已在读的 `ConversationStats`）→ `model.probed` 事件 →
  `GET /runs/{id}` 的 `execution.runtime_fingerprint` 合并呈现（`source` 标明占位还是实测，
  缺项逐项点名）。两处**有界偏离**已逐条写明理由；离线判据**不**声称 provider 侧真相（WP3 的事）。
  本轮**未发起任何真实调用**（离线受控执行体驱动；真实样本在 WP3）。门禁：m0 23/23。
- 2026-09-21 derive：由 GOAL-20260921-010 的 EC-04 派生（`parent_goal` 投影 ALL_PLAN）。
  **只读代码与配置、未发起任何真实调用**，实测得 E-1…E-9 与候选面表 + 三条不可回避取舍。
  **承重墙定为 WP1（定案）**：核心问题是「**调用后**才存在的四要素，如何在**冻结于调用前**的
  manifest 之外成为可读的 canonical 事实」，以及「缺项怎么表达而不扩口径枚举」。
  **本 PLAN 的起点事实**：E-4/E-6 —— 真实 run 的读面**今天恒为 NOT_VERIFIED 占位**，
  而四要素的记录类型与口径**早就写好**（E-5），只是**没有产品调用方**（E-6）。
