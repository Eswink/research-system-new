---
id: RECHECK-20260918-095
plan_id: PLAN-20260918-095
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-005-cycle3
baseline_ref: dbe4f1f
checked_head: worktree
---

# RECHECK-20260918-095 — 声明未消费项清账（GOAL-005 cycle 3 = EC-03）

## 检查范围

PLAN-20260918-095 声称的交付面：两条「声明了没人读」的处置（`ClaimRequest.lease_ttl_seconds`
移除、示例契约 `failure_policy` 未消费键移除）、两件判据用例、文档同源。

**不在本轮**：`on_validation_failure` 的**消费者**（需要一个 canonical 状态机决策，见 W-3）、
`unhonored` 机制本身、任意用户契约里未知键的行为（机制未动，见 W-4）。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| 反向搜索先于处置 | 全树按名字搜两处声明的**读者与写者** | PASS（`lease_ttl_seconds`：三实现只读引擎级 `self._lease_ttl`、19 个 `ClaimRequest(...)` 构造点无一传它；`on_validation_failure`：只进 `unhonored`） |
| AC-01 请求级字段真的消失 | `grep -rn "lease_ttl_seconds"`（非 `.cursor`，逐条分类）+ 读 port 字段 | PASS（剩余命中 = 引擎构造参数 / 观测白名单 / 文档记录；**无一处**是请求级读或传） |
| AC-01 钉住用例 | `test_claim_request_declares_no_lease_ttl_field` 实跑 | PASS（`dataclasses.fields(ClaimRequest)` 不含该名） |
| AC-02 示例只声明被消费键 | `test_example_contracts_declare_only_honored_failure_policy_keys`（对示例每个契约断言 `unhonored == ()`） | PASS |
| AC-02 用户键仍被点名 | `tests/domain/test_failure_policy_view.py`（未知键进 `unhonored`、不改取值）+ 应用用例（声明 `on_validation_failure` ⇒ 仍 1 次尝试、仍 `FAILED`） | PASS（机制未削弱，用例保留未改） |
| AC-03 文档同源 | `PORTS.md`（M16 增量段）/ `TASK_HANDOFF.md §2.1` / `failure_policy.py` docstring / port `ClaimRequest` docstring | PASS（四处都写"TTL 在引擎级"与"示例只声明被消费键 + 为什么 `on_validation_failure` 没有消费者"） |
| AC-04 反证 | 把移除项放回去重跑对应用例 | PASS（两次各自 **1 red**，红的正是对应钉住用例，见「反证与实测」） |
| AC-05 门禁 | 定向套件 + `framework/validate_bundle` + m0 | PASS（见「门禁」） |
| 未改断言/门禁/快照 | `git diff` 对照 | PASS（改 5 个产品/文档文件 + 2 个测试文件；无门禁、无快照、无 schema 改动） |
| Canonical 边界 | 是否动了状态机/迁移 | PASS（无状态、无迁移、无事件类型改动） |

## 反证与实测

- **反证 ①（请求级字段回流）**：把 `lease_ttl_seconds: int = 300` 放回 `ClaimRequest`
  ⇒ `tests/contracts/test_claim_fencing_contract.py` **1 failed, 18 passed, 9 skipped**，
  失败点 = `assert 'lease_ttl_seconds' not in {...}` ⇒ 钉住用例有判别力。
- **反证 ②（示例契约回流）**：把 `on_validation_failure: DEAD_LETTER` 放回示例契约
  ⇒ `tests/loaders/test_contract_loaders.py` **1 failed, 21 passed**，
  失败点 = `Left contains one more item: 'on_validation_failure'` ⇒ 不变量有判别力。
- **恢复后复跑**：`tests/loaders + tests/contracts/test_claim_fencing_contract.py`
  ⇒ **41 passed / 9 skipped**（树已复原；`git status` 无意外文件）。
- **定向套件**（DSN pin 配方）：
  `tests/api tests/adapters tests/e2e tests/contracts tests/application tests/domain tests/loaders`
  ⇒ **2474 passed / 7 skipped**（355.46s）。
