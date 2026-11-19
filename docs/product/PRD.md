# Product Requirements Document v1.0

> **本文档是产品需求面的单一权威。**
> 历史文档 `docs/PRODUCT.md`（v0.4.0，105 行）与 `docs/product/PRD_GAP_ANALYSIS.md`
> （275 行）的内容已并入本文，两份保留为历史档案、不再单独维护。
> 与代码冲突时**以代码与实跑为准**（本仓一贯口径），并在同一轮修正本文。
> **防漂移**：GOAL-116 EC-01 的判据（`tests/tooling/` 下，随 EC-01 落地）逐条断言
> 「本文的说法 == 树的事实」（改本文数字或改树里的事实 ⇒ 判红并点名条号）。
> 本表其余数字仍是**调研时点（2026-11-20）的读数**（§7.1 属时点读数，不进防漂移判据）。
>
> 建档：GOAL-20261120-116（序 84）。调研日期 2026-11-20。

## 1. 产品是什么 / 不是什么

### 1.1 是什么

```text
Research Agent Operating Environment
+ Autonomous R&D Control Plane
+ Evidence-native Audit System
```

一句话：**一个可审计的科研执行环境**——用户给方向与预算，系统编译协议、预检、
分派角色与任务、调工具、跑实验、做独立评审、产出可复核的交付物，
并把每一步落进 canonical 状态。

用户提供：Research Objective（方向）· Target Profile（可选）· Code/Data/Sources ·
LLM Relay URL + Key + Model IDs · Tool Integrations · Budget · Autonomy Policy。

系统完成：

```text
Compile → Preflight → Role/Agent Allocation → Task Execution
→ Tool/Workspace Operations → Evidence/Experiment → Independent Evaluation
→ Deliverable → Reproducibility/Audit
```

### 1.2 不是什么

- 纯聊天机器人；
- 固定 26 Agent 群聊；
- 论文文本生成器（本仓判的是**结构事实**，不是文采）；
- IDE 克隆；
- 无权限边界的 Shell Agent；
- 把 LLM 评分当科学真相的系统。

### 1.3 与市面的定位差异（一句话）

市面对手全部选择「**做深一节**」：Sakana 做实验+论文、Elicit 做综述、
Kosmos 做长时程分析。本仓选择「**做全链路**」，并把**投稿仪式**（编辑决定 /
逐条应答 / 投稿包五件 / 期刊闭集）做成结构事实——这一点今天**没有被任何对手做到**。
代价是全链路的每一节都比对手浅，见 §5。

## 2. 目标用户与场景

| 项 | 内容 |
| --- | --- |
| 用户 | **单用户、个人长期使用者**（研究者 / 独立研究员） |
| 不是 | 企业 SaaS、多租户、团队协作平台（M18 DEFERRED，`ADR-0028`） |
| 部署 | Personal Production（单机 + 可选 GPU worker） |
| 关键场景 | ① 一个方向跑出一份可复核的手稿与投稿包；② 多轮推进同一课题并累积结论；③ 留下能被人复核的取证链 |

**明确的非需求**：多人协同、组织隔离、计费与账号体系。

## 3. 核心工作流

### 3.1 十一相主链（旗舰）

`examples/protocols/direction_to_manuscript_v1.yaml` —— **11 相：9 个会话相（10 个
角色实例，`review` 相 2 位评审）+ 2 个确定性相（`experiment` / `report`）**。

