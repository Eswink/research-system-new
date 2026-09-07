# infra/compose — 活跃 Compose 栈

四个相互分离的栈，各自职责独立，不合并个人生产、完整验证与 CI 证据职责。
服务、端口、网络、只读文件系统、capability drop、凭据隔离与固定镜像语义与
根目录时期完全一致。

| 文件 | 职责 |
| --- | --- |
| `postgres-test.yaml` | CI/开发用一次性 PostgreSQL（tmpfs 数据目录，端口 15432，用完即弃） |
| `otel-evidence.yaml` | M15 遥测证据管线：pinned OTel Collector，loopback-only 发布，可与 postgres-test 叠加 |
| `personal-production.yaml` | PA-1 个人生产基线：持久化 PostgreSQL 命名卷 + Collector；API/gateway/worker/console 按 `docs/operations/PERSONAL_DEPLOYMENT.md` 本机启动 |
| `research-validation.yaml` | 本地完整集成与验证栈：六个研究服务 + 无凭据 loopback 代理；见 `docs/operations/RESEARCH_COMPOSE.md` |

## 迁移映射（2026-09-07 根目录分类归档）

| 旧路径（仓库根） | 当前路径 |
| --- | --- |
| `docker-compose.m14.yml` | `infra/compose/postgres-test.yaml` |
| `docker-compose.m15.yml` | `infra/compose/otel-evidence.yaml` |
| `docker-compose.personal.yml` | `infra/compose/personal-production.yaml` |
| `docker-compose.research.yml` | `infra/compose/research-validation.yaml` |

## 调用约定

一律从仓库根运行，并用 `--project-directory .` 固定项目目录，使 build context、
bind mount（如 `./data/otel`）与根 `.env` 凭据加载继续以仓库根解析：

```text
docker compose --project-directory . -f infra/compose/postgres-test.yaml up -d
docker compose --project-directory . -f infra/compose/postgres-test.yaml -f infra/compose/otel-evidence.yaml up -d --build
docker compose --project-directory . -f infra/compose/personal-production.yaml up -d --build
docker compose --project-directory . -f infra/compose/research-validation.yaml up -d --build --wait
```

## 安全清理

- 停止并移除容器/网络但保留数据卷：`down`（不带 `-v`）。
- `down -v` 会删除命名卷（数据库与 Artifact 持久数据），仅在明确要清库时评估后使用。
- 个人生产与 research-validation 栈的卷承载 Canonical State 关联数据；清理前确认
  `docs/operations/BACKUP_RECOVERY.md` 的备份边界。
