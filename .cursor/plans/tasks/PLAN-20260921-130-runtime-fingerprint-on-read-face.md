---
id: PLAN-20260921-130
slug: runtime-fingerprint-on-read-face
title: 运行时指纹四要素落读面，并把「模型不存在」的样本面如实收口（GOAL-010 EC-04）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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

- [ ] WP1 **定案（承重墙，先审后改）**：在下面的**候选面表**上定案——四要素在**读时刻**
  分别从哪里来、DTO 长什么样、缺项怎么表达、`REPEATABLE_CONFIGURATION` 由谁判。
  产出：定案 + 代价 + 回退路径 + **不做**边界。**先落记录再改代码**。
- [ ] WP2 **按定案落读面**：DTO/映射/回填源 + 读面判据（含 AC-3 的按压）+ OpenAPI 快照与
  web 类型（若 DTO 变化，按仓库配方同步）。
- [ ] WP3 **「模型不存在」样本**：按 AC-4 二选一落地（真实调用取最小必要，或如实登记 + 代价）。
- [ ] WP4 **门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。

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

- 2026-09-21 derive：由 GOAL-20260921-010 的 EC-04 派生（`parent_goal` 投影 ALL_PLAN）。
  **只读代码与配置、未发起任何真实调用**，实测得 E-1…E-9 与候选面表 + 三条不可回避取舍。
  **承重墙定为 WP1（定案）**：核心问题是「**调用后**才存在的四要素，如何在**冻结于调用前**的
  manifest 之外成为可读的 canonical 事实」，以及「缺项怎么表达而不扩口径枚举」。
  **本 PLAN 的起点事实**：E-4/E-6 —— 真实 run 的读面**今天恒为 NOT_VERIFIED 占位**，
  而四要素的记录类型与口径**早就写好**（E-5），只是**没有产品调用方**（E-6）。
