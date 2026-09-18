---
id: RECHECK-20260918-094
plan_id: PLAN-20260918-094
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle2
baseline_ref: 55757a3
checked_head: worktree
---

# RECHECK-20260918-094 — 审批通过后续跑失败的补偿（GOAL-005 cycle 2 = EC-02）

## 检查范围

PLAN-20260918-094 声称的交付面：审批入口的续跑失败补偿、四条用例与反证、文档同源。
**不在本轮**：`resume_paused` 侧（GOAL-004 EC-06 已收口）、补偿的诚实边界
（进程内上下文不复活、无任务级归因）——沿用 EC-06 的既有边界，不重复主张。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| 缺口描述先被纠正 | 读状态机 + 端点代码，对照 RECHECK-090 W-1 的原文 | PASS（W-1 写"停在 `WAITING_FOR_APPROVAL`"；实测 `decide` 先落 `RUNNING` ⇒ 失败后是**悬空 RUNNING**；PLAN 已写明这一纠正） |
| AC-01 失败即补偿 | 用例断言 **store 里的** run 行状态（不是响应文本） | PASS（`PAUSED`；裁决仍 `APPROVED`） |
| AC-02 原因可观测 | 读 `/runs/{id}/events` 的 `run.resume_failed` payload 三个键 | PASS（`failure_type` / `message` / `compensated_to`） |
| AC-03 可重入 | 补偿后再 `POST /runs/{id}/resume` | PASS（200 + `continuation=RESUMED`；不再被 409 挡） |
| AC-04 既有语义不变 | 正常路径用例 + 竞态用例 | PASS（正常 ⇒ `RUNNING` 无失败事件；竞态 ⇒ no-op 且无事件） |
| AC-05 反证 | 补偿替换为 `raise exc` 后重跑 | PASS（**2 failed / 2 passed**，红的正是断言补偿的两条） |
| AC-06 文档同源 | `docs/api/CONTROL_PLANE_API.md` Tasks / Approvals 节 | PASS（写明结局口径、响应不新增字段、单入口与竞态语义） |
| 未改断言/门禁/快照 | `git diff --stat` 对照提交内容 | PASS（只改产品 1 文件 + 新增 1 测试文件 + 1 文档；无门禁/快照改动） |
| Canonical State 边界 | 迁移是既有的 `RUNNING --PAUSE--> PAUSED` | PASS（未新增状态/迁移 ⇒ 不需 ADR） |
| 定向套件 | `tests/api tests/application tests/contracts tests/domain tests/e2e`（DSN pin） | PASS（**1997 passed / 4 skipped**） |

## 反证与实测

- **反证跑**：把 `_resume_after_approval` 的补偿分支换成 `raise exc`（等价于修复前的行为）
  ⇒ `tests/api/test_approval_resume_compensation_api.py` **2 failed / 2 passed in 2.66s**，
  失败点分别落在「store 里是 `PAUSED`」与「补偿后能重入」两条断言上 ⇒ 断言有判别力，
  不是"永远绿"。恢复补偿后 **4 passed**。
- **判据落在 canonical 而非响应**：AC-01 断言读 `runs_store`（`_stored_state`），
  与 EC-06 的既有手法一致——响应可能只是"说得好听"。
- **未做的验证**：没有跑真实的"执行期炸掉"端到端（本 PLAN 的失败注入是执行侧替身）；
  真实的执行失败路径由 GOAL-004 的 fault 矩阵覆盖，本轮不重复。

## 告警（W）

- **W-1（进程内上下文不复活）**：补偿只改 canonical；`_waiting` 里的上下文已被 pop，
  进程内不会再复活 ⇒ 重入走 `resume_paused`（无暂停上下文时再走 durable 重建）。
  与 EC-06 的 W-2 同一边界，本轮不改变。
- **W-2（响应仍是 200）**：`decide` 的成功响应不含续跑结局字段，调用方要判失败必须读
  canonical 状态或事件链（文档已写明）。若将来需要传输层信号，属产品决策。
- **W-3（失败原因无任务级归因）**：事件 payload 只有异常类型与文本（沿用 EC-06 口径）。
- **W-4（只有一处驱动）**：审批续跑只有 API 端点一个入口（守护线程不涉审批）；
  补偿实现与 `resume_paused` 共用，但"两入口语义一致"这条在本轮表现为**单入口**而非
  两条一致——已写进文档，不假装成两处。

## 门禁

- 治理 validator：绿（本机实跑）。
- 定向：见上表（1997 passed / 4 skipped）；合并跑 `test_resume_compensation_api` +
  `test_approvals_api` + 新文件 **18 passed**。
- 本地 m0 与 CI 六 job 终态：见 PLAN 状态历史与 GOAL-005 迭代日志（循环内回填）。

## 结论

EC-02 成立：审批通过后的续跑失败**不再是悬空 `RUNNING`**——裁决落库不变，run 被补偿回
`PAUSED`，失败原因进事件链，且补偿后可从停车态真的续起来。判据形态与 GOAL-004 EC-06
逐条对齐（失败即补偿 / 可观测 / 可重入 / 反证），并且**先纠正了上游告警对缺口的描述**
（不是 `WAITING_FOR_APPROVAL`，而是已落 `RUNNING`）。

结果为 **PASS**：反证有判别力（2 红）、定向套件全绿、未改任何门禁或断言、未触
Canonical State 边界。W-1…W-4 是沿用 EC-06 的诚实边界，不因本轮而消失。
