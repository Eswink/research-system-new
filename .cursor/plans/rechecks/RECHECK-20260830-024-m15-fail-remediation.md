---
id: RECHECK-20260830-024
plan_id: PLAN-20260828-024
attempt: 2
status: COMPLETED
result: PASS
created_at: 2026-08-30
completed_at: 2026-08-30
reviewer: root-agent-independent-pass
baseline_ref: M15 首轮独立复审 FAIL（6 BLOCKER + ~24 MAJOR + ~25 MINOR，2026-08-30）
checked_head: m15_fail_remediation_98df6116 修复轮（WP0–WP8 全部 completed）
---

# RECHECK-20260830-024 — M15 Observability / Cost / Eval Operations 修复轮独立复检

## 冻结范围

- 任务计划：`.cursor/plans/m15_fail_remediation_98df6116.plan.md`（WP0–WP8）
- 原始验收条件：`docs/roadmap/MILESTONES.md` §M15（Purpose/Scope/Key Deliverables）
  + `docs/roadmap/M15_COMPLETION_RECORD.md` §2 的 21 条 DoD 退出标准
- 复审基线：首轮独立复审判定 FAIL（6 BLOCKER + ~24 MAJOR + ~25 MINOR）
- 本重判证据：**修复轮完成后从当前代码 + 真实 PostgreSQL + 真实 pinned collector +
  独立 OS 进程/探针取证**，不采信文档自证；6 个 BLOCKER 逐条复现原始路径

## 复审方法（对抗性，非文档自证）

- 环境：docker `research-system-postgres-1`（healthy，15432）、
  `research-system-otel-collector-1`（healthy，**127.0.0.1:4318 loopback-only**）、
  `uv run --frozen --no-sync`、Python 3.12、pnpm web 工具链
- 独立 BLOCKER 复现探针（本会话内联运行，可复跑）：
  - BLOCKER-1：`git ls-files .importlinter.sqlite` 确认纳入跟踪 +
    `test_relay_boundaries.py` 6 passed（clean-clone 架构门禁不再缺文件）
  - BLOCKER-2：marker 经 operation 属性通道注入 → 真实 OTLP wire bytes 零出现
  - BLOCKER-3：超长含 secret 值经 `sanitize_attributes` → 先 redact 后截断（残片不泄露）
  - BLOCKER-4：blackhole collector 下 `flush(1.0)`=0.000s / `shutdown(1.0)`=0.000s（< 1.5s）
  - BLOCKER-5：`test_execute_task_accounting.py` 重试耗尽收敛 FAILED，无 duplicate entry_id 崩溃
  - BLOCKER-6：Run A 冻结 v1 → 当期表改 v2 → `resolve_run_pricing` 从快照存储解析 v1，金额不变

## 检查结果（DoD 21 条重判矩阵）

