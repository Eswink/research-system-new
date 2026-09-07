# Personal Deployment Guide — v0.4.0

本指南定义单用户 Personal Production 部署的可执行路径。PostgreSQL 是业务
Canonical State（唯一权威状态）；Artifact blob 使用内容寻址目录；API、Worker
Gateway 与 Remote Worker 是可重启进程；OpenTelemetry Collector 仅承载非权威观测。

PA-1R 在 Windows 11 + PowerShell、Docker Desktop 29.2.1、PostgreSQL 16.14、
单张 NVIDIA GPU 上重放了本指南的关键步骤。物理异地 GPU、多用户、Enterprise、
multi-GPU/HPC 不在本基线内。

本指南继续以宿主机 API/Gateway/真实 Docker-GPU Worker 为个人生产路径。若只需要默认
无外网、无 Docker Socket 的六个研究服务加无凭据 loopback 代理集成栈与完整门禁环境，使用
[RESEARCH_COMPOSE.md](RESEARCH_COMPOSE.md)；其中 deterministic Worker 不是生产执行平面。

## 1. 前置与冻结安装

必需组件：Git、uv、pnpm、Docker Desktop + Buildx。GPU 部署还需要 NVIDIA
驱动、NVIDIA Container Toolkit，以及可被 Docker 使用的 `nvidia` runtime。

```text
VERSION                 唯一项目版本源
infra/compose/personal-production.yaml  PostgreSQL + OTel Collector
.env                    gitignored 的操作员配置
```

POSIX：

```bash
git clone <repo> research-os
cd research-os
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
cp .env.example .env
```

PowerShell：

```powershell
git clone <repo> research-os
Set-Location research-os
uv lock --check
uv sync --frozen --dev
pnpm install --frozen-lockfile
Copy-Item .env.example .env
```

编辑 `.env`，替换所有占位值。`.env` 是操作员配置清单，不是允许所有进程继承的
统一权限集。API、Gateway、Worker 必须按下文使用各自所需的环境变量。

## 2. 构建 GPU 应用镜像

正式部署不能假设 `research-os-gpu-sandbox:m17-v1` 已存在。以下命令固定
`linux/amd64`、关闭 provenance 附件、显式传入 `SOURCE_DATE_EPOCH`，并由
`Dockerfile.gpu` 归一化 `useradd` 生成文件的时间戳：

```text
docker buildx build --load --no-cache --provenance=false --platform linux/amd64 --build-arg SOURCE_DATE_EPOCH=0 -f adapters/execution/sandbox/Dockerfile.gpu -t research-os-gpu-sandbox:m17-v1 .
```

这条命令在 PA-1R 中从同一 clean source 连续构建两次，均得到应用镜像：

```text
sha256:3d306d299abcb7c5384151ee15b6b7f5819e70203e5da50b47341710720c9d5c
```

核对：

```text
docker image inspect research-os-gpu-sandbox:m17-v1 --format "{{.Id}} {{.Os}}/{{.Architecture}}"
```

当前 recipe 在已资格化环境中应为上述 digest 和 `linux/amd64`。`m17-v1` 只作为
本地构建标签；Worker 的 `RESEARCHOS_WORKER_DOCKER_IMAGE` 与
`RESEARCHOS_WORKER_GPU_IMAGE` 必须使用 `.env.example` 中的
`research-os-gpu-sandbox@sha256:3d306d299abcb7c5384151ee15b6b7f5819e70203e5da50b47341710720c9d5c`
digest-qualified 引用。若 inspect 不同，
先核对 Git source、Docker/Buildx 版本、平台、基座 digest 与完整构建参数；不得把
漂移镜像冒充相同部署身份。运行时还会把实际应用镜像 digest 写入 Run Manifest。

## 3. 加载操作员环境

Compose（配合 `--project-directory .`）会自动读取仓库根 `.env`。本机 Python 进程不会自动读取它。

POSIX（仅在 API 或 Gateway 专用 shell 中）：

```bash
set -a
. ./.env
set +a
```

PowerShell（仅在 API 或 Gateway 专用终端中）：

```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
}
```

