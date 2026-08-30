# M15 Completion Record — Observability / Cost / Eval Operations

> **状态头注（2026-08-30 修复轮完成）**：本记录首轮（2026-08-29）自证草稿经
> **2026-08-30 独立复审判定 FAIL**（6 BLOCKER + ~24 MAJOR + ~25 MINOR）。
> 修复轮 `../../.cursor/plans/m15_fail_remediation_98df6116.plan.md` 的 WP0–WP8
> 已全部完成：6 个 BLOCKER 均以独立探针复现原始路径并确认修复；全量门禁
> m0 profile **23/23 deterministic checks PASS**（2420 passed / 5 skipped），
> collector-quality / requires_docker / e2e / probes / validators 全绿。
> recheck 见 `../plans/rechecks/RECHECK-20260830-024-m15-fail-remediation.md`
> （result=PASS）。以下内容按本轮实际执行证据重写。

- Date: 2026-08-29（首轮）/ 2026-08-30（修复轮完成）
- Plan: `PLAN-20260828-024-m15-observability-cost-eval-operations`
- Remediation plan: `.cursor/plans/m15_fail_remediation_98df6116.plan.md`（WP0–WP8 全部 completed）
- Roadmap authority: [MILESTONES.md](MILESTONES.md) §M15（Entry Gate M11 PASS ✅）
- Verification baseline（本轮实测）：`run_all_checks.py --profile m0` = **23/23 deterministic checks PASS**，`python/tests` 2420 passed / 5 skipped；mypy 615 files 0 error；ruff check/format 全绿；web 27 tests + typecheck + build 全绿
- 结论：**M15 DONE（2026-08-30 修复轮完成 + recheck PASS）**；M16 未动。

## 1. 交付物

| Work Package | 交付物 | 位置 |
|---|---|---|
| WP1 观测平面 | 自营观测词汇（闭集,无内容通道） | `packages/application/observability/` |
| WP1 | TelemetrySink Port + Null + Fake | `packages/application/ports/telemetry_sink.py`, `adapters/fakes/telemetry_sink.py` |
| WP1 | OTel adapter（8 模块,SDK 仅此包） | `adapters/otel/`（config/resource/span_mapping/metric_mapping/sink/provider/failsafe） |
| WP1 | 九类信号站点 | relay gateway / tool_plane / PolicyWrappedToolExecutor / sqlite+pg workflow / outbox relay / schedulers / docker backend / eval runner / orchestration |
| WP1 | collector 证据管线（digest-pinned 0.139.0） | `docker-compose.m15.yml`, `adapters/otel/collector/` |
| WP1 | in-repo OTLP/HTTP receiver + 故障注入 + 隐私 canary | `tests/observability/` |
| WP2 | ledger 修正（quantity_status/attempt/全保真编解码） | `packages/domain/budget.py`, `adapters/{sqlite,postgres}/budget_ledger.py` |
| WP2 | 版本化定价快照 + 五状态成本投影 | `schemas/pricing-table.schema.json`, `packages/application/cost/` |
| WP3 | EvalReportStore（verbatim body + 可重建索引） | `packages/application/ports/eval_report_store.py`, `adapters/{sqlite,postgres,fakes}/eval_report_store.py`, `migrations/005_eval_state.sql` |
| WP3 | ComparabilityVerdict + 分段趋势 | `packages/application/evaluation/{comparability,trend}.py` |
| API/Console | 三个只读 operations 端点 + Console 视图 | `services/api/{routers,dto,mappers}/operations.*`, `apps/web/src/features/operations/` |
| WP4 | 隐私 canary / 架构门禁 / supply-chain / soak | `tests/observability/test_privacy_canary.py`, `.importlinter.otel`, `UPSTREAM_COMPONENTS.yaml`, `tools/probes/probe_telemetry_soak.py` |
| WP1/2/3（未申报） | relay/workflow 适配器重构（`adapters/relay/completions.py`、`transport.py`；`adapters/sqlite/workflow_ops.py`、`workflow_engine.py` 扩展；`adapters/postgres/workflow_engine.py`、`telemetry_notes.py`） | 首轮完成记录未登记，本行补记 |

> 既存条件（记录不修复）：`services/api/composition.py` 与
> `services/api/pg_composition.py` 的 composition root 在生产路径注入
> `FakeAgentRuntime`（M13 遗留），M15 telemetry/cost 视图因此投影 fake
> agent loop，不代表真实执行；`LMNR_PROJECT_API_KEY` 存在时 OpenHands
> 会话 trace 会经进程内厂商 shim 外发（仓库无 env allow-list）——"Vendor
> SDK 不采用"仅限定 Research OS 自有代码。

