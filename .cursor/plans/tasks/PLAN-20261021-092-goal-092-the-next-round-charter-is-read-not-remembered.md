---
id: PLAN-20261021-092
slug: goal-092-the-next-round-charter-is-read-not-remembered
title: GOAL-092 EC-01…05 —— 下一轮 charter 由上一轮的残余与阶梯机械派生（读取器 + 反证臂 + 一轮真用）
status: DONE
created_at: 2026-10-21
updated_at: 2026-10-21
parent_goal: GOAL-20261021-092
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md
memory_entries:
  - MEM-20261021-226
---

# PLAN-20261021-092 — GOAL-092 全五个 EC

## 验收条件

- [x] **EC-01**：确定性读取器在树（`tools/next_round_charter.py` + `tools/charter_parse.py`），对已收口 GOAL 产出三块可提取事实（`W-NN` 逐条原文 / 阶梯「下一级」/ CI 台账读数），判断面显式留空。
- [x] **EC-02**：九条拒绝臂各有独立用例（删一条 `W` / 改正文 / 非终态 ×3 / 缺复检 / 复检属他 GOAL / 复检不通过 / 断号 / 阶梯未收录 / 残余节空而无标记），全部 `exit 2` + 点名 + 不写盘。
- [x] **EC-03**：同输入两次 ⇒ `sha256` 相同；经 `--out` 落盘两次 ⇒ `read_bytes()` 相同且无 `\r`。
- [x] **EC-04**：产物真的被用作序 60 的 charter 输入；上一轮七条残余 **7/7** 有处置（`W-6` / `W-7` 有实际动作）。
- [x] **EC-05**：记录 → `git add` 全部受判文件 → 记录面判据 → **最后**跑 m0 写见证 → 提交推送 → CI 到终态；阶梯「迭代」行同轮升级；战役预算触顶登记。

## 一、五个 EC 的落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `tools/next_round_charter.py`（入口 + 渲染）、`tools/charter_parse.py`（纯解析原语） | `tests/tooling/test_next_round_charter.py`（19 例） |
| EC-02 | 同上（`Refusal` 的九个 code） | 同左（9 条拒绝用例，合成树上改事实） |
| EC-03 | 同上（二进制写盘 + 无时钟） | 同左（2 条确定性用例） |
| EC-04 | `.cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md`（产物）+ GOAL「上一轮残余的处置」表 | `tools/goal092_closeout_assertions.py` |
| EC-05 | 记录 + 正式见证 + CI 台账 + 战役级核算 | 见证 `terminal_line` + 指纹相等 |

## 二、执行顺序（本轮实际走的）

1. **先让读取器在真文件上跑通**（不是先写判据）：对着 GOAL-091 跑出骨架，人眼核对
   `W-1…W-7` 与阶梯「复检」行确实对上 —— 这一步先暴露了「残余节里还有 `R-1…R-3` 一组，
   它们的续行同样是缩进的」这个会污染切分的形态。
2. **再写判据**：五条提示词判据各自落成用例；判据自己的切分实现**独立写一份**
   （不用被测实现的输出当期望）。
3. **反证逐条在合成树上改事实**（不改断言）：删整条 `W-7`、改正文、改 `status`、
   删复检、改 `parent_goal`、改 `result`、删 `W-2` 留断号、改宪章的阶梯行、清空残余节。
4. **同轮登记**：两个新脚本与判据文件在**写下第一行之前**就想清楚要进哪些清单
   （`IN_SCOPE` / `_VERIFIERS` / `CASE_FLOORS`），落地即登记 —— 这是 GOAL-091 `W-7` 的直接回应。
5. **真用一次**：用骨架的 `W` 列表驱动本文件的「上一轮残余的处置」表，7/7 逐条给下场。
6. **收口**：记录写完 → `git add` **全部**受判文件 → 记录面判据 → **最后**跑 m0 →
   不再改受判文件 → 提交推送。

## 三、实跑读数（本轮）

- `pytest tests/tooling/test_next_round_charter.py -q` ⇒ **19 passed**。
- 对 GOAL-091 真文件：残余 **7/7**、阶梯命中 **复检** 一行、CI 台账 5 success + 1 无 run
  ⇒ 结论「全绿」。
- 产物两次落盘 `sha256` 相同：`2776ad06134269876a384f163dbe9aba4500f962b64da275bd8a0d23cbd17024`。
- 四道门（`ruff format --check` / `ruff check` / 规模 / `mypy`）在**写完时**即全绿
  —— 因为登记先于写（`W-7` 的顺序反转）。

## 实施清单

1. [x] 读宪章 / GOAL 格式规范 / 治理校验器 / 四道门射程 / 收口验证器清单（决定落点与登记面）。
2. [x] 写 `tools/charter_parse.py`（纯解析原语）与 `tools/next_round_charter.py`（入口 + 渲染）。
3. [x] 写 `tests/tooling/test_next_round_charter.py`（19 例：不丢不增 / 确定性 / 九条拒绝臂 / 判断面留空 / CI 读数 / 口径同源）。
4. [x] 同轮登记进 `IN_SCOPE`（四道门射程）。
5. [x] 在 GOAL-091 真文件上产出骨架并落 `evidence/`。
6. [x] 写 GOAL-092 / 本 PLAN / MEM-226；七条残余逐条处置。
7. [x] 写 RECHECK-092；`goal092_closeout_assertions.py` + `verify_goal092_closeout.py`；登记进 `_VERIFIERS` / `CASE_FLOORS`。
8. [x] 阶梯「迭代」行升级 + 程序表序 60 + 进展记录 + 两表归档 + 战役级核算（预算触顶）。
9. [x] `git add` 全部受判文件 → 记录面判据 → 全量 m0（见证）→ 提交推送 → CI 台账。

## 证据

- `tests/tooling/test_next_round_charter.py`（19 例；含九条拒绝臂与两条确定性）
- `.cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md`（产物，`sha256:2776ad06…`）
- `tools/next_round_charter.py` / `tools/charter_parse.py`（四道门全绿）
- `RECHECK-20261021-092`、两树判词归档、m0 见证、CI 台账（逐提交）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-21 | **IN_PROGRESS** | 建档并落地 EC-01…EC-04；读取器 + 判据 + 产物 + 七条残余处置表全部在树。 |
| 2026-10-21 | **DONE** | EC-05 收口：记录面判据 → 全量 m0（见证）→ 提交推送 → CI 到终态。 |

## 影响报告

- **产品代码**：零改动（本轮只新增 `tools/` 下的开发侧资产；`PRODUCT_ROOTS` 与 m0 条数未变）。
- **Domain / API / schema**：零改动。
- **安全 / 凭据**：零改动；新增文件不含凭据（`tools/credential_audit.py` 四面 `offenders=0`）。
- **兼容性 / 迁移**：零迁移。新增的是一份记录面制品与两个开发侧脚本。
- **上游版本**：零影响（无新依赖）。
