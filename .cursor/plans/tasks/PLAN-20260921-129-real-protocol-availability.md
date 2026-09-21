---
id: PLAN-20260921-129
slug: real-protocol-availability
title: 真实协议的可用性：把「真实执行体跑一份自称 Fake 的 demo 协议」这个错配修掉（GOAL-010 EC-03）
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
    GOAL-20260921-010 cycle 3 = EC-03（真实协议的可用性）。授权来源：2026-09-21 用户 goal 模式指令
    frontmatter `authorization.ref`——(1) live-gated 真实调用授权（**次数取最小必要**）；
    (5) push-to-main-for-CI（只推 main、不 force、不重写历史）。**本 PLAN 明文不做**：
    改验收门的判定语义使其变松、改 validator/门禁/快照（**含设计基线/release asset**）、
    skip 或降低任何断言强度、新增依赖、改上游 pin、把真实 runtime 设为默认、把凭据写进 CI。
    **触到 Domain / Canonical State 边界（例如给协议加新的域字段）即 BLOCKED**；
    **为了让 run 跑通而删除/削弱 `required_capabilities` 以绕过 preflight = 放宽验收门**
    （GOAL frontmatter escalation_triggers 第 11 条）⇒ **触及即 BLOCKED**。
    **不引入新依赖、不新造 URL 判据**（复用既有 `endpoint_policy`）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260921-129 — 真实协议的可用性（GOAL-010 EC-03）

## 目标

**确定「真实 run 用哪份协议」并把它落地成可判事实。** 现状是一个**产品面可见的错配**：
登记面（`examples/config/project.yaml`）把本项目的协议登记为 `ai_ml_research_v0_4_0`，
控制台「参考协议预检」也以此命名；**而真实 run 跑的却是 `console_demo_research_v1.yaml`**——
该文件头部**自己写着**「受控 **Fake** agent loop 快速终态…**不冒充真实研究执行**」。
用真实执行体跑一份**自称不是真实研究**的协议，是本 EC 要消灭的形态。

**判据（EC-03 原文）**：所选**协议 id 出现在 run 的 canonical 事实里**（不是只出现在测试文件里）；
且该协议文件在仓库中**存在且被登记**（加载器可解析）。
**反证**：把 canonical 事实里的协议标识改回 demo 协议 ⇒ 判据**必须红**。

## 验收条件

- **AC-1 决策被记录（承重墙）**：候选**逐个点名**、取舍与**代价**写明、**回退路径**写明。
  **不得**为了让 run 跑通而降低协议的能力要求（删 `required_capabilities` 绕过 preflight
  = 放宽验收门 ⇒ 触及即 BLOCKED）；**也不得**为了凑 id 而把协议写成「不声明任何能力」的空壳。
- **AC-2 可用性（**实测**，不是加载成功就算）**：所选协议在**产品路径**上可解析——
  ①文件可加载；②`required_roles` 在 `examples/config/roles.yaml` 里**逐个**存在；
  ③`required_capabilities` 在 `examples/config/policy.yaml` 里**逐个**被授予（点名出处）；
  ④`task_contract` 在 `examples/contracts/task_contracts.yaml` 里**存在**，且其
  `acceptance_criteria` 逐条**可达**（含 `EVIDENCE_COVERAGE` 的 `minimum_sources`——
  EC-02 收紧后**只有非模型自述的来源计入**）。
- **AC-3 登记同源**：示例目录与**登记面**指向**同一份**协议；登记面的耦合面
  （`FRAMEWORK_MANIFEST.json` 是 **release asset**、`examples/contracts/compiled_run_plan.yaml`
  是该协议的 golden 编译计划、控制台**设计基线** `design-outlines.json` 渲染了协议名、
  `protocol_drafts.py` 模板表、web e2e stub/fixture、loader 测试）**逐个点名并同源更新**，
  基线类改动**按既有配方重生成**（不手改基线数字）。
- **AC-4 canonical 判据**：run 的 canonical 事实（run 记录 / 事件链 / 读面）中可取的协议标识
  **恰为**所选协议 id。
