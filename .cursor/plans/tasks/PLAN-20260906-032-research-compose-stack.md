---
id: PLAN-20260906-032
slug: research-compose-stack
title: Research OS 容器化 Compose 验证栈
status: DONE
created_at: 2026-09-06
updated_at: 2026-09-06
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-06：在 Docker 中创建 Research OS Compose 容器组成，执行完整验证，发现问题后计划修复并循环至全部 PASS"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260906-034-research-compose-stack.md
memory_entries: []
---

# PLAN-20260906-032 — Research OS 容器化 Compose 验证栈

## 目标

提供一个可由单条 Docker Compose 命令构建、启动并验证的 Research OS 本地栈，包含
PostgreSQL、OpenTelemetry Collector、Control Plane API、Worker Gateway、默认安全的
确定性 Worker 与 Research Console；随后在同一冻结环境中执行完整 M0 门禁及容器集成
验证，对失败项逐一修复并循环复跑，直到全部 hard gate 通过。

## 范围

- 包含：
  - 新增独立的 `docker-compose.research.yml`，不改变已验收的个人生产 Compose。
  - 新增职责单一且供应链固定的 Python 服务镜像与 Web Console 镜像。
  - PostgreSQL 作为 Canonical State；API 与 Gateway 共用内容寻址 Artifact 卷。
  - Collector 仅承载可丢弃的派生遥测；停止 Collector 不影响业务状态。
  - 六个研究服务仅连接 internal network；无凭据固定目标 proxy 负责宿主机 loopback publish。
  - Worker 默认使用确定性执行后端，不挂载 Docker Socket，不接收数据库或 LLM 凭据。
  - Gateway 与 Worker 共享容器网络命名空间并保持 Gateway loopback bind，避免伪报 TLS。
  - Compose 静态契约测试、真实 build/config/up/health/smoke/down/up 验证。
  - 完整 `m0 --keep-going` 验证及所有新失败的定位、最小修复、回归复跑。
  - 同步部署文档、环境变量模板、供应链 pin/许可证证据和文档索引。
- 不包含：
  - 不把宿主机 Docker Socket 暴露给默认 Worker。
  - 不声称确定性 Worker 是真实 Docker/GPU 执行平面。
  - 不改变 Domain、产品 API DTO、Schema、数据库 migration 或已接受 ADR。
  - 不修改 `docker-compose.personal.yml` 的个人生产验收边界。
  - 不执行 Git commit、push、PR、tag、release 或 Manifest 刷新。
  - 不修复与本任务无关且会覆盖用户现有改动的问题；若其阻断全量门禁，只记录并在不覆盖的前提下做兼容修复。

## 架构与数据流

```text
Browser / host tests → credential-free fixed-target proxy
                     → Console / API / PostgreSQL / Collector

Deterministic Worker → shared-loopback Worker Gateway
                     → PostgreSQL queue/lease/fencing
                     → shared Artifact volume through Gateway only

API / Worker / Gateway → OTel Collector → gitignored disposable telemetry bind directory
```

- 所有者模块：根 Compose 负责编排；`infra/docker/research/` 只负责镜像构建与容器入口；
  `services/api`、`services/worker` 与 `apps/web` 保持原有 entry adapter 职责。
- 上游输入：根 `VERSION`、`uv.lock`、`pnpm-lock.yaml`、`.env` 中显式凭据与端口。
- 下游输出：PostgreSQL/Artifact/控制面命名卷、`data/otel` 派生文件和 loopback HTTP 服务。
- Canonical State：仅 PostgreSQL Domain Entity；Console、Worker、Collector 与容器状态都不是业务真相。
- Port / Adapter：API/Gateway 通过现有 PostgreSQL、Artifact、Telemetry adapters；Worker 仅通过 HTTP Gateway。
- Policy / Security Gate：后端 internal network、固定目标无凭据 proxy、loopback publish、
  edge bridge 禁用 IP masquerade、非 root/read-only 应用容器、`no-new-privileges`、`cap_drop: ALL`、无 Docker Socket、无真实 LLM、无公共网络。
- 状态与失败语义：Compose healthcheck 失败即启动失败；Worker 注册必须可由 API 读取；
  Collector 故障只允许遥测降级；PostgreSQL/Gateway 故障阻断对应业务链。

## 验收条件

- [x] AC-01：`docker compose -f docker-compose.research.yml config` 成功，六个研究服务加
  host proxy、卷、internal/edge network、依赖与 healthcheck 均解析正确。
