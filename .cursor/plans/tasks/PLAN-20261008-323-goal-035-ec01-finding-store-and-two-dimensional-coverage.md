---
id: PLAN-20261008-323
slug: goal-035-ec01-finding-store-and-two-dimensional-coverage
title: GOAL-035 cycle 1（EC-01）：验收结论落 canonical + 两维覆盖判词可读 —— 结论读面 + 两向反证
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-324-goal-035-ec01-finding-store-and-coverage.md
memory_entries:
  - a-judged-verdict-needs-a-recorded-read-face-not-a-recomputation
  - existing-judges-decide-where-a-new-read-face-may-land
parent_goal: GOAL-20261008-035
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-035 的 **EC-01**（来源支持可判定）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**记录，不重算**（读面必须能区分
    「门判过」与「门根本没跑」；派生式读面做不到 ⇒ 不许）；**不放宽任何既有判据的断言**
    （两处实测冲突因此**改设计**而非改判据）；**不改**协议 / 合约 schema；**不改**
    `EVIDENCE_COVERAGE` 的判定语义与判词文本（复用既有 `evaluate_criterion` /
    `count_retrieved_sources`，**不建第二套**）；**不得**把「加了记录面」冒充质量可判定；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-035 EC-01 从「判据存在且被测试」推进到「**研究循环里真的判过、且可复核**」：
    ① **结论落 canonical**：验收门的逐条判词（哪条判据 / 过没过 / 判词里的数）在**求值点**
    落库（新增 `ReviewFindingStore` Port + SQLite/PG 实现 + 迁移），**通过与被拒都记**；
    ② **读面**：新增 `GET /runs/{run_id}/reviews` 只读路由（未接存储 ⇒ 503，未知 run ⇒ 404，
    **不假装空结论**）；③ **判据**：出厂合约 `real_retrieval_deliverable`（两维都声明）实跑
    ⇒ 判过且判词逐字读出两维读数，且读面 claim↔evidence 关系在同一次 run 上同时成立；
    ④ **两向反证**：只抬计数维 ⇒ 判负点名计数；只打掉 / 只抬性质维 ⇒ 判负点名 retrieved
    且同句读出计数维已满足（**两维各自被单独触发**）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **结论落 canonical（写面）**：验收门求值后把逐条判词落库（`finding_id` 主键 ⇒ 重复写
      幂等空操作）；SQLite 与 PG **两个实现同一语义**（判词逐字回读 / 跨 reopen 持久化 /
      run 级隔离）；生产组合根的**写面与读面同一实例**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/contracts/test_review_finding_store_contracts.py -q` ⇒ 3 passed；
      `RESEARCHOS_POSTGRES_DSN=… uv run … -m pytest
      tests/postgres/test_review_finding_store_pg.py tests/postgres/test_migration_files.py -q`
      ⇒ 8 passed（live PG，含新迁移 016）。
    status: PASS
  - id: AC-2
    criterion: >-
      **读面（只读路由）**：`GET /runs/{run_id}/reviews` 经**产品读面**取结论（不经内部
      对象）；未接存储 ⇒ **503 且点名**（不是空列表）、未知 run ⇒ 404；OpenAPI 快照与
      web 类型同步；读面隐私清单逐条登记（新面 = 零命中类 + 理由 + 一等边界）。
    verify: >-
      `tests/e2e/test_two_dimensional_coverage_and_claim_relation.py::
      test_unconfigured_store_and_unknown_run_are_named_not_silently_empty` 绿；
      `tests/contracts/test_openapi_snapshot.py` 绿；
      `tests/observability` ⇒ 132 passed（含白名单派生两向一致）。
    status: PASS
  - id: AC-3
    criterion: >-
      **两维判过 + 判词逐字可读 + 读面关系**（EC-01 (c)）：实跑 `real_retrieval_research_v1`
      ⇒ 结论 `verdict=PASS`，覆盖判词逐字读出两条事实（`N >= min sources; M >= min_retrieved
      retrieved`）；**判词里的性质维读数 = 读面上 `RETRIEVED` 证据条数**（正数，否则子集断言
      在空集上恒真）；计数维读数 = 检索来源 + 声明输入之和（自产制品**不**计入）；读面
      `claim↔evidence` 关系非空且**覆盖全部检索来源**，claim 已 VERIFIED。
    verify: >-
      `tests/e2e/test_two_dimensional_coverage_and_claim_relation.py::
      test_two_dimensional_coverage_passes_and_both_facts_are_readable` 绿（实测判词
      `EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（两维各自被单独触发）**：① 只抬计数维（`minimum_sources=99`，接线不变）
      ⇒ `REJECT` 且判词 `N < 99 sources`（**不提** retrieved），同一判词在失败消息里也在；
      ② 只打掉性质维（不接能力步 ⇒ 检索来源 0，声明输入仍满足计数维）⇒ 判词
      `0 < 1 retrieved sources (1 >= 1 sources)`；②补强：接线不变、只抬性质维阈值
      ⇒ 判词 `2 < 99 retrieved sources (3 >= 1 sources)`（检索来源仍在读面关系里）。
    verify: >-
      同文件 `test_count_dimension_alone_rejects_and_never_names_retrieved` /
      `test_nature_threshold_alone_rejects_with_count_read_as_satisfied` /
      `test_nature_dimension_alone_rejects_while_count_stays_satisfied` 绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **按压（判据不得空转）**：摘除落库 ⇒ 读面空读、判据判红；把计数维放宽成「自产也计入」
      ⇒ 计数维读数判据判红。两次按压后**逐字节复原**。
    verify: >-
      实测：P-1（不落库）⇒ 4 failed（三条 `assert 0 == 1` + 一条索引越界）；
      P-2（计数含自产）⇒ 1 failed（`assert 4 == (2 + 1)`）；`RESTORED`。
    status: PASS
  - id: AC-6
    criterion: >-
      **门绿**：`run_all_checks.py --profile python --keep-going` 六项确定性检查全绿（含全量
      `mypy` 1139 源文件、全量 pytest）；`ruff check` / `ruff format --check` /
      `test_python_source_limits`（450 行 / 50 行）全绿。
    verify: >-
      `PASS: profile=python; 6 deterministic checks`；`tests/tooling/test_python_source_limits.py`
      ⇒ 1149 passed。
    status: PASS
