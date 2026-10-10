---
id: PLAN-20261010-369
slug: goal-043-ec01-04-closeout-assets-run-own-assertions
title: GOAL-20261010-043 cycle 1（EC-01…EC-04）：加载面修正 + 崩溃面修正（结构判据）+ 机器判据钉住形态
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-370-goal-043-ec01-04-closeout-assets.md
memory_entries:
  - closeout-assets-must-run-their-own-assertions
parent_goal: GOAL-20261010-043
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-043 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不重写**任何历史 GOAL 的 `latest_recheck`
    结论；受判面**只许等价或更宽**；**复检资产必须可执行**（崩了不是判负）；
    **改既有判据必须走自证清单**（`MEM-20261009-210`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让收口复检资产**自身**可信：① 勘察读数（声明/实载对拍 + 自有断言 0 命中 + 崩溃实测）
    → ② 三处加载面修正（`verify_goal0{38,39,40}` 改为加载**各自**的断言集）
    → ③ 崩溃面修正（`goal040_closeout_assertions.py` 的**文本 index** 判据改 **AST 结构判据**，
    受判面等价）→ ④ 机器判据钉住形态（**声明==实载** + **被点名断言集可执行** +
    **射程分区不漏项**；**合成反例必红**）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿**：六处验证器「声明的 `ASSERTIONS`」与「`_load_assertions` 实载」逐条对拍；
      实测自有断言名在判词里 **0** 命中；直接调 `goal040_closeout_assertions` ⇒ **崩溃**
      （`ValueError: substring not found`，点名文本锚点与真实签名的差）。
    verify: >-
      `rg` 对拍 + `verify_goal040_closeout.py --verdict-only | grep -c <自有断言名>` = 0 +
      直接调用抛 `ValueError`。
    status: PASS
  - id: AC-2
    criterion: >-
      **加载面修正（三处）**：改为加载各自的断言集；三处**跑完不崩**且**自有断言名真的
      出现在判词里**。
      **建档子句如实修正**：初版「判词数只增不减」**不成立且不该成立**（换加载面必然改变
      条数）⇒ 改为「**跑自己的**断言」。
    verify: >-
      三个验证器各跑一次 ⇒ 60 / 60 / 59 PASS、**0 FAIL**，自有断言名命中 > 0。
    status: PASS
  - id: AC-3
    criterion: >-
      **崩溃面修正**：按文本 index 匹配调用签名的判据改 **AST 结构判据**（按**被调函数名**
      取行号，与实参无关）⇒ 签名演进不再打断它；受判面**等价**（仍要求两者都在场：任一缺 ⇒ 判红）。
    verify: >-
      直接调 `assertion_verdicts` ⇒ 跑完不崩；把结构判据改回文本匹配 ⇒ 判据必红（P-2）。
    status: PASS
  - id: AC-4
    criterion: >-
      **机器判据钉住形态**：新增 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`
      —— 声明==实载（AST 读；两种世代形态都接）+ 被点名断言集**可执行** + **射程分区不漏项**
      （在射程 / 逐条登记为旧一代，理由非空、不得重叠）。
      **两向**：合成「声明 A 实载 B」与「断言集抛异常」两例 ⇒ 判据**必须报红**；真实树 ⇒ 绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling -q` ⇒ **1422 passed**；
      新增判据 **7 passed**；两向反证 `P-1`（复现历史加载缺陷）/`P-2`（复现崩溃缺陷）**全红**。
    status: PASS
---

# PLAN-20261010-369 — GOAL-20261010-043 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-043`（MAINLINE 程序表**序 11**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（声明/实载对拍 + 0 命中 + 崩溃实测） | PASS |
| AC-2 | 加载面修正（三处；子句如实修正） | PASS |
| AC-3 | 崩溃面修正（AST 结构判据） | PASS |
| AC-4 | 机器判据钉住形态（两向反证） | PASS |

## 实施清单

- [x] WP-1 勘察读数（对拍 + 0 命中 + 崩溃类型与消息）
- [x] WP-2 三处加载面修正（`verify_goal0{38,39,40}` 加载各自的断言集）
- [x] WP-3 崩溃面修正（`_dispatch_precedes_conclusion_face` + `_first_call_line`，AST 按被调名取行号）
- [x] WP-4 机器判据（新判据文件；含射程分区与两向反例）
- [x] WP-5 两向反证（P-1/P-2 全红 + 二进制复原 raw `sha256` 一致 + 归档进树）
- [x] WP-6 记录 + 门（四道门 / `tests/tooling` 1422 passed）

## 证据

| 门 | 读数 |
| --- | --- |
| 修正前（对拍） | `038`/`039`/`040` **声明 ≠ 实载**（都实载 `goal037_closeout_assertions.py`） |
| 修正前（自有断言） | `verify_goal040_closeout.py` 的判词里其自有断言名命中 **0** |
| 修正前（崩溃） | 直接调 `goal040_closeout_assertions.assertion_verdicts` ⇒ **`ValueError: substring not found`** |
| 修正后（三处） | `verify_goal038` **60 PASS / 0 FAIL**；`verify_goal039` **60 PASS / 0 FAIL**；`verify_goal040` **59 PASS / 0 FAIL**（自有断言名命中 > 0） |
| 新判据 | `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` **7 passed** |
| `tests/tooling` 全量 | **1422 passed** |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict 对本轮改动文件**全绿** |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0）|
| 两向反证 | `P-1` / `P-2` **全红**；二进制复原 raw `sha256` **逐字节相同**；归档 `GOAL-20261010-043-press-two-way.txt`（110 B / `CR=0`） |

### 判词数变化（**如实登记，不淡化**）

| 验证器 | 修正前判词数 | 修正后判词数 | 说明 |
| --- | --- | --- | --- |
| `verify_goal040` | 73（加载 037 的 34 条自有断言集） | **59**（加载自己的 20 条） | **变少** —— 换加载面必然改变条数；037 的 34 条仍由 **037 自己的验证器**运行 ⇒ 组合覆盖不丢失 |

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词 | `numstat` |
| --- | --- | --- | --- |
| `tools/goal040_closeout_assertions.py` | 文本 index 判据 ⇒ **AST 结构判据**；新增两个 AST 助手 | **等价**（仍要求「分派先于结论面」且两者都在场） | 见 RECHECK |
| `tools/verify_goal0{38,39,40}_closeout.py` | `_load_assertions` 的加载面 + 注释 | **等价**（不改判据，只改**加载谁**） | 见 RECHECK |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | **新增**文件 | — | 新增 |

## 影响报告

- **Domain / API / schema 变化**：零（只动 `tools/` 复检资产与 `tests/tooling` 判据）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无（历史 GOAL 的终态与结论**未触碰**）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 三处加载面 + 崩溃面（AST）修正落地；新判据 7 passed；两向反证 P-1/P-2 全红。 |
| 2026-10-10 | DONE | 四道门 + `tests/tooling` 1422 passed；`RECHECK-20261010-370` 独立复检。 |
