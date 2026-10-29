---
id: PLAN-20261029-100
slug: goal-100-submission-ready-and-citation-binding
title: GOAL-100 子计划 —— 能投出去的稿：引用编号钉死 + 投稿决策面 + 返修底座 + retmax 可配
status: DONE
created_at: 2026-10-29
updated_at: 2026-10-29
parent_goal: GOAL-20261029-100
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261029-100-goal-100-submission-ready-and-citation-binding.md
memory_entries:
  - .cursor/memory/entries/MEM-20261029-233-shared-seams-fail-silently.md
---

# PLAN-20261029-100

## 背景与靶子

序 67（GOAL-099）已产出「投稿形状」的手稿，但它有四处**结构缺口**，每一处都能用
`rg -n` 指到具体位置 —— 本轮逐条补上，并且每条都有**反证**。

### 靶子 1：引用编号没有进提示词（本轮性价比最高）

**取证**：`packages/application/run_orchestration/retrieval_prompt.py` 的
`render_retrieval_prompt` 逐条渲染 `f"- {identifier}{mark}: {shown}"` —— **裸标识**，
没有 `[1]`…`[n]`。而 `packages/application/deliverable/references.py` 的
`ReferenceTable.markdown()` 用 `enumerate(..., start=1)` 编号 ⇒ **编号规则只存在于汇编器
一侧**，模型必须自己数「这是第几条」，数错了**没有判据会红**（GOAL-099 `W-1`）。

**做法**：把编号规则提成**一个函数** `references.numbered_records(identifiers)`
（去重后首次出现顺序、从 1 起），汇编器与渲染器**都调它**；渲染器给每一行加 `[n]` 前缀。

**做的时候发现的第二处缺口**（本章程之外，但同一件事）：检索上下文也会收 `ids[]` 形状的
记录（esearch 的命中列表），而 `reference_table` 明确跳过它们（没有著录字段）⇒ 若给它们
编号，其后每一条都会**整体错位**。⇒ `RetrievalEntry.citable` + `[not citable]` 标注
（可见但不占号），读面载荷同时补这一列（否则读者重建不出那一行）。

### 靶子 2：投稿决策面（角色存在但从未被激活）

**取证**：`rg -l scientific_editor examples/protocols/` **零命中**；`roles.yaml:409` 里
该角色在（`review_panel_role: WRITER`）；`ACCEPT_WITH_REVISIONS` / `major` / `minor`
全仓零命中 ⇒ 决定词表只有验收门的 `PASS` / `REJECT`。

**做法**：`EditorialDecision` 四值进 `packages/domain/enums.py`；`editorial` 相 +
`editorial_decision` 契约；`agents.yaml` 绑定第五个不同底层模型（`qwen3.8-27b`，
实查可用）；`team_templates.yaml` 的 `standard` 池收录（不进池 = 编译期
`ROLE_CAPACITY` ERROR，实测消息在 GOAL 的迭代日志里）。

### 靶子 3：返修闭环的底座（最容易被做浅的一项）

**取证**：`rebuttal` 全仓零命中；`ReviewFinding.findings` 是扁平的判据渲染串
（`acceptance_observation.criterion_line` ⇒ `"{criterion_type}: {reason}"`）；审稿人的
`weakest_link` 只在 e2e 夹具里出现过，**产品代码从未解析它**。

**做法**：`author_response.py` —— `ReviewerRemark`（审稿人 + 原文 + 严重性）→
`ReviewPoint`（`P1…Pn`）→ `AuthorResponse`（`point_id` → `response` → `action_taken`）→
`validate_responses`（漏答 / 编造 / 重复三条各点名）→ `response_letter`（逐条成段）。
点表由**已落库的评审交付物**派生 ⇒ **不新增任何表 / 列 ⇒ 无迁移风险**（这是本轮选这条
路线的全部理由：动 `review_findings` 的列要 SQLite + PG 两侧 migration + 两侧序列化）。

### 靶子 4：`retmax` 可配（余量项）

**取证**：`services/api/retrieval_wiring.py` 的 `fixed_arguments={"retmax": 3}`。
**做法**：`DEFAULT_RETMAX = 3` + `RESEARCHOS_RETMAX` + `retrieval_calls(retmax=...)`；
默认逐字段不变；非法值点名拒绝（不静默回落）。

## 做的时候发现并修掉的五个**实现**缺陷

逐条记下来，因为每一个都是「判据全绿而产品是坏的」那一类：

1. **`editorial` 相只声明三条能力** ⇒ 另三条能力对应的 provider（`europe_pmc` /
   `ncbi_eutils` / `openhands_workspace`）**没有**进本相的 `tool_requirements` ⇒ 排不出
   会话工具面 ⇒ 真实 run 在建会话时点名失败
   （`ToolDefinition 'europe_pmc' is not registered`）。修法：六条能力全声明
   （与 `manuscript` 相同一手法）。**判据（`compile_protocol`）没抓到它** —— 它只在
   真实 run 上炸。
