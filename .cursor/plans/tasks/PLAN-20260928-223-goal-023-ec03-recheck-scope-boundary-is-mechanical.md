---
id: PLAN-20260928-223
slug: goal-023-ec03-recheck-scope-boundary-is-mechanical
title: GOAL-023 cycle 3（EC-03）：受判射程边界机械化 —— 新增判据把「起点 + 四条历史 + 计数」从散文变成机械事实（含两向反证）
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-023
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-023 的 **EC-03**（受判射程边界机械化，收 `RECHECK-20260928-218` 的 `W-1`）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「复检资产归档化 +
    `tools/` 受判面以新增判据形式收口 + **受判射程边界机械化**」+ 修被新判据证明的缺陷
    + 文档同源更新；**不改安全策略、不放宽任何判据**；push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）；默认 runtime 保持 **Fake**、
    默认 CI **离线**、默认门**一律离线**。
    **本 PLAN 专属边界（形式硬约束）**：**必须是「新增判据」** ——
    **不得修改** `tests/architecture/python/test_declared_recheck_paths_have_evidence.py`
    （只**读**它的公开面）；**不得**回填 / 改写任何历史 RECHECK（按压是临时且**逐字节复原**的）；
    **不得**新增依赖；**不得**改 `PRODUCT_ROOTS` / m0 条数 / 作业结构。
exit_criteria:
  - id: AC-1
    criterion: >-
      新判据在树、落在 m0 的 `python/tests` 收集面内 ⇒ m0 条数**仍为 23**；
      且**只读**既有判据的公开面（`CUTOFF` / `CLOSEOUT_SLUG_SUFFIX` / `MIN_DECLARED_PATHS` /
      `is_obligated` / `closeout_records`），既有那条判据**逐字节未改**
    status: PASS
  - id: AC-2
    criterion: >-
      判据输出并断言：**受判起点**（逐字 `2026-09-28`）、**射程外清单恰好四条**
      （`goal-018` / `019` / `020` / `021` 的 `closeout-recheck`，**逐条点名**）、
      **射程内计数** ≥ 1、两集**互斥**、扫描面两侧**都非空**
    status: PASS
  - id: AC-3
    criterion: >-
      **反证两向**（hermetic，`tmp_path`）：① 新收口复检被**回填到起点之前** ⇒ 判红
      （防 **backdate 逃逸**）；② 历史记录被**改成在射程内** ⇒ 判红（防**回填历史**）
    status: PASS
  - id: AC-4
    criterion: >-
      **仓库级按压**（真实记录、Edit 做、`raw sha256` 逐字节复原）：把 `RECHECK-218` 回填到
      `2026-09-27` ⇒ 判据判红；把 `RECHECK-210` 改成 `2026-09-28` ⇒ 判据判红
      （并实测**既有那条判据也同时判红** ⇒ 两条判据结论一致）
    status: PASS
  - id: AC-5
    criterion: >-
      **登记该判据不判**「射程内记录的实质质量」，**只判边界本身** —— 以**行为**证明
      （质量全坏的记录只要边界对就不判红），不是靠一句散文
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-224-goal-023-ec03-recheck-scope-boundary.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-159-mechanizing-a-scope-claim-needs-two-way-reverse-proof.md
---

# PLAN-20260928-223 — GOAL-023 cycle 3（EC-03）：受判射程边界机械化

**主题**：`RECHECK-20260928-218` 的 **`W-1`** 说「EC-02 判据的受判起点 = 建档日，**四条历史收口复检
仍在射程外**」—— 那当时只是**散文**。散文不会自己失效，失效的是**它描述的事实**：
一条新记录被**回填**、或一条历史记录被**改写**，边界就静默改变了，而没有任何东西会说话。
本 PLAN 用**新增判据**把边界钉成**可复核事实**，并给**两个方向**各配一条反证。

## 验收条件

| # | 条件 | 状态 |
| --- | --- | --- |
| AC-1 | 新增判据在树、m0 仍 23、既有判据逐字节未改 | **PASS** |
| AC-2 | 起点逐字 / 射程外恰好四条 / 射程内计数 ≥ 1 / 互斥 / 两侧非空 | **PASS** |
| AC-3 | hermetic 两向反证（backdate 逃逸 / 回填历史） | **PASS** |
| AC-4 | 仓库级按压两向 + `raw sha256` 逐字节复原；与既有判据结论一致 | **PASS** |
| AC-5 | 「只判边界不判质量」以**行为**证明 | **PASS** |

## 实施清单

- [x] WP1（`86cffaa`）：`tests/architecture/python/test_recheck_scope_boundary_is_mechanical.py`（**6 例**）。
- [x] WP2：hermetic 两向反证 + 仓库级两向按压与逐字节复原。
- [x] WP3：记录（本 PLAN / `RECHECK-20260928-224` / `MEM-20260928-159` / GOAL 回写）+ m0 + push。

