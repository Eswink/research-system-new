---
id: PLAN-20260917-084
slug: freeze-protocol-body-into-run
title: 来源自足续跑：协议正文冻结进 run 行，重建不再依赖外部文件
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 1 = EC-01（承接 GOAL-003「终止与收口 · BLOCKED 记录（2026-09-18）」后继入口第 2 项 / RECHECK-20260915-083 W-3）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-084-freeze-protocol-body-into-run.md
memory_entries:
  - MEM-20260917-059
---

# PLAN-20260917-084 — 来源自足续跑（GOAL-004 cycle 1 = EC-01）

## 目标

cycle 20 让"重启后按来源重建续跑"成为真实能力，但重建的输入是**外部文件**
（路径来源读 `examples/protocols/<path>`；草稿来源读草稿库修订行）。来源可解析是重建的
前提，来源消失即拒绝——这是诚实的边界，但意味着"重启后能续跑"依赖那份文件的可获得性，
不是纯自足（RECHECK-083 W-3 已如实登记）。

本轮把**重建的输入**从"外部文件的当前内容"改成"run 行里冻结的那份正文"：

1. 启动时把**被解析的那份协议正文**连同其 `sha256` 冻结进 run 行（canonical 事实）；
2. 重建时优先用冻结正文重装配——外部文件被删/被改都不再影响这条 run；
3. 漂移判据**不放宽**：冻结正文解出的 plan 仍要过 `assert_semantics_frozen`
   （语义 digest 不符一律拒绝、一次都不执行）；
4. 没有冻结正文的旧 run 走既有来源解析，且拒绝原因点名"缺的是哪条事实"。

## 口径

1. **冻结的是被解析的那份正文**，不是"再读一遍文件"：路径来源读文本一次 → 用这段文本
   解析（`load_protocol_from_text`，与草稿修订同一条 Text→Domain 链）→ 同一段文本入
   run 行。启动与重建因此对**同一份字节**解析，不存在"解析了一份、冻结了另一份"。
2. **正文与 digest 是值对象不变量**：`ProtocolBody(text, digest)` 在构造时校验
   `sha256(text) == digest`（篡改的正文构造不出来），空正文拒绝。
3. **正文是 run 行的一部分**（`runs.run_json`），不是第二套存储：canonical 行原子、
   备份与迁移同路；不动 `ArtifactStore`（CAS 是派生面，这里要的是"run 自己记得"）。
   代价与边界写进文档：正文随 run 行占空间（协议 YAML 量级为 KB）。
4. **重建优先级**：run 行有冻结正文 ⇒ 只用它（不碰文件系统、不碰草稿库）；没有 ⇒
   既有来源解析（旧 run 的兼容路径），失败时拒绝原因**同时点名**"没有冻结正文"与
   "来源不可解析"。
5. **不可伪造的守卫仍然只有一条**：语义 digest 校验（`assert_semantics_frozen`）——
   换一份正文（哪怕自洽）解出的 plan 与 `run.manifest_semantic_digest` 不符就拒绝。
   本轮的冻结正文不引入新的"信任输入"，它只是把同一份输入持久化。
6. **读面诚实**：`RunDetailDto` 增补 `protocol_body_digest`（None = 旧行，没有冻结
   正文，重启续跑仍依赖外部来源可解析）。

## 验收条件

- [x] AC-01 **正文随 run 落 canonical**：`POST /projects/{id}/runs`（路径来源与草稿来源
  同一条装配链）启动后，run 行带 `ProtocolBody`，其 digest 等于该正文的 sha256；SQLite 与 PG
  两个 store 往返一致（旧行解码为 None，不伪造）。
- [x] AC-02 **文件消失后仍能重建续跑**：API 面——用临时协议文件启动 run（真跑完，
  留下冻结事实）⇒ **删除该文件** ⇒ 以同一冻结事实构造停车 run ⇒
  `POST /runs/{id}/resume` 的 `continuation == "REBUILT"`（装配链从冻结正文重建），
  全程不读那份文件；e2e 面——从 **canonical 行里读回来的正文**重建上下文并跑完断点。
