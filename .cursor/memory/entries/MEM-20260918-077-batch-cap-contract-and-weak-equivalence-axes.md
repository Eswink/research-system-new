---
id: MEM-20260918-077
title: "批量读的上限要写成契约事实（值/口径/失败分类/分块责任），弱同判要逐条点名并机器校验"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-104-batch-read-upper-limit-and-fake-boundary.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-104-batch-read-cap-and-fake-boundary.md
supersedes: []
tags:
  - ports
  - contracts
  - fakes
  - batch-reads
  - governance
---

# 批量读上限是契约事实；"弱同判"要么对齐、要么逐条点名并可机器校验

## 做了什么

GOAL-006 cycle 5（EC-05）把两处**隐含**变成**显式**：

1. `dispatch_ownership_many`（批量派发读面）此前没有规模上限——传多少 id 就发多大的语句。
   现在：上限 `MAX_DISPATCH_OWNERSHIP_BATCH`（port 常量，值只在 port 写一次）、判定按**入参
   长度**（重复 id 不豁免）、超限 ⇒ `InvalidInputError`（调用方 bug，**可判定拒绝，不静默
   截断**）、恰好等于上限合法；三实现共用 port 的**同一句**校验，且都放在**读库之前**
   （PG 那条必须留在 `try` 之外，否则会被 `_wrap_operational` 包成瞬时失败）。分块归
   **调用方**：服务层按上限切块、合并，并承担"整批可能跨多个快照（块内仍是一个快照）"
   这条边界；任一块读不到就整批空 dict，不交半份答案。
2. Fake 与持久化实现的**弱同判**此前散在注释里。现在：port 模块 docstring 末节逐条点名
   8 条可同判轴与 3 条不可同判轴（租约过期 / LOST worker / 重排与 `BOTH`），每条点名判据
   文件与用例名；`tests/contracts/test_dispatch_ownership_weak_equivalence.py` 做机器校验。

## 为什么这样做

- **上限的四个要素都要落在契约里**：值（常量，唯一事实源）、判定口径（按什么计数）、失败
  分类（调用方 bug ⇒ `InvalidInputError`，不是瞬时失败）、**谁来分块**。少任何一个，调用方
  就会自己发明一套（或去重试一个永远不会成功的调用：PG 把校验放进 `try` 就会被
  `_wrap_operational` 包成 `TransientPortError`，实测复现）。
- **静默截断比报错更坏**：读面少条目 = 悄悄说假话；要么拒绝，要么由调用方分块后合并。
- **"弱同判"只写在注释里会漂**：删一条轴、把某条"三实现"用例悄悄改成只跑持久化实现、
  把引用指到不存在的用例，读起来都还像回事。所以把点名做成机器判据：可同判轴的引用必须
  真的在三实现上跑，并与套件里所有三实现用例**双向一一对应**（少点名 = 漏登记，多点名 =
  文本撒谎）；不可同判轴的引用**不许**声称三实现。
- **引用不是修辞**：轴清单里点名 `文件 + 用例名`，解析不到就红（把用例名写错一个字母
  也会红）。

## 怎么做与复现

```bash
export RESEARCHOS_POSTGRES_DSN="postgresql://research_os:research_os_m14_test@localhost:15432/research_os"
uv run --frozen --no-sync python -B -m pytest \
  tests/contracts/test_dispatch_ownership_weak_equivalence.py \
  tests/contracts/test_dispatch_ownership_contract.py \
  tests/adapters/sqlite/test_dispatch_read_snapshot.py \
  tests/api/test_run_dispatch_view_api.py \
  tests/postgres/test_dispatch_ownership_pg.py -q                      # 全绿
# 反证（七条，先红后复原）：删 Fake/SQLite/PG 的上限校验或挪到读之后、把某条三实现用例改成
# 持久化参数化、把 [不同判] 改成 [同判]、把用例名写错、改掉 PORTS.md 里的值。
```

上限的判定落点：`packages/application/ports/workflow_engine.py::validate_dispatch_batch`；
三实现各自在入口最早处调用；服务层切块在
`services/api/run_dispatch_view.py::_dispatch_batch_chunks`。

## 适用边界（踩过的坑）

- **轴清单写在方法 docstring 里会撞 50 行函数门禁**（本仓库
  `tests/tooling/test_python_source_limits.py`：函数 ≤ 50 行、文件 ≤ 450 行）；清单放
  **模块 docstring**，方法 docstring 只留契约要点 + 指针。
- **长测试名的 `path::test_name` 紧邻写法轻易超 100 列**（ruff E501）；"文件 + 用例名"
  分开点到同一轴内即可，判据分辨率不变（P6 反证：写错一个字母仍然红）。
- **"超限在读库之前"要能反证**：SQLite 用语句探针（超限时语句数 == 0，并留一条对照读
  反空洞）；PG 用"已关闭的引擎"反证（`_ensure_open` 抛 `PermanentPortError`，拿到上限错误
  就说明校验先于它）。
- **`adapters/postgres/workflow_engine.py` 恰好 450 行（硬上限，零余量）**：再改该文件前必须
  先让出行数或拆分（RECHECK-104 W-4）。
- 相关：[[MEM-20260918-073]]（一次读 = 一条语句 = 一个快照）、[[MEM-20260918-074]]、
  [[MEM-20260918-076]]（相位事实与有界等待的结构判据）。

## 来源

- PLAN-20260918-104 / RECHECK-20260918-104（GOAL-20260918-006 cycle 5 = EC-05）。
- 上游：RECHECK-20260918-097 W-2 / W-3（批量读无上限、Fake 弱同判只散在注释里）。