- [x] AC-02：静态契约测试证明默认栈无 Docker Socket/privileged/public bind，Worker 环境无
  PostgreSQL/LLM 凭据，所有新外部镜像与构建工具均精确 pin 并有许可证/升级门禁。
- [x] AC-03：`docker compose ... up -d --build --wait` 成功，PostgreSQL、Collector、API、
  Gateway、Worker、Console 全部 running/healthy，API OpenAPI、Console 首页与 Worker 注册可读。
- [x] AC-04：同一 Compose 项目执行一次 stop/start 或 down/up 重建后，PostgreSQL 与 Artifact
  命名卷保留，服务恢复且 worker 重新注册；不删除用户既有卷。
- [x] AC-05：新增测试先出现预期 RED，再由最小实现转为 GREEN；相关 Python/TypeScript/
  Compose 定向测试全部通过。
- [x] AC-06：在 Compose 提供 PostgreSQL/Collector、Docker daemon 可用的串行环境中，完整
  `run_all_checks.py --profile m0 --keep-going` 返回 0，所有 selected checks 为 PASS。
- [x] AC-07：`validate_bundle.py`、治理 validator、文档一致性检查和 Compose smoke 最终复跑均 PASS；
  普通验证不修改 `FRAMEWORK_MANIFEST.json` 或 release evidence。
- [x] AC-08：复检覆盖范围、架构、安全、凭据隔离、兼容性与实际运行证据，结论为 PASS 或仅含
  不阻断且明确记录的 PASS_WITH_WARNINGS。

## 实施清单

- [x] STEP-01：记录现有 Compose、运行入口、Docker 版本、工作区用户改动与全量门禁基线。
- [x] STEP-02：先新增 Compose 静态契约测试并运行，确认因目标资产缺失而 RED。
- [x] STEP-03：实现固定供应链的 Python/Web 镜像、`.dockerignore` 与安全 Compose 拓扑。
- [x] STEP-04：同步 `.env.example`、部署说明、供应链注册、许可证矩阵与 `docs/INDEX.md`。
- [x] STEP-05：运行定向 lint/typecheck/tests 与 `docker compose config/build/up --wait`，修复至通过。
- [x] STEP-06：执行 API/Console/Worker 注册、凭据隔离、Collector 降级和持久卷重启 smoke。
- [x] STEP-07：串行运行完整 M0 profile；每个失败先分类、补回归证据、最小修复并重跑。
- [x] STEP-08：创建独立 recheck attempt，重跑最终 gates，记录证据并更新计划状态。

## 子代理使用

