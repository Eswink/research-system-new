# Personal Deployment Guide (PA-1 verified, 2026-09-03)

单用户个人生产部署 baseline。所有命令均在本次 PA-1 会话中真实执行过
（证据见 `scratch/pa1-20260903/`，本节标注 [P1]/[P2]/[P3]… 对应证据文件）。

前置：Windows + Docker Desktop（WSL2）、uv、pnpm、NVIDIA GPU + nvidia
runtime（GPU worker 需要）。组件：PostgreSQL 16 + OTel Collector 跑在
Docker 中；API / worker gateway / worker 以 uv 进程跑在本机（console 可选）。

## 1. 安装 / 部署

```bash
git clone <repo> research-os && cd research-os
uv sync --frozen --dev            # [P1] 5s (uv cache)
pnpm install --frozen-lockfile    # [P1] 21s (pnpm store)
cp .env.example .env              # 编辑密码/密钥（见 §7）
docker compose -f docker-compose.personal.yml up -d --build   # [P1] postgres+collector
```

校验：`docker compose -f docker-compose.personal.yml ps` 两个服务 healthy。
首次启动会自动建 schema（API/gateway 组装时 pg_migrate，幂等；
迁移版本 001–009 → migration_version=9 [P1]）。

## 2. 启动

```bash
set -a; source .env; set +a

# Control Plane API（PG canonical；RESEARCHOS_DATABASE_URL 必须设置）
uv run uvicorn --factory services.api.app:create_app --host 127.0.0.1 --port 8000

# Worker gateway（RESEARCHOS_POSTGRES_DSN + WORKER_ENROLLMENT_SECRET）
uv run python -m services.api.worker_gateway

# Remote/GPU worker（零 DB 凭据；只持 gateway URL + enrollment secret）
uv run python -m services.worker --worker-id personal-w1

# Research Console（可选，端口 5173，/api 代理到 8000）
pnpm --dir apps/web dev
```

**首次使用前必须 provisioning（PA-1 F5）**：未配置 LLM endpoint/model 的控制面
启动 run 会诚实收敛 FAILED（`run.failed` 事件携带具体 preflight codes，如
`ENDPOINT_*`/`MODEL_*` 缺失项）。先经 Console wizard 或
`POST /llm-endpoints` + `POST /models` 注册 relay 端点与模型，再启动 run。

## 3. 停止

```bash
# 进程：Ctrl-C（API lifespan 逆序停 scheduler；worker SIGTERM 优雅 drain）
# 基础服务：
docker compose -f docker-compose.personal.yml down        # 保留数据卷
docker compose -f docker-compose.personal.yml down -v     # 删除数据卷（毁库）
```

## 4. 健康检查（[P8] 实测端点）

```text
GET /openapi.json                    API 存活
GET /cluster/workers                 worker fleet（worker_ref/state/last_heartbeat）
GET /evaluations/trend?dataset_id=m17_gpu_v1   评测趋势（回归标记）
GET /runs/{run_id}/cost、/usage、/telemetry、/events、/tasks
GET /llm-endpoints/{id}/health
```

数据库侧（worker GPU 观察在表中，[P8]）：

```bash
docker exec research-system-postgres-1 psql -U research_os -d research_os \
  -c "SELECT worker_id,state,gpu_observed_at IS NOT NULL FROM workers"
```

注意：OPERATIONS_RUNBOOK 旧版列出的 `/control-plane/health`、
`/database/health` 等路径并不存在（PA-1 校正）；以本表为准。

## 5. Backup

工具（推荐，PA-1 实测）：

```bash
uv run python tools/backup.py [--container research-system-postgres-1] \
  [--blob-root ./data/artifacts-blobs] [--out data/backups] [--keep 7] [--verify]
```

（pg_dump + blob tar + manifest.json + `--keep` 保留策略；`--verify` 以只读
方式抽查 live blob 与 PG canonical 行的 digest 一致性。）

手工等价命令：
# PostgreSQL（custom 格式；同 major 版本兼容）
docker exec research-system-postgres-1 pg_dump -U research_os -d research_os \
  -Fc > data/backups/research-os-$(date +%Y%m%d-%H%M%S).dump

# ArtifactStore（PG 元数据已含于 dump；blob 单独备份）
tar -czf data/backups/artifacts-$(date +%Y%m%d-%H%M%S).tar.gz \
  -C <blob-root> .          # blob-root = RESEARCHOS_WORKER_ARTIFACT_BLOB_DIR 或 .artifacts
```

secret 不进备份（§7 验证：dump/tar 均不含 DB 密码）。

## 6. Restore（[P3]/[P4] 实测）

```bash
# 1) 全新 postgres 16 实例（复用 personal compose，改 REVIEWED_OTEL/POSTGRES_HOST_PORT）
# 2) 恢复
docker exec -i <new-postgres> pg_restore -U research_os -d research_os \
  --clean --if-exists < data/backups/research-os-<ts>.dump     # 无错误输出
# 3) 校验
docker exec <new-postgres> psql -U research_os -d research_os \
  -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"   # 22