2. **`review:review_decision` 作跨相 `inputs` 恒 ambiguous**：`review` 相是评审面板
   （两个 `ResearchTask`），`cross_phase_inputs.producer_task_id` 按
   `{run_id}:{phase}:` 前缀命中两条 ⇒ 点名 `ambiguous` 失败。修法：评审点经**提示词那一段**
   （`REVIEW POINTS`）送到，不是跨相 `inputs`。
3. **`wants_review_points` 读了 `task.contract`**，而 `ResearchTask` 只有 `contract_id`
   （合约对象由调用方**另参**传入）⇒ `getattr` 拿到 `None` ⇒ **静默返回 `False`** ⇒ 点表
   从未进提示词，而表面上一切正常（模型回一条 `P1`，汇编器随后点名漏答）。
4. **已渲染的字符串被当点对象再渲染一次**：`session_prompts.review_points_prompt` 返回
   **文本**，`compose_prompt` 又把它交回 `prompt_with_review_points` ⇒ `tuple("<文本>")`
   按**字符**迭代 ⇒ 提示词里是 19 行 `-  (): `（与 MEM「已渲染的提示段被当视图再渲染」
   同一形态）。修法：`str` 短路（与 `_section_of` 同一条缝）。
5. **应答信只 `put` 不 `register`** ⇒ `GET /runs/{id}/artifacts` 看不到它（读面走
   claim→relation 投影）。修法：`_register_response_letter`（与手稿的 `_register` 同形）。

## 判据与按压

| 文件 | 条数 | 按压（按掉实现 ⇒ 必须红） |
| --- | --- | --- |
| `tests/application/test_citation_numbers_reach_the_prompt.py` | 8 | 把注入那一段从**真文件**还原成裸标识 ⇒ 6 条红（含「提示词—References 编号一致」）；逐字节复原后 14 条全绿 |
| `tests/application/test_editorial_decision.py` | 19 | 四值各判 + 越界（大小写 / 拼写 / 验收门词）各点红 + 非 accept 空改动点红 |
| `tests/application/test_author_response.py` | 26 | 漏答 / 编造 id / **删一条应答** 三条各点红 |
| `tests/api/test_retmax_is_configurable.py` | 11 | `DEFAULT_RETMAX` 改 5 ⇒ 2 条红；`sha256` 复原 |
| `tests/e2e/test_direction_to_manuscript_product_path.py` | 9 | 产品入口跑十相；编辑决定与应答信各一条专门用例 |

## 结果

`tools/verify_goal100_closeout.py --root . --verdict-only`：产品面 **44 PASS / 0 FAIL**；
记录面在写完记录后转绿（收口复检见 RECHECK）。

## 验收条件

| EC | 验收方式 | 判据文件 |
| --- | --- | --- |
| EC-01 | 提示词每条可引用来源带 `[n]`、与 References 序号逐条相等；编造编号点名；改回裸标识 ⇒ 判据红 | `tests/application/test_citation_numbers_reach_the_prompt.py`（8） |
| EC-02 | 四值各可判；越界值点名；非 accept 空改动点名；两个面取值不重叠 | `tests/application/test_editorial_decision.py`（19） |
| EC-03 | 点表稳定；漏答 / 编造 id / 删一条应答 三条各红；应答信逐条成段 | `tests/application/test_author_response.py`（26） |
| EC-04 | 默认逐字段不变；显式与环境变量两条通路都改参数；非法值点名 | `tests/api/test_retmax_is_configurable.py`（11） |
| EC-05 | 验证器 + 断言集在树、两处登记、判词零 FAIL（含自指） | `tools/verify_goal100_closeout.py` |
| EC-06 | 宪章四处 + ALL_PLAN（序 68 / 阶梯 / 进展 3 行 / 修订 5 格） | `tools/verify_goal100_closeout.py` 的记录面判词 |

## 实施清单

1. `references.numbered_records` —— 编号权威（唯一）。
2. `retrieval_prompt.render_retrieval_prompt` 注入 `[n]` + `[not citable]`。
3. `retrieval_context.RetrievalEntry.citable` + 载荷列 `citable`。
4. `enums.EditorialDecision`（四值 + `parse` + `requires_changes`）。
5. `deliverable/editorial_decision.py`（解析 / 校验 / 渲染）。
6. `agents.yaml` 绑定 `editor` + `models.yaml` 声明 `scientific_editor_model`。
7. `team_templates.yaml` 的 `standard` 池收录 `scientific_editor`。
8. `roles.yaml` 扩 `scientific_editor` 的三条只读能力。
9. `task_contracts.yaml` 加 `editorial_decision` 与 `author_response`。
10. `direction_to_manuscript_v1.yaml` 加 `editorial` 与 `revision` 两相。
11. `deliverable/author_response.py`（点表 / 应答 / 校验 / 应答信）。
12. `run_orchestration/review_points.py`（点表装配 + **唯一**派生点）。
13. `session_prompts.review_points_prompt` + `agent_runtime` / `task_executor` /
    `session_builder` / `compose_prompt` 的第六槽位（含 `str` 短路）。
