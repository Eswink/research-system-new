---
id: PLAN-20260920-124
slug: live-failure-path-semantics
title: 失败路径的诚实语义成为可判事实：无效凭据 / 端点拒绝 / 模型不存在三类情形的期望写成判据能核对的事实，并给一条实跑反证（EC-04）
status: IN_PROGRESS
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 4 = EC-04（失败路径的诚实语义）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（live 调用**次数取最小必要**、不重复重跑、不做压测/批量）与第 (2) 条凭据纪律。**本 PLAN 的反证最多发起 1 次真实出站**（用一个**故意无效**的凭据值，inline 前缀注入，不写任何文件），失败即预期结果。不改 Policy/eligibility、不新增依赖、不改 pin、不把凭据写进 CI、不修改任何门禁或断言强度。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260920-124 — 失败路径的诚实语义（GOAL-009 cycle 4 = EC-04）

## 目标

把 EC-04 的三类失败情形从**散文期望**变成**判据能核对的事实**，并给**一条实跑反证**：

1. **无效凭据**：门**只看存在性**（`has()`）⇒ 值无效也**开门** ⇒ 发起调用 ⇒ **明确失败**并落终态、
   **不**静默成功、**不**无限重试。这条「门开但值无效」是本仓**最容易被误读**的语义，必须可判。
2. **端点拒绝**：URL 策略是**门链第一环且先于触网** ⇒ 拒 localhost/环回/私有/保留时
   **零出站**、且**点名策略**；链**短路**（不再派生 health/credential 的拒绝）。
3. **模型不存在**：**明确失败**并落记录、**不**回退到别的模型——需把「run 腿不消费 fallback 列表」
   钉住（本仓**存在** `ModelProfile.fallback` 与 `plan_fallback`，所以这条**不是显然的**）。

## 先探明再动手（只读勘察，2026-09-20）

| # | 事实 | 出处 | 对 EC-04 的意义 |
| --- | --- | --- | --- |
| G-1 | 门只用 `has()`（存在性），**不** `resolve()`；**空值 ⇒ 关门** | `packages/application/model_relay/live_run_gate.py`；`tests/e2e/test_ec04_live_gate_offline.py::test_empty_credential_value_closes_the_gate` | 「无效但非空 ⇒ **开门**」**已由实现推出**，但**没有**任何判据把「无效值 ⇒ 开门」写下来 ⇒ 本 PLAN 要补 |
| G-2 | 端点拒绝**已有强离线判据**：URL 策略先于触网、**零出站**（记录型传输替身计数为 0）、策略放开后替身**确实收到请求**（反证不空转）、链短路、逐条点名 | `tests/api/test_runtime_egress_gate.py`（10 用例，含 `test_denied_url_makes_zero_outbound_calls` / `test_allowed_url_does_probe_so_the_counter_is_not_vacuous`） | **不重复实现**；本 PLAN 只把「三类期望各自有明文」中的这一条**指到**该套件，并核对它**真的**在断言那件事 |
| G-3 | 「门关 ⇒ 零出站」是**结构性**的（门不接 gateway、不构造 URL、不碰 socket） | `live_run_gate.py` 模块文档串 + 同文件的 `mock.patch.object(socket, "socket", …)` 用例 | 同上，**不重复** |
| G-4 | **无模型回退**：`build_llm` 只接收**一个** `ModelDefinition`，`model=` 经 `resolve_runtime_model_name` 变换（**一一对应**，无候选列表）；`num_retries` 来自 `endpoint.max_retries`（示例配置 = **2**） | `adapters/openhands/llm_factory.py`；`examples/config/llm_endpoints.yaml` | 「模型不存在 ⇒ 不回退」在**装配层**成立；须由判据钉住（否则将来有人接上 fallback 也无人知道） |
| G-5 | **fallback 概念确实存在**，但**会话中途不切换模型**（只记录决策与候选） | `packages/application/model_relay/fallback.py` 文档串；`examples/config/model_profiles.yaml`（`research_strong.primary=research_alpha`，`fallback=[reviewer_gamma]`） | G-4 的边界必须**写清楚**：不是「本仓没有 fallback」，而是「**run 的 LLM 装配路径不消费 fallback**」 |
| G-6 | 失败链的读面已经存在：`run.failed` / `task.failed` 事件的 `message` | `tests/e2e/live_run_support.py::run_failures` | 反证的观察面**不必新建**：用既有读面取失败原因 |

## 口径（先写死）

- **门开 ≠ 凭据有效**。门答的是「**能不能发起**」，不是「**会不会成功**」。本 PLAN 把这条写成判据，
  并且**不**把门改成校验有效性（那是行为变更，不在授权内）。
