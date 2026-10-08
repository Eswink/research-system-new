---
id: PLAN-20261008-337
slug: goal-037-ec01-canonical-program-skeleton
title: GOAL-037 cycle 1（EC-01）：勘察定稿 + 研究程序的 canonical 骨架（域类型 + store + 迁移 + 接线）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-338-goal-037-ec01-canonical-program-skeleton.md
memory_entries:
  - jsonb-decodes-must-accept-parsed-objects
parent_goal: GOAL-20261008-037
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-037 的 **EC-01**（勘察定稿）与 EC-02 的前置骨架。授权原文见该 GOAL
    的 `authorization.ref`。**本 PLAN 专属边界**：程序 ↔ run 的关联**只落 canonical**
    （`ResearchRun` 字段 + `runs` 表列 + 程序面两张表）；**不改**任何既有判据断言
    （新增判据属新增文件）；新读面 / 新 DTO 字段按既有纪律同轮同步（OpenAPI 快照 +
    `types.ts`，由既有判据决定）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为
    那四个字（**明确否认**）。
objective: >-
    把 GOAL-037 的两条实测缺口落成**可实现的骨架**：① **决策定稿（EC-01）** —— 六条
    设计决策逐条定稿（关联落点 / 编排落点 / 读形态 / memory 边界 / 轮数纪律 / 承接面），
    每条带读数；② **canonical 骨架** —— `ResearchRun` 增 `program_id` / `program_index`
    （None = 独立 run，向后兼容），`RunStore.for_program`（按载荷 JSON 抽取，**不改 `runs` DDL**）；领域
    `ResearchProgram`（声明 + 上界护栏）+ `ProgramStore` 端口 + SQLite / PG 适配器 +
    PG 迁移 017 + 两个组合根接线；③ **同轮同步**：run 序列化的全部落点（两个 run store /
    canonical 读面 / API DTO）+ OpenAPI 快照 + `types.ts`（由既有判据逐条钉住）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **六条设计决策定稿且带读数**：① 关联落点 = `ResearchRun` 字段 + `runs` 表列
      （canonical）；② 编排落点 = `packages/application/run_orchestration/` 新模块
      （通过既有 start-run use case，不绕 preflight / freeze）；③ 读形态 = GOAL-036 承接链
      （能力名取词表里**已登记未承接**的 `research_state.read`，不扩词表）；④ memory 边界
      = 不动 memory 面；⑤ 轮数 = 结论驱动 + 上界护栏可区分；⑥ 承接面只为这一件事扩容。
    verify: >-
      本 PLAN 的「决策定稿」节逐条 + 复核命令与读数；`rg` 读数（词表 46 不变、
      `research_state.read` 在差集表）。
    status: PASS
  - id: AC-2
    criterion: >-
      **程序关联落 canonical 且向后兼容**：`ResearchRun` 增 `program_id: str | None = None`
      / `program_index: int | None = None`（校验：program_id 非空串时 index 必须 ≥ 1，两者
      同生同灭）；`RunStore.for_program(program_id) -> tuple[ResearchRun, ...]`（按 index
      排序；**落地形态修订**：关联在既有 run 载荷内、按 JSON 抽取查询，**不增 `runs` 表列**
      —— 理由见决策 ①）；
      两个 run store 的**序列化逐字段**（to_dict / from_dict）同步 —— 漏一处在
      「迁移一次就静默丢失」（本仓既有教训）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters -q` ⇒
      全绿；新判据：round-trip（含 program 字段）+ 旧行（无 program 字段）反序列化仍成立。
    status: PASS
  - id: AC-3
    criterion: >-
      **程序域类型 + 存储 + 迁移**：`packages/domain/program.py::ResearchProgram`
      （id / project_id / protocol_id / max_runs / created_at / updated_at；校验 max_runs ≥ 1）；
      `packages/application/ports/program_store.py`（create / get / for_project /
      record_decision / decisions_of / close）；SQLite + PG 适配器；
      PG 迁移 `017_research_programs.sql`（`research_programs` + `program_decisions` 两表，
      决策表含**被引事实的原文**列）；两个组合根接线（sqlite / pg）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿；
      迁移可跑（test DB 上 `pg_migrate` 通过）。
    status: PASS
  - id: AC-4
    criterion: >-
      **同轮同步（只增字段，不改既有断言）**：run 的读面 / DTO 同步 ——
      `adapters/canonical/run_read.py` 载荷、`services/api/routers/runs.py` 的 run DTO、
      OpenAPI 快照（按生成器重生成）+ `apps/web` 类型；既有判据逐条钉住（差分只增字段）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿；OpenAPI 快照判据绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **门链 + 记录面**：ruff / format / mypy / 规模四道门绿；新增记录（本 PLAN、
      GOAL 迭代日志 / 状态历史行）；治理 `validate.py` 绿；记录面判据绿；
      as-is m0 **23/23**（记录写完之后）。
    verify: >-
      门读数逐条 + `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261008-337 — GOAL-037 cycle 1（EC-01）研究程序的 canonical 骨架

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 六条设计决策定稿（带读数） | PASS |
| AC-2 | 程序关联落 canonical（域字段 + for_program + 序列化） | PASS |
| AC-3 | 程序域类型 + 存储 + 迁移 017 + 组合根接线 | PASS |
| AC-4 | 同轮同步（读面 / DTO / OpenAPI / 前端类型） | PASS |
| AC-5 | 四道门 + 记录面 + 治理 + as-is m0 23/23 | PASS |

