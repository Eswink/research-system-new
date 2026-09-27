---
id: PLAN-20260928-217
slug: goal-022-ec04-closeout-two-tree-self-bootstrap
title: GOAL-022 cycle 4（EC-04）：自举收口复检 —— 用 EC-01 的入口跑本轮自己的两树复检 + 残余与未覆盖范围逐条登记
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-022
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-022 的 **EC-04**（收口复检 + 残余登记，**自举**：必须用 EC-01 建好的
    入口做本轮自己的收口复检）。授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为
    「**复检过程机械化 + 判据固化 + 环境口径固化**」三件事 + **文档同源更新**；
    **不加新能力、不放宽任何判据、不改安全策略**；push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）；默认 runtime 保持 **Fake**、
    默认 CI **离线**。
    **本 PLAN 专属边界**：**不得**放宽任何既有判据 / 门禁 / 阈值 / 放行面；
    **不得**新增依赖；**不得**把 token 写进任何地方；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**为了「让收口好看」而改动任何受保护判据或历史记录。
exit_criteria:
  - id: AC-1
    criterion: 用 `tools/two_tree_recheck.py`（EC-01 交付的入口，**在树**）对当前树与干净 checkout 跑本轮收口复检脚本，两树**逐行判词相同**且 `sha256` 相同
    status: PASS
  - id: AC-2
    criterion: >-
      as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`，且运行**在记录写入之后**
      （承 MEM-145：写记录 → 记录面判据 → 全量门）
    status: PASS
  - id: AC-3
    criterion: 治理 `validate.py` 绿（含 `DOCS-CHECK`）
    status: PASS
  - id: AC-4
    criterion: CI 台账到终态（M0 八 job + CodeQL，含 `run_attempt`）
    status: PASS
  - id: AC-5
    criterion: 承继残余逐条在位（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`）
    status: PASS
  - id: AC-6
    criterion: 未覆盖范围逐条明写（读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口）
    status: PASS
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-218-goal-022-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-156-empty-subject-set-means-the-judge-is-not-yet-in-force.md
---

# PLAN-20260928-217 — GOAL-022 cycle 4（EC-04）：自举收口复检

**主题**：本轮**不是**再补一份手工复检，而是**验证 EC-01 的入口真的能被用起来**——
用它跑 GOAL-022 自己的收口复检，并对 EC-02 判据的 `W-1`
（「受判集合为空 ⇒ 判据今天没有真实执法对象」）做**实证**：
本轮的收口复检记录就是那条**第一条真实受判记录**。

**不新增任何树内文件**：收口复检探针与留档全在 `scratch/`（gitignored），
**零产品代码改动**、**零既有判据改动**、**零新依赖**。

## 验收条件

