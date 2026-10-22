---
id: MEM-20261022-228
title: "判据靠继承就必然漏：跨 GOAL 纪律要写成遍历树的判据，不写进单个验证器的断言集"
status: ACTIVE
created_at: 2026-10-22
updated_at: 2026-10-22
scope: repository
confidence: 0.95
review_after: 2027-04-22
source_plans:
  - .cursor/plans/tasks/PLAN-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md
supersedes: []
tags: [judge-inheritance, cross-goal, ledger, test-tooling, report-narrative, digit-ban, goal-062]
---

## 做了什么

**两件**，都做成可判：

1. **台账纪律从「单 GOAL 断言」提成「跨 GOAL 判据」**：
   `tests/tooling/test_goal_ledger_covers_every_commit.py` **遍历**
   `.cursor/plans/goals/GOAL-*.md`，对每个终态且在受判面内的 GOAL 判「`CI 台账` 的
   `提交` 列里每个哈希都出现在某条 cycle 行的 `commits` 格里」。**只认 `commits` 列**
   （同一行别格出现不算 —— 那正是「把提交塞进散文」的形态）。祖父条款
   `_CUTOFF_SEQ = 61` / `_CUTOFF_DATE = 2026-10-22`；
2. **报告由模型撰写、数字仍可溯源**：
   `deliverable/report_narrative.py`（第 1…4 节 = 模型叙述、第 5 节 = 汇编器写的事实表）
   + `run_orchestration/report_narrative_task.py`（`narrate` / `llm_narrator`）+
   `report_task.ReportTaskDeps.narrator`（可选缝）。

## 为什么这样做

### 一、判据靠「继承」就必然漏

`_log_verdicts` 原本在 `tools/goal092_closeout_assertions.py` —— 它只保护 GOAL-092 自己。
GOAL-093 因此**没有**这条判据：台账 **4 行**、实际提交 **7 个**，三个提交既不进台账也不进
任何 cycle 行，而收口验证器仍报 **68 PASS / 0 FAIL**。同一个毛病以「**另一个 GOAL**」的
面貌重现 —— 因为它是**继承来的**，而继承靠每个验证器**主动**把自己的 GOAL 传进去。

**上提到 `closeout_recheck_assertions.standard_verdicts(root)` 解决不了**：那个函数只收
**树根**，不知道「当前在验哪个 GOAL」⇒ 上提之后仍要**主动传** ⇒ 失效点原样存在。

**正确形态 = 让判据自己去树里找受判对象**：遍历 `GOAL-*.md` ⇒ 新增 GOAL **自动**受判，
69 个验证器一个都不用改。落 `tests/tooling/` ⇒ 在 m0 的 `python/tests` 收集面内。

### 二、报告：把数字移出叙述面，才可能既让模型写又不丢溯源

确定性汇编的硬约束是「每个数字可溯源」。让模型写正文的直接风险就是数字脱离来源。
解法不是「让模型自觉」，而是**把两个面切开**：

- **叙述**（第 1…4 节）= 模型写，**禁止任何 Unicode 十进制数位**（`unicodedata.category
  == "Nd"`）。写了就**点名拒绝**，**不静默抽掉** —— 静默改写会让「这段是谁说的」不可判；
- **事实表**（第 5 节）= 汇编器写，每行带来源列，值逐字来自 `ReportInputs`（四个既有读面）。

「谁写的」也做成可读：接上叙述者 ⇒ `Artifact.created_by = model:<endpoint>/<returned>`
+ 元数据 `narrative` 块；没接 ⇒ **逐字节**回到既有汇编（`created_by` 仍是
`system:report-assembler`）。

## 两个可复用的坑

- **任务书不能发「它不许用的东西」**：首版 `narrative_prompt` 把**来源标识**
  （`39000001`）发给模型，而叙述被禁止含数字 ⇒ 等于**请它违规**。判据自己抓到了这一点。
  现在任务书只给**类别计数 + 指标名**。
- **测试替身别用 `type("_D", (), {"narrator": f})`**：函数变成类属性后就是**绑定方法**，
  `deps.narrator(prompt)` 会把 deps 当第一个参数传进去（`TypeError: takes 1 positional
  argument but 2 were given`）。用 `@dataclass` 才是普通可调用对象。
