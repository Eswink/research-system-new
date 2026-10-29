---
id: RECHECK-20261029-100
slug: goal-100-submission-ready-and-citation-binding
title: GOAL-100 复检 —— 能投出去的稿：引用编号钉死 + 投稿决策面 + 返修底座 + retmax 可配
status: COMPLETED
result: PASS
created_at: 2026-10-29
updated_at: 2026-10-29
plan_id: PLAN-20261029-100
parent_goal: GOAL-20261029-100
owners:
  - root-agent
verify_paths:
  - packages/application/deliverable/references.py
  - packages/application/run_orchestration/retrieval_prompt.py
  - packages/application/run_orchestration/retrieval_context.py
  - packages/application/run_orchestration/session_prompts.py
  - packages/application/run_orchestration/task_executor.py
  - packages/application/run_orchestration/phase_runner.py
  - packages/application/run_orchestration/review_points.py
  - packages/application/run_orchestration/manuscript_assembly.py
  - packages/application/deliverable/editorial_decision.py
  - packages/application/deliverable/author_response.py
  - packages/application/ports/agent_runtime.py
  - packages/domain/enums.py
  - services/api/retrieval_wiring.py
  - adapters/openhands/session_builder.py
  - examples/config/agents.yaml
  - examples/config/models.yaml
  - examples/config/roles.yaml
  - examples/config/team_templates.yaml
  - examples/contracts/task_contracts.yaml
  - examples/protocols/direction_to_manuscript_v1.yaml
  - tests/application/test_citation_numbers_reach_the_prompt.py
  - tests/application/test_editorial_decision.py
  - tests/application/test_author_response.py
  - tests/application/test_retrieval_prompt_renderer.py
  - tests/application/test_retrieval_context_read_face.py
  - tests/application/test_retrieval_context_seam.py
  - tests/api/test_retmax_is_configurable.py
  - tests/contracts/test_direction_to_manuscript_protocol.py
  - tests/e2e/test_direction_to_manuscript_product_path.py
  - tests/e2e/direction_to_manuscript_support.py
  - tests/e2e/retrieval_context_support.py
  - tools/verify_goal100_closeout.py
  - tools/goal100_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261029-100 — GOAL-100

## 检查结果

**PASS**。六个 EC 逐条独立取证；EC-01…EC-04 由本轮新增的 **64 条判据**（8 + 19 + 26 + 11）
与 **9 条产品入口用例**判，EC-05/EC-06 由收口验证器与宪章四处判。逐条如下。

## 逐条核对

### EC-01 引用编号注入（8 例，`tests/application/test_citation_numbers_reach_the_prompt.py`）

- **三向判据**：① 正向 —— 提示词里每条**可引用**来源带 `[n]`，且 `n` 与
  `## References` 的序号**逐条相等**（两侧**各自**算一遍：汇编器读制品字节、渲染器读视图）；
  ② 反证「编造编号」—— 正文写 `[4]`（条目只有 3 条）⇒ `ManuscriptError` 点名称
  `[4]`；③ 反证「改回裸标识」—— 读**真文件** `retrieval_prompt.py`，把注入那一条语句
  还原成 `prefix = ""`、写进临时模块执行 ⇒ 提示词里**一条编号都没有** ⇒「提示词—References
  编号一致」判据**必须**红（证明它在看注入，而不是在看汇编器自己的编号）。
- **同源**：编号规则只有一处 —— `references.numbered_records`（去重后首次出现顺序、从 1 起）；
  汇编器与渲染器**都调它**（`test_the_shared_numbering_rule_is_one_function` 钉住行为）。
- **不可引用条目不占编号**：`ids[]` 形状（esearch 命中列表，无著录字段）标 `[not citable]`
  且**不占**编号 —— 占号会让其后每一条**整体错位**，而模型仍照提示词逐条引用的话，
  `[2]` 会指到另一篇文献上去。读面载荷补 `citable` 一列（否则读者重建不出那一行）。
- **真文件按压的读数**：`sha256` 复原前先确认判据真的红了 —— 6 条红
  （含 `test_every_citable_source_carries_its_reference_number`、`..._map_agrees_...`、
  `..._duplicate_record_...`、`..._id_only_record_...`、`..._removing_the_injection_...`
  与读面重建那条）；复原后 14 条全绿。

### EC-02 投稿决策面（19 例，`tests/application/test_editorial_decision.py`）

