---
id: RECHECK-20260906-034
plan_id: PLAN-20260906-032
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-06
completed_at: 2026-09-06
reviewer: root-agent-independent-pass
baseline_ref: 88eb5d73c8094c913de1eadbd906fc31d09328ef
checked_head: working-tree-on-88eb5d73c8094c913de1eadbd906fc31d09328ef
---

# RECHECK-20260906-034 — Research Compose 栈独立复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260906-032-research-compose-stack.md`。
- 验收条件：AC-01 至 AC-08；复检从原始目标重查，不继承实现阶段的完成声明。
- 变更范围：`docker-compose.research.yml`、`.dockerignore`、
  `infra/docker/research/`、Compose/Web 配置、直接依赖闭包、定向测试、部署/供应链文档与计划记录。
- 保留边界：任务开始前已有的模块命名 Rule、validator 与两个 architecture 测试不归入本任务；
  当前状态与基线一致，未被覆盖，且完整 M0 门禁验证兼容。
- 基线：未提交工作树，Git HEAD
  `88eb5d73c8094c913de1eadbd906fc31d09328ef`；未创建 commit、未 push、未刷新
  `FRAMEWORK_MANIFEST.json`。
- 冻结命令：Compose `config --quiet`、无缓存 build、`up -d --wait`、HTTP/Worker/隔离 smoke、
  Collector 降级恢复、命名卷 `down/up` 持久性、定向 pytest/ruff、完整 M0 profile、bundle/governance/docs
  validators。验证值仅通过进程环境注入，未写入仓库或复检证据。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围、职责与 Canonical State | 当前 diff；`docker-compose.research.yml`；`RESEARCH_COMPOSE.md`；原有 personal/m14/m15 Compose 未改 | PASS |
| G-02 | AC-01..AC-05：解析、静态契约、构建、运行、TDD | `config --quiet`；独立 `build --no-cache` + `up -d --wait`；ruff/format；Compose/proxy tests **20 passed**；frontend 单测 1 failed → 1 passed | PASS |
| G-03 | AC-06..AC-07：完整质量与治理门禁 | 独立 `run_all_checks.py --profile m0 --keep-going` 返回 0：**23/23 deterministic checks PASS**；Python 收集 3014 项，mypy 713 files，Web 27 tests，typecheck/build、bundle、governance、Hook/learning eval、docs consistency 全部 PASS | PASS |
| G-04 | 安全、凭据隔离与供应链 | 静态契约验证 internal-only、loopback publish、Worker 无 DB/LLM 环境、无 privileged/socket；runtime inspect 验证 Worker read-only、cap drop ALL；构建日志只解析登记的 OCI digest，未解析 Dockerfile frontend | PASS |
| G-05 | 故障隔离、持久性、兼容性与恢复 | Collector stop 时 OpenAPI 仍 200，重启恢复 healthy；独立 PostgreSQL probe database 与 Artifact marker 经 Compose down/up 保留，Worker 重注册；marker 随后删除 | PASS |
| G-06 | 计划完整性、发布边界与最终状态 | `validate.py`；`git diff --check`；`git diff --exit-code -- FRAMEWORK_MANIFEST.json`；无 commit/push/release | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | 阻断（已关闭） | Python runtime image 采用 `uv sync --no-dev` 后暴露 `pydantic`、`PyYAML`、`jsonschema` 仅为开发依赖，API/Gateway 无法启动 | 将三个真实运行时直接依赖精确 pin 到 project dependencies 并刷新 `uv.lock`；无缓存镜像与完整 M0 均通过 |
| F-02 | 阻断（已关闭） | Docker Desktop 对 internal bridge 的直接 PortBindings 不提供可靠宿主机访问 | 保持六个研究服务 internal-only；增加无凭据固定目标 proxy，单独连接关闭 masquerade 的 edge bridge并仅发布 `127.0.0.1` |
| F-03 | 供应链（已关闭） | 三个新 Dockerfile 的 `# syntax=docker/dockerfile:1.7` 会隐式解析可漂移 frontend，且构建不需要其扩展特性 | 先增加回归断言并观察 1 failed，再删除三条指令；两次独立无缓存重建均未再解析该 frontend |
| F-04 | 验证探针（已关闭） | 首次 smoke 用原始 `worker_id` 检查 `/cluster/workers`，与 API 有意只暴露 digest `worker_ref` 的隐私契约冲突 | 不改产品；按 DTO 契约检查 12 位脱敏 `worker_ref`、READY 状态，并以 Worker 日志确认注册源 |

## 结论

- 结果：`PASS`。
- 理由：AC-01 至 AC-08 的 hard gate 均有独立、可复现的运行证据；最终完整 M0 profile
  为 23/23 PASS，Compose 无缓存构建、健康启动、故障隔离与持久卷恢复均通过。
- 安全结论：默认栈无 Docker Socket、无 privileged、无公共网络出口；Worker 不接收 PostgreSQL/LLM
  凭据；宿主机入口仅为 loopback 固定目标 proxy；所有新增镜像基座有精确 digest、许可证与升级门禁。
- 兼容性结论：未变更 Domain/API DTO/Schema/migration；原 personal/m14/m15 Compose 保持不变；
  `FRAMEWORK_MANIFEST.json` 未修改。
- 后续动作：将 PLAN-20260906-032 标记 `DONE`；无可复用事实需要另建工程记忆，稳定操作事实由部署文档、
  静态契约测试与供应链登记承载。不自动进入真实 Docker/GPU Worker 容器化或发布流程。
