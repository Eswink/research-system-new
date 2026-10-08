---
id: PLAN-20261008-345
slug: goal-037-ec05-self-bootstrap-closeout
title: GOAL-037 cycle 5（EC-05）：自举收口 —— 验证器进树 + 两树复检 + 判词归档 + as-is m0 + 治理 + 台账
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-346-goal-037-ec05-self-bootstrap-closeout.md
memory_entries: []
parent_goal: GOAL-20261008-037
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-037 的 **EC-05**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不改**任何既有判据 / 门禁 / 阈值
    （`tools/` 两件新脚本是**新增**；`IN_SCOPE` **纯收紧**，只增不删）；判词行**不含**
    任何树的绝对路径（两树入口会拒绝）；**不读**两树写出的判词做一致性断言
    （输入即输出 ⇒ 永不收敛）；**不得**为让首轮变绿而删掉存在性断言（bootstrap 时序
    如实登记）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-037 收口成**可机械复核**的终态：① **验证器进树** ——
    `tools/verify_goal037_closeout.py` 复用 `tools/closeout_recheck_assertions.standard_verdicts`
    （**一行不重写**）+ 本轮断言集 `tools/goal037_closeout_assertions.py`，两者进 `IN_SCOPE`
    （**纯收紧**）；② **两树复检** —— `tools/two_tree_recheck.py --script-mode shared`
    对「当前树 + 干净 checkout」跑同一组断言并逐行比对；**判词归档进树**
    （`.cursor/plans/goals/evidence/`，二进制写盘、`CR=0`）；③ **as-is m0 23/23**
    （在全部记录写入之后，独占、仓库 `.venv`）；④ **治理 + 宪章判据**绿；⑤ **CI 台账
    逐提交**（含取消 / 真红的如实登记与自我指涉边界封闭）；⑥ 承继残余与未覆盖范围逐条；
    ⑦ **本轮残余 `O-1`…`O-5` 逐条定格**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树且复用标准断言集**：`tools/verify_goal037_closeout.py` 调用
      `standard_verdicts(root)`（公共面一行不重写），本轮特有断言收在
      `tools/goal037_closeout_assertions.py`（EC-01/02 骨架与编排 / EC-03 跨 run 知识 /
      EC-04 幂等与中断 / 判据面例数下界 / 归档形态 / 射程面）；`--verdict-only` 输出只有
      `PASS` / `FAIL` 两种前缀且**不含任何树的绝对路径**。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal037_closeout.py --root .
      --verdict-only` ⇒ 逐行判词；非判词行 0、路径行 0。
    status: PASS
  - id: AC-2
    criterion: >-
      **`IN_SCOPE` 纯收紧**：本轮两个新脚本（验证器 + 断言集）进
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的必备清单（只增不删），
      并过**四道门**（`ruff format --check` / `ruff check` / `mypy` / 规模 450·50）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **两树复检 + 归档进树**：`tools/two_tree_recheck.py --script-mode shared --base-ref
      <含交付面的提交>` ⇒ `TWO-TREE PASS`（两路判词逐行相同、`sha256` 相同）；判词归档
      `.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-{current,clean}.txt`
      **在树**、非空、`CR=0`；**bootstrap 时序如实登记**（归档由被归档的入口写出 ⇒
      首轮必红于「归档不存在」，次轮才全绿）。
    verify: >-
      入口两轮读数（首轮 / 次轮）+ 归档形态读数（字节数 / `CR=0` / 两份 `sha256`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23（在全部记录写入之后）**：`--profile m0 --keep-going`、独占、
      仓库 `.venv`、`uv run --frozen --no-sync python -B`、不接管道；终局行
      `PASS: profile=m0; 23 deterministic checks`；`PASS [` 24 / `FAILED [` 0。
    verify: >-
      m0 日志终局行 + `passed/skipped` 读数（收集数增量逐文件分解）。
    status: PASS
  - id: AC-5
    criterion: >-
      **治理 + 宪章判据**：`.cursor/skills/governance-check/scripts/validate.py` 绿；
      `tests/tooling/test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 在程序表序 5、
      进展记录行指向真实 RECHECK 文件）。
    verify: >-
      两条命令的终局输出。
    status: PASS
  - id: AC-6
    criterion: >-
      **承继残余与未覆盖逐条明写**：GOAL-036 的 `M-1`…`M-5` / `R26-*` 终态 /
      未覆盖范围（读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 / `R-M1` 未收口）
      逐条在位；本轮残余 `O-1`…`O-5` 逐条定格（已收口 / 未覆盖分界）。
    verify: >-
      验证器 `residuals-enumerated` / `prior-residuals-kept` /
      `uncovered-scope-enumerated` / `r26-*` 判词。
    status: PASS
  - id: AC-7
    criterion: >-
      **CI 台账逐提交**：逐提交登记 run/结论（`cancelled` 如实登记 + 原因 + `covered_by`）；
      空集合 / 空字段 = 未取证；**自我指涉边界**明写并以「末条已取证提交 + 仅记录改动」封闭，
      不得循环引用。
    verify: >-
      GOAL「CI 台账」节的逐提交行 + 边界行的封闭说明。
    status: PASS
---

# PLAN-20261008-345 — GOAL-037 cycle 5（EC-05）自举收口

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 验证器进树（复用标准断言集一行未重写；判词纯且与路径无关） | PASS |
| AC-2 | `IN_SCOPE` 纯收紧 + 两脚本过四道门 | PASS |
| AC-3 | 两树复检 `TWO-TREE PASS` + 判词归档进树（`CR=0`；bootstrap 时序如实登记） | PASS |
| AC-4 | as-is m0 23/23（在全部记录写入之后） | PASS |
| AC-5 | 治理 `validate.py` 绿 + MAINLINE 宪章判据绿 | PASS |
| AC-6 | 承继残余与未覆盖范围逐条在位（`M-1`…`M-5` + 本轮 `O-1`…`O-5`） | PASS |
| AC-7 | CI 台账逐提交（含自我指涉边界封闭） | PASS |

## 实施清单

- [x] `tools/verify_goal037_closeout.py`：入口（标准断言集 + 本轮断言 + 记录面）。
- [x] `tools/goal037_closeout_assertions.py`：本轮特有断言（骨架与编排 / 跨 run 知识 /
      幂等与中断 / 判据面例数下界 / 归档形态 / 射程面）。
- [x] `tests/tooling/test_tooling_scripts_meet_product_gates.py`：`IN_SCOPE` **纯收紧** +2 行。
- [x] `.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-{current,clean}.txt`：两树判词归档。
- [x] 记录面：本 PLAN、`RECHECK-20261008-346`、GOAL 收口面（EC 终态 + 导览表 +
      残余 `O-1`…`O-5` + 迭代日志 + 状态历史 + CI 台账）、MAINLINE 进展行、`ALL_PLAN`。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 验证器进树 | `tools/verify_goal037_closeout.py`（入口）、`tools/goal037_closeout_assertions.py`（本轮特有断言） |
| WP-2 | `IN_SCOPE` 纯收紧 | `tests/tooling/test_tooling_scripts_meet_product_gates.py`（+2 行，只增不删） |
| WP-3 | 两树 + 归档 | `tools/two_tree_recheck.py --script-mode shared`（首轮 bootstrap 红 / 次轮 `TWO-TREE PASS`）；`.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-{current,clean}.txt` |
| WP-4 | as-is m0 | `--profile m0 --keep-going`（在全部记录写入之后） |
| WP-5 | 治理 + 宪章 | `validate.py`；`tests/tooling/test_mainline_program_is_intact.py`；MAINLINE 进展记录追加一行 |
| WP-6 | 记录面 | 本 PLAN、`RECHECK-20261008-346`、GOAL 收口（EC-05 + 导览表 + 残余/未覆盖逐条 + 迭代日志 + 状态历史 + CI 台账） |

### 判据（本轮特有断言 → 每条都能被单变量按压判红）

| 轴 | 断言（摘要） | 落点 |
| --- | --- | --- |
| EC-01/02 | 域字段（`program_id` / `program_index`）/ `for_program` / 程序域与端口 / 迁移 `017` / 驱动（六判定可区分）/ 三路由 / 启动面接线（`program_id=inputs.program_id`）/ DTO | `packages/domain/{run,program}.py`、`packages/application/ports/program_store.py`、`adapters/postgres/migrations/017_*.sql`、`packages/application/run_orchestration/program_runner.py`、`services/api/routers/programs.py`、`services/api/run_execution.py` |
| EC-03 | 实现（`research_state_read` 定义）/ 能力映射 / provider handler / 会话绑定行（逐字）/ **两组合根**接线 / 目录声明 / `policy.yaml` 恰一条 allow / 镜像表 / 协议与合约 | `adapters/canonical/research_state_read.py`、`read_surface.py`、`read_provider.py`、`services/api/session_tool_support.py`、`pg_composition.py`、`examples/config/**`、`examples/protocols/cross_run_knowledge_v1.yaml` |
| EC-04 | 判据在树 + `at-least-once` / 崩溃窗口 `DEDUP` / 「恰好一次」的**否认**形态逐条在场 | `tests/e2e/test_program_idempotency_on_the_run_path.py` |
| 判据面 | 四份判据文件的例数**下界**（6 / 6 / 5 / 7）；四条**引用的**既有判据仍在树 | `tests/e2e/**`、`tests/application/run_orchestration/**`、`tests/architecture/**`、`tests/application/preflight/**` |
| 归档面 | 两份归档在树、非空、`CR=0`（**不读内容**做断言 —— 输入即输出） | `.cursor/plans/goals/evidence/**` |
| 射程面 | `IN_SCOPE` 含本轮两脚本且**仍钉住**入口与标准断言集 | `tests/tooling/test_tooling_scripts_meet_product_gates.py` |

### 门（实测读数）

| 门 | 读数 |
| --- | --- |
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `2 files already formatted`（`ruff format --check apps services packages adapters tests` ⇒ 全绿） |
| `mypy`（strict） | `Success: no issues found in 2 source files`（本项目面）；全仓 `1160 +` files 绿 |
| 规模（450 行 / 函数 50 行） | `tools/goal037_closeout_assertions.py` **278** 行 / `tools/verify_goal037_closeout.py` **202** 行（函数均在 50 行内，由判据参数化复核） |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **8 passed** |
| `tools/verify_goal037_closeout.py --root . --verdict-only` | 起草中间态 **75 PASS / 4 FAIL**（逐条：归档未生成 ×2、本轮两份记录未写 ×2）⇒ 记录落地后收口态 **79 判词 / 0 FAIL** |
| 两树复检 | 首轮 bootstrap 红（读数见 `RECHECK-20261008-346` 第 3 节）；次轮 **`TWO-TREE PASS`** |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`**（读数见 GOAL 迭代日志 cycle 5 行） |

## 无可复用事实

本 cycle 只新增 `tools/` 下的机械面（收口验证器 + 本轮断言集）与记录；
收口机器的可复用事实已由 `MEM-20261008-203`（判词归档由被归档的入口写出）与
`MEM-20261008-206`（收口断言的下界与标记形态取实测）承载，本 cycle 未产生新的可复用事实。

## 影响报告

- **Domain / API / schema 变化**：**零**（本轮只新增 `tools/` 下的机械面与记录）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（`IN_SCOPE` 纯收紧；既有判据一字不动）。
- **观测隐私**：无新出口。
- **上游版本影响**：无。
- **下一项任务**：收口后**立即开下一个 GOAL**（MAINLINE 程序表序 6 / replan）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | WP-1/WP-2 落地（两脚本进树 + `IN_SCOPE` 纯收紧 + 四道门绿）；中间态 75 PASS / 4 FAIL（逐条为记录未写，属预期时序）。 |
| 2026-10-08 | DONE | WP-3…WP-6 全部落地：两树次轮 `TWO-TREE PASS`、归档进树（`CR=0`）、治理 + 宪章判据绿、CI 台账逐提交。`RECHECK-20261008-346` 独立复检。 |