| # | 相 | 类型 | 角色 | 产出 |
| --- | --- | --- | --- | --- |
| 1 | `question` | 会话 | research_director | `research_question` |
| 2 | `retrieval` | 会话 + 运行链 | domain_researcher | `retrieval_report` |
| 3 | `novelty` | 会话 | novelty_author | `novelty_claim` |
| 4 | `plan` | 会话 | research_director | `research_plan` |
| 5 | `experiment` | **确定性** | experiment_engineer（声明） | `experiment_runs` |
| 6 | `review` | 会话 ×2 | scientific_reviewer + novelty_reviewer | `review_decision`（QUALITY_GATE） |
| 7 | `manuscript` | 会话 | research_writer | `manuscript_narrative` |
| 8 | `editorial` | 会话 | scientific_editor | `editorial_decision`（四值闭集） |
| 9 | `revision` | 会话 | research_writer | `author_responses` |
| 10 | `submission` | 会话 | research_writer | `submission_package` |
| 11 | `report` | **确定性汇编** | — | 7 件 `.md`（见 §3.2） |

### 3.2 一次 run 的交付物

`report` 相确定性产出 7 件：

`research_report.md` · `manuscript.md` · `cover_letter.md` · `author_contributions.md` ·
`conflicts_of_interest.md` · `data_availability.md` · `supplementary.md`

有改稿材料时额外产出 `manuscript_v2.md`（`supersedes` → v1）与 `response_letter.md`。

**写法归属可读**：模型写正文（第 1–4 节 / IMRaD），汇编器写数字与 References；
`Artifact.created_by` + 元数据 `narrative` 块说明「谁写的」。

### 3.3 拟定新增：数据分析→报告（本文档提出，GOAL-116 二阶交付）

外部基准（§7）要求 agent **从原始数据**产出报告。当前链路无此能力（§5.3）。
拟新增 `analysis_to_report_v1`：数据勘察 → 分析计划 → **脚本执行（AUTHORED）** →
校验 → 报告。

## 4. 能力矩阵 vs 市面

> **读法**：外部一列全部来自**公开页面/论文**，**未经实测**。本仓一列是实查。

| 能力 | 本仓 | Apevon Science | Sakana AI Scientist | Edison Kosmos | FutureHouse | Google co-scientist | Elicit / Consensus / Undermind |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 文献检索 | ✅ PubMed + Europe PMC，默认 3 条 | 宣称（未实测） | ✅ Semantic Scholar 查新 | ✅ 文献 + 自有数据 | ✅ PaperQA2 全文 RAG | ✅ | ✅ 400M+ / 深度检索 |
| 全文阅读 | ❌ **仅元数据与摘要** | 宣称 | ❌ | ✅ | ✅ | ✅ | ✅（Consensus/Undermind） |
| 假设生成 | ⚠️ 单条 novelty 主张 | 宣称 | ✅ 多想法筛选 | ✅ 分支假设 | ⚠️ | ✅ 多假设 + Elo 自评 | ❌ |
| 实验执行 | ⚠️ **三个白名单脚本** | 宣称（GPU 环境） | ✅ 自己写代码跑 | ✅ 计算分析 | ❌ | ❌ | ❌ |
| 任意分析代码 | ❌ `AUTHORED` 默认关闭 | 宣称 | ✅ | ✅ | ❌ | ❌ | ❌ |
| 手稿 | ✅ IMRaD + Vancouver References | 宣称「to paper」 | ✅ LaTeX 论文 | ❌ | ❌ | ❌ **不写论文** | ❌ |
| 编辑决定 / 逐条应答 | ✅ **唯一**（四值闭集 + P1…Pn） | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 投稿包五件 | ✅ **唯一** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 独立评审可归因 | ✅ 双模型 + `reviewer_model` | 宣称 | ⚠️ 自评审（单模型） | 未公开 | ❌ | ❌ 自评 Elo | ❌ |
| 审计 / 可复现 | ✅ **冻结 manifest + 内容寻址 + 两树复检** | 宣称可追溯 | ⚠️ 存执行文件 | 宣称 on-prem | ❌ | ❌ | ❌ |
| 长时程 / 中途 steering | ❌ 无 | 宣称 | ❌ | ✅ 24h / 292 轨迹 | ❌ | ⚠️ 专家在环 | ❌ |
| 外部基准读数 | ❌ **零**（本文档要补） | 宣称 RCB 榜首（未证实） | 自评接近人类 | 未公开 | 基准 LitQA2 | 自评 Elo | 各自内部基准 |
| 身份 / 多租户 | ❌ 单 token，读面不认证 | 团队版 | ❌ | ✅ SOC2 / on-prem | ❌ | 受限测试 | ✅ SaaS |

