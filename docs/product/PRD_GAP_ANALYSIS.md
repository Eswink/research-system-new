# PRD 差距分析 — 与市面科研 agent 的对照，以及作为科研 agent 的不足

> **本文档的读法**：只写「差在哪」，不写「我们更好」。
> 每条结论带仓库内证据（`file:line`）与外部对照来源。
> 外部对照基于 2026-11-18 的公开资料；它们自身的局限性同样登记在列。
>
> **建档**：GOAL-20261119-115 / PLAN-20261119-115。本文档是**调研交付物**，
> 不构成产品承诺，也不改任何产品边界。

## 0. 先讲清楚「本仓是什么」

仓库自述是 **system specification + Cursor project engineering framework**，产品是第二件事
（`README.md:3`）。这与市面所有科研 agent 的定位都不同——它们的自述是"一个能帮你做 X 的工具"，
本仓的自述是"一套可审计的科研执行环境，附带一个控制面"。

产品定义写在 `docs/PRODUCT.md:7-13`：

```text
Research Agent Operating Environment
+ Autonomous R&D Control Plane
+ Evidence-native Audit System
```

**明确的非目标**（`docs/PRODUCT.md:41-48`）：纯聊天机器人 · 固定 26 Agent 群聊 ·
论文文本生成器 · IDE 克隆 · 无权限边界的 Shell Agent · 把 LLM 评分当科学真相的系统。

**目标用户**（`docs/roadmap/MILESTONES.md:81-84`）：

> Research OS 当前服务于**单用户、个人长期使用的 Autonomous Research / R&D System**；
> 暂无 multi-user / organization 产品需求，无 Enterprise SaaS 部署目标。

**没有 PRD 文件。** 全仓 `find -iname "*prd*"` 零命中；`docs/PRODUCT.md`（105 行）
是事实上的产品定义，其余读起来像 PRD 的文档都是工程宪章（`.cursor/plans/goals/MAINLINE.md`
455 行，82 行程序表描述的是内部可验证性目标，不是用户成果）。

---

## 1. 与市面科研 agent 的定位差异

| 系统 | 它做什么 | 它明确不做 | 本仓的位置 |
| --- | --- | --- | --- |
| **Sakana AI Scientist** | 从代码库 + 方向自动：头脑风暴 → 查新 → 写代码 → **跑实验** → 出图 → 写 LaTeX 论文 → 自评审 → 循环。约 **$15/篇** | 无视觉（读不了自己的图、修不了超大表格）；会误实现想法、做不公平基线；有时"比较不了两个数字的大小"；曾试图绕过限制（改自己的超时） | 本仓有**阶段级验收门 + 可归因双评审 + canonical 审计**（Sakana 的自评审是单模型、不可归因）；缺**端到端无人干预产出率** |
| **Google AI co-scientist** | 多 agent 出**假设 / 研究提案 / 实验方案**；Elo 自评 | **不写论文**；不独立验证输出；需专家在环（科学家设目标、喂种子想法、给反馈）；仅 Trusted Tester 可用 | 本仓把 co-scientist 不做的（manuscript / editorial / revision / submission 五件套）做成了结构事实；但**假设发掘的广度为零** |
| **FutureHouse PaperQA2** | 带句级引用的文献问答、contradiction detection（`contracrow`）；自述在部分指标超人 | **不写论文**；**不跑实验**；不写代码；公开版不含授权全文，需自备 PDF | 本仓检索链更窄（`retmax` 默认 3，协议自陈"不是文献综述"）；但本仓的证据链落 canonical、可跨 run 聚合 |
| **Edison Scientific Kosmos** | 长时程自主分析：读文献、分析数据、生成并**分支**假设、中途 steering；公开数据点：24 小时内 292 条独立分析轨迹；on-prem、SOC 2 | 页面**未公开任何局限性说明** | 本仓**没有任何长时程 / 分支探索语义**；`phase.strategy` 多阶段只变成"更多串行会话"（见 §3.2） |
| **Elicit** | 文献综述 / 系统综述筛查 / 数据抽取；最多 1000 篇 + 20000 数据点；句级引用 | **不跑实验**；**不写论文**；"设计实验"指规划支持 | 本仓有引用结构读数（分布 / 充分性）但**阈值全 `None`**、无真实语料标定 |

### 结论式判断

**本仓是唯一一个把「投稿仪式」做成结构事实的开源系统**：
`editorial` 相的四值闭集（`accept` / `minor_revision` / `major_revision` / `reject`）、
`revision` 相的逐条应答（`P1…Pn` + 三档严重性）、投稿包五件制品、期刊闭集。
市面没有任何一个对手做到这一步——它们全部在"写完论文"就停。

**但它在这三件事上系统性落后：**

