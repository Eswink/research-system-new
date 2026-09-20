---
id: MEM-20260920-095
title: "一条 hermetic 用例其实对「凭据是否可解析」不封闭：前序模块 import 过 litellm ⇒ .env 凭据入进程 ⇒ 目录端点真的做发现（真实出站），run.failed 消失 ⇒ 全量 m0 单条红；CI 无凭据故不可复现"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md
supersedes: []
tags:
  - m0
  - gating
  - dotenv
  - credential
  - hermetic-test
  - egress
  - goal-009
---

# 「凭据可得性」会改变号称 hermetic 的用例行为（GOAL-009 cycle 1）

## 做了什么

在 GOAL-009 cycle 1 跑全量 m0 时拦下 **1 红**（`python/tests`），用**反证**把它定位到
「**凭据是否可解析**」这个环境维度上——而**不是**我最初的假设（DSN 钉定）。顺带证明了一条
**安全相关**的事实：**本地门在「离线」的名义下会发出真实请求**。

## 现象

- 全量 m0：**22/23**，唯一红项是
  `tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
  （`assert failed, events` ⇒ `[]`，即没有任何 `run.failed` 事件）。
- 该用例的 captured log 里有**真实的**
  `GET https://apihub.agnes-ai.com/v1/models "HTTP/1.1 200 OK"`。
- 该用例**单独跑**必然通过；只有在「前序模块 import 过 openhands-sdk」之后才红。

## 为什么这样做（根因）

1. **不封闭的是一个「凭据」维度，不是 DSN 维度。** 该用例自称 hermetic，清了
   `DATABASE_URL` / `RESEARCHOS_DATABASE_URL` / `POSTGRES_DSN` 三个键，**但没有任何机制
   隔离凭据**。openhands-sdk → litellm 在 import 时 `load_dotenv()`（向上找到仓库根 operator
   `.env`，override=False ⇒ **只设缺席键**），于是 `LLM_MAIN_KEY` 进入进程并被
   `EnvCredentialResolver.has()` 判为可解析。
2. 目录里 `main` 端点的 `discovery.enabled: true` ⇒ 控制面**真的发起端点发现**；
   发现成功后控制面状态改变 ⇒ 同一条 run 走到 `FAILED` 却**不再产出 `run.failed` 事件**
   ⇒ 断言拿到空集。
3. **顺序敏感**：没有前序 import 时 litellm 还没加载、凭据还不可解析，用例就走它自己的
   hermetic 路径并正常通过。

## 怎么做与复现

```bash
# 红：前序 import 过 openhands ⇒ 凭据可解析 ⇒ 真实发现 ⇒ run.failed 消失
uv run --frozen --no-sync python -B -m pytest tests/adapters/openhands \
  "tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure" -q
# ⇒ 1 failed, 83 passed，且日志里出现 GET https://apihub.agnes-ai.com/v1/models "200 OK"

# 绿（决定性反证）：键存在且为空 ⇒ litellm 的 load_dotenv 不覆盖 ⇒ 凭据不可解析
LLM_MAIN_KEY="" uv run --frozen --no-sync python -B -m pytest tests/adapters/openhands \
  "tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure" -q
# ⇒ 84 passed，且没有任何出站记录
```

⇒ **红 ⇔ 凭据可解析**。**CI 两样都没有**（无 `.env`、无凭据；`quality-*` job 只设
`PYTHONUTF8` / `PYTHONIOENCODING`）⇒ **该红在 CI 上不可复现**。

**被自己推翻的中间假设（一并记住，免得再踩）**：第一轮之后曾把它归给「为让 `tests/postgres`
连库而钉的 test DSN 活过了该用例只清 3 个键的 hermetic 守卫」。**换成空 DSN 复跑仍红 ⇒ 该假设
不成立**，DSN 只是改变了 postgres 用例的 skip 计数（12 → 204），红项不变。
**教训**：`pytest` 的单条红在「换个环境配置还是红」之前，别急着宣布根因。

## 适用边界

- **适用于**：全量 m0 出现「单条、看似无关、单独跑就绿」的红时，把**凭据可得性**列为待验维度；
  评估「开发机上有可用凭据」对所谓离线门的影响（它会让门**替你真调用**）。
- **不适用于**：断言产品代码有缺陷。本轮**只改文档与记录**（无产品代码改动），且反证显示
  红项随凭据出现/消失——**不是**产品路径的回归。
- **未处置（如实登记）**：该用例对凭据维度不封闭、且顺序敏感；**未修**（跑测试改测试、
  改 hermetic 守卫不在本 cycle 射程内）。「有凭据时本地门会出网」作为**残余**跟进。
  相关：[[MEM-20260908-017]]（DSN 钉定配方）、[[m0-gating-dsn-pinning]]。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md`（GOAL-009 cycle 1 = EC-01）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md` 的 **W-7**
  （三轮 m0、被推翻的中间假设、最小复现、决定性反证、真实出站）
- 目标：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
- 既有同族记忆：`.cursor/memory/entries/MEM-20260908-017-litellm-dotenv-gating.md`
