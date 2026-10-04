---
id: RECHECK-20261005-282
slug: goal-029-ec05-self-bootstrap-closeout
title: GOAL-029 EC-04/EC-05 复检 — 两树判词归档留档 + 自举收口（验证器进树 + TWO-TREE PASS + m0 23/23）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-281
parent_goal: GOAL-20261004-029
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261005-281`（GOAL-20261004-029 的 cycle 4+5 子计划）—— EC-04（两树判词归档留档）
与 EC-05（自举收口）。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 两份判词归档在树（二进制写盘） | **PASS** | `.cursor/plans/goals/evidence/GOAL-20261004-029-verdict-{current,clean}.txt` 各 **2593 字节**、**54 行**、**CR count 0**、`sha256` **相同**（`db4faa07d42532d0dd4793a9d42b8392784ecfb761af07562e7915eb12b9a503`）；判据断言纯度（只有判词行前缀）与路径无关（无盘符）；落点不被 `.gitignore` 覆盖 |
| AC-2 | 两向反证 | **PASS** | 文本模式写一份 ⇒ **2 failed**（`sha256` 不同 + 含 CR，实测 18 个 CR）；二进制复原 ⇒ 绿。另固定两条实测事实：文本模式在 Windows 写 CRLF；`.gitattributes` 的 `* text=auto eol=lf` 会把差异在提交时**静默归一化** ⇒ `git diff` **不足**以充当逐字节证据（已断言 staged blob 仍为纯 LF） |
| AC-3 | 收口验证器进树 + 复用标准集 + 四道门 | **PASS** | `tools/verify_goal029_closeout.py`（**419 行** ≤450）**复用** `closeout_recheck_assertions.standard_verdicts`；只读工具集 `tools/closeout_recheck_tools.py`（118 行）按**路径**加载（`tools/` 不是包）；两者**双双进 `IN_SCOPE`**（纯收紧）；四道门 **8 passed** |
| AC-4 | 两树同结论 | **PASS** | `TREE current` 与 `TREE clean` 各 **54 判词**、`sha256` **相同**、`COMPARE identical=True`、**`TWO-TREE PASS`**（两树 exit=0）；两路判词二进制写盘到归档落点 |
| AC-5 | as-is m0 23/23（记录写入之后） | **PASS** | 见 GOAL「状态历史」的本轮终态行（`PASS: profile=m0; 23 deterministic checks`） |
| AC-6 | 治理与台账 | **PASS** | `validate.py` 绿；CI 台账逐提交（`cancelled` 如实登记 + 原因；`total_count=0` 记未取证 + 显式覆盖声明）；残余与未覆盖逐条 |

## 按压（两向）

| # | 按压形态 | 结果 | 复原 |
| --- | --- | --- | --- |
| P-1 | 把 `clean` 归档用**文本模式**重写（`write_text` 不带 `newline=""`） | **2 failed**：`test_the_two_archives_have_the_same_sha256` + `test_neither_archive_has_carriage_returns`（实测 18 个 CR） | 二进制复原 ⇒ CR=0、`sha256` 与 current 相同 ⇒ 13 passed |

## 复检发现（如实登记，未修）

- **`W-1`（本轮实测并修掉的自身缺陷，值得登记）**：EC-05 验证器起初**读**两树入口写回的判词归档
  做断言 ⇒ **输入即输出**：两棵树**先后**执行同一脚本，第一次执行时归档还是上一轮的内容
  ⇒ 两棵树读到**不同**的历史残留（实测首跑 current 判红 / clean 判绿），且**永不收敛**。
  **修法**：归档形态由 EC-04 的**专属判据**承担（跑在门禁里、在两树写入**之后**）；
  验证器只判 GOAL 自己的交付物。沉淀为 `MEM-20261005-186`。
- **`W-2`**：验证器**不**判 EC-04 归档（见 `W-1`）⇒ EC-05 的判词数是 **54**（若含归档断言会是 57）；
  归档由 EC-04 判据独立判（13 passed）。两者**互补不互相顶替**。
- **`W-3`**：两树第二棵是**已推送 HEAD** 的 checkout（承 GOAL-028 `W-3`）⇒ **必须先提交再跑**；
  本轮实测：首跑 RED（干净树不含未提交的验证器）⇒ 提交推送后 **TWO-TREE PASS**。
  这也是两树入口**有效性**的正控制。
- **`W-4`**：`IN_SCOPE` 的读取起初只认 `ast.Assign`，而该常量是 **`AnnAssign`（带类型标注）**
  ⇒ 恒定读到空元组 ⇒ 判据**假红**（文件其实在表里，实测「表内 12 条」）。改用
  `Assign`/`AnnAssign` 都认的读取器后转绿 —— 与 `MEM-20261005-185`（判据射程要按压）同族。
- **`W-5`**：本文件（RECHECK）与 GOAL 的迭代日志/状态历史里的 `sha256` 是**本轮那次运行**的读数；
  两树入口每次运行都会**重写**归档（内容随树的状态变化）⇒ 引用时必须写明是哪一次
  （本轮的 `db4faa07…` 对应 `dcd8387` 提交后的那次运行）。
- **`W-8`**：EC-02 主判据的受判面被写成 `declared & implemented` ⇒ 掩蔽（已修，详见下节）。
- **`W-7`**：CI 首跑判红（**只在 Linux 暴露**）：文本模式行尾转换是平台相关的，
  判据按平台分档断言（详见下节）。
- **`W-6`**：收口验证器只覆盖本轮交付物与标准面，**不**覆盖产品运行语义（承 GOAL-023 的有界射程）；
  前四轮的 `W-NN` 族**原样保留**。

## 复检补充：CI 首跑判红（已修，**只在 Linux 暴露**的判据缺陷）

`656ae37` 的 M0 首跑 `quality-ubuntu-latest` 判红：
`tests/tooling/test_two_tree_verdicts_are_archived.py::test_text_mode_and_binary_mode_differ`
报 `文本模式必须与二进制模式产生不同 sha256` —— **本地 Windows 全绿**。

**根因**：`Path.write_text` 的行尾转换是**平台相关**的 —— Windows 把 `
` 写成 `
`，
**Linux / macOS 不转换**（`newline=None` 时 `
` → `os.linesep` = `
`）。
我那条断言把 Windows 行为写成了跨平台事实 ⇒ Linux 上假红。

**修法（不放宽，只是各自说各自平台的事实）**：
- **跨平台硬断言** `test_the_entry_style_is_lf_only`：入口那种写法（`newline=""`）
  必须产出纯 LF —— 归档纪律的载体，两平台都成立；
- **平台事实** `test_text_mode_hazard_matches_this_platform`：按 `os.name` 分档断言。

**这条与 `W-4` 同族**（判据射程要按压/要按真实条件说事实），登记为 **`W-7`**：
本判据原先把「本机平台的行为」当成「普适行为」—— 与「只扫 `ast.Name`」同类的
**射程错配**（对象没变，是断言覆盖的条件集错了）。

## 复检补充：**完成核对**抓到 EC-02 主判据的掩蔽缺陷（已修，`c15614f`）

复检后做**完成核对**（逐条把 objective 的要求映到证据）时，读 EC-02 主判据源码发现：
受判面被写成 `declared & implemented` ⇒ 「**声明了但没实现**」**在构造上不可能被报出来**
（交集天然排除缺实现者）。判据/门禁/m0 **全绿**都没抓到它 —— 因为它绿得"对"。

**修好后立刻报出三条真实缺口**：

| 能力 | 审计结论 | 处置 |
| --- | --- | --- |
| `claim.read` | 声明了但**没有实现** | **本轮补真实现**（读 canonical ledger 的 claim + evidence relation，与 `evidence_read` 共用 run 归属口径）+ 接进出厂绑定表 + 3 条判据 |
| `experiment.read` | 同上 | **从出厂声明面移除**（保留声明而无承接面 = GOAL-028 `W-1` 的原形）；登记理由 + 列为下一批候选 |
| `experiment_plan.read` | 同上 | 同 `experiment.read` |

**记录修正（不掩盖）**：本轮先前报的「承接面 **17/46**」**含两条假计数** ⇒ 修正为
**15/46**；A 组读能力实承接 **6 条**。GOAL 的迭代日志与状态历史已同步改正并写明修正理由。

**登记为 `W-8`**：判据绿 ≠ 判据覆盖了对的东西。本条的教训是
「写『A ⇒ B』型判据时受判面取 A（声明的全集），不要取 `A ∩ B`」——
与 `MEM-20260922-160`（不得靠**并集**掩蔽）是镜像形态（这里是**交集**把本该受判的排出去）。
沉淀为 `MEM-20261005-187`。

## 复检补充（完成核验纠偏）：**A 组承接补足到 5/5**（`9206ca8`）

完成核验指出 EC-01 的原文硬门槛「A 组的 **≥5 条**读能力接成会话工具」未满足（当时只 3 条），
且我把 `experiment.read` / `experiment_plan.read` 判为「需 ExperimentStore 进入 provider 依赖面
⇒ 下一批候选」。**该判断偏保守且已纠正**：`ExperimentStore` **本就在两个组合根的 Port 面上**
（SQLite 根 `_SqliteStoreParts` / PG 根 `c["experiment_store"]`）⇒ 接进去是**装配改动**，
不是新依赖、也不是新能力面。

**本轮补上（A 组 5/5）**：

| A 组读能力 | 实现 | 来源 |
| --- | --- | --- |
| `claim.read` | `CanonicalReadProvider._claim_read` | `EvidenceLedger`（claim + relation） |
| `deliverable.read` | `CanonicalReadProvider._deliverable_read` | `ArtifactStore`（`{run_id}:deliverable.json`） |
| `budget.read` | `CanonicalReadProvider._budget_read` | `BudgetLedger.snapshot()` |
| `experiment_plan.read` | `CanonicalReadProvider._experiment_plan_read` | **`ExperimentStore.list_plans`**（与 `GET /experiment-plans` 同一方法） |
| `experiment.read` | `CanonicalReadProvider._experiment_read` | **`ExperimentStore.get_run`** + 证据侧 `experiment_run_id`（与 `GET /runs/{id}/experiments` 同源两步） |

**接线**：绑定表 + `canonical_read_register` / `session_tool_face` 接收 `experiment_store`；
**两个组合根**各自传自己的 Port 实例（同一实例贯穿编排与工具面，避免两套状态）。
**声明面同轮**：`tool_providers.yaml` 重新声明这两条（**这次有实现**）+ 审计文档同轮更新。
**判据**：新增 4 条；EC-02 射程内清单 6 → **8 条**（下界同步）。
**按压**：删掉实现映射 ⇒ **3 failed**（主判据 + 下界 + 工具面）。

**如实读数：承接面 12/46 → 17/46（每条都真有实现）；A 组 5/5。**

## 下一批可真实现的能力清单（§七 要求，逐条）

按「零新增依赖 / 零凭据 / 有 canonical 或既有 Port 来源」的标准，从当前未承接的 29 条里筛：

| 能力 | 组 | 可实现的依据 | 阻力 |
| --- | --- | --- | --- |
| `citation.validate` | B | `ncbi_eutils` 已有 `citation.inspect`（elink），validate 是其**判定层**（同一响应上加判定语义） | 需先定义「何为验证通过」的判据（属产品口径） |
| `run.read` | B | run 的真相在 `RunStore`（既有 Port），读面今天只在 HTTP 层 | 需决定会话工具返回的 run 视图形状 |
| `dataset.read` | B | 需先有 canonical **数据集实体**（今天没有） | **先建实体**，非本轮射程 |
| `provenance.read` | B | 证据链投影已有（`evidence.read` 就是它的一半） | 需区分与 `evidence.read` 的口径 |
| `research_map.read` / `research_state.read` | B | 需先有对应实体 | **先建实体** |
| `review.read` | B | 评审走 task/handoff 面 | 需决定投影口径 |
| `target.read` | B | 需先有目标实体 | **先建实体** |
| `agent_run.read` | A（无实体） | 域里没有 `AgentRun`（最近的是 task + agent_id） | **先建实体**，否则无对象可读 |
| 各 `*.write`（`deliverable.write` / `experiment_plan.write` / `audit.write` / `idea.*` / `review.write`） | C | 有 canonical 路径（`persist_completion` / `save_plan`） | **写面**：给写能力开工具面需**用户拍板**（策略面判「该拒绝」） |
| `external.publish` / `package.install` / `git.commit` / `workspace.delete` | D | `policy.yaml` 现为 `require_approval` | **接通审批通道需拍板** |
| `network.public` | D | `policy.yaml` 显式 deny | 维持现状 |

**最短路径（B 组）**：`citation.validate`（复用既有 elink 响应 + 定义判定口径）与 `run.read`
（`RunStore` 已在 Port 面上，与 `experiment_store` 同一形态）—— 两者都不需要新依赖，
只差**声明 + 实现 + 放行口径**。

## 结论

`PLAN-20261005-281` 的 **AC-1…AC-6 全 PASS**；
`result = PASS_WITH_WARNINGS`（六条 `W-NN` 如实登记，其中 `W-1`/`W-4` 是本轮实测并修掉的
自身缺陷、`W-3` 是自举时序、`W-2`/`W-5`/`W-6` 是射程与引用边界）。

**GOAL-029 的五个 EC 全 PASS** ⇒ 满足 `ACHIEVED` 的前置条件。

**明确否认**：**不**宣称项目安全（`R-M1` 未收口）；**不**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