- **未做的验证**：没有为"示例契约少两条键"造端到端 run（示例契约的消费路径由既有 e2e
  覆盖，本次只动声明面）；没有对**外部**调用方（仓库外）做兼容性验证——只能登记为
  兼容性风险（见 PLAN「影响报告」）。

## 告警（W）

- **W-1（观测白名单里同名条目）**：`packages/application/observability/attributes.py:73`
  的 `AttributeKey.lease_ttl_seconds` 仍在。它是**属性键白名单**的允许名，不承诺"有人发它"
  （同表 34 个条目里有 4 个在仓库内未被引用），且白名单由
  `tests/observability/test_m16_vocabulary.py` 以"发射键必须在白名单内"的方式强制 ⇒
  它不是 EC-03 意义上的"声明了没人读"。不在本轮清账范围，登记为观察项。
- **W-2（EC-03 原文的两种读法）**：EC-03 写"若判定「不提供」，则从 port 与三个实现的构造参数
  中移除写明"。本轮按"**移除请求级声明** + **写明引擎级位置**"处置：三个实现的
  `lease_ttl_seconds` 构造参数**是被读的**（claim / `renew_lease` / 过期回收共用同一值，
  `tests/adapters/sqlite/test_dispatch_ownership.py:122` 以 `expires_at == START + TTL` 钉住），
  删掉它是砍真实能力；且 EC-03 的另一分支（"取租路径读请求里的值（**默认仍 300**）"）
  本身就预设引擎级默认存在。判读依据写在 PLAN「反向搜索」与本文，供后续复核推翻。
- **W-3（`on_validation_failure` 仍无消费者）**：本轮只把它从**示例声明面**移除。
  要给真实消费者，必须决定"验收门拒收后如何处置一条已 durable `SUCCEEDED` 的任务行"
  （改写回 `DEAD_LETTER` 或新增终态）——canonical 状态机 + 产品语义决策，属 ADR 边界，
  登记为后继入口（GOAL-005「不进入循环 / 需人工拍板」节）。
- **W-4（判据的射程）**：「无声明了没人读」只覆盖**平台自带声明面**（示例契约 + port +
  文档）。任意用户契约里的未知键仍会被 `unhonored` **点名**而**不生效**——这是设计
  （不猜语义），不是残留；`allow_partial_evidence` 属这一类，本轮按同文件同类一并移除。

## 结论

**PASS_WITH_WARNINGS**。两条「声明了没人读」都已清账，且各自带可判定判据：

- `ClaimRequest.lease_ttl_seconds`：从 port 移除（读者 0、写者 0，全树反向搜索分类核对），
  引擎级 TTL 与能力保留；钉住用例 + 反证（放回去 ⇒ 该用例红）。
- 示例契约 `failure_policy`：`on_validation_failure` 与同类的 `allow_partial_evidence`
  从示例移除，只留被消费的 `on_task_failure: FAIL_RUN`；不变量用例（示例契约
  `unhonored == ()`）+ 反证（放回去 ⇒ 该用例红）。`unhonored` 机制与"用户键仍被点名"
  的既有用例未被削弱。
- 文档四处同源（PORTS / TASK_HANDOFF §2.1 / `failure_policy.py` / port docstring）。

W-1…W-4 是诚实边界：观测白名单同名条目不是同类死声明（W-1）、EC-03 原文的两种读法与
本轮判读依据（W-2）、`on_validation_failure` 的**消费者**仍需 canonical 决策（W-3，
已登记为后继入口）、判据只覆盖平台自带声明面（W-4）。

## 门禁

- `framework/validate_bundle`（单跑）：**验证通过**。
- m0 首跑：**22/23**，唯一红 = `framework/validate`（治理），原因是本 PLAN 当时仍是草稿
  （缺五个章节、未进 `ALL_PLAN`）⇒ 属记录未写完的中间态，不是产品缺陷。
- m0 复跑（补 `## 结论` 章节后，全量）：**PASS: profile=m0; 23 deterministic checks**
  （全量 pytest **3903 passed / 10 skipped**，479.83s；`DOCS-CHECK PASS: 6 deterministic checks`）。
