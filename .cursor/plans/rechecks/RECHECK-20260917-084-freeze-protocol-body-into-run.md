---
id: RECHECK-20260917-084
plan_id: PLAN-20260917-084
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle1
baseline_ref: 5607992
checked_head: 87c2d86+worktree
---

# RECHECK-20260917-084 — 来源自足续跑（GOAL-004 cycle 1 = EC-01）

## 检查范围

PLAN-20260917-084 声称的交付面：① `ProtocolBody` 值对象（正文 + sha256，构造即校验）；
② `ResearchRun.protocol_body` 随启动落 canonical（HTTP 面与队列派发同源）并随状态迁移保留；
③ 重建优先用冻结正文，外部文件/草稿修订消失不再阻断；④ 漂移判据不放宽（语义 digest
校验仍是唯一守卫，且"一次都不执行"）；⑤ 拒绝原因点名缺的是哪条事实；⑥ 两个 run store
（SQLite/PG）往返一致、旧行显式留空。

**未覆盖**（见告警）：没有剩余工作的重建会退化成"重跑全部"（本轮发现，属相邻缺陷）；
旧 run（早于正文冻结）没有正文，仍依赖来源可解析；正文随 run 行占空间。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 正文随 run 落 canonical（AC-01） | API 用例：`POST /projects/{id}/runs` 后从 canonical 行读回 `protocol_body`，其 digest == 该文件字节的 sha256，且 `GET /runs/{id}` 的 `protocol_body_digest` 与之一致；SQLite 用例：往返 + **跨状态迁移不丢** + 旧行 None；PG 用例：JSONB 往返同判据（实跑非 skip） | PASS |
| 文件消失后仍能重建（AC-02） | API 用例（真 SQLite + 真装配链）：用临时模板启动 run（`SUCCEEDED`，留下真冻结 digest 对）⇒ **删除该文件** ⇒ 以同一 run 的冻结事实停车 ⇒ `POST /runs/{id}/resume` ⇒ `continuation == "REBUILT"`、note 明说"rebuilt from the recorded protocol source"。同一条路径在修复前是 `NONE` + `protocol file not found`（见本文件"反证"） | PASS |
| 不放宽：换正文 ⇒ 拒绝（AC-03a） | API 用例：把冻结正文换成同协议的 `0.4.1`（自洽、可解析）⇒ 重建被拒（`drifted`），run 的 manifest digest 未重盖，任务身份数不变（**一次都不执行**）；e2e 用例：正文解出的定义与装配链**逐字段相等**（`parse_frozen_protocol(body) == m7_protocol()`），断点语义不变（第一个任务不重跑、断点任务 `attempt=2`、run `SUCCEEDED`） | PASS |
| 拒绝原因点名两条事实（AC-03b） | API 用例：旧 run（无正文）+ 来源不可解析 ⇒ note 同时含 `no frozen protocol body` **与** `protocol file not found` | PASS |
| 值对象不变量（AC-04） | domain 用例 4：digest 与正文不符 ⇒ 构造拒绝；空正文拒绝；`digest == sha256(text)`；`ProtocolSource` XOR 判据回归 | PASS |
| 门禁与记录（AC-05） | 定向：api 9 / e2e 5 / domain 4+13 / sqlite 4 / pg 3 全绿；`python/typecheck`（m0 全量）绿；`framework/validate` 绿；m0 = **PASS: profile=m0; 23 deterministic checks**（见"门禁"段）；RECHECK + MEM-059 + GOAL/ALL_PLAN 记账 | PASS |

## 反证与实测

- **修复前的实况**（同一场景、同一装配链，本轮实现前量得）：`continuation=NONE`，
  note = `... rebuild refused: ... protocol file not found: 'frozen-body-<hex>.yaml'`
  ⇒ "能续跑"依赖的是那份文件的可获得性。
- **换一份自洽正文**：`version: 0.4.0 → 0.4.1`（可解析、schema 合法）⇒
  `ManifestFreezeError: resume semantics drifted from frozen manifest`，且任务身份数前后相等。
- **PG 退避用例的墙钟依赖**（本轮 CI 红项）：`test_workflow_retry_backoff_pg.py` 的两个用例
  注入固定引擎时钟（`START=2026-09-17T09:00:00Z`），却用 SQL `now() - interval '1 second'`
  挪 deadline；CI 墙钟越过 09:00Z 后两者**必然红**（与本轮改动无关，文档提交亦复现）。
  处置：夹具改用引擎时钟写 deadline（`%s - interval '1 second'` 传 `START`），
  **断言一字未改**；本机修复前 2 failed/1 passed、修复后 3 passed。

