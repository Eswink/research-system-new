---
id: PLAN-20260926-196
slug: record-face-is-covered-by-the-gate-receipt
title: GOAL-020 cycle 1（EC-02）：记录面门禁覆盖 —— 把「门禁结论是否覆盖记录面」变成机械事实
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-020
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-020 的 **EC-02**（记录面门禁覆盖；用户判词明写「本 EC 是本节最要紧的
    一条」）。授权沿用该 GOAL 的 `authorization.ref`：**前端 token 输入与携带**、
    **记录面门禁覆盖（方法论修复）**、**认证运维面**三条；push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）；默认 runtime 保持 **Fake**、
    默认 CI **离线**。**明文不做**：读面认证（GET/HEAD）、多租户 / organization scope /
    RBAC / 对象级授权（BOLA/BFLA）、调用方自报身份、新增依赖、把 token 写进任何地方、
    改认证的 401 响应形态、改 `Idempotency-Key` 语义。
    **本 PLAN 专属边界**：**不得**改 `tests/architecture/python/test_reproducibility_wording.py`
    的**判据 / 词表 / 扫描面**，也**不得**放宽其中任一条（`git diff` 取证该文件零改动）；
    **不得**改 m0 的**条数**（终态行必须仍是 `PASS: profile=m0; 23 deterministic checks`）；
    **不得**改 `.github/workflows/**` 的 job 结构；**不得**放宽任何阈值 / 门禁 / 放行面；
    **不得**新增策略面 allow；**不得宣称项目安全**（`R-M1` 未收口）。
    **本 PLAN 改的是「顺序 / 覆盖机制」**——即 EC-02 的原文要求。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-197-record-face-coverage-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-146-record-face-defect-is-timing-not-scan-surface.md
---

# PLAN-20260926-196 — 记录面门禁覆盖（EC-02）

## 目标

把 GOAL-019 发现的缺陷修成**机械保证**：**任何一次门禁结论都必须明确覆盖记录面**，
且这一点**不能靠人记得**。

**缺陷的真实形状（本 PLAN 的判据设计依据；建档日实测）**：记录面**并非从未被扫**——
`python/tests` 与 framework 组**已经**会扫 `.cursor/plans`。真正的缺陷是**时间性的**：
本地 SOP 把全量门跑在**记录写入之前**（GOAL-019 / PLAN-194 / RECHECK-195 / `MEM-20260926-145`
一致记载），于是**该次门禁结论对「记录面当时不存在的内容」不成立**。
⇒ 用户判词给的三选一里，**选项①「全量门包含记录面判据」在字面上已经成立，却不足以修复缺陷**；
必须选能**把结论与记录面内容状态绑定**的那条 ⇒ **选 ②/③ 的实质**：
一条**可按压的覆盖判据** + 一条**被该判据按小节绑定的 SOP 顺序条款**，
使「记录面在受判集合内」成为**每次门运行都被机器复核的事实**而非叙述。

## 验收条件

- [x] **AC-1（先红后绿 · 修前对照）**：`scratch/goal020-ec02-wp-a-red-before.py` 取证——
      临时向记录面写一条含禁用形态的记录 ⇒ `test_reproducibility_wording.py` **单独判红**
      （退出码 1）；逐字节删除 ⇒ **5 passed**。⇒ 记录面**本来就在**扫描面内，缺陷是**时刻**
      （门跑在记录写入之前）。**证据是判据行为，不是叙述。**
- [x] **AC-2（修后对照）**：走 **canonical 命令**跑**完整门**（`run_all_checks.py --profile m0
      --keep-going`）**在探针在树时** ⇒ 终态行 `FAILED: 3 check(s): python/format-check=1,
      python/tests=1, framework/validate=1`，其中 **`python/tests` 的红就是探针**
      （记录面违规 ⇒ 门判红）。**「复原 ⇒ 绿」的证据见「证据」节的终态全量门**。
- [x] **AC-3（判据零改动）**：`git diff --stat -- tests/architecture/python/test_reproducibility_wording.py`
      = **空**；`_SCAN_ROOTS` / `OVERCLAIM_PHRASES` / `NEGATION_MARKERS` 逐字未动。
- [x] **AC-4（m0 条数不变）**：机制落在 `tests/architecture/python/` ⇒ 属 `python/tests`
      既有 check 的收集面 ⇒ **不新增 check**。按压轮实测 `PASS [` = **21** 且 `FAILED` = **3**
      ⇒ **21 + 3 = 24 = 23 计数项 + 1 不计数项**（`release-assets-immutable`），
      与 `docs/architecture/LOCAL_GATE_PROTOCOL.md` 的既有口径一致；**终态绿行见证据节**。
- [x] **AC-5（扫描面清单）**：11 条（内容依赖 8 + 名称 / 存在性依赖 3）写在 GOAL-020
      「目标与退出标准」第 8 条 + `MEM-20260926-146`，**含未覆盖面**
      （`.cursor/memory/entries` 不在话术判据与凭据审计的记录面里）⇒ 收口 `W-14`。
- [x] **AC-6（新判据自身受判）**：`scratch/goal020-ec02-wp-c-press.py` 的按压矩阵
      **7/7 符合预期**（6 红 + 1 期望不红），逐字节 sha256 还原，终态复跑 `exit=0`。
      判据读**符号值**与**行为**（`_SCAN_ROOTS` / `_scan_files()` 实际产出 /
      `credential_audit.RECORDS_DIR` / 治理 `iter_cursor_text_files()` 实际产出 /
      runner 收集面常量）⇒ **不被文档字面量喂饱**。

## 实施清单

