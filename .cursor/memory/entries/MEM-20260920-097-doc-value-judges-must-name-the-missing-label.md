---
id: MEM-20260920-097
title: "从文档里取值来重算的判据：解析必须按固定标签且缺则点名——静默返回空串会让「判据没在看」伪装成「判据通过」"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-123-live-drift-sample-as-judged-record.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-123-live-drift-sample-as-judged-record.md
supersedes: []
tags:
  - testing
  - same-source
  - judge
  - documentation
  - falsification
  - goal-009
---

# 文档取值型判据的解析契约（GOAL-009 cycle 3）

## 做了什么

GOAL-009 EC-03 要把「实测返回 model 名 vs 声明值 ⇒ `MATCH`」这条样本从**散文**变成
**判据能重算的事实**。做法是新增
`tests/architecture/python/test_live_drift_sample_same_source.py`：从
`docs/integration/LIVE_MODEL_RUNBOOK.md` §6 解析出（声明值, 返回标识, 判定, run id），
再代入域函数 `assess_model_drift` **重算**，断言重算结果 == 文档写的判定。

样本当前是**一致**（`agnes-2.5-flash` vs `agnes-2.5-flash`）。判据同时钉住「读面同源」
（`services/api/routers/models.py` 的 drift 必须由同一个域函数产生）、
`UNKNOWN ≠ 无漂移`、以及两条证明力边界在场。

## 为什么这样做

- **「文档里写着 MATCH」不是判据**：它是人手抄进表格的一行字，抄错了没有任何东西会红。
  只有把值**重新算一遍**，文档才变成**可判**的。
- **解析器本身是新的腐坏面**。如果 `_cell()` 在找不到标签时返回 `""`（很多解析器的默认写法），
  那么一旦标签行被改名或删掉，判据会拿空串去断言，**要么恒绿、要么报一个和真因无关的错**——
  「判据没在看」就伪装成了「判据通过」。所以 `_cell()` / `_token()` 对缺失**点名报错**：
  `the runbook sample no longer has a row labelled '…'`。
- 这条与 [[MEM-20260920-092]]（新判据必须被反证**压**过）是**互补**的：092 说的是
  「要用改动把它压红」，本条说的是「**解析路径也要被压**——压出的是解析器的失败模式」。

## 怎么做与复现

**判据的两条硬要求**（写文档取值型判据时照抄）：

1. **只认固定标签**，不用宽松正则去猜格式：`| {label} |` 前缀匹配，标签是判据与文档之间的**契约**；
2. **取不到就点名报错**，绝不返回空串/`None` 让调用方去断言：
   ```python
   for line in text.splitlines():
       if line.startswith(f"| {label} |"):
           return line.split("|")[2]
   raise AssertionError(f"… no longer has a row labelled {label!r}")
   ```

**两条压法都要跑**（只跑第 1 条不够）：

```bash
# 压法一：改坏值 ⇒ 重算那条必须红，且同文件其余条仍绿（定位精确）
#   实测：1 failed, 7 passed；消息把 declared/returned/两态都打出来
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_live_drift_sample_same_source.py -q -p no:randomly

# 压法二：压解析路径本身 ⇒ 必须点名缺哪个标签（不静默）
uv run --frozen --no-sync python -B -c "
import sys; sys.path.insert(0, 'tests/architecture/python')
import test_live_drift_sample_same_source as J
J._cell('不存在的标签')   # 期望 AssertionError，消息里带标签名
"
```

**反证的边界（必须一起写进记录）**：改坏**一个**值会红，但把**两个值同时**改成另一对
**自洽**的假样本**不会**红——重算仍是 `MATCH`。兜住它的是**交叉引用**：
样本行里的 run id 必须**同时出现在**同一 goal 的 RECHECK 记录里（判据已断言），
所以假样本要么沿用真 run id（与 id 对应的观测不符），要么换 id（判据当即红）。

## 适用边界

- **适用于**：任何「文档/记录里写着一个**能重算**的结论」的判据——
  漂移判定、口径枚举（`REPEATABLE_CONFIGURATION` 这类）、阈值、计数、状态迁移结论。
- **不适用于**：文档里的**纯叙述**（措辞、理由、影响面）。那些只能判**在场**，
  不要给叙述加正则——会把判据变成文笔检查，一改就红且红得没意义。
- **不要**为了让判据不红而放宽解析：标签行改名就**同时改判据**，标签是契约不是措辞。
  相关：[[MEM-20260920-092]]、[[MEM-20260920-089]]（读面会说谎，需要措辞门）。

## 来源

- 判据：`tests/architecture/python/test_live_drift_sample_same_source.py`（8 个用例）
- 样本：`docs/integration/LIVE_MODEL_RUNBOOK.md` §6（run id `142f7e77-cd4d-4044-a953-79296509fd54`）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-123-live-drift-sample-as-judged-record.md` 的 **W-2 / W-3**
- 计划：`.cursor/plans/tasks/PLAN-20260920-123-live-drift-sample-as-judged-record.md`
- 目标：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
