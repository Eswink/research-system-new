---
id: RECHECK-20260923-135
plan_id: PLAN-20260922-135
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-135 — 沙箱实验阶段（GOAL-011 EC-03 的机械面）

## 检查范围

**不采信 PLAN-135 的结论文本**：接缝面由独立复检脚本从树上重新推导，**并由本 cycle 实跑**两类判据
（离线 + 真实容器）。**EC-03 的载体面（真实 run 跑到 `SUCCEEDED`）未达成**，因此本复检的结论是
**机械面 PASS + 载体面未达成**（如实登记，不记成功）。

## 检查结果

| # | 该 PLAN 的主张 | 复检怎么验的 | 结论 |
| --- | --- | --- | --- |
| 1 | 实验**声明化**：`TaskContract.experiment` 可选、缺省保持会话语义 | A 层：`packages/domain/tasks.py` 里 `ExperimentExecutionSpec` 在位；B 层：`tests/application/run_orchestration/test_sandbox_experiment_dispatch.py` 在位（含「未接线即点名拒绝、不静默回退」） | ✅ |
| 2 | 执行体 = **既有 Docker 后端**（不新增后端/依赖） | A 层：`services/api/experiment_support.py` 里 `docker_experiment_assembly` / `sandbox_experiment_runner` 在位；本 cycle 实跑 `tests/e2e/test_sandbox_experiment_seam_docker.py` ⇒ **2 passed**（真实容器、镜像 digest 进执行事实） | ✅ |
| 3 | 三项读面齐备（实验 / 证据 / 预算） | 同上判据的四段断言：科学产物（`n_train`/`n_test` 指标）→ 证据准入（`content_digest` 可重算）→ `GET /runs/{id}/experiments` 与 `/artifacts` 同值 → carrier 终态如实 | ✅（机械面） |
| 4 | 策略面 fail-closed（越权能力默认 DENY） | B 层：`tests/api/test_sandbox_experiment_seam.py` 五条（含逐能力参数化的 `test_every_guarded_capability_is_denied_by_default`）⇒ 本 cycle 实跑 passed | ✅ |
| 5 | 终态如实（`FAILED` 不得写成成功） | 载体协议今天仍收敛 `FAILED`（`rebuild` 读面 `missing=[manifest_digest]` 的缺口已在 cycle 10 修掉，但终态与判词未动）；`PLAN-138` 的 AC-4 逐字记 `FAILED` + 判词 | ✅ |
| 6 | 该 PLAN 的两处**载体声明**在 cycle 10 被**撤回** | `PLAN-135` 的定案 D-1 明文写「m12 **不做**载体」；cycle 9 的 `PLAN-138` 反其道行之并撞上 8 处夹具判据 ⇒ cycle 10 **只撤回载体面**，本 PLAN 的机械面（接缝三文件 `governed.py` / `experiment_support.py` / `clean_run_stages.py` 与 2 份判据）**保留** | ⚠️ 见 W-5 |

## 结论

**PASS_WITH_WARNINGS**：EC-03 的**机械面**（声明化派发 → 既有 Docker 后端执行 → 三读面齐备 →
策略 fail-closed）在树上成立且被真实容器判据钉住；**载体面未达成**（真实 run 未到 `SUCCEEDED`），
故 EC-03 整体仍为未达成，本 GOAL 以 BLOCKED 收口。

**W 列表（承自 PLAN-135，本次复检未消除）**

- **W-5**（本轮新增）：**同一份工作被两个 PLAN 以相反的前提做过**（`PLAN-135` 定案「m12 不做载体」，
  `PLAN-138` 拍板「把 m12 做成载体」）。两者都记录了理由，但**没有一处**在开工前核对另一份的定案。
  这不是文档缺失，而是**定案之间缺少交叉检查**：下次拍板前应先读**同 GOAL 内**相关 PLAN 的定案表。
- **W-6**：`PLAN-135` 的 AC-3「一次真实 LLM 驱动的 run 到终态」在载体上**仍然**未完成；
  「机械面达成」不等于 EC-03 达成——本条与 EC-03 的**未达成**状态一同进入下一轮输入。
