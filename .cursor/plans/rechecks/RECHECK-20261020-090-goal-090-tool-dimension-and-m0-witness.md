---
id: RECHECK-20261020-090
slug: goal-090-tool-dimension-and-m0-witness
title: GOAL-090 复检 —— 覆盖门工具维（堵 W-6）+ m0 见证
status: COMPLETED
result: PASS
created_at: 2026-10-20
updated_at: 2026-10-20
plan_id: PLAN-20261020-090
parent_goal: GOAL-20261020-090
owners:
  - root-agent
verify_paths:
  - tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py
  - tests/tooling/test_m0_witness_matches_the_tree.py
  - tools/run_m0_with_witness.py
memory_entries: []
---

# RECHECK-20261020-090 — GOAL-090

## 检查结果

**PASS**。五条 EC 全部达成；两向按压在**真文件**上各判红并 raw `sha256` 逐字节复原；
受影响套件 **1270 passed / 72 skipped**（零回归）；m0 见证三态语义成立，正式见证由一次
真实全量运行产生，终态行 `PASS: profile=m0; 23 deterministic checks`。

## 一、既有判据改动逐条申报

基线 `0c641955`（本轮起点）。**判定口径**：删除行必须逐条给出「原谓词 → 新谓词 +
为什么不是放宽」；新增行一律是**收紧或显式登记**。

| 文件 | `numstat`（+/-） | 删除的谓词 / 行 | 现在的谓词 | 性质 |
| --- | --- | --- | --- | --- |
| `packages/domain/acceptance.py` | +38 / -12 | `_evaluate_evidence_coverage` 的返回分支（`if minimum_retrieved is None: return ...True...` + 末尾的三分句 return） | 三分支改为「累积 `parts` 再拼」；**既有两维的判词逐字保留**（有判据钉住：`test_without_the_declaration_the_behaviour_is_byte_identical` 断言 `reason == "2 >= 1 sources; 1 >= 1 retrieved"`） | **等价重构 + 收紧**（新增第三维；未声明时判词**逐字**不变，有专门判据） |
| `packages/application/run_orchestration/evaluation_gate.py` | +7 / -0 | —（纯新增） | `EvaluationInputs.tool_evidence_count` 槽 + `to_criterion_inputs()` 透传一行 | 纯新增（缺省 `None` ⇒ 未声明本维的合约不受影响） |
| `packages/application/run_orchestration/task_phase_helpers.py` | +5 / -0 | —（纯新增） | import + 一行 `tool_evidence_count=count_tool_evidences(...)` | 纯新增 |
| `packages/domain/tasks.py` | +19 / -0 | —（纯新增） | 可选字段 + `__post_init__` 负值拒绝 | 纯新增（缺省 `None`） |
| `adapters/contracts/tasks_loaders.py` | +1 / -0 | —（纯新增） | 解析 `minimum_tool_evidences` | 纯新增 |
| `schemas/task-contract.schema.json` | +1 / -0 | —（纯新增） | `"minimum_tool_evidences": {"type": "integer", "minimum": 0}` | 纯新增 |
| `examples/contracts/task_contracts.yaml` | +14 / -6 | `research_question_retrieval` 的 `version: 1.0.0` 与两维 purpose 段 | `version: 1.1.0`、三维 purpose、`minimum_tool_evidences: 1` | **收紧**（新增一维；既有通过面不放松） |

**零改动声明**：`count_retrieved_sources`（性质维口径）**一行未动** —— B 方案被否，
理由是它会挡掉「上游检索给下游用」的正当形态。`TrustLabel` 与
`producer_trust_label` **一行未动** —— 那是需用户拍板的 A 方案。

## 二、两向按压（真文件，二进制读写）