14. `manuscript_assembly.maybe_assemble_response_letter` + `_register_response_letter`。
15. `retrieval_wiring`：`DEFAULT_RETMAX` / `RETMAX_ENV` / `configured_retmax` / `retmax=`。
16. `tools/verify_goal100_closeout.py` + `tools/goal100_closeout_assertions.py` + 两处登记。
17. 宪章四处 + `ALL_PLAN.md`。

## 证据

- `tests/application/test_citation_numbers_reach_the_prompt.py`（8 条；真文件按压：改回裸标识
  ⇒ 6 条红，`sha256` 复原后 14 条全绿）；
- `tests/application/test_editorial_decision.py`（19 条）；
- `tests/application/test_author_response.py`（26 条）；
- `tests/api/test_retmax_is_configurable.py`（11 条；`DEFAULT_RETMAX` 改 5 ⇒ 2 条红，`sha256` 复原）；
- `tests/e2e/test_direction_to_manuscript_product_path.py`（9 条，含编辑决定与应答信各一条）；
- `tools/verify_goal100_closeout.py --root . --verdict-only`：**64 PASS / 0 FAIL**；
- 套件：`tests/application + tests/contracts + tests/loaders + tests/domain` **2608 passed / 73 skipped**；
  `tests/api + tests/e2e manuscript` **737 passed / 4 skipped**；
  `tests/e2e manuscript + tests/application + tests/api` **2189 passed / 5 skipped**。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-29 | ACTIVE | 建档；四个靶子逐条勘察取证后按 EC-01…EC-04 落地。 |
| 2026-10-29 | DONE | 六个 EC 全达成；五个实现缺陷修复；判据 64 条 + 产品入口 9 条全过；收口验证器零 FAIL。 |

## 影响报告

- **Domain**：新增 `EditorialDecision`（`packages/domain/enums.py`）——**只加不改**，
  `QualityGateVerdict` 与 `TrustLabel` 逐字未动。
- **API / schema**：无新路由、无 OpenAPI 快照变化（新能力全部经既有读面与既有编排路径）。
- **契约 / 协议**：`task_contracts.yaml` 加两份契约；`direction_to_manuscript_v1.yaml`
  八相 → 十相（**既有相一字未改**，只追加）。受影响判据已逐条申报（见 RECHECK 的
  「与既有判据的关系」表）。
- **数据 / 迁移**：**零 migration**（点表与应答信都由已落库制品派生）。
- **安全 / 凭据**：`scientific_editor` 扩三条**只读**能力（`claim.read` / `evidence.read` /
  `artifact.read`，均已有 `allow`）；`forbidden_capabilities` 四条逐字未动；
  `policy.yaml` **零改动**；无新凭据、无新出网面。
- **兼容性**：`retmax` 默认逐字段不变；提示词形态变了两处（检索段加编号、第六槽位），
  受影响的既有判据已逐条申报并更新（不是放宽）。
- **上游版本**：无新增依赖、无 pin 变更。

## 可复用事实

- **「能力面漏声明 ⇒ 会话工具面漏 provider ⇒ 真实 run 才炸」**：`capability_execution:
  run_chain` 只排除**本相 `tool_requirements` 里**的 provider；少声明一条能力，它的
  provider 就排不出会话工具面，而 `compile_protocol` 零 ERROR。
- **评审面板相不能当跨相 `inputs` 的产出方**：`producer_task_id` 按
  `{run_id}:{phase}:` 前缀解析，面板有 N 个任务 ⇒ 恒 `ambiguous`。评审判词经提示词那一段送。
- **`ResearchTask` 只有 `contract_id`**（没有 `contract`）：按 `task.contract` 判断会
  `getattr` 到 `None` **静默失效**。
- **`compose_prompt` 收到的是已渲染的 `str`**：写新的一段时必须有 `str` 短路，否则
  `tuple("<文本>")` 按字符迭代（提示词里是 `-  (): ` 空行）。
- **`ArtifactStore.put` 不等于「读面可见」**：`GET /runs/{id}/artifacts` 走 claim→relation
  投影，只 `put` 不 `register` 的制品读不到。
- **收口断言集要与被引资产同步演进**：给协议加相之后，上一轮收口断言集的「相集清单」
  会判负 —— 那是资产坏了（被引代码演进了），不是产品缺陷；判准是「清单是否仍逐字描述
  当前协议」。

## 残余

`W-1`（`retmax` 只有环境变量层）/ `W-2`（检索摘录仍有重复行，编号相同）/ `W-3`（多臂
指标行序由 uuid 决定）/ `W-4`（应答信的 `action_taken` 不判内容）；`U-1`（创新是否真新）/
`U-2`（**叙述质量与事实一致性仍无判据**）/ `U-3`（policy allow 零改动）。逐条详述见
GOAL 正文的「残余与未覆盖范围」。
