---
id: MEM-20260929-172
title: "自举收口的两个工具同时受 450 行上限与复杂度 10 的约束 ⇒ 验证器只能「公共判词复用标准断言集 + 只写特有断言」，审计器的下界判定必须用合成输入做行为判据（源码里写下界文案不算证据）"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-253-goal-026-ec05-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-254-goal-026-ec05-self-bootstrap-closeout.md
supersedes: []
tags: [closeout, tooling, scale-gate, behavioural-criterion, ci-ledger, goal-026, ec-05]
---

## 做了什么

GOAL-026 的 EC-05 自举收口要**同时**满足两件互相拉扯的事：把五条 EC 的判据面钉进一个
**可复跑**的验证器，并让**验证器自己**也进机器门。实测的落地形态：

- `tools/verify_goal026_closeout.py`（**449 / 450 行**）：公共面（受保护判据 / 规模门 /
  产品根 / m0 条数 / 两树入口 / 规范页 / 记录路径自洽）**一行都不重写**，直接调
  `tools/closeout_recheck_assertions.py::standard_verdicts` 取 18 条标准判词，本文件只追加
  30 条特有判词；判词名用 `ec01-files` / `ec02-cases-floor` / `ec05-audit-empty-jobs` 这类
  **短名 + `v = factory` 别名 + 单行调用**才压得进上限。
- `tools/audit_goal026_ledger.py`（**201 行**）：`audit_pair` 首版**复杂度 11 > 10**
  （被 ruff 的 `max-complexity` 抓），拆成 `run_problem()` + `jobs_problem()` 才过门。
- 「**空集合 = 未取证**」这条下界由**验证器以合成输入跑审计器**判定（`tempfile` 现造四对
  run / jobs：空集 / 欠数集 / 有失败 job / 完整集），并要求 `rc != 0` + 输出含「未取证」
  + 失败 job 被**点名**。

## 为什么这样做

- **规模门 + 复杂度门对 `tools/` 同样生效**（一旦进 `IN_SCOPE`）⇒ 收口验证器不可能既
  「把公共面抄一遍」又「写满本轮断言」。**复用标准断言集不是风格偏好，是空间约束**：
  抄一遍公共面 ≈ 190 行，抄完就顶格了。
- **下界判定必须行为化**：GOAL-025 的教训是脚本对空 `jobs` **无条件打 OK**
  （`scratch/audit_goal025_ledger.sh`）。若只断言「源码里有 `if not jobs` 就判未取证」，
  那么把该分支改成 `return None` 也照样绿 —— **文案不是判据**。合成输入 + 按压 P1
  （改空集分支 ⇒ 唯一红行恰是该判词）才把这条下界变成**可证伪**的。
- **`rc` 与判词必须一起断言**：审计器是**子进程**，只断言「输出里有未取证」会被
  「打印了但退出码 0」骗过 ⇒ 四个合成形态都同时断言 `rc` 与输出。

## 怎么做与复现

1. 收口复检：`uv run --frozen --no-sync python -B tools/verify_goal026_closeout.py --root .
   --verdict-only` ⇒ **48 行判词 / 48 PASS / `rc=0`**（日志 `scratch/goal026-c5-verify.log`）。
2. 台账按轮次收窄：`... tools/audit_goal026_ledger.py --runs-dir scratch --prefix goal026-c4-
   --expect-sha <本轮 sha>`；**`--expect-sha` 是按目录全量生效**的 ⇒ 多轮证据混放时会得到
   一堆「sha 不符」红（首轮实测 8 条），那是工具**正确**行为，用 `--prefix` 收窄即可。
3. 按压两向（均已逐字节复原）：P1 审计器空集分支 → `return None` ⇒ 唯一红行
   `FAIL ec05-audit-empty-jobs -> rc=0`；P2 产品 `_consult_circuit` 的 except 分支 → `pass`
   ⇒ 判词红 **且** EC-03 判据文件自己的用例红（`1 failed, 4 passed`）。
4. 留档：`scratch/goal026-ec05-press-matrix.log`（2882 字节 / `CR` 计数 0 / 二进制写盘）。

## 适用边界

- 结论落在**本仓的收口机器**（`tools/verify_goal0NN_closeout.py` 这一族）与
  **`tests/tooling` 的射程机制**上；换仓需重核 450 行上限与 `max-complexity = 10` 是否同值。
- 验证器余量只有 **1 行**（449/450）⇒ 下一次追加必须先把公共面搬出去或改复用形态。
- 台账的**原始证据在树外**（`scratch/`，gitignored）⇒ 树内可复跑的是「审计器的形状 +
  行为判据」，**不是**台账本身（`R26-7`）；第三方在干净 checkout 上无法重derive CI 结论。
- 例数下界只数 `test_` 前缀函数个数 ⇒ 「例数够但断言被弱化」它抓不到（`W-4`）。

## 来源

- `PLAN-20260929-253`（GOAL-026 EC-05）与 `RECHECK-20260929-254`（§1 / §4 / §6）；
- 留档：`scratch/goal026-c5-verify.log`、`scratch/goal026-ec05-press-matrix.log`、
  `scratch/goal026-{c0..c4}-run-*-jobs.json`、`scratch/goal026-c4-ledger-audit.log`；
- 相关代码：`tools/closeout_recheck_assertions.py`（公共判词）、`tools/two_tree_recheck.py`（两树入口）、
  `tests/tooling/test_tooling_scripts_meet_product_gates.py`（射程 + 四道门）；
- 同族记忆：[[MEM-20260929-169]]（取消后无新副作用 ⇒ 判据要锚在计数上）、
  [[MEM-20260929-170]]（吞掉迁移异常 = fail-open，本轮的按压 P2 正是它的产品面）。