## 证据

**边界事实（实测，非叙述）**

| 观察 | 结果 |
| --- | --- |
| 受判起点 `CUTOFF`（读既有判据） | `2026-09-28`（与绑定值逐字一致） |
| slug 约定 / 路数下界 | `closeout-recheck` / `2`（与绑定值一致） |
| 扫描面 | **5** 条（`slug` 以 `closeout-recheck` 结尾） |
| **射程内** | **1** 条：`RECHECK-20260928-218-goal-022-closeout-recheck.md` |
| **射程外** | **4** 条：`RECHECK-20260926-189-goal-018-…` / `-195-goal-019-…` / `-200-goal-020-…` / `RECHECK-20260927-210-goal-021-…` |

**判据自查**

| 观察 | 结果 |
| --- | --- |
| `ruff check` / `ruff format --check` / `mypy` | **全绿**（`mypy`：`Success: no issues found`） |
| 规模 | **192 行**；**无**超 50 行函数 |
| 定向套件 | 本判据 **6 passed**；与既有判据合跑 **15 passed** |
| 既有判据 | `git diff HEAD -- tests/architecture/python/test_declared_recheck_paths_have_evidence.py` **为空**（逐字节未改） |

**hermetic 反证两向（在 `tmp_path` 上造收口复检夹具）**

| 方向 | 夹具 | 判据结果 |
| --- | --- | --- |
| 基线 | 4 条历史（`2026-09-26`）+ 1 条新记录（`2026-09-28`） | `boundary_problems == []` |
| ① backdate 逃逸 | 把那条新记录改成 `2026-09-27` | **判红**，失败消息**点名**该文件 |
| ② 回填历史 | 把 `RECHECK-…-189-goal-018-…` 改成 `2026-09-28` | **判红**，失败消息**点名**该文件 |
| 质量无关 | 质量全坏（无 `verify_paths`）但边界正确 | **不判红** ⇒ 判据不越权 |

**仓库级按压（真实记录；按压 / 复原一律用 Edit 工具）**

| # | 按压对象与内容 | 判据结果 | 复原（raw `sha256`） |
| --- | --- | --- | --- |
| ① | `RECHECK-20260928-218-goal-022-closeout-recheck.md`：`created_at` `2026-09-28` → `2026-09-27` | **`2 failed, 4 passed`**（射程外清单多出一条 + `scan_face_covers_both_sides`） | 回到 `b46e551ffd4f83071c29cd5f5ce13dc11f1aae8e03129cea91580e2b9736edd9` |
| ② | `RECHECK-20260927-210-goal-021-closeout-recheck.md`：`created_at` `2026-09-27` → `2026-09-28` | **`1 failed, 5 passed`**（射程外清单少了一条） | 回到 `b459e3a36dd1671fbd6bbb203dc152a25d5feecccd0ed4a35237eacce51a8ab7` |

**补充观察（两条判据一致）**：在按压 ② 的状态下，**既有那条判据也同时判红**
（`test_no_obligated_closeout_recheck_has_a_declaration_gap`：被回填的历史记录没有
`verify_paths`）⇒ 边界判据与质量判据在「回填」这一形态上**结论一致**，不是各说各话。
复原后两条判据合跑 **15 passed**；`git status --short .cursor/plans/rechecks/` **为空**。

**as-is 本机 m0（记录写入之后、独占、仓库 `.venv`、DSN 固化）**

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`） |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外） |
| `FAILED` / `ERROR` | **零** |
| 日志与时刻 | `scratch/goal023-c3-m0.log`，文件时刻**晚于**本 PLAN 与 `RECHECK-224` 的写入时刻 ⇒ 门在记录之后 |
| 治理 | `validate.py` = `Cursor 治理验证通过` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档；先实测边界事实（扫描面 5 / 射程内 1 / 射程外 4），再写判据。 |
| 2026-09-28 | DONE | 五条验收全部成立且有实跑证据；`RECHECK-20260928-224` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain / API / schema**：**零改动**。
- **安全 / 凭据**：**零改动**；未新增任何 token 字面量。
- **兼容性 / 迁移风险**：**无**。新增判据只读既有判据的公开面与仓库记录；
  既有那条判据**逐字节未改**；历史 RECHECK **零回填**（两次按压均逐字节复原）。
- **上游版本影响**：**零依赖改动**。
- **未覆盖范围（原样保留）**：读面未认证 / 多租户与 RBAC 未做 / BOLA·BFLA 未做 /
  部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
- **下一项任务**：GOAL-023 EC-04（自举收口复检 + 残余登记）。
