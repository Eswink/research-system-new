---
id: RECHECK-20261028-099
slug: goal-099-submission-shaped-manuscript
title: GOAL-099 复检 —— 投稿形状的手稿（IMRaD + 真参考文献 + 图表数据表）
status: COMPLETED
result: PASS
created_at: 2026-10-28
updated_at: 2026-10-28
plan_id: PLAN-20261028-099
parent_goal: GOAL-20261028-099
owners:
  - root-agent
verify_paths:
  - packages/application/deliverable/references.py
  - packages/application/deliverable/manuscript.py
  - packages/application/deliverable/research_report.py
  - packages/application/run_orchestration/manuscript_facts.py
  - packages/application/run_orchestration/manuscript_assembly.py
  - packages/application/run_orchestration/report_task.py
  - packages/application/run_orchestration/report_facts.py
  - packages/application/protocol_compile/cross_phase_inputs.py
  - packages/domain/tasks.py
  - services/api/report_support.py
  - services/api/executor_wiring.py
  - examples/contracts/task_contracts.yaml
  - examples/protocols/direction_to_manuscript_v1.yaml
  - examples/protocols/direction_to_report_v2.yaml
  - adapters/research_tools/europe_pmc_parsing.py
  - adapters/research_tools/parsing.py
  - tests/contracts/test_direction_to_manuscript_protocol.py
  - tests/application/test_manuscript_assembler.py
  - tests/application/test_manuscript_references.py
  - tests/application/test_manuscript_reference_order.py
  - tests/application/test_manuscript_assembly.py
  - tests/e2e/test_direction_to_manuscript_product_path.py
  - tests/e2e/direction_to_manuscript_support.py
  - .cursor/plans/goals/evidence/GOAL-20261028-099-two-tree-current.txt
  - .cursor/plans/goals/evidence/GOAL-20261028-099-two-tree-clean.txt
  - tools/verify_goal099_closeout.py
  - tools/goal099_closeout_assertions.py
memory_entries: []
---

# RECHECK-20261028-099 — GOAL-099

## 检查结果

**PASS**。六个 EC 逐条独立取证；EC-01…EC-04 由本轮新增的 96 条判据（收集数 38 + 24 + 22 + 5 + 7）
判，EC-05/EC-06 由收口验证器（**80 条判词**）与宪章四处判。逐条如下。

## 逐条核对

### EC-01 八相协议（38 例，`tests/contracts/test_direction_to_manuscript_protocol.py`）

- 直接读协议文档断言**八相字面顺序**（`question / retrieval / novelty / plan / experiment /
  review / manuscript / report`），不靠产品代码转述；
- `compile_protocol` 通过且**零 ERROR**（`validate_bundle.py` 看不见新协议 ⇒ 这一格只能
  自己判）；
- 手稿相是会话相：合约 `research_manuscript` 的 `report` 与 `experiment` 都是 `None`，
  phase 是 `single_agent` + `capability_execution: run_chain`；
- 三条跨相边解析成三元组，性质全部 `RETRIEVED`（由**产出方**声明推导 —— 这是既有
  `producer_trust_label` 的读数，不是本协议放宽了什么；测试里原来猜 GENERATED 的地方已改成
  断言真实读数并写明理由）；
- 九条边逐条在位；C-1：`experiment` / `report` 两相无 `inputs`；
- 既有四份协议的字面相集**一字未改**（`direction_to_question_v1` 两相 /
  `research_report_chain_v1` 四相 / `direction_to_report_v1` 六相 / `direction_to_report_v2`
  七相）；
- **两条真文件按压**：① 给 `research_manuscript` 加 `report: {}` ⇒ 编译产
  `CROSS_PHASE_INPUT_INVALID` 且 severity 为 ERROR、点名 `manuscript`；② 摘掉手稿相的
  `plan:research_plan` ⇒ 边集判据判红。两处都按 raw `sha256` 逐字节复原。

### EC-02 手稿结构与引用闭合（24 例，`tests/application/test_manuscript_assembler.py`）

- `Abstract` + 六个编号节按文档顺序出现，`References` 在最后；标题元组逐字钉住；
- 模型那块面**不含** `## References`（汇编器专写）；
- `[1][2]` ↔ 编号行 `1.` `2.` 逐条映射；越界 `[3]` 点名；孤儿第三条点名；
- **8 个键逐键参数化**：任一节写数字 ⇒ `ManuscriptError` 点名该节与该字符；
  引用标记里的数字**不**算违规；
- 散文（排除 `## ` 标题行与抬头）无数字，数据表有 `7990.0` / `178.5` 且带
  `| 类别 | 名称 | 值 | 来源 |`；表在 Results 与 Discussion 之间；
- 改 `year` ⇒ 引用行随之变；旧的 dict-repr 行不满足三条事实；
- 抬头记录叙述作者 / 返回名 / 汇编时状态；同一输入逐字节相同；空 `run_id` 名字点名拒绝；
  文末如实登记两块面与缺失类别。

### EC-03 真参考文献（22 例 = 20 `test_manuscript_references.py` + 2 `test_manuscript_reference_order.py`）

- 完整记录渲染出作者 / 年 / 刊名；**两种作者形态各自渲染**（NCBI 列表 / Europe PMC 整串），
  同一 payload 里并存时两条都有作者；
- 超长作者列表**可见地**截断（前 N + `et al`）；
- 缺 `authors` ⇒ `39284801: missing authors`，**不**出现 `Unknown` / `N/A` / `n.d.` /
  `Anonymous` / `TBD`；缺 `journal` 同理；同时缺两个 ⇒ 两个都点名；
