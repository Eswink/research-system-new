---
id: PLAN-20260905-030
slug: pa1r-independent-production-reaudit
title: PA-1R Independent Personal Production Re-audit
status: DONE
created_at: 2026-09-05
updated_at: 2026-09-06
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-05 PART C — PA-1R Independent Personal Production Re-audit"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260906-032-个人生产最终复审v1.md
memory_entries: [pa1r-pass-baseline-complete, mimosa-scanner-false-positives, verify-recheck-claims-against-git]
---

# PLAN-20260905-030 — PA-1R Independent Personal Production Re-audit

## 目标

### 闭环授权与执行计划 v3（2026-09-06）

用户本轮明确要求：“根据上述结论，计划并解决所有BLOCKER ，直到PA-1R  阶段完全PASS”。
本轮继续同一验收任务，撤销仅审计不落地的限制；为关闭已经指出的源码发布身份阻塞，
将**范围白名单内的本地提交、离线 Git bundle、Personal Production Release Record**
列为必要交付步骤。该授权不包含 push、远端 PR/tag/release，不改变 M18/M19 停止线。
先完成代码修复子门禁，再冻结本地 revision，最后从该 revision 独立重建执行 PA-1R；
代码子门禁通过不等于 PA-1R 通过，任一 hard gate 失败均不得标记 COMPLETE。

- [x] V3-01：运行前持久化 ResearchRun/Manifest；中断后同 ID 重放；拒绝配置/镜像漂移。
- [x] V3-02：真实 GPU hard-kill → 同 Worker 重启 → 旧 generation 容器自动清理 → 新尝试完成。
- [x] V3-03：修复大于 2 GiB 显存计量溢出，核对 GPU 时间精度和迁移兼容性。
- [x] V3-04：运行最终候选的 lint/typecheck/tests、架构与契约/治理验证；保留失败和回归证据。
- [x] V3-05：仅显式暂存本任务文件，扫描暂存内容；本地不可变提交与离线 bundle。
- [x] V3-06：从已冻结 revision 新 clone，冻结安装、真实 DB/Artifact restore、中断跨恢复重放。
- [x] V3-07：真实 Worker/GPU/API/Scheduler/Collector 故障；Secret 六介质扫描及阳性对照。
- [x] V3-08：核对 Release Record 的 code/schema/protocol/runtime/upstreams；记录 14 项判定。

证据根：`scratch/PA1R闭环v1/`。保留此前报告作为已被后续证据纠正的历史，不静默改写。
执行环境：ChatGPT 经本地 MCP；不宣称已创建新的 Cursor IDE 窗口。

从 `main@687527394b41834a3e74e84e3ef5cfc01eaca750` 建立全新、零信任的个人生产
复审环境，不使用 PA-1 PASS 或旧 evidence 作为通过依据；通过实际部署、实际备份
恢复、故障注入、真实 GPU 研究运行和版本身份核对，独立判定 PA-1R。

只有全部 hard gate 独立成立且无未关闭 BLOCKER 时，才记录
`Research OS Personal Production Baseline = COMPLETE`。PASS 后停止，不启动 M18/M19。

## 范围

- 包含：
  - 从正式文档重建 clean deployment，识别 hidden manual state；
  - PostgreSQL custom-format backup 恢复到 clean PostgreSQL 16 target；
  - Artifact archive 恢复、全量/抽样 digest 与引用闭包核对；
  - 恢复态 `Run → Artifact → Evidence → Claim → Evaluation → Deliverable` 审计；
  - canary Secret 对 Git、backup、logs、telemetry、Artifact、exports 的扫描；
  - Remote Worker hard-kill/restart/reconnect/recovery；
  - 真实 GPU success/cancel/timeout/restart/cleanup；
  - Control Plane/Scheduler restart、Collector down 的业务持续性；
  - restored/clean 环境完整 Reference Research Run，核对 Artifact/Evidence/Evaluation/
    Usage/Deliverable；
  - code revision、DB schema、Worker protocol、runtime/upstream 与 Release Record 核对；
  - BLOCKER 的复现、根因、最小修复、回归、恢复/重跑和复审。
- 不包含：
  - 继承 PA-1 结论或把旧 `scratch/pa1-*` 当成本次运行证据；
  - 自动启动 M18/M19；
  - multi-user、Enterprise、multi-GPU/HPC、新产品能力；
  - push、远端 PR/tag/release；本地白名单提交、离线 bundle 与本地 Release Record 例外见闭环 v3 授权。

## 架构与数据流

- 所有者模块：Control Plane/API 与 scheduler 位于 `services/api`；Remote Worker 位于
  `services/worker`；PostgreSQL 与 Artifact Store adapter 位于 `adapters/postgres`；
  研究编排与 Evaluation/Usage/Deliverable 位于 `packages/application`。