---

# PLAN-20261008-323 — GOAL-035 cycle 1（EC-01）：验收结论的 canonical 读面 + 两维覆盖可读

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 结论落 canonical（Port + SQLite/PG + 迁移 016 + 组合根同实例） | PASS |
| AC-2 | 读面 `GET /runs/{id}/reviews`（503/404 不假装）+ 快照/类型/隐私清单同步 | PASS |
| AC-3 | 两维判过 + 判词逐字可读 + 读面 claim↔evidence 关系（同一次实跑） | PASS |
| AC-4 | 两向反证：计数维单独触发 / 性质维单独触发（换事实 + 换阈值两式） | PASS |
| AC-5 | 按压两次判红且逐字节复原 | PASS |
| AC-6 | python profile 六项门全绿 + 规模门 | PASS |

## 实施清单

- [x] `packages/application/ports/review_finding_store.py`：`ScopedReviewFinding` +
      `ReviewFindingStore` Port（append-only；作用域与域类型分开，**不改** `ReviewFinding`）。
- [x] `adapters/sqlite/review_finding_store.py`：`review_findings` 表 +
      `INSERT OR IGNORE`（同 id 幂等空操作）。
- [x] `adapters/postgres/review_finding_store.py` + `migrations/016_review_findings.sql`：
      与 SQLite 同一语义（`ON CONFLICT (finding_id) DO NOTHING`）。
- [x] `packages/application/run_orchestration/acceptance_observation.py`：`criterion_line`
      （**唯一**判词渲染点，失败消息与落库面共用）+ `acceptance_finding` +
      `record_acceptance_evaluation`（**通过与被拒都记**）。
- [x] 接线：`OrchestrationDependencies.review_findings` / `PhaseRunnerDeps.review_findings` /
      `fact_stores()` / SQLite 组合根 / PG 组合根 / `ApiDeps.review_findings`（写读同实例）。