# 4) 恢复 blob（解包到新目录）→ 逐项校验 digest（m12_evidence.content_digest ==
#    artifacts.digest == blob sha256；引用闭环 — [P4] 5/5 pairs ok）
```

不需要手动迁移：schema 随 dump 而来（migration_version=9）。

## 7. Credential setup / restore（[P5] 实测）

| 凭据 | 存哪 | 恢复/轮换 |
| --- | --- | --- |
| PostgreSQL 密码 | gitignored `.env`（RESEARCHOS_POSTGRES_PASSWORD + 两个 DSN） | 明文只在 initdb 生效；已有卷必须 `ALTER USER research_os PASSWORD '<new>'`（owner 可改自己），再更新 .env（[P5] 实跑 ALTER→新密码可连→改回） |
| Worker enrollment secret | `.env`（WORKER_ENROLLMENT_SECRET=gateway / RESEARCHOS_WORKER_ENROLLMENT_SECRET=worker，两值必须一致） | 改值 → 重启 gateway + worker；旧 secret worker 注册被拒（[P5b] S4 实跑） |
| LLM relay key | 环境变量或以 console wizard 注册进内存 RegistryCredentialResolver（重启即清） | 重新 wizard 注册或设 DEV_LLM_API_KEY；本会话无真实 LLM key（honest boundary） |
| OTLP | 无凭证；collector 仅 loopback（无 auth/TLS，M15 控制项） | 无需配置；改 RESEARCHOS_OTEL_ENDPOINT |

`.env`、`secrets/`、`data/`、`.artifacts/` 均已 gitignore（[P5] git ls-files 验证）。

## 8. Remote Worker setup

```bash
set -a; source .env; set +a
uv run python -m services.api.worker_gateway      # 先启 gateway
uv run python -m services.worker --worker-id my-rw1   # 协议 "1" 不匹配即拒
```

worker 自身不持 DB 凭据（子进程环境剥离 RESEARCHOS_POSTGRES_DSN/
DATABASE_URL，[P5b] harness 保证）。失联/恢复：LOST 由服务端判定（15s），
租约经 LeaseRecoveryScheduler 回 QUEUED；迟到结果被 fence 拒
（[P5b] S1/S3/S5 实跑）。

## 9. GPU Worker setup

```bash
export RESEARCHOS_WORKER_EXECUTION_BACKEND=docker
export RESEARCHOS_WORKER_DOCKER_IMAGE=research-os-gpu-sandbox:m17-v1
export RESEARCHOS_WORKER_GPU_IMAGE=research-os-gpu-sandbox:m17-v1   # 同 digest pin
uv run python -m services.worker --worker-id personal-gpu1
```

启动时以 DeviceRequests 真实探测（不支持则注册 CPU-only，fail-closed，
不会“连上就宣称 GPU”）；每 ~1 分钟空闲重探。GPU 观察在
`workers.gpu_observation_json` / `gpu_observed_at`；cluster DTO 现含
`gpu_probe_digest` / `gpu_observed_at`（无 raw device name，PA-1 修复轮
交付）。GPU 镜像 digest：
sha256:b0a03d7c5047b476ae950d878a42df85ffe7dfd3a3c9d280bfdcd4874a085bfe，
默认 `research-os-gpu-sandbox:m17-v1`。

## 10. Common failure recovery

- **进程偶发退出**：重启进程即可（所有状态在 PG；[P7]）。
- **PostgreSQL 重启**：PG adapter 连接现已自动重连（PA-1 F2 修复：
  `ReconnectableConnection` 在空闲连接损坏时换用新连接；事务中失败不重试）。
  重启 PG 后控制面进程无需重启即可继续服务；过期租约由 LeaseRecoveryScheduler
  自动收敛（[P7] B 实跑 + tests/postgres/test_reconnect.py）。
- **worker LOST / 迟到结果**：服务端自动处理（reaper + fence）；不要手工
  改 PG（[P5b]）。
- **孤留 GPU 容器**：worker 启动探测会清扫已停止的 GPU 镜像容器
  （[P6] 实测 leftover=[]）；运行中的容器不会被触碰。
- **日志里出现 DSN**：密码重定向（`***REDACTED***`，[P1] probe 输出为证）。
- **临时目录 / 容器积累**：探针/作业 scratch 已 finally 清理（W1/W2
  修复，[P6] 实测）；长期运行可定期
  `docker ps -a --filter ancestor=research-os-gpu-sandbox:m17-v1 -q | xargs docker rm -f`（仅限已退出容器按需执行）。

## 11. Upgrade

无自动升级机制（诚实记录）。个人流程：
`git pull → uv sync --frozen --dev → pnpm install --frozen-lockfile →
uv run python -m tools.probes.probe_migration（或启动时 ensure_schema）
→ 重启进程 → 校验 identity（VERSION/迁移版本 9/镜像 digest/worker
probe digest dfe7932f…）。[P9] rehearsal：迁移重放幂等（仍 1..9）、全栈
重启后身份一致。

## 12. Research run troubleshooting

- 运行卡 QUEUED：查 `leases`（应为 0）+ workers 是否 READY；
  `GET /cluster/workers`。
- GPU 任务失败：`tasks.status` + `execution_jobs.failure_category`
  （GPU_OOM/GPU_UNAVAILABLE 是 failure 类别，不是科学结果）。
- 科学负结果≠系统故障：负结果 memory 属预期路径（[P2]）。
- 遥测 cost 显示 UNKNOWN：无价格源（真实成本模型未配置，诚实）。

## 13. Telemetry troubleshooting

- collector 停止时 API 异步导出报错（后台线程 "Exception while
  exporting Span"）——不影响请求结果（[P8] 实测 200 + 数据落库）。
- **已知诚实边界**：OTEL 开启 + collector 保持运行是推荐态；
  M15 的 fail-isolation 套件覆盖 down/500/timeout（P11 复跑）。
- 检查：`docker compose -f docker-compose.personal.yml ps` 看 collector
  healthy；`data/otel/research_os_signals.json` 增长；隐私：闭集词表
  无 prompt/key（[P5] 扫描为证）。

## 14. 明确不支持（explicitly unsupported）

Multi-user / Organization / RBAC / tenant isolation / Enterprise SLO /
compliance / incident management platform / central enterprise secret
manager / multi-GPU / HPC / autoscaling；物理异地 GPU host（未验证）；
自动升级/CD；跨 major 版本的 PG 备份恢复（需先恢复到旧 major）。