- 上游输入：冻结配置、Protocol/Role/Agent/Model/Tool 契约、worker capability、
  pinned runtime/image、canary-only credential environment。
- 下游输出：PostgreSQL canonical Domain state、内容寻址 Artifact blob、Evidence/Claim、
  EvalReport、UsageLedger、Deliverable 与受限 telemetry。
- Canonical State：PostgreSQL Domain Entity；Artifact blob 必须由 canonical metadata digest
  引用，telemetry/log/UI/runtime checkpoint 均不构成业务真相。
- Port/Adapter：Application-owned ports 连接 PostgreSQL、Artifact、Worker gateway、
  execution backend 和 OTel adapter；Worker 不持 PostgreSQL 凭据。
- Policy/Security Gate：default deny、worker enrollment、lease/fence、GPU no-fallback、
  digest admission、secret redaction、telemetry fail-open/non-authoritative。
- 失败语义：at-least-once + idempotency + deduplication；worker LOST 后租约恢复，迟到
  result 被 fence；cancel/timeout/OOM 为结构化失败，不能伪造成科学负结果。

## 验收条件

- [x] AC-01：clean clone 按正式文档冻结安装并重建 stack，不依赖未声明本地文件或手工 DB。
- [x] AC-02：从本次生成的 PostgreSQL backup 实际恢复到 clean target，正式 Domain 表与
  schema/migration 身份可查询。
- [x] AC-03：从本次 Artifact backup 实际恢复，digest 校验与 orphan/missing 扫描通过。
- [x] AC-04：恢复态 `Run → Artifact → Evidence → Claim → Evaluation → Deliverable`
  抽样闭环成立，引用均可解析且 digest 一致。
- [x] AC-05：canary Secret 除授权配置源外，不出现在 Git、backup、logs、telemetry、
  Artifact 或 exports。
- [x] AC-06：Remote Worker hard-kill、gateway interruption 与 restart 后自动恢复，不手工改 DB。
- [x] AC-07：真实 GPU success、cancel、timeout、worker restart 均有运行证据且无 orphan
  container/GPU process。
- [x] AC-08：Control Plane/Scheduler restart 保留业务状态；Collector down 不破坏 canonical
  写入、Usage、Cost 或 Evaluation。
- [x] AC-09：restored/clean 环境完整 Reference Research Run 产生可核对的 Artifact、Evidence、
  Evaluation、Usage 和 Deliverable。
- [x] AC-10：code revision、DB schema、Worker protocol、runtime/upstream/image digest 与正式
  Release Record 一致；不存在未声明 drift。
- [x] AC-11：所有发现均完成 reproduce/root cause/minimal fix/regression/re-run/re-audit，
  或作为 non-blocking debt 有可证实理由；无未关闭 BLOCKER。
- [x] AC-12：适用 lint/typecheck/tests、system specification validator、Cursor governance
  validator 与独立 recheck 有新鲜证据。

## 实施清单

- [x] STEP-01：冻结基线并创建独立 clean clone、独立 compose project/ports/volumes。
- [x] STEP-02：执行 frozen dependency install、stack build/start、migration/health 核对。
- [x] STEP-03：在 canonical PostgreSQL + ArtifactStore 中生成完整研究真相样本。
- [x] STEP-04：生成本次 DB/Artifact backup，恢复到 clean target 并执行 cross-restore audit。
- [x] STEP-05：执行 canary Secret 多介质扫描。
- [x] STEP-06：执行 worker、GPU、durable component 与 collector 故障注入。
- [x] STEP-07：执行 restored/clean Reference Research Run 与运营面核对。
- [x] STEP-08：核对 Release/version identity 与 upstream pin。
- [x] STEP-09：修复并重新审计全部 BLOCKER。
- [x] STEP-10：创建独立 recheck 与 PA-1R 正式记录，更新索引和停止线。

## 子代理使用