- **AC-5 反证成对**：把 canonical 事实里的协议标识**改回 demo 协议** ⇒ 判据**红**；复原 ⇒ 复绿。
- **AC-6 真跑（最小必要次数）**：真实 runtime 下用所选协议起一次 run，**终态如实记录**——
  **只有 `SUCCEEDED` 是成功**；`FAILED` 如实写并附失败原因与归类，**不得**写成成功、
  **不得**为了它改判据。
- **AC-7 门禁与记录**：规模门禁自查（**50 行函数 / 450 行文件**）→ 定向套件 →
  `make validate-all`（m0 全量 23/23）→ 治理 `validate.py` 绿 → 独立 RECHECK（含 W 列表）+
  GOAL 回写（EC-03 状态 / 迭代日志 / `child_plans` / `latest_recheck`）。

## 实施清单

- [x] WP1 **协议候选与解析链实测 + 定案**（**承重墙，先审后改**）。把每个候选的
      角色/能力/合约/preflight/会话成本**实测**完整，据此**二选一**：
      **(A) 对齐到已登记的真实协议**，或 **(B) 新增一份真实协议并登记**。
      产出：候选表（含代价）、定案与理由、回退路径、以及**不做**边界。
      **已完成**：**取 (B)**。**(A) 的两个必答问题都已正面回答**（A1：10 条非自述来源
      今天只有「声明输入」（否决——只有计数变真）与「工具结果」（无生产调用方 + live 工具惰性
      ⇒ 需先做检索接线，属另立 cycle 的 W-7）两条路，**本轮答不了**；A2：phase 数 = 会话数
      ⇒ 11 次真实会话，与「最小必要」纪律冲突）。**实测**补一条决定性事实：
      `evidence.read` **未被 `policy.yaml` 授予**（`default_effect: DENY`）⇒ `sort_analysis_v1`
      在真实 policy 下**连 preflight 都过不去**。⇒ 在册 6 份协议里**没有一份**同时满足
      「语义对真实执行体成立」与「合约本轮可达」。**(B) 的规格、四条护栏、代价、诚实边界已写死在
      「WP1 定案」节**（WP2 按规格落地）。
- [x] WP2 **按定案落地**（**已完成**）。逐条对齐「(B) 的规格」：协议
      `examples/protocols/real_research_task_v1.yaml`（id `real_research_task_v1_0_1`，
      1 phase `analysis` / `single_agent` / `domain_researcher` / `artifact.read` /
      `task_contract: real_research_deliverable` / `inputs: [input-brief:real_research_v1]`，
      头部写明真实执行体语义**与受控范围**）；合约 `real_research_deliverable`
      （`ARTIFACT_EXISTS: analysis_report` 恰一个 + `EVIDENCE_COVERAGE minimum_sources: 1`，
      **不含** `SCHEMA_VALID`／`TEST_PASSES`）；声明输入
      `examples/inputs/real-research-brief-v1.json` + `services/api/demo.py::DECLARED_INPUTS`
      同一 id，同源结构判据的协议映射同步；登记面 `services/api/routers/protocol_drafts.py`
      新增 `real-research-task` 模板（**不动** `project.yaml` 的 `protocol:` 字段 ⇒ 不触发设计基线重生成）。
      **规格外的一项改动，如实登记**：合约 schema 要求 `output_schema` 必填 ⇒ 新增
      `schemas/real_research_deliverable_v1.schema.json`（信封字段取自 adapter 实现，不编形状），
      并在 `validate_bundle.py` 的 JSON Schema 注册表加**一行**。这是仓库**既有**的新 schema 维护路径
      （先例：提交 `4156238` 在同一提交里新增 `export_bundle_v1`/`reproducibility_audit_v1`
      两个文件**及其注册行**）。**它不是放宽**：注册表仍是双向一致检查，且**已按压**
      （删掉该行 ⇒ 该检查红、报出同一条不一致；复原 ⇒ 复绿），`git diff` 显示**只加一行**、
      校验逻辑一字未改。两个被否的备选：(d) 只声明名字不建文件（留下悬空声明）、
      (a) 复用语义不符的**已注册**名（正是 EC-01 抓的那类「名不副实」）。
      **实测**：产品路径编译 PASS（1 条 INFO `DAG_ORPHAN_PHASE`——单 phase 无后继，如实）；
      模板面 4 项含 `real-research-task`；声明输入已 seed（装配内 3 件制品、mark 状态可重入）。