- [x] AC-03 **不放宽**：冻结正文换成另一份（自洽但不同）时，重建被拒且一次都不执行
  （语义 digest 不符）；没有冻结正文且来源不可解析时，拒绝原因点名两条事实
  （`no frozen protocol body` + 具体解析失败原因）。
- [x] AC-04 **值对象不变量**：`ProtocolBody` 拒绝 digest 与正文不符、拒绝空正文；
  `ProtocolSource` 的 XOR 判据不变（回归用例）。
- [x] AC-05 **门禁与记录**：定向套件 + 契约快照重生成 + web 门 + m0 23 项 + RECHECK-084 +
  MEM-059 + GOAL-004 cycle 1 记账（迭代日志/EC 状态/child_plans/ALL_PLAN 投影）。

## 实施清单

- [x] WP-A **冻结事实**：`ProtocolBody` 值对象（domain）+ `ResearchRun.protocol_body`
  （含三个显式重建函数）+ `StartRunCommand.protocol_body` + `_start_run_impl` 落行 +
  `read_protocol_text`（catalog，同一路径校验）+ `load_protocol_with_body` /
  `parse_frozen_protocol`（API 装配）+ SQLite/PG 两个 run store 编解码 + 用例。
- [x] WP-B **重建与读面**：`ExecutionRequest.protocol_body` 优先解析（不碰文件/草稿库）+
  `run_resume` 传入冻结正文 + 拒绝原因点名两条事实 + `RunDetailDto.protocol_body_digest`
  （`_run_state_dto` 与 `list_runs` 两处）+ web 类型/夹具同步 + 用例。
- [x] WP-C **收口**：契约快照重生成 + 定向 + m0 → commit（每 WP 独立）→ push → CI 六 job →
  RECHECK-084 + MEM-059 + GOAL-004 回写。

## 证据

- **提交**：`3d9cc73`（WP-A 冻结事实）、`87c2d86`（WP-B 重建与读面）；收口记录提交见 GOAL 迭代日志。
- **定向套件**：api **9 passed**、e2e **5 passed**、domain **4 + 13 passed**、
  sqlite **4 passed**、pg **3 passed**（命令与逐条判据见 RECHECK-084「门禁」段）。
- **反证实测**：删除外部模板后 `continuation=REBUILT`（修复前为 `NONE` +
  `protocol file not found`）；换一份自洽正文 ⇒ `resume semantics drifted`，任务身份数不变。
- **相邻发现**：重建"没有剩余工作"的 run 会退化成重跑全部并收敛 `FAILED`
  （`conflicting claim registration`）——RECHECK-084 W-1，登记为后继入口。
- **CI 红项（与本改动无关，已修）**：`collector-quality` 的
  `test_workflow_retry_backoff_pg.py` 两个用例用 SQL `now()` 挪 deadline 而引擎注入固定
  时钟 ⇒ 墙钟越过 `START` 后必红；夹具改用引擎时钟，断言未改。修复提交 `5607992` →
  run **35204710864 六个 job 全 success**。
- **门禁**：见 RECHECK-084「门禁」段（web 门 + m0 23 项）。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 1 = EC-01）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B 交付 + 定向/e2e/契约/web 门/m0 全绿；
  RECHECK-20260917-084（PASS_WITH_WARNINGS）→ `status: DONE`。

## 影响报告

- **Domain**：新增 `ProtocolBody` 值对象；`ResearchRun` 新增 `protocol_body` 字段
  （三个重建函数同步复制，避免静默丢字段——cycle 20 的教训）。
- **API/schema**：`RunDetailDto` 新增 `protocol_body_digest`（可空，向后兼容）；
  `POST /projects/{id}/runs` 的入参不变。
- **持久化**：`runs.run_json` 多一个键；SQLite 无 DDL 变化，PG 无迁移（JSONB）。
  旧行解码为 `None`（诚实空态），不伪造、不推断。
- **安全/凭据**：无新凭据面；冻结正文是受控模板/草稿修订的副本（不含密钥）。
- **兼容性/迁移风险**：无破坏性迁移；旧 run 行为不变（仍走来源解析）。
- **上游版本影响**：无新依赖。
