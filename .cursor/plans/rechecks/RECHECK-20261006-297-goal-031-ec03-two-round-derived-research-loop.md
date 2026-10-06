---
id: RECHECK-20261006-297
slug: goal-031-ec03-two-round-derived-research-loop
title: 复检：GOAL-031 EC-03 —— 科研真成环（声明式派生 + 两轮链 + 两臂实测 + 两向反证）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-06
updated_at: 2026-10-06
plan_id: PLAN-20261006-297
reviewer: root-agent
parent_goal: GOAL-20261006-031
verify_paths:
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/e2e/test_research_loop_second_round_derived.py -q
    ⇒ 13 passed
  - >-
    uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters
    tests/architecture tests/loaders tests/contracts -q ⇒ 2125 passed / 73 skipped
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 EC-03 与 fix_policy；复检两路（判据面 + 定向回归面），
    另以 scratch 脚本**实跑**生成判词归档。**不改任何既有判据**（本轮 `git diff --numstat`
    对 `tests/` 既有文件为空 = 零改动，逐字可核）。
---

# RECHECK-20261006-297：EC-03 复检

## 检查结果

**PASS_WITH_WARNINGS**。EC-03 的六条判据（声明式派生 / 两臂可区分 / canonical 留痕 /
读面可读 / 两向反证 / 实跑终态）逐条实测通过，判词归档进树；两条警告 `W-EC03-1` /
`W-EC03-2` 如实登记（下述）。

## 结论

EC-03 的四条分支（(a) 声明式派生 / (b) 两臂实测且可区分 / (c) canonical 留痕与读面可读 / (d) 两向反证）**逐条实测通过**，判据 13 passed、定向回归 2125 passed / 73 skipped、`tests/tooling` 1323 passed；判词归档由 scratch 脚本**实跑**生成并二进制写盘（CR=0）。两条警告（`W-EC03-1` 判据初版构造缺陷自修 / `W-EC03-2` 相位过滤新机制只被本协议证明）如实登记；既有判据**零改动**（`git diff --numstat` 对 `tests/` 既有文件为空）。

## 复核路径（`verify_paths` 两路）

### 路径 1：判据面

```
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_research_loop_second_round_derived.py -q
⇒ 13 passed, 18 warnings
```

五个测试类逐条对上 EC-03 的分支：`TestTheDerivationIsDeclared`（(a) 声明）/
`TestTheFirstRoundTriggersTheSecond`（(b)① 触发臂 + (c) 读面）/
`TestWithoutAFIRSTRoundHitTheSecondIsSkippedNotFailed`（(b)② 不触发臂 + 两臂可区分）/
`TestTheJudgeItselfBites`（(d) 反证两向 + 受判面前提）。

### 路径 2：定向回归面

```
uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters \
  tests/architecture tests/loaders tests/contracts -q
⇒ 2125 passed, 73 skipped, 2 warnings
```

覆盖 `phase_capabilities` / `phase_runner` / `task_phase_helpers` / `outcomes` /
`read_provider` 的全部既有消费者（运行链、编排、canonical 读面、MCP 注册、欧 PMC 契约）。

### 补充门（本轮改动文件）

- `ruff check` / `ruff format --check`：全绿（首跑 5 条 line-too-long + 1 条未排序 import，
  逐条修掉后复跑全绿）。
- `mypy`：`Success: no issues found in 37 source files`。

## 判据面逐条取证（判词原文，逐字抄自归档）

归档：`.cursor/plans/goals/evidence/GOAL-20261006-031-ec03-two-arms-and-derivation.txt`
（由 `scratch/goal031-cycle3/gen_ec03_evidence.py` **实跑一次 run** 生成并二进制写盘）。

### (a) 触发臂

```
state=SUCCEEDED
http_endpoints=['esearch.fcgi', 'efetch.fcgi']
round1_tools=['evidence_read', 'literature_search']
round2_tools=['artifact_read', 'evidence_read', 'literature_read']
round1_search_ids=['39000001', '39000002']
round2_read_artifact=tool-result:…:literature_read:39000001+39000002:literature_read
round2_artifact_content_ids=['39000001', '39000002']
```

**派生链可追**：第二轮读取步的 operation key **逐字**含第一轮检索返回的两个 PMID；
`artifact.read` 的返回内容里 `content.ids` 与第一轮检索结果**逐字相等**（经读面读回，
不是内存传递）。

### (b) 不触发臂（同一协议、同一装配，只换检索响应为零命中）

