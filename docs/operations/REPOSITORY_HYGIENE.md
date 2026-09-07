# Repository Hygiene — 根目录分类归档规则

本文件固化仓库根目录的分类边界：哪些资产必须留在根目录、哪些归入专责目录、
哪些是可再生垃圾、哪些是受保护的本地状态。回归门禁为
`tests/tooling/test_repository_root_layout.py`，它只约束工程资产布局，
不检查、不删除凭据、运行数据或用户本地历史。

## 1. 必须留在根目录（固定根锚点）

工具链要求文件位于仓库根，移动即破坏解析：

- `VERSION`、`UPSTREAM_COMPONENTS.yaml`（上游组件登记与 pin 清单）
- `pnpm-workspace.yaml`、`pnpm-lock.yaml`、`uv.lock`（workspace/锁文件）
- `pyproject.toml`、`tsconfig*.json`、`eslint.config.mjs`、
  `dependency-cruiser.config.mjs`、`.prettierrc.json`、`.python-version`、`.node-version`
- `.importlinter` 与全部 `.importlinter.*` 契约配置
- 入口文档：`README.md`、`AGENTS.md`、`CHANGELOG.md`、`BACKLOG.md`、
  `CODEX_BOOTSTRAP.md`、`Makefile`
- 忽略与打包边界：`.gitignore`、`.gitattributes`、`.dockerignore`、`.cursorignore`、
  `.prettierignore`、`.env.example`
- 发布快照（只由显式发布流程生成）：`FRAMEWORK_MANIFEST.json`、
  `.cursor/releases/RELEASE_EVIDENCE.json`

根目录 YAML/YML 白名单（由门禁断言）：`UPSTREAM_COMPONENTS.yaml`、
`pnpm-lock.yaml`、`pnpm-workspace.yaml`。

## 2. 归入专责目录的工程资产

工程资产放入职责目录，不堆在根目录：

- Compose 栈 → `infra/compose/`（见 `infra/compose/README.md` 的职责说明与迁移映射）
- Dockerfile 与容器辅助脚本 → `infra/docker/`
- CI 工作流 → `.github/workflows/`
- 文档 → `docs/`；CLI 与校验脚本 → `tools/`；测试 → `tests/`

历史迁移映射（2026-09-07 根目录分类归档）：

| 旧路径（根目录） | 当前路径 |
| --- | --- |
| `docker-compose.m14.yml` | `infra/compose/postgres-test.yaml` |
| `docker-compose.m15.yml` | `infra/compose/otel-evidence.yaml` |
| `docker-compose.personal.yml` | `infra/compose/personal-production.yaml` |
| `docker-compose.research.yml` | `infra/compose/research-validation.yaml` |

历史 completion/audit/qualification 记录保留原路径表述，只补充本映射说明，
不改写原验收事实。

## 3. 可再生、可精确删除

以下内容为工具或测试运行产物，被 `.gitignore` 忽略，可在确认无源码/文档引用后
按精确路径删除；删除后由对应工具重新生成：

- 根目录运行日志：`m0_profile_run.log`、`m13_gate.log`、`m13_reauth_gates.log`、`.vite-e2e.log`
- 工具缓存目录：`.import_linter_cache/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`

删除纪律：不使用 `git clean` 或通配式破坏性删除；若候选文件出现新引用、被进程
占用或不再被忽略，则跳过并报告。

## 4. 受保护的本地状态（不清理、不移动）

- 运行数据与产物：`data/`、`artifacts/`、`.artifacts/`
- 工作现场：`scratch/`、`.cursor/plans/`（含已完成 Plan 与 Recheck，保持不动）
- 凭据域：`.env`、`secrets/`（只由凭据管理流程处置，见 `docs/security/SECRET_MANAGEMENT.md`）
- 第三方 Agent 状态目录：`.workbuddy/`、`.zcode/`、`.mimosa/`、`.freebuff/`、`.venv/`、`node_modules/`

## 5. Compose 调用约定

四个栈统一从仓库根调用，并显式固定项目目录：

```text
docker compose --project-directory . -f infra/compose/<stack>.yaml ...
```

`--project-directory .` 保证文件移动后 build context、bind mount 与根 `.env`
仍以仓库根解析；省略它会把相对路径解析到 `infra/compose/` 下，造成构建上下文与
凭据加载回归。清理卷必须显式评估后使用 `down -v`，默认只用 `down`。
