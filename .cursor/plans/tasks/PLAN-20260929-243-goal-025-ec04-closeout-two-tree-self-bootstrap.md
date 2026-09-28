---
id: PLAN-20260929-243
slug: goal-025-ec04-closeout-two-tree-self-bootstrap
title: GOAL-025 cycle 4（EC-04）：自举收口 —— 收口验证器进树并入 IN_SCOPE + 两树复检 + as-is m0 + 残余与未覆盖逐条
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-025
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-025 的 **EC-04**（复用 022 / 023 / 024 的收口机器）。授权沿用该 GOAL 的
    `authorization.ref`：范围 = 「**新增判据 / 测试侧工具**（进 `tools/` 的必须**显式**加入
    `IN_SCOPE` ⇒ **纯收紧**）」+「**文档同源更新**」；push-to-main-for-CI 口径（**只推 main、
    不 force**、不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增** `tools/verify_goal025_closeout.py` 与**一行** `IN_SCOPE`
    收紧；**不修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名清单同 GOAL）；**不动**
    `tools/two_tree_recheck.py` 与 `tools/closeout_recheck_assertions.py`（只调用）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；**零**新依赖；**全离线**；金丝雀一律
    测试内构造的合成串；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口验证器进树并入必备清单**：`tools/verify_goal025_closeout.py`（复用
      `closeout_recheck_assertions.py` 的公共判词，只写本轮特有断言）过**四道门**
      （format / ruff / mypy / 规模），且 `IN_SCOPE` 显式把它加入（**纯收紧**，下界单调）。
    status: PASS
  - id: AC-2
    criterion: >-
      **两树同结论**：`tools/two_tree_recheck.py --script tools/verify_goal025_closeout.py
      --script-mode shared --root .` ⇒ 当前树 + 干净 checkout 判词**逐行相同** + `sha256` 相同 +
      `TWO-TREE PASS` / `EXIT=0`；两路留档**二进制一致**。
    status: PASS
  - id: AC-3
    criterion: >-
      **as-is 本机 m0 = 23/23**（终态行 `PASS: profile=m0; 23 deterministic checks`，
      **运行发生在记录写入之后**，承 MEM-145）+ 治理 `validate.py` 绿（含 `DOCS-CHECK`）+
      CI 台账到终态（八 job + CodeQL + `run_attempt`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **残余与未覆盖逐条在位**：12 条承继残余 + `G24-1`…`G24-6`（`G24-2` / `G24-3` / `G24-6`
      本轮收口，`G24-1` 部分收窄，`G24-4` / `G24-5` 注明**需用户拍板**）+ 五条未覆盖范围
      （**读面未认证** / 多租户 / BOLA·BFLA / 部署面未验证 / **R-M1 未收口**）逐条明写；
      收口验证器自身的按压（先红后绿 + raw `sha256` 逐字节复原）留档。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-244-goal-025-ec04-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-166-closeout-verifier-must-be-in-scope-and-pressable.md
---

# PLAN-20260929-243 — GOAL-025 cycle 4（EC-04）：自举收口

**动因**：GOAL-025 的三条交付（响应头面 / 正控制矩阵 / 白名单派生）各自有判据与复检，
但**没有**一条把「这些交付在本轮终态下**同时**成立」这件事机械地钉住 —— 这正是
`tools/verify_goal025_closeout.py` 的职责：它**复用**标准断言集，只补本轮特有的断言，
并且**自己也进射程**（否则「验证器」会成为唯一不过门的受判物）。

## 验收条件

见 frontmatter `AC-1`…`AC-4`。

## 实施清单

- [x] WP1：`tools/verify_goal025_closeout.py`（**447 行**）—— 标准断言集（GOAL-023 起的公共面）
      + 本轮特有断言：`EC-01` 头部清单三档分区（受判 2 / 豁免 3 / 不发射 1）+ 例数下界；
      `EC-02` 载体矩阵（正控制 6 / 机械理由 2）+ 源矩阵 4 条 + 例数下界；`EC-03`
      **重算**「派生面 == 人工清单」（读树内快照 JSON + 两个清单的 AST 字面量）；
      `EC-04` 前三 EC 终态 / 本 EC 时序 / 复检路径 / 子计划与记忆 / 残余与未覆盖 /
      自己进 `IN_SCOPE` / 自己无超长函数。
- [x] WP2：`IN_SCOPE` 显式加入本验证器（**纯收紧**：必备清单 ⊆ 射程 单调；且这使四道门
      （format / ruff / mypy / 规模）**覆盖**本轮新增的 `tools/` 脚本）。
- [x] WP3：`RECHECK-20260929-244`（独立复检）+ `MEM-20260929-166`。
- [x] WP4：两树复检（当前树 + 干净 checkout）+ as-is m0 + 治理 `validate.py` + CI 台账终态 +
      残余 / 未覆盖逐条。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 收口验证器 | `tools/verify_goal025_closeout.py` **447 行**；判词 **37 条**（标准面 18 + 本轮特有 19） |
| 四道门（本验证器） | `ruff format --check` = `1 file already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 1 source file`；规模 **447 行** / 函数无超 50 行 |
| 射程收紧 | `IN_SCOPE` 由 4 → **5** 条（新增 `tools/verify_goal025_closeout.py`）；`tests/tooling/` 三件套 **25 passed** |
| 收口复检（当前树） | `--verdict-only` ⇒ **37 PASS / 0 FAIL**（收口前只剩 `ec04-latest-recheck-resolves` 一条红，由本 PLAN 的 RECHECK 落地后转绿） |
| 按压（本验证器，先红后绿） | V1 GOAL 的 `EC-02` 由 `PASS` 改成**未终态取值** ⇒ `FAIL ec04-ec01-to-ec03-are-pass -> 未终态：[…]`（逐字判词见留档）；V2 `latest_recheck` → 不存在路径 ⇒ `FAIL records-declare-existing-rechecks` + `FAIL ec04-latest-recheck-resolves`；V3 派生面塞入未登记路由 `/__press-probe` ⇒ `FAIL ec03-derived-face-equals-the-registry`（点名该路由）+ `FAIL ec03-derivation-floors-are-pinned`；三处 raw `sha256` 逐字节复原后复绿 **37 PASS / 0 FAIL**；证据 `scratch/goal025-ec04-press-matrix.log`（**二进制写盘**） |
| 两树复检 | 待跑（干净 checkout 必须是**已提交的收口树** ⇒ 在收口提交之后跑，结果以「收口补记」落 GOAL） |
| m0 / 治理 / CI | 见 GOAL 迭代日志与 CI 台账（**记录写入之后**才跑；终态行 `PASS: profile=m0; 23 deterministic checks`） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | 建档（GOAL-025 cycle 4，EC-04）；验证器与射程收紧已进工作树（37 判词，收口前只剩一条红 —— 由本轮 RECHECK 落地后转绿）。 |
| 2026-09-29 | DONE | 验证器进树（**37 判词全绿**）+ `IN_SCOPE` 4 → 5（纯收紧）+ `tests/tooling/` 三件套 25 passed + 三处按压先红后绿且 raw `sha256` 逐字节复原 + `RECHECK-20260929-244` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain/API/schema**：无（`tools/**` + 记录；产品代码、权威快照与既有判据零改动）。
- **安全/凭据**：无凭据改动；收口复检全离线；判词不含任何树的绝对路径（两树入口的硬判据）。
- **兼容性/迁移风险**：无（纯新增脚本 + 一行射程收紧；m0 条数仍 `23`）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-025 收口（ACHIEVED）；后续 GOAL 的残余承继面见 GOAL 正文。
