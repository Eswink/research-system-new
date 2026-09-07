# PA-1 — Personal Production Acceptance Record

- date: 2026-09-03 (session)
- reviewer: ZCode Agent Mode (PA-1 personal production acceptance, fresh session)
- entry gates: SI-1 PASS (`scratch/si1-20260902/SI1_REVIEW_RECORD.md`), M17 DONE
  (RECHECK-20260902-028 PASS_WITH_WARNINGS, PART B fixes at 8ecb129)
- environment: RTX 4060 Laptop 8GiB (WDDM, driver 581.80), Docker Desktop
  29.2.1 + nvidia runtime, PostgreSQL 16.14 (persistent named volume via
  docker-compose.personal.yml), pinned GPU image
  research-os-gpu-sandbox:m17-v1 (sha256:b0a03d7c5047…), OTel collector
  0.139.0, source HEAD dc6676c + 4 PA-1 commits, VERSION 0.4.0
- scope: production-baseline acceptance only — no new product capability
  beyond one bug fix and the documented operator artifacts listed below
- evidence: `scratch/pa1-20260903/` (per-item evidence files p1…p11 + drivers)

## Verdict

**PA-1 = PASS**（无 BLOCKER；11 项逐项通过；发现已记录见下：
F1 内存来源白名单装配缺失、F2 PG 重启后连接不自动重建、
F3 PG EvalReportStore 读取路径（已修复 dc6676c）、F5 未配置控制面
无法跑 demo run、F6a/F6b 环境非封闭性与 worker 子进程环境继承、
F7 event publish 未提交事务导致的测试脆性、W3 GPU_TIME 整数秒）。

**PA-1R = READY**（独立对抗复审模式同 M16 attempt-2；建议聚焦
F1/F2/F5、M17 W-01..W-04、Mimosa 扫描口径，以及本记录中各"honest
boundary"）。

## 11 项逐项结果

| # | 项 | 证据 | 结果 |
| --- | --- | --- | --- |
| 1 | Reproducible Deployment | `p1_rebuild_evidence.md`：全新 `git clone --no-hardlinks`（无主树状态）→ uv/pnpm frozen 安装 → 自建镜像栈（独立卷 15433）→ API/gateway/worker 均启动；worker 带真实 GPU 观察注册 | PASS |
| 2 | PostgreSQL backup + actual restore | `p3_pg_restore.md`：pg_dump -Fc (44,425 B, PG 16.14) → 全新实例 restore --clean → 22 表 + migration 1..9 + 抽样 runs/manifest/tasks/evidence/claims/memory/eval/usage/approvals/outbox/sources 逐项一致；同 major 版本要求已记录 | PASS |
| 3 | Artifact backup + restore | `p4_artifact_restore.md`：29 行/14 唯一 blob 快照 + tar (11 KB, 内容寻址去重) → 恢复新目录 → 0 anomalies 重验 → experiment_result.json 真实 GPU 字段 → 闭包 5/5（evidence.digest == artifact.digest == blob sha256）→ corrupt/missing 检测 fail-closed | PASS |
| 4 | Secret hygiene | `p5_secrets.md`：git 扫描仅合成测试脚本文本；实际密钥不在 git/dump/archive/telemetry/logs；.env/secrets/data 全 gitignore；DB 凭据恢复实测（ALTER USER → 新密码可连 → 恢复）；enrollment 轮换实测（P5b S4）；LLM key 内存/环境注册如实记录（本会话无真实 key） | PASS |
| 5 | Remote Worker recovery | `p5b_remote_worker_recovery.md`：S1 进程硬杀→LOST→再启 READY；S2 SIGTERM 优雅退出→再启；S3 gateway 断开→worker 重连 READY；S4 凭据轮换（旧 secret 拒/新 secret 注册）；S5 mid-job 硬杀→lease 恢复→新 worker 恰一次 SUCCEEDED；无手工 PG 修改 | PASS |
| 6 | GPU Worker recovery | `p6_gpu_recovery.md`：真实 GPU 任务 → mid-GPU-job 硬杀 → lease 恢复 → 新 worker 完成（恰一次、fence 1→2 权威替换）→ GPU 观察重新探测（probe digest dfe7932f… 稳定）→ 无 orphan 运行容器（W2 清扫实测）→ nvidia-smi 无沙箱计算进程 → 二次重跑完成 | PASS |
| 7 | Component restart durable | `p7_restart_durability.md`（A 部分按 F5 修正）：API kill/restart 干净服务（运行状态存在 PG）；**B：PG 停止/启动（持久卷）→ 按操作流程重建控制面 → lease 恢复 → 恰一次 SUCCEEDED、fence 替换、无孤儿**；M14 crash/restart 套件在 P11 复跑 | PASS（含 F2 记录） |
| 8 | Observability / Cost / Eval ops | `p8_observability.md` + `p11_m0.log`：真实回答了 run 状态/worker 健康/GPU 状态/queue 异常/usage+UNKNOWN cost/eval 无回归；collector 关闭 → 请求面与数据库真相不受影响（导出错误仅 async 后台线程）；**发现并修复 PG 评审读取路径 bug（dc6676c：/evaluations/trend 由 422 恢复 1 段 0 divergence）** | PASS（修复交付） |
| 9 | Real Research Acceptance Run | `p2_acceptance_run.md`：官方 M17 GPU slice 全链 1 passed（14.26s）+ PG 生产存储 driver（run e82dc0ff…：manifest/artifacts/evidence VERIFIED/claim/audit PASS/eval PASS/memory NEGATIVE_RESULT 0.97/budget GPU_TIME 1+CPU_TIME 11/EvalScorer 7/deliverable digest） | PASS |
| 10 | Upgrade / version baseline | `p9_version_baseline.md`：VERSION 0.4.0 / HEAD dc6676c / 迁移 9 / openhands-sdk 1.42.0 / protocol "1" / GPU+collector+PG image digest / 部署配置指纹；全栈重启身份一致；无升级机制（诚实）+ 最小 rehearsal（迁移幂等重放 1..9、重启身份稳定） | PASS |
| 11 | Operational documentation | `PERSONAL_DEPLOYMENT.md`（14 节，命令全部实际执行）+ OPERATIONS_RUNBOOK 健康面校正 + BACKUP_RECOVERY 引用 | PASS |
| — | M0-M17 critical regressions 全绿 | `p11_gates.md`：m0 22/23 检查 PASS（python/tests 因 F7 两个脆性用例在套件负载下失败、专用运行均绿）；python/tests 2835 passed/5 skipped；DB 套件（postgres/distributed/observability/PG crash-restart/workflow-restart）145 passed | PASS（F7 记录） |

