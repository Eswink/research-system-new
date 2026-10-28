---
id: PLAN-20261028-099
slug: goal-099-submission-shaped-manuscript
title: GOAL-099 子计划 —— 投稿形状的手稿（IMRaD + 真参考文献 + 图表数据表）
status: DONE
created_at: 2026-10-28
updated_at: 2026-10-28
parent_goal: GOAL-20261028-099
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261028-099-goal-099-submission-shaped-manuscript.md
memory_entries: []
---

# PLAN-20261028-099

## 背景与靶子

序 66 收口时的产物是**研究报告**：四节中文、确定性汇编、来源渲染成 Python 的 `dict`
字面量。本轮把它推到**投稿形状**。

### 靶子 1：英文 IMRaD 手稿（本轮核心）

**取证（本轮建档 `rg -n` 读数，不重新推导）**：

- `packages/application/deliverable/research_report.py:26-31` 的四条节标题是中文
  （`## 1. 问题与动机` … `## 4. 评审与结论`）；
- `manuscript` / `introduction` / `methods` / `discussion` / `conclusion` 作**章节**在
  `packages/`、`services/`、`adapters/` **全部零命中**；
- 来源渲染成 `f"- {dict(item)}"`（`research_report.py` 的 `_bullet_list`）⇒
  `- {'identifier': '39000001', 'evidence_id': 'ev-1', 'title': '…'}`。

### 靶子 2：真参考文献表（元数据早已取到却从未被用）

- Europe PMC 解析 `pmid/doi/title/journal/year/authorString`
  （`adapters/research_tools/europe_pmc_parsing.py:20-27`）；
- NCBI 解析 `pmid/title/abstract/journal/year/authors`（`adapters/research_tools/parsing.py:59-91`）；
- 整份 tool-result JSON 已落盘，但 `.get("journal")` / `.get("year")` / `.get("authors")`
  在应用层**零命中**，`SourceRecord.authors` 恒空。

**先量后定策略（本 WP 的第一步就是这个读数）**：扫 `data/artifact-blobs` 里 17 份含
`articles[]` 的 tool-result 制品 ⇒ **10 条 distinct 记录**，其中
`authors[]` 列表形态 **6** 条、`authorString` 整串形态 **4** 条、两种都为空的 **0** 条；
`journal` / `year` / `title` 缺失 **0/30**。⇒ 两种形态都必须处理（只处理一种会在另一种上
静默丢作者），而缺失路径仍要**点名**（0% 是这份样本的读数，不是上游服务的保证）。
取证：`.cursor/plans/goals/evidence/GOAL-20261028-099-ec03-metadata-census.txt`。

### 靶子 3：把模型叙述真的接进产品（本轮按 EC-04 落地）

`services/api/executor_wiring.py` 的 `report_task_for` 此前不传手稿开关 ⇒ 从产品入口起的
run 只产报告。本轮把「同时汇出手稿」做成**显式装配参数**（缺省开），并在执行体里以
「本 run 有没有 `manuscript_narrative` 制品」为**唯一**判据决定产不产 —— 出厂七份协议都
不产该制品 ⇒ 对它们零影响。

## 核心设计取舍（先设计再动手）

| 问题 | 取舍 | 理由 |
| --- | --- | --- |
| 手稿相由谁执行 | **会话相**（合约不声明 `report:`） | `protocol_compile/cross_phase_inputs.py` 的 `_executor_consumes_declared_inputs` 对 `report`/`experiment` 执行体一律返回 False ⇒ 那样的相写 `inputs:` 会在**编译期**被拒。而 Related Work 要读检索产物、Methods 要读立题产物 ⇒ 必须是会话相 |
| 模型能不能写数字 | **不能**（引用标记除外） | 数字必须可核。正文写任何 Unicode 十进制数位 ⇒ `ManuscriptError` 点名拒绝，**不静默抽掉**（静默改写会让「这段是谁说的」不可判 —— 承 `report_narrative.py` 的既有机制） |
| 数字写在哪 | 汇编器的**图表数据表**（Results 之下）+ References 的年份 | 每行带来源列、值逐字取自 `ReportInputs`（四个既有读面）；References 逐字取自落盘字节 |
| 谁写 References | **只有汇编器** | 模型只写 `[1]`…`[n]`；编号↔条目映射由装配期决定 |
| 编号怎么定 | 检索摘录列表里**去重后的首次出现位置** | 检索链两步（search + read）会重复列出同一批记录，而 References 去重 ⇒ 按裸位置数会让模型写出的编号越界（本 WP 实测到的真缝，记 `W-2`） |
| 手稿在哪个相装配 | **report 相**（确定性） | 装配需要 `reviews` 与 `run` 两个执行期事实，它们只在报告相的装配面在场 |
| `created_by` 写什么 | `model_assisted:<agent>` | 正文是模型写的、数字与 References 是汇编器写的。两个方向都不能冒充（`fix_policy` 明令） |

