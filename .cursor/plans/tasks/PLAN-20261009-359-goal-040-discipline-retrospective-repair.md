---
id: PLAN-20261009-359
slug: goal-040-discipline-retrospective-repair
title: GOAL-040 纪律回溯修复（独立 cycle）：三个既有 e2e 判据的谓词回退（强度下降）复核 + 显式形态恢复部署（先于 MAINLINE 序 9）
status: DONE
created_at: 2026-10-09
updated_at: 2026-10-09
latest_recheck: .cursor/plans/rechecks/RECHECK-20261009-360-goal-040-discipline-retrospective-repair.md
memory_entries:
  - narrowing-an-existing-predicate-must-be-declared
parent_goal: GOAL-20261008-040
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-09 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本次触发的**第一件事**是
    **纪律回溯修复**（独立 cycle，先于序 9）。授权原文要点：**禁止**凭提示词的描述下结论，
    必须**实跑取值**（以 `49b2c7d` = GOAL-040 建档提交、尚未含实施为对照面）；
    逐条判定越界与否；**恢复强度**（助手改**显式声明形态**，不得保留「至少一轮」式回退）；
    沉淀 MEM 并写进本 GOAL 及后续 GOAL 的 `fix_policy` 自证清单；写入 MAINLINE 修订记录
    （只追加一行）。**关键区分**：「权限下放」= 可以决定，**不等于**可以放宽判据。
    **本 PLAN 专属边界**：**不改产品代码**（本轮只动判据与记录）；**不删任何既有断言**
    （只增不减；改动逐条给 `git diff --numstat` 删除行读数）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。驱动 = client-goal、owner = root-agent。