Subagent 默认不启用。本任务的 Compose 实现、运行态验证与失败修复存在顺序依赖，根代理
直接执行，避免无意义 fan-out。若最终出现可独立复核的架构/安全面，再单独决定是否委派；
每个 wave 最多 3 个且禁止二次委派。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | 顺序执行更符合共享 Docker 状态约束 |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | check | `git status --short`; `docker version`; `docker compose version` | Docker Engine 29.2.1、Compose v5.1.0；4 个既有模块命名治理改动需保留 |
| EV-02 | STEP-01 | file | `docker-compose.m14.yml`, `docker-compose.m15.yml`, `docker-compose.personal.yml`, `PERSONAL_DEPLOYMENT.md` | 现状只容器化 PostgreSQL/Collector，其余为宿主机进程 |
| EV-03 | STEP-02/05 | TDD | `pytest tests/tooling/test_research_compose.py`; frontend 回归单测 RED→GREEN | 目标资产缺失阶段先失败；最终供应链缺陷回归精确复现为 1 failed，删除三条 `# syntax=` 后 1 passed |
| EV-04 | STEP-03/04 | files | Compose、3 个 Dockerfile、固定目标 proxy、`.dockerignore`、部署/供应链文档 | 七容器编排；六个研究服务 internal-only；外部镜像按 OCI index digest 固定并登记许可证/升级门禁 |
| EV-05 | STEP-05 | check | ruff check/format + `pytest tests/tooling/test_research_compose.py tests/tooling/test_loopback_proxy.py -q` | lint/format PASS；20 passed |
| EV-06 | STEP-05 | runtime | `docker compose ... config --quiet`; `build --no-cache`; `up -d --wait` | 全部返回 0；七容器 running，五个带 healthcheck 的服务 healthy；构建只解析已登记 digest，无 Dockerfile frontend 拉取 |
| EV-07 | STEP-06 | smoke | OpenAPI、Console、`/cluster/workers`、worker container inspect | HTTP 200；1 个 READY 脱敏 worker projection；Worker 非 privileged、只读 rootfs、drop ALL、无 Docker Socket |
| EV-08 | STEP-06 | recovery | Collector stop/start；PostgreSQL 独立 probe database + Artifact marker 后 Compose down/up | Collector 停止时 API/Canonical State 可读且恢复 healthy；两类 marker 保留；Worker 重新注册；测试 marker 已删除 |
| EV-09 | STEP-07 | full gate | `run_all_checks.py --profile m0 --keep-going` | 返回 0；profile=m0 的 23 个确定性检查全部 PASS，含 3014 项 Python 收集、Web 27 tests、mypy 713 files、bundle/governance/docs checks |
| EV-10 | STEP-07 | release boundary | `release-assets-immutable`; `git diff -- FRAMEWORK_MANIFEST.json` | PASS；普通验证未修改发布 Manifest |
| EV-11 | STEP-08 | recheck | `RECHECK-20260906-034-research-compose-stack.md` | PASS；独立重跑无缓存 build、运行态/恢复 smoke、20 项定向测试与完整 M0 23/23 gates |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-06 | 初始化为独立 research Compose，而非扩写 personal Compose | 保留 PA-1/PA-1R 已验收个人生产基线与迁移路径 | 新栈定位为本地完整集成/验证，不篡改历史运行事实 |
| 2026-09-06 | 默认 Worker 使用 deterministic backend | 默认禁止 Docker Socket；真实 Docker/GPU Worker 需独立高权限宿主机部署 | 可验证分布式控制链，但不冒充真实实验执行平面 |
| 2026-09-06 | Gateway 与 Worker 共享网络命名空间 | Gateway 代码对非 loopback 明文 bind fail closed；设置虚假 TLS 标志不可接受 | Gateway 保持 127.0.0.1，无宿主机暴露，Worker 仍可访问 |
| 2026-09-06 | 增加无凭据固定目标 host proxy | Docker Desktop 对 internal bridge 的 PortBindings 不提供宿主机可达性；直接把 API/DB 接入普通 bridge 会放开公共出口 | 六个研究服务保持 internal-only；仅 proxy 跨接禁用 masquerade 的 edge bridge |
| 2026-09-06 | 不重复请求实施批准 | 用户当前请求已明确授权实现、验证与失败修复循环 | 计划不扩大到发布、真实凭据或高权限 Worker |
| 2026-09-06 | 删除三个 Dockerfile 的 `# syntax=docker/dockerfile:1.7`，并增加回归测试 | 当前构建不使用必须依赖该 frontend 的特性；可漂移标签会形成未登记的隐式供应链依赖 | 无缓存重建改用 Docker 内建 Dockerfile 解析器；已登记 base/builder digest 不变 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-06 | — | APPROVED | 用户请求明确授权本范围实施与循环验证 | 当前用户请求 |
| 2026-09-06 | APPROVED | IN_PROGRESS | 完成最小仓库地图并开始基线与 TDD | EV-01、EV-02 |
| 2026-09-06 | IN_PROGRESS | VERIFYING | 实现、运行态恢复 smoke 与完整 M0 门禁通过，冻结独立复检范围 | EV-03..EV-10、RECHECK-20260906-034 |
| 2026-09-06 | VERIFYING | DONE | 独立复检重跑全部 hard gate 并判定 PASS | EV-11、RECHECK-20260906-034 |

## 影响报告

- Domain/API/schema：无 Domain、API DTO、Schema 或 migration 语义变化；新增部署入口，并让 Vite dev/preview 共用可配置 API proxy。
- 安全/凭据：新增进程级最小环境、internal network、loopback publish；默认无 Docker Socket；验证值未写入仓库。
- 兼容性/迁移：不改数据库 migration；新 Compose 与 personal/m14/m15 文件并存，普通 `down` 保留命名卷。
- 上游版本：Python、uv、Node、pnpm、PostgreSQL 与 Collector 均有精确版本/digest、许可证和升级门禁；无浮动 Dockerfile frontend。
- 工程记忆：无可复用事实需要另建工程记忆；稳定操作事实已由 `RESEARCH_COMPOSE.md`、静态契约测试和供应链登记共同承载。
- 下一项任务：完成后只报告结果，不自动进入真实 Docker/GPU Worker 容器化或发布流程。