## 告警

- **W-1（重建的"没有剩余工作"分支会重跑全部，本轮发现）**：`resume_rebuilt` 把剩余
  specs 传成**空元组**时，执行体的 `ctx.pending or ctx.resolve_sessions()` 把空元组当作
  "没提供"，于是重新解析全量 specs 并再次投递**已完成**的任务；与 claim/证据面冲突
  （`conflicting claim registration` / `unknown task`）⇒ run 收敛 `FAILED`。
  实测：一条已 `SUCCEEDED` 的 run 停车后重建续跑 ⇒ `continuation=REBUILT` 但
  `run.failed: ... produced malformed result: conflicting claim registration`。
  影响面：重建一条"已经跑完"的 run；对**有剩余工作**的断点 run 语义正确（e2e 已证）。
  登记为后继入口（产品语义问题：没有剩余工作应收敛到什么状态），不在本 EC 判据内。
- **W-2（旧 run 没有正文，不可追溯回填）**：正文只在启动路径产生。本轮之前的所有 run 行
  没有 `protocol_body`（解码为 None），其重启续跑仍依赖来源可解析——诚实的边界，
  不做推断、不伪造。
- **W-3（正文随 run 行占空间）**：协议 YAML 为 KB 量级，`run_json` 因此成倍增长；
  本轮判据下可接受（单一 canonical 行、无第二套存储），若未来协议体积变大需重估
  （或转内容寻址存储 + 引用）。
- **W-4（读面语义边界）**：`protocol_body_digest` 非空只表示"这条 run 自己记得那份字节"，
  **不保证重建一定成功**——目录/契约/定价漂移仍会拒绝。读面文档与 DTO 注释已写明。
- **W-5（同类时钟风险只做了 grep 排查）**：注入时钟的 PG 用例共 12 个文件，只有本文件
  用 SQL `now()` 写时钟敏感列（grep 证据：`now()` 在 `tests/postgres/*.py` 仅此一处，
  修复后为零）。未逐个复验其余用例是否还有别的墙钟依赖形态。

## 门禁

- 定向套件：`tests/api/test_run_source_and_rebuild_api.py` **9 passed**；
  `tests/e2e/test_restart_rebuild_resume.py` **5 passed**；
  `tests/domain/test_protocol_body.py` **4 passed**；`tests/domain/test_run_entity.py`
  **13 passed**；`tests/adapters/sqlite/test_run_protocol_source_and_success_keys.py`
  **4 passed**；`tests/postgres/test_run_source_and_task_identities_pg.py` **3 passed**。
- 受影响契约：`tests/contracts/test_openapi_snapshot.py` **8 passed**（`RunDetailDto`
  新增 `protocol_body_digest` 后重生成 `docs/api/openapi.m13.json`，+11 行）。
- web 门：`typescript/{format:check,lint,typecheck,boundaries,test,web-lint,web-test,web-typecheck,web-build}`
  全绿（`apps/web/tests/e2e/apiFixtures.ts` 的 `RunDetailDto` 夹具同步新字段）。
- m0：`PASS: profile=m0; 23 deterministic checks`（全量 pytest **3773 passed / 10 skipped**，
  497.96s；首轮 m0 红 2 处——契约快照漂移与 web 夹具缺字段，均为本改动引入、已修后复跑全绿）。

## 结论

cycle 20 的重建入口让"重启后能续跑"成立，但它的输入是**外部文件的当前内容**——来源消失
即拒绝（RECHECK-083 W-3）。本轮把输入换成"run 行里那份**被解析过的字节**"：启动时冻结
（值对象保证正文与 digest 自洽），重建时只认它，外部文件/草稿修订的消失不再阻断；
拒绝路径改成点名两条事实；漂移判据一个字没放宽（换一份自洽正文仍被语义校验拒绝，
且一次都不执行）。

结果为 **PASS_WITH_WARNINGS**：W-1 是本轮**新发现**的相邻缺陷（"没有剩余工作"的重建会
退化成重跑全部并收敛 `FAILED`），已附实测与复现，登记为后继入口；W-2/W-3/W-4/W-5 是
适用范围与口径的如实登记。**未宣称"任何 run 重启后都能续跑"**：旧 run 没有正文，
旧行仍依赖来源可解析；正文在、目录漂移时同样拒绝。
