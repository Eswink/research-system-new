---
id: PLAN-20260929-237
slug: goal-025-ec01-response-header-face-in-scan
title: GOAL-025 cycle 1（EC-01）：响应头面进扫描 —— 头清单逐条分类 + 零命中 + 反证红 + 复原绿 + 非空取证
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-025
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-025 的 **EC-01**（收 GOAL-024 的残余 `G24-2`）。授权沿用该 GOAL 的
    `authorization.ref`：范围 = 「**新增判据**（一律落 `tests/**`，落在既有 `python/tests`
    收集面内 ⇒ m0 条数仍 `23`）」+「**测试侧夹具 / 探针**」+「修**被新判据证明为真缺陷**的问题
    （**只允许收紧**：清洗回显内容 / 关闭泄漏通道）」；push-to-main-for-CI 口径（**只推 main、
    不 force**、不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**判据与夹具文件，**不修改**任何既有判据 / 夹具 / 门禁 /
    阈值 / 放行面（点名：`test_privacy_read_face_canary.py`、`read_face_route_registry.py`、
    `read_face_canary_support.py`、`content_canary_support.py`、`test_privacy_canary.py`、
    `test_privacy_exit_census.py`、`test_privacy_content_canary_end_to_end.py`、
    `test_privacy_boundary_clauses_are_pinned.py`、三道记录面判据、多路证据判据、射程边界判据、
    `test_tooling_scripts_meet_product_gates.py`、`tests/egress_guard.py`）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；**零**新依赖；**全离线**（无真实出网）；
    金丝雀一律**测试内构造的合成串**；**不得**把真实 prompt / token / 凭据写进任何地方；
    **不得**用测试自选的**标识符**（如 `artifact_id`）携带金丝雀去制造头面假红；
    **不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **头清单逐条显式分类且写在判据源码里（承 MEM-158）**：新增判据把读面**响应头**纳入
      扫描面，头部清单是一个**分区**（逐条显式、理由非空、无第三种状态），判定为
      **受判** / **豁免（机械理由 + 值形态断言）** / **登记为不发射（出现即判红）**；
      **运行期观测到的未分类头 ⇒ 判红**；登记与运行期观测**两向**核对（陈旧登记亦判红）。
    status: PASS
  - id: AC-2
    criterion: >-
      **零命中 + 非空取证（承 MEM-156）**：沿默认离线链注入合成内容金丝雀后，**全部**
      观测到的响应头**零命中**；且**受判头 ≥ 1 且本次运行中真的被观测到**（逐条观测计数
      非空），否则判红 —— **不得**空转。
    status: PASS
  - id: AC-3
    criterion: >-
      **两向反证 + 按压 + 逐字节复原（承 MEM-159 / MEM-152）**：① 把金丝雀塞进一个**受判头**
      （真实应用上的按压路由）⇒ 判据**判红**且失败消息**点名头名 + 路由 + 金丝雀 kind**；
      ② 出现**未分类**的新头 / **登记为不发射**的头被观测到 ⇒ 各自判红并点名；
      ③ 内容放进 **canonical**（正文）⇒ **不**判红（不该红时不红）；
      ④ 按压后**逐字节复原**（raw `sha256`，**二进制读写**）⇒ 复绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **终态**：四道门（`ruff format --check` / `ruff check` / 规模 450 行 · 50 行 / `mypy`）全绿；
      既有隐私判据**逐字节未改**且与本轮新判据合跑全绿；as-is 本机 m0 =
      `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**）；治理 `validate.py` 绿；
      CI 台账到终态（八 job + CodeQL + `run_attempt`）。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-238-goal-025-ec01-response-header-face-in-scan.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-163-response-headers-are-a-separate-judged-face.md
---

# PLAN-20260929-237 — GOAL-025 cycle 1（EC-01）：响应头面进扫描

**动因**：GOAL-024 的读面判据（`test_privacy_read_face_canary.py`）通过
`read_face_canary_support.response_text()` **只读响应体**；响应头**字面上不在扫描面**，
收口时被如实登记为残余 `G24-2`。而本仓读面**确实**在发 `Content-Disposition`
（`filename` 取自 `artifact.id`）与 `ETag`（取自 `artifact.digest` / `record.revision`）
——**回显类头**是真实存在的，不是假想面。本 PLAN 把这一面纳入受判面，并证明「内容金丝雀在
**全部**响应头上零命中」。

## 验收条件

见 frontmatter `AC-1`…`AC-4`（全部 PASS，证据见下）。

## 实施清单

- [x] WP1：`tests/observability/read_face_header_inventory.py`（**217 行**）—— 头清单分区
      （受判 2 / 豁免 3 / 登记为不发射 1）+ 七条纯函数自审 + 头值扫描纯函数。
- [x] WP2：`tests/observability/test_privacy_read_face_headers.py`（**245 行 / 13 例**）——
      逐路由实取头 + 分区自审 + 受判头非空取证 + 正控制（`Content-Disposition.filename`
      逐字符等于净化后的 `artifact.id`、`ETag` 等于 `artifact.digest`）+ 两向反证 +
      真实应用按压 + 逐字节复原 + 标识符边界钉住。
- [x] WP3：`RECHECK-20260929-238`（独立复检，`PASS_WITH_WARNINGS`）+ 工程记忆
      `MEM-20260929-163`。
- [x] WP4：记录（本 PLAN / GOAL 回写）+ 四道门 + as-is m0 + push + CI 台账终态。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 新判据 | `test_privacy_read_face_headers.py` **13 passed** |
| 实取规模 | **65** 条读路由取到响应（下界 40）；头部观测计数 `content-type` 65 / `content-length` 65 / `etag` **4** / `content-disposition` **1** / `x-content-type-options` **1** / `last-modified` **0** |
| 受判头非空取证 | `content-disposition` 与 `etag` 逐条计数 > 0 ⇒ 受判面**非空**（承 MEM-156） |
| 零命中 | 全部 65 条路由的全部头逐值扫描 ⇒ **零违规** |
| 正控制 | `Content-Disposition` 实测 = `inline; filename="canary-artifact_<run>"`（`filename` 逐字符等于净化后的 `artifact.id`；处置词由 `media_type` 决定 ⇒ 断言只钉住 `inline` / `attachment` 两者之一）；`ETag` 逐字符等于 `f'"{meta.digest}"'` |
| 按压（源码级，先红后绿） | P1 删 `content-disposition` 规则 ⇒ `未分类的响应头:content-disposition` + `受判面低于下界:1 < 2`；P2 抽空 `etag` 理由 ⇒ `理由为空:etag`；P3 `last-modified` 改判 `EXEMPT` ⇒ `豁免头缺少机械值形态:last-modified` + `登记陈旧(本轮未观测到):last-modified` |
| 逐字节复原（raw `sha256`） | 三处按压后均回到 `9e9a51ea65603f03cc76d4ea050bdd5555d917138ed9cca41d2bbd37c4e0babd`（`MATCHES_BASELINE True`），判据复绿 13 passed；证据 `scratch/goal025-ec01-press-matrix.log`（**二进制写盘**） |
| 两向反证 | 受判头带金丝雀（真实应用按压路由）⇒ 判红点名**路由 + `etag` + `artifactbody`**；未分类新头 ⇒ 判红点名；登记为不发射的头出现 ⇒ 判红点名；内容进 canonical / 正文 ⇒ **头面零命中**（不该红时不红） |
| 四道门 | `ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模 **217 / 245 行**，规模门定向跑 **2 passed** |
| 既有判据未改 | `git diff --stat -- tests/observability/` 为空；`tests/observability/` 全目录 **113 passed, 1 skipped**（GOAL-024 cycle 4 收口时 100 passed + 1 skipped ⇒ **+13** = 本轮新判据） |
| m0 / 治理 / CI | 见 GOAL 迭代日志与 CI 台账（**记录写入之后**才跑；终态行 `PASS: profile=m0; 23 deterministic checks`） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | 建档（GOAL-025 cycle 1，EC-01）。 |
| 2026-09-29 | DONE | 两个新判据文件进树（13 例全绿）、四道门绿、三处源码按压先红后绿且 raw `sha256` 逐字节复原、RECHECK-238 `PASS_WITH_WARNINGS`、MEM-163 沉淀。 |

## 影响报告

- **Domain/API/schema**：无（`tests/**` + 记录）。
- **安全/凭据**：无凭据改动；新判据全离线、金丝雀为测试内合成串。
- **兼容性/迁移风险**：无（纯新增判据文件；既有判据逐字节未改，m0 条数仍 `23`）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-025 cycle 2（EC-02：正控制矩阵与未注入面的判定化）。
