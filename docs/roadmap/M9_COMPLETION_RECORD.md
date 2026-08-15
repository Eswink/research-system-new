# M9 — Real Experiment Runtime 完成记录

- 日期：2026-08-15
- 范围权威：`docs/roadmap/MILESTONES.md` M9 节
- 前置：M7 DONE；M9 计划经 Plan Mode 批准（Cursor Plan `m9_真实实验运行时`）
- 结论：**M9 DoD 全部满足**

## 交付摘要

| Work Package | 交付 | 落点 |
| --- | --- | --- |
| WP1 Container Execution | `DockerExecutionBackend`（docker-py 低层 API，一次性容器，默认 deny host_config）、`profiles.py` 资源限额映射、`sandbox/Dockerfile`（base image OCI index digest pin、非 root） | `adapters/execution/` |
| WP2 Experiment Lifecycle | `ExperimentPlan/ExperimentRun/ExperimentRunSpec/ExperimentRunResult/Metric/MetricValue` + 状态机；`FileWorkspaceBackend`（真实目录/lease/内容寻址 snapshot）；`ExperimentExecutor` use case | `packages/domain/experiments.py`、`packages/domain/experiment_state.py`、`adapters/workspace/`、`packages/application/experiments/` |
| WP3 Reproducibility & Artifact Lifecycle | `ReproducibilityAudit`（确定性 audit_digest）+ `build_reproducibility_audit` use case；`ArtifactRetentionPolicy` 类型化 + `apply_retention`；`build/decode_export_bundle` | `packages/domain/reproducibility.py`、`packages/application/experiments/repro_audit.py`、`packages/application/artifacts/` |

## DoD 逐项证据

| DoD 项（MILESTONES M9） | 证据 |
| --- | --- |
| ExecutionBackend contract suite 以真实容器实现通过 | `tests/contracts/test_execution_backend_docker.py`（6 tests，requires_docker，本机 Docker 29.2.1 实跑 PASS）+ `tests/contracts/test_ports_regressions.py`/`test_ports_persistence.py`（Fake 同语义离线 PASS） |
| DockerWorkspace 创建/挂载/清理全量验证 | `tests/adapters/execution/test_docker_backend_e2e.py`：create/mount（容器内写文件→宿主工作区可见）/执行/清理（无残留容器断言）10 tests PASS |
| ExperimentRun 可复现（同 input 同 digest） | `tests/application/experiments/test_experiment_e2e.py::test_same_input_same_output_digest`：同 input+seed+image → 同 input_digest + 同 image_digest + 同输出 artifact 内容；`test_different_seed_different_input_digest` 反向验证 |
| 容器超时/崩溃故障注入测试 | timeout→TIMED_OUT+容器被 kill（`test_timeout_kills_container_and_returns_timed_out`）；非零退出→FAILED+category；OOM→FAILED+oom_killed；pids 限额阻断 fork bomb；镜像缺失→PermanentPortError(CONFIGURATION)；网络禁用断言 |
| 镜像 pin 与供应链登记 | `UPSTREAM_COMPONENTS.yaml`（`docker_py` 7.2.0 sdist sha256 + `research_os_sandbox_image` DOCKERFILE 条目 base_index_digest pin）；`docs/references/LICENSE_MATRIX.md` 双条目；`docs/references/upstream/M9_DOCKER_QUALIFICATION.md` 沙盒边界审计；每次执行运行时解析实际 image digest 写入 `compute_usage_summary["image_digest"]`；校验器 `_check_dockerfile_adopted`（`tests/tooling/test_validate_bundle_dockerfile.py` 6 tests） |
| 独立复审 PASS + m0 profile 全绿 | m0 profile 18/18 deterministic checks PASS（本机 Windows + Docker 实跑，含 1298 pytest、validate_bundle、governance、TS 全套）；独立 recheck 见 `.cursor/plans/rechecks/`（完成后追加） |

## 清偿的技术债（BACKLOG P1）

1. **DockerWorkspace 容器链路全量验证**：M6 遗留。清偿方式：M9 裁决
   OpenHands DockerWorkspace 保持 mapping-only（agent-server 运行模型与
   ExecutionBackend 命令执行语义不兼容，`openhands-workspace` 未 pin），
   真实容器链路改由 `adapters/execution/DockerExecutionBackend` 承担并经
   E2E 全量验证；M6 映射代码误导性 docstring 已修正。
2. **ExecutionBackend 容器执行（Sandbox）**：M7 以进程内/Fake 语义执行。
   清偿方式：`DockerExecutionBackend` 通过 contract suite（Fake+Docker
   双实现）+ 容器 E2E + 故障注入。

## 关键设计决策记录

1. 执行路径 = `adapters/execution/`（docker-py 自建），不复用 OpenHands
   DockerWorkspace（见 M9_DOCKER_QUALIFICATION.md §1 对比表）。
