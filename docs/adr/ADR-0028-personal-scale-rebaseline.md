# ADR-0028 — Personal Scale Rebaseline（RM-P2）

Status: Accepted
Date: 2026-09-02
Deciders: Eswink（single owner）
Scope: `docs/roadmap/MILESTONES.md` Post-M7 节（M17/M18/M19/SI-1/PA-1/PA-1R）、`BACKLOG.md`、`docs/INDEX.md`、`docs/roadmap/M16_COMPLETION_RECORD.md` 注记；docs-only，不改代码/Domain/API/schema，不改写 M0–M16 历史

## Context

M16 Distributed Execution + Remote Sandbox/Worker 已 DONE（2026-08-31），
并经 attempt-2 独立对抗复审维持 PASS（2026-09-01，
RECHECK-20260901-025-m16-attempt2；F-1..F-10 全部关闭）。此时路线图上
M17（GPU / HPC）、M18（Multi-user / Organization / RBAC）、M19
（Production Security / Governance + Backup/Recovery/SLO）均为 PLANNED，
其定义面向多用户/企业/HPC 集群环境。

实际产品现实（RM-P2 确认）：

- Research OS 当前服务于**单用户、个人长期使用的 Autonomous Research
  / R&D System**；
- 暂无 multi-user / organization 产品需求，无 Enterprise SaaS 部署目标；
- 当前有一台真实远程计算服务器；可真实验证的 GPU 资源仅为该服务器上
  的**单卡 GPU**；
- 没有可真实测试的 multi-GPU / multi-node / Slurm / HPC 环境。

既有规划原则（MILESTONES.md 规划节）本就要求"不为未来假设制造没有
当前需求的基础设施"。原 M17/M18/M19 定义与之冲突：会迫使建设无法
真实验证的基础设施，或诱导用 Fake/Mock 冒充完成。

## Decision

1. **M17 重定义**为 `Remote GPU Execution / Personal Scale Baseline`：
   让 M16 Distributed Execution Plane 在真实远程单卡 GPU Worker 上
   发现 GPU capability、调度 GPU-required task、建立真实 GPU
   container/runtime、运行真实计算实验、处理 OOM/CUDA/timeout/
   cancellation、记录 Artifact/Metric/Usage、进入 Evidence/Evaluation、
   完成真实 GPU Research Slice。不建通用 HPC 平台。
2. **M17 Deferred Scope**（不删除、不标记完成、不作为 M17 PASS 条件、
   禁止 Fake/Mock 宣称 supported）：multi-GPU scheduling、multi-GPU
   training、NCCL、distributed training、multi-node execution、Slurm、
   PBS、MPI、HPC scheduler、RDMA、InfiniBand、heterogeneous accelerator
   fleet、GPU autoscaling、cluster federation、HPC quota system。
   获得真实环境/需求时经新 ADR 重新激活。
3. **M18 DEFERRED** — `no current multi-user / organization
   requirement`。激活条件：出现第二个真实用户；团队共同使用；
   Organization/Project ownership 需求；共享服务器部署；对外服务；
   tenant isolation 成为真实需求；商业化或多人协作。当前不实现
   Tenant / Organization / cross-tenant data isolation / multi-user
   RBAC / tenant quota / tenant billing。
4. **M19 DEFERRED** — `Enterprise track not activated`，不得标记部分
   完成或 PASS。其中对单用户同样有价值的能力（backup/restore、
   secret hygiene、PostgreSQL/Artifact recovery、release/version
   truth、operational recovery）不"提前做 M19"，纳入 PA-1。
5. **新增非产品 Gate**：SI-1（M17 独立复审 PASS 后的全链集成评审：
   Research Objective → Control Plane → Distributed Scheduler →
   Remote Worker → Real GPU → Experiment → Artifact → Evidence →
   Claim → Evaluation → Usage/Cost，含 network failure / stale
   Worker / cancellation / GPU OOM / Artifact corruption / recovery
   故障面）、PA-1（个人生产验收，13 项范围）、PA-1R（独立个人生产
   复审）。**PA-1R PASS 后宣布 Research OS Personal Production
   Baseline = COMPLETE。**
6. **Post-baseline Operating Model**：PA-1R PASS 后不自动恢复
   M18/M19，进入 Usage-driven Development——后续开发优先级来自真实
   使用中的 capability/tool/skill/protocol/evaluation/runtime/
   reliability/UX/cost gap；路线由 `roadmap-driven infrastructure`
   转为 `real-usage-driven improvement`。
7. **M16 能力保留**：M16 已实现并验证的全部能力（含超出当前个人规模
   需求的 multi-worker、partition scheduling、lease/fencing、
   stale-result rejection、worker failover、远程 workspace/artifact
   完整性、分布式观测）保持 `Implemented and validated`，不删除、
   不弱化，原 M16 DoD 不降低。

## Consequences

- 正：路线与可真实验证的环境对齐；M17 Entry Gate（M16 PASS）已满足，
  可按新范围立项；M18/M19 保留完整定义与依赖 DAG，未来可无损重新
  激活；SI-1/PA-1/PA-1R 给出明确的"个人生产基线"终点与停止线。
- 负/风险：Deferred Scope 项在获得真实环境前无任何实现进度（有意为
  之）；若未来环境变化（第二用户/GPU 集群/商业化），需重新评估本
  ADR 相关决策并可能回到原 M17/M18/M19 定义。
- 记录：M0–M16 历史 Completion/Review Record 不因本 ADR 改写；
  `M16_COMPLETION_RECORD.md` 仅追加 RM-P2 注记。
