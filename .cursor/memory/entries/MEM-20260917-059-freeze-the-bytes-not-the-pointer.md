---
id: MEM-20260917-059
title: "冻结就冻结被解析的那份字节：来源自足靠 run 行；时钟混用的用例是定时炸弹"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-084-freeze-protocol-body-into-run.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-084-freeze-protocol-body-into-run.md
supersedes: []
tags:
  - durability
  - resume
  - canonical-state
  - frozen-semantics
  - test-clock
  - value-object
---

# 冻结就冻结被解析的那份字节

## 做了什么

cycle 20 的重建入口按 `protocol_source` 重新解析（文件或草稿修订），于是"重启后能续跑"
依赖那份外部文件还在（RECHECK-083 W-3 已如实登记）。本轮把**被解析的那份正文**连同
sha256 冻结进 run 行（`ProtocolBody` 值对象 + `ResearchRun.protocol_body`），重建只认它：

```text
启动：read_protocol_text(path) → load_protocol_from_text(text) → ProtocolBody.of(text) 入 run 行
重建：run.protocol_body → parse_frozen_protocol → compile/preflight → assert_semantics_frozen
实测：外部文件删除后 POST /runs/{id}/resume ⇒ continuation=REBUILT（修复前：NONE + "protocol file not found"）
```

## 为什么这样做

1. **"来源"与"内容"是两件事**：来源（路径/修订号）是**指针**，指针可以悬空；续跑需要的
   是**内容**。只冻结指针等于把可用性押在外部世界的稳定性上。冻结内容后，指针退化成
   审计信息（这份 run 从哪来），而不是可用性前提。
2. **冻结的必须是"被解析的那一份"**：先读文本、再从这段文本解析、再把同一段文本入行，
   启动与重建才对**同一份字节**解析。分两次读（"解析用文件、冻结再读一遍"）会留一个
   "解析了 A、冻结了 B"的窗口——这类不一致不会立刻报错，只会在重建时变成漂移。
3. **不变量要由值对象兜住**：`ProtocolBody(text, digest)` 构造时校验
   `sha256(text) == digest`，空正文拒绝 ⇒ 被改过的正文**构造不出来**，而不是等重建时
   才发现。真相仍然只有一条守卫：语义 digest 校验（换一份自洽的正文 ⇒ 拒绝）。
4. **拒绝原因要点名缺的是哪条事实**：有冻结正文时"文件不在"不再是拒绝理由；没有正文时
   拒绝必须同时说清"没有冻结正文"与"来源为什么解析不出来"，否则运维只能猜。

## 怎么做与复现

```bash
python -m pytest tests/domain/test_protocol_body.py -q                     # 值对象不变量
python -m pytest tests/api/test_run_source_and_rebuild_api.py -q           # HTTP：文件删除后仍重建
python -m pytest tests/e2e/test_restart_rebuild_resume.py -q               # 真 SQLite：断点语义不变
python -m pytest tests/postgres/test_run_source_and_task_identities_pg.py -q  # PG parity
tools/gen_openapi.py   # 动了 DTO 就要重生成快照（契约测试会红）
```

## 适用边界（踩过的坑）

- **语义 digest 覆盖 `run_id`**：把一条 run 的冻结事实"挪"到另一个 id 上，重建必然被判
  漂移。测试里想构造"停车后的同一条 run"，必须**保留原 id**——换 id 不是"这条 run 停车"，
  而是"另一条 run 声称自己有别人的冻结语义"。
- **混用两个时钟的用例是定时炸弹**：PG 退避用例注入固定引擎时钟（`now=lambda: START`），
  却用 SQL `now() - interval '1 second'` 去挪 deadline。墙钟越过 START 之前它一直绿，
  越过之后**必然红**（与产品行为无关）。修法是让夹具用**引擎自己的时钟**写那条 deadline；
  断言一个字没改（GOAL-004 建档轮 CI 就是这么红的）。
- **"没有剩余工作"的重建会退化成"重跑全部"**：`resume_rebuilt` 把剩余 specs 传成空元组时，
  执行体里 `ctx.pending or ctx.resolve_sessions()` 会把空元组当成"没提供"，于是重新解析
  全量 specs 并再次投递已完成的任务 ⇒ 与证据/claim 面冲突 ⇒ run 收敛 `FAILED`
  （RECHECK-084 W-2）。要重跑一条跑完的 run，必须在产品语义上先回答"没有剩余工作"该
  收敛到什么状态。
- 旧 run（早于正文冻结）`protocol_body` 为空 ⇒ 仍走来源解析，行为不变（不伪造、不推断）。
- 相关：[[MEM-20260915-058]]（进程内上下文不是续跑能力）、[[MEM-20260915-047]]（声明了
  却没消费者的配置等于谎言）、[[MEM-20260915-049]]（"存在"不等于"可解析"）。

## 来源

- PLAN-20260917-084 / RECHECK-20260917-084（GOAL-20260917-004 cycle 1 = EC-01）。