| 按压 | 改了什么 | 判据反应 | 复原 |
| --- | --- | --- | --- |
| (a) 合约摘维 | `examples/contracts/task_contracts.yaml` 删掉 `minimum_tool_evidences: 1` 一行 | `test_the_shipped_retrieval_contract_declares_the_dimension` **判红**，消息逐字点名「检索格没有声明工具维 ⇒ GOAL-089 的 W-6 在出厂检索格上仍然敞开」并打印该合约现文 | `sha256` 复原为 `997fe81695859df32309c9369f72dd162c4dbaf93b006e55db4c551743fbfd44`，复绿 **10 passed** |
| (b) 计数恒零 | `result_handler.py` 的 `return sum(1 for item in evidence if item.tool_refs)` → `return 0  # PRESS` | `test_tool_refs_is_the_discriminator_between_the_two_evidence_kinds` **判红**：`assert 0 == 1` | `sha256` 复原为 `4a7682d0db14e0d580a22ba87da17ca71e9a6098509881a4ccd6bd6e810f71e6`，复绿 **10 passed** |
| (c) 见证按压 | `schemas/task-contract.schema.json` 改一个标识符（受判面内的文件） | `test_the_witness_is_for_the_tree_we_are_looking_at` **判红**，逐条点名「当前有而见证没有（2 项）」与「见证有而当前没有（1 项）」，并打印该文件两版 `sha256` | `sha256` 复原为 `38341aeb80d54af40d761542f0a90e3dd5b7d79836f7ebf2c310edfc9b09a660` |

**按压 (c) 抓到两处自己造成的缺陷**（都被判据在当轮抓到，不是事后发现）：

1. **见证自我指涉（位置）**：见证文件本身落在受判面里 ⇒ 写见证会改变它所描述的树
   ⇒ `--skip-run` 写完立刻判红。修法 = `SELF_REFERENTIAL` 白名单。
2. **见证自我指涉（时刻）**：见证在门**跑完之后**才写，而判据**本身就在门里**跑 ⇒
   「本次运行里见证尚不存在」是**结构必然**，把这种情况判红会让「跑一次门」永远无法
   自证覆盖 —— 判据变成了它自己的反例。修法 = **第三态**：见证入口在 `subprocess.run`
   之前写 `M0-WITNESS.in-progress`、`finally` 里删；判据见标记在场 ⇒ `pytest.skip` 并
   点名理由（**可见的跳过，不是静默通过**）。并单列判据
   `test_the_in_progress_state_is_a_real_third_state_not_a_silent_pass` 钉住这一语义
   （含「标记必须在 `finally` 删除」与「两边路径逐字一致」两条反证）。

## 三、判据清单（新文件，逐条）

`tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py`（10）：

1. `test_a_cross_phase_only_source_passes_the_first_two_dimensions` —— **先钉住缺口存在**：
   只有跨相来源时前两维确实通过（这是 `W-6` 的形态，不是想象）；
2. `test_the_tool_dimension_rejects_a_cross_phase_only_source` —— **核心反证**：同样的
   来源集合加工具维 ⇒ 判负并点名「a cross-phase input is not a tool call」；
3. `test_one_real_tool_call_satisfies_the_tool_dimension` —— 只多一条调用事实即判过；
4. `test_without_the_declaration_the_behaviour_is_byte_identical` —— 未声明 ⇒ 判词**逐字**
   等于 `"2 >= 1 sources; 1 >= 1 retrieved"`（零回归的机械保证）；
5. `test_an_unknown_tool_count_is_named_not_ignored` —— fail-closed；
6. `test_a_negative_declaration_is_refused_at_construction` —— 域层拒绝；
7. `test_the_shipped_retrieval_contract_declares_the_dimension` —— 读**产品数据文件**；
8. `test_tool_refs_is_the_discriminator_between_the_two_evidence_kinds` —— 钉住判据赖以
   成立的**结构事实**（两类证据在 `tool_refs` 上可分）；将来跨相输入若开始带 `tool_refs`，
   本条判红提醒改写判别依据；
9. `test_a_multiple_tool_threshold_counts_each_call` —— 阈值 >1 按条数判，不折算成布尔；
10. `test_the_dimensions_are_independent_not_substitutes` —— 三维互不顶替，任一缺即判负。

`tests/tooling/test_m0_witness_matches_the_tree.py`（5）：

1. `test_the_witness_is_for_the_tree_we_are_looking_at` —— 核心；不等时**逐条点名**差异；
2. `test_the_witness_records_a_terminal_line` —— 「跑过」≠「跑完了」；
3. `test_the_witness_reports_red_honestly_instead_of_hiding_it` —— 红也照记；
4. `test_the_witness_tool_is_wired_to_the_canonical_runner` —— 入口不得自拼一套；
5. `test_the_witness_is_committed_not_scratch` —— 见证必须在树内被跟踪。

## 四、记录面与门（顺序按纪律执行）

```text
① 写全部记录（GOAL / PLAN / RECHECK / 阶梯 / 程序表 / 进展记录）
② 记录面判据
③ 最后：tools/run_m0_with_witness.py 跑全量 m0 并写正式见证
④ 之后不再改任何受判文件
```

