---
id: RECHECK-20261018-519
slug: goal-084-ec05-self-bootstrap-closeout
title: 复检 — GOAL-084 EC-05：自举收口（两树同结论 + m0 23/23 + 记录面自洽）
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-517
parent_goal: GOAL-20261018-084
reviewer: root-agent
owners:
  - root-agent
verify_paths:
  - 本树判词（`tools/verify_goal084_closeout.py --root . --verdict-only`）
  - 干净 checkout 判词（同一脚本、同一解释器、`--script-mode shared`）
  - as-is 全量 m0（静止工作树，终态行）
memory_entries: []
---

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| EC-05a | **验证器进树且自举** | **PASS** | `tools/verify_goal084_closeout.py` + `tools/goal084_closeout_assertions.py`；`self-loads-its-own-assertions` 按**本文件名**推出应载 `goal084_closeout_assertions.py` 并断言源码里引用的就是它 |
| EC-05b | **本树判词全绿** | **PASS** | `--root . --verdict-only` ⇒ **67 条 `PASS`、0 条 `FAIL`**（`EXIT=0`） |
| EC-05c | **两树同结论** | **PASS** | 两树入口：`verdicts=67` / `sha256=0e04121fe61676a528be7dc0dad58ae626a0051c438b98f500245034cae880a1`（两侧**完全相同**）；`COMPARE identical=True` / `TWO-TREE PASS` |
| EC-05d | **as-is m0** | **PASS** | 静止工作树、记录写完之后：`PASS: profile=m0; 23 deterministic checks`；`python/typecheck` ⇒ **1274 source files** |
| EC-05e | **治理** | **PASS** | `validate.py` ⇒ `Cursor 治理验证通过`（ALL_PLAN / Task Plan / Recheck / Memory 交叉引用一致） |
| EC-05f | **凭据四面** | **PASS** | `tools/credential_audit.py` ⇒ `tracked / records / config_db / logs` 四面 `offenders=0` |
| EC-05g | **阶梯记账（两个面）** | **PASS** | 宪章「复检」域的 `依据 GOAL` 收录本 GOAL；宪章「进展记录」有本 GOAL 一行且 `RECHECK` 列指向 `RECHECK-20261018-518`（两条都由 `ladder-*` / `progress-*` 判词钉住） |
| EC-05h | **CI 台账逐提交** | **PASS** | `e7d43001` 记 **零 run + 原因 + `covered_by`**；`6c6d9456` 八 job 全 `success` + 三条 CodeQL `success`，`run_attempt=1`、零 `cancelled`、零 rerun |

## 判词面（本轮特有的断言，逐条）

`tools/goal084_closeout_assertions.py` 的 67 条里有 **35 条是本轮特有**（其余是标准断言集
与记录面）。要点：

- **EC-01**：`resolver-module-exists` / `resolver-entry` / `resolver-by-role` /
  `resolver-describe` / `resolver-uses-target-tuple` / `resolver-states-the-target-identity` /
  **`resolver-has-no-outbound-imports`**（AST 扫 13 个黑名单根名 ⇒ 零出网）；
- **EC-02**：`role-checks-imports-resolver` / `role-checks-uses-target-labels` /
  `unresolved-role-is-named`（`MODEL_MISSING` + 点名词同在）+
  出厂目录真实读数四条（生产者 / 评审者 / 第二评审者 `model_name` 各自在位，且
  `factory-reviewer-differs-from-producer`）+ `critic-primary-is-the-third-party-model` +
  **`critic-does-not-fall-back-to-the-producer-model`**（`research_alpha` 不在该 profile 块里）；
- **EC-03**：`resolver-reads-profile-fallback` + 两条成对用例在位；
- **EC-04**：厂商协议通过 / 反向按压 / 未声明不判三条用例在位；
- **例数下界**：`test_review_independence` **8**、`_judgment` **9**、`_gate` **4**
  （读数取自 `pytest --collect-only`；删掉任一条即判红）。

**一处如实登记（初次运行的真红）**：首版把 `test_review_independence.py` 的下界写成 **9**，
实际收集 **8** ⇒ `case-floor-test_review_independence` 判红。处置是**把下界改成实测值 8**
（记录里的 `8 passed` 一直是对的），不是删用例、不是放宽断言。

## 两树复检的形态（逐条）

| 项 | 读数 |
| --- | --- |
| 解释器 | 两侧都是**主树 `.venv`**（`--script-mode shared`；干净树不自建环境） |
| 输出纯度 | 只接受 `PASS` / `FAIL` 开头的判词行；判词**不含任何树的绝对路径** |
| 判词数 | current **67** / clean **67** |
| `sha256` | `0e04121fe61676a528be7dc0dad58ae626a0051c438b98f500245034cae880a1`（两侧**相同**） |
| 结论 | `COMPARE identical=True` / `TWO-TREE PASS` |
| 归档 | `.cursor/plans/goals/evidence/GOAL-20261018-084-ec05-current.txt` / `…-clean.txt`（二进制写盘，CR=0） |

## 警告（如实登记）

- **`W-1`**：EC-05 的判词就在本文件里 —— 时序上 GOAL 的 EC-05 在本复检**跑之前**是待办，
  所以验证器接受「达成 ∪ 待办」两种取值。**这是时序，不是放宽**。
- **`W-2`**（承前）：本判据只判「底层模型 + endpoint 是否相同」，**不判**「评审是否真的
  独立判断」。
- **`W-5`**：`research_strong.fallback` 仍是 `[reviewer_gamma]`（= 生产者的同一个底层模型）⇒
  **生产侧没有模型多样性**；它有专门判据钉住（`test_the_gate_still_bites_…` 用的就是这条路径）。
- **`W-6`**：`glm-5.3` 的 `STRUCTURED_OUTPUT_NATIVE` **未声明** —— provider 声称支持，
  实跑 `json_schema` 未被强制（多出 schema 外的键、string 写成 number）。
- **`R-M1` 未收口** ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」（**明确否认**）。

## 未覆盖的面

- **读面认证**、**多租户·RBAC·BOLA·BFLA**、**部署面验证**、**D 组审批通道** —— 均未做；
- 默认 runtime 仍是 Fake（§11）；
- 「评审真的用不同模型判出负」是阶梯的**下一级**，不在本 GOAL 射程（见宪章）。

## 结论

**PASS**。EC-01…EC-05 全部达成：本树 **67 条判词全绿**、两树判词逐行相同且 `sha256` 一致、
as-is m0 **23/23**、治理通过、凭据四面 `offenders=0`、CI 台账逐提交（含「零 run」的
`covered_by` 登记）。首次运行抓到的一处真红（例数下界 9 vs 实测 8）已按实测修正并如实登记。
