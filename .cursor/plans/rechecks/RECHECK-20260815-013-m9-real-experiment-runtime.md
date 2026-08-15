---
id: RECHECK-20260815-013
plan_id: PLAN-20260815-013
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-15
completed_at: 2026-08-15
reviewer: root-agent-independent-pass
baseline_ref: null
checked_head: null
---

# RECHECK-20260815-013 — M9 Real Experiment Runtime 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260815-013-m9-real-experiment-runtime.md`
- 验收条件：AC-01..AC-10
- 变更范围：`adapters/execution/`（新增）、`adapters/workspace/`（新增）、
  `packages/domain/experiments.py`/`experiment_state.py`/`reproducibility.py`
  （新增）、`packages/domain/workspace.py`/`artifacts.py`（扩展）、
  `packages/application/experiments/`（新增）、`packages/application/artifacts/`
  （新增）、`adapters/sqlite/artifact_store.py`、`adapters/fakes/`、
  `adapters/openhands/workspace_adapter.py`（docstring）、
  `tests/adapters/execution|workspace/`、`tests/application/artifacts|experiments/`、
  `tests/contracts/registry.py` + `test_execution_backend_docker.py`、
  `tests/domain/test_experiments.py`/`test_artifacts.py`、
  `tests/tooling/test_validate_bundle_dockerfile.py`、`pyproject.toml`、
  `uv.lock`、`.github/workflows/m0-quality.yml`、`UPSTREAM_COMPONENTS.yaml`、
  `docs/references/LICENSE_MATRIX.md` + `docs/references/upstream/M9_DOCKER_QUALIFICATION.md`、
  `docs/architecture/PORTS.md`、`docs/roadmap/M9_COMPLETION_RECORD.md`、
  `docs/roadmap/MILESTONES.md`、`BACKLOG.md`、`docs/INDEX.md`、
  `schemas/reproducibility_audit_v1.schema.json` + `export_bundle_v1.schema.json`、
  `.cursor/skills/system-spec-check/scripts/validate_bundle.py`（DOCKERFILE 来源支持）
- 基线：M7 DONE（2026-08-14）；未创建 commit（Git Hard Boundaries 默认）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | 变更清单对照用户批准的 Cursor Plan 三 work packages；`packages/application/experiments/` 依赖方向（只依赖 ports/domain，不 import adapters）；ExecutionBackend/WorkspaceBackend/ArtifactStore 职责边界保持 | PASS |
| G-02 | 验收条件 | AC-01..AC-10 逐条对照 M9_COMPLETION_RECORD DoD 证据表 | PASS |
| G-03 | lint/typecheck/test | ruff check（packages/adapters/tests 全过 + .cursor F,I）、ruff format --check（293 files）、mypy strict（281 files）、m0 profile 18/18 PASS（含 1298 pytest 本机 Docker 实跑） | PASS |
| G-04 | 安全与凭据 | 容器默认 deny 断言（network none/Privileged False/CapDrop ALL/no-new-privileges/ReadonlyRootfs/Tmpfs/PidsLimit/Memory/NanoCpus 逐项 `docker inspect` 断言测试）；env 白名单；无新增凭据；secret redaction 回归（test_common_contract） | PASS |
| G-05 | 兼容性与迁移 | ExecutionSpec 新字段全部可选（既有 fixtures 未改必填）；ArtifactRetentionPolicy.parse 兼容字符串；contract suite 注册表语义不变；Sqlite artifacts 表 schema 未变（仅状态机迁移表扩展）；governance validate PASS | PASS |
| G-06 | 计划、记忆、供应链 | UPSTREAM_COMPONENTS docker_py 与 sandbox image 条目通过 validate_bundle（含 DOCKERFILE 来源形态校验 + 6 回归测试）；LICENSE_MATRIX 双条目；ALL_PLAN 唯一索引已加 | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | info | MILESTONES M9 Inputs 声称的 Experiment 实体在代码中不存在（调查实证） | 在 M9 Domain 新建（属 M9 范围）；已记录于完成记录 |
| F-02 | info | OpenHands DockerWorkspace 容器链路 M6 "smoke" 实际不存在 | 裁决 mapping-only；真实链路改由 adapters/execution 承担并全量验证 |
| F-03 | info | retention 定时调度、Experiment 实体持久化 | 新增 BACKLOG P2/P1 条目，归属 M14 |
| F-04 | info | 容器 rootfs 只读等为进程级隔离，非 VM 级 | 记录为已知残余风险（M9_DOCKER_QUALIFICATION §3），系统级强化属后续 Milestone |

## 结论

- 结果：`PASS`
- 理由：六项 gate 全部通过；M9 DoD（MILESTONES.md 权威定义）逐项有
  独立可执行证据（m0 profile 全绿含真实容器测试、validate_bundle、
  governance）；Findings 均为已记录不阻塞项。
- 后续动作：计划进入 DONE；M9 停在阶段边界；并行组 1 剩余 M10/M11
  待立项。
- 工程记忆：无可复用事实（M9 交付为产品代码、测试与契约资产；无跨
  任务可复用的工程操作事实需写入 memory）。