`RESEARCHOS_POSTGRES_DSN` 是全链首选 DSN（PA-1 链统一：API 控制面、Gateway 与
生产工作流按同一键序解析），它优先于 `RESEARCHOS_DATABASE_URL`，后者又优先于
宿主机可能存在的通用 `DATABASE_URL` / `POSTGRES_DSN`。
四键必须指向同一 PostgreSQL 实例。

API、Gateway 与 Reference Workflow 同时读取 `RESEARCHOS_ARTIFACT_BLOB_DIR`，
必须指向同一内容寻址 blob root。Gateway 显式 `blob_dir` 优先，其次为该变量；
仅在它未设置时兼容旧 `RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR`。Worker 本身通过
Gateway 传输 bundle，不需要共享 blob 目录或数据库凭据。

正式示例 catalog 的 endpoint `credential_ref` 是 `LLM_MAIN_KEY`。
`DEV_LLM_API_KEY` is not an alias for `LLM_MAIN_KEY`。使用正式 Protocol 时必须设置
`LLM_MAIN_KEY`；只有传入 `--live-relay` 才会发出真实模型请求。

## 4. 启动 PostgreSQL 与 Collector

```text
docker compose --project-directory . -f infra/compose/personal-production.yaml up -d --build
docker compose --project-directory . -f infra/compose/personal-production.yaml ps
```

两个服务都应为 healthy。PostgreSQL 使用命名卷，普通 `down` 保留数据；
`down -v` 会删除数据库，仅可用于明确批准的重建。
PostgreSQL 与 Collector 的宿主机端口均只绑定 `127.0.0.1`；个人生产默认不得把
Canonical State 或无认证 OTLP receiver 暴露到 LAN/public interface。

API/Gateway 首次组装会幂等执行 migration。当前正式 schema 身份为 migration
`001` 到 `010`，public table 数为 22。`010` 将 `peak_gpu_memory_bytes` 从 INTEGER
扩宽为 BIGINT，避免单卡超过 2 GiB 的观测值导致结果无法入库。Worker protocol 保持
`1`，JSON integer 不变；升级时先排空写入，并为 ALTER TABLE 留出维护窗口。

## 5. 启动 Control Plane、Gateway 与 Worker

在已加载操作员环境的独立终端中启动 API：

```text
uv run --frozen --no-sync uvicorn --factory services.api.app:create_app --host 127.0.0.1 --port 8000
```

在另一个已加载操作员环境的独立终端中启动 Worker Gateway：

```text
uv run --frozen --no-sync python -B -m services.api.worker_gateway
```

Worker 只能继承 Gateway URL、enrollment secret、执行配置、遥测配置和可选 blob
路径。启动前从 Worker 专用终端移除数据库及 LLM 凭据。

POSIX：

```bash
set -a
. ./.env
set +a
unset RESEARCHOS_POSTGRES_PASSWORD RESEARCHOS_DATABASE_URL RESEARCHOS_POSTGRES_DSN
unset DATABASE_URL POSTGRES_DSN LLM_MAIN_KEY DEV_LLM_API_KEY
uv run --frozen --no-sync python -B -m services.worker --worker-id personal-gpu1
```

PowerShell：

```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $name, $value = $_ -split '=', 2
    [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
}
Remove-Item Env:RESEARCHOS_POSTGRES_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:RESEARCHOS_DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:RESEARCHOS_POSTGRES_DSN -ErrorAction SilentlyContinue
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:POSTGRES_DSN -ErrorAction SilentlyContinue
Remove-Item Env:LLM_MAIN_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DEV_LLM_API_KEY -ErrorAction SilentlyContinue
uv run --frozen --no-sync python -B -m services.worker --worker-id personal-gpu1
```

生产 Worker 必须设置 `RESEARCHOS_WORKER_EXECUTION_BACKEND=docker`。
Worker protocol 默认 `1`；Worker runtime version 默认直接读取根 `VERSION`，当前为
`0.4.0`。Gateway 暂时不可达时 Worker 会退避重连；恢复后重新注册，不需要手工改 DB。

可选 Console：

```text
pnpm --dir apps/web dev
```

## 6. 健康与只读运营查询

```text
GET /openapi.json
GET /cluster/workers
GET /runs/{run_id}
GET /runs/{run_id}/usage
GET /runs/{run_id}/cost
GET /runs/{run_id}/telemetry
GET /runs/{run_id}/events
GET /runs/{run_id}/tasks
GET /runs/{run_id}/placement
GET /evaluations/trend?dataset_id=m17_gpu_v1
```

