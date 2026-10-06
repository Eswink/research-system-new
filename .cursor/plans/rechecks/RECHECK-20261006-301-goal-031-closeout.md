---
id: RECHECK-20261006-301
slug: goal-031-closeout
title: 复检：GOAL-20261006-031 自举收口（EC-05）—— 验证器进树 + 两树复检 + as-is m0 + 治理 + CI 台账
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-06
updated_at: 2026-10-06
plan_id: PLAN-20261006-301
reviewer: root-agent
parent_goal: GOAL-20261006-031
verify_paths:
  - >-
    uv run --frozen --no-sync python -B tools/verify_goal031_closeout.py --root . --verdict-only
    ⇒ 80 PASS / 0 FAIL（本树；#本 GOAL 工具自举）
  - >-
    uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script
    tools/verify_goal031_closeout.py --script-mode shared --root . --base-ref HEAD
    ⇒ 两树各 80 判词、逐行相同、sha256 相同、COMPARE identical=True、TWO-TREE PASS
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261006-031 的 EC-05 与 fix_policy；收口复检按 `MEM: goal-closeout-procedure`
    （验证器进树 + 两树 + 归档 + m0 + 治理 + 台账），声明 `verify_paths` ≥ 2 路并用**本 GOAL
    自己的工具自举**。**不改任何既有判据**（`IN_SCOPE` 为纯收紧；standard_verdicts 一行未重写）。
---

# RECHECK-20261006-301：GOAL-031 自举收口

## 检查结果

EC-05 的七条分支逐条实测：

1. **验证器进树 + `IN_SCOPE`（纯收紧）**：`tools/verify_goal031_closeout.py`（120 行）+
   `tools/goal031_closeout_assertions.py`（368 行）——**公共面一行不重写**（直接调
   `tools/closeout_recheck_assertions.standard_verdicts`），只写 GOAL-031 特有断言；
   两文件加入 `tests/tooling/test_tooling_scripts_meet_product_gates.py::IN_SCOPE`
   （**只增不删**）；两文件均过四道门（`ruff check` / `ruff format --check` / 规模 /
   `mypy`）。
2. **本树判词**：`--verdict-only` ⇒ **80 PASS / 0 FAIL**（`SUMMARY total=80 failed=0`）。
3. **两树复检 + 判词归档进树**：`tools/two_tree_recheck.py --script-mode shared` ⇒
   两树各 **80** 判词、**逐行相同**、`sha256` **相同**、`COMPARE identical=True`、
   **`TWO-TREE PASS`**；两份归档落 `.cursor/plans/goals/evidence/`
   （`GOAL-20261006-031-verdict-{current,clean}.txt`，二进制写盘，CR=0）。
4. **as-is m0 = `PASS: profile=m0; 23 deterministic checks`**（在**全部记录写入之后**；
   独占、仓库 `.venv`、`uv run --frozen --no-sync python -B`、canonical DSN pin、不接管道）。
5. **治理 `validate.py` 绿**。
6. **CI 台账逐提交**（`cancelled` 如实登记 + 原因 + `covered_by`；空集合 = 未取证；
   自我指涉边界**明写并封闭**）。
7. **承继残余逐条在位 + 决策登记 16 项 + 未覆盖范围逐条明写**（收口验证器的记录面断言
   逐条核对）。

## 结论

**PASS_WITH_WARNINGS**。五 EC（EC-01…EC-04 各自 PASS + EC-05 本收口）齐备，收口机器
（验证器 / 两树 / 归档 / m0 / 治理 / 台账）逐条绿。三条警告如实登记（下述 `W-EC05-1/2/3`），
**均不影响收口结论**。

## 复核路径（`verify_paths` 两路）

### 路径 1：本树自举复检（本 GOAL 的工具）

```
uv run --frozen --no-sync python -B tools/verify_goal031_closeout.py --root . --verdict-only
⇒ 80 PASS / 0 FAIL（SUMMARY total=80 failed=0）
```

判词面覆盖：标准断言集（受保护判据 / 规模门 / 产品根 / m0 条数 / 两树入口 / 规范页 /
记录自洽）+ 本 GOAL 特有断言（逐 EC 判据文件与例数下界 / EC-01 六条放行逐条 + 镜像 /
EC-02 三态常量 + 取数点唯一 / EC-03 三个声明字段 + 触发判定 + 跳过贯通 / EC-04 两个 DTO
字段 + 快照 + 生产者 / 两条新协议 phase 面 / 承接声明与出厂绑定 / 六份判词归档 /
`IN_SCOPE` / 记录面）。

### 路径 2：两树复检（当前树 + 干净 checkout）

