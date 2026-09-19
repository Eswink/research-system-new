---
id: PLAN-20260919-112
slug: toolpack-capability-policy-decision
title: "`tool_pack.*` 二选一终态：ADR 草案（Proposed）+ 权威登记 + 同源收敛 + 结构判据（EC-06）"
status: IN_PROGRESS
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 6 = EC-06。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`。EC-06 只允许 (a) 既有边界内实现 或 (b) ADR 草案（`Status: Proposed`）+ 权威登记 + 同源收敛；**是否采纳、是否置 Accepted 归用户**。本 PLAN 遵守：不放松默认 deny、不新增 canonical 状态/迁移、不改 Accepted ADR、不新增依赖、真实端点调用永不进默认 CI。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260919-112 — `tool_pack.*` 二选一终态（GOAL-007 cycle 6 = EC-06）

## 选择与理由（二选一里的哪一条，以及为什么）

选 **(b) ADR 草案（Proposed）+ 权威登记 + 同源收敛 + 结构判据**。理由是可复核的：

- **(a) 走不通**：「既有边界内实现」的两种可能实现方式都会命中 `escalation_triggers`：
  ① 给 `examples/config/policy.yaml` 加 `tool_pack.*` 的 allow 规则 =
  **放松默认 deny 姿态**（核心安全策略）——明确不在循环授权内；
  ② 让 `tool_pack.update` 走「待批准」= 需要改 `ToolPackLifecycle._require_decision`
  对 `REQUIRE_APPROVAL` 的处理（今天只拦 `DENY`）+ 决定审批语义 = 产品决策。
  两者都**必须**留给用户拍板，循环内不得自行决定。
- **(b) 是 EC-06 明文允许的终态**：ADR 草案（`Status: Proposed`）+ 权威登记 +
  同源收敛，且"是否采纳归用户"。

## 本轮勘察事实（只读，2026-09-19；均给出路径，可复核）

| # | 事实 | 位置 |
| --- | --- | --- |
| 1 | 平台策略**没有任何 `tool_pack.*` 规则**，`default_effect: DENY` ⇒ 真实默认下 console 写面 403（live 夹具层放行四个能力才跑得通） | `examples/config/policy.yaml:2`、`tests/api/console_api_app.py:139-156` |
| 2 | 唯一的 ToolPack 邻近规则 `action: TOOL_PACK_INSTALL_OR_UPDATE` **按构造不可能匹配**：`_require_decision` 只传 `capability=`，而 `PolicyRule.matches` 要求 `action` 相等 ⇒ 意图声明在，策略面**从不消费它** | `examples/config/policy.yaml:41`、`packages/application/tool_plane/lifecycle.py:64-77`、`packages/domain/policy.py:29-33` |
| 3 | `tool_pack.*` **不在平台能力词表**里（48 项无此项）；写面 manifest 声明未知能力会被 422，而生命周期自身求值的能力名**从不做词表校验** | `examples/config/capabilities.yaml`、`services/api/tool_pack_support.py:60-72` |
| 4 | `_require_decision` **只拦 `DENY`**：`REQUIRE_APPROVAL` 既不阻断也不登记 ⇒ 今天把规则改成"待批准"会**静默放行**（这条是安全侧的关键事实） | `packages/application/tool_plane/lifecycle.py:73` |
| 5 | 供应链 digest 的读面是真的：`INSTALLED` → `CatalogSnapshot.tool_pack_digests` → `CompiledRunPlan` → preflight `SUPPLY_CHAIN_UNPINNED` → 冻结进 `RunManifest.tool_pack_digests` | `services/api/catalog_merge.py:133-149`、`packages/application/protocol_compile/compiler.py:130`、`packages/application/preflight/checks.py:219-226`、`packages/domain/manifest.py:59` |
| 6 | **事实名 → 合约 artifact 名的映射不存在**：会话产出键名是 `session_message`，合约要求 `analysis_report`，acceptance gate 是**字面包含**判定 ⇒ 真实会话必判拒（EC-03 已固定为"链在正常工作"） | `adapters/openhands/runtime_adapter.py:66-91`、`examples/contracts/task_contracts.yaml:71-84`、`packages/domain/acceptance.py:93-101` |
| 7 | 仓库已有**同一形态的先例**：ADR-0030（Proposed）+ `docs/INDEX.md` 登记 + 一条手写判据测试（断言 `Status: Proposed`、INDEX 行含 `Proposed`、三处声明面都指向 ADR、**行为不变**） | `docs/adr/ADR-0030-validation-failure-consumption.md`、`tests/tooling/test_pending_validation_failure_registration.py` |
| 8 | ADR 房规：标题 `# ADR-00NN — <标题>`、`Status: Proposed`、`Date:`、`Deciders:`、`Scope:`，章节序 `Context → Decision needed → Options → Trigger → Consequences → Evidence / References`；下一个编号 = **ADR-0031** | `docs/adr/ADR-0029-…`、`docs/adr/ADR-0030-…` |
| 9 | 登记面：`docs/INDEX.md` 的 ADR 列表（`ADR-0025…0030` 已登记；ADR-0019 **未**登记——先例说明登记是逐条人工的，没有自动化） | `docs/INDEX.md:48,168-176` |
| 10 | 治理/文档校验**不检查 ADR**（`validate.py` 0 命中；`docs_consistency_check.py` 不读 `docs/adr/`）⇒ 判据必须由**手写测试**承担（先例同形态） | `.cursor/skills/governance-check/scripts/validate.py`、`tools/docs_consistency_check.py` |
| 11 | 三处权威登记面（"不提供/待决"口径）：控制面 API 文档、控制台页面图、live 夹具注释 | `docs/api/CONTROL_PLANE_API.md:433-436`、`docs/frontend/CONSOLE_PAGE_MAP.md:289-292`、`tests/api/console_api_app.py:150-156` |
| 12 | 一处**文档与实现不符**（顺带纠正）：`DATABASE_SCHEMA.md` 的 Tool 草图写着表名 `tool_pack_manifests`，树里没有这张表，已落地的是 `tool_packs`；且该草图其余名称（`research_runs`…）同样不是物理名 ⇒ 纠正方式是**加一行"草图名 ≠ 物理名"的注记并点出实际表名**，不逐条改名 | `docs/storage/DATABASE_SCHEMA.md:59-78`、`adapters/sqlite/tool_pack_store.py:29-38`、`adapters/sqlite/tool_provider_registry.py:21` |