**结论**：本仓在**审计链、投稿仪式、评审可归因**三处领先；在**文献深度、假设发散、
端到端产出率、外部读数**四处落后；在**长时程**上结构性缺失。

## 5. 竞争差距与优先级

### 5.1 一阶差距（已量化，可直接推进）

| # | 差距 | 读数 | 优先级 |
| --- | --- | --- | --- |
| D-1 | **无外部基准** | 零次外部评测 | **P0（本文档的由来）** |
| D-2 | 端到端产出率 | 十一相链真实 **4 SUCCEEDED / 31 FAILED / 1 PAUSED**（36 次，截至 2026-11-18 普查；集中在 retrieval 9 / experiment 6 / plan 5） | P1 |
| D-3 | 文献深度 | 默认 `retmax=3`；仅元数据，无全文 | P1 |
| D-4 | 任意分析代码 | `AUTHORED_ALLOWED_BY_DEFAULT = False`；沙盒无科学栈 | **P1（D-1 的前置）** |

### 5.2 二阶差距（需新域概念或产品决策）

| # | 差距 | 性质 |
| --- | --- | --- |
| D-5 | 假设发散为零 | 需 `HypothesisSet` 新域概念（改 Canonical State） |
| D-6 | 投稿面不存在 | `submission` 在 OpenAPI **零命中**；期刊是占位符（假 ISSN） |
| D-7 | 旗舰链不可从 UI 到达 | `protocol_drafts.py` 只暴露 5 个模板，十一相不在其中 |
| D-8 | 无身份系统 | 单 token；读面永不认证；`access_control.yaml` 零 Python 消费者 |

### 5.3 结构性缺失（本轮不排期）

- **长时程 / 分支探索**：`phase.strategy` 只被编译器消费，相数 = 会话数，无并行；
  `POST /runs/{id}/interventions` 对语义变更返回 501。
- **全文抓取**：`elink` 只回 PMC id，不取正文。

## 6. 需求登记表

> **机器可读约定**：本表列序固定为 `ID | 需求 | 状态 | 判据`。
> 状态词表：`已实现` / `部分` / `未实现` / `不宣称`（四值，不许别的词）。
> 判据列写**可执行的命令或可复核的文件路径**。
> **防漂移判据**（GOAL-116 EC-01 交付，见 `PLAN-20261120-119` WP-A）按本表逐条断言
> 「文档说法 == 树的事实」；该判据尚未落地，落地前本表是**人工维护**的。

