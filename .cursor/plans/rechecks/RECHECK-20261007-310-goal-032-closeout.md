---
id: RECHECK-20261007-310
slug: goal-032-closeout
title: 复检：GOAL-20261007-032 自举收口（EC-04）—— 验证器进树 + 两树复检 + as-is m0 + 治理 + CI 台账
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-07
updated_at: 2026-10-07
plan_id: PLAN-20261007-309
reviewer: root-agent
parent_goal: GOAL-20261007-032
verify_paths:
  - >-
    uv run --frozen --no-sync python -B tools/verify_goal032_closeout.py --root . --verdict-only
    ⇒ 64 PASS / 0 FAIL（本树；#本 GOAL 工具自举）
  - >-
    uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script
    tools/verify_goal032_closeout.py --script-mode shared --root . --base-ref HEAD
    ⇒ 两树判词逐行相同、sha256 相同、COMPARE identical=True、TWO-TREE PASS
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 EC-04 与 fix_policy；收口复检按 `MEM: goal-closeout-procedure`
    （验证器进树 + 两树 + 归档 + m0 + 治理 + 台账），声明 `verify_paths` ≥ 2 路并用**本 GOAL
    自己的工具自举**。**不改任何既有判据**（`IN_SCOPE` 为纯收紧；`standard_verdicts` 一行未重写）。
---

# RECHECK-20261007-310：GOAL-032 自举收口

## 检查结果

四条 AC 逐条实测（读数见下；两树与 m0 的终值随收口提交登记在 GOAL 的「CI 台账」与
「迭代日志」）：

1. **验证器进树 + `IN_SCOPE`（纯收紧）**：`tools/verify_goal032_closeout.py`（193 行）+
   `tools/goal032_closeout_assertions.py`（317 行）——**公共面一行不重写**（直接调
   `tools/closeout_recheck_assertions.standard_verdicts`），只写 GOAL-032 特有断言；
   两文件加入 `IN_SCOPE`（**只增不删**，`git diff --numstat` = `+3 / -0`）；
   两文件均过四道门。**首轮被门抓到的自己的错**：断言集初版调用
   `toolbox.ast_module(...)`——该工具箱**没有**这个方法（它按 `text_body` 工作）⇒
   `AttributeError`；另有两处 mypy（`Any` 返回 / `walk(None)`）与一处超长行 ⇒ 全部按门修，
   **未**放宽任何门。
   **首轮被验证器自身抓到的自己的错**：① `_dict_keys` 只读 `tree.body` ⇒ 读不到
   **类体内**的 `_TRANSITIONS` ⇒ `ec01-dead-letter-has-exactly-one-edge` 报 `none`
   （若判据写成"空集即通过"就会**静默假绿**——本判据的形态是"必须恰为 `REQUEUE`"，
   所以它抓住了）；② 例数下界按**参数化例数**写（8 / 7）而实际是**函数 def 数**
   （6 / 4）⇒ 两条判红 ⇒ 按实际读数定基（**只下调到实测值**，不是放宽到 0）。
2. **两树复检**：见 `verify_paths` 第 2 路（`TWO-TREE PASS`）；判词归档进树
   （`.cursor/plans/goals/evidence/GOAL-20261007-032-verdict-{current,clean}.txt`，
   二进制写盘、CR=0）。
3. **as-is m0**：终局行 `PASS: profile=m0; 23 deterministic checks`（**全部记录写入之后**、
   独占、仓库 `.venv`、canonical DSN pin、不接管道）。
4. **治理 + CI 台账**：`validate.py` 绿；台账逐提交（`7eef4bf` / `547c12a` / `de928ac` /
   本批次），自我指涉边界明写并以「末条提交 + 覆盖说明」封闭。

## 警告（如实登记）

- **`W-1`｜`R26-7` / `R26-8` 原样保持**：CI 台账的原始 JSON 证据仍在树外（`scratch/`，
  gitignored）；GOAL 正文的 EC 汇总表与 frontmatter 的一致性未机械化（本轮靠人工同轮更新）。
- **`W-2`｜本验证器的 64 条判词未逐条按压**：按压只覆盖了三个反证（EC-01 两条 / EC-02 两条 /
  EC-03 一条 = 5 臂，见各自 RECHECK）；**其余判词的"改坏会判红"未逐条实测**
  （承 GOAL-026/031 的同款残余）。
- **`W-3`｜两树复检的干净 checkout 是 `HEAD`**：`--base-ref HEAD` ⇒ 它证明的是
  「提交后的树也成立」（排除未提交产物），**不是**跨版本回归。
- **`W-4`｜EC-02 的 PG 判据在无 PG 的环境会 skip**：本轮在 CI 上（有 PG 服务）实跑；
  本机读数亦为实跑（`localhost:15432`）。**skip 不等于 PASS**（台账口径）。
- **`W-5`｜承继残余仍在**：`W31-1`…`W31-4`、`W27-*`、`W10-12`、`G24-5`、
  `R-M1`、`R26-2/3/4/6`、`R26-7/8` 逐条保持（见 GOAL 的「承继残余」节）。
- **`W-6`｜未覆盖范围原样保留**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面 /
  `R-M1` / D 组审批通道 —— 逐条见 GOAL。
- **`R-M1` 未收口**（不得宣称项目安全）；**投递语义仍非 exactly-once**（**明确否认**；
  口径只能是 at-least-once + idempotency + deduplication）。

## 结论

`PASS_WITH_WARNINGS`。四条 AC 全 PASS，两路复检（本树 64 判词 + 两树同结论）与
as-is m0 齐备；`W-1`…`W-6` 如实登记。**未**改任何既有判据（`IN_SCOPE` 纯收紧）；
**未**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**；
口径只能是 at-least-once + idempotency + deduplication）。
