---
id: MEM-20260919-084
title: "「待拍板」要落成可判形状：ADR 草案 + 四处同源 + 判据钉「行为未变」；策略规则 scope 是严格相等（生命周期请求不带 scope ⇒ 带 scope 的 allow 永不命中）"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-112-toolpack-capability-policy-decision.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-112-toolpack-capability-policy-decision.md
supersedes: []
tags:
  - policy
  - tool-pack
  - adr-draft
  - change-detection
  - scope-matching
  - honest-registration
---

# `tool_pack.*` 待拍板面（GOAL-20260919-007 / EC-06）

## 做了什么

`tool_pack.install|update|revoke` 的"产品决策面"在既有边界内**做不了**（放松默认 deny /
改审批语义），于是按 EC-06 的另一条路交付：**ADR-0031 草案（`Status: Proposed`）**
+ `docs/INDEX.md` 权威登记 + 三处声明面同源收敛 + 一个判据测试
（`tests/tooling/test_toolpack_capability_policy_pending.py`，10 passed）。**零产品代码改动**。

## 为什么这样做

1. **"没实现"和"策略未定"要分开**。`tool_pack.*` 的写面、digest 重算、读面（→
   `catalog_merge` → `CompiledRunPlan` → preflight `SUPPLY_CHAIN_UNPINNED` → 冻结进
   manifest）都已在树；缺的只是"平台默认策略给不给放行"。把这种状态写成"待实现"会误导，
   写成"已实现"更误导 ⇒ 正确形态是**草案 + 判据把今天的行为钉住**。
2. **判据必须能证明"不是文案改动"**。只读文档的断言挡不住"注释改了、行为没变"这种假
   交付。本轮的做法是**跑求值器与 use case**：(i) 真实 `policy.yaml` 经
   `NativePolicyEvaluator` 对三个能力判 DENY 且判词是 `used default policy effect`；
   (ii) 走**公共** `ToolPackLifecycle.submit` + 记录型求值器，证明请求 `action is None`
   且被拒。F-3 反证时给 `policy.yaml` 加一条**不带 scope** 的 allow 规则 ⇒ 测试报
   `DID NOT RAISE PermanentPortError`（`submit` 真的成功了）—— 这条"行为红"才是判据
   值钱的证据。
3. **§策略面实测细节（本仓没有文档写过）**：`PolicyRule.matches` 对 `scope` 是
   **严格相等**（`self.scope is None or self.scope == scope`），而生命周期构造
   `PolicyRequest` 时**只传 `actor` / `capability` / `resource`**。推论两条：
   ① 任何带 `scope` 的 allow 规则**永不命中**生命周期（给 `tool_pack.install` 加
   `scope: project` 的 allow 规则，实测 DENY 判定不变）；
   ② **不带 scope** 的 allow 规则**立刻生效**（实测 `submit` 直接成功）。
   所以"运维显式放行"必须写成不带 scope 的规则，或先让调用方补 scope。
4. **同源收敛 = 一处索引 + 每处声明面都指向同一份记录**。索引（`docs/INDEX.md`）是唯一
   入口；声明面（控制面 API 文档 / 控制台页面图 / live 夹具注释）各自原先都写着"这是缺口"，
   但**不指向任何决策记录** ⇒ 读者走到那里就断了。收敛动作很小（各加一句 ADR 指针），
   价值在于"从任一处都能走到同一份待拍板记录"。

## 怎么做与复现

- 判据：`uv run --frozen --no-sync python -B -m pytest tests/tooling/test_toolpack_capability_policy_pending.py -q` ⇒ 10 passed。
- 反证四处（记录在 RECHECK-20260919-112）：
  ① ADR 改 `Status: Accepted` ⇒ 1 failed；② 删任一声明面的 ADR 指针 ⇒ 1 failed；
  ③ 加**带 scope** 的 allow 规则 ⇒ 1 failed（只有结构断言红，DENY 那条安然无恙）；
  ④ 加**不带 scope** 的 allow 规则 ⇒ 3 failed，含 `DID NOT RAISE` 的行为红。

## 适用边界（踩过的坑）

- **草案期间行为一点没变**：真实部署下 `tool_pack.*` 仍 403，控制台写面仍不可用；
  live 套件跑得通**只因为夹具层放行**（`tests/api/console_api_app.py` 的
  `_ConsoleToolPackPolicy`），这**不等于**产品允许。
- **那条 `action: TOOL_PACK_INSTALL_OR_UPDATE` 是死的**：它写在 `require_approval` 段，
  但没有任何调用方传 `action` ⇒ 按构造不可能匹配。"策略文件里写了"不等于"策略面消费它"。
  更危险的推论：`_require_decision` **只拦 DENY**，所以今天把它"接通"反而会**静默放行**。
- **拍板后实施时判据会红**，这是刻意设计（改行为先改记录）；实施者要同时更新判据、ADR
  状态与本记录，而不是绕开判据。
- `docs/storage/DATABASE_SCHEMA.md` 是**草图**口径：`tool_pack_manifests`、`research_runs`
  等都不是物理名（已落地的是 `tool_packs`、`runs`）。改文档时别把草图名当表名 grep。
- 判据里"事实名仍来自 adapter"是**文本包含**（强度低于 EC-03 的端到端用例）；
  真正的行为证明在 `tests/e2e/test_ec03_real_runtime_offline_chain.py`。

## 来源

- `.cursor/plans/tasks/PLAN-20260919-112-toolpack-capability-policy-decision.md`
- `.cursor/plans/rechecks/RECHECK-20260919-112-toolpack-capability-policy-decision.md`
- 草案：`docs/adr/ADR-0031-toolpack-capability-policy.md`（先例：ADR-0030 同形态）
- 策略面：`examples/config/policy.yaml`、`packages/domain/policy.py`（`PolicyRule.matches`）、
  `packages/application/policy/native.py`、`packages/application/tool_plane/lifecycle.py`
- 验收面：`packages/domain/acceptance.py`（字面包含判定）、
  `examples/contracts/task_contracts.yaml`（`console_demo_deliverable` → `analysis_report`）
- 判据：`tests/tooling/test_toolpack_capability_policy_pending.py`