- [x] WP3 **canonical 判据 + 反证**（**已完成**）：新增
      `tests/api/test_real_protocol_identity.py`，把三个面钉在一起——**文件自己**声明的 `id:`
      （从正文里读，不 import 被测实现）、**canonical run** 的 `protocol_id`（经读面回读）、
      **被解析的那份字节**（`protocol_body_digest` == 该正文的 sha256，且冻结正文里含它自己的 id），
      并断言 run 走到 `SUCCEEDED`。**成对**：两份协议各起一次 run，身份、正文摘要、正文内容
      三者都必须互不相同且互不出现对方的名字 ⇒ 判据**不可能是常量**。
      **按压（AC-5）**：把期望值改成「canonical 事实 = **demo** 协议的 id」⇒ 真实协议那条**红**
      （`assert 'real_research_task_v1_0_1' == 'console_demo_research_v1_0_1'`，失败信息里带着
      真实 canonical 事实），**demo 那条仍绿**（证明不是一刀切地红）⇒ 复原 ⇒ **复绿**。
      **顺带测得一条事实**：新合约在**默认（Fake）离线装配**下也到 `SUCCEEDED`
      ——声明输入已 seed ⇒ `EVIDENCE_COVERAGE` 被**非模型自述**来源满足，即「可达性」
      在控制面已经成立；**真实执行体**下的可达性由 WP4 单独取样，本文件**不**声称。
- [ ] WP4 **真实 run**（最小必要次数）：真实 runtime 下用所选协议起 run；终态如实落 RECHECK。
- [ ] WP5 **门禁 + 复检 + 收口**：规模门禁自查 → 定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。

## 证据

### derive 阶段已实测的事实（**只读代码/配置，未发起任何真实调用**）

| # | 事实 | 核对方式 | 对本 EC 的含义 |
| --- | --- | --- | --- |
| E-1 | **真实 run 用哪份协议，今天是测试侧的常量** | 读 `tests/e2e/live_run_support.py`：`_PROTOCOL = "console_demo_research_v1.yaml"`，`start_run()` 用它 POST `/projects/{id}/runs` | 「真实 run 用哪份协议」这件事**今天没有产品面的决定**，只有一个测试文件里的字符串 ⇒ 本 EC 要把决定**落到登记面** |
| E-2 | **登记面指向的是另一份协议** | 读 `examples/config/project.yaml:7`：`protocol: ai_ml_research_v0_4_0`；同一字符串出现在控制台**设计基线**（团队页渲染 `ai_ml_research_v0_4_0.yaml · 仅对此模板及当前配置有效`）与 `services/api/routers/protocol_drafts.py:55`（模板表） | 错配是**产品面可见**的：面板说的是一份真实研究协议，run 跑的是自称 Fake 的那份 |
| E-3 | **示例目录里有 6 份协议，需求面差异极大** | `load_protocol()` 逐份加载（详见下表） | 选型不是「换个字符串」，而是**选择语义+成本** |
| E-4 | **产品面只登记了 4 条合约** | 读 `examples/contracts/task_contracts.yaml`：`domain_discovery`（`SCHEMA_VALID` + `ARTIFACT_EXISTS source_set` + **`EVIDENCE_COVERAGE 10`**）、`experiment_execution` 与 `m12_experiment_execution`（`ARTIFACT_EXISTS metrics` + `TEST_PASSES` + `POLICY_COMPLIANT`）、`console_demo_deliverable`（`ARTIFACT_EXISTS analysis_report` + `EVIDENCE_COVERAGE 1`） | **`task_contract` 不在这 4 条里的协议，在产品路径上解析不出合约** ⇒ 候选面被这条实测**大幅收窄** |
| E-5 | **`sort_analysis_v1.yaml` 的两条合约只活在测试里** | 该协议的 `task_contract: sort_analysis_execution` / `sort_analysis_review` 在 `examples/contracts/task_contracts.yaml` 中**不存在**，只在 `tests/e2e/scenario_catalog.py` 定义 | 它虽是 2-phase 且能力齐全，**今天不是产品协议** ⇒ 若选它必须**先把它登记成产品合约** |
| E-6 | **`phase.strategy` 在产品侧只是声明** | `rg -n "\.strategy\b" packages services adapters`（排除 tests）⇒ **唯一**消费者是 `packages/application/protocol_compile/compiler.py:62`（透传进 `CompiledPhase.strategy`）；**编排层不读它** | `parallel_agents` / `map_reduce` / `population_search` / `iterative_optimizer` 今天**不是可执行语义** ⇒ **phase 数 = 会话数**（`ai_ml_research_v0_4_0` 有 **11** 个 phase）⇒ 直接决定 live 调用成本，且「多智能体并行」这句话在 UI/文档里**不可宣称** |
| E-7 | **canonical 载体已经存在** | run 记录带 `protocol_id`（实测值 `console_demo_research_v1_0_1`，PG e2e 与 EC-02 live 样本都读到过） | AC-4 的判据**有现成读面**，不需要新造字段 |
| E-8 | **登记面的改动有基线耦合（爆破面）** | `rg -l "ai_ml_research_v0_4_0"`（排除 scratch）⇒ `FRAMEWORK_MANIFEST.json`（**release asset，`release-assets-immutable` 门禁会比对**）、`examples/contracts/compiled_run_plan.yaml`（该协议的 golden 编译计划，`tests/loaders/test_contract_loaders.py` 用它）、`examples/config/project.yaml`、`services/api/routers/protocol_drafts.py`、`apps/web/tests/e2e/{design-outlines.json,stub-routes.ts,apiFixtures.ts}`、`tests/loaders/test_example_protocol_integration.py` | 换协议**不是改一行**：至少 6 处同源面 + 1 处基线 + 1 处 release asset ⇒ WP2 必须**逐个点名处理** |