- **`inspect.getsource` 的子串不是行为判据**：`"narrative.author if narrative is not None" in source`
  判的是**代码形态** —— 把那一行改成 `narrative.author or "x"` 或写死常量，子串判据仍绿而
  制品上的作者已经错了。正确形态是**真的跑一次** `execute_report_task`，再从 `FakeArtifactStore`
  读回 `Artifact.created_by`（`tests/application/test_report_task_narrator_behaviour.py`）。
  同一纪律：`str(ID)` 是 dataclass 的 **repr**（`ID(value='…')`），不是 UUID 文本 ⇒ 拼制品 id 必须取 `.value`。

## 射程边界（本记忆**不**声称的）

- **叙述质量无人判**：判的是「谁写的」与「数字在哪」，不是「写得好不好」，也**不**判
  「叙述与事实一致」（模型可以写不含数字但仍然错的句子）。
- **跨 GOAL 判据不读 git 历史**：CI 的 `actions/checkout` 未声明 `fetch-depth`（实测六处
  均无）⇒ 工作区只有 HEAD 一个提交 ⇒ 「数这一轮有多少提交」在 CI 上会**空真**。
  该判据判的是**两份记录之间**的关系；「台账是否穷尽 git」由收口复检在本机取证。
- **`llm_narrator` 未在产品组合根默认接线**：只给产品闭包（`report_support.narrative_runner`）
  与可注入面；出厂路径今天仍是确定性汇编（接上会改交付物 `created_by`，属产品行为变更）。

## 怎么做与复现

```bash
# 1) 跨 GOAL 台账判据（真树）
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_goal_ledger_covers_every_commit.py -q
# ⇒ 6 passed

# 2) 两向按压（各判红一次，再按 raw sha256 逐字节复原）
cp .cursor/plans/goals/GOAL-20261022-093-*.md scratch/press.orig
sha256sum .cursor/plans/goals/GOAL-20261022-093-*.md          # 记下按压前的值
#   按压①：删掉迭代日志 cycle 2 的数据行（2 行 → 1 行）⇒ 判红并点名 4 个提交
#   按压②：从 cycle 2 的 `commits` 格删掉 `33e48f57` ⇒ 判红并点名它
cp scratch/press.orig .cursor/plans/goals/GOAL-20261022-093-*.md
sha256sum .cursor/plans/goals/GOAL-20261022-093-*.md          # 必须与按压前逐字节相同

# 3) 报告面判据
uv run --frozen --no-sync python -B -m pytest \
  tests/application/test_report_narrative.py \
  tests/application/test_report_narrative_on_the_product_path.py -q
# ⇒ 24 passed

# 4) 报告面反证（撤掉数字禁令 ⇒ 必须判红）
#    report_narrative.validate_narrative 里 `found = _numeral(...)` → `found = None`
#    ⇒ 3 failed；复原后 17 passed，sha256 回到原值
```

**判据为什么不能由真树的绿证明**：GOAL-093 的台账在按压前是日志的**子集** ⇒「台账 ⊆ 日志」
本来就会绿；「它会咬」只能由**按压**证明。这也解释了为什么该判据**不能**只用「台账是否穷尽
git」来定义（CI 里 `fetch-depth` 默认 1 ⇒ 空真）。

## 适用边界

- 判的是「**两份记录之间**的关系」（台账 → 日志），**不**判台账的结论对不对，也**不**判
  cycle 行的「修复 / 剩余差距」写得是否如实。
- 祖父条款只覆盖序 ≥ 61：更早的 GOAL 不回填（回填 = 改写历史记录）。
- 报告面判的是**结构事实**（谁写的 / 数字在哪），**不**判叙述质量，也**不**判叙述与事实
  是否一致。
- `llm_narrator` 未在产品组合根默认接线；出厂路径今天仍是确定性汇编。

## 来源

- `tests/tooling/test_goal_ledger_covers_every_commit.py`（本轮新增，6 条）
- `tests/application/test_report_narrative.py`（17 条）
- `tests/application/test_report_narrative_on_the_product_path.py`（7 条）
- `.cursor/plans/rechecks/RECHECK-20261022-094-goal-094-ledger-judge-and-the-model-written-report.md`
  （第三节 = 两向按压的 `sha256` 与判词原文）
- `.cursor/plans/goals/GOAL-20261022-093-the-review-verdict-drives-the-next-round.md`（台账补至 7 行）
