---
id: PLAN-20261008-325
slug: goal-035-ec02-reproducibility-conclusion-on-the-run-path
title: GOAL-035 cycle 2（EC-02）：可复现结论在 run 路径产出并落读面 —— 复用既有域类型与 digest + 两向反证
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-326-goal-035-ec02-reproducibility-conclusion.md
memory_entries:
  - an-unpersisted-conclusion-does-not-exist-for-the-read-face
parent_goal: GOAL-20261008-035
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-035 的 **EC-02**（可复现可判定）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不建第二套**（复用既有
    `ReproducibilityAudit` 域类型、`build_reproducibility_audit` /
    `verify_reproducibility_audit` / `verify_audit_outputs`、既有 `save_audit/get_audit`
    存储面与既有 `is_auditable_state` 可审态口径）；**不改**审计的锚点清单与 digest 算法；
    **不得**把 WARNING 藏起来凑一个空发现列表；**不得**声明位级复现（口径只有「可重复配置」）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 EC-02 从「审计只在遗留 M12 链产出」推进到「**研究循环的 run 路径**上产出**可判定的
    可复现结论**，且结论落在**读面**」：① 实验跑到科学终态（`SUCCEEDED` / `NEGATIVE_RESULT`）
    时**封存审计**（既有 use case）并**随实验一起落库**（不是只在执行体内存里算一下）；
    ② 读面 `GET /runs/{run_id}/experiments` 逐条给出读数（`audit_digest` / `audit_status` /
    **重算**的 `audit_verified` / 逐条 `audit_findings`），没有审计就诚实标 unavailable；
    ③ 判据：结论可读且**独立重算**与读面一致（两条路径一致才算证据）；④ 反证两向：篡改
    绑定载荷 ⇒ 重算判红；换掉一个关键引用（输出制品置墓碑）⇒ 发现里**逐字点名**那个制品。
