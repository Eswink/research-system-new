# Research Compose — 本地完整集成与验证栈

`infra/compose/research-validation.yaml` 把 Research OS 的本地集成面放入一个默认安全的 Compose
项目：PostgreSQL、OpenTelemetry Collector、Control Plane API、Worker Gateway、验证
Worker 与 Research Console 六个研究服务，以及一个无凭据的固定目标 loopback 代理。它用于开发、
集成测试和完整质量门禁，不替代 `infra/compose/personal-production.yaml` 的已验收个人生产流程。

## 1. 诚实边界

- PostgreSQL 是唯一 Canonical State；容器状态、Console 状态和 Collector 文件都不是业务真相。
- API、Gateway 与 Worker 复用现有 application Port 和 adapter，不创建第二套队列或 Artifact 真相。
- 默认 Worker 使用 `deterministic` 测试后端，且只声明 `compose_validation` capability；它只证明
  注册、心跳和 Gateway 控制链，不能代表真实 Docker/GPU 实验执行。
- 默认栈不挂载 `/var/run/docker.sock`，不使用 `privileged`，不把 Docker Socket 权限伪装成普通
  容器能力。真实 Docker/GPU Worker 仍按 [PERSONAL_DEPLOYMENT.md](PERSONAL_DEPLOYMENT.md)
  在明确授权的 Worker host 上运行。
- `research_internal` 是 `internal: true` 网络。六个研究服务只连接该网络，默认 API 不接收
  LLM key，也不能访问公共网络；因此该栈不声称完成 live relay。
- `host-proxy` 是唯一同时连接 `research_internal` 与 `research_edge` 的进程。它没有业务凭据，
  只转发 Compose 文件中固定的四个目标；边缘 bridge 关闭 IP masquerade，宿主机发布全部限制为
  `127.0.0.1`。需要外部 relay 时应使用单独、经过安全审查的 Compose override，而不是放宽默认文件。

## 2. 服务与数据流

```text
Browser / host tests → 127.0.0.1 fixed ports → credential-free host-proxy
                     → Console :5173 → /api proxy → Control Plane API :8000
                     → PostgreSQL :5432
                     → OTel Collector :4318

Control Plane API → PostgreSQL Canonical State + shared Artifact volume

Validation Worker → 127.0.0.1:8081 Worker Gateway（共享网络命名空间）
                  → PostgreSQL queue / lease / fencing
                  → Artifact volume（只经 Gateway 传输）

API / Worker → OTel Collector :4318 → gitignored `data/otel` evidence directory
```

Gateway 继续绑定容器网络命名空间内的 `127.0.0.1`。Worker 通过
`network_mode: service:worker-gateway` 进入同一命名空间，因此无需把明文 Gateway 发布到宿主机，
也无需把 `RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS` 虚假设为已启用。

## 3. 配置

复制模板并只在本机编辑 `.env`：

### POSIX

```bash
cp .env.example .env
```

### PowerShell

```powershell
Copy-Item .env.example .env
```

至少替换：

```text
RESEARCHOS_POSTGRES_PASSWORD
WORKER_ENROLLMENT_SECRET
RESEARCHOS_WORKER_ENROLLMENT_SECRET
```

PostgreSQL 密码会进入 DSN，需使用 URL-safe 字符。`.env` 已被 Git 和 Docker build context
排除。不要把 `docker compose config` 的展开结果写入日志或提交；只用 `config --quiet` 做解析检查。
Compose 按进程职责传递环境：Worker 不接收 PostgreSQL、LLM 或宿主机 Docker 凭据。

可选 loopback 端口：

```text
RESEARCHOS_POSTGRES_HOST_PORT=15432
RESEARCHOS_OTEL_HOST_PORT=4318
RESEARCHOS_API_HOST_PORT=8000
RESEARCHOS_CONSOLE_HOST_PORT=5173
RESEARCHOS_IMAGE_TAG=local
```

同一主机已有 personal-production/postgres-test/otel-evidence 栈时，为 research 项目选择不同端口，并用 `-p` 指定独立项目名。

## 4. 构建和启动

### POSIX

```bash
export RESEARCHOS_POSTGRES_PASSWORD='replace-with-url-safe-secret'
export WORKER_ENROLLMENT_SECRET='replace-with-worker-secret'
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml config --quiet
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml up -d --build --wait
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml ps
```

### PowerShell

```powershell
$env:RESEARCHOS_POSTGRES_PASSWORD = "replace-with-url-safe-secret"
$env:WORKER_ENROLLMENT_SECRET = "replace-with-worker-secret"
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml config --quiet
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml up -d --build --wait
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml ps
```