**候选表（E-3 的展开，属性全部实测）**：

| 协议 | id | phase 数 | `task_contract` | 产品合约可达 | `required_capabilities` | 语义（头部自述） |
| --- | --- | --- | --- | --- | --- | --- |
| `console_demo_research_v1` | `console_demo_research_v1_0_1` | 2 | `console_demo_deliverable` | ✅ | `artifact.read` | **「受控 Fake agent loop…不冒充真实研究执行」** ⇒ 语义不适用（本 EC 的起点） |
| `ai_ml_research_v0_4_0`（**登记面所指**） | `ai_ml_research_v0_4_0` | **11** | `domain_discovery` + `experiment_execution` | ✅（合约在册） | **无**（一条都没声明） | 真实多阶段研究协议（`intake`…`final_audit`） |
| `m12_reference_research_v1` | `m12_reference_research_v1_0_0` | 7 | `domain_discovery` + `m12_experiment_execution` | ✅ | `literature.search` / `literature.read` | 真实参考文献研究协议 |
| `m17_gpu_research_v1` | `m17_gpu_research_v1_0_0` | 6 | `m12_experiment_execution` | ✅ | 无 | GPU 受控实验（依赖 docker/GPU） |
| `sort_analysis_v1` | `sort_analysis_v1_0_1` | 2 | `sort_analysis_execution` + `sort_analysis_review` | ❌（E-5，合约只在测试里） | `workspace.read` / `workspace.write.code` / `code.execute` / `artifact.write` / `evidence.read` | M7 垂直切片参考场景（**受控范围、可重复**） |
| `human_gate_demo_v1` | `human_gate_demo_v1_0_0` | 1 | `domain_discovery` | ✅ | `literature.search` / `literature.read` | 人工门 demo |

**能力面（AC-2 的判据出处）**：`examples/config/policy.yaml` 授予
`workspace.read` / `artifact.read` / `artifact.write` / `literature.search` / `literature.read` /
`code.execute` / `workspace.write.code` / `workspace.write.notes` / `workspace.delete` /
`memory.write` / `network.academic` / `network.public` / `package.install` / `external.publish`；
`examples/config/roles.yaml` 声明了候选协议要用的全部角色（`domain_researcher` / `literature_scout` /
`experiment_engineer` / `scientific_reviewer` / `research_writer` 等，逐个在册）。