## 口径

- **ADR 只写"需要拍板什么"，不代替拍板**：`Status: Proposed`，`Deciders` 行写明待拍板；
  **不得**写 `Accepted`（判负）。
- **不自作主张改产品策略**：不动 `policy.yaml`、不动能力词表、不动 acceptance 语义、
  不动 `_require_decision` 的决策处理——那是拍板后的实施。
- **判据必须证明"不是文案改动"**：至少一条用例/结构判据把**今天的行为**钉住
  （fail-closed 仍成立：真实平台策略对 `tool_pack.*` 判 DENY；合约仍按字面名判拒），
  并给出反证签名（删 ADR 指针 / 改成 Accepted / 加 allow 规则 ⇒ 各自红）。
- **登记 = 唯一入口**：`docs/INDEX.md` 的 ADR 列表加一行，行内含 `Proposed`（先例口径）。

## 验收条件

- **AC-01**：`docs/adr/ADR-0031-toolpack-capability-policy.md` 在树，`Status: Proposed`；
  含问题陈述、候选方案与代价（≥3 条）、为何本轮不做、触发条件、影响面。
- **AC-02**：`docs/INDEX.md` 登记该 ADR（行内含 `Proposed` / 待拍板口径）。
- **AC-03**：同源收敛——三处权威登记面（控制面 API 文档 / 控制台页面图 / live 夹具注释）
  都指向该 ADR；（顺带澄清 `DATABASE_SCHEMA.md` 的 Tool 草图名与物理表名的关系）。
- **AC-04**：结构判据测试（新）断言：ADR `Status: Proposed` 且**非** `Accepted`；INDEX 已登记
  且行内标 Proposed；三处声明面都提到该 ADR 文件名；**行为未变**——真实
  `examples/config/policy.yaml` 经 `NativePolicyEvaluator` 对 `tool_pack.install|update|revoke`
  判 DENY，且 acceptance gate 对 `analysis_report` 契约仍拒 `session_message`。
- **AC-05**：反证——① 把 ADR 改成 `Accepted` ⇒ 判据红；② 删任一声明面的 ADR 指针 ⇒ 判据红；
  ③ 给 `policy.yaml` 加 `tool_pack.install` allow ⇒ 判据红。
- **AC-06**：尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 23 项绿；治理 `validate.py` 绿
  （PLAN 与 ALL_PLAN **同提交**——cycle 5 的 CI 教训）。
- **AC-07**：**不放松任何边界**：`policy.yaml` / capabilities / acceptance 语义 / 生命周期
  决策处理均**零改动**（`git diff` 可核）。

## 实施清单

- [ ] **WP-A** ADR-0031 草案（`Status: Proposed`，含 `tool_pack.*` 与"事实名→合约名"两个决策面）
- [ ] **WP-B** `docs/INDEX.md` 权威登记
- [ ] **WP-C** 三处声明面同源收敛 + `DATABASE_SCHEMA.md` 草图名/物理名注记
- [ ] **WP-D** 判据测试（含三条反证签名登记）
- [ ] **WP-E** 尺寸/静态/受影响套件/m0 门禁

## 证据

（执行后回填。）

## 影响报告

（执行后回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 6 建档（EC-06）；只读勘察 12 条事实回填；二选一判定为 **(b) ADR 草案**（(a) 的两种实现都命中 escalation） |