- **反证只发 1 次出站**，且用**故意无效**的值（不是真凭据），因此**不消耗额度**；
  值以 **inline 前缀**注入（`LLM_MAIN_KEY=<故意无效>`），**不写 `.env`、不写任何文件**。
- **失败即预期结果**：本 PLAN 的实跑**期望就是失败**；把失败写成 PASS 或把成功说成失败都违规。
- **「复原」= 无残留**：inline 前缀不落任何文件 ⇒ 复原是**结构性**的（`git status` 空 +
  离线门套件复绿 + EC-01 样本仍在），**不再为此补发一次真实调用**（次数取最小必要）。

## 验收条件

- **AC-1 三类期望有明文**：`docs/integration/LIVE_MODEL_RUNBOOK.md` 新增一节，按**固定标签**
  写出三类情形的期望语义（可被判据按标签解析）。
- **AC-2 无效凭据可判**：判据实测「**非空但无效**的值 ⇒ `has()` 为真 ⇒ 门**开**」，
  并与「空值 ⇒ 门关」成对断言（两条**都在**才算把语义钉住）。
- **AC-3 端点拒绝指到既有判据且核对它在断言什么**：判据核对
  `tests/api/test_runtime_egress_gate.py` 里「零出站」与「反证非空转」两条用例**存在**、
  且**未被 skip/删除**；期望语义行指向该套件。
- **AC-4 无回退可判**：判据断言 run 的 LLM 装配路径**不消费** fallback
  （`build_llm` 只收一个模型；`session_llm_factory` 不查候选列表），
  并断言重试是**有界的**（`num_retries` 来自 endpoint 配置，不是无上限）。
- **AC-5 实跑反证（live，1 次出站）**：用**故意无效**的凭据跑新增的失败路径用例 ⇒ 观察到
  「门开 / 走到**终态** / 失败消息**非空** / usage **未归账** / 消息**不含**注入值」；
  **先红后绿不适用**（本例期望就是失败），因此**换**成「**预置条件式反证**」：
  同一用例在**预置条件不成立**时（未声明失败用例开关）必须 **SKIP 并点名原因**，
  而不是「恰好通过」——由离线判据钉住这条 skip 语义。
- **AC-6 本地门禁绿**：定向套件 + `make validate-all`（m0，CI 同形配置）+ 治理。

## 实施清单

- [ ] WP1 三类期望的明文（AC-1）：runbook 新增 §7，按固定标签写。
- [ ] WP2 离线判据 `tests/architecture/python/test_live_failure_paths_same_source.py`（AC-1/2/3/4/5）。
- [ ] WP3 实跑反证（AC-5）：新增 live 用例（`requires_live_llm`）+ 1 次出站 + 原始观察记录。
- [ ] WP4 复原核对：`git status` 空 / 离线门套件复绿 / EC-01 样本仍可读。
- [ ] WP5 本地验证（AC-6）→ RECHECK → DONE → ALL_PLAN → 回写 GOAL-009 → commit/push/CI。

## 证据

（执行时逐条填入。）

### WP1 期望明文

（待填）

### WP2 判据

（待填）

### WP3 实跑反证

（待填）

### WP4 复原核对

（待填）

## 状态历史

- 2026-09-20 建档：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 4（EC-04）。
  **反证最多 1 次真实出站**，且用**故意无效**的凭据值（不消耗额度、不落文件）。

## 影响报告

**Domain / API / Schema**：**无变化**。不新增/修改域实体、DTO、路由或迁移；本 PLAN 只新增
**判据**、**一条 live 用例**与**文档明文**。

**安全 / 凭据**：**无新增信任面**。反证用**故意无效**的值（非真凭据），inline 前缀注入、
不落任何文件、不回显、不进日志；判据另行断言「失败消息**不含**注入值」（这正是本仓
最该被钉住的泄漏面）。**默认 deny 姿态不放松**：不打开 localhost、不放宽 URL 策略、不改 Policy。

**兼容性 / 迁移风险**：无迁移。**风险**：新增 live 用例若在无预置条件时**不 skip**，
未来操作者跑整个 live 套件会撞上一个「期望失败」的用例 ⇒ 处置是**预置条件式开关**
（未声明即 SKIP 并点名），并由判据钉住该 skip 语义；**不得**为了让套件全绿而让它恒过。

**上游版本影响**：无。不新增依赖、不改任何 pin。

**下一项任务**：WP1 明文 → WP2 判据 → WP3 实跑反证 → WP4 复原核对 → WP5 收口并回写 GOAL-009 的 EC-04。