### 已知的**不可回避**取舍（定案必须在其中做出选择并写明代价）

1. **`domain_discovery` 的 `minimum_sources: 10`**：`ai_ml_research_v0_4_0` 与
   `m12_reference_research_v1` 的**第一个 phase**都绑它 ⇒ EC-02 收紧后该 phase 需要
   **10 条非模型自述来源**（`RECHECK-128` **W-7** 登记的「从未被任何 run 路径行使过」）。
   两条路：为它接上**真实检索来源**（新的检索能力接线，成本高、属新能力面），
   或**如实选定一份不需要 10 条来源的真实协议**（不降低任何既有声明）。
2. **`TEST_PASSES` / `POLICY_COMPLIANT`**：两条 `*_experiment_execution` 都要求它们 ⇒
   需要**真实测试证据与策略合规记录**才可能 PASS（`console_demo_deliverable` 没有这两条，
   这正是它当初能跑到 `SUCCEEDED` 的原因之一）。
3. **会话成本（E-6）**：phase 数 = 会话数 ⇒ 11 个 phase 的协议**违反**「live 调用取最小必要」
   的纪律，除非分阶段并如实登记。

⇒ **倾向（**WP1 定案，不是预判**）**：**(B) 新增一份真实协议并登记**，其语义对真实执行体**成立**、
能力需求**等于**真实所需（不空、不多）、合约**在册且可达**、phase 数**取最小**；
**(A) 对齐到 `ai_ml_research_v0_4_0`** 若被选，则必须**同时**给出「10 条来源从哪来」与
「11 个 phase 的会话预算」两个答案——否则它就是「把 run 挂在一条跑不动的协议上」。

## WP1 定案（**已完成**：取 **(B) 新增一份真实协议并登记**）

### 先回答 (A) 必须回答的两个问题（不回避、不用「以后再说」搪塞）

**(A1) `domain_discovery` 的 `minimum_sources: 10`——那 10 条非模型自述来源从哪来？**
今天只有两条机制能产生非自述来源，**两条都不通**：

- **声明输入**（组合根种入的 `USER_PROVIDED` 制品）：要凑到 10 条就得**声明 10 份输入**。
  那会让计数达标而**没有任何检索发生**——正是 EC-02 WP1 点名拒绝的形态
  （「把数字抬上去，而不让 claim 更真」）。**否决。**
- **工具结果**（`register_tool_evidence`）：EC-02 实测它**没有任何生产调用方**（E-4），
  且 live 判据里的工具是**惰性**的（恒返回 `inert`，属 EC-02 WP1 的**被拒来源类**）。
  要诚实满足它必须：把 `literature.search` 接到**真实检索 provider**
  （`examples/config/tool_providers.yaml` 已登记 `eutils-2026-08-22`；`adapters/research_tools/ncbi.py`
  会 `spill_large_result`）→ 把 `register_tool_evidence` **接进 run 链** → 让 live 装配使用
  **真实工具而不是惰性工具** → 新增一个**出网面**与它的证据纪律。
  **这是一整个 cycle 的接线**，且正是 EC-02 登记为残余的 **W-7**。
  ⇒ **(A1) 的诚实答案：本轮没有来源可用；要回答它必须先做检索接线（另立 cycle）。**

**(A2) 11 个 phase 的会话预算？**
E-6 实测「**phase 数 = 会话数**」⇒ `ai_ml_research_v0_4_0` 一次真实 run 至少 **11 次真实模型会话**
（重试另计），其中 `experiment_execution` 还要 `TEST_PASSES` + `POLICY_COMPLIANT`
（需要真实 workspace 执行与测试证据）。这与本 GOAL 的「**live 调用取最小必要**」纪律**直接冲突**。
⇒ **(A2) 的诚实答案：本轮预算不够，而且它不该是第一个真实协议。**

### 实测支撑：**在册的 6 份协议里，没有一份同时满足两个条件**

两个条件是：**①语义对真实执行体成立**（头部不得自称「受控 Fake…不冒充真实研究执行」）、
**②合约在本轮可达**（`task_contract` 在册**且**逐条 `acceptance_criteria` 能被真实 run 诚实满足）。