```
uv run --frozen --no-sync python -B tools/two_tree_recheck.py --script tools/verify_goal031_closeout.py \
  --script-mode shared --root . --base-ref HEAD \
  --verdict-current scratch/goal031-cycle5/verdict-current.txt \
  --verdict-clean   scratch/goal031-cycle5/verdict-clean.txt
⇒ TREE current=D:esearch-system exit=0 verdicts=80 sha256=38bd17d3…
  TREE clean=<干净 checkout>        exit=0 verdicts=80 sha256=38bd17d3…
  COMPARE identical=True
  TWO-TREE PASS

（`sha256` 全文：`38bd17d342c236f2c336a0627e5de880737bb334617d52d9bdc5589e3470ba88`；
两份归档各 3495 字节、CR=0、`sha256` **相同**；日志 `scratch/goal031-cycle5/two-tree2.log`）
```

### 补充门

- 治理：`uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
  ⇒ 绿（无 error 行）。
- 四道门：`tests/tooling/test_tooling_scripts_meet_product_gates.py` ⇒ 8 passed。
- as-is m0：`PASS: profile=m0; 23 deterministic checks`（日志 `scratch/goal031-cycle5/m0-final.log`；
  `PASS [` **24** / `FAILED [` **0** / **5210 passed / 21 skipped / 180 warnings**，
  python 段 `679.98s`；独占、仓库 `.venv`、canonical DSN pin、不接管道、`EXIT=0`）。

## 警告（如实登记，不掩盖）

- `W-EC05-1`｜**首跑两树 RED 是预期且已如实登记**：干净树停在 `cc762b3`，缺本轮**尚未提交**的
  EC-05 增量（`IN_SCOPE` 条目 + GOAL 未覆盖范围逐条化）⇒ 两处 DIFF 被**逐条点名**
  （`in-scope-tools/verify_goal031_closeout.py` / `uncovered-scope-enumerated`）。
  处置 = **先提交再重跑**（承 `MEM: two-tree-recheck` 的「输入即现场」纪律：两树比的是**同一
  提交**上的结论，未提交的工作树增量不在干净树里 —— 这不是判据缺陷，是入口的正确行为）。
- `W-EC05-2`｜**两树同结论 ≠ 跨平台同结论**（承 GOAL-024 的 `W-NN` 同族）：两树用**同一台
  机器、同一个解释器** ⇒ 平台相关判据（路径 / 大小写 / 行尾）不在本复检的证明面内；
  本 GOAL 的判据面不含平台分支，但该边界**不因此消失**。
- `W-EC05-3`｜**收口验证器是读树判据**：它**不重跑**判据 / 门禁，只核「交付物在树 + 记录在位」；
  「判据真的绿」由本 RECHECK 的路径 1（判据文件的例数下界）与各 cycle 的 RECHECK 承担。

## 残余与未覆盖（逐条明写）

- **承继残余（原样保留，不重开）**：`R-M1`（未宣称项目安全）；`R26-1` / `R26-5` / `R26-7` /
  `R26-8`；`W27-*` / `W10-12`；`G24-5`；历史 `tools/` 的 73 条旧 lint 与无机器门脚本
  （只有**被点名脚本**有界受判）；`W-EC02-1`（夹具 1 行重写）/ `W-EC02-2` / `W-EC02-3`；
  `W-EC03-1`（判据初版构造缺陷，自修）/ `W-EC03-2`（相位过滤新机制只被本协议证明）。
- **本轮新增残余**：`W31-1`（放行 ≠ 被用：3 条未放行能力未被一次 run 使用）/ `W31-2`
  （同步集是重新定基）/ `W31-3`（`_PROVIDERS` 单行 tuple）/ `W31-4`（触发面新机制）。
- **未覆盖范围（逐条明写，不得据此宣称安全）**：**读面未认证**；**多租户未做** / **RBAC 未做** /
  **BOLA·BFLA 未做**（M18 deferred）；**部署面未验证**；**D 组审批通道未接通**；
  **`R-M1` 未收口**；`G24-5` 未做；`R26-2/3/4/6` 未做。**不得**据此宣称项目安全；
  **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
  deduplication）。
- **决策登记 16 项**：五项**授权开工**（① 放行面扩容 / ② `citation.validate` 全链 /
  ③ `G24-4` 改名 / ④ `.zcodeignore` 入 `.gitignore` / ⑤ pin 最小追加）**全部落地**；
  十一项**决定不做**（⑥ 默认 runtime 改真 / ⑦ 读面认证 / ⑧ 多租户·RBAC·BOLA·BFLA /
  ⑨ D 组审批通道 / ⑩ `G24-5` / ⑪ 部署面验证 / ⑫–⑮ `R26-2/3/4/6` / ⑯ destructive 改 allow）
  **逐条保持不做**（另有全局禁令三条：不得放宽既有断言 / 不得宣称项目安全 / 不得宣称
  exactly-once —— **本轮未触犯**）。