objective: >-
    把 GOAL-20261008-040 在**同轮同步集之外**对三个既有 e2e 判据做的谓词回退（「恰好
    两轮」→「至少一轮」的容错回退、以及一条结论面用例被改成失败面后**结论面在 e2e 上
    失去覆盖**）**复核、登记、并在判据强度上恢复**：① **两树实跑复核**（`49b2c7d`
    干净 checkout vs 当前 HEAD，逐场景取值，不凭描述下结论）；② **逐条判定越界**
    （读 GOAL-040 的 `fix_policy` 同步集清单，给 `git diff --numstat` 删除行读数，
    逐条比对谓词）；③ **恢复受判强度**（助手改**显式声明形态**：成功面断言**恰好两轮**、
    失败面断言**恰好一轮**；回补结论面 `STOP_RULE` 的 e2e 覆盖）；④ **两向反证**
    （按压 ⇒ 该红必红；二进制复原 ⇒ raw `sha256` 逐字节相同）；⑤ **沉淀与固化**
    （新增 MEM + 写进本 PLAN 与后续 GOAL 的 `fix_policy` 自证清单 + MAINLINE 修订记录一行）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **两树实跑复核（读数逐条）**：在 `49b2c7d` 的**干净 checkout** 与当前 HEAD 上，
      对同一组场景（消费面 normal/mismatch/missing-path、知识面 missing-provider、
      推进面 reject、结论面）跑**同一份探针**，逐场景给出轮次数 / 各轮终态 / 判定种类 /
      受引事实。**必须实跑取值**（禁止凭描述下结论）。
    verify: >-
      `scratch/goal041_probe_final.py` 两树各跑一次 ⇒ 读数表进 `scratch/`；
      三文件定向套件在 `49b2c7d` 与 HEAD 上**各自全绿**（16 例）。
    status: PASS
  - id: AC-2
    criterion: >-
      **逐条判定越界与否（删除行读数）**：读 GOAL-20261008-040 的 `fix_policy` 同步集
      清单；给三个文件各自的 `git diff --numstat 49b2c7d HEAD` 删除行读数与**逐行删除内容**；
      逐条比对**谓词是否等同**；结论（越界与否）如实登记进本 PLAN 与 RECHECK，
      **不得淡化**。
    verify: >-
      `git diff --numstat 49b2c7d HEAD -- tests/e2e/` ⇒ 三文件各 `-5`；
      `git diff 49b2c7d HEAD -- <file> | grep '^-[^-]'` 逐行列出（见本 PLAN「证据」节）。
    status: PASS
  - id: AC-3
    criterion: >-
      **恢复受判强度（显式声明形态，零容错回退）**：`_two_rounds` / `_two_round_program`
      只服务**成功面**并断言 `program_index == [1, 2]`；失败面助手 `_failing_round`
      断言 `== [1]` **且**第 2 次推进落 `STOP_RUN_FAILED`；知识面反证①同形态断言；
      **回补**结论面 `STOP_RULE` 的 e2e 覆盖（`SUCCEEDED` + 判词不命中规则 ⇒
      `STOP_RULE` + 逐字 `cited_facts` + 终态 `SUCCEEDED` 一并断言）
      ⇒ 三文件定向套件 **21 passed**（原 16 + 回补 1 + 其余例数不变）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_cross_run_consumption_is_decidable.py
      tests/e2e/test_program_advance_on_the_run_path.py
      tests/e2e/test_cross_run_knowledge_on_the_run_path.py
      tests/e2e/test_program_stop_reasons_are_decidable.py -q` ⇒ **21 passed**。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（按压 ⇒ 必红 / 二进制复原 ⇒ raw `sha256` 相同）**：对**五条**新收紧 /
      新回补的断言各做一次按压（改坏受判面），每条都必须判红；复原用**二进制读写**
      （`Path.read_bytes` / `write_bytes`，`newline` 不参与）并逐条比对 raw `sha256`
      **逐字节相同**（`git diff` 会被行尾归一化掩盖 ⇒ 不作证据）。
    verify: >-
      `scratch/goal041_press_two_way.py` ⇒ `PRESS SUMMARY: ALL RED + RESTORED`；
      判词归档进树 `.cursor/plans/goals/evidence/GOAL-20261008-040-repair-press-two-way.txt`。
    status: PASS
  - id: AC-5
    criterion: >-
      **沉淀与固化**：新增 MEM（改既有判据的断言属同轮同步集之外；收窄受判面必须**显式
      申报**；「强度不变」是一句**需要自证**的断言 —— 自证形态 = 逐条枚举 + `numstat`
      删除行读数 + 逐条谓词比对）并写进 `memory_entries`；把它写进**本 PLAN 及后续 GOAL**
      的 `fix_policy` **自证清单**；写入 MAINLINE `## 修订记录`（**只追加一行**）。
    verify: >-
      `.cursor/memory/entries/MEM-20261009-210-*.md` 在树 + `INDEX.md` 有行；
      MAINLINE 修订记录末行是本次新增；`tests/tooling/test_mainline_program_is_intact.py` 绿。
    status: PASS
  - id: AC-6
    criterion: >-
      **门与台账**：三文件定向套件全绿 + **全量 m0 23/23**（在**记录写入之后**、独占、
      仓库 `.venv`、`uv run --frozen --no-sync python -B`、不接管道）+ 治理 `validate.py`
      绿（含 `DOCS-CHECK`）+ CI 到终态 + 台账**逐提交**。
    verify: >-
      m0 终局行 `PASS: profile=m0; 23 deterministic checks`；治理绿；
      `scratch/poll_ci_all.sh <sha>` 遍历该 sha 全部 run + `/jobs`。
    status: PASS
---

# PLAN-20261009-359 — GOAL-040 纪律回溯修复（独立 cycle）

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 的**常驻入口**要求：本次触发的**第一件事**
> 就是这个独立 cycle（**先于序 9**，半个 cycle 量级），可与序 9 建档**同批推送**。
> **它不是序 9 的 GOAL** —— 序 9 的 GOAL 另立（`GOAL-20261009-041`，见 MAINLINE 程序表）；
本 PLAN 是 GOAL-20261008-040 的**收口后修复 cycle**（其 `escalation_triggers` 对应此形态）。

## 靶子（实测，不是提示词的描述）