| # | 验收条件 | 结果 |
| --- | --- | --- |
| AC-1 | 用 **EC-01 交付的入口**（`tools/two_tree_recheck.py`，**在树**）对**当前树**与**干净 checkout** 跑本轮收口复检脚本 ⇒ 两树**逐行判词相同** + `sha256` 相同 + 入口退出码 `0` | **PASS** |
| AC-2 | as-is 本机 m0 到 **23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`），且运行**在记录写入之后**（承 MEM-145） | **PASS** |
| AC-3 | 治理 `validate.py` 绿（含 `DOCS-CHECK`） | **PASS** |
| AC-4 | CI 台账到终态（M0 **八 job** + CodeQL，含 `run_attempt`） | **PASS** |
| AC-5 | 承继残余**逐条在位**：`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` / `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12` | **PASS** |
| AC-6 | 未覆盖范围**逐条明写**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 | **PASS** |

## 实施清单

| WP | 内容 | 状态 |
| --- | --- | --- |
| WP1 | 写收口复检断言集（覆盖 EC-01…EC-03 交付面 + 六个受保护判据在位 + 入口无盘符绝对路径）⇒ 12 条判词 | 完成 |
| WP2 | 单树干跑（`--root . --verdict-only`）⇒ 12/12 PASS、`EXIT=0` | 完成 |
| WP3 | 两树实跑（`--script-mode shared`；干净 checkout = `git worktree add --detach @ 5359fab`）⇒ 两树 12 条、`sha256` 相同、`TWO-TREE PASS`、`EXIT=0` | 完成 |
| WP4 | **自举实证**：跑 EC-02 判据确认**本轮记录被真的执法**（含按压「抹掉 `verify_paths` ⇒ 判红」+ 逐字节复原） | 完成 |
| WP5 | 记录写入后跑记录面判据 + 独占全量 m0 | 完成 |
| WP6 | commit + push + CI 轮询到终态 + 台账 | 完成 |

## 证据

| # | 交付物 / 证据 | 说明 |
| --- | --- | --- |
| E1 | `scratch/goal022-ec04-closeout-recheck.py` | 收口复检断言集（12 条判词；只读结构性事实；判词行**不含绝对路径**） |
| E2 | `scratch/goal022-ec04-verdict-current.txt` | **当前树**判词留档；raw `sha256` = `e6febee8…` |
| E3 | `scratch/goal022-ec04-verdict-clean.txt` | **干净 checkout**判词留档；raw `sha256` = `e6febee8…`（与 E2 一致是**结论**，不是同一份文件） |
| E4 | `scratch/goal022-ec04-two-tree.log` | 入口运行记录（`TREE …` / `COMPARE identical=True` / `TWO-TREE PASS`） |
| E5 | `scratch/goal022-ec04-m0.log` | as-is 本机 m0 日志（终态行 + 运行时刻） |
| E6 | `RECHECK-20260928-218`（本目录同批） | 独立复检；`verify_paths` 声明**两路** —— 它是 EC-02 判据的**第一条真实受判记录** |
| E7 | `MEM-20260928-156` | 可复用事实：「受判集合为空 ⇒ 判据尚未生效；要在第一条真实记录上按压才算收口」 |

**两树入口的实跑判词**（两树逐行相同）：
`TREE current=D:\research-system exit=0 verdicts=12 sha256=e6febee8…` /
`TREE clean=D:\research-system-clean-tree exit=0 verdicts=12 sha256=e6febee8…` /
`COMPARE identical=True` / `TWO-TREE PASS`。

**自举实证的实测判词**：
扫描面 **4 → 5** 条、**受判集合 0 → 1** 条、`declared_path_problems(本条) = []`、`outstanding = 0`；
按压 ⇒ **`1 failed, 8 passed`**（失败消息逐字点名本记录）；
raw `sha256` 复原一致（`485fcee7…`）⇒ **9 passed**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | cycle 4 开工：写收口复检断言集（12 条判词） |
| 2026-09-28 | IN_PROGRESS | 单树干跑 12/12 PASS；两树实跑 `TWO-TREE PASS`、`sha256` 相同 |
| 2026-09-28 | IN_PROGRESS | 自举实证：受判集合 0 → 1；按压 `1 failed, 8 passed`；逐字节复原 ⇒ 9 passed |
| 2026-09-28 | DONE | 记录写入后跑记录面判据 + 独占全量 m0；治理绿；GOAL-022 置 ACHIEVED |

## 影响报告

- **改动**：新增 `scratch/` 探针与留档（gitignored）；新增 `.cursor/plans/` 两条记录 +
  一条 `MEM-156`；更新 GOAL-022 与 `ALL_PLAN.md`。**无树内产品 / 测试 / 文档改动**。
- **lint/typecheck/test**：以记录面判据 + 全量门结论为准（见 `RECHECK-20260928-218`）。
- **Domain/API/schema 变化**：**无**。
- **安全/凭据变化**：**无**（不碰 token、不碰认证面、不碰 `MIMOSA_*`）。
- **兼容性/迁移风险**：**无**（纯记录 + gitignored 探针）。
- **上游版本影响**：**无**。
- **下一项任务**：GOAL-022 收口（状态 → ACHIEVED）；后续若要把 `tools/` 纳入
  `PRODUCT_ROOTS`（收口 EC-01 的 `W-1`），需**单独立项**（超出本 GOAL 授权）。
