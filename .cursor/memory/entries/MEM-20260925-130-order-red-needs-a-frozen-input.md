---
id: MEM-20260925-130
title: "顺序红要变成确定性判据：冻结时钟 / 注入环境，把「合并跑红单独跑绿」压成 0.4 秒复现"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-161-cross-suite-isolation-census-and-fix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-163-cross-suite-isolation-census-and-fix.md
supersedes: []
tags: [test-isolation, ordering, deterministic-repro, litellm-dotenv, egress-guard]
---

## 做了什么

2026-09-25 的本地 as-is m0 是 **21/23**，`python/tests` 里的红**只在整轮出现**：

```
FAILED tests/contracts/test_protocol_draft_store_contract.py::test_list_orders_by_recency_and_filters_project
AssertionError: assert ['pdraft_00000001', 'pdraft_00000002'] == ['pdraft_00000002', 'pdraft_00000001']
```

单独跑该文件 9 passed。两件事把「偶发」变成机械事实：

1. **冻结时钟**：`SqliteProtocolDraftStore.create` 用 `now_iso(None)`（真实墙钟，Windows 粒度
   约 15.6ms）⇒ 两次 create 可能拿到**同一个** `created_at`。探针把
   `adapters.sqlite.protocol_draft_store.now_iso` 换成常量、`InMemoryProtocolDraftStore` 用
   `clock=lambda: 同一时刻`、PostgreSQL 用参数绑定的 UPDATE 把两行钉到同一时刻 ⇒
   **三个实现同时 RED**（0.34s）。根因随之明确：`ORDER BY created_at DESC, draft_id`
   的 tie-break 是**升序**，与「按新近」相反；InMemory 的稳定排序同样退化为插入序。
2. **注入环境**：同一条 `python/tests` 里的另一类红是出站判据的整轮红灯，点名
   `198.18.0.83:443` 由 `test_start_run_unprovisioned_control_plane_reports_actionable_failure`
   发起。把 `LLM_MAIN_KEY=<任意值>` 放进环境后**单独跑该文件**即可复现（**2.24s**，替代
   569s 全量）⇒ 根因是 `litellm` **导入期**的 `load_dotenv()` 把 gitignored `.env` 注入进程
   环境，使「未配置控制面」的 hermetic 用例真的去探出厂端点。

**一处承继记录的事实更正**：此前把那条出站红灯归因为「本机 fake-IP DNS 特殊 ⇒ 环境项」。
实测口径是：`tests/egress_guard.py` 的放行面只有 `localhost`，任何**可解析**的非环回目的地
都会被拦并判红；本机 DNS 只是让 `kind` 显示成 `private`。**凭据在场**才是红的原因
（CI 无 `.env` ⇒ 不可解析 ⇒ 不探端点 ⇒ 全绿）。分类因此是「真实缺陷（测试隔离）」，
处置是**修隔离**，不是登记为环境项、更不是豁免 fake-IP 段。

## 为什么这样做

「合并跑红、单独跑绿」用「再跑一遍看看」是**无法收口**的：读到的绿可能只是时钟运气，
读到的红也没有可对照的判据。把触发条件**显式构造**（同刻时钟 / 注入凭据键）之后：
修前必红、修后必绿，且复现成本从 ~10 分钟降到亚秒级 —— 这才让「修的是根因」可证明。

## 怎么做与复现

- 预判定性探针（零出网、只读）：`uv run --frozen --no-sync python -B
  scratch/goal015_c1_order_tie_probe.py` ⇒ 逐实现打印 `OK` / `RED`；
  `scratch/goal015_c1_credential_refs_probe.py` ⇒ 列出出厂目录里**有效**的 `credential_ref`。
- 判据（进了默认门，进 CI）：`pytest tests/contracts/test_protocol_draft_store_order_tie.py -q`
  与 `pytest tests/architecture/python/test_default_gate_credential_isolation.py -q`。
- **遇到顺序 / 时序类红时的动作**：先找**共享的可变输入**（时钟、环境变量、共享 DB 行、
  端口、容器），再用「把它固定住」的探针把红做成确定性判据；归因纪律不变——**先枚举来源
  再修**（本轮 21/23 的两条红里，`python/tests` 一条其实由**两个**独立原因叠加而成）。

## 适用边界

- 只适用于**可构造**触发条件的时序红：如果红的来源既不能冻结也不能注入（例如依赖真实
  网络抖动或外部服务），本手法不适用，应按 GOAL-015 EC-02 的口径登记为环境项并附基线对照。
- 冻结时钟的判据断言的是**语义**（全序 / 新近在前），不是某个实现的 SQL 字面量；换实现
  只要语义相同仍应绿。
- 不要把「注入凭据键」当成允许出网：注入的目的是让**隔离**可被检验，判据仍然全拦非环回。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-161-cross-suite-isolation-census-and-fix.md`（WP1–WP5）
- `.cursor/plans/rechecks/RECHECK-20260925-163-cross-suite-isolation-census-and-fix.md`
- `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`（普查表：R-1…R-4 + 历史签名复核）
- 证据：`scratch/goal015-c1-m0-census.log`（21/23 基线）、`scratch/goal015-c1-roundA.log` /
  `-roundB.log`（两轮 `4455 passed`）、`scratch/goal015-c1-press-*`（成对按压）