## 工作包

- **WP-1 读面与渲染**：`packages/application/deliverable/references.py`（Vancouver + 两形态
  作者 + 缺失点名）、`manuscript.py`（八键 + IMRaD 标题 + 数字禁令 + 引用双向闭合）。
- **WP-2 装配**：`run_orchestration/manuscript_facts.py`（复用 `report_inputs` ⇒ 与报告同源）、
  `manuscript_assembly.py`（正文制品 + canonical 事实 → `manuscript.md` + 证据/claim）。
- **WP-3 声明面**：`examples/contracts/task_contracts.yaml` 的 `research_manuscript`
  （**不声明** `report:` / `experiment:`）+ `examples/protocols/direction_to_manuscript_v1.yaml`
  （八相，v2 七相 + `manuscript`；**不改 v2**）。
- **WP-4 装配开关**：`ReportTaskDeps.manuscript` / `report_task_runner(manuscript=…)` /
  `executor_wiring.report_task_for(manuscript=True)`（缺省开，但只在有正文制品时产出）。
- **WP-5 判据**：编译面 38 例、结构面 24 例、参考文献 22 例（20 + 2 编号顺序）、产品入口 7 例、
  同一 run 字面逐字节 5 例、收口验证器按压 4 例。
- **WP-6 收口**：`tools/verify_goal099_closeout.py` + `goal099_closeout_assertions.py` + 登记
  `_VERIFIERS` / `IN_SCOPE`；本 PLAN / GOAL / RECHECK 与宪章四处记账。

## 验收条件

1. `tests/contracts/test_direction_to_manuscript_protocol.py` 全过（收集 38 例），且两条按压臂
   在**真文件**上真的判红、按 raw `sha256` 逐字节复原；
2. `tests/application/test_manuscript_assembler.py` 全过（收集 24 例）：IMRaD 八节、引用双向
   闭合、8 个键逐键的数字禁令；
3. `tests/application/test_manuscript_references.py` + `test_manuscript_reference_order.py`
   全过（收集 22 例）：两种作者形态、缺失点名、占位符不出现、改 `year`/`journal` 表随之变；
4. `tests/application/test_manuscript_assembly.py` 全过（5 例）：**同一 run** 开/关手稿的
   `research_report.md` **字面逐字节相同**；正文写数字 ⇒ 任务 FAILED 且手稿不落库；
5. `tests/e2e/test_direction_to_manuscript_product_path.py` 全过（7 例，`requires_docker`）：
   经 `TestClient(create_app(deps))` 产出 `manuscript.md`，关掉开关 ⇒ 只有报告；
6. `tests/tooling/test_goal099_closeout_verifier_goes_red.py` 全过（4 例）：三条真文件按压
   证明收口验证器**会红**；
7. `tools/verify_goal099_closeout.py --root . --verdict-only` **零 FAIL**（80 条判词）；
8. 宪章：程序表序 67、阶梯「报告」行收录本 GOAL 并写明「手稿层 ≠ 报告层」、进展与修订
   各一行（修订 **5 格**、进展插在最上面）、`ALL_PLAN` 顶部登记子 PLAN；
9. `ruff check` 与 `ruff format --check` 对全部改动文件全绿；`mypy` 全量通过；
   `validate_bundle.py` 验证通过；`credential_audit.py` 四面 `offenders=0`；
