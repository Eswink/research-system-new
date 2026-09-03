---
id: RECHECK-20260903-029
plan_id: PLAN-20260903-029
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-03
completed_at: 2026-09-03
reviewer: root-agent-independent-pass
baseline_ref: ab5ffc8
checked_head: working-tree（PA-1 债务修复实施，基线 ab5ffc8 W3+BUSY 之后 + Final 门禁）
---

# RECHECK-20260903-029 — PA-1 后全量债务修复复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260903-029-pa1-debt-remediation.md`
- 权威任务书：`.zcode/plans/plan-sess_2fc63c9d-ea0a-463d-8c4f-2601ad2ca96d.md`
  （用户批准的分 5 Phase 债务修复计划）
- 验收条件：见任务计划 §验收条件（F1/F2/F5/blob 目录/dsn/F6a/F6b/F7/backup/
  worker 遥测/cluster DTO/NCBI defuse/凭据字面量/Mimosa 处置/W3/BUSY/最终门禁）
- 变更范围：`packages/{domain,application}/`（budget/experiments/execute/
  usage_collection/budget_entries/clean_run_*/deliverable/cost/run_orchestration）、
  `adapters/{postgres,sqlite,execution,research_tools}/`、`services/{api,worker}/`
  （settings/pg_composition/dto/worker_gateway/telemetry）、`tests/` 各套件、
  `tools/backup.py`、`docs/{roadmap,operations,audits}/` 记录、任务计划与复检记录
- 基线：`ab5ffc8`（W3 + BACKLOG-178 提交）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | F1 内存来源白名单 | `MemoryStore.allow_source` + gate 接线（630b834）；`tests/application/memory/test_gate.py` 新断言；PG 组合实测可写入 | PASS |
| G-02 | F2 PG 自动重连 | `ReconnectableConnection` 委托包装（`adapters/postgres/db.py`）；`tests/postgres/test_reconnect.py` 8 绿；dsn_from_env 含 RESEARCHOS_POSTGRES_DSN | PASS |
| G-03 | F5 preflight codes | `_preflight_failure_message` 携带 codes（94b271d）；200+FAILED 诚实语义不变（既有 4 个诚实-FAILED 测试绿）；PERSONAL_DEPLOYMENT §2 provisioning 步骤 | PASS |
| G-04 | API blob 目录 env | `RESEARCHOS_ARTIFACT_BLOB_DIR` → PostgresArtifactStore（db91977）；composition 测试绿 | PASS |
| G-05 | F6a 环境封闭 | `effective_database_url()` 仅显式 database_url（9cd572d）；清洗 env 下 api 套件全绿 | PASS |
| G-06 | F6b worker 子进程白名单 | `worker_child_env` `_INHERIT_KEYS`（f76b783）；`test_worker_child_env_holds_zero_db_credentials` 零泄漏断言 | PASS |
| G-07 | F7 outbox 自提交 | `SqliteOutboxEventPublisher.publish` `with self._conn:`（bc7bd92）+ 3 新测试；timeline 全绿 | PASS |
| G-08 | tools/backup.py | CLI（pg_dump + blob tar + manifest + --verify + --keep）（95ed21d）；smoke 绿；PERSONAL_DEPLOYMENT §5 引用 | PASS |
| G-09 | worker 遥测装配 | `build_worker_telemetry` + `__main__`（fbca94c）；Null 默认 / FailSafe；loop 单测 + vocabulary 绿 | PASS |
| G-10 | cluster DTO GPU 字段 | `gpu_probe_digest`/`gpu_observed_at`（无 raw device name）；operations API 测试断言 | PASS |
| G-11 | NCBI defuse | `parse_efetch_xml` 拒 DTD/ENTITY + 5MB 上限（4c754b3）；parsing 6 绿 | PASS |
| G-12 | 凭据字面量 | S2/scratch canaries → env 惰性默认（4c754b3）；残留扫描仅合成测试文本 | PASS |
| G-13 | Mimosa 处置记录 | `docs/audits/PA1_MIMOSA_REVIEW.md` 40 findings 逐条处置（db17e12）；partial/static_only 声明 | PASS |
| G-14 | W3 小数秒 | `int \| Decimal` 全链（ab5ffc8）；canonical serialization 拒绝 float → Decimal 编码；`_json_seconds`；无 DB 迁移 | PASS |
| G-15 | BUSY 接线 | claim→CLAIM / submit→JOB_SETTLED（ab5ffc8）；`test_busy_worker_refuses_second_claim_until_settled` 绿；跨任务替换测试随 BUSY 语义修复 | PASS |
| G-16 | 最终门禁 | 清洗 env `m0`：python 2871 passed + 修复后 source-limits 701 passed + typescript/web-build + framework 全绿；DB 套件（postgres/distributed/GPU slice/scenarios）全绿；脆性用例（p11 两个）专用复检 2 passed | PASS |

## 说明

- 跨任务替换测试（`test_cross_task_output_substitution_rejected`）在 BUSY 接线后
  需先结算任务 A 才能 claim 任务 B（worker 单 in-flight 上限是权威语义）；测试已
  更新为先 settle A 再尝试以 A 的 bundle 冒充 B 的输出——攻击面断言（409）不变。
- `test_gpu_reproduction_e2e.py` 主测试函数 52 行超 50 行函数上限 → 拆分
  `_assert_semantic_reproducibility` 帮助函数；source-limits 复跑 701 passed。
- Mimosa 密封扫描在提交钩子反复报告 scanner_enobufs（会话级限制）；处置记录
  以 scan-2026-09-03T06-45-52 的 40 findings 为准，声明 static_only，不宣称"安全"。

## 结论

Phase 1–5 全部完成，验收条件逐条有真实证据（提交 + 定向测试 + 最终门禁）。
判定 **PASS**。完成后停止，债务表 0 残留（仅保留项有理由记录），
PA-1 COMPLETION RECORD 债务表逐项关闭；不自动进入下一里程碑。
