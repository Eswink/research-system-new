---
id: RECHECK-20261008-326
slug: goal-035-ec02-reproducibility-conclusion
title: 独立复检：GOAL-035 cycle 2（EC-02）可复现结论进读面
plan_id: PLAN-20261008-325
status: COMPLETED
result: PASS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-326 — GOAL-035 cycle 2（EC-02）独立复检

复检对象：`PLAN-20261008-325`。独立重跑下列机械面，**不引用 PLAN 结论当证据**。

## 检查结果

### 1. 审计在 run 路径产出并落库（AC-1）

| 读法 | 读数 |
| --- | --- |
| `pytest tests/application/experiments tests/e2e/test_ec02_experiment_chain_offline.py -q` | 96 passed |
| **可审态口径复用**（不是自写门） | `rg -n "is_auditable_state" packages/application/experiments/execute.py` ⇒ 命中；`rg -n "run.is_terminal" …/execute.py` ⇒ **零命中** |
| id 派生复用 | `rg -n 'derived_id\("audit"' packages/` ⇒ 只出现在 `clean_run_stages.py`（遗留链）与 `execute.py`（新路径），**同一口径** |
| 落库点 | `_persist_run` 同时 `save_run` + `save_audit`（同一处、同一存储） |

### 2. 读面与声明面（AC-2）

| 读法 | 读数 |
| --- | --- |
| `pytest tests/api tests/contracts -q` | 全绿（无审计夹具上 `reproduction_available is False` + note 含 `unavailable` **仍成立**） |
| `pytest tests/observability -q` | 133 passed, 2 skipped（隐私清单分区 + 派生两向一致） |
| OpenAPI 快照 | `tools/gen_openapi.py` 重生成后 `tests/contracts/test_openapi_snapshot.py` 绿（新增 4 字段 + 新 DTO） |
| web 类型同步 | `apps/web/src/api/types.ts` 已加 `AuditFindingDto` + 四字段 |

### 3. 主干判据（AC-3）——两条独立路径一致

```
pytest tests/e2e/test_reproducibility_conclusion_on_the_run_path.py -q  ⇒  3 passed
```

读面读数：`reproduction_available=true`、`audit_digest` `sha256:` 前缀、`audit_status=PASS`、
`audit_verified=true`、**零 FAIL 发现**（WARNING `CODE_DIGEST_NOT_PINNED` 如实呈现）。
独立路径：从**存储**取回审计对象自行 `compute_audit_digest()` 与读面读数**逐条一致**。

### 4. 反证两向（AC-4）

| 臂 | 改动 | 读数 |
| --- | --- | --- |
| ① 篡改绑定载荷 | 改 `command`、不重新封存 | `audit_verified=false` **且** `audit_status=PASS` ⇒ 两条是不同事实 |
| ② 换掉关键引用 | 输出制品置墓碑 | severity `FAIL` 的发现，`message` **点名**该制品 id |

### 5. 按压复核（AC-5，独立重跑）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `audit=None`（不产出） | **3 failed** |
| P-2 | `audit_verified` 硬编码 `True` | **1 failed**（篡改臂 `assert True is False`） |

两次按压后复原（重跑判据 3 passed）。

### 6. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| `mypy`（1140 源文件） | `Success: no issues found` |
| `ruff check` / `ruff format --check`（触及面） | 绿 |
| 规模门 | 1150 passed |
| `tests/e2e` | 252 passed, 13 skipped |
| **as-is m0**（`--profile m0 --keep-going`，冻结树、记录写完之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0；**5354 passed, 20 skipped**） |
| m0 计数差归因 | 基线 = EC-01 那轮（5350 passed / 20 skipped）⇒ **+4 passed**；收集数逐文件 diff：`+3` 新判据 + `+1` 源文件参数化 ⇒ **无未解释用例、skipped 未升** |
| 中间两处红（如实登记） | TS 夹具漏 4 字段（同轮补齐）；`framework/run_cursor_framework_evals` 的 `WinError 5` **既有偶发签名**（单跑 PASS + 独占重跑取终态行，未改 check） |

### 7. 未覆盖 / 一等边界

- 本复检只覆盖 **EC-02**；EC-03 / EC-04 **尚未收口**（状态以 GOAL frontmatter 为准）；
- **跨机器位级复现不在声明范围内**（口径只有「可重复配置」）；
- 读面新增字段是 digest / 状态 / 模板判词（点名制品 **id**，不含正文）；隐私清单已登记；
- **不得**声明项目安全（`R-M1` 未收口）；**不得**宣称投递语义为那四个字（**明确否认**）。

## 结论

**PASS**。审计在 run 路径产出并落库（既有 use case / 既有可审态谓词 / 既有 id 派生，**未建第二套**）、
读面按事实给读数（无审计则 honest unavailable）、主干两条独立路径一致、反证两向各自判红且点名、
按压两次判红并复原。**未覆盖范围与一等边界逐条明写，不外推。**