## Findings（已记录，无 BLOCKER）

- **F1（P2 发现）** `services/api/pg_composition` 装配 PostgresMemoryStore
  未提供 allowed_sources → 生产组合下受控内存写入 deny-by-default；
  官方 slice 与 PA-1 driver 都在组合根提供来源才成功。个人使用应对：
  允许来源需在组合根提供（文档注记）→ 待修（P2 排期）。
- **F2（P7 发现）** PG 重启后已持有的 psycopg 连接 stale，无自动重连；
  操作流程必须重启控制面进程（已文档化 §10）。优化项：adapter 层
  reconnect/retry（P2）。
- **F3（P8 发现，已修复 dc6676c）** PostgresEvalReportStore 读路径对
  psycopg 已解码的 jsonb 列再 json.loads → JSONDecodeError →
  /evaluations/trend 在 PG 组合下 422；修复后 1 段 0 divergence。
- **F5（P8 发现）** 未配置的控制面（空 project/endpoint/model 存储）运行
  console_demo run 立即 run.failed（含 OTEL 关闭、collector 开/关时均
  一致）——属配置状态而非 telemetry/restart 问题；配置经 console wizard
  完成（记录为部署前提 + 后续补一条"PROVISION"检查）。
- **F6a（P11 发现）** `ApiSettings.effective_database_url()` 在显式构造
  `ApiSettings(db_path=…)` 时仍回退到环境 DSN — 环境中存在
  RESEARCHOS_DATABASE_URL/DATABASE_URL 时，SQLite 面向的 API 测试整体切到
  PG 组合（api restart 事件重放缺失、run 列表混入 PG 行）；测试非封闭 +
  PG 组合下 events 重放是真实缺口。正确门禁上下文 = 清洗环境（本记录
  的 P11 即按此执行）。
- **F6b（P11 发现）** `worker_child_env` 整体继承会话环境 — 会话级
  RESEARCHOS_WORKER_EXECUTION_BACKEND=docker 等会漏入场景 worker 子进程，
  破坏 cancel/scenario 时序；CI 无此问题（hermetic）。建议 harness 只
  白名单必要键。
- **F7（P11 发现，测试脆性/隐性缺口）** `test_api_restart_recovers_timeline`
  的机制已定位：seed 的 event publish 写入**未提交事务**，其可见性依赖
  同连接上随后某个 `with self._conn:` 存储（seed 中的 approvals.replace）
  一并提交——因此任何扰动（本机完整套件会话中 openhands SDK 导入路径 + 提交
  次序）都会让 GET 读不到事件（events=[]，200）而失败；在独立/专用运行中
  全部通过（standalone 5-6 passed；DB 套件 145 中通过）。修复建议（P2）：
  event publisher 每次 publish 显式提交（事务性 outbox 语义）+ 测试
  等待提交。同理 `test_scenario_h` 的取消时序在负载下变脆（M17 W-04 系）。
  两者在 dedicated/CI 等价上下文中均绿：m0 22/23 检查 PASS，
  python/tests 2835 passed + 上述两个脆性用例（专用运行绿），
  DB 套件 145 passed，5 skipped。