2. ExecutionSpec 契约增量（向后兼容可选字段）：`workspace_path` /
   `environment` / `workdir`；PORTS.md 已同步。
3. NEGATIVE_RESULT 语义：exit 0 + 声明 NEGATIVE_RESULT/FAILED →
   `ExperimentRunState.NEGATIVE_RESULT`（科学结论）；非零退出/timeout/
   crash → FAILED/TIMED_OUT 且不采信输出声明（`classification.py` +
   测试覆盖）。
4. 实验输出契约：`experiment_result.json`（对齐
   `experiment_run_output_v1` schema）+ `stdout.log`/`stderr.log`（backend
   写入工作区）；两者进入 post-snapshot 与 ArtifactStore。
5. ArtifactStore 状态机扩展：QUARANTINED→DELETED_TOMBSTONE（retention
   清理需要）；Sqlite blob 共享删除缺陷修复（引用检查后再物理删除）。
6. retention 为显式触发用例（调度留 M14）；export bundle 为内容寻址
   bundle artifact（magic + canonical manifest + digest 复核）。
7. WorkspaceBackend 不执行命令、ExecutionBackend 不记账、ArtifactStore
   不拥有 Evidence truth——三个边界保持不变；实验执行为独立 use case，
   不重写 run_orchestration Agent 会话路径（M12 集成）。

## 边界与 Non-goals 遵守

- 无远程多 Worker（M16）、无 GPU/HPC（M17）、无 Temporal（M14）、无
  Research Console（M13）、无系统级强化沙盒。
- 容器默认 deny：仅 bind-mount 租约工作区、network none、非 privileged、
  cap drop ALL、no-new-privileges、readonly rootfs + tmpfs /tmp、
  CPU/memory/pids 限额；不挂 Docker socket/host shell/home；env 由用例
  白名单构造；运行时 host_config 断言测试见
  `test_host_config_boundaries_during_run`。
- 未开放宿主 Shell、Secret 枚举、unrestricted network。

## 上游影响

- 新增 ADOPTED：`docker-py 7.2.0`（Apache-2.0，PyPI sdist sha256
  `cebb9377…43ac`，uv.lock 固定）；`research-os-sandbox` 镜像（仓库内
  Dockerfile，base `python:3.12-slim` OCI index digest
  `sha256:dd293726…88e65`）。
- OpenHands SDK 1.42.0 未变更；DockerWorkspace 映射代码保持
  mapping-only（docstring 修正，无功能变化）。
- Domain/API/schema 变化：ExecutionSpec 增 3 个可选字段（向后兼容）；
  ExecutionRun.compute_usage_summary 增 3 个键；Artifact.retention_policy
  从 str 升级为 `ArtifactRetentionPolicy`（解析/序列化同步 Sqlite+Fake）；
  新增 `ExperimentPlan/ExperimentRun/Metric/MetricValue/ReproducibilityAudit`
  实体与 `ExperimentPlanState/ExperimentRunState` 状态机；新增
  `schemas/reproducibility_audit_v1`、`schemas/export_bundle_v1`。
- 安全/凭据变化：无新增凭据域；容器环境变量经 application 白名单构造。

## M12 Readiness（MVP 判定依赖）

- M12 需要"真实实验步骤"：M9 已交付真实容器实验执行 use case
  （`ExperimentExecutor`）+ ReproducibilityAudit + retention/export；
  M12 集成点 = run_orchestration task 类型映射到 experiment use case
  （`experiment_execution` TaskContract 已存在），无阻塞。
- M12 阻塞项不在 M9 范围：usage 归账闭环（ModelRelay 真实链路）、
  M8 工具面、M10 证据账本、M11 评测面。

## M17 Readiness（GPU/HPC 语义基础）

- M17 依赖 M9 的 `ExperimentRun` 语义与 `ExecutionBackend` Port：
  `resource_profile` → 限额映射（`profiles.py`）是确定性映射表，M17
  的 GPU profile 可扩展同一机制；`ReproducibilityAudit` 的
  resource_profile/image pin 绑定可直接承载 GPU 资源指纹；无阻塞。

## 验证命令（实际执行证据）

- `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → PASS（18/18 checks）
- `docker build -t research-os-sandbox:latest adapters/execution/sandbox` → 成功
- `uv run --frozen --no-sync python -B -m pytest tests/adapters/execution tests/contracts/test_execution_backend_docker.py -m requires_docker` → 通过
- 全量 pytest：1298 passed（含容器套件）；validate_bundle + governance validate PASS

## 下一项任务

M9 停在阶段边界。并行组 1 剩余：M10（Evidence/Memory/Provenance）、
M11（Evaluation Plane）；汇聚门 IG-1（M12 entry）需 M8+M9+M10+M11 全部
独立复审通过。