| 协议 | ① 语义成立 | ② 合约可达 | 卡在哪 |
| --- | --- | --- | --- |
| `console_demo_research_v1` | ❌（头部自称 Fake demo） | ✅ | 本 EC 的起点 |
| `ai_ml_research_v0_4_0`（**登记面所指**） | ✅ | ❌ | `domain_discovery` 的 10 条来源（A1）+ 11 phase 预算（A2）+ `TEST_PASSES`/`POLICY_COMPLIANT` |
| `m12_reference_research_v1` | ✅ | ❌ | 同上（7 phase） |
| `m17_gpu_research_v1` | ✅ | ❌ | `m12_experiment_execution` 的 `TEST_PASSES`/`POLICY_COMPLIANT` + GPU/docker 依赖 |
| `sort_analysis_v1` | ✅ | ❌ | 两条合约**不在册**（只活在测试里）；且 review phase 要 `evidence.read`——**`policy.yaml` 没有授予它**（`default_effect: DENY`）⇒ 真实 policy 下 **preflight 就过不去** |
| `human_gate_demo_v1` | ❌（名为 demo） | ❌ | `domain_discovery` 的 10 条来源 |

（`evidence.read` 未授予是**实测**：`rg -n "evidence\.read" examples/config/policy.yaml` ⇒ 无命中；
授予集为 `artifact.read` / `artifact.write` / `code.execute` / `external.publish` / `literature.read` /
`literature.search` / `memory.write` / `network.academic` / `network.public` / `package.install` /
`workspace.delete` / `workspace.read` / `workspace.write.code` / `workspace.write.notes`。）

⇒ **定案：取 (B)。** (A) 不是被否决的坏选项，而是**本轮答不了它的两个前提**；
它作为「完整研究计划」的终态保留，**登记为后继入口**。

### (B) 的规格（WP2 按此落地，逐条可判）

- **协议**：`examples/protocols/real_research_task_v1.yaml`，id `real_research_task_v1_0_1`
  （版本后缀沿用既有格式）。**1 个 phase**：`analysis`，`strategy: single_agent`，
  `required_roles: [domain_researcher]`（`roles.yaml` 在册；与 demo 协议**同一角色**，
  实测在 live 装配里可解析），`required_capabilities: [artifact.read]`
  （`policy.yaml` **已授予**、scope `project`；与 EC-01 那条已跑到 `SUCCEEDED` 的路径**同一能力集**）。
- **头部语义必须诚实**（本协议存在的理由）：写明「**真实研究任务**：由**所选 runtime** 执行，
  在真实执行体下就是真实模型会话」；**不得**照抄 demo 的自述，**也不得**声称
  多智能体/并行/检索（E-6／A1 实测它们不是可执行语义）；**受控范围也要写明**——
  单任务单交付物，**不**代表完整研究计划。
- **合约**：新登记一条（拟定 `real_research_deliverable`）：
  `ARTIFACT_EXISTS: analysis_report`（**恰一个**声明产物——EC-01 的机制要求唯一，
  多产物会回落事实名并判拒）+ `EVIDENCE_COVERAGE minimum_sources: 1`。
  **不加** `SCHEMA_VALID`／`TEST_PASSES`（今天诚实做不到的判据不写进去——写了就是让协议不可用，
  与「放宽」是两件不同的事）。
- **声明输入**：`inputs: [input-brief:real_research_v1]`，内容为**操作者提供的任务简报**
  （新增 `examples/inputs/real-research-brief-v1.json`；同步 `DECLARED_INPUTS` 表与同源判据
  `tests/architecture/python/test_declared_input_sources.py` 的协议映射）。
- **登记同源**：示例目录 + 登记面（`examples/config/project.yaml` 或模板面）指向同一份；
  受影响的耦合面（E-8：release asset / golden 编译计划 / 设计基线 / 模板表 / loader 测试）
  **逐个点名处理**，基线类**按配方重生成**而非手改。

**护栏（防「换名字的 demo」，也防放宽）**：