| ID | 需求 | 状态 | 判据 |
| --- | --- | --- | --- |
| R-01 | 协议编译 → 预检 → 冻结 manifest → 执行 | 已实现 | `tests/application/run_orchestration` |
| R-02 | 十一相链可在一次 run 内走完 | 已实现 | `tests/e2e/manuscript_chain_live_support.py`；真实读数见 §7 |
| R-03 | 手稿 IMRaD + Vancouver References + `[n]` 双向闭合 | 已实现 | `packages/application/deliverable/manuscript.py` |
| R-04 | 编辑决定四值闭集 + 逐条应答 `P1…Pn` | 已实现 | `packages/application/deliverable/author_response.py` |
| R-05 | 投稿包五件（信/贡献/COI/数据可用/补充） | 已实现 | `packages/application/run_orchestration/submission_assembly.py` |
| R-06 | 双模型评审可归因 + 分歧可读 + advisory 并存 | 已实现 | `GET /runs/{id}/panel-advice`；`tests/e2e/test_two_models_judge_the_same_artifact.py` |
| R-07 | 硬门 `REVIEW_SCORE ≥ 0.8` 不得放宽 | 已实现 | `examples/contracts/task_contracts.yaml` |
| R-08 | 文献检索（PubMed / Europe PMC 元数据） | 已实现 | `adapters/research_tools/ncbi.py`、`adapters/research_tools/europe_pmc.py` |
| R-09 | 文献全文 | 未实现 | `adapters/research_tools/` 内无 PMC 正文 fetch |
| R-10 | 检索深度可配（出厂默认 3，上限 100） | 已实现 | `services/api/retrieval_wiring.py`（`DEFAULT_RETMAX=3` / `MAX_RETMAX=100`） |
| R-11 | 实验执行（白名单脚本） | 已实现 | `packages/application/experiments/script_authority.py`（`shipped_scripts()`） |
| R-12 | 任意分析代码（`AUTHORED`） | 部分 | 机制在（具名 profile），**默认关闭**：`AUTHORED_ALLOWED_BY_DEFAULT = False` |
| R-13 | 沙盒含科学计算栈 | 未实现 | `adapters/execution/sandbox/Dockerfile`（`python:3.12-slim`，无 numpy 等） |
| R-14 | 假设发散（多候选 + 排序） | 未实现 | 代码面无 `HypothesisSet` 实体（仅文档提及该概念） |
| R-15 | 投稿端点（真实投稿系统对接） | 未实现 | `docs/api/openapi.m13.json` 内 `submission` 零命中 |
| R-16 | 身份 / 多租户 / RBAC | 不宣称 | `packages/domain/principal.py`（M18 DEFERRED） |
| R-17 | exactly-once | 不宣称 | `docs/architecture/WORKFLOW_RELIABILITY.md`（口径 = at-least-once + 幂等 + 去重） |
| R-18 | 外部基准读数（ResearchClawBench） | 未实现 | `docs/benchmarks/RESEARCHCLAWBENCH.md`（接入方案） |
| R-19 | 叙述质量 / 论证成立 / 引用是否支持主张 | 不宣称 | `packages/application/deliverable/manuscript_quality.py` 的 `NOT_JUDGED` 五项 |
| R-20 | 模型视觉能力 | 未实现 | `examples/config/models.yaml` 零 `VISION` 声明 |

## 7. 验收与读数

### 7.1 内部读数（实查）

| 项 | 读数 | 时点 |
| --- | --- | --- |
| 十一相链真实 run | **4 SUCCEEDED / 31 FAILED / 1 PAUSED**（36 次） | 2026-11-18 普查 |
| 失败集中相 | retrieval 9 · experiment 6 · plan 5（= 20/31，65%） | 同上 |
| 双评审真实 run（新中转站） | **3 次**：k1 FAILED（2/2 判负）· k2 FAILED（2/2 判负）· k3 **SUCCEEDED**（2/2 通过）；三次 `voters=2`、`independent=True`、判词可归因 | 2026-11-19 |
| 双评审分歧 | 三次的 `dissent` **均为空**（同一合约组内两位判词一致）——如实登记：免费模型集上**未观测到分歧** | 2026-11-19 |
| 单次评审耗时 | 120s / 107s / 88s | 同上 |
| console 覆盖 | 33 路由 = **14 full / 18 partial / 1 gap** | 2026-11-20 |
| 后端面 | 109 paths / 134 operations（69 GET · 45 POST · 9 PATCH · 3 PUT · 8 DELETE） | 同上 |
| 能力承接 | 47 条声明 · 22 条有 provider · **14 条被协议实际使用**（`examples/protocols/*.yaml` 的 `required_capabilities` 并集） | 同上 |

### 7.2 外部读数（本轮要建立）

基准：**ResearchClawBench**（InternScience，MIT）。40 任务 × 10 学科；
agent 从**原始数据**产出 `report/report.md`；多模态 LLM judge 按加权 rubric 打分。