GOAL-20261008-040 改动三个既有 e2e 判据文件，其中**一处谓词被替换（强度下降）**，
而该 GOAL 的 `fix_policy` 只授权「同轮同步面：**加法 / 搬迁登记**（**谓词、阈值、受判形态
一字未改**）」且要求**逐条枚举进清单**。三处改动**均未逐条枚举**（清单里只有通用条款）
⇒ 属 `escalation_triggers` 的「需要改**同轮同步集以外**的既有判据断言」形态。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 两树实跑复核（`49b2c7d` vs HEAD，逐场景读数） | PASS |
| AC-2 | 逐条判定越界（numstat 删除行读数 + 谓词逐条比对） | PASS |
| AC-3 | 恢复受判强度（显式声明形态 + 回补结论面覆盖）⇒ 21 passed | PASS |
| AC-4 | 两向反证（5 条按压全红 + raw sha256 复原一致 + 归档进树） | PASS |
| AC-5 | 沉淀与固化（MEM + fix_policy 自证清单 + MAINLINE 修订记录一行） | PASS |
| AC-6 | 门与台账（定向 + m0 23/23 + 治理 + CI 终态 + 逐提交） | PASS |

## 实施清单

- [x] WP-1 立题复核：两树同跑同一探针（`scratch/goal041_probe_final.py`）取逐场景读数
- [x] WP-2 越界判定：`git diff --numstat 49b2c7d HEAD -- tests/e2e/` + 逐行删除内容比对谓词
- [x] WP-3 恢复强度（消费面）：`_two_rounds` 断言恰好两轮；新增 `_failing_round` 断言恰好一轮
- [x] WP-4 恢复强度（知识面）：`_two_round_program` 断言恰好两轮；反证① 断言恰好一轮 + 失败面
- [x] WP-5 恢复强度（推进面）：**回补**结论面 `STOP_RULE` e2e 覆盖（原断言被删、无处接住）
- [x] WP-6 两向反证：五条按压（P-1…P-5）全红 + 二进制复原 raw `sha256` 相同 + 归档进树
- [x] WP-7 沉淀：MEM-20261009-210 + 本 PLAN 的 `fix_policy` 自证清单 + MAINLINE 修订记录一行
- [x] WP-8 门与台账：定向 21 passed → 记录 → 记录面判据 → 全量 m0 → push → CI → 台账

## 证据

### AC-1 两树实跑读数（同一探针，两树各跑一次）

| 场景 | `49b2c7d`（干净 checkout） | HEAD（本树） |
| --- | --- | --- |
| consumption/normal | `[1,2]` S,S · `CONTINUE` · started | `[1,2]` S,S · `CONTINUE` · started |
| consumption/mismatch | `[1,2]` S,**F** · `CONTINUE` · started | `[1,2]` S,**F** · `CONTINUE` · started |
| consumption/missing-path | `[1,2]` **F,F** · `CONTINUE` · started | **`[1]` F** · **`STOP_RUN_FAILED`** · not started |
| knowledge/missing-provider | `[1,2]` **F,F** · `CONTINUE` · started | **`[1]` F** · **`STOP_RUN_FAILED`** · not started |
| advance/reject | `[1]` **F** · **`STOP_RULE`** | `[1]` F · **`STOP_RUN_FAILED`** |
| conclusion-face/cross | `[1]` **S** · `STOP_RULE` `verdict PASS` | `[1]` S · `STOP_RULE` `verdict PASS` |
| conclusion-face/program | `[1]` **S** · `STOP_RULE` `verdict PASS` | `[1]` S · `STOP_RULE` `verdict PASS` |

**读数揭示的失真形态（与提示词的描述不同，以实跑为准）**：失败轮**并非**「没有任何落库
结论」（那一轮仍有 `produce` phase 落库的 `verdict PASS`）；真实形态是**旧代码把
「这一轮跑失败了」读成「结论判续」** ⇒ 第 2 轮真的被起出来（`[1,2]` 两轮全 FAILED）。

**等价性实测**：`missing-path` 第 1/2 轮的 `CUSTOM_EVALUATOR` 判词、`missing-provider`
第 1/2 轮的 `run.failed` 正文，去 UUID 后**逐字相同** ⇒ 「取第 1 轮」在**谓词上等价**、
但**观测宽度 2 → 1**（**不是**「强度不变」）。

**结论面可构造性实测**：一轮 `SUCCEEDED` + 声明 `continue_on=["ACCEPT"]` ⇒ `STOP_RULE` +
`verdict PASS` + 不起第 2 轮（两树都成立）⇒ 原用例删掉的**结论面覆盖可被接回**，
且 GOAL-040 新增文件**没有**接住它（该文件零条 `STOP_RULE` 用例）。

### AC-2 删除行读数（`git diff --numstat 49b2c7d HEAD`）