成功条件：PostgreSQL、Collector、API、Gateway、Console 为 `healthy`，Worker 与
`host-proxy` 为 `running`。首次启动会由现有 migration runner 幂等升级 PostgreSQL schema；
本 Compose 不定义新 migration。

## 5. Smoke 验证

### POSIX

```bash
curl --fail http://127.0.0.1:${RESEARCHOS_API_HOST_PORT:-8000}/openapi.json >/dev/null
curl --fail http://127.0.0.1:${RESEARCHOS_API_HOST_PORT:-8000}/cluster/workers
curl --fail http://127.0.0.1:${RESEARCHOS_CONSOLE_HOST_PORT:-5173}/ >/dev/null
```

`/cluster/workers` 的 `workers` 列表应至少包含一个经过脱敏的 worker projection；Gateway/Worker
日志会记录 `compose-validation-worker` 的注册。该事实只证明验证 Worker 已注册，不证明真实容器
实验能力。

### PowerShell

```powershell
$apiPort = if ($env:RESEARCHOS_API_HOST_PORT) { $env:RESEARCHOS_API_HOST_PORT } else { "8000" }
$consolePort = if ($env:RESEARCHOS_CONSOLE_HOST_PORT) { $env:RESEARCHOS_CONSOLE_HOST_PORT } else { "5173" }
Invoke-WebRequest "http://127.0.0.1:$apiPort/openapi.json"
Invoke-RestMethod "http://127.0.0.1:$apiPort/cluster/workers"
Invoke-WebRequest "http://127.0.0.1:$consolePort/"
```

## 6. 完整验证

先保持 Compose 栈运行，再把宿主机测试指向它。所有重负载门禁必须串行执行。

### POSIX

```bash
export RESEARCHOS_POSTGRES_DSN="postgresql://research_os:${RESEARCHOS_POSTGRES_PASSWORD}@127.0.0.1:${RESEARCHOS_POSTGRES_HOST_PORT:-15432}/research_os"
export RESEARCHOS_OTEL_COLLECTOR_ENDPOINT="http://127.0.0.1:${RESEARCHOS_OTEL_HOST_PORT:-4318}"
export RESEARCHOS_REQUIRE_POSTGRES=1
export RESEARCHOS_REQUIRE_COLLECTOR=1
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

### PowerShell

```powershell
$postgresPort = if ($env:RESEARCHOS_POSTGRES_HOST_PORT) { $env:RESEARCHOS_POSTGRES_HOST_PORT } else { "15432" }
$otelPort = if ($env:RESEARCHOS_OTEL_HOST_PORT) { $env:RESEARCHOS_OTEL_HOST_PORT } else { "4318" }
$env:RESEARCHOS_POSTGRES_DSN = "postgresql://research_os:$($env:RESEARCHOS_POSTGRES_PASSWORD)@127.0.0.1:$postgresPort/research_os"
$env:RESEARCHOS_OTEL_COLLECTOR_ENDPOINT = "http://127.0.0.1:$otelPort"
$env:RESEARCHOS_REQUIRE_POSTGRES = "1"
$env:RESEARCHOS_REQUIRE_COLLECTOR = "1"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

完整 M0 profile 会执行 Python lint/format/mypy/pytest、TypeScript/Console lint/test/typecheck/build、
system specification、Cursor governance、Hook/learning eval 和文档一致性检查。真实付费 LLM 不是
默认验证依赖。

## 7. 故障隔离与恢复

Collector 是派生观测面，可单独停止并验证 API 仍可读取 Canonical State：

```text
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml stop otel-collector
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml start otel-collector
```

重启 Gateway 后 Worker 会按现有重连策略重新注册。重启 PostgreSQL 后，API/Gateway 的
`ReconnectableConnection` 会在下一次操作时重建连接；无法安全重放的事务仍 fail closed。

普通停止和移除容器会保留命名卷：

```text
docker compose --project-directory . -p research-os-validation -f infra/compose/research-validation.yaml down
```

`down -v` 会删除 PostgreSQL、Artifact 与控制面命名卷，但不会删除 bind-mounted
`data/otel`；清理任何一类数据都只能用于明确批准的测试重建。不要对 personal/production
项目使用 validation 项目的清理命令，也不要复用其项目名。

## 8. 供应链与升级

Python、uv、Node、PostgreSQL 与 Collector 的外部镜像均以 OCI index digest 固定；Python 包和
Node 包继续分别以 `uv.lock` 与 `pnpm-lock.yaml` 为解析真相。镜像来源、许可证和升级门禁记录在
`UPSTREAM_COMPONENTS.yaml` 与 `docs/references/LICENSE_MATRIX.md`。升级 tag 不能替代 digest
更新；升级后至少重跑 image build、Compose smoke、容器安全契约和完整 M0 profile。
