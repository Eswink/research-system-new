# M9 Docker / Execution Sandbox Qualification

- 日期：2026-08-15
- 范围：M9 Real Experiment Runtime 的容器执行面
- 结论：docker-py 7.2.0 + 仓库内 sandbox Dockerfile = ADOPTED；
  OpenHands DockerWorkspace = mapping-only（不承接 M9 执行语义）
- 权威 pin：`UPSTREAM_COMPONENTS.yaml`（`docker_py`、`research_os_sandbox_image`）

## 1. 决策：自建 DockerExecutionBackend，不复用 OpenHands DockerWorkspace

M6 已留下 `build_docker_workspace` 映射代码（`adapters/openhands/workspace_adapter.py`），
但 OpenHands DockerWorkspace 的运行模型与 ExecutionBackend Port 语义不兼容：

| 维度 | OpenHands DockerWorkspace | ExecutionBackend Port（M5 冻结） |
| --- | --- | --- |
| 运行模型 | 长驻 agent-server（HTTP + X-Session-API-Key），agent 循环驱动 | 一次性命令执行（`execute(spec, timeout) -> ExecutionRun`），同步语义 |
| 命令级 timeout | SDK 无命令级 timeout（M6_ADAPTER_DESIGN_NOTES） | TIMED_OUT 状态化返回 |
| stdout/stderr | 经事件流，无 digest 采集面 | `stdout_digest`/`stderr_digest` 必须采集 |
| 依赖 pin | `openhands-workspace` 独立包未 pin（M6 遗留） | 全依赖精确 pin（仓库契约） |
| 生命周期 | agent-server 进程生命周期 | 每次 execute 创建/清理一次性容器 |

结论：M9 在 `adapters/execution/` 以 docker-py 低层 API（`client.api.*`）自建
DockerExecutionBackend；M6 映射代码保持 mapping-only（docstring 已修正，不再
声称"探测式 smoke"）。

## 2. 镜像供应链

- Dockerfile：`adapters/execution/sandbox/Dockerfile`（仓库内，可审计、可重建）。
- 基础镜像：`python:3.12-slim`，按 OCI index digest pin：
  `sha256:dd29372629eeba2dd003fd9e9d35a5b8236c44727875a0364254b5127af88e65`
  （Docker Hub registry API，2026-08-15 查询，`application/vnd.oci.image.index.v1+json`）。
- 镜像内基线：非 root 用户 `researcher`（uid 1000）、`/workspace` 工作目录、无 ENTRYPOINT。
- 运行时 digest：每次 `execute` 经 `inspect_image` 解析实际 image digest，
  写入 `ExecutionRun.compute_usage_summary["image_digest"]`，由
  ReproducibilityAudit 绑定（不可靠 digest 解析 → audit FAIL）。
- 镜像引用分界：`DockerExecutionBackend.DEFAULT_IMAGE`
  （`research-os-sandbox:m9-sandbox-v1`）仅为本地开发默认（可变 tag）；
  测试/CI 使用 `research-os-sandbox:m9-test` 构建 tag；生产 composition
  必须注入 `name@sha256:<digest>` pinned reference——该消费路径由
  `test_pinned_image_reference_is_consumed_and_recorded`（容器 E2E）
  验证，运行时 digest 解析 + 审计绑定为 tag 漂移检测。
- 升级门禁：镜像重建 + container E2E + reproducibility regression 全绿，
  且需显式批准（UPSTREAM_COMPONENTS.yaml upgrade_gate）。

## 3. 沙盒边界（运行时 host_config，默认 deny）

与 AGENTS.md §9 对齐，DockerExecutionBackend 每次执行强制施加：

| 边界 | 配置 |
| --- | --- |
| 网络 | `NetworkMode: none`（unrestricted network 默认 deny） |
| privileged | `Privileged: False` |
| capability | `CapDrop: ["ALL"]` |
| 提权 | `SecurityOpt: ["no-new-privileges"]` |
| rootfs | `ReadonlyRootfs: True` + `/tmp` tmpfs（`rw,noexec,nosuid,size=64m,mode=1777`） |
| 挂载 | 仅 bind-mount `spec.workspace_path`（或隔离临时目录）到 `spec.workdir` |
| 资源 | CPU/memory/pids 限额（`adapters/execution/profiles.py` 确定性映射） |
| 用户 | 镜像内 uid 1000 非 root |
| 禁止 | 不挂 Docker socket / host shell / home；不枚举 secret；env 由用例白名单构造 |

已知残余风险（记录不隐瞒）：容器 rootfs 只读与 pids/caps 限制是 Docker
进程级隔离，不是 VM 级；系统级强化 Sandbox（MicroVM 等）属后续 Milestone
（M16/M17），M9 不承诺。

## 4. 依赖登记

- docker-py `7.2.0`：Apache-2.0，sdist sha256
  `cebb93773d334f778e023a7ee352a8d6e13ab1bd3b863a4d4a59dec897df43ac`
  （PyPI JSON API，2026-08-15）；`uv.lock` 已固定；Windows 侧附带
  `pywin32>=304`（仅 win32）。
- 上游证据链：本文件 + `UPSTREAM_COMPONENTS.yaml` + `docs/references/LICENSE_MATRIX.md`。
- 使用面：仅 `adapters/execution/` import docker SDK（`adapter_only_import_boundary`）；
  Domain/Application 不接触 docker 类型。

## 5. 验证矩阵

| 项 | 落点 |
| --- | --- |
| Port contract（Fake 离线） | `tests/contracts/`（既有套件，不依赖 docker） |
| 真实容器 contract | `tests/contracts/test_execution_backend_docker.py`（`requires_docker`） |
| 创建/挂载/执行/timeout/失败/清理/资源边界/网络禁用 | `tests/adapters/execution/test_docker_backend_e2e.py` |
| 故障注入 | 同上（timeout kill、非零退出、OOM、镜像缺失、无残留容器） |
| 安全边界主动攻击 | `tests/adapters/execution/test_docker_backend_security_e2e.py`（host home / socket / rootfs / pip / 提权） |
| 实验全链容器 E2E | `tests/application/experiments/test_experiment_e2e.py`（确定性重跑 digest、NEGATIVE_RESULT、timeout、ReproducibilityAudit 全链） |
| CI | `.github/workflows/m0-quality.yml` `container-quality` job（ubuntu，build + requires_docker 集合） |
| 平台边界 | Windows Docker Desktop = 本地兼容性 smoke（开发机运行）；ubuntu-latest `container-quality` job = 权威 Linux 容器语义 gate（含上述全部容器套件）。不做跨平台行为一致化，Windows 侧失败只作为本地环境信号，不作为容器语义裁决 |