**评分语义（必须如实转述）**：> **50 = 达到已发表论文水平**；> 70 = 超越。
公开榜首 **34.89**（InnoClaw），另一条公开读数 28.38（jiutian-DeepInsight）。
README 原话：`every point above 50 is uncharted territory`。

**本仓目标（按三阶）**：

| 阶 | 目标 | 判定 |
| --- | --- | --- |
| 一阶 | 取得**基线读数**（含 0 分） | 能产出 `report.md` 与否都要记；零分是合法读数 |
| 二阶 | 同任务分数 **> 基线** 且报告含 ≥1 图 | 若仍为 0 ⇒ 点名结构性阻塞并 BLOCKED |
| 三阶 | 3 任务 / ≥2 学科各有读数 | 逐条记录分数、耗时、失败分类 |

**不宣称**：即使拿到非零分，也**不宣称**「达到论文水平」（那是 >50）。

## 8. 声称边界

1. **`NOT_JUDGED` 五项**（逐字，`manuscript_quality.py`）：引用是否支持该句、论证是否
   成立、方法学是否合适、引用是否充分、文风 / 可读性 / 语法。**全部未判。**
2. **引用充分性阈值全 `None`**：有读数 ≠ 判了「充分」。
3. **无全文**：只有元数据与摘要；References 不是文献综述。
4. **无视觉**：模型不能读自己产出的图。
5. **单用户**：无租户隔离、无 RBAC、无 BOLA/BFLA；**读面永不认证**。
6. **不宣称项目安全**（`R-M1` 未收口）。
7. **不宣称 exactly-once**。
8. **模型可重复配置 ≠ 完全可复现**（§4：中转站可在同一 id 后换真实模型）。
9. **外部对照全部来自公开页面，未经实测**；对手的局限是**它们自己承认的**。

## 9. 非目标与暂不实施

| # | 事项 | 为什么不进本轮 |
| --- | --- | --- |
| 1 | 真实投稿端点 / 期刊对接 | 决定外部世界互动，需产品决策 |
| 2 | `journals.yaml` 真实化 | 涉及对外声明，「不是评分」是刻意的 |
| 3 | RBAC / 多租户 | M18 整块，改 Canonical State 边界 |
| 4 | `AUTHORED` **出厂默认**开启 | 安全面扩大；本轮只在基准 profile 内放行 |
| 5 | `retmax` 出厂默认提高 | 影响成本与检索语义，需拍板取值 |
| 6 | 假设发散 `HypothesisSet` | 新域概念 |
| 7 | 长时程 / 分支探索 | 重写编排语义，代价远大于收益 |
| 8 | 读面认证 | 与既有「读面永不认证」设计相悖 |
| 9 | `plan_fallback` 接线 | 要重算评审独立性的穷举结论 |

## 10. 来源

**仓库内**：`docs/PRODUCT.md`、`docs/product/PRD_GAP_ANALYSIS.md`、
`docs/roadmap/MILESTONES.md`、`docs/adr/ADR-0028`、
`docs/architecture/{SYSTEM_ARCHITECTURE,MANUSCRIPT_QUALITY,WORKFLOW_RELIABILITY}.md`、
`docs/security/IDENTITY_AND_ACCESS.md`、`docs/frontend/CONSOLE_PAGE_MAP.md`、
`docs/api/{CONTROL_PLANE_API.md,openapi.m13.json}`、
`apps/web/src/navigation/{registry,pageSupport}.ts`、
`packages/application/deliverable/*.py`、`examples/protocols/direction_to_manuscript_v1.yaml`。

**外部**（公开页面，未经实测）：Apevon Science（`apevon.ai`；注意
`apevonscience.com` 是 JS 空壳）、ResearchClawBench（`github.com/InternScience/
ResearchClawBench`，arXiv 2606.07591）、Sakana AI Scientist（arXiv 2408.06292）、
Google AI co-scientist、FutureHouse（PaperQA2 / Robin）、Elicit、Consensus、Undermind。