| # | 退出条件 | 结果 | 证据（本会话实测） |
| --- | --- | --- | --- |
| 1 | OTel qualification 可信 | PASS | semconv 直接依赖声明移除（传递依赖表述）；"16 项矩阵"失实表述清除；qualification 与 UPSTREAM_COMPONENTS/LICENSE_MATRIX 一致 |
| 2 | import-linter + 边界 | PASS | `.importlinter.sqlite` 纳入跟踪（BLOCKER-1）；otel/postgres/api 契约 KEPT；AST 扫描含 tools/；source_modules 元测试；tests/architecture 66 passed |
| 3 | trace hierarchy | PASS | run→task 父子链 + PROJECT span 脱链修复；test_otel_adapter 父链接断言 |
| 4 | 信号站点测试 | PASS | 各站点测试 + fail-open 对称性（scope.__enter__/scheduler/outbox_relay）补齐 |
| 5 | 无内容通道 + canary | PASS | canary 重写为真实注入 9 类 marker 扫描 OTLP wire/caplog/capsys/端点（7 passed）；redaction 顺序修复；独立复现 BLOCKER-2/3 |
| 6 | 真实 OTLP + collector | PASS | collector-quality 44 passed（RESEARCHOS_REQUIRE_COLLECTOR=1 fail-closed，skip 即失败） |
| 7 | 故障下 canonical state 相等 | PASS | 8 注入 × 投影相等；BLOCKER-4 独立复现 flush/shutdown 墙钟 < 1.5s |
| 8 | audit vs telemetry 分离 | PASS | telemetry 不回读；domain events 唯一审计 truth |
| 9 | 成本唯一 usage 输入 | PASS | project_dimensions 只接受 UsageLedgerEntry；test_cost_projection 14 passed |
| 10 | 五状态成本 | PASS | 8 状态含 PARTIALLY_METERED/CURRENCY_CONFLICT/NO_DATA；UNKNOWN 不折叠 0；currency 参与算术 |
| 11 | pricing 历史稳定 | PASS | BLOCKER-6 独立复现：持久化 Run A 改价后重读金额/版本不变；migration 006 快照存储 |
| 12 | retry/failure/cancel 记账 | PASS | BLOCKER-5 独立复现：execute_task 重试耗尽无崩溃；test_execute_task_accounting 10 passed；phase_runner 接线 budget |
| 13 | trend provenance | PASS | missing_evaluations 经路由接线（非恒空）；query_page 最新优先 + truncation |
| 14 | comparability 分支 | PASS | 4 个零覆盖分支补齐（RUBRIC/SCORER/GATE_CONFIG/SEGMENTED/INCOMPATIBLE）；标签错位修复 |
| 15 | verdict provenance | PASS | StoredEvalReport 强制 digest==body + verdict 闭集；trend verbatim body 交叉校验 |
| 16 | INFRA_ERROR 隔离 | PASS | reviewer_failure_count 投影列；pass_ratio 分母排除 INFRA；贯穿 index→store→trend→API |
| 17 | Console projection-only | PASS | 去 /100 与硬编码 USD；production-boundaries 5 断言；web 27 tests + typecheck + build 全绿 |
| 18 | soak 与资源 | PASS | probe_telemetry_soak --pg SOAK PASS（200 迭代 0 drop、50 PG 任务唯一 id）；telemetry 不消耗业务时钟 |
| 19 | 全量回归 | PASS | m0 profile **23/23 deterministic checks**（2420 passed/5 skipped）；mypy 615 files 0；ruff 0；requires_docker 39；e2e 73/1skip；9 probes PASS；validators 全绿 |
| 20 | 供应链 | PASS | 5 包 ADOPTED + collector digest pin；validate_bundle 0 错误；collector loopback 绑定 |
| 21 | recheck | PASS | 本记录（RECHECK-20260830-024，result=PASS） |

## 本重判轮 Findings（修复轮执行中新发现并处置）

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | BLOCKER | `.importlinter.sqlite` 虽已从 .gitignore 移除但从未 `git add`，clean clone 仍缺文件（BLOCKER-1 未真正闭环） | 本会话 `git add` 纳入跟踪 + relay 边界测试复跑确认 |
| F-02 | MAJOR | `PostgresWorkflowEngine.cancelled_task_ids` 把 `cancelled` property 当方法调用（`self.cancelled()`）→ 运行时 TypeError | 修复为 `self.cancelled`（与 sqlite 引擎一致）；mypy 捕获 |
| F-03 | MAJOR | 工作树遗留 32 个 mypy 错误 + 4 个 pytest 失败（前轮修复改变生产行为未同步测试/类型） | 全修：composition 类型化 dataclass、mapper Literal 闭集收敛、preflight 显式 re-export、3 个旧行为测试同步为诚实期望 |
| F-04 | MINOR | `probe_telemetry_soak --pg` 用 `soak-{i}-{ID}` 前缀串作 task id，违反 ID 的 UUID4 契约 → 崩溃 | 修复：task id 用合法 UUID4，描述前缀只放 idempotency_key；SOAK PASS |

## 结论

M15 修复轮 WP0–WP8 全部完成；6 个 BLOCKER 均以独立探针复现原始路径并确认修复；
全量门禁 m0 profile 23/23 deterministic checks PASS；21 条 DoD 从原始验收条件重判
全部 PASS。**M15 判定 DONE（recheck PASS）**。M16 未动。