1. **不得只有名字不同**：头部必须写明真实执行体语义与受控范围；
2. `required_capabilities` 必须是**真实所需**——不是删空以绕过 preflight；
3. 合约判据**不得为空壳**（至少 `ARTIFACT_EXISTS` + `EVIDENCE_COVERAGE ≥ 1`），
   且**不得改动任何既有合约**使其变松；
4. **不得声称系统做不到的语义**（多智能体并行、真实检索——E-6／A1 实测）。

**代价（如实）**：新协议 + 新合约 + 新输入 + 登记面 ≈ 4 处产品面改动；
若改 `project.yaml` 的 `protocol:` 字段，会触发**设计基线**重生成（控制台团队页渲染协议名）
与可能的 release asset 更新——**按既有配方做，不手改基线数字**。

**本 EC 的诚实边界**：新协议只覆盖**单任务真实研究**；「完整研究计划」（多阶段/并行/检索）
仍**不可用**——它需要 A1 的检索接线与 E-6 的策略执行语义，**不在本 PLAN 射程内**，登记为残余。

### 失败如何落终态

- 真实 run 不能跑通所选协议 ⇒ 按失败面归类（协议面 / 能力面 / 合约面 / 装配面）并按 fix_policy 纠错；
  **`FAILED` 如实写**，**不得**改判据、**不得**降能力、**不得**把终态写成成功。
- 若定案**需要**改 Domain / Canonical State 边界（如给协议加新域字段），或**必须**删/削弱
  `required_capabilities` 才能过 preflight ⇒ **BLOCKED**（GOAL frontmatter 的 escalation_triggers），
  留人工拍板，**不在本 PLAN 自行决定**。

### 回退路径（写明）

选定协议是**配置/示例面**的改动（协议文件 + 登记面 + 合约 + 基线），
回退 = 把登记面与 `live_run_support._PROTOCOL` 指回 `console_demo_research_v1.yaml`
并复原基线；**不涉及** Domain / Canonical State / 数据迁移。回退后 EC-01/EC-02 的判据仍成立
（它们的判据钉的是交付物与证据面，不依赖协议选择）。

## 影响报告

### 为什么承重墙是 WP1（先审后改）

EC-01 是在**一处可判事实**（交付物键名）上打开，EC-02 是在**没有来源的地方开出一条来源链**，
EC-03 的性质又不同：**它是一个「选择」，而选择的代价分布在三个面**——
**语义**（这份协议的头部注释是写给谁看的）、**可达性**（角色/能力/合约/preflight）、
**成本**（phase 数 = live 会话数，E-6）。
先动 `live_run_support._PROTOCOL` 只会得到两种坏结局之一：**跑通了但语义还是假的**
（换一份协议名，头部依旧写着「不冒充真实研究执行」），或者**为了跑通而降能力**
（删 `required_capabilities` 绕过 preflight）——后者是本 GOAL 的**明文禁区**。
所以 WP1 的产出（候选表 + 定案 + 代价 + 回退路径）**先于**任何改动。

### 与已达成 EC 的边界

- **EC-01 的判据不依赖协议选择**（它钉「交付物键名由合约声明决定 + 真实 run 走到 `SUCCEEDED`」）；
  但**换协议会换合约**，而 EC-01 的证据是在 `console_demo_deliverable` 上取的 ⇒
  换协议后**不得**据此宣称 EC-01 的证据被削弱；若新协议的合约不同，**另行取样**。
- **EC-02 的判据同样不依赖协议选择**，但**新协议的合约若声明 `EVIDENCE_COVERAGE`**，
  其 `minimum_sources` 必须由**非模型自述**来源满足（声明输入即可，机制已在册）——
  这是 WP2 必须一并处理的面，**不得**靠「新合约不声明覆盖」来回避（那是放宽）。

## 状态历史

- 2026-09-21 derive：由 GOAL-20260921-010 的 EC-03 派生（`parent_goal` 投影 ALL_PLAN）。
  派生阶段**只读代码与配置、未发起任何真实调用**，实测得 E-1…E-8 与候选表；
  其中 **E-1/E-2**（决定只在测试常量里、登记面指向另一份协议）确认了本 EC 的起点形态，
  **E-4/E-5**（产品面只登记 4 条合约；`sort_analysis_v1` 的合约只在测试里）与
  **E-6**（`phase.strategy` 只是声明 ⇒ phase 数 = 会话数）把候选面**收窄并量化**。
  本 PLAN 的承重墙定为 **WP1（定案）**，未开工。