exit_criteria:
  - id: AC-1
    criterion: >-
      **审计在 run 路径产出并落库**：实验终态时封存 `ReproducibilityAudit`（既有
      `build_reproducibility_audit`）；`audit_id` 用既有派生口径（`derived_id("audit", …)`
      ⇒ 同一实验 ⇒ 同一身份）；**可审态沿用既有谓词** `is_auditable_state`（执行失败/超时/
      取消**不**审计，不另立一套）；不可审或缺 spec/result ⇒ 如实缺席（不把跑完的实验变失败）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/experiments
      tests/e2e/test_ec02_experiment_chain_offline.py -q` ⇒ 96 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **读面**：`ExperimentRunDto` 增加 `audit_digest` / `audit_status` / `audit_verified` /
      `audit_findings`（`AuditFindingDto{code,severity,message}`），`reproduction_available`
      由**事实**决定（不再是硬编码 False）；措辞按事实选：有审计谈读数、没有审计
      honest unavailable（既有断言 `reproduction_available is False` + note 含
      `unavailable` 在**无审计**的夹具上**仍然成立**）。OpenAPI 快照 + web 类型 +
      读面隐私清单同步。
    verify: >-
      `tests/api` + `tests/contracts` + `tests/observability` 全绿（133 passed）；
      `tools/gen_openapi.py` 重生成后快照判据绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **判据（新，主干）**：一次真实 run（`sort_analysis_v1`，实验走真容器）跑到 `SUCCEEDED`
      ⇒ 读面 `reproduction_available=true`、`audit_digest` 以 `sha256:` 开头、
      `audit_status=PASS`、`audit_verified=true`、**零 FAIL 发现**（WARNING 如实呈现，不隐藏）；
      并**独立重算**：从**存储**取回审计对象自行 `compute_audit_digest()`，与读面读数逐条一致。
    verify: >-
      `tests/e2e/test_reproducibility_conclusion_on_the_run_path.py::
      test_the_run_path_records_a_verifiable_reproducibility_conclusion` 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证两向**：① **篡改绑定载荷**（改一个被绑定字段、不重新封存）⇒ 读面
      `audit_verified=false`，而 `audit_status` 仍 `PASS`（两条是**不同**的事实，分开验）；
      ② **换掉一个关键引用**（审计绑定的输出制品置墓碑）⇒ 出现 severity `FAIL` 的发现，且
      `message` **逐字点名**该制品 id（code ∈ {ARTIFACT_MISSING, ARTIFACT_CORRUPTED,
      ARTIFACT_DIGEST_DRIFT}）。
    verify: >-
      同文件另两例绿（`test_tampering_the_bound_payload_is_caught_by_digest_recomputation`
      / `test_swapping_an_output_artifact_is_named_in_the_findings`）。
    status: PASS
  - id: AC-5
    criterion: >-
      **按压**：摘掉审计产出 ⇒ 三例全红；把 `audit_verified` 改成硬编码 `True` ⇒ 篡改臂判红
      （证明「重算」是载重的，不是回读一个标记）。按压后逐字节复原。
    verify: >-
      实测：P-1（不产出审计）⇒ **3 failed**；P-2（`audit_verified=True` 硬编码）⇒ **1 failed**
      （`assert True is False`）；`RESTORED`。
    status: PASS
---

# PLAN-20261008-325 — GOAL-035 cycle 2（EC-02）：可复现结论进读面

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 审计在 run 路径产出 + 落库（既有 use case / 既有可审态口径 / 既有 id 派生） | PASS |
| AC-2 | 读面四字段 + 措辞按事实 + 声明面三处同步 | PASS |
| AC-3 | 主干：结论可读 + **独立重算**一致 | PASS |
| AC-4 | 反证两向（篡改载荷 / 换掉引用并点名） | PASS |
| AC-5 | 按压两次判红且复原 | PASS |

## 实施清单

- [x] `packages/application/experiments/execute.py`：`_audit_for`（终态封存；**复用**
      `build_reproducibility_audit` + `is_auditable_state` + `derived_id("audit", …)`）；
      `ExperimentExecutionOutcome.audit`。
- [x] `services/api/experiment_support.py`：`_persist_run` 把审计**随实验**落库（读面读存储）。
- [x] `services/api/dto/inspection.py`：`AuditFindingDto` + `ExperimentRunDto` 四字段。
- [x] `services/api/routers/experiments.py`：`_apply_audit`（重算 `audit_verified`）、
      `_output_findings`（跨核对制品存储，点名制品）、`reproduction_note(experiments)`（按事实选措辞）。
- [x] 声明面：OpenAPI 快照重生成 + `apps/web/src/api/types.ts` + 读面隐私清单登记更新。
- [x] 判据：`tests/e2e/test_reproducibility_conclusion_on_the_run_path.py`（3 例）。

## 证据

### 勘察读数（实测）

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | 审计 use case 存在且完备 | `build_reproducibility_audit(run: ExperimentRun, …)` 绑定 command/code/env/seed/资源/镜像/前后快照/输出 digest/指标 digest；`audit_digest` 由确定性载荷封存 |
| 2 | 复核面两件 | `verify_reproducibility_audit`（重算 digest，返回 bool）与 `verify_audit_outputs`（跨核对制品存储，返回**点名**的结构化发现） |
| 3 | 存储存在 | `ExperimentStore.save_audit/get_audit`（两适配器 + `reproducibility_audits` 表） |
| 4 | **run 路径零调用**（实测） | 产品侧唯一调用点是 `m12_reference/clean_run_stages.py`（遗留链）+ `m12_reference/persistence.py` 的落库 |
| 5 | 读面此前硬编码 | `ExperimentRunDto.reproduction_available` 恒 `False`（`routers/experiments.py`）+ `REPRODUCTION_NOTE` 明说「不在控制面板持久化边界内」 |
| 6 | 可审态已有谓词 | `is_auditable_state`：只有 `SUCCEEDED` / `NEGATIVE_RESULT` 入审计（**首版我自写门 ⇒ 与既有口径分叉；已改为复用**） |
| 7 | 落库点已有 | `_persist_run` 已把 `ExperimentRun` 存进实验存储（审计只差一行） |
| 8 | 域口径里有 WARNING | `code_digest` 未单独 pin ⇒ `CODE_DIGEST_NOT_PINNED`（WARNING，「诚实标注而非缺陷」）⇒ 判据断言「零 FAIL」而非「空列表」 |

### 判据（新，3 例）与反证逐字

```
tests/e2e/test_reproducibility_conclusion_on_the_run_path.py ... [100%]  3 passed
```

| 臂 | 改动 | 读面读数 |
| --- | --- | --- |
| ③ 反证①：篡改载荷 | 改 `command` 且不重新封存 | `audit_verified=false`、`audit_status=PASS`（**两条不同的事实**）、`audit_digest` 不变 |
| ④ 反证②：换掉引用 | 输出制品置墓碑 | 发现含 severity `FAIL`，`message` 点名该制品 id，code ∈ {ARTIFACT_MISSING, ARTIFACT_CORRUPTED, ARTIFACT_DIGEST_DRIFT} |

### 按压（AC-5）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | 不产出审计（`audit=None`） | **3 failed** ⇒ `RESTORED` |
| P-2 | `audit_verified` 硬编码 `True`（不重算） | **1 failed**（`assert True is False`，篡改臂）⇒ `RESTORED` |

### 门（本 PLAN 触及面）

| 门 | 读数 |
| --- | --- |
| `tests/application/experiments` + `tests/e2e/test_ec02_experiment_chain_offline.py` | 96 passed |
| `tests/api` + `tests/contracts` + 应用层 | 1330 passed, 76 skipped |
| `tests/e2e`（全量，含真容器那几例） | 252 passed, 13 skipped |
| `tests/observability`（含隐私金丝雀 + 白名单派生） | 133 passed, 2 skipped |
| `mypy`（1140 源文件） / `ruff check` / `ruff format --check` | 0 错 / 绿 / 绿（首跑各 1 条：`no-any-return` + 两文件待格式化 ⇒ 已修） |
| 规模门（450 / 50 行） | 1150 passed |
| **as-is m0**（冻结树，**全部记录写入之后**） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / pytest **5354 passed, 20 skipped**）|
| m0 计数差归因（逐文件 diff，**不是印象**） | 收集数 **+4** 全部分解：`+3` 新判据文件 + `+1` `test_python_source_limits`（按源文件参数化 × 新增 1 个 `.py`）；**skipped 未升** |
| 首跑两处红（如实登记） | ① **TS 夹具漏字段**：`apps/web/tests/e2e/apiFixtures.ts` 的 `ExperimentRunDto` 字面量缺 4 个新字段 ⇒ `typescript/typecheck` + `web-typecheck` + `web-build` 三条红 ⇒ 补齐（**同轮修**）；② `framework/run_cursor_framework_evals` **`WinError 5` on `evolution_state.json.tmp`**（既有偶发签名）⇒ **单跑取证 PASS** + 独占重跑取终态行（**未改 check、未查产品代码**） |

## 影响报告

- **Domain / API / schema 变化**：API **有**（`ExperimentRunDto` 四个新字段 + 新 `AuditFindingDto`；
  OpenAPI 快照与 web 类型已同步）。**Domain 未改**（复用 `ReproducibilityAudit` / `AuditFinding`
  原样；未动锚点清单与 digest 算法）。协议 / 合约 schema 未改。
- **安全 / 凭据变化**：无新增凭据面。读面新增字段只有 digest / 状态 / 判词（点名制品 **id**，
  不含制品正文）；隐私清单已按此更新并写明一等边界。
- **兼容性 / 迁移风险**：无迁移（`reproducibility_audits` 表早已存在）。既有断言
  （`reproduction_available is False` + note 含 `unavailable`）在**无审计**夹具上仍成立
  （实测 `tests/api/test_experiments_api.py` 绿）。
- **观测隐私**：新增读面字段均为 digest / 枚举 / 模板句；不新增日志或遥测出口。
- **上游版本影响**：无。
- **下一项任务**：EC-03（覆盖充分 + 评审联动：`review_score` 在产品路径被赋值 + `REVIEW_SCORE` 三态）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 勘察定稿：审计实现完备、存储存在、**run 路径零调用**、读面硬编码 False。设计：复用既有 use case + 既有可审态谓词 + 既有 id 派生；落库点用既有 `_persist_run`。 |
| 2026-10-08 | DONE | 五条 AC 全 PASS：审计在 run 路径产出并落库、读面四字段（措辞按事实）、独立重算一致、两向反证（篡改载荷 / 换掉引用并点名）、按压 3 failed + 1 failed 且复原。**首版自写可审态门与既有 `is_auditable_state` 分叉 ⇒ 同轮改为复用**；断言从「空发现列表」改为「零 FAIL」（域口径里 WARNING 是诚实标注）。`RECHECK-20261008-326` 独立复检。 |