## 2. DoD PASS/FAIL 矩阵（21 条退出标准，2026-08-30 修复轮证据重写）

| # | 退出标准 | 证据（本轮实际执行） | 判定 |
|---|---|---|---|
| 1 | OTel qualification 报告 | `docs/references/upstream/M15_OTEL_QUALIFICATION.md`（adopted/rejected 面、collector 故障行为；semconv 0.60b1 为 SDK 传递依赖、代码零 import，直接依赖声明已移除并同步 UPSTREAM_COMPONENTS/LICENSE_MATRIX） | PASS |
| 2 | import-linter 契约 + 边界测试 | `.importlinter.otel`/`.postgres`/`.api` KEPT；`tests/architecture/python/test_otel_boundaries.py`（AST 扫描含 tools/ + source_modules 元测试 + postgres 契约执行）；`.importlinter.sqlite` 已纳入版本控制（BLOCKER-1 修复，`git ls-files` 确认）；`tests/architecture` 66 passed | PASS |
| 3 | trace hierarchy（真实 run） | `test_otel_adapter.py::test_parent_linkage_follows_correlation_hierarchy`（真实 OTel SDK，run→task 父子链 + 同 trace_id；PROJECT span 脱链已修） | PASS |
| 4 | 每信号站点测试 | gateway/tool/workflow/docker/eval/orchestration 站点测试；fail-open 对称性补齐（scope.__enter__/scheduler/outbox_relay） | PASS |
| 5 | 词汇无内容通道 + canary | 闭集 `AttributeKey`（27 键）/`MetricLabel` + `sanitize_attributes`（**先 redact 后截断**，全字符串键脱敏）；`test_privacy_canary.py` 重写为真实注入 9 类 marker 并扫描真实 OTLP wire bytes/caplog/capsys/telemetry 端点（7 passed）；独立复现：marker 经 operation 属性通道注入后 OTLP wire bytes 零出现 | PASS |
| 6 | 真实 OTLP 字节 + pinned collector canary | `otlp_receiver.py`（真实 socket + opentelemetry-proto 解码）；collector 文件输出断言；collector-quality 套件 44 passed（RESEARCHOS_REQUIRE_COLLECTOR=1 fail-closed） | PASS |
| 7 | collector 故障下 canonical state 相等 | `test_failure_isolation.py` 八种注入 × canonical state 逐项相等；PG 变体事务/lease/outbox 相等；**BLOCKER-4 独立复现**：blackhole collector 下 flush=0.000s/shutdown=0.000s（< 1.5s 硬上界，watchdog 生效） | PASS |
| 8 | audit vs telemetry 分离 | telemetry 不回读；domain events 仍是唯一审计 truth（PORTS.md §7） | PASS |
| 9 | 成本唯一 usage 输入 | `project_dimensions` 只接受 `UsageLedgerEntry`；`test_cost_projection.py` 14 passed | PASS |
| 10 | 五状态成本 | ACTUAL/ESTIMATED/MONETARY_UNAVAILABLE/USAGE_UNKNOWN/ZERO + PARTIALLY_METERED/CURRENCY_CONFLICT/NO_DATA；UNKNOWN 永不折叠为 0；currency 参与算术（跨币种拒绝） | PASS |
| 11 | pricing 版本/摘要历史稳定 | **BLOCKER-6 独立复现**：`test_pricing_snapshot_freeze.py::test_price_change_cannot_mutate_persisted_run_a_projection`（Run A 冻结 v1 → 当期表改 v2 → `resolve_run_pricing` 从快照存储解析 v1，金额 200/版本 v1 不变）+ 遗留 run 显式未冻结 + 快照缺失显式降级；migration 006 定价快照存储 | PASS |
| 12 | retry/failure/cancel 记账 | **BLOCKER-5 独立复现**：`test_execute_task_accounting.py` 10 passed（重试耗尽收敛 FAILED 无 duplicate entry_id 崩溃；attempt 作用域 entry 唯一；phase_runner 接线 budget）；cancellation 记账经 `cancelled_task_ids` 去碰撞 | PASS |
| 13 | trend store provenance | `build_trend` 唯一输入 `EvalReportStore`；`missing_evaluations` 经 `expected_digests` 路由接线（第三态非恒空）；query_page 最新优先 + truncation 标记 | PASS |
| 14 | comparability 分支 | CASE_SET/RUBRIC/DATASET/GATE_CONFIG/SCORER/EVALUATOR/SYSTEM_VERSION/SEGMENTED/INCOMPATIBLE 各分支测试（`test_eval_trend_m15.py` 补齐 4 个零覆盖分支）；标签错位修复（rubric/scorer 先于 dataset） | PASS |
| 15 | verdict provenance | 回归 marker 全部来自 `compare_reports`；`StoredEvalReport` 强制 `report_digest==digest(body)` + verdict 闭集；trend `_point_of` 用 verbatim body 交叉校验 index，冲突降级 INDETERMINATE | PASS |
| 16 | INFRA_ERROR 隔离 | 独立计数贯穿 index→store→trend→API；`reviewer_failure_count` 投影列（reviewer 设施故障不再呈现干净 PASS）；pass_ratio 分母排除 INFRA | PASS |
| 17 | Console projection-only | 浏览器零成本计算/零阈值/零 vendor 依赖（去 /100 与硬编码 USD，渲染服务端金额+币种）；`production-boundaries.test.mjs` 5 断言（成本算术/币种/verdict 字面量/阈值/厂商 SDK）+ web 27 tests + typecheck + build 全绿 | PASS |
| 18 | soak 与资源对比 | `test_telemetry_overhead.py`（drop_count 聚合 inner 计数，非恒真）；`probe_telemetry_soak.py --pg` SOAK PASS（200 迭代 0 drop、1400 spans、50 PG 任务唯一 id）；telemetry 不消耗业务时钟 | PASS |
| 19 | 全量回归 | m0 profile **23/23 deterministic checks PASS**（2420 passed/5 skipped；mypy 615 files 0；ruff 0；TS 5 + web 4 + framework 8 全绿）；requires_docker 39 passed；e2e 73 passed/1 skipped；9 probes PASS；validate_bundle/governance/learning/docs-consistency 全绿 | PASS |
| 20 | 供应链 | 5 包 ADOPTED（semconv 移除直接依赖）+ collector DOCKERFILE 组件 digest pin；validate_bundle 0 错误；collector 端口绑 loopback（127.0.0.1:4318） | PASS |
| 21 | recheck（原始验收条件） | `RECHECK-20260830-024-m15-fail-remediation.md`（result=PASS）：6 BLOCKER 独立探针复现 + 21 条 DoD 从原始验收条件重核 + 全量门禁实测 | PASS |

