---
id: MEM-20260908-017
title: litellm dotenv 门禁非封闭 — 完整 m0 需要 DSN 键钉定
status: ACTIVE
created_at: 2026-09-08
updated_at: 2026-09-08
scope: repository
confidence: 0.95
review_after: 2026-12-08
source_plans:
  - .cursor/plans/tasks/PLAN-20260908-033-research-console-rebuild.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260908-035-research-console-rebuild.md
supersedes: []
tags: [m0, gating, litellm, dotenv, postgres, environment]
---

# MEM-20260908-017 — litellm dotenv 门禁非封闭 — 完整 m0 需要 DSN 键钉定

## 做了什么

定位并处置完整 m0 门禁中 `tests/postgres` parity 套件的"密码认证失败"批量错误：
根因是 litellm import 时 `load_dotenv()` 将操作员 `.env` 的 personal-production DSN
注入测试进程；按 RECHECK-20260906-032 先例，在门禁进程环境预置 postgres-test DSN
并将其余 DSN 键钉为空串，未修改任何仓库代码，复跑 m0 23/23 PASS。

## 为什么这样做

- dotenv 的 override=False 语义：**键已存在（含空串）则不覆盖**——预置即免疫注入。
- 但空串对 `os.environ.get(key, default)` 调用方不是"缺失"——键存在即返回空串，
  所以 `RESEARCHOS_POSTGRES_DSN` 必须预置真实测试 DSN 而非空串。
- 不改产品代码：这是门禁环境问题（PA-1 F-1 同类），产品运行期 DSN 解析语义正确。

## 现象

完整 `run_all_checks.py --profile m0` 内 `tests/postgres/test_workflow_engine_parity.py`
5 个参数化用例在 setup 阶段报 `FATAL: password authentication failed for user "research_os"`；
standalone `pytest tests/postgres/` 同套件 63 全过。伴随框架 evals 偶发
`evolution_state.json.tmp → os.replace` PermissionError（Windows 文件锁，复跑即过）。

## 根因

openhands-sdk → litellm 在 import 时自动 `load_dotenv()`，向上搜索到仓库根操作员
`.env`（gitignored，含 personal-production 栈的 `RESEARCHOS_POSTGRES_DSN`/
`RESEARCHOS_DATABASE_URL`＝旋转密码@127.0.0.1:15432）。`load_dotenv()` 默认
override=False：**键不存在才注入**。PA-1 F-1 曾以"空串钉住 RESEARCHOS_DATABASE_URL/
DATABASE_URL/POSTGRES_DSN"处置；当时 `.env` 无 `RESEARCHOS_POSTGRES_DSN` 行。
2026-09-08 起操作员 `.env` 补了 `RESEARCHOS_POSTGRES_DSN` 行 → 空串方案对它失效，
且空串会被 `tests/postgres/*` 的 `os.environ.get("RESEARCHOS_POSTGRES_DSN", default)`
直接取用（键存在值为空串，不触发 default）→ 连接空 DSN 被拒。

## 怎么做与复现（本计划 RECHECK-20260908-035 验证有效）

运行 m0 的进程环境预置四键，阻止 dotenv 注入且不产生空串 DSN：

```powershell
$env:RESEARCHOS_POSTGRES_DSN = "postgresql://research_os:research_os_m14_test@localhost:15432/research_os"  # postgres-test 凭据
$env:RESEARCHOS_DATABASE_URL = ""; $env:DATABASE_URL = ""; $env:POSTGRES_DSN = ""
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

- `RESEARCHOS_POSTGRES_DSN` 预置正确测试 DSN → dotenv 不覆盖 → parity/worker gateway
  测试连到 postgres-test 容器（`infra/compose/postgres-test.yaml`，tmpfs 临时库，
  需先 `docker compose -f infra/compose/postgres-test.yaml up -d --wait`）。
- 其余三键空串（falsy）→ dotenv 不覆盖 → 设置链跳过 → 各装配回落 SQLite/显式注入。

## 适用边界

- 适用于：本仓库完整 m0 门禁、分段 pytest 批量、任何会 import openhands/litellm 的
  测试进程；操作员 `.env` 含 personal-production DSN 的工作机。
- 不适用于：CI 封闭环境（无操作员 `.env`，dotenv 搜不到文件）；不 import litellm
  的纯前端/工具链检查。
- 不是产品缺陷：运行期（非测试）的 DSN 解析链（settings.py / adapters.postgres.db）
  语义符合 PA-1 设计；本条只约束门禁环境隔离。

## 备忘

- `tests/api/test_worker_plane_composition.py` 3 例带 `@pytest.mark.postgres`，需要
  15432 容器健康；m0 前先起容器。
- 长期方案（未实施，建议 BACKLOG）：门禁运行器统一注入钉定环境，或测试进程内
  阻断 litellm 的 dotenv（如 conftest 预置哨兵值），使操作员 `.env` 与分段门禁彻底隔离。
- 当年 RECHECK-20260906-032 的"三键空串"配方在 `.env` 增加 `RESEARCHOS_POSTGRES_DSN`
  行后失效——**空串钉定对 `os.environ.get(key, default)` 调用方无效**（键存在即返回空串）。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260908-033-research-console-rebuild.md` | STEP-08 全量门禁执行记录 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260908-035-research-console-rebuild.md` | F-01 门禁环境非封闭处置与 23/23 PASS |
| repository | `RECHECK-20260906-032`（个人生产最终复审 F-1 节） | litellm import 时 load_dotenv 的首次定位与空串先例 |
| repository | `.env`（gitignored 操作员文件） | `RESEARCHOS_POSTGRES_DSN` 行是 2026-09-08 失效诱因 |
| repository | `tests/postgres/conftest.py` `_postgres_dsn()` | 键存在即返回（空串不触发 default）的行为证据 |