**读数**：正式见证 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`；
`test_m0_witness_matches_the_tree.py` 5 passed（指纹相等）；
`test_evidence_coverage_tool_dimension.py` 10 passed；
受影响套件（`tests/application/run_orchestration/` + `tests/domain/` + `tests/contracts/`）
**1270 passed / 72 skipped**；凭据审计四面 `offenders=0`。

## 五、未覆盖范围（如实登记）

- **A 方案未做**：`producer_trust_label` 仍会把「声明了 `run_chain` 但本次未执行调用」的
  会话格推成 `RETRIEVED`。本轮工具维**只挡住声明了它的合约**（出厂检索格已声明），
  **不是**通用修复。通用修复需改 `TrustLabel` 语义 ⇒ 需用户拍板。
- **见证只覆盖本地树**：CI 覆盖推送后的树，两者对象不同。
- **见证不校验 23 项是否全部执行完**：那是终态行的职责。
- **无 live run**：本轮受判面是求值逻辑与本地门机制，均不触网；不声称任何模型行为。

## 结论

**PASS**。五条 EC 全部达成：工具维落地且三维正交（10 条判据）；两向按压在真文件上各判红
并 raw `sha256` 逐字节复原；出货检索格升版 1.1.0 并声明新维；m0 见证三态语义成立、自我指涉
边界经实测修掉。零回归 1270 passed / 72 skipped；宪章三判据 20 passed；凭据四面 `offenders=0`。

**如实登记的三条边界**：`A`（改 `TrustLabel`）未做，故工具维不是通用修复；见证只覆盖本地树；
无 live run（本轮受判面不触网）。

## 六、正式见证读数（最后一次全量 m0）

按顺序纪律执行：**全部记录写完 → 记录面判据 → 最后跑门 → 之后不再改树**。

| 项 | 读数 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks` |
| `PASS [` 行数 | **24**（含计数之外的 `release-assets-immutable`） |
| 失败项 | **0** |
| `green` | `True` |
| `exit_code` | `0` |
| `tree_changed_during_the_run` | `False`（跑门期间工作树静止，见证与运行同一棵树） |
| 见证落点 | `.cursor/plans/goals/evidence/M0-WITNESS.json`（**树内被跟踪**，CR=0） |
| 见证判据复跑 | **7 passed**（指纹相等 ⇒ 覆盖关系成立） |
| 指纹口径 | **按文件内容**（4526 个受判面文件 × sha256），**不含** git 脏状态 |

**运行条件**：`RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` / `RESEARCHOS_LIVE_LLM`
均未设置；`RESEARCHOS_POSTGRES_DSN` 与 `RESEARCHOS_POSTGRES_TEST_DSN` 置空；
以 `uv run --frozen --no-sync python -B tools/run_m0_with_witness.py` 运行。

**这一节本身是顺序纪律的产物**：见证绑定的是「跑门那一刻的树」，所以读数只能**在门之后**
写。GOAL-089 为此多跑了三次全量 m0；本轮把顺序当受判对象走，只跑一次得到正式见证，
并在门内以第三态（进行中标记）处理「见证尚未写」这个结构必然。

## 七、CI 判红如实登记（`effbe9e5`，已修）

`effbe9e5` 的 M0：`quality-ubuntu-latest` 与 `quality-windows-latest` **判红**，其余六 job
`success`。红点逐字：

```
Failed: m0 见证与当前树**不一致** ⇒ 最后一次全量 m0 覆盖的不是现在这棵树
  见证记录的 HEAD: 0c641955…；当前 HEAD: effbe9e5…
  见证有而当前没有（24 项）：[('.cursor/memory/INDEX.md', 'M', …), …]
```

**这是本轮的真缺陷，不是 flake**：第一版指纹记的是「脏文件清单」，本地有 24 个未提交改动、
CI 是干净检出 ⇒ **同一个提交在两处指纹永远不等**。本地 23/23 全绿**没能预测**它，因为
本地那次运行的指纹与本地工作树天然自洽。

**修法**：指纹改按**文件内容**算（4500+ 个受判面文件的 sha256），并单列判据禁止
`dirty` / `status` 回到指纹里。**这条记入「本地绿 ≠ CI 绿」的实例**：判据的正确性
必须在**两种工作树形态**（有未提交改动 / 干净检出）下都成立。