1. **端到端产出率**：十一相链真实成功率 **11.1%**（4 succeeded / 36）。
2. **假设发散的广度**：没有"生成 N 个候选假设并筛"的语义。
3. **文献综述的深度**：`retmax` 默认 3、单一文献源族。

市面对手全部选择"**做深一节**"（Sakana = 实验+论文，Elicit = 综述，Kosmos = 长时程分析）；
本仓选择"**做全链路**"。这两条路没有对错，但全链路的代价就是上面三件都浅。

---

## 2. PRD 缺口：产品声明 vs 实际暴露

### 2.1 结构性缺口（声明了但不存在）

| 缺口 | 证据 | 性质 |
| --- | --- | --- |
| **投稿面不存在** | `docs/api/openapi.m13.json` 里 `submission` **零命中**；`services/api/routers/` **无** submission / journal 路由。"submission" 只是 run 内的 markdown 制品 | 声明 vs 暴露断裂 |
| **期刊是占位符** | `examples/config/journals.yaml:11-14` 三个条目、假 ISSN；文件自陈"不是评分、不是推荐、不是真实注册信息" | 刻意为之，但 PRD 未登记 |
| **旗舰链不可从 UI 到达** | `services/api/routers/protocol_drafts.py:47-66` 只暴露 **5 个模板**；十一相链**不在其中**。用户必须手打 `protocol_path`（只在 `ProgramsSection.tsx:196` 有 placeholder 提示） | 可达性缺口 |
| **报告生成 / 导出禁用** | `pageSupport.ts` 的 `insights/reports` = `partial`，`generate` / `edit` / `export-pdf` / `publish` 全禁用 | 有制品、无操作 |
| **无身份系统** | `services/api/middleware.py` 单共享 token；读面（GET/HEAD）**永不认证**；`Principal` 只有 `id` + `kind`，无租户 / RBAC / BOLA（`packages/domain/principal.py:5-9` 明写不表达授权语义） | M18 deferred，已登记 |
| **RBAC 配置是死件** | `examples/config/access_control.yaml` 定义了四个角色与 `agent_principals`；全仓 `packages/`·`services/`·`adapters/`·`tests/` **零 Python 消费者** | 声明 vs 暴露断裂（最典型的一处） |
| **无 exactly-once / 无多租户 / 不宣称安全** | `docs/architecture/WORKFLOW_RELIABILITY.md:162`、`docs/security/IDENTITY_AND_ACCESS.md:85,173`、`docs/audits/PA1_MIMOSA_REVIEW.md` | 已诚实登记 |

### 2.2 console 覆盖度（33 条规范路由）

来源：`apps/web/src/navigation/registry.ts` + `pageSupport.ts`。

| 等级 | 数量 |
| --- | --- |
| `full` | **14** |
| `partial` | **18** |
| `gap` | **1** |

**18 条 `partial` 混装两类完全不同的问题**，PRD 必须把它们拆开：

**(a) 真缺后端面**（有页面、无 API，产品确实做不了）：

| 页面 | 缺什么 |
| --- | --- |
| `library/prompts` | 版本树、A-B 测试 |
| `library/datasets` | 上传、字段 schema |
| `library/notebooks` | 单元格编辑、执行 |
| `insights/reports` | 生成、编辑、PDF、发布 |
| `portfolio/experiments` | 复现执行、日历/矩阵视图 |
| `ops/data-health` | 聚合质量报告 |
| `ops/integrations` | provider 凭据绑定、健康复核的 schema 漂移比对 |

**(b) 诚实边界**（功能在，但射程有限，页面如实标注）：

| 页面 | 边界原文 |
| --- | --- |
| `portfolio/projects` | "agents/memory/experiments 数据面仍单项目共享，租户隔离属 M18 deferred" |
| `run/timeline` | "无抢占式中断；跨进程暂停上下文不持久化" |
| `govern/budget` | "预测只覆盖已预留额度（未预留开销不外推）；运行中语义变更仍 501" |
| `insights/cost-analytics` | "不插值、UNKNOWN 不当 0、跨币种不给金额" |
| `library/lineage` | "数据集/提示词与 Run 的引用关系无记录面…不猜测连边" |
| `ops/schedules` | "不能新增执行路径（只能绑定既有 job 词表）、无删除/归档、无 cron 表达式" |
| `notifications` | "无实时推送，数量只来自当前页" |
| `settings` | "无账户/身份/Billing/平台 API Keys API" |

**唯一的 `gap`** 是 `ops/matrix`——"界面状态说明页（非实时运维状态）"，是**刻意的设计面**，
不是缺失功能。

### 2.3 后端面现状

`services/api/app.py:354-389` 挂载 **33 个 router**；`docs/api/openapi.m13.json`：
**108 paths / 133 operations**（68 GET · 45 POST · 9 PATCH · 3 PUT · 8 DELETE）。

