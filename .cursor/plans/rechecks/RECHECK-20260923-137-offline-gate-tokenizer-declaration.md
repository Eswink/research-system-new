---
id: RECHECK-20260923-137
plan_id: PLAN-20260922-137
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-137 — 「默认 CI 离线」的措辞与判据同源（GOAL-011 EC-05）

## 检查范围

**不采信 PLAN-137 的结论文本**：措辞同源面由独立复检脚本重判（同一句在**判据自身**与
`docs/architecture/AGENT_RUNTIME.md` 里逐字在场），行为面由本 cycle 的实跑复核。

## 检查结果

| # | 该 PLAN 的主张 | 复检怎么验的 | 结论 |
| --- | --- | --- | --- |
| 1 | 定案取 (B) 降级措辞 + 判据（不固化词表） | `PLAN-137` 定案 D-1 在案（理由三条：外部二进制资产要 pin/digest/更新策略、收益只有每轮一次请求、EC-05 原文允许二选一）；`PLAN` 与 GOAL 的措辞一致 | ✅ |
| 2 | 声明受判：**跑 Python 门的作业**必须先预热 tokenizer | B 层：`tests/tooling/test_m0_ci_coverage.py::test_every_job_that_runs_the_python_gate_prewarms_the_tokenizer_first` 按名在位；`test_the_one_controlled_download_sentence_is_verbatim_in_both_homes` 在位；本 cycle 实跑 `tests/tooling` 全绿（**判据未被改动**） | ✅ |
| 3 | 同源句逐字在两处 | A 层：同一句 `CANONICAL_SENTENCE` 在 `tests/egress_guard.py`、`tests/tooling/test_m0_ci_coverage.py`、`docs/architecture/AGENT_RUNTIME.md` **三处**逐字在位（脚本按行比对，不是人读） | ✅ |
| 4 | 行为可判定（成对实跑） | cycle 8 的 A0/A1 成对实验（无代理 ⇒ 绿；注入不可达代理 ⇒ 红，且红线可归因）已在 `PLAN-137` 的证据里；本 cycle 未重跑（**不**把承前证据说成本轮实测） | ✅（承前） |
| 5 | `tests/egress_guard.py` 一行不改 | E 层正则判 `ALLOWED_KINDS` 仍只有 `localhost`；本 cycle 的 `git diff` 未触及该文件 | ✅ |

## 结论

**PASS_WITH_WARNINGS**：EC-05 的两处措辞（判据文档 + 架构文档）与判据机器校验同源，
判据本身在 cycle 8 已被**按压**（摘掉 `eval-gate` 的预热门 ⇒ 逐字红；复原 ⇒ 绿且 `git diff` 无痕）。

**W 列表（承自 PLAN-137，本次复检未消除）**

- **W-9**：预热门**当前必要性未被证实**（两条最可能触发的子集在冷缓存下都无词表下载）⇒
  按 PLAN-137 的决定**不删、登记为待复现项**。本轮不重测（保持承前口径）。
- **W-10**：`R-6` 的另一半——**CI 每轮仍有一次受控外部下载**（litellm 的 model cost map，
  失败即回落本地副本）——本轮**未消除**：它是「默认门离线」这条声明的**边界**，
  不是「判据被放宽」。任何把它消掉的方案都属新授权（见 GOAL 的「下一轮输入」）。
- **W-11**：本机跑全量门必须同时 pin 三条 DSN **与** `LLM_MAIN_KEY=""`（操作者 `.env` 会让
  litellm 在导入期把 key 带进进程 ⇒ 判据整轮判红、零用例失败）。配方在
  `docs/architecture/AGENT_RUNTIME.md`，本轮收口的 m0 实跑按此执行。
