---
id: MEM-20261028-232
title: "判据只覆盖一半函数会照绿：判负路径与悬空引用是本仓两类反复出现的假绿"
status: ACTIVE
created_at: 2026-10-28
updated_at: 2026-10-28
scope: repository
confidence: 0.95
review_after: 2027-04-28
source_plans:
  - .cursor/plans/tasks/PLAN-20261027-098-goal-098-independent-novelty-and-derived-experiment.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261027-098-goal-098-independent-novelty-and-derived-experiment.md
supersedes: []
---

# 判据只覆盖一半函数会照绿

## 做了什么

序 66（GOAL-098）真跑抓到一个产品缺陷：`novelty_claim_step.with_novelty` 的**判负**分支写
`replace(gate, passed=False, verdicts=(*gate.verdicts, rejection))`，而 `GateOutcome` 既没有
`verdicts` 字段（叫 `evaluations`），`passed` 也只是**只读 property** ⇒ 任何一次创新点判负
都会抛 `AttributeError`，把「声明不成立」变成「运行时崩」。

## 为什么这样做

`test_direction_to_report_v2_novelty.py` 只判了**直通面**（非创新点合约原样返回）与
`novelty_verdict` 自己返回非空 —— **没有一条**把那个非空判词喂回 `with_novelty`。
判据覆盖了函数的一半，于是读起来是绿的。**判负路径还有第二层门**：它要先跑完检索才轮到
执行，而当时真跑两次都被上游 503 挡在检索相 ⇒ 这条路径**一次都没被执行过**。

## 两类反复出现的假绿（本仓实测）

1. **半覆盖判据**：只测 happy path / 只测直通分支。识别手法 = 问「这个函数有几个出口」，
   每个出口至少一条用例；`with_novelty` 现在有 8 例（含判负、判据追加而非替换、归因
   不被改写、真文件按压证明改回旧写法会让 5 条以同一个 `AttributeError` 判红）。
2. **悬空取证引用**：docstring 写「真容器那一段是 `evidence/...-ec03-*.txt`，不在这里假装」，
   而该文件**从未创建**。它比没写更坏 —— 读起来像取证已存在。识别手法 = 凡 docstring 点名
   一个树内路径，就加一条判据钉「它在树」（`ec03-no-dangling-evidence-reference`）。
   同类前例：GOAL-076 的 `verify_goal076_closeout.py` 悬空引用了一个从未存在的验证器。

## 怎么做与复现

- **按压必须确认「真的红了」**：本轮两次踩「按压工具自己有 bug」——① 用 `monkeypatch`
  改**已导入**模块对字节码毫无影响（按压假绿）；② 子进程 `pytest` 目标名少写 `::ClassName`
  ⇒ exit 4（usage error）被读成「按压成功」。形态收进
  `tests/application/subprocess_press_support.py`（`PressResult.bit` 要求
  按压红 + 复原绿 + 复原逐字节相同）。
- **取证写出面要追加，不要覆盖**：一次抖动（`retry budget exhausted`）把上一次 `SUCCEEDED`
  的读数整个盖掉 ⇒ 「留存证据」被「最后一次尝试」替换。
- **派发面 ≠ 容器面**：`assembly.script` 是**输入**，容器产出的指标才是**输出**。两段都要
  判（`tests/e2e/test_experiment_script_selection_docker.py` 按脚本各自的签名指标区分）。

## 适用边界

适用于「有多个出口的函数（happy path + 判负/拒绝/异常）」与「docstring 里点名树内路径」的
任何判据面。**不**声称所有历史判据都已普查过出口覆盖（本轮只修了自己射程内的两处）；也
**不**声称 `with_novelty` 之外的判负路径都健全 —— 那是「判据的判据」这条长期路线的靶子。

## 来源

- GOAL：`.cursor/plans/goals/GOAL-20261027-098-independent-novelty-and-derived-experiment.md`
- 子 PLAN：`.cursor/plans/tasks/PLAN-20261027-098-goal-098-independent-novelty-and-derived-experiment.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261027-098-goal-098-independent-novelty-and-derived-experiment.md`
- 真跑取证：`.cursor/plans/goals/evidence/GOAL-20261027-098-ec02-novelty-independence-run.txt`
  （`run_id=783e6dc7`，`state=SUCCEEDED`）与
  `.cursor/plans/goals/evidence/GOAL-20261027-098-ec03-container-run.txt`（两个脚本各一次真容器）
- 判据：`tests/contracts/test_novelty_rejection_turns_the_gate_red.py`（8 例）、
  `tests/e2e/test_experiment_script_selection_docker.py`
