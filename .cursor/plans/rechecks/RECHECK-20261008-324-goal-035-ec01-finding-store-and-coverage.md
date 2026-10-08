---
id: RECHECK-20261008-324
slug: goal-035-ec01-finding-store-and-coverage
title: 独立复检：GOAL-035 cycle 1（EC-01）验收结论读面 + 两维覆盖可读
plan_id: PLAN-20261008-323
status: COMPLETED
result: PASS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-324 — GOAL-035 cycle 1（EC-01）独立复检

复检对象：`PLAN-20261008-323`（EC-01 验收结论读面 + 两维覆盖可读）。独立重跑下列机械面，
**不引用 PLAN 结论当证据**；每条给出可重跑的读法与读数。

## 检查结果

### 1. 结论落 canonical（AC-1）

| 读法 | 读数 |
| --- | --- |
| `pytest tests/contracts/test_review_finding_store_contracts.py -q` | 3 passed |
| `RESEARCHOS_POSTGRES_DSN=… pytest tests/postgres/test_review_finding_store_pg.py tests/postgres/test_migration_files.py -q` | 8 passed（live PG；迁移 016 被 `_migration_versions()` 从目录派生，未硬编码） |
| 写面与读面同一实例 | `assemble(ApiSettings(db_path=":memory:"))` ⇒ `deps.runs._deps.review_findings is deps.review_findings` = **True**（判据内断言） |
| 判定不是「重算」 | 读面路径**不调用** `evaluate_criterion` / `count_retrieved_sources`：`rg -n "evaluate_criterion\|count_retrieved_sources" services/api/routers/inspection.py` ⇒ 零命中 |

### 2. 读面边界（AC-2）

| 读法 | 读数 |
| --- | --- |
| 未知 run | 404（`test_unconfigured_store_and_unknown_run_are_named_not_silently_empty`） |
| 未接存储 | 503 + `not configured`（**不是空列表**） |
| OpenAPI 快照 | `tests/contracts/test_openapi_snapshot.py` 绿（`/runs/{run_id}/reviews` 在快照内） |
| 读面隐私清单 | `tests/observability` ⇒ **132 passed, 3 skipped**（含 `test_registry_is_an_exact_partition_of_the_read_face` 与派生一致性两向） |

### 3. 两维判过 + 判词逐字 + 读面关系（AC-3）

```
pytest tests/e2e/test_two_dimensional_coverage_and_claim_relation.py -q  ⇒  5 passed
```

判词实测（读面原文）：`EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`
（`verdict=PASS`、`review_type=acceptance_gate`、`contract_id=real_retrieval_deliverable`）。
两条**互不顶替**的自洽断言在位：判词性质维读数 = 读面 `RETRIEVED` 证据条数（且 ≥1）、
计数维读数 = 检索来源 + 声明输入（自产不计入）。

### 4. 两向反证（AC-4）——逐字原文

| 臂 | 改动 | 判词原文 | 收敛 |
| --- | --- | --- | --- |
| ① 只抬计数维 | `minimum_sources=99`（接线不变） | `EVIDENCE_COVERAGE: 3 < 99 sources`（**不提** retrieved） | `FAILED` / `REJECT` |
| ② 只打掉性质维 | 不接能力步（检索来源 0） | `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (1 >= 1 sources)` | `FAILED` / `REJECT` |
| ②补强 | 接线不变、`minimum_retrieved_sources=99` | `EVIDENCE_COVERAGE: 2 < 99 retrieved sources (3 >= 1 sources)` | `FAILED` / `REJECT` |

②补强臂同时断言读面关系里**仍有**检索来源 ⇒ 判负**只**由性质维给出（不是「没检索」的代理）。
①臂的判词与失败消息**同源**（`any("< 99 sources" in message)` ⇒ 渲染只有一处）。

### 5. 按压复核（独立重跑两次按压）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `record_acceptance_evaluation` 直接返回（不落库） | **4 failed**（三条 `assert 0 == 1`，一条索引越界） |
| P-2 | `evidence_source_count` 去掉自产过滤 | **1 failed**：`assert 4 == (2 + 1)` |

两次按压后复原：P-2 的受改文件（`result_handler.py`，已跟踪）`git diff --numstat` **为空**；
P-1 的受改文件是新文件（`git diff` 看不到未跟踪文件）⇒ 复原以**重跑判据全绿**为准
（`pytest tests/e2e/test_two_dimensional_coverage_and_claim_relation.py
tests/contracts/test_review_finding_store_contracts.py -q` ⇒ **8 passed**）。

### 6. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| **as-is m0**（`--profile m0 --keep-going`，冻结树、记录写完之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0；**5350 passed, 20 skipped**） |
| m0 计数与基线对照（基线 = 本 PLAN 之前那次 m0：5330 passed / 21 skipped） | passed **+20**、skipped **−1**；收集数 **+19** 逐文件分解 = 3 + 5 + 3（三份新判据文件）+ 8（`test_python_source_limits` 按源文件参数化 × 本轮新增 8 个 `.py`）⇒ **无未解释用例、无静默转跳** |
| `run_all_checks.py --profile python --keep-going` | **`PASS: profile=python; 6 deterministic checks`** |
| `mypy`（全量，1139 源文件） | `Success: no issues found` |
| `ruff check` / `ruff format --check`（触及面） | 绿 |
| `test_python_source_limits.py` | 1149 passed（`composition.py` 418 行 / `service.py` 450 行） |
| `tests/e2e` | 248 passed, 13 skipped |

### 7. 未覆盖 / 一等边界（不得据本 RECHECK 外推）

- 本复检只覆盖 **EC-01**；EC-02 / EC-03 / EC-04 **尚未收口**（状态以 GOAL frontmatter 为准）；
- **读面未认证**、多租户 / RBAC / BOLA·BFLA 未做、部署面未验证 —— **原样保留**；
- 新读面的隐私口径是「**按判据模板不含正文**」，**不是**「结构性保证零正文」
  （`SCHEMA_VALID` / `TEST_PASSES` 判词的例外已登记在隐私清单里）；
- **不得**据此宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为那四个字（**明确否认**）。

## 结论

**PASS**。六条 AC 的机械面全部独立重跑通过：结论在**求值点**落库（两实现同语义 + 迁移 016）、
只读路由**不假装**（503/404 点名）、两维判词逐字可读且与读面关系**在同一次实跑**成立、
两向反证**各自单独触发**（换事实与换阈值两式结论一致）、按压两次判红且逐字节复原、
python profile 六项确定性检查全绿。**未覆盖范围与一等边界逐条明写，不外推。**