未配置价格源时，GPU/CPU/Evaluation 用量仍必须可见；成本应返回 HTTP 200 和
`MONETARY_UNAVAILABLE`，不能返回伪造的 0，也不能因未知维度返回 422。

## 7. Durable Reference Research Run

用于个人生产验收的入口是：

```text
uv run --frozen --no-sync python -B tools/personal_reference_workflow.py --run-id <UUID> --timeout 600
```

它只组合 PostgreSQL stores、内容寻址 ArtifactStore、RemoteExecutionBackend 与真实
Worker，不组合 Fake 或 SQLite。它执行正式 M17 GPU Protocol/experiment/eval dataset，
并持久化 Run、Manifest、ExperimentRun、Artifact、Evidence、Claim、EvalReport、
Usage、Memory 与 Deliverable。完成后会核对实际 Worker 镜像 digest。

`tools/m12_reference_workflow.py` 是离线/一次性演示入口，不是个人生产持久化验收入口。
使用它成功退出，不能证明 PostgreSQL 中存在完整 Research Truth。

Reference Workflow 在派发前保存 `RUNNING`、冻结的 Manifest、输入配置 digest 和
预期 GPU image digest；实际 Worker image 不一致时不得生成成功 Deliverable。
进程被硬停后，使用同一正式命令和相同 `--run-id` 重放 `RUNNING` Run：任务幂等身份
不包含宿主机工作目录，恢复目录无需复制原 workspace。已完成 Experiment/Artifact
会重新核验后复用。已终态 Run 不允许该命令静默覆写；配置、脚本或镜像改变时必须
创建新 Run。旧版未保存冻结输入/运行中 Manifest 的 Run 不支持自动重放。

新 Experiment 标识使用完整 Run UUID 的双射命名空间，保留冻结 M12 样例标识；
不再只使用 Run UUID 前缀。历史已完成 Evidence/Artifact 记录不进行重命名或迁移。

## 8. Backup

本工具生成配对逻辑备份，不提供跨 PostgreSQL 与 blob 文件系统的在线原子快照。
正式备份前先暂停新任务并等待当前写入完成，再停止本部署 API/Gateway/Worker 和
Reference CLI 写入进程；只保留 PostgreSQL/Collector。完成备份后方可恢复写入。
不要通过停止别的项目进程或删除生产卷来制造备份一致性。

先确定 Compose PostgreSQL 容器 ID。

POSIX：

```bash
PG_CONTAINER=$(docker compose --project-directory . -f infra/compose/personal-production.yaml ps -q postgres)
uv run --frozen --no-sync python -B tools/backup.py \
  --container "$PG_CONTAINER" \
  --blob-root ./data/artifacts-blobs \
  --out ./data/backups --keep 7 --verify --sample 100
```

PowerShell：

```powershell
$pgContainer = docker compose --project-directory . -f infra/compose/personal-production.yaml ps -q postgres
uv run --frozen --no-sync python -B tools/backup.py `
  --container $pgContainer `
  --blob-root ./data/artifacts-blobs `
  --out ./data/backups --keep 7 --verify --sample 100
```

工具以二进制方式生成 PostgreSQL custom-format dump，并生成 Artifact tar 与 manifest。
`--verify` 校验 live canonical Artifact 行到 blob digest；它不是 restore 测试，仍需下一节。

## 9. Clean Restore

恢复目标必须是新的 PostgreSQL 16 实例与空 Artifact 目录。示例先创建隔离目标：

POSIX：

```bash
docker volume create research_os_restore_pgdata
docker run -d --name research-os-restore-postgres \
  -e POSTGRES_DB=research_os -e POSTGRES_USER=research_os \
  -e POSTGRES_PASSWORD="$RESEARCHOS_POSTGRES_PASSWORD" \
  -p 127.0.0.1:15433:5432 \
  -v research_os_restore_pgdata:/var/lib/postgresql/data postgres:16-alpine
```

PowerShell：

```powershell
docker volume create research_os_restore_pgdata
docker run -d --name research-os-restore-postgres `
  -e POSTGRES_DB=research_os -e POSTGRES_USER=research_os `
  -e POSTGRES_PASSWORD=$env:RESEARCHOS_POSTGRES_PASSWORD `
  -p 127.0.0.1:15433:5432 `
  -v research_os_restore_pgdata:/var/lib/postgresql/data postgres:16-alpine