- **四值各可判**（`accept` / `minor_revision` / `major_revision` / `reject` 逐个参数化）；
  `accept` **允许**空改动清单，其余三值 `requires_changes` 为真；
- **反证：越界值点名拒绝** —— 九种形态逐个判红（`ACCEPT` / `Accept` / `accepted` /
  `minor revisions` / `minorrevision` / `revise` / `PASS` / `major` / 空串），判词列出四值；
  底层的 `EditorialDecision.parse` **自己**就拒（不靠解析器包一层）；
- **反证：要求返修却不说要改什么** —— 空列表 / 缺键 / 列表里混一条空串 / 非列表各判红；
  理由为空也判红；
- **面不混用**：`EditorialDecision` 与 `QualityGateVerdict` 取值**不重叠**，且既有门词
  逐字未动（`PASS` / `REVISE` / `BLOCK` / `PASS_WITH_WARNINGS`）；
- **两种输入形态都认**：信封（`declared_artifact` + 正文里的围栏 JSON 块，与产品路径上的
  真实字节同形）与直形态（受控夹具）。

### EC-03 返修底座（26 例，`tests/application/test_author_response.py`）

- **点表**：审稿人写成的那句话本身（`ReviewOrder` 的 `weakest_link` 与 `findings[]`）→
  `ReviewerRemark` → `ReviewPoint`（`P1…Pn` + 三档严重性）；`FAIL` 判词 ⇒ `must_fix`、
  其余 ⇒ `should_fix`（**机械映射**，只看行首那个词）；同一份产物两次派生（含记录顺序颠倒）
  ⇒ 逐条相同；两位评审者各自的点**都**编号（不合并）。
- **三条反证**：① **漏答**（有两点只答一点）⇒ 点名 `P2`；② **编造 `point_id`**
  （答 `P9`）⇒ 点名并列出真实点表；③ **删一条应答** ⇒ 判据**必须**红（证明它在逐条数，
  不是只看非空）。另判重复应答、空回应正文、无 id 的条目各点名。
- **应答信**：逐条 `### P<n> (<severity>)` + `> <原意见>` + `**Response.**` +
  `**Action taken.**`；漏答时**拒绝渲染**（不产出「看起来像应答信」的残件）；无评审点时
  写一句显式说明。
- **无迁移**：点表由**已落库制品**派生，`review_findings` 表**一列未加**
  （`rg -n "point_id" adapters/` 零命中）。

### EC-04 `retmax` 可配（11 例，`tests/api/test_retmax_is_configurable.py`）

- **默认逐字段不变**：`DEFAULT_RETMAX == 3`；不传参、不设环境变量 ⇒
  `fixed_arguments == {"retmax": 3}`（与改动前的字面量相同）；空 / 空白环境值回落默认；
  read 那条调用**不受影响**（`fixed_arguments == {}`、`ids_from_previous == "ids"`）。
- **改配置 ⇒ 参数变**：显式 `retmax=10` 与 `RESEARCHOS_RETMAX=12` 各一条；显式值优先于
  环境变量。
- **反证：非法值点名拒绝**：`abc` / `3.5` / `-1` / `0` / 超上界 / `1e3` 逐个判红，
  判词含变量名；显式值 0 / 负 / 超界同样判红。
- **真假文件按压**：把 `DEFAULT_RETMAX` 改成 5 ⇒ 2 条判据红；`sha256` 逐字节复原。

### EC-05 收口资产

- `tools/verify_goal100_closeout.py`（302 行）+ `tools/goal100_closeout_assertions.py`
  （263 行）在树；登记进 `_VERIFIERS` 与 `IN_SCOPE`；自指判据
  `self-loads-its-own-assertions` 通过（按**本文件名**推应载断言集）。
- 判词：产品面 **44 PASS / 0 FAIL**（引用编号 3 + 编辑决定 6 + 应答底座 6 + `retmax` 1 +
  用例条数 5 + 标准断言集与记录面）；记录写完后的终态读数见 GOAL 的 CI 台账。

### EC-06 宪章记账

- 程序表 **序 68** 在位（能力域 `报告`）；阶梯「报告」行 `依据 GOAL` 收录本 GOAL，`当前级`
  追加「投稿决策 + 逐条应答（可判的流程面）」与「引用编号随行给到模型」；
  `下一级` **逐字保持**「叙述质量与事实一致性可判」（本轮**没做**，不声称已判）。