| 文件 | 新增 | 删除 |
| --- | --- | --- |
| `tests/e2e/test_cross_run_consumption_is_decidable.py` | 15 | **5** |
| `tests/e2e/test_cross_run_knowledge_on_the_run_path.py` | 13 | **5** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | 14 | **5** |
| `tests/e2e/program_advance_support.py` | 2 | 0 |

逐条谓词比对见 `RECHECK-20261009-360` 第 2 节（含三行**被替换的谓词**原文）。

### AC-3 定向套件

`tests/e2e/` 四文件 **21 passed**（原 16 + 回补结论面 1；`test_program_advance_on_the_run_path.py`
用例数 **6 → 7**）。

### AC-4 两向反证（`scratch/goal041_press_two_way.py`）

```
--- P-1 --- test_program_advance_on_the_run_path.py: 按压 RED | sha 复原一致=True | c11c1ee8642d
--- P-2 --- test_cross_run_consumption_is_decidable.py: 按压 RED | sha 复原一致=True | b21f5740ed9a
--- P-3 --- 同上文件: 按压 RED | sha 复原一致=True | b21f5740ed9a
--- P-4 --- test_cross_run_knowledge_on_the_run_path.py: 按压 RED | sha 复原一致=True | 23a5be3182da
--- P-5 --- 同上文件: 按压 RED | sha 复原一致=True | 23a5be3182da
PRESS SUMMARY: ALL RED + RESTORED
```

归档：`.cursor/plans/goals/evidence/GOAL-20261008-040-repair-press-two-way.txt`（613 B / `CR=0`）。

### AC-6 门与台账

- 定向：`tests/e2e` 四文件 **21 passed**；驱动 `test_program_runner.py` +
  幂等 + 记录面 + 规模 + 射程自查 **1219 passed**；
- 四道门（`ruff format --check` / `ruff check` / `mypy` strict）对三个改动文件**全绿**；
- 全量 m0：**23/23**（在全部记录写入**之后**，见「证据」与 CI 台账）；
- 治理 `validate.py` + `test_mainline_program_is_intact.py` 绿；
- CI：逐提交台账见本 PLAN 末节。

## 影响报告

- **Domain / API / schema 变化**：**无**（本轮只动判据与记录，**零产品代码改动**）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（不触 canonical / 迁移 / DTO）。
- **上游版本影响**：无。
- **判据面变化（逐条）**：三个文件均由「容错回退 / 覆盖丢失」改为「**显式声明形态**」；
  `test_program_advance_on_the_run_path.py` 用例数 **6 → 7**（回补结论面）；
  消费面受判轮次 **2 → 1**（**受判面收窄，如实登记**，谓词逐字保持）。
- **下一项任务**：MAINLINE 序 9（`GOAL-20261009-041`）建档（与本 cycle 同批推送）。

## fix_policy（本 PLAN 及**后续 GOAL** 的自证清单）

**改既有判据的申报纪律（本轮新增，固化进后续 GOAL 的 `fix_policy`）**：任何对**既有**
判据文件的改动，必须：

1. **逐条枚举**改动面（哪一行、改成什么）；
2. 用 `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；
3. **逐条比对谓词是否等同**（不是「强度未降」的口头断言）；
4. **收窄受判面必须显式申报**：写明**收窄了什么**（轮次 / 取值域 / 观测宽度）与**理由**；
   **不得**称「强度不变」——「强度不变」是一句**需要自证**的断言；
5. 属**同轮同步集之外**的形态 ⇒ 命中 `escalation_triggers`，须在 RECHECK 里**如实登记**。

## 无可复用事实

**不成立** —— 本轮沉淀 MEM-20261009-210（见 `memory_entries`）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-09 | IN_PROGRESS | 两树探针读数取齐（`49b2c7d` vs HEAD 逐场景）；越界判定（`numstat` 三文件各 -5 + 逐条谓词比对）；三文件改显式声明形态 + 回补结论面覆盖 ⇒ 定向 21 passed。 |
| 2026-10-09 | DONE | 两向反证五条按压全红 + raw `sha256` 复原一致 + 归档进树；MEM-20261009-210 + MAINLINE 修订记录一行；`RECHECK-20261009-360` 独立复检（PASS_WITH_WARNINGS）。 |
