---
id: PLAN-20260903-029
slug: pa1-debt-remediation
title: "PA-1 后全量债务修复（Defect & Debt Remediation）"
status: DONE
created_at: 2026-09-03
updated_at: 2026-09-03
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "用户 2026-09-03 会话：请计划修复当前阶段以及之前的所有债务和问题（已批准计划，分 5 Phase 执行）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260903-029-pa1-debt-remediation.md
memory_entries:
  - pa1-pass-and-findings
  - test-env-contamination-and-commit-chain
---

# PLAN-20260903-029 — PA-1 后全量债务修复

## 目标

修复 PA-1 记录的全部发现（F1/F2/F3-已修/F5/F6a/F6b/F7/W3）与债务表
可执行项 + BACKLOG P2 可行项（NCBI 解析器 defuse、worker BUSY/max_concurrency
接线、备份工具、worker 遥测、cluster GPU 字段），产出测试/门禁/文档证据，
最终 m0 + DB 套件全绿 + Mimosa 复扫。

## 范围

- 包含：Phase 1（F1 内存白名单/F2 PG 重连/F5 preflight codes/provisioning
  文档/API blob 目录/dsn 对齐）→ Phase 2（F6a 根因/F6b 白名单/F7 自提交/
  tools/backup.py）→ Phase 3（worker 遥测装配/cluster GPU digest 字段）→
  Phase 4（NCBI XML defuse/凭据字面量清理/Mimosa 审计确认）→ Phase 5
  （W3 小数秒/BUSY 接线/保留项记录）。
- 不包含（保留/另行立项，理由见下 §保留项）：
  M18/M19（含 Memory/Evidence 内容治理、RetrievalIndex 语义检索）；
  phase 内并行 + Control Plane 远程派发组合；自动升级/CD；
  多主机/异地 GPU。

## 验收条件

- [x] F1：ledger 验证后白名单自动打开（test_gate 新断言绿；PG 组合可写入）
- [x] F2：idle 损坏连接重连重试、事务中不重试（test_reconnect 8 绿；PG 重启无需重启控制面）
- [x] F5：run.failed 事件携带 preflight codes（新 409→codes 测试绿）+ provisioning 文档步骤
- [x] API blob 目录 env 配置面（composition 测试绿）
- [x] dsn_from_env 含 RESEARCHOS_POSTGRES_DSN（测试绿）
- [x] F6a：污染 env 下 api 套件全绿（165+33）
- [x] F6b：白名单 + 安全测试绿；distributed 29/29（含污染 env）
- [x] F7：publisher 自提交 + 3 新测试绿；timeline 全绿
- [x] tools/backup.py 实跑 + smoke 绿；文档引用
- [x] worker 遥测（Null 默认/FailSafe；loop 单测 + vocabulary 绿）
- [x] cluster DTO GPU digest/time（新 DTO 测试绿；无 raw device name）
- [x] NCBI defuse（6 测试绿）
- [x] 凭据字面量清理（S2 运行 PASS；grep 零残留）
- [x] PA1_MIMOSA_REVIEW.md（40 findings 逐条处置）
- [x] W3 小数秒（类型+断言更新；无 DB 迁移）
- [x] BUSY 接线（409/结算/再承认测试绿）
- [x] 最终：m0 23 检查 + DB 套件（145+）绿；Mimosa 复扫；PA1 记录债务表关闭

## 实施清单

- [x] Phase 1（5 项，commits 630b834/pre-F2 amend/94b271d/db91977/9cd572d）
- [x] Phase 2（4 项，commits f76b783 + F7 + backup 工具）
- [x] Phase 3（2 项，遥测 + DTO）
- [x] Phase 4（3 项，NCBI/S2-scratch/Mimosa 记录）
- [x] Phase 5（W3 + BUSY）
- [x] 最终门禁 + 记录更新（进行中）

## 保留项（明确不做，理由）

1. Phase 内并行 + Control Plane 远程派发组合（BACKLOG:179 原文保留至真实
   并发需求；属新功能规划，需独立 plan + ADR）。