- [x] `services/api/dto/inspection.py`（`ReviewFindingDto`）+ `routers/inspection.py`
      （`GET /runs/{run_id}/reviews`）；OpenAPI 快照重生成 + `apps/web/src/api/types.ts` 同步。
- [x] 读面隐私清单登记（`tests/observability/read_face_route_registry.py`，ZERO_HIT + 理由 +
      一等边界）。
- [x] 判据：`tests/e2e/test_two_dimensional_coverage_and_claim_relation.py`（5 例：主干 /
      计数维反证 / 性质维阈值反证 / 性质维归零反证 / 读面边界）。
- [x] 存储判据：`tests/contracts/test_review_finding_store_contracts.py`（3 例）+
      `tests/postgres/test_review_finding_store_pg.py`（3 例）。

## 证据

### 勘察读数（实测，非印象）

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | 逐条判词的既有读面 | **只在被拒路径**：`gate_rejection_reason` → 失败消息；通过路径**零读面** |
| 2 | `ReviewFinding` / `Decision` 的持久化 | **从不落库**（全仓 `rg` 无 store 写入；`handoff.decision_refs` 指向一个不存在的对象） |
| 3 | 两维判词形态 | 过（两维）`{c} >= {m} sources; {r} >= {mr} retrieved`；拒计数 `{c} < {m} sources`；拒性质 `{r} < {mr} retrieved sources ({c} >= {m} sources)`；缺维三条 fail-closed |
| 4 | 出厂两维合约 | `real_retrieval_deliverable`（`minimum_sources: 1` + `minimum_retrieved_sources: 1`），被 `real_retrieval_research_v1.yaml` 使用 |
| 5 | 实跑读数（主干） | count=**3**（1 声明输入 + 2 检索来源）、retrieved=**2** ⇒ 判词 `3 >= 1 sources; 2 >= 1 retrieved` |
| 6 | `RETRIEVED` 盖章点 | provider 声明的 `network_domains`（唯一盖章处，未改） |

### 设计决定：为什么是**独立读面**（两处既有判据实测冲突，**都不放宽**）

| 方案 | 撞到的既有判据 | 处置 |
| --- | --- | --- |
| 判词进**事件 payload** | `test_artifact_content_is_not_in_domain_json` 断言事件 payload 不得含 `analysis_report`；而 `ARTIFACT_EXISTS` 判词**逐字点名合约声明的制品名** | **弃**（不放宽该断言） |
| 判词进**制品**（每任务一份结论制品） | `tests/e2e/test_idempotency.py` 断言 `list_refs()` 条数**精确值** | **弃**（不放宽该断言） |
| **独立存储 + 独立只读路由** | 无 | **采用** |

**记录，不是重算**（本 PLAN 的硬约束）：派生式读面（读取时按 canonical 事实重跑判据）
在一扇**从未求值**的门上照样会给出结论 ⇒ 无法区分「门判过」与「门根本没跑」。因此结论在
**求值点**落库，读面只读。

### 判据（新，5 例）

```
tests/e2e/test_two_dimensional_coverage_and_claim_relation.py ..... [100%]  5 passed
```

- 主干：`verdict=PASS` + 判词 `EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`
  两条事实**逐字**读出；判词里的性质维读数 = 读面 `RETRIEVED` 证据条数（且 ≥ 1）；
  计数维读数 = 检索来源 + 声明输入（自产**不**计入，由读面推导）；读面关系覆盖全部检索来源
  且 claim 已 `VERIFIED`（`claim.verified` 事件在同一次 run 的事件链里）。
- 反证 ①③④ 见 AC-4；边界例见 AC-2。

### 按压（AC-5）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `record_acceptance_evaluation` 改为不落库 | **4 failed**（三条 `assert 0 == 1`：读面为空；一条索引越界）⇒ `RESTORED` |
| P-2 | 计数维去掉「自产不计入」过滤 | **1 failed**：`assert 4 == (2 + 1)` ⇒ `RESTORED` |