- 2026-09-21 WP1 **定案完成**（本 PLAN 的承重墙）：**取 (B) 新增一份真实协议并登记**。
  **(A) 没有被否决，而是它有两个本轮答不了的前提**，两个都正面回答了、没有用「以后再说」搪塞：
  **A1** 的 10 条非自述来源今天只有「声明输入」（**否决**：只有计数变真、没有检索发生，
  正是 EC-02 WP1 点名拒绝的形态）与「工具结果」（**无生产调用方** + live 工具**惰性**
  ⇒ 必须先做检索接线，那是一个 cycle 的活，正是 EC-02 的残余 **W-7**）；
  **A2** 的 11 个 phase 在 E-6 的「phase 数 = 会话数」下等于 **11 次真实会话**，
  与「live 调用取最小必要」冲突。
  **本轮新增一条决定性实测**：`evidence.read` **未被 `policy.yaml` 授予**
  （`default_effect: DENY`）⇒ `sort_analysis_v1` 的 review phase 在真实 policy 下
  **连 preflight 都过不去**（它此前只在 `FakePolicyEvaluator` 下被跑过）。
  据此得到一条可判结论：**在册 6 份协议里没有一份同时满足「语义对真实执行体成立」
  与「合约在本轮可达」** ⇒ (B) 是唯一可行路径，而不是偏好。
  **(B) 的规格已写死**（协议 id / 1 个 phase / 角色与能力都取自**已授予**集 /
  合约恰一个声明产物 + 覆盖 ≥ 1 / 声明输入 + 登记同源），并配**四条护栏**
  （防「换名字的 demo」、防删空能力、防空壳判据、防声称做不到的语义）。
  **本轮未发起任何真实调用、未改任何产品代码、未改门禁/断言、未改 pin。**

- 2026-09-21 WP2 **落地完成**（产品面改动 + 登记面 + 一处**已按压**的注册表行）。
  落地面逐条对齐 (B) 的规格，**未动** `project.yaml`（所以设计基线不重生成），
  **未改任何既有合约/判据/能力集**（新合约是新增，不是改旧）。
  **规格外新增的 schema 文件与注册表行**是本轮唯一触及受治理文件（`.cursor/skills/.../validate_bundle.py`）
  的改动：一行注册表条目，跟仓库自己的维护路径（先例 `4156238`），并已**反证按压**
  （删行 ⇒ 红、复原 ⇒ 绿）。**第一次 m0 全量因此红**（`framework/validate_bundle`：
  注册表不一致 + `additionalProperties: true`），两条都已按其**规格**修好：
  注册表补登；schema 自身改为 `additionalProperties: false` 并列全 adapter 恒发的 7 个键
  （**没有**放宽 `check_object_boundaries`——它一字未改，且对**这一份文件**刚红过）。
  **本轮仍未发起任何真实调用**；真实 run 在 WP4。

- 2026-09-21 WP3 **判据落地并按压**（canonical 协议身份 + 常驻反证）。
  判据的形态刻意选成「三个面互相钉死」而不是「回读一个字段」：只回读 `protocol_id`
  会被「run 记录照抄了入参」这种平凡实现满足，而把**文件自己声明的 id**、
  **canonical 记录**、**被解析的那份字节的摘要**三者放在一起，
  E-1/E-2 那种「登记面指向 A、run 装配 B」的分家形态才会被抓出来。
  **按压如实**：真实协议那条红、demo 那条同时绿——后者是本判据区分力的证据
  （不是把 `assert True` 换成 `assert False` 那种一刀切）。
  **顺带测得**：新合约在 Fake 离线装配下到 `SUCCEEDED`，覆盖门由**已 seed 的声明输入**
  满足——所以 WP4 的真实 run 要跨的只剩「真实执行体 + 真实端点」这一步，
  协议/合约/能力面**不再是未知量**。**本轮仍未发起任何真实调用。**