**判定：M15 修复轮完成，21/21 DoD PASS，recheck PASS（2026-08-30）；M15 DONE。**

## 3. 信号矩阵（实现面）

| Scope | Span | Metrics | 关联 |
|---|---|---|---|
| LLM_CALL | `llm.call` / `llm.list_models` | LLM_CALL_DURATION_MS（sink 自动）、LLM_CALL_RETRY_ATTEMPTS（内部重试） | endpoint_id/model_id 属性;tokens on success |
| TOOL_CALL | `tool.execute` / `tool.execute_direct` | TOOL_CALL_DURATION_MS（sink 自动） | task_id correlation;tool_id/attempt |
| WORKFLOW_QUEUE | workflow.submit/acquire_lease/heartbeat/complete/cancel/cancel_run（sqlite+pg） | WORKFLOW_QUEUE_LAG_MS、WORKFLOW_TASK_DURATION_MS、WORKFLOW_LEASE_EXPIRED | task_id/run_id correlation |
| OUTBOX_RELAY | `outbox.relay_pass`（scheduler） | OUTBOX_BACKLOG、OUTBOX_DRAINED | run 过滤 pending |
| LEASE_RECOVERY | `lease_recovery.pass` / `lease_recovery.recover` | WORKFLOW_LEASE_EXPIRED | — |
| EXPERIMENT_RUN | `experiment.execute`（docker backend） | EXPERIMENT_DURATION_SECONDS（sink 自动） | resource_type/exit_code/oom/image_digest |
| EVAL_RUN | `eval.run` | EVAL_RUN_DURATION_MS（sink 自动）、EVAL_INFRA_ERRORS、EVAL_MISSING_EVALUATIONS | eval_run_id correlation |
| RUN | `run`（orchestration）+ `task`（phase loop） | — | project/run/trace correlation |

## 4. 隐私与韧性证据

- **无内容通道**：`AttributeKey` 闭集（**27 键**，2026-08-30 修正）+ `sanitize_attributes`（白名单 +
  redact_text + 截断）;`MetricLabel` 7 键不含任何业务 id;correlation 业务 id
  只以 `research_os.correlation.*` 落 span,不进 metric。
- **Canary**：七类唯一标记（API key/Authorization/DSN 密码/prompt/tool arg/
  source body/artifact body）在真实 OTLP 字节、Console 投影、应用输出零出现。