## 决策定稿（AC-1；逐条带读数）

| # | 决策 | 定稿内容 | 依据 / 读数 |
| --- | --- | --- | --- |
| ① | 程序 ↔ run 关联落点 | `ResearchRun.program_id` + `program_index`（None = 独立 run）；**关联在 run 载荷内**（`run_json`），查询走 JSON 抽取 | 关联必须与 run 的写入**同一次**落 canonical（避免「先起 run 后绑定」的窗口）。**落地形态修订（实现期）**：`runs` 行本就是 JSON 载荷 ⇒ **不增列、不加索引**（`json_extract` / `->>`），把爆炸半径压到零（既有 DDL / 迁移 / 平台差异全不触碰）；程序内 run 数为个位数，扫描代价可忽略；规模变了再评估增列（`RECHECK-20261008-338` W-4 登记） |
| ② | 编排落点 | `packages/application/run_orchestration/` 新模块（驱动）；通过既有 start-run use case 启动 | 应用层不 import `services/api`（分层）；起点仍是 compile → preflight → freeze → execute |
| ③ | 跨 run 知识的读形态 | 承接**词表里已登记但未承接**的 `research_state.read`（**不扩词表**） | 词表 46 条不变；`research_state.read` 在差集表（`POLICY_SURFACE_AUDIT.md`），语义正是「研究状态（含程序内前序 run 的结论）」 |
| ④ | memory 面 | **不动**（无项目维度是另一条线） | GOAL-037 决策 ④；`MemoryRecord` / `m12_memory` / `GET /projects/{id}/memory` 零改动 |
| ⑤ | 轮数 | 结论驱动 + 上界护栏**可区分** | 承 GOAL-034 纪律：先结论后护栏；停止理由逐字留档 |
| ⑥ | 承接面 | 只为这一件事（`research_state.read`）扩容 | MAINLINE：广度不是一条轴；不做数量目标 |

## 实施清单

- [x] `packages/domain/run.py`：`program_id` / `program_index`（+ 校验 + 逐字段复制纪律）。
- [x] `adapters/{sqlite,postgres}/run_store.py`：编码/解码逐字段 + `for_program`（JSON 抽取）。
- [x] `adapters/postgres/migrations/017_research_programs.sql`：`research_programs` + `program_decisions`（**不动 `runs`**）。
- [x] `packages/application/ports/run_store.py`：`for_program`。
- [x] `adapters/{sqlite,postgres}/run_store.py`：序列化逐字段 + `for_program`。
- [x] `packages/domain/program.py` + `packages/application/ports/program_store.py`。
- [x] `adapters/{sqlite,postgres}/program_store.py`。
- [x] 组合根接线（`services/api/composition.py` / `pg_composition.py`）+ DTO/读面/快照同步。
- [x] 记录面：本 PLAN、GOAL 行、`ALL_PLAN`。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 关联落 canonical | `packages/domain/run.py`（两字段 + 同生同灭校验 + 三个重建函数逐字段复制）；`adapters/{sqlite,postgres}/run_store.py`（编码/解码 + `for_program`）；`packages/application/ports/run_store.py` |
| WP-2 | 程序域与存储 | `packages/domain/program.py`；`packages/application/ports/program_store.py`；`adapters/{sqlite,postgres}/program_store.py`；`adapters/postgres/migrations/017_research_programs.sql` |
| WP-3 | 接线 | `services/api/composition.py` / `pg_composition.py`（两组合根同侧；`ApiDeps.program_store`） |
| WP-4 | 同轮同步 | `services/api/routers/runs.py` + `services/api/dto/runs.py`；`adapters/canonical/run_read.py`；`docs/api/openapi.m13.json`（生成器重生成，+22 行）；`apps/web/src/api/types.ts` |
| WP-5 | 判据 | `tests/domain/test_research_program.py`（9 例）；`tests/adapters/sqlite/test_program_store_sqlite.py`（4 例）；`tests/postgres/test_program_store_pg.py`（2 例）；三个既有假 RunStore 补 `for_program`（mypy `arg-type` 逐处点名后补） |
| WP-6 | 记录面 | 本 PLAN、`RECHECK-20261008-338`、`MEM-20261008-207`、GOAL 行、`ALL_PLAN` |

