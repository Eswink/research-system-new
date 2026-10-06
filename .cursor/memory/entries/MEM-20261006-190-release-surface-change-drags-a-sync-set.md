---
id: MEM-20261006-190
title: "放行面扩容的必然同步集：往 policy.yaml 加 allow 会移动**若干既有判据的钉定值**（不止镜像表），且 pin 夹具的追加形态各有不同"
status: ACTIVE
created_at: 2026-10-06
updated_at: 2026-10-06
scope: repository
confidence: 0.92
review_after: 2027-04-06
source_plans:
  - .cursor/plans/tasks/PLAN-20261006-293-goal-031-ec01-read-capability-release.md
  - .cursor/plans/tasks/PLAN-20261006-295-goal-031-ec02-citation-validate-full-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261006-293-goal-031-ec01-read-capability-release.md
  - .cursor/plans/rechecks/RECHECK-20261006-295-goal-031-ec02-citation-validate-full-chain.md
supersedes: []
tags: [policy-allow, pin-fixtures, sync-set, difference-set, goal-031, plan-293, plan-295]
---

## 做了什么

GOAL-031 的两处「放行面变化」实测出的**必然同步集**（不只是镜像表）：

**EC-01（往 `policy.yaml` 的 `allow` 加 6 条只读能力）** ⇒ 建档勘察实测**6 条既有判据转红**
（`6 failed / 4428 passed`），逐类：
1. 镜像表 `policy_check._CAPABILITY_SCOPE`（并集相等由 `test_m2_audit` 锁死——改一侧必红）；
2. **差集表**（`docs/architecture/POLICY_SURFACE_AUDIT.md`）：放行面变化会让「该登记」条目
   **移出**差集 ⇒ 表行数与计数必须同轮更新（`test_policy_surface_difference_set` 双向完备）；
3. **登记面钉定值**：`EXPECTED_REGISTERED` / `_REGISTERED_NOT_GRANTED` 这类「未放行清单」
   的示例名必须换成**仍未被放行**的能力（原本拿 `claim.read` 当例子 ⇒ 放行后它不再是例子）；
4. 其他以「未放行」为前提的 onboarding 判据（断言按新状态翻转，**强度未降**地重新定基）。

**EC-02（新增 provider 承接 `citation.validate`）** ⇒ pin 面三类，**形态各不同**：
- **多行 set 字面量**（`test_europe_pmc_pin_and_registration.py`）：**纯追加一行**
  （`git diff --numstat` 删除行 **0**）；
- **单行 tuple**（`tests/api/run_fixtures.py::_PROVIDERS`）：追加必然产生 **1 行替换**
  （内容只增不减）⇒ 如实登记为 `W-EC02-1` / `W31-3`，**不得伪称删除为 0**；
- **两条下界断言**（`test_mcp_registration_and_refutations` 等）同样只剩追加。

## 为什么这样做

「放行面」不是一个文件的局部改动，而是一张**多面契约**：policy.yaml ↔ 镜像表 ↔ 差集表 ↔
「未放行子集」的判据示例 ↔ pin 夹具。只改 policy.yaml 会让一批判据红；把红判据挨个改绿
而不区分「**重新定基**」与「**放宽断言**」则可能违规。正确口径：
- **同步集内**的钉定值可以**重新定基**（数值 / 示例随授权状态变化），但**谓词形态与强度
  必须保持**，并在记录内**逐条自证**；
- **同步集以外**的任何断言改动 ⇒ 命中全局禁令 ⇒ BLOCKED。

## 怎么做与复现

- **动手前先勘察**：在隔离 worktree 里先把 `allow` 改好，跑全量受判面，**逐条点名**转红的
  判据与其钉的是什么（GOAL-031 建档实测 `6 failed / 4428 passed` 即此）。
- **pin 追加**用 `git diff --numstat` **逐文件出示删除行读数**；单行 tuple 的 1 行替换
  **如实登记**，不伪称 0。
- **deny 面基线指纹**：`require_approval:` 段起至文件末的 LF 归一化 `sha256`
  （本仓基线 `bf04fa4e…`）写进新判据内，前后**逐字节相等**才算「零改动」。
- 复现：
  `uv run --frozen --no-sync python -B -m pytest tests/application/preflight/test_release_expansion_is_read_only.py
  tests/application/test_m2_audit.py tests/application/preflight/test_policy_surface_difference_set.py -q`
  ⇒ 全绿；判据与读数归档
  `.cursor/plans/goals/evidence/GOAL-20261006-031-ec01-release-ledger.txt` /
  `GOAL-20261006-031-ec02-release-and-pin-ledger.txt`。

## 适用边界

本仓所有**策略面 / 声明面 / 词表**变化（放行、承接、能力词表增删）都适用；
`tools/` 目录的旧 lint 资产不在受判面内（只有**被点名脚本**过四道门）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261006-293-goal-031-ec01-read-capability-release.md` /
  `.cursor/plans/tasks/PLAN-20261006-295-goal-031-ec02-citation-validate-full-chain.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261006-293-goal-031-ec01-read-capability-release.md` /
  `.cursor/plans/rechecks/RECHECK-20261006-295-goal-031-ec02-citation-validate-full-chain.md`
- 事实：建档实测 `6 failed / 4428 passed`（逐条点名）+ GOAL 的「事实层结论」节；
  pin 读数归档 `.cursor/plans/goals/evidence/GOAL-20261006-031-ec02-release-and-pin-ledger.txt`