```
state=SUCCEEDED
http_endpoints=['esearch.fcgi']          ← 读取步一次请求都没发
round2_tools=['artifact_read', 'evidence_read']   ← 无 literature_read 工具证据
skipped=[{"reasons": ["run-chain tool literature_read skipped: previous step carried no
  'content.ids' ids and this call declares requires_previous_ids=False"], "task_id": "…"}]
```

**两臂可区分**（同一读数上互斥）：`literature_read` 证据在场 / 不在场；
`skipped` 空 / 非空（理由逐字点名工具 `literature_read`、字段 `content.ids`、
触发形态 `requires_previous_ids=False`）。且**跳过不是失败**：两臂 run 都 `SUCCEEDED`。

### (d) 反证两向

```
① 派生规则改坏（ids_from_previous -> content.no_such_field）
   state=FAILED
   failures=["…previous step's result carries no 'content.no_such_field' …"]
② 读面抓手摘掉（artifact_from_previous -> no_such_artifact）
   state=FAILED
   failures=["…expected exactly one evidence artifact_id ending with 'no_such_artifact',
             found [] (candidates: […])"]
```

两条判词都**点名**（路径名 / 后缀名 + 候选列表）——不是「被拒」这类钝判词。

## 既有语义零改动的自证

- **既有判据零改动**：`git diff --numstat` 对 `tests/` 既有文件 **为空**
  （本轮新增两个文件，未改任何一个既有判据；`git status` 逐文件可核）。
- **既有四类取参语义不变**：三个新字段全部有缺省（`requires_previous_ids=True` /
  `phase_id=None` / `artifact_from_previous=None`），缺省路径与旧实现逐行相同
  （`test_run_chain_capabilities` 11 例、`test_literature_chain_run_offline`、
  `test_mcp_registration_and_refutations` 一字未改且全绿）。
- **`run.completed` 载荷**：无跳过 ⇒ 不带 `skipped` 键（既有载荷形状不变；
  `test_restart_recovery` / `test_vertical_slice_happy_path` 全绿）。
- **事件词表**：仍 38 条（本 EC **未新增事件类型**，`TestEventTypeInventory` 全绿）。
- **读面增列是纯追加**：`artifact_id` 与 HTTP 读面 DTO 的既有列同源；
  `tests/adapters/canonical` 两条既有读面判据未改且绿。

## 规模门（450 行硬上限）

| 文件 | 行数 | 处置 |
| --- | --- | --- |
| `phase_capabilities.py` | 461 → **441** | 判定逻辑拆出 `phase_capability_triggers.py`（151 行） |
| `phase_runner.py` | 449 → **402** | 两个 parking 路径拆出 `phase_pause.py`（95 行） |
| `tests/e2e/two_round_loop_support.py` | **373**（新） | 未越限 |
| `tests/e2e/test_research_loop_second_round_derived.py` | **319**（新） | 未越限 |

两处拆分都是**逐行搬运**（判定/事件/返回对象未改一个字符），既有判据全绿即证。

## 警告（如实登记，不掩盖）

- `W-EC03-1`｜**判据初版有构造缺陷（自己修）**：`TestTheDerivationIsDeclared::…no_if_then…`
  首版用裸 `in source` 扫全文，被**自己的 docstring 例子**（提到 `literature_search`）
  误伤 ⇒ 改为 AST 取**可执行代码**里的字符串常量（跳过 docstring）。修的是判据的**构造**，
  判据的**强度**（「应用层不得出现领域能力名」）未降。
- `W-EC03-2`｜**相位过滤是新机制，只被本协议证明**：`RunChainCall.phase_id` 的一般性只由
  本 EC 的两轮协议取证；第二个消费者出现时需复核（与 `W31-4` 同源，登记为一般性残余）。

## 残余与未覆盖（原样保留 + 本轮新增）

- 承继：`R-M1`（未宣称项目安全）/ `R26-1` / `R26-5` / `R26-7` / `R26-8` / `W27-*` /
  `W10-12` / `G24-5`；GOAL-019…030 的未覆盖范围**原样保留**。
- 本轮：`W31-1`（放行 ≠ 被用，3 条未放行能力未被 run 使用）/ `W31-2`（同步集是重新定基）/
  `W31-3`（`_PROVIDERS` 单行 tuple）/ `W31-4`（触发面新机制）/ `W-EC02-1/2/3`。
- 本 EC **不声称**：模型读懂了第一轮的结论（交付物契约只判产物存在与来源覆盖）；
  多轮迭代的收敛/上限（两轮是射程）。