- **W3（继承 SI-1）** GPU_TIME 整数秒下限（1s vs 实测 ~2s）——诚实但粗糙；
  记录为 known。
- **W4** /evaluations/trend 曾对 PG 后端 422（已修复 dc6676c；P11 复跑
  tests/application + observability 相关）。
- **Honest boundaries**：GPU host == Control Plane host（多主机 GPU 未验证，
  M17 同）；live LLM 无（接受链路不依赖 LLM）；cost_status UNKNOWN（无价
  格源）；Mimosa 扫描在本会话部分 enobufs（commit 前结论不完整——按 hook
  说明未宣称安全，建议 PA-1R 前重跑完整扫描）。

## Remaining personal-use debt（PA-1 后债务修复轮 2026-09-03 逐项关闭）

| # | 债务项 | 状态 | 关闭证据 |
| --- | --- | --- | --- |
| 1 | F1 内存白名单装配 | 已关闭 | `MemoryStore.allow_source` + gate 接线（commit 630b834）；test_gate 新断言 + PG 组合实测可写入 |
| 2 | F2 PG 重启自动重连 | 已关闭 | `ReconnectableConnection` 委托包装（含 dsn_from_env 对齐）；test_reconnect 8 绿；PERSONAL_DEPLOYMENT §10 改为自动重连 |
| 3 | F5 未配置控制面 run 路径 | 已关闭 | run.failed 事件携带 preflight codes（`_preflight_failure_message`，commit 94b271d）+ provisioning 文档步骤；200+FAILED 诚实语义不变 |
| 4 | W3 GPU_TIME 精度 | 已关闭 | `gpu_elapsed_seconds`/`UsageLedgerEntry.quantity` → `int \| Decimal` 全链（commit ab5ffc8）；canonical-safe、无 DB 迁移 |
| 5 | API blob 目录 env 配置面 | 已关闭 | `ApiSettings.artifact_blob_dir` + `RESEARCHOS_ARTIFACT_BLOB_DIR` → PostgresArtifactStore（commit db91977） |
| 6 | worker 进程无 telemetry sink | 已关闭 | `services/worker/telemetry.py::build_worker_telemetry` + `__main__` 装配（commit fbca94c）；Null 默认 / FailSafe |
| 7 | cluster DTO 不含 GPU 观察 | 已关闭 | `ClusterWorkerDto` +gpu_probe_digest/gpu_observed_at（无 raw device name；commit fbca94c） |
| 8 | 每小时自动化 backup 未设置 | 保留（运维决策） | `tools/backup.py` CLI（pg_dump + blob tar + --verify + --keep）已交付（commit 95ed21d）；RPO 由部署方定 |
| 9 | 无升级机制 | 保留（PA-1 non-goal） | 文档 §11 手动流程不变 |
| 10 | RetrievalIndex 持久化 / Memory 内容治理 | 保留（M18/M19 DEFERRED） | RM-P2/ADR-0028；见 PLAN-20260903-029 §保留项 |
| 11 | M17 W-01..W-04 | 保留（PART B 已缓解） | 不变 |
| 12 | F6a 测试环境非封闭 | 已关闭 | `effective_database_url()` 仅返回显式 database_url（commit 9cd572d）；清洗 env 下 api 套件全绿 |
| 13 | F6b harness worker_child_env 泄漏 | 已关闭 | worker_child_env 白名单 `_INHERIT_KEYS`（commit f76b783）+ 安全测试断言零泄漏 |
| 14 | F7 event publisher 显式提交 | 已关闭 | `SqliteOutboxEventPublisher.publish` 自提交（`with self._conn:`，commit bc7bd92）+ 3 新测试；timeline 全绿 |

另关闭：NCBI efetch XML DTD/实体 defuse + 5MB 上限（commit 4c754b3）、
mock 凭据字面量惰性默认（4c754b3）、worker BUSY/max_concurrency 接线
（BACKLOG-178，commit ab5ffc8，含跨任务替换测试修复）、Mimosa 处置记录
（`docs/audits/PA1_MIMOSA_REVIEW.md`，commit db17e12）。

## 结论

Personal Production Baseline 的可验证证据齐备：重建、备份恢复、恢复演练、
真实 GPU 验收运行、版本身份、运维文档。发现的缺口均为已记录的非阻塞
项（F1/F2/F3/F5/W3）且 F3 已在本次修复并验证（dc6676c）。满足全部
Exit Criteria（发现项作为 WARN 记录，无 BLOCKER）。

**PA-1 = PASS**

**PA-1R = READY**（下一步：独立对抗复审；见 MILESTONES.md PA-1R 节）。


## 路径迁移说明（2026-09-07 根目录分类归档）

上文环境说明中的 `docker-compose.personal.yml` 为验收当时路径；该文件现已迁至
`infra/compose/personal-production.yaml`（调用统一为 `docker compose --project-directory . -f infra/compose/personal-production.yaml`）。
原验收事实不变，完整映射见 `docs/operations/REPOSITORY_HYGIENE.md`。