运行证据由 root agent 直接取得。待实际证据冻结后，可用一波最多 3 个只读 reviewer
分别审查架构恢复闭包、安全/secret 与验收证据；reviewer 不得二次委派，其报告不自动
成为结论，必须由 root agent 复核。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| 1 | 运行证据后的架构、安全、验收独立复核 | 0/3 | 未启动（root agent 直接取证，逐 gate 复核由 RECHECK-032/033 承担） | `RECHECK-20260906-032` 全表 |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | baseline | `git status --short; git rev-parse HEAD; docker version; nvidia-smi` | HEAD 6875273；工作区 clean；Docker/GPU 可用 |
| EV-02 | AC-01..AC-10 | runtime | `scratch/PA1R闭环v1/续审release-v2/`（全链 drill/gate/secret 证据）+ `续审release-v1/`（前序候选证据） | 全部 PASS（RECHECK-20260906-032） |
| EV-03 | AC-12 | validators/recheck | `质量门禁_m0v1.json`（821e581，59/59）+ `质量门禁_m0_release-v3_f630b6d.json`（59/59）+ 密封扫描 seal `a4813342…` | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-05 | PA-1 文档仅作为待重放的操作说明，不作为本次 PASS evidence | 用户要求不使用 PA-1 结论 | 消除旧结论继承 |
| 2026-09-05 | 使用新 clean clone、独立 compose project/ports/volumes | 排除开发者主工作区与旧 volume 的 hidden state | 运行成本增加但证据独立 |
| 2026-09-05 | 不自动启动 M18/M19 | 用户明确停止线与 ADR-0028 | 无范围扩张 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-05 | — | DRAFT | 建立任务计划 | 用户 PART C 请求 |
| 2026-09-05 | DRAFT | APPROVED | 用户请求已明确授权完整 PA-1R 执行与最小修复 | authorization.ref |
| 2026-09-05 | APPROVED | IN_PROGRESS | 开始独立基线与运行环境重建 | EV-01 |

## 影响报告

## 续审 v2（2026-09-05，用户输入：继续）

不继承 v1 报告的各项 PASS。先验证正式命令、Gateway/Control Plane blob root、
Run→execution task 归属、跨 Run 用量隔离、真实 GPU 故障和证据闭包。
v1 将 release 作为唯一 blocker 的判断暂不作为事实；所有新发现须先复现再修复。
保留已有工作树改动及 v1 失败报告；新增审计文件采用中文名称与 v2 后缀。
Git commit/push/tag/release 仍未获显式授权，不通过扩大本计划范围自动执行。
当前执行上下文为 ChatGPT→本地 MCP；不得把它描述成已新建的 Cursor IDE 窗口。

- [x] V2-01：复现部署/归属/用量缺口，记录独立 before/after 回归。
- [x] V2-02：完成适用 lint/typecheck/tests 和契约/治理 validators。
- [x] V2-03：从明确封存的候选源码重建、恢复和重跑；核对真实 GPU 故障恢复。
- [x] V2-04：生成 v2 复检记录与 14 项最终判定；未通过 hard gate 不标 COMPLETE。

### 续审影响报告

- 新增 schema migration `010_GPU显存计量宽度v1.sql`：实库 `integer` 列对
  2^31 字节返回 SQLSTATE 22003；仅扩宽为 BIGINT，不改变 Worker protocol 1 或 JSON
  integer 契约，不引入新依赖。旧备份需先正常 restore，再由正式 migration runner 升到 010。
  必须验证旧行不变、迁移幂等、真实大于 2 GiB GPU job 的结果可结算；未完成之前不关闭发现。

- Domain/API/schema：审计开始时无变更；若出现 BLOCKER，仅在授权范围内做最小修复。
- 安全/凭据：只使用本次 canary，不使用或输出真实凭据；所有扫描结果需脱敏。
- 兼容性/迁移：重点核对 PostgreSQL 16、migration 001–009、Worker protocol `1`、
  GPU/OTel/OpenHands pins。
- 上游版本：不得在本任务顺手升级；只核对锁与实际 runtime。
- 下一项任务：仅 PA-1R 复审；PASS 后停止，不启动 M18/M19。


## 闭环继续执行 v4（2026-09-06）

本轮用户输入：接下来请继续执行任务。
已读回前轮 v5：5/5 门禁 exit 0，1,554 测试通过，mypy 708 文件通过，framework 8 项通过；
主树与 v5 的 1,342 文件清单无漂移。审计专用端口均空闲；未对无关现有进程进行终止。
代码封存子门禁：`.cursor/plans/rechecks/RECHECK-20260906-031-源码封存子门禁v1.md`。
下一步按已授权 v3 执行白名单本地候选 commit，再从该 revision 完整重建验收；最终 PA-1R gate 不继承子门禁结论。
历史 v2 的“未授权 commit”限定已由 v3 显式闭环计划取代；远端发布禁令不变。

- 2026-09-06 DONE：attempt-5/6 全部 hard gate 独立成立（`RECHECK-20260906-032` PASS）；
  `docs/operations/PA1R发布记录v1.json` 落盘（基线 821e581，后继规范化 f630b6d）。
  Commit 门禁根因（litellm 自动 dotenv + gitignore 吞源码 + 硬编码 collector 名）闭环，
  遗留债务清偿见 `PLAN-20260906-031`。不启动 M18/M19。