**设计期对照按压**（对照方案被弃的原因，留档）：把判词放进事件 payload ⇒ 内容隐私金丝雀
1 failed（点名 `analysis_report`）；断掉 retrieved 证据的 relation ⇒ 主干 1 failed
（`assert 2 == 0`：**读面空而判词仍写 `2 >= 1 retrieved`** —— 这正是
`MEM: evidence-read-face-claim-relation` 的失效形态，本 PLAN 的读面关系断言因此是载重的）。

### 门（本 PLAN 触及面）

| 门 | 读数 |
| --- | --- |
| `run_all_checks.py --profile python --keep-going` | **`PASS: profile=python; 6 deterministic checks`**（首跑 `python/typecheck` 1 failed：判据文件两处 `no-any-return`；`python/tests` 1 failed：新读面未登记隐私清单 ⇒ 两条已修） |
| `tests/e2e` / `tests/domain+application+contracts+api` | 248 passed / 2334 passed（含新例） |
| `tests/observability`（含隐私金丝雀 + 白名单派生） | 132 passed, 3 skipped |
| 规模门（450 / 50 行） | 1149 passed；首跑 `composition.py` 457 行、`service.py` 451 行 ⇒ 搬迁 `config_store_parts.py` + 归组 `fact_stores()` ⇒ 418 / 450 |
| **as-is m0**（冻结树，**全部记录写入之后**） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / pytest **5350 passed, 20 skipped**）—— 口径：DSN 钉 15432 + `LLM_MAIN_KEY=""` + 起 OTel collector |
| m0 计数差归因（逐文件 diff，**不是印象**） | 收集数 **5353 → 5372（+19）**，`diff` 逐文件比对**全部分解**：`+3` 存储契约 / `+5` 两维判据 / `+3` PG 存储 / `+8` `test_python_source_limits`（该文件**按源文件参数化**，本轮新增 8 个 `.py`）；**skipped 21 → 20（未升）** ⇒ 无静默转跳 |
| mypy | 1139 源文件 **0 错** |

## 影响报告

- **Domain / API / schema 变化**：API **有**（新只读路由 + `ReviewFindingDto`；OpenAPI 快照与
  web 类型已同步）。**Domain 类型未改**（`ReviewFinding` 原样复用，作用域在存储面）。
  **协议 / 合约 schema 未改**（既有两维合约直接实跑）。
- **安全 / 凭据变化**：无新增凭据面；新读面按既有口径**不认证**（读面认证在本 GOAL 的
  「明确不做」清单里，未变）。读面隐私清单已逐条登记新面 + 一等边界。
- **兼容性 / 迁移风险**：PG 新增迁移 `016`（纯新增表 + 索引，可重入 `CREATE TABLE IF NOT
  EXISTS`）；SQLite 侧由 store 自带 `_SCHEMA` 建表（**既有 gitignored dev DB 需删掉重建**，
  见 `MEM: sqlite-dev-db-stale-schema`）。既有调用方语义**逐字节不变**（缺省 `None` ⇒ 不记）。
- **观测隐私**：新读面返回**判据名 + 声明派生的标识符/枚举/计数**；**一等边界**：
  `SCHEMA_VALID` 判负时判词含校验器错误文本（可能引用输出片段）、`TEST_PASSES` 判负时含
  实验自报的测试名 ⇒ 该面是「按模板不含正文」而非「结构性保证零正文」，已写进隐私清单。
- **上游版本影响**：无。
- **下一项任务**：EC-02（可复现可判定）—— `build_reproducibility_audit` /
  `verify_reproducibility_audit` 目前只在遗留 M12 链被调用，run 路径零调用。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 勘察定稿：两维判据实现完备但**通过路径无读面**；三处既有判据冲突实测（事件面 / 制品面 / 无 finding 存储）⇒ 设计定为「独立存储 + 独立只读路由」。首版曾把判词放进新事件 payload，实测撞内容隐私金丝雀后**改设计而非改判据**。 |
| 2026-10-08 | DONE | 六条 AC 全 PASS：落库（两实现同语义 + 迁移 016）+ 只读路由（503/404 不假装）+ 两维判词逐字可读 + 读面关系 + 两向反证（计数单独 / 性质单独两式）+ 两次按压 + python profile 六项门全绿。`RECHECK-20261008-324` 独立复检。 |