- 无标识记录进 `skipped`；`ids[]` 形态不产出条目也不报缺失；非 `tool:` 来源不算；
  空表仍写 `## References`；
- 改制品 `year` / `journal` ⇒ 引用行随之变（表真读字节）；
- **编号顺序 = 提示词里去重后首次出现顺序**（两条证据：search 两条记录 + read 同样的两条
  + 一条新的 ⇒ 三条编号，`[1]` 是列表里先出现的那条）；`[4]` 越界被拒；
- **两条真文件按压**：① 删掉 `authorString` 分支 ⇒ 整串形态作者静默变空且进 `problems`；
  ② 插一行填 `("Unknown",)` ⇒ 渲染里出现占位符词（结构判据因此必须独立于「缺失计数」——
  那一格是本轮**最有价值**的按压，见下「按压假绿的教训」）。

### EC-04 产品入口（7 例 e2e + 5 例同一 run 字节）

- `tests/e2e/test_direction_to_manuscript_product_path.py`：`TestClient(create_app(deps))` →
  `POST /projects/example-project/runs` → `SUCCEEDED`；八件产物齐（含
  `manuscript_narrative` 与 `manuscript.md`）；经既有读面取回 `manuscript.md` 字节并判
  IMRaD 顺序、真 Vancouver 行（`Hoffmann C` / `Nat Commun` / `2024`，无 `{`、无占位符）、
  正文无数字、数据表带来源列与指标行、`created_by = model_assisted:*`；
- 关掉开关 ⇒ `manuscript.md` **不在**库里、报告照出；两次 run 的报告在**内容面**相同
  （四节标题 / 指标名集合 / 读数多重集 / 判词）；
- `tests/application/test_manuscript_assembly.py` 在**同一个 run id** 上判：开 / 关两臂的
  `research_report.md` **字面逐字节相同**；没有正文制品时（出厂七份协议的形态）开了开关
  也**不产**手稿；正文写数字 ⇒ 任务 `FAILED` 且手稿不落库。

### EC-05 / EC-06

由 `tools/verify_goal099_closeout.py`（**82 条判词，0 FAIL**；两树复检那次为 **80** 条 ——
两份判词归档文件是那之后才加进「引用了就必须在树」那条判据的）与宪章四处判。
四条**真文件按压**由 `tests/tooling/test_goal099_closeout_verifier_goes_red.py` 判
（摘本 GOAL 的 id / 把 `下一级` 冒认成「已判」/ 给手稿合约加 `report: {}` / 基线全绿）。

### 收口两树（GOAL 第九节停止条件 1）

`tools/two_tree_recheck.py --script tools/verify_goal099_closeout.py --root . --script-mode shared`
⇒ **`TWO-TREE PASS`**（该次读数：**80** 条判词/棵）：两棵各 **80** 条判词、`sha256` **相同**
`44332689c5bd693a2af7c21ba4a24ed2c338771ee9f325901c47bae2a65f6adb`、`exit=0`。
判词归档进树（`evidence/GOAL-20261028-099-two-tree-{current,clean}.txt`，各 3265 字节，
`cmp` **逐字节一致**）。

## 按压假绿的教训（本轮最该记住的一条）

`test_filling_a_placeholder_would_turn_the_absence_judge_red` **第一次写时失败了** ——
不是产品缺陷，是**判据自己沉默**：把 `fields["authors"] = fields["authors"] or ("Unknown",)`
插进 `_entry_of` 之后，`missing` 变成空元组 ⇒ 「点名缺失」那条判据与它要防的动作**改的是
同一个量**。这正是 `fix_policy.forbidden` 点名的「补造缺失的作者 / 年份」。

⇒ 处置：判据改成**结构面**（渲染输出里不得出现占位符词表），并保留按压证明它在违规形态下
**真的红**。两件事都留了判据，缺一个就会在下一轮静默回归。

同类问题本轮还抓到两处（都不是产品缺陷，是我自己的判据错）：
`assert result.plan is None` 是**假判据**（`compile_protocol` 只在 DAG 阻塞时返回 `None`，
跨相 ERROR 随计划携带）；产品入口跨两次 run **不可能**逐字节相同（uuid + 随机臂序）⇒
拆成「产品入口判内容面 / 同一 run 判字面字节」。

## 非回归证据

- 既有报告判据：`tests/application/test_report_task_narrator_behaviour.py`、
  `test_report_narrative_on_the_product_path.py`、`test_research_report_assembler.py`、
  `test_report_narrative.py` 合计 **41 passed**（手稿开关缺省 False，五处既有
  `report_task_runner(...)` 调用点全部不传 ⇒ 逐字沿用旧语义）；
- 既有四份协议的相集判据一字未改且仍绿。

## 结论

**PASS**。六个 EC 全达成：EC-01…EC-04 由 96 条判据（收集数 38 + 24 + 22 + 5 + 7）
判，EC-05 由收口验证器 **80 条判词** 与 4 例真文件按压判，EC-06 由宪章四处与
`ALL_PLAN` 判。**残余照实登记、不追认为达成**（`W-1`…`W-5`：编号化提示词未做、检索摘录
重复项、多臂行序由 uuid 决定、`retmax=3`、叙述质量无判据）。

## 未覆盖 / 残余

见 GOAL 的 `## 残余与未覆盖范围`：`W-1`（编号化提示词未做）、`W-2`（检索摘录重复项）、
`W-3`（多臂行序由 uuid 决定 —— 既有性质）、`W-4`（`retmax=3`）、`W-5`（叙述质量无判据）、
`U-1`/`U-2`/`U-3`、`R-1`/`R-2`/`R-3`。