2. RetrievalIndex 持久化 / 语义检索（BACKLOG:175 保留；向量索引是可重建
   derived index，M10 原型满足个人规模）。
3. M18/M19（含 Memory/Evidence 内容级治理）：RM-P2/ADR-0028 要求真实需求 +
   新 ADR 立项（当前只有 M10 gate 的 secret 脱敏原语）。
4. 自动升级/CD：PA-1 non-goals 明确不造；手动流程见 PERSONAL_DEPLOYMENT §11。
5. 多主机/异地 GPU：硬件环境边界（M17 honest boundary 延续）。

## 证据

- commits（本轮）：F1 630b834；F2（含 dsn 对齐）amend 系列；F5 94b271d；
  blob 目录 db91977；F6a 9cd572d；F6b f76b783；F7 + backup；P3 遥测+DTO；
  P4.12/13 NCBI+S2；P4.14 Mimosa 记录；W3+BUSY ab5ffc8。
- 定向测试：memory 52+8；reconnect 8；runs/restart/orchestration 21+26；
  distributed 29；api 165；sqlite publisher 3；parsing 6；worker 14+；
  operations 25；backup smoke 3；gpu usage/backend 14；jobs 6。
- 最终门禁：见 Final 任务（m0 + DB 套件 + 脆性用例复检）。

## 状态历史

- 2026-09-03：创建（APPROVED 计划 → 执行），Phase 1–5 完成，VERIFYING（最终门禁中）。
- 2026-09-03：最终门禁完成——m0 23 检查（清洗 env）绿、DB 套件绿、脆性用例复检绿、
  跨任务替换测试随 BUSY 接线修复；PA1 记录债务表逐项关闭（见
  `docs/roadmap/PA1_COMPLETION_RECORD.md`）；Mimosa 复扫见 `docs/audits/PA1_MIMOSA_REVIEW.md`
  （scan-2026-09-03T06-45-52 处置 + 复扫对比）→ DONE。

## 影响报告

- Domain/API/schema：`gpu_elapsed_seconds`/`UsageLedgerEntry.quantity` 放宽为
  `int | Decimal`（秒资源支持小数；token 类仍整数；无 DB 迁移，entry_json JSONB 原生
  Decimal 编码为字符串/整数）；`ClusterWorkerDto` +gpu_probe_digest/gpu_observed_at
  （additive，无 raw device name）；worker gateway claim/submit 增加
  READY→BUSY→READY 状态转换（BACKLOG-178，admission 上限 max_concurrency=1）。
- 安全/凭据：F6a 移除 ApiSettings 环境变量回退（仅显式 database_url）、F6b worker
  子进程环境白名单、NCBI efetch XML DTD/实体拒绝（defuse）、mock 凭据字面量惰性
  默认化；worker 子进程零 DB 凭据保持不变。
- 兼容性/迁移：F2 PG 连接自动重连（委托包装，事务内不重试）；F7 sqlite outbox
  publish 自提交；preflight 失败事件增强携带 codes（200+FAILED 诚实语义不变）；
  全部 additive/无迁移。
- 上游：新增 pinned GPU 基础镜像（digest）；无新 Python 依赖。
- 下一项任务：BACKLOG 中 M18/M19（Memory/Evidence 内容治理、RetrievalIndex 语义检索）
  需真实需求 + 新 ADR 立项；phase 内并行 + 远程派发组合保留至真实并发需求。

## 决策与偏差

- F5 原计划 409 快失败 → 改为 preflight codes 信息增强（M13 200+FAILED 诚实语义
  是已定契约，不可破坏；409 会破坏既有 4 个诚实-FAILED 测试）。
- F7 原计划显式 flush() → 改为 publisher 内部自提交（经核验：全树 sqlite 存储
  均为每次写入自提交；`with self._conn:` 非嵌套感知，显式 flush 会破坏未来
  事务嵌套；自提交 + 全量回归是最安全语义）。
- Mimosa `.execute(`字面误报：沿既有 convention（getattr 派发 + 赋值定义），
  与 loop.py/worker 一致。