- **故障隔离**：8 种注入 × canonical state（task 状态/投递/completion/usage/
  reservation/claim）与 telemetry-off baseline 相等;FailSafe drop 计数供
  `GET /runs/{id}/telemetry` 暴露 exporter 健康。

## 5. 兼容性与迁移风险

- `UsageLedgerEntry` 新字段全部带默认值;历史行解码为 KNOWN/attempt=1
  （不重解释既有数字）;M13 budget 契约与 `/runs/{id}/usage` 契约保持不变。
- PG 迁移 005（eval_reports 表）、006（pricing_snapshot 表，BLOCKER-6 定价冻结）、
  007（eval report 完整性加固：verdict 闭集 CHECK、reviewer_failure_count、
  recorded_at 不可变触发器）均为纯新增/加性，幂等可重放；migration 测试从真实
  迁移目录动态推导版本（WP0 起 broken 注入用下一版本号，当前为 007）。
- OTel 1.39.1 各包早已是 uv.lock 传递依赖（openhands-sdk→lmnr）,
  版本零漂移;M15 将其提升为直接依赖声明（含 sdist digest 登记）。
  **2026-08-30 修正**：`opentelemetry-semantic-conventions==0.60b1`
  （pre-release）全仓零 import，直接依赖声明已移除（保留为 SDK 传递依赖），
  `UPSTREAM_COMPONENTS.yaml`/`LICENSE_MATRIX.md`/qualification 同步更新。
- Console：client.ts 拆出 `http.ts` 保持规模阈值;OpenAPI 快照再生
  （+516 行,三端点）;tautological 快照测试已修复（漂移可被发现）。

## 6. 剩余非阻塞债务 → 清偿记录（2026-08-29 债务清偿轮）

M15 收尾时记录的债务已全部清偿；各证据项如下：

1. **PHASE 级 span** — ✅ 已清偿：
   `session_resolution.resolve_sessions` 填充 `SessionSpecContext.phase_id`；
   `phase_runner.execute_phases` 按连续同 phase 分组包 PHASE span（name="phase"），
   TASK correlation 携带 phase_run_id + trace_id，父子链接经层级字段集投影成立。
   测试：`tests/application/test_phase_spans_m15.py`（分组/父链接/失败传播/空 phase 回退）。
2. **pinned collector 常驻 CI** — ✅ 已清偿：`.github/workflows/m0-quality.yml`
   新增 `collector-quality` job（compose 起 m14+m15 → pytest `-m "requires_collector
   or postgres"`）；本地同命令验证 3 passed。
3. **circuit_state 信号** — ✅ 已清偿（方案 A，行为变更 opt-in）：
   `OpenAIChatGateway` 内置 per-endpoint 内存态断路器（仅
   `endpoint.circuit_breaker` 配置存在时启用），OPEN 短路（DENIED +
   circuit_state 属性）、成功/失败驱动迁移、half-open 探测恢复；
   `apply_failure` 增加 `now` 参数修复自然开路 `opened_at=None` 的 domain 缺陷。
   测试：`tests/adapters/relay/test_gateway_circuit.py`（5 tests）。
4. **SLO/告警** — 保留（M19 范围，本轮不动）。
5. **RSS 精确测量** — ✅ 已清偿：stdlib-only `_rss_mib()`（Windows psapi /
   Linux /proc·resource / macOS resource）；overhead 测试泄漏断言 +
   `probe_telemetry_soak.py` 打印 RSS before/after；不新增依赖。
6. **span_ref 并发碰撞（清偿轮新发现）** — ✅ 已清偿：确定性 scope 的引用只
   摘要层级字段集 + trace_id（父子投影一致）；叶子 scope 加 per-invocation
   nonce。修复 llm.call 空 correlation 全进程共享引用导致的 SpanMapper
   覆盖/孤儿/幻影 drop。测试：`test_otel_adapter.py` nonce 两则。
7. **pre-M15 过期状态文档** — ✅ 已清偿：BACKLOG/MILESTONES 中 M14
   "IN PROGRESS/DoD 未完成"、M12 "待重新独立复审" 表述与 RECHECK-20260828-
   022/023 重判结果对齐。

## 7. M16 / M19 就绪度

- **M16（Distributed Execution）**：M14 durable workflow + M15 telemetry
  （queue lag/lease 指标、outbox 信号）为远程 worker 调度提供观测基座;
  入口条件满足。
- **M19（Security/Governance/SLO）**：telemetry 隐私面（无内容通道、
  canary、cardinality 审计）已就绪;SLO 定义可直接消费现有 metric 词汇。
