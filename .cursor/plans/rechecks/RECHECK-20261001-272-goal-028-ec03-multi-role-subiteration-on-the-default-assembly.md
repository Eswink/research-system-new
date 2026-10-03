---
id: RECHECK-20261001-272
slug: goal-028-ec03-multi-role-subiteration-on-the-default-assembly
title: GOAL-028 EC-03 复检 — 真实多 role 协议在默认装配上跑到终态（五件事逐条）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-01
updated_at: 2026-10-01
plan_id: PLAN-20261001-271
parent_goal: GOAL-20261001-028
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261001-271`（GOAL-20261001-028 的 cycle 3 子计划）——把 **真实那条**多 role 协议
（`multi_role_research_v1.yaml`：run-chain 检索 → 沙箱实验 → 带质量门的评审）从
「只在测试装配（`map_tools=True`）能跑」推进到「**默认装配下跑到 `SUCCEEDED`**」。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **默认装配实跑**到 `SUCCEEDED`（非 `map_tools=True`） | **PASS** | `test_the_run_reaches_success_and_every_phase_is_checkable`：走 `build_agent_runtime` 的真实缺省 + `register_session_tools` 注入实现 ⇒ `state=SUCCEEDED`、`protocol_id=multi_role_research_v1_0_0`、`manifest_digest` 在场、**失败列表里没有 `is not registered`** |
| AC-2 | **四相位产出逐条可复核**（真标识 / 真 metrics / 评审反证 / 读面四列 / Handoff digest） | **PASS** | ① `source_trust_label` 集合 == `{RETRIEVED}` 且拼接串含真 PMID（`39284801` / `40601758` 至少一条）；② 实验 `image_digest` 在场 + `metrics` 制品在；③ 反证臂：摘掉检索接线 ⇒ run `FAILED` 且判词点名 `retrieved sources`，且工具证据列表为空；④ 四列（`id` / `source_ref` / `content_digest` / `source_trust_label`）逐条非空；⑤ `handoff_digests()` 三条 `sha256:<64hex>` 且互不相同 |
| AC-3 | 既有判据**逐字节未改**且全绿 | **PASS** | `git diff` 对 `test_multi_role_research_offline.py` / `test_ec03_real_runtime_offline_chain.py` / `test_tool_binding_on_the_default_assembly.py` / `tests/application/preflight/` / `egress_guard.py` / `run_fixtures.py` / `test_session_tool_bindings_exposure.py` **均为空**；连同新判据 **10 passed** |

**协议改动是纯新增**：`examples/protocols/multi_role_research_v1.yaml` **+12 行 / −0 行**
（`git diff --stat` 实测 `1 file changed, 12 insertions(+)`）—— 只加 `session_tool_bindings`
与它的注释；phase 的 `id` / `role` / 能力 / 契约 / 输出 / 门 / 超时**一字未动**。

## 按压（先红后绿 + 逐字节复原）

| 编号 | 做法 | 结果 | 复原取证 |
| --- | --- | --- | --- |
| P-3 | 从协议删掉 `europe_pmc` 那条绑定声明 | **3 failed**，主判据的失败文本正是 **`ToolDefinition 'europe_pmc' is not registered`**（且覆盖断言抓到 `europe_pmc` 未绑） | 恢复后 `sha256sum -c` 逐字节一致（`multi_role_research_v1.yaml` = `3134b3c8…`）；连同既有判据 **10 passed** |

## 复检发现（一处初始误判，已按实测纠正）

**首版只绑三条 ⇒ `europe_pmc` 未绑（真问题，判据抓到）**：我起初以为 review 的会话工具面
不含 `europe_pmc`（它被 scouting 声明为 run-chain）。实测纠错：**run-chain 排除是
per-phase 的**（`run_chain_tool_ids(plan, phase.id)` 只对**声明了** `run_chain` 的那个 phase
生效）⇒ 在 review 这一相位，`europe_pmc` **仍在会话工具面内**，必须绑定。
这是 EC-01 声明面的语义（`face = 冻结集 − 本 phase 的 run-chain 排除`）在真实协议上的第一次
应用，判据的覆盖断言把它当场抓住。

**一处判据分流（如实登记，不是放宽）**：绑定覆盖断言只对 **`strategy: single_agent`** 的
phase 成立。`experiment` 是 `deterministic` 且合约声明 `experiment: {}` ⇒ 派发按
`phase_runner` 的既有语义（`contract.experiment is not None` ⇒ `dispatch_experiment`）
**根本不创建会话** ⇒ 它的会话工具面**从不被消费**，对它要求绑定会给协议加一行没有语义的声明。
判据另断言「本协议**恰有一个**带会话面的 phase」以防分流过宽（空真）。

## WARNINGS（逐条登记，本 EC 不消解）

- **`W-1`｜会话工具的实现是判据侧的惰性桥**：生产组合根**不**自带「工具名 → 实现」的表
  （承 EC-01 `W-1`）⇒ 本判据以装配方身份注入。**含义**：证的是「默认装配路径下链路成立」，
  不是「出厂即可跑」——出厂要跑仍需装配方接线。
- **`W-2`｜`experiment` phase 的会话工具面不被消费**：见上「判据分流」。若将来该 phase 改
  走会话，绑定需要同轮补（判据的分流条件会随之失效并判红 ⇒ 有守卫）。
- **`W-3`｜惰性桥不驱动模型调工具**：本判据证「会话起得来 + 链路产出可复核」，**不**证
  「模型会正确调用这些工具」——后者属会话语义，不在本 GOAL 射程。
- **`W-4`｜真标识来自离线夹具**：`39284801` / `40601758` 是真实发表记录（2026-09-30 实取），
  但经 `httpx.MockTransport` 注入 ⇒ 证的是**解析与取证链**，不是「今天上游可达」
  （真实出网属 EC-02 `W-1`）。
- **`W-5`｜实验段依赖 Docker**：判据挂 `requires_docker`，非 Linux 容器守护进程下如实 skip
  （由 `container-quality` 作业真跑）。

## 未覆盖范围（承继，逐条在位）

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 外部队列只在登记面；
5. **`R-M1` 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称
   项目安全。

**可靠性口径**：本 EC 不涉及投递语义；本仓**明确否认**「恰好一次」，口径只能是
at-least-once + idempotency + deduplication。

## 结论

GOAL-20261001-028 的 **EC-03 达成**：**真实那条**多 role 协议在**默认装配**（生产组合根的
真实缺省，非测试后门）下跑到 `SUCCEEDED`，五件事（真标识 + `RETRIEVED` / 真 metrics /
评审真能判拒 / 读面四列 / Handoff digest 序列）逐条可复核；协议改动**纯新增 12 行**；
既有判据逐字节未改。五条 `W-NN` 如实登记。

**本地门终态**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24 / `FAILED [` = 0 /
EXIT=0 / **4974 passed / 21 skipped**；日志 `scratch/goal028-c3b-m0.log`，记录写入后独占运行、
canonical DSN pin、不接管道、零进程残留）；治理 `validate.py` 绿；记录面判据 19 passed。

**本地门首跑抓到 3 条（`python/tests`）—— 全是我自己 cycle 1 的判据，已同轮重新分类**：
`tests/e2e/test_tool_binding_on_the_default_assembly.py` 与
`tests/architecture/python/test_session_tool_bindings_exposure.py` 的 `_UNDECLARED` 清单里
钉着「`multi_role_research_v1` **不**声明绑定」—— 而本 EC 的授权协议改动**正是**给它加绑定。
处置：该协议从 `_UNDECLARED` **移入** `_BOUND`，并新增 `_EXPECTED_DECLARED` 把两个协议的
期望声明**逐字**写死（文档改一个字即红）；`_UNDECLARED` 余下三份协议仍钉「未声明 ⇒ 空」。
**没有放宽任何断言**：判的仍是同一件事（「没声明就逐字不变」），只是把一份**按授权改了声明**
的协议从「没声明」那一侧移到「有声明」那一侧。