- `进展记录` 追加 1 行并插在**最上面** ⇒ 3 行；`修订记录` 追加 1 行、**5 格**、插在表格
  全部数据行之后 ⇒ 3 行；子 PLAN 登记进 `ALL_PLAN.md` **表格顶部**。
- **policy allow 未扩容**：新两相只声明已放行的读能力 ⇒ `POLICY_SURFACE_AUDIT.md` /
  `_CAPABILITY_SCOPE` / 预期登记集**本轮零改动**（用户预授权的扩容本轮**没用到**）。

## 修掉的五处**实现**缺陷（判据全绿而产品是坏的）

| # | 形态 | 判据为什么没抓到 | 修法 |
| --- | --- | --- | --- |
| 1 | `editorial` 相只声明三条能力 ⇒ 另三件的 provider 排不出会话工具面 | `compile_protocol` 零 ERROR；只在**真实 run** 建会话时点名 `ToolDefinition 'europe_pmc' is not registered` | 六条能力全声明（与 `manuscript` 同一手法） |
| 2 | `review:review_decision` 作跨相 `inputs` 恒 `ambiguous` | 编译期只看「该产物在产出方的 `outputs` 里」，不看「产出方有几个任务」；`review` 是评审面板（两个任务） | 评审点经**提示词那一段**（`REVIEW POINTS`）送 |
| 3 | `wants_review_points` 读 `task.contract`（`ResearchTask` 只有 `contract_id`） | `getattr` 返回 `None` ⇒ **静默 `False`** ⇒ 点表从未进提示词；模型照「P1」回一条，汇编器随后点名漏答 | 按**在场字段** `contract_id` 判断 |
| 4 | 已渲染的字符串被当点对象再渲染一次 ⇒ 19 行 `-  (): ` | 单测直接喂点对象（不走 `compose_prompt` 那条缝） | `str` 短路（与 `_section_of` 同一条缝） |
| 5 | 应答信只 `put` 不 `register` ⇒ 读面看不到 | 进程内 `artifacts.get(...)` 能读到；`GET /runs/{id}/artifacts` 走 claim→relation 投影 | `_register_response_letter`（与手稿 `_register` 同形） |

## 与既有判据的关系（改了什么、为什么）

| 文件 | 改动 | 理由 |
| --- | --- | --- |
| `tests/application/test_retrieval_prompt_renderer.py` | 一行字面量：`- {identifier}: {shown}` → `- [1] {identifier}: {shown}` | 那一行**是契约**（EC-01 改了提示词形态）；判据的语义（渲染器不放大）逐字未变 |
| `tests/application/test_retrieval_context_seam.py` | 载荷多一列 `citable` | 读面载荷补列（否则重建不出 `[n]`）；判定逻辑逐字未变 |
| `tests/application/test_retrieval_context_read_face.py` | 重建那一行时**独立重算**编号 | 判据**变强**了（原来只比 `identifier`，现在还要编号对） |
| `tests/e2e/retrieval_context_support.py` | `prompt_lines_for` 独立重算编号 | 同上（不 import 渲染器当预言机） |
| `tests/contracts/test_direction_to_manuscript_protocol.py` | 相集 8→10、边集 9→11、用例改名 `..._eight_...` → `..._ten_...` | 协议**真的**加了两个相；判据的受判面仍是「文档自己的相表」 |
| `tests/e2e/direction_to_manuscript_support.py` | 相集 / 产物名 / 两个新会话格的受控回复 | 同上 |

**没有放宽任何判据**：上述每一处要么是「契约真的变了」（提示词形态、相集），要么是
「判据变强」（独立重算编号）。`retmax` 那一条连字面量都没改（`{"retmax": 3}` 仍是判据里的
断言值）。

## 残余与未覆盖（与 GOAL 正文一致）

`W-1`（`retmax` 只有环境变量这一层）/ `W-2`（检索摘录仍会出现重复行，只是编号相同）/
`W-3`（多臂指标行序由 uuid 决定）/ `W-4`（应答信的 `action_taken` 不判内容）/
`U-1`（创新是否真新未判）/ `U-2`（**叙述质量与事实一致性仍无判据**）/ `U-3`（policy allow
零改动）/ `R-1`…`R-4`（安全未收口 / 非恰好一次 / 混合归属 / 编辑能力面扩三条）。

## 结论

六个 EC 全达成，`result: PASS`。两树复检见 GOAL 的 CI 台账（本文件不重复登记读数）。
