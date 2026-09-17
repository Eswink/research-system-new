---
id: MEM-20260915-058
title: "进程内上下文不是续跑能力：重建靠 durable 来源 + 稳定身份，且检查点的输入必须也落盘"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.93
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-083-durable-resume-entry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-083-durable-resume-entry.md
supersedes: []
tags:
  - durability
  - resume
  - canonical-state
  - idempotency-key
  - http-boundary
  - frozen-semantics
---

# 进程内上下文不是续跑能力

## 做了什么

cycle 18/19 让"重排未到期"的失败把 run 停 `PAUSED`，并让本进程的守护线程按时续跑；
cycle 20 的探针（`scratch/goal3-cycle20-probe1-restart-loses-the-plan.py`）量出重启后
**没有任何交付入口**：

```text
收口前（探针实测，scratch/goal3-cycle20-probe1-before.txt）：
        has_paused_context=False / resume_paused 抛 InvalidInputError /
        守护线程派发 0 / durable 只记着断点那条任务，计划里另外 2 条 specs 只在进程内存
收口后（e2e 用例实测，同一条链换真实现：
        tests/e2e/test_restart_rebuild_resume.py；探针脚本写于改造前，
        只能量"现状"，量不了新路径）：run 行记下 protocol_source（路径 xor 草稿修订）
        ⇒ 重建上下文 ⇒ 按 idempotency key 重算剩余工作
        ⇒ run SUCCEEDED、runtime 执行 2 次、断点任务 attempt=2
```

顺带修掉一个真缺陷：**冻结语义 digest 从来没有过 HTTP 边界**（`RunOutcome` 只回填
manifest digest 与定价引用，`run_from_execution` 据此构造 run 实体），于是任何经 API
启动的 run 落库时 `manifest_semantic_digest` 都是 None——而 resume 的漂移校验
（`assert_semantics_frozen`）**只认它**。旧路径走 `resume_paused`（不做漂移校验），
所以这个"永远过不去"的检查点从没被触发过。

## 为什么这样做

1. **续跑能力 = durable 事实 + 重建路径，而不是进程内存**。进程内存里的
   `RunContext` + 剩余 specs 只能证明"这个进程碰巧还在"；重启后要么拒绝（旧行为：
   run 停在那里等人工，且人工也救不了），要么按 durable 事实重建。选后者就必须先把
   **装配来源**落成 canonical 事实——来源可重解析，协议正文副本会漂移。
2. **剩余工作只能按稳定身份重算**。`resolve_sessions` 每次解析都会生成**新的随机
   task id**；引擎按 idempotency key（`run:phase:agent`）去重 ⇒ 拿新 id 去 `acquire_lease`
   只会得到"任务不存在"。所以重建路径先问 `task_identities`（key → task_id → status）：
   已 `SUCCEEDED` 的不重跑，其余换成 canonical task id 再交付。**不新增状态**（"还剩什么"
   由计划 + 任务面推出来，不落第二份 specs 副本）。
3. **检查点的输入必须同样 durable**。漂移校验写得再好，只要它的输入（语义 digest）
   在边界上被丢掉，这个检查就永远不触发——**一个从不开火的守卫等于没有守卫**。
   同类信号：字段名在 JSON 里"看起来在"，但构造实体时没传。
4. **顺序与副作用**：先迁 canonical（`PAUSED → RUNNING`）并**落库**，再续跑——协作式
   暂停谓词读的就是 canonical 状态（cycle 19 的教训）；重建失败时两个入口的诚实口径
   不同：API 面保持"解除暂停、不伪造续跑"（`PAUSED` 是派发面闸门，不该由一次失败的
   续跑重新关上），守护线程把 run 放回停车状态（它一个任务都没执行，留 RUNNING 不实）。

## 怎么做与复现

```bash
python -B scratch/goal3-cycle20-probe1-restart-loses-the-plan.py     # 收口"前"现状（对照见下）
python -m pytest tests/e2e/test_restart_rebuild_resume.py -q          # 4 passed（真 SQLite，收口后）
python -m pytest tests/api/test_run_source_and_rebuild_api.py -q      # 5 passed（HTTP 面）
python -m pytest tests/adapters/sqlite/test_run_protocol_source_and_success_keys.py -q
python -m pytest tests/postgres/test_run_source_and_task_identities_pg.py -q   # PG parity
```

写"跨进程续跑/重建"这类功能的检查清单：① 重建需要哪些输入？每个输入是不是 durable
（能读回来）？② 计划里的工作与已完成的工作靠什么对齐（稳定身份，而不是每次新生成
的 id）？③ 已有的守卫（漂移/一致性校验）的**输入**有没有过边界？④ 状态迁移与副作用
的顺序（谁读这个状态来决定行为）？⑤ 拒绝路径：来源缺失/不可解析/漂移各自说什么，
会不会留下"看起来在跑"的状态？

## 适用边界（踩过的坑）

- **来源消失即拒绝**：协议文件被删或草稿修订不可解析 ⇒ 重建拒绝（不换一份协议）；
  旧 run（早于来源登记）同样拒绝——**不能靠猜协议内容续跑**。
- **`ValueError` 收敛分支仍不落语义 digest**（该 run 已终态 `FAILED`，resume 不可能）；
  `manifest.frozen` 事件 payload 也只带 manifest digest ⇒ 语义 digest 只存在于 run 行。
- **两个入口的拒绝语义不同**（见上），这是有意的：一个是用户请求，一个是后台找活。
- **重建会重跑 preflight**（预留 ref 由 policy+reservations 确定性派生、重复预留是
  同一行的幂等写），因此重建成功后会登记预留引用以便终态释放。
- 相关：[[MEM-20260915-057]]（派发先迁状态且必须可见）、[[MEM-20260915-056]]（终态会把
  声明好的续跑变成孤儿）、[[MEM-20260915-047]]（声明了却没消费者的配置等于谎言）、
  [[MEM-20260915-054]]（退避与它的时钟）。

## 来源

- PLAN-20260915-083 / RECHECK-20260915-083（GOAL-20260915-003 cycle 20）。