### 门（实测读数）

| 门 | 读数 |
| --- | --- |
| `ruff check`（改动面） | `All checks passed!` |
| `ruff format --check` | 绿（新增/改动文件逐条已格式化） |
| `mypy`（strict） | `Success: no issues found in 1151 source files` |
| 新判据 | `tests/domain/test_research_program.py` **9 passed**；`tests/adapters/sqlite/test_program_store_sqlite.py` **4 passed**；`tests/postgres/test_program_store_pg.py` **2 passed** |
| 广面套件 | `tests/domain + tests/adapters + tests/contracts` **1590 passed, 5 skipped**；`tests/application + tests/architecture` **1063 passed, 1 skipped**；`tests/contracts + tests/api + tests/tooling` **2516 passed, 76 skipped** |
| 迁移 | live PG `migrate` ⇒ `migration_version` 最新 **17**；`research_programs` / `program_decisions` 两表可见 |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / **5389 passed, 20 skipped**；收集数 +22 = 新判据 15 例 + 源文件参数化（新模块 5 个源文件 × 规模门参数）逐文件分解；`skipped` 20 未升）。日志 `scratch/m0-goal037-cycle1-rerun.log`（gitignored）（首跑**真红**于前端型检查 ⇒ 同轮同步夹具后重跑取值） |

> **一次真红并修（门链抓到，如实登记）**：as-is m0 **首跑真红**于三个前端型检查
> （`typescript/typecheck` / `typescript/web-typecheck` / `typescript/web-build`）——
> `apps/web/tests/e2e/apiFixtures.ts` 与 `apps/web/tests/e2e/stub-routes-runs.ts` 的
> **7 处 `RunDetailDto` 字面量**缺新增的 `program_id` / `program_index`
> （TS2739 逐处点名）。处置 = **同轮同步夹具**（补 `null`），不是放宽类型；修后三个检查
> 分别单跑绿（`tsc --noEmit` / `pnpm typecheck` / `web build`）⇒ 重跑全量 m0 取终局读数。
> 教训与既有纪律一致：**改 DTO 要同步 OpenAPI 快照 + `types.ts` + e2e 夹具**三处
> （本轮前三处里漏了第三处，被门链咬住）。

> **一次真红并修（如实登记）**：`PostgresProgramStore` 首版读 JSONB 列用了
> `json.loads(str(row[...]))` ⇒ live PG 上 `JSONDecodeError`（psycopg 把 jsonb 回成已解析
> 对象）。处置 = **两形态都接住**（`_json_object`），并把这条写进 `MEM-20261008-207`；
> 同一轮 mypy 以 `arg-type` 点名 3 个测试假 RunStore 缺 `for_program` ⇒ **补假实现**
> （不是给 Port 加默认实现、也不是 `# type: ignore`）。

## 影响报告

- **Domain / API / schema 变化**：Domain 增字段与类型；新增两张表（迁移 017）；
  `runs` 表**不动**（关联在既有载荷内）；API DTO 只增字段。
- **安全 / 凭据变化**：无（不动放行面 / 不动 memory 面）。
- **兼容性 / 迁移风险**：旧 run 行无 program 字段 ⇒ 反序列化按 None（判据钉住）；
  SQLite 侧零 `_SCHEMA` 变更 ⇒ **无需**删开发库。
- **观测隐私**：无新出口（决策记录只留 digest / 原文判词，不含新敏感面）。
- **上游版本影响**：无。
- **下一项任务**：cycle 2（驱动 + advance 入口 + 双 run 实跑 ⇒ EC-02）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 建档：六条决策定稿（带读数）；骨架 WP 待落地。 |
| 2026-10-08 | DONE | WP-1…WP-6 全部落地：关联落 canonical（域字段 + `for_program` + 两个 run store 序列化）、程序域/存储/迁移 017/两组合根接线、同轮同步（读面 + DTO + OpenAPI 重生成 + `types.ts`）、新判据 15 例全绿、四道门绿。**一次真红并修**：PG JSONB 解码（已登记 `MEM-20261008-207`）；mypy `arg-type` 点名三处假 RunStore ⇒ 补假实现。`RECHECK-20261008-338` 独立复检。 |
