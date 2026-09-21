---
id: RECHECK-20260921-127
plan_id: PLAN-20260921-127
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-21
completed_at: 2026-09-21
reviewer: root-agent-goal-010-ec01
baseline_ref: 17cef9b
checked_head: 49ed9c3
---

# RECHECK-20260921-127 — 真实交付物契约（GOAL-010 EC-01）

## 检查范围

**不采信实施叙述**：从 EC-01 的**原始验收条件**重新核对——「一次真实 run 在**真实执行体**下
**验收门 PASS** 且终态**恰为 `SUCCEEDED``」+「反证：删掉映射/契约 ⇒ 回到 REJECT」+
「**禁止**放宽验收判据使其通过」+「**禁止**用 Fake 结构化输出伪造成功路径」。
逐条核对：live 证据、反证的成对性、验收门与相关门禁**未被修改**、本地全量门禁、凭据纪律。

## 检查结果

### 1. EC-01 的判据本体：真实 run 到 `SUCCEEDED`（**实跑**）

判据文件 `tests/e2e/test_real_deliverable_contract_live.py`（`plan` 新增），
以**单条命令内联前缀**开门（`set -a; . ./.env; set +a` 后
`RESEARCHOS_AGENT_RUNTIME=openhands`），跑前自检
`EnvCredentialResolver().has('LLM_MAIN_KEY')` ⇒ **True**（只问存在性，未物化值）。

| 次 | 结果 | 证据 |
| --- | --- | --- |
| 第 1 次 | **`1 passed`**（32.92s） | 判据三条全中（终态 / 无失败 / 交付物按声明名）；`tmp_path` 未保留，**无 run id** |
| 第 2 次（`--basetemp=scratch/ec01-live`，为**取回记录**） | **`1 passed`**（42.70s） | 落盘 `scratch/ec01-live/*/ec01-live-contract.json` |

**记录（第 2 次的落盘原文）**：

```json
{
  "run_id": "f1710564-855c-43f7-9fdd-84966a878cf9",
  "state": "SUCCEEDED",
  "failures": [],
  "artifact_ids": [
    "14081ebd-0171-444b-ac79-c45f7a07f153:analysis_report",
    "f9358b3d-0f34-487f-bb1d-bcdd56a4a21e:analysis_report"
  ],
  "deliverable_id": "14081ebd-0171-444b-ac79-c45f7a07f153:analysis_report",
  "declared_artifact": "analysis_report",
  "fact_name": "session_message",
  "contract_id": "console_demo_deliverable"
}
```

**与 GOAL-009 的对照（这是本 EC 要跨过的那一步）**：GOAL-009 EC-01 在同一路径上的终点是
`FAILED`（run `142f7e77-…`，制品后缀 `:session_message`，失败消息点名 acceptance gate）。
本次**终态恰为 `SUCCEEDED`**、`failures` **为空**、两件制品都以 **`:analysis_report`** 结尾
——**名字来自合约声明**（`declared_artifact = analysis_report`），**事实名仍被登记**
（`fact_name = session_message`）。

**门 PASS 是怎么判出来的（把推断的强度写清楚）**：本判据用「终态 `SUCCEEDED` +
`failures` 为空 + 交付物按声明名登记」三条判定，**没有**逐条读回 criterion 的 reason 文本
（它们活在该次进程内的 review finding 里，进程结束即消失——与 GOAL-009 W-2 同一类限制）。
「门 PASS」是**从代码路径推出**的：`task_phase_helpers.register_and_gate` 在
`evaluate_gate` 返回 `None`（未通过）时必然写 `failure_step("… rejected by acceptance gate")`
⇒ run `FAILED`；反之 `SUCCEEDED` 且无该消息 ⇒ 门**通过**。同一蕴含关系在离线链用例
（`test_real_runtime_offline_chain_segments` 与 `…_rejects_a_non_unique_declaration`）上
**两个方向都被实跑钉住**。见 W-1。

### 2. 反证成对（**两次压测，四次观察**）

| # | 压测对象 | 改动 | 观察 | 复原 |
| --- | --- | --- | --- | --- |
| ① | 链级（WP4） | `declared or _FACT_NAME` ⇒ `_FACT_NAME` | **PASS 分支 RED**：制品回落 `:session_message`、run `FAILED`、失败消息含 `rejected by acceptance gate` | 复原 ⇒ GREEN |
| ② | 链级（WP4） | `len(declared) == 1` ⇒ `declared` | **REJECT 分支 RED**：adapter 猜了 `analysis_report`，`_assert_events_mapped` 的后缀断言命中 | 复原 ⇒ GREEN |
| ③ | 判据级（WP3） | 同 ② | **`test_a_non_unique_declaration_is_not_guessed` RED**（消息把合约原样打出来） | 复原 ⇒ GREEN |
| ④ | 判据级（WP3） | 把文档里「回落事实名」的措辞改弱 | **`test_the_read_face_documents_the_provenance_fields` RED** | 复原 ⇒ GREEN |

**压测后 `git diff` 只剩意图内改动**（四次压测的改动全部撤回，未留在提交里）。
⇒ EC-01 的「删掉映射/契约 ⇒ 回到 REJECT」**成立**，且「不猜」边界**也是**被压过的判据。

### 3. 验收判据**未被放宽**（独立取证，不采信叙述）

| 检查 | 方法 | 结果 |
| --- | --- | --- |
| 验收门判定语义未改 | `git diff 17cef9b..49ed9c3 -- packages/domain/acceptance.py` | **空** |
| 合约未被改成迁就现状 | 同上，`-- examples/contracts/task_contracts.yaml` | **空**（`ARTIFACT_EXISTS: analysis_report` 原样） |
| ADR-0031 结构判据未被修改 | 构造判据时读了它的**断言本体**：第 4 条判的是 `evaluate_criterion` 的**字面匹配**（`CriterionInputs` 由用例**手工构造**、不经过 adapter）⇒ D2-A 形态（门不改、声明侧给名字）下它原样保持绿 | `git diff` 对该文件 **空**；该文件 **10 passed** |
| 既有判据未被削弱 | 离线链由**单分支**改为**双分支**：`_assert_deliverable_adjudicated` 拆出共用的 `_assert_deliverable_landed`，**新增** `_assert_deliverable_rejected` 与新用例 | 判据**只增不减**；GOAL-009 的判据拒绝证据**被保留**为反证分支 |
| 新增判据不与被测实现循环论证 | 链级与判据级都用**字面量** `analysis_report` / `session_message` 断言，**不** import adapter 的 helper 当判定依据 | 见两处 docstring 与断言本体 |

**整份 PLAN 的改动面（`17cef9b..49ed9c3`，11 个文件）**——逐项核对「没动不该动的」：

```
M .cursor/plans/ALL_PLAN.md                              M docs/adr/ADR-0031-toolpack-capability-policy.md
M .cursor/plans/goals/GOAL-...-010-...md                 M docs/architecture/AGENT_RUNTIME.md
A .cursor/plans/tasks/PLAN-20260921-127-...md            M docs/integration/LIVE_MODEL_RUNBOOK.md
M adapters/openhands/runtime_adapter.py                  M docs/integration/OPENHANDS_ADAPTER.md
A tests/architecture/python/test_real_deliverable_contract_same_source.py
M tests/e2e/live_run_support.py                          M tests/e2e/test_ec03_real_runtime_offline_chain.py
```

**`packages/domain/acceptance.py`、`examples/contracts/task_contracts.yaml`、
`tests/tooling/test_toolpack_capability_policy_pending.py` 三者在整个 PLAN 范围内
`git diff` 均为空**——「验收门没被改、合约没被改、ADR 结构判据没被改」是**可复查的事实**，
不是本文件的声明。

### 4. 本地全量门禁

```
PASS: profile=m0; 23 deterministic checks
4271 passed, 14 skipped, 64 warnings in 526.66s   (exit 0, FAIL 0)
```

（CI 同形配置：`RESEARCHOS_POSTGRES_DSN` pin 到测试 DSN + 另三个 DSN 键置空 +
`LLM_MAIN_KEY=""` 复现 CI 的「无凭据」条件。新 live 判据在 m0 中如实显示为 `s`
——**CI 保持离线**。）

定向：`tests/architecture tests/tooling tests/e2e` ⇒ **1345 passed / 5 skipped / 1 failed**
（该红 `test_pg_crash_restart` 是**未 pin DSN** 的环境签名，pin 后 m0 全绿；见 W-3）；
治理 `validate.py` 绿；`DOCS-CHECK PASS: 6 deterministic checks`。

### 5. 凭据纪律

- 内联前缀跑完**未留在环境**、**未写进 `.env`**（`grep -c '^RESEARCHOS_AGENT_RUNTIME' .env` ⇒ `0`；新 shell `env` 里 ⇒ `0`）。
- **被跟踪文件里命中凭据值的个数 = 0**（扫描 `git ls-files` 全量文件按值比对，**只输出命中数，未打印值**）。
- 本 RECHECK 与 PLAN/GOAL 的记录里**没有**凭据值或片段。

## Warnings（不阻断，如实登记）

- **W-1 「门 PASS」是代码路径推出的蕴含关系，不是直读 criterion 文本。** 判据用「终态
  `SUCCEEDED` + `failures` 为空 + 交付物按声明名」三条判定；逐条 criterion 的 reason 活在
  该次进程内的 review finding 里，进程结束即消失。该蕴含关系在 **`task_phase_helpers`** 里
  是确定的（未过门 ⇒ 必写 `rejected by acceptance gate` ⇒ `FAILED`），且**两个方向都在离线链上
  被实跑钉住**——但「EC-01 verify 里那句『逐条 criterion reason 一并登记』」本 cycle **没有**
  逐条登记，如实登记为缺口。
- **W-2 真实调用共 **2** 次**（都是同一判据、同一形态、都 `SUCCEEDED`）。第 2 次的**唯一**目的是
  取回 run id 与判据记录（第 1 次写进了会被清理的 `tmp_path`）。**只算一次会更好**——
  那需要判据在第一次就写到可保留的位置；本轮是「先跑通、再补记录」，**如实登记**。
- **W-3 定向跑的那条红是环境签名，不是回归。** `tests/e2e/test_pg_crash_restart.py`
  在**未 pin 测试 DSN** 的组合里红（`.cursor/memory/` 的 `m0-gating-dsn-pinning` 已逐条登记
  这一族），pin 后 m0 全绿、单跑该文件通过。同族另有 3 条 `worker_plane_composition` 与 1 条
  **凭据可得性**用例（`RECHECK-20260920-121` W-7），本轮**未重复**它们的最小复现
  ——上一次复现**真的发起过一次出站**，而这正是 GOAL-010 **EC-05** 尚未处理的残余。
- **W-4 EC-02 未被本 cycle 触及：这次成功 run 的证据链**仍然**由模型自述满足**。
  `EVIDENCE_COVERAGE ≥ 1` 数的是**从同一次会话输出派生**的 evidence（`TrustLabel.GENERATED`），
  即**交付物自己**。本 cycle 让 run 成功了，但**没有**让「证据来自真实可查来源」成立——
  这正是 EC-02 的存在理由，**不得**读成本 EC 已顺带解决。
- **W-5 (i) 路径未被验证。** 取 (ii)（声明化命名）⇒「让模型自己产出合约声明的键名」这条
  路径**没有**被验证过。这是选择的代价，不是缺陷；若将来要用 (i)，需要新的判据与样本。
- **W-6 前端读面未被判据把守。** 本 cycle 未改 DTO/路由/前端，因此**未触**快照类门禁；
  但 `ModelCatalogTable` / `ModelDetails` / `ModelInspector` 的 `endpoint_id` 渲染
  （`RECHECK-20260920-122` W-5）**仍然**没有判据。属 GOAL-010 的残余，未处理。
- **W-7 单次「成功」的证明力边界。** 两次 `SUCCEEDED` 说明**这一次**契约被满足；
  它**不**证明真实模型**稳定**产出可用的交付物（交付物内容仍是自由文本，
  `ARTIFACT_EXISTS` 只判**存在**、不判**内容是否合格**）。按 AGENTS.md §4 的口径，
  可重复性结论**只能**停在这里。
- **W-8 CI 台账**：见 GOAL-010 的台账表；**未跑到终态的不记**。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01 达到终态：**真实 run 首次走到 `SUCCEEDED`**
（run `f1710564-855c-43f7-9fdd-84966a878cf9`，`failures` 为空，两件制品都按合约声明的
`:analysis_report` 登记，事实名 `session_message` 仍被登记）；**判据没有放宽**——
`packages/domain/acceptance.py` 与示例合约的 `git diff` 均为**空**，ADR-0031 的结构判据
**零改动且 10 passed**；**反证成对且被压过四次**（链级两个方向 + 判据级两条），
每次压测后复原、`git diff` 只剩意图内改动；离线链由单分支改为**双分支**，
GOAL-009 的判据拒绝证据**被保留**而非删除。PLAN-20260921-127 可置 **DONE**
（WP3/WP5 已补做，见本文件 §1–§3）。

**Warning 不阻断的理由**：W-1 是**如实说明证据的强度**（蕴涵关系 vs 直读文本）、
W-2 是**调用次数的如实登记**（2 次，第 2 次为取回记录）、W-3 是**已定性的环境签名**、
W-4/W-5/W-6 是**明确划出的射程边界**（EC-02 未触及、(i) 路径未验证、前端无判据）、
W-7 是**证明力边界**、W-8 是台账填写规则——**没有一条是被掩盖的失败**。
**全程未改任何门禁/断言强度、未放宽验收判据、未新增依赖、未改 pin、未改默认 runtime、
未把凭据写进 CI。**