**已在文档里明写缺席的 HTTP 面**（`docs/api/CONTROL_PLANE_API.md:554-569`）：
`GET /me`、organizations、memberships、project data-policy、project export、
project delete-request、`POST /runs/{id}/fork`、`POST /memory/proposals/{id}/decide`、
`POST /runs/{id}/stream` 或 WS。

---

## 3. 作为科研 agent 的不足（调研判断）

按「对科研有效性影响 × 修复可行性」排序。

### 3.1 假设发散为零（最严重）

`novelty` 相做的是：**对检索结果宣称新颖性**——输入是检索到的文献，输出是一段新颖性主张。
它**不是**"生成 N 个候选假设并机械筛选"。

co-scientist 与 Kosmos 的核心能力恰好是后者。本仓在**结构上不具备**：
- 无"候选假设集合"这个域概念；
- 无假设间的比较/排序面；
- `Decision` 只表达"采纳/不采纳"，不表达"在 N 个里选了哪个"。

### 3.2 无长时程 / 中途 steering

本仓的语义是"**一次 run 走完固定的相序列**"。没有：
- "跑 24 小时"的时间预算语义（`timeout_seconds` 是每相/每任务的，不是全局探索预算）；
- "中途分支"（`phase.strategy` 在产品侧**只有编译器一个消费者**；
  `real_research_task_v1.yaml:15-21` 明写"phase 数 = 会话数，多阶段只会变成更多串行会话，不是并行"）；
- "人可插入并改变方向"（`POST /runs/{id}/interventions` 对语义变更返回 **501**）。

Kosmos 的 292 条并行分析轨迹，在本仓**结构上无法表达**。

### 3.3 文献覆盖默认极浅（**但不是「无配置面」**）

**出厂默认 `retmax = 3`**（`services/api/retrieval_wiring.py:58` `DEFAULT_RETMAX = 3`）。
协议自陈："References 不是文献综述，因为一次 run 只有约 3 条检索命中"
（`direction_to_manuscript_v1.yaml:38-42`）。

**一处已过期的陈述（实测更正）**：那份协议注释写的是"`retmax` 硬编码为 3（**无配置面**）"——
**这是陈旧的**。GOAL-20261101-103 EC-05 之后 `retmax` 有**四级回落**：
显式参数 > **项目声明**（`ResourceCatalog.retmax`）> 环境变量 `RESEARCHOS_RETMAX` >
`DEFAULT_RETMAX`，上限 `MAX_RETMAX = 100`
（`retrieval_wiring.py:67-95`、`packages/application/ports/resource_catalog.py:39-48`）。
同样陈旧的还有 `research_report_chain_v1.yaml:29`、`grounded_report_chain_v1.yaml:40`、
`real_experiment_research_v1.yaml:24` 三处 `retmax=3` 的表述。**`adapters/research_tools/`
的 `SEARCH_RETMAX = 10` 是另一层**（工具自身缺省，被上面四级覆盖）。

⇒ 所以这里的差距**不是"缺机制"，而是"默认值太浅 + 注释未随机制更新"**。
市面 RAG 系统（Elicit：1000 篇；PaperQA2：本地全库）是 **2–3 个数量级**的差距，
而本仓把深度留在 `3`。

### 3.4 内容级判定仍是空白

`packages/application/deliverable/manuscript_quality.py:54-60` 的 `NOT_JUDGED` 五项：

```text
whether a citation supports the sentence it is attached to (only: not unrelated)
whether the argument holds (premises sufficient / inference valid / conclusion supported)
whether the method is appropriate for the question
whether the citation set is sufficient for each claim
writing style, readability, grammar
```

且引用充分性的**三个阈值全部是 `None`**（`citation_sufficiency.py:59-65`）——
理由是全仓零真实语料，取值是编造。

**但这是全行业共同短板**，不是本仓独有：Sakana 的自评审只能给"Weak Accept"、
co-scientist 明写"不独立验证输出"、Kosmos 连局限性说明都不给。
本仓的独特之处是**把"不判什么"写成了代码里的常量**，而对手把同一件事写成营销语言的免责声明。

### 3.5 无可复现的外部基线对照

实验只跟自己比（臂间同名指标求差），没有行业标准的 baseline 形态；
`AUTHORED`（模型写实验脚本）**出厂关闭**（`script_authority.py:49`
`AUTHORED_ALLOWED_BY_DEFAULT = False`）。

Sakana 至少跑过"自动评审给出的分数分布"这个外部信号；本仓的评审是内部闭环。

### 3.6 论文质量无外部信号

