---
id: PLAN-20261008-339
slug: goal-037-ec02-program-advance-entry
title: GOAL-037 cycle 2（EC-02）：程序推进驱动 + advance 入口 + 双 run 实跑（结论驱动）
status: IN_PROGRESS
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261008-037
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-037 的 **EC-02**（程序编排，深度轴）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：启动下一轮**必须**经既有 start-run use case
    （不绕 preflight / manifest freeze）；判定输入**只**取落库事实（run 终态 + 落库判词）；
    **不**用固定轮数替代结论驱动；新读面按既有纪律同轮同步（OpenAPI 快照 + `types.ts` +
    **e2e TS 夹具**）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字
    （**明确否认**）。
objective: >-
    把「程序编排」从骨架推到**真的跑起来**：① **驱动**（`advance_program`）—— 读程序内
    run + 上一轮终态 + 上一轮落库评审判词 ⇒ 判定（`START` / `CONTINUE` / `STOP_RULE` /
    `STOP_GUARDRAIL` / `WAIT` / `DEDUP`）⇒ 落一条**含被引原文**的决策 ⇒ 必要时经既有
    启动面起下一轮；② **产品入口** —— `POST /projects/{id}/programs`（建程序）、
    `POST /programs/{id}/advance`（推进）、`GET /programs/{id}`（读面：程序 + 各轮 run +
    逐条决策，点名「为何继续 / 为何停」）；③ **双 run 实跑** —— 一次程序跨两次 run 推进，
    第 2 轮由第 1 轮落库结论驱动；四态（继续 / 结论停 / 护栏停 / 幂等）各有判据；④ 门链 +
    记录 + as-is m0。
exit_criteria:
  - id: AC-1
    criterion: >-
      **驱动 + 六条判定**：`packages/application/run_orchestration/program_runner.py`
      （`advance_program`）—— 判定输入全是落库事实；启动面**注入**（缺省 ⇒ 点名「未提供
      启动面」，绝不静默当作已启动）；`cited_facts` 是被引事实的**原文**（判词逐字 /
      状态逐字）；`STOP_RULE` 与 `STOP_GUARDRAIL` **种类可区分**；`DEDUP` 覆盖崩溃窗口
      （认领未落库 ⇒ 不产生第二个 run）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py -q` ⇒ 7 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **产品入口与读面**：三个路由（建程序 / 推进 / 读面）+ DTO + OpenAPI 快照 +
      `types.ts` + e2e TS 夹具同轮同步；读面逐条给出「第 N 轮：为何继续 / 为何停」
      （决策种类 + 理由 + 被引 run）；推进在缺启动面时**点名**（不静默 200）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒
      全绿；OpenAPI 快照判据绿。
    status: PENDING
  - id: AC-3
    criterion: >-
      **双 run 实跑（结论驱动）**：一次程序实跑跨两次 run —— 第 1 轮终止后由编排启动
      第 2 轮；第 2 轮的存在**由第 1 轮落库判词驱动**（判词不命中 ⇒ 不起第 2 轮）；
      四态各有实跑判据：继续 / 结论停 / 护栏停（与结论停**可区分**）/ 幂等（重放不产生
      第二个 run）；反证：无启动面 ⇒ 点名。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿；新增判据文件全绿。
    status: PENDING
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：ruff / format / mypy / 规模四道门绿；记录（本 PLAN、GOAL 行、
      `RECHECK-20261008-340`）；治理 `validate.py` 绿；记录面判据绿；as-is m0 **23/23**
      （记录写完之后）。
    verify: >-
      门读数逐条 + `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261008-339 — GOAL-037 cycle 2（EC-02）程序推进驱动 + advance 入口

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 驱动 + 六条判定（含 `DEDUP` 崩溃窗口） | PASS |
| AC-2 | 产品入口与读面（三路由 + 同轮同步） | PENDING |
| AC-3 | 双 run 实跑（结论驱动 + 四态 + 反证） | PENDING |
| AC-4 | 四道门 + 记录面 + 治理 + as-is m0 23/23 | PENDING |

## 实施清单

- [x] WP-1：`program_runner.py`（`advance_program` + `_StartIntent`）+ 7 例判据。
- [ ] WP-2：三个路由 + DTO（`ProgramDto` / `ProgramDecisionDto` / `ProgramDetailDto`）+
      组合根接线（启动面 = 既有 start-run use case 的注入）。
- [ ] WP-3：同轮同步（OpenAPI 重生成 + `types.ts` + e2e TS 夹具）。
- [ ] WP-4：`tests/e2e/test_program_advance_on_the_run_path.py`（双 run 实跑 + 四态
      + 反证）。
- [ ] WP-5：`RECHECK-20261008-340` + GOAL 行 + `ALL_PLAN` + m0。

## 证据

### CI 真红并修（如实登记）

**`7c0da21` 的 M0 run（`37781594902`）在 `quality-ubuntu-latest` + `quality-windows-latest`
双平台真红**：`tests/tooling/test_python_source_limits.py` 判
`packages/application/run_orchestration/program_runner.py 存在超过 50 行的函数:
[('advance_program', 108)]`。**本地漏跑**：写驱动后我只跑了驱动判据与四道门
（ruff/format/mypy），**没**跑规模门所在的 `tests/tooling` 全量 ⇒ 门链在 CI 才咬住。
处置 = **拆函数**（不是调阈值）：`advance_program` → `_evaluate`（事实判定）+
`_after_hit`（护栏 / 去重 / 继续）+ `advance_program`（调度）三件，各 ≤ 50 行；
修后本机 `tests/tooling/test_python_source_limits.py` **1170 passed**、驱动判据 7 passed、
ruff/format/mypy 绿。**未**触碰任何判据或阈值。

### WP-1（已完成轮的读数）

| 门 | 读数 |
| --- | --- |
| `tests/application/run_orchestration/test_program_runner.py` | **7 passed**（`START` / `WAIT` / `STOP_RULE` / `CONTINUE` / `STOP_GUARDRAIL` / `DEDUP` / 无启动面点名） |
| `ruff check` | `All checks passed!` |
| `ruff format --check` | 绿 |
| `mypy`（strict） | `Success: no issues found in 1153 source files` |

判据要点（逐条可被单变量按压）：`test_stop_rule_cites_the_verbatim_verdict`（判词逐字进
`cited_facts`）；`test_guardrail_is_distinguishable_from_the_conclusion_stop`（种类不同）；
`test_replay_does_not_start_a_second_run_at_the_same_index`（崩溃窗口 ⇒ `DEDUP`、run 数不变）；
`test_missing_start_face_is_named_not_faked`（缺启动面**点名**）。

### 剩余 WP 的读数

（随 WP-2…WP-5 落地回填。）

## 影响报告

- **Domain / API / schema 变化**：无新域类型（驱动用既有 `ResearchProgram` /
  `ProgramDecision`）；WP-2 会新增只读/写入路由与 DTO（只增）。
- **安全 / 凭据变化**：无（不动放行面；启动面沿用既有 preflight / policy 链）。
- **兼容性 / 迁移风险**：无（无迁移；路由为新增）。
- **观测隐私**：决策记录只落判词原文与状态（不含新敏感面）。
- **上游版本影响**：无。
- **下一项任务**：WP-2…WP-5；之后 cycle 3（EC-03 跨 run 知识读入）/ cycle 4（EC-04）/ 收口。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | WP-1 落地：驱动 + 六条判定 + 7 例判据全绿（四道门绿）。WP-2…WP-5 待推进。 |