- [x] **WP-A（先红）：机制性复现修前缺陷** —— `scratch/goal020-ec02-wp-a-red-before.py`
      （只读 + 自复原；记录面 532 个文件的两轮快照 + 扫描面行为取证）。
- [x] **WP-B（修）：新增覆盖判据** `tests/architecture/python/test_record_face_is_covered_by_the_gate.py`
      （**215 行 / 8 例**，零超长函数）。**两处与原设计的偏差，如实登记**：
      ①**未**断言 `Makefile` 的 `validate-all` 命令行，**改绑 runner 自己的收集面常量**
      （`boundary_test` 的 AST 值 + `FRAMEWORK_SCRIPTS`）——理由：`Makefile` 目标只是
      runner 的一行包装，而**真正决定「判据是否在门里」的是 runner 的收集面**，绑后者机械性更强；
      ②**未**逐条覆盖 8 条内容依赖判据的扫描根，**实际覆盖 4 条最承重的**
      （话术判据=符号值+行为、凭据审计=符号值、治理=行为、runner 收集面）
      + **把未覆盖面显式断言**（`test_the_recorded_uncovered_ranges_are_still_accurate`）。
      其余判据（`validate_bundle` 版本串 / 链接、治理 plan-recheck-goal 结构、
      `test_pending_decisions_briefing`、`test_live_drift_sample_same_source`）在
      **清单**里逐条登记，但**未**各自建断言——**范围如实保留**，不宣称「8 条全部受判」。
- [x] **WP-C（后绿）：按压 + 复原** —— 7/7 符合预期；**报告实际判红集合**；
      并修好 P6 暴露的**真缺陷**（判据原按整篇文档判履行 ⇒ 改为**按小节**判，见 RECHECK-197 第二节）。
- [x] **WP-D（记录）** —— `LOCAL_GATE_PROTOCOL.md` 新增
      `### 记录面覆盖（GOAL-020 EC-02）` 节（canonical 顺序 + 被判据绑定的两个判据名）；
      `RECHECK-20260926-197`；`MEM-20260926-146`（+ `INDEX.md` 登记）；GOAL-020 回写。

## 证据

- **先红对照**：`scratch/goal020-ec02-wp-a-red-before.py` 输出——探针在树 ⇒ 判据 `exit=1`
  （`test_no_affirmative_fully_reproducible_claim`）；删除 ⇒ `5 passed`。
  **附带发现**：首版探针因自身含「禁止」二字被**否定标记豁免**而**没红**
  ⇒ 按压探针不得把自己的意图词写进去（已记入 RECHECK-197）。
- **后绿（完整门）**：`scratch/goal020-ec02-press-full-gate.log` —— 探针在树时
  `FAILED: 3 check(s): python/format-check=1, python/tests=1, framework/validate=1`；
  **另两条红是本轮真缺陷，已修**：`python/format-check`（新判据 1 处该折叠的 assert）
  + `framework/validate`（`MEM-146` 引用的 `RECHECK-197` 尚未存在、`MEM-146` 未入 INDEX）。
  ⇒ **定向套件当时全绿，全量门抓到两处真红**（承 GOAL-019 的同一教训）。
- **判据零改动**：`git diff --stat -- tests/architecture/python/test_reproducibility_wording.py` = 空。
- **按压矩阵**：`scratch/goal020-ec02-wp-c-press.py` —— 7/7 符合预期（6 红 + 1 期望不红），
  每轮报**实际判红集合**，全部 sha256 逐字节还原。
- **定向复跑**：`tests/architecture/python` + `tests/tooling` = **1187 passed**；
  规模门禁 `tests/tooling/test_python_source_limits.py` = **1034 passed**（新文件 215 行，无超长函数）。
- **未覆盖范围（如实保留）**：`W-14` 清单里 8 条内容依赖判据中**只有 4 条**各建了断言；
  `.cursor/memory/entries` 不在话术判据与凭据审计的记录面内（**已显式断言该事实**）；
  「每次门都跑在记录之后」仍是**人的顺序**，判据保证的是「记录面在受判集合内」。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 建档（GOAL-020 cycle 1 = EC-02）。已实测定位缺陷形态（时间性而非「没扫」）、m0 条数硬编码面（三处）、扫描面 11 条清单。 |
| 2026-09-26 | DONE | 四 WP 完成。**交付**：`test_record_face_is_covered_by_the_gate.py`（215 行 / 8 例）+ `LOCAL_GATE_PROTOCOL.md` 顺序节 + `RECHECK-197`（`PASS_WITH_WARNINGS`）+ `MEM-146`。**按压 7/7**；**判据零改动**；**m0 条数不变**（21+3=24 = 23+1）。**本轮被全量门抓到两处真红并已修**（format-check / 治理引用自洽）⇒ 再次证明定向全绿 ≠ 全量绿。`RECHECK-20260926-197` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain/API/schema 变化**：**无**（本 PLAN 不动产品代码；只新增判据 + 文档 + 记录）。
- **安全/凭据变化**：**无**（不涉及凭据面；不记 token）。
- **兼容性/迁移风险**：低——新增判据落在 `tests/**`，不改 m0 条数、不改既有判据、
  不改 workflow 结构。**主要风险已实测并覆盖**：新判据若绑定字面量而非符号 ⇒ 会变成
  「被文档喂饱」的恒真判据（本 PLAN 用符号值 + 行为取证 + 7 条按压规避）。
- **上游版本影响**：**无**（零依赖改动）。
- **下一项任务**：GOAL-020 cycle 2 = **EC-01**（前端 token 输入与携带 + 三态实跑）。
