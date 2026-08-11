# Workspace & Execution Runtime v0.4.0

## 1. Research Workspace

逻辑视图：

```text
/sources
/data
/code
/experiments
/artifacts
/notes
/reports
/system
```

不等于宿主机目录。

## 2. WorkspaceLease

```text
workspace_id
agent_session_id
base_snapshot
read_scopes
write_scopes
network_profile
compute_profile
expires_at
heartbeat
```

无 Lease 不得写入。

## 3. Role-aware Policy

### LiteratureScout
只写 notes/artifacts。

### ExperimentEngineer
隔离可写 code/experiments。

### Reviewer
默认只读。

### ResearchWriter
只写 deliverable scope。

## 4. 并发

可写 Agent 默认独立：

```text
git worktree
or
isolated snapshot/volume
```

不共享 mutable tree。

## 5. ExecutionBackend

```text
OpenHands LocalWorkspace    # 仅可信开发
OpenHands DockerWorkspace   # MVP 默认
OpenHands RemoteWorkspace
ApptainerWorkspace          # HPC/rootless
SWE-ReX Adapter             # 可选远程/并行
Managed MicroVM Adapter     # 可选生产
```

Research OS 只依赖端口。

## 6. Trust Profiles

```text
TRUSTED_LOCAL
SANDBOXED_STANDARD
SANDBOXED_RESTRICTED
HARDENED_UNTRUSTED
```

不同 Profile 控制：

- mounts
- egress
- package install
- CPU/RAM/GPU
- PID/process
- time
- secrets

## 7. Snapshot / Merge

```text
WorkspaceLease
→ Agent changes
→ WorkspaceSnapshot
→ deterministic validation
→ diff/review
→ merge
```

## 8. Experiment Reproducibility

ExperimentRun 绑定：

```text
workspace snapshot
code digest
environment digest
input digest
command/spec
seed
resource profile
artifacts
```