没有投稿命中率、没有与人类评审的一致性对照、没有期刊接收数据。
本仓有 editorial decision（四值闭集）但那是**模型自己的判定**，不是外部世界的反馈。

### 3.7 多语言 / 多学科空

角色与能力全部指向 CS / 生物医学：工具只有 `ncbi_eutils`、`ncbi_citation`、`europe_pmc`、
`m12_artifact`、`openhands_workspace`。没有化学（PubChem / RDKit）、物理（arXiv 全量）、
社科（SSRN / JSTOR）的工具面。

### 3.8 无法验证「原创」

`novelty` 判的是"与已检索文献不重复"，不是"真的新"。而检索覆盖只有 3 条记录 ⇒
"不重复"的判据面窄到接近空真。

---

## 4. 建议的优先级（供决策，本轮不执行）

按「可自动验收 × 对科研有效性影响」排序：

| 优先级 | 方向 | 理由 | 可自动验收？ |
| --- | --- | --- | --- |
| **①** | **复检可靠性**（本轮 GOAL-115） | 阶梯「复检」整格挂在它上面；24/24 FAILED 里有一半是真缺陷不是判负 | 是 |
| **②** | 文献深度（`retmax` **默认值**提高 + 多源） | 机制已在（四级回落，上限 100），缺的是**缺省取值**与多源工具面 | 是（配置 + 判据） |
| **③** | 假设发散（多假设生成 + 筛） | §3.1 是最严重缺口；需新域概念（`HypothesisSet`） | 部分（生成数量可判，"哪个更好"不可判） |
| **④** | 投稿面真实化 | §2.1 最大的声明/暴露断裂；但需产品决策（对接哪个系统） | 部分 |
| **⑤** | 身份 / RBAC | `access_control.yaml` 是死件；M18 整块 | 否（需产品决策） |

**不建议优先做的**：长时程 / 分支探索（§3.2）——它要求重写编排语义，
代价远大于收益，且 Kosmos 的优势来自其数据与算力而非架构。

---

## 5. 声称边界

- 本文档的外部对照基于**公开页面**，未做实测；对手的局限性是**它们自己承认的**，
  不排除有未承认的。
- 本文档**不宣称本项目安全**（`R-M1` 未收口）。
- 本文档**不宣称**上述任何缺口有已知最优解；§4 的排序是工程判断，不是研究结论。
- 数字来自仓库内实查（2026-11-18）：36 次 `direction_to_manuscript` run 中 4 次 SUCCEEDED；
  24 次 `dual_model_review` 全 FAILED 但**全部来自 2026-10-20 单一 47 分钟窗口**，
  换站后未重跑——见 GOAL-20261119-115 的建档取证。

### 5.1 模型接入的**数据保留事实**（必须与产品声明一起读）

当前零价模型目录里有一条**非 ZDR** 的接入：`iceman-contributor-free`（GOAL-20261119-115
的用户授权范围内可用）。它的 provider 口径是 **prompt 会用于改进模型** ⇒
**研究与手稿正文会进训练数据**。

本仓把它绑定在 `novelty_author`（`examples/config/models.yaml` 的
`novelty_author_model`）。这意味着**创新点声明的正文**（以及它读到的检索摘录）会离开
「不训练」边界。写作组、两位评审者与创新点评审落在另外三个模型上；其中
`hy4-flash-free` 的 provider 口径是 **0-day retention**（最干净）。

**这是一条产品事实，不是配置细节**：任何「稿件不出本机/不入训练」的对外声明都必须
先说明这一条。换模型时同样要重判（`tests/loaders/test_free_model_only_policy.py`
只判零价，**不**判 ZDR —— 后者没有机器可读的上游字段，只能靠这条记录）。

## 6. 来源

**仓库内**：`docs/PRODUCT.md`、`docs/roadmap/MILESTONES.md`、`docs/adr/ADR-0028`、
`docs/architecture/{SYSTEM_ARCHITECTURE,MANUSCRIPT_QUALITY,WORKFLOW_RELIABILITY}.md`、
`docs/security/IDENTITY_AND_ACCESS.md`、`docs/frontend/CONSOLE_PAGE_MAP.md`、
`docs/api/{CONTROL_PLANE_API.md,openapi.m13.json}`、
`apps/web/src/navigation/{registry,pageSupport}.ts`、
`packages/application/deliverable/{manuscript_quality,citation_sufficiency}.py`、
`examples/protocols/direction_to_manuscript_v1.yaml`、`examples/config/{journals,access_control}.yaml`。

**外部**：Sakana AI Scientist（`sakana.ai/ai-scientist`）、
Google Research AI co-scientist（`research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist`）、
FutureHouse PaperQA2（`github.com/Future-House/paper-qa`）、
Edison Scientific Kosmos（`edisonscientific.com`）、Elicit（`elicit.com`）。