```

等待 `pg_isready` 成功后，以 manifest 中同一时间戳的 dump/archive 执行：

```text
uv run --frozen --no-sync python -B tools/restore.py --container research-os-restore-postgres --dump data/backups/research-os-<timestamp>.dump --artifact-archive data/backups/artifacts-<timestamp>.tar.gz --blob-target data/restored-artifacts
```

`tools/restore.py` 不使用 shell 重定向，因此 Windows PowerShell 不会损坏二进制 dump；
它拒绝路径穿越、symlink/hardlink、非内容寻址路径，并逐 blob 校验 SHA-256。目标
Artifact 目录非空时会 fail closed。

恢复后至少核对：

```text
SELECT version FROM migration_version ORDER BY version;     -- 1..10
SELECT count(*) FROM information_schema.tables WHERE table_schema='public'; -- 22
SELECT run_id, run_json->>'state' AS state,
       run_json->>'manifest_digest' AS manifest_digest
FROM runs WHERE run_id='<run-id>';
```

随后让一个只读 API 实例指向 restore DSN 和 restore blob root，核对：

```text
Run → Manifest Artifact → Experiment Artifacts → Evidence → Source → Claim
    → EvalReport → Deliverable
```

每个 Artifact/Evidence content digest 必须与恢复 blob 的实际 SHA-256 一致；缺失、损坏、
跨 Run 引用或无法解析的 Deliverable 均使恢复失败。

## 10. 故障恢复

- **Control Plane/Scheduler**：硬停并重启相同配置；Run、Usage、Evaluation、Artifact
  引用来自 PostgreSQL/ArtifactStore，应保持可读。过期 lease 由 scheduler 恢复。
- **Gateway**：短时停机不会要求重启 Worker；Worker 捕获 transport outage、退避并用
  新 client/session 自动注册。
- **Worker**：mid-job 硬停后，旧 lease 过期回队列，新 generation 领取并以更高 fence
  完成；迟到结果被拒。禁止手工改 PostgreSQL。
- **Worker 自有执行容器**：仅在 Gateway 成功授予新 generation 后，清理同一 Gateway
  命名空间、同一 Worker、较旧 generation、同一精确 image ID 且名称匹配的执行容器。
  活跃旧会话容器已失去执行权，因此也会停止；其它 Worker/Gateway、当前/未来 generation、
  不同镜像或无归属标签的容器不在清理范围。引擎清理失败时不允许继续 claim。
  旧版无标签容器或跨镜像升级必须先由操作员明确排空，不宣称自动接管。
- **GPU cancel/timeout**：两条路径都必须停止执行容器并释放 lease。Worker 启动探针只
  清理 Research OS 自有、已停止、且镜像 ID 精确匹配的容器；不会删除运行中或外部容器。
- **PostgreSQL**：连接包装器会在空闲连接失效后重连；事务中失败不做不安全重放。
- **Collector**：可停止 Collector 验证业务隔离。导出器可记录连接错误，但 Run、Usage、
  Cost、Evaluation 与 Artifact 写入必须继续成功；Collector 恢复后指标继续进入
  `data/otel/research_os_signals.json`。

## 11. Secret hygiene

`.env`、`data/`、`.artifacts/` 与 secrets 目录必须保持 gitignored。Canary 检查应覆盖：
Git 当前树与历史、PostgreSQL dump、Artifact archive、恢复 blob、API/Worker/Container
日志、OTel 文件、exports 与 workspace。只报告指纹和命中数量，不打印原始 secret。

PostgreSQL dump 会备份 Domain 数据，因此业务字段本身不得承载凭据。Artifact、Evidence、
Telemetry 与日志也不得写入 endpoint key、enrollment secret 或 DSN。

## 12. Version / release truth

每次接受或升级都应记录并交叉核对：

- 根 `VERSION` 与 API/Worker service version；
- Git commit，以及按明确授权保留的未提交 patch 状态；
- PostgreSQL 16 runtime、22 张 public 表、migration `001..010`；
- Worker protocol `1` 和 runtime version `VERSION`；
- OpenHands SDK `1.42.0` 与 `UPSTREAM_COMPONENTS.yaml`/`uv.lock`；
- Docker/Buildx、GPU driver/CUDA/torch/cuDNN 的实际值；
- GPU base OCI digest `sha256:7b324d212a4450795b49edba9949b7cdc72429148a64e974334bfe5774d51385`；
- GPU application image digest（当前 recipe：`sha256:3d306d299abcb7c5384151ee15b6b7f5819e70203e5da50b47341710720c9d5c`）；
- OTel Collector `0.139.0` base digest与 PostgreSQL image major。

项目升级必须经显式发布流程；本指南不会创建 commit、tag 或 release。

## 13. 停止与边界

主机进程使用 Ctrl-C 优雅停止。基础服务：

```text
docker compose --project-directory . -f infra/compose/personal-production.yaml down
```

该命令保留 PostgreSQL 卷。删除卷、restore 容器或备份必须另行确认。

当前明确不支持：multi-user/Organization/RBAC、Enterprise SLO/合规、central secret
manager、multi-GPU/HPC/autoscaling、物理异地 GPU host、自动升级/CD，以及跨 PostgreSQL
major 版本直接恢复。


## PA-1R 闭环：恢复与发布身份

当前个人部署先应用 migration 010（GPU 峰值显存 INTEGER → BIGINT）与 011
（GPU 秒数 INTEGER → NUMERIC）。旧 001–009 备份仍先恢复到新的 PostgreSQL 16；
随后启动本版 API/Gateway 的正式 migration runner 升级至 012，再执行 schema 核对。
迁移在停写维护窗口执行；旧整数值保持原值，不伪造历史小数精度。回退旧源码不等于
回退数据库 schema，需保留升级前完整 DB/Artifact 备份。

Worker protocol 保持 `1`，新增可选 `gpu_elapsed_seconds_exact` 十进制字符串；新 Gateway
优先采用该值，缺省仍接受旧整数报文。旧 Gateway 忽略该可选字段，无法保证小数精度；
先升级 Gateway/DB，再升级 Worker。Release Record 必须记录正在运行的同版组件。

Durable Reference Run 在 dispatch **之前**写入 RUNNING ResearchRun、冻结 Manifest 和
reference_inputs Artifact。编排进程硬退出后，可用原 `--run-id` 在同一库或实际恢复库
重放：校验冻结配置、复用已入队 Task／已完成 Experiment、幂等归账；拒绝配置或镜像
漂移。已完成或业务失败的终态 Run 不允许原地重新执行，应查询原 Artifact 或创建新 Run。

GPU Worker 重启后只清理可证明归属于同 Gateway 边界、同 Worker identity、更旧注册
 generation 且镜像身份一致的 Research OS 执行容器，包含仍运行的旧容器；没有归属标签
的历史容器不能自动推断归属。首次升级应先停止旧版 Worker 并由操作员确认旧容器清空。
这不是任意容器清扫权限，也不是对未重启 Worker 的即时 GPU 回收承诺。

正式发布身份不得只记录版本号或 dirty worktree：本地不可变 commit、可检出的 Git
bundle、冻结依赖、DB migration 文件摘要、Worker 协议、实际 OCI/runtime/upstream 值须
由 Personal Production Release Record 对照。Cursor Framework 的旧 RELEASE_EVIDENCE
不能替代本产品的发布记录。PA-1R 验收入口：

```text
uv run --frozen --no-sync python -B tools/PA1R运行演练v1.py prepare --candidate-version release-v1 --revision <完整commit>
uv run --frozen --no-sync python -B tools/PA1R运行演练v1.py drill --candidate-version release-v1
```

故障与密钥审计入口分别为 `tools/PA1R故障演练v1.py` 与 `tools/PA1R密钥审计v1.py`。
前者通过 `PA1R_CANDIDATE_VERSION` 选择上述同一候选，后者通过 `--candidate-version`。
这些操作只使用独立审计实例、卷、随机 canary；不连接生产凭据、不推送远端、不启动 M18/M19。

Migration 012 保存 Worker 原始 execution wall duration，重放已完成作业时复用该值，而不是重新计算轮询延迟。CPU_TIME 在此 Reference slice 表示执行 wall-duration 的历史命名，不表示 NVML/进程 CPU cycles 测量。