10. m0 终态行 `PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、
    `tree changed during the run: False`。

## 实施清单

- [x] WP-1 `deliverable/references.py`（Vancouver + 两种作者形态 + 缺失点名 + 编号顺序）
- [x] WP-1 `deliverable/manuscript.py`（八键 / 七条 IMRaD 标题 / 数字禁令 / 引用双向闭合）
- [x] WP-2 `run_orchestration/manuscript_facts.py`（复用 `report_inputs` ⇒ 与报告同源）
- [x] WP-2 `run_orchestration/manuscript_assembly.py`（正文制品 + 事实 → `manuscript.md` + 证据）
- [x] WP-3 `examples/contracts/task_contracts.yaml` 的 `research_manuscript`（不声明 `report:`）
- [x] WP-3 `examples/protocols/direction_to_manuscript_v1.yaml`（八相；v2 一字未改）
- [x] WP-4 装配开关三跳：`ReportTaskDeps.manuscript` → `report_task_runner` → `report_task_for`
- [x] WP-5 判据五个文件（编译 38 / 结构 24 / 参考文献 22 / 同一 run 5 / 产品入口 7）
- [x] WP-6 `verify_goal099_closeout.py` + `goal099_closeout_assertions.py` + `_VERIFIERS` /
      `IN_SCOPE` 登记 + 按压判据 4 例
- [x] WP-6 宪章四处记账 + `ALL_PLAN` + GOAL / PLAN / RECHECK / 两份取证

## 证据

| 项 | 文件 / 命令 | 读数 |
| --- | --- | --- |
| EC-01 编译面 | `tests/contracts/test_direction_to_manuscript_protocol.py` | 38 passed（含两条真文件按压） |
| EC-02 结构面 | `tests/application/test_manuscript_assembler.py` | 24 passed |
| EC-03 参考文献 | `test_manuscript_references.py` + `test_manuscript_reference_order.py` | 22 passed（含两条真文件按压） |
| EC-03 元数据普查 | `.cursor/plans/goals/evidence/GOAL-20261028-099-ec03-metadata-census.txt` | 10 条 distinct 记录：`authors[]` 6 条 / `authorString` 4 条 / 缺失 0；`journal`/`year`/`title` 缺失 0/30 |
| EC-04 同一 run 字节 | `tests/application/test_manuscript_assembly.py` | 5 passed（字面逐字节相同） |
| EC-04 产品入口 | `tests/e2e/test_direction_to_manuscript_product_path.py` | 7 passed（`requires_docker`：真容器实验） |
| EC-04 取证 | `.cursor/plans/goals/evidence/GOAL-20261028-099-ec04-product-path.txt` | 八件产物齐、真 Vancouver 行、正文无数字、开关关掉不产手稿 |
| EC-05 收口资产 | `tools/verify_goal099_closeout.py` | **80 条判词，0 FAIL** |
| EC-05 按压 | `tests/tooling/test_goal099_closeout_verifier_goes_red.py` | 4 passed（三条按压真的翻红） |
| 零回归 | `tests/application/test_report_task_narrator_behaviour.py` 等四份 | 41 passed（开关缺省关） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-28 | IN_PROGRESS | 建档 + WP-1…WP-6 落地；EC-01…EC-04 判据全绿 |
| 2026-10-28 | **DONE** | 收口账合上：EC-05 验证器 80 条判词零 FAIL + 4 例按压；EC-06 宪章四处与 `ALL_PLAN`；六个 EC 全 PASS |

## 影响报告

- **Domain / API / schema**：`TaskContract` / `ReportAssemblySpec` / 任何 DTO **一字未动**；
  手稿开关是 `ReportTaskDeps` 的**装配面**字段（缺省关）+ `report_task_for` 的参数（缺省开）。
  无 OpenAPI 快照变更、无 `types.ts` 变更（没有新路由、没有新读面 DTO）。
- **安全 / 凭据**：无新增凭据面；`sk-` 仍只进 gitignored `.env` 的 `LLM_MAIN_KEY`；
  `credential_audit.py` 四面 `offenders=0`。手稿相**只用已放行能力**（`artifact.read` /
  `evidence.read` / `deliverable.read` / `literature.search` / `literature.read` /
  `workspace.read`），**未**改 `policy.yaml` / `POLICY_SURFACE_AUDIT.md` /
  `EXPECTED_REGISTERED` 那组镜像（无新能力名 ⇒ 差集判据零改动）。
- **兼容性 / 迁移**：五处既有 `report_task_runner(...)` 调用点全部不传 `manuscript` ⇒
  缺省 `False` ⇒ 逐字节沿用旧语义；出厂七份协议都不产 `manuscript_narrative` 制品 ⇒
  即使组合根开了开关也不产手稿。无迁移、无 schema 变更。
- **规模门**：`report_task.py` 一度 468 行 ⇒ 把「要不要装手稿 / 成功消息」移到
  `manuscript_assembly.py`（441 行）；`test_manuscript_references.py` 一度 515 行 ⇒ 编号顺序
  判据拆到 `test_manuscript_reference_order.py`；`_assets` / 写数字那条用例各拆一层。
  `tools/goal099_closeout_assertions.py` 一度 454 行 ⇒ 压缩注释与合并同义判据到 445 行。
- **上游版本**：无新增依赖；无版本 pin 变更；未引入绘图库 / pandoc / reportlab / weasyprint。

## 可复用事实

本轮沉淀的可复用事实已写进 RECHECK 的「按压假绿的教训」一节（**判据与被防的动作改同一个量
⇒ 判据自己沉默**；形态是「缺作者时填占位符让缺失计数变空」）。它是跨 GOAL 可复用的，
因此**不**声明「无可复用事实」；本轮未单独立 MEM 文件（GOAL 的 `memory_entries` 为空，
如实登记）。

## 残余

见 GOAL 的 `## 残余与未覆盖范围`（`W-1`…`W-5`、`U-1`…`U-3`、`R-1`…`R-3`）。本 PLAN 不重复。
