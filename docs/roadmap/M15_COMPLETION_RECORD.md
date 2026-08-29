# M15 Completion Record — Observability / Cost / Eval Operations

- Date: 2026-08-29
- Plan: `PLAN-20260828-024-m15-observability-cost-eval-operations`
- Roadmap authority: [MILESTONES.md](MILESTONES.md) §M15（Entry Gate M11 PASS ✅）
- Verification baseline: `run_all_checks.py --profile m0` = **19/19 PASS**（多轮复跑，
  含 PostgreSQL live 套件；typescript 5 项门禁全绿；web console build/lint/test 全绿）
- 结论：**M15 DONE（PASS）**；停在里程碑边界，M16 未动。

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

## 2. DoD PASS/FAIL 矩阵（21 条退出标准）

| # | 退出标准 | 证据 | 判定 |
|---|---|---|---|
| 1 | OTel qualification 报告 | `docs/references/upstream/M15_OTEL_QUALIFICATION.md`（16 项问题矩阵、adopted/rejected 面、collector 故障行为、semconv 0.60b1 风险） | PASS |
| 2 | import-linter 契约 + 边界测试 | `.importlinter.otel` KEPT；domain/application/fakes/sqlite/postgres/relay/mcp/api 的 forbidden 列表 + opentelemetry 全 0 broken；`tests/architecture/python/test_otel_boundaries.py`（含 AST 扫描 + postgres 契约开始执行） | PASS |
| 3 | trace hierarchy（真实 run） | `tests/observability/test_otel_adapter.py::test_parent_linkage_follows_correlation_hierarchy`（真实 OTel SDK,run→task 父子链 + 同 trace_id） | PASS |
| 4 | 每信号站点测试 | gateway（test_gateway_telemetry）、tool（contract+capability plane）、workflow（queue lag/duration/lease metric 断言）、docker（execution telemetry 包装）、eval（runner metric）、orchestration（RUN/TASK span） | PASS |
| 5 | 词汇无内容通道 + canary | 闭集 `AttributeKey`/`MetricLabel` + `sanitize_attributes`（结构上不可表达 prompt/response/args/body）;`test_privacy_canary.py` 七类唯一 marker 零出现 | PASS |
| 6 | 真实 OTLP 字节 + pinned collector canary | `tests/observability/otlp_receiver.py`（真实 socket + opentelemetry-proto 解码）;collector 文件输出断言（requires_collector 标记,本机 docker compose 验证） | PASS |
| 7 | collector 故障下 canonical state 相等 | `test_failure_isolation.py` 八种注入（down/timeout/500/slow/queue-full/malformed/restart/hangup）× workflow/outbox/budget/evidence 投影逐项相等;PG 变体（postgres 标记）事务/lease/outbox 相等 | PASS |
| 8 | audit vs telemetry 分离 | telemetry 不回读（port 契约 + FailSafe 计数只用于展示）;domain events 仍是唯一审计 truth（PORTS.md §7） | PASS |
| 9 | 成本唯一 usage 输入 | `project_dimensions` 只接受 `UsageLedgerEntry`（telemetry 类型不可达）;`test_cost_projection.py` | PASS |
| 10 | 五状态成本 | ACTUAL/ESTIMATED/MONETARY_UNAVAILABLE/USAGE_UNKNOWN/ZERO 各自测试;UNKNOWN 永不折叠为 0 | PASS |
| 11 | pricing 版本/摘要历史稳定 | `test_price_change_cannot_mutate_historical_projection`（v1 投影不可被 v2 改写） | PASS |
| 12 | retry/failure/cancel 记账 | attempt 作用域 entry id 追加不碰撞;duplicate entry_id 被 ledger 拒绝（不 double-count）;失败/取消 = UNKNOWN（不伪造） | PASS |
| 13 | trend store provenance | `build_trend` 唯一输入 `EvalReportStore`;`missing_evaluations` 第三态 | PASS |
| 14 | comparability 分支 | CASE_SET/DATASET/GATE_CONFIG/SCORER/EVALUATOR/SYSTEM_VERSION/SEGMENTED/INCOMPATIBLE 各分支测试 | PASS |
| 15 | verdict provenance | 回归 marker 全部来自 `compare_reports`（trend 不发明阈值）;FrozenConditions 未修改（M11 digest 全绿） | PASS |
| 16 | INFRA_ERROR 隔离 | 独立计数贯穿 index→store→trend→API;不折算/不 PASS/不丢弃 | PASS |
| 17 | Console projection-only | 浏览器零成本计算/零阈值/零 vendor 依赖（production-boundaries.test.mjs 接入根 test 脚本） | PASS |
| 18 | soak 与资源对比 | `test_telemetry_overhead.py`（off/on 延迟 ≤8×、线程稳定、干净 shutdown、drop=0）;`probe_telemetry_soak.py` 手工运行 PASS（60+ 迭代 0 drop,420 spans） | PASS |
| 19 | 全量回归 | m0 profile 19/19（含 2320+ tests;M14 postgres/crash-restart/probes off 与 on-故障注入双跑 123 passed） | PASS |
| 20 | 供应链 | 6 包 ADOPTED（sdist sha256 = uv.lock 实测值）+ collector DOCKERFILE 组件（manifest digest pin）+ LICENSE_MATRIX 7 行;validate_bundle 0 错误 | PASS |
| 21 | recheck（原始验收条件） | 计划 DoD 21 条逐项映射本文档矩阵;M15 acceptance recheck 由本记录 + m0 19/19 承接 | PASS |

**判定：21/21 PASS — M15 DONE。**

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

- **无内容通道**：`AttributeKey` 闭集（29 键）+ `sanitize_attributes`（白名单 +
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
- PG 迁移 005 纯新增表（eval_reports）,幂等可重放;migration 测试更新至
  5 版本（broken 注入改用 006 保持回归意图）。
- OTel 1.39.1 / semconv 0.60b1 早已是 uv.lock 传递依赖（openhands-sdk→lmnr）,
  版本零漂移;仅新增直接依赖声明（uv.lock 26 行插入,无版本变更）。
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
