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

`code digest` = 代码出处/内容的独立 provenance pin（由请求方可选提供，
例如代码来自 repository commit 而非工作区文件的场景）。未提供时，代码
内容由执行前 `workspace snapshot` 覆盖；ReproducibilityAudit 对此发出
`CODE_DIGEST_NOT_PINNED` WARNING（诚实标注，不升级为 FAIL）。

## 9. Remote Workspace Transfer (M16)

- `WorkspaceBackend.export_bundle/import_bundle`：canonical bundle（sorted
  path/sha256/base64，`adapters/workspace/bundle.py`）+ 双重完整性校验
  （bundle 字节经 ArtifactStore 内容寻址 + 物化后工作区树 digest vs
  snapshot digest）。
- 输入 immutable：远程执行只接受 snapshot digest + artifact ref；符号链接与
  路径穿越在导出/导入两侧均被拒绝；物化失败回滚工作区目录。
- `ExecutionBackend.execute` 增可选 `cancelled` 协作取消回调（Docker 轮询 ->
  kill -> CANCELLED）；`RemoteExecutionBackend` 超时下发 cancel。
