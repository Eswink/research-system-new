---
id: MEM-20261023-229
title: "单向判据只挡住了它能看见的那一半：台账纪律要两向判，归因要认对编号空间"
status: ACTIVE
created_at: 2026-10-23
updated_at: 2026-10-23
scope: repository
confidence: 0.95
review_after: 2027-04-23
source_plans:
  - .cursor/plans/tasks/PLAN-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md
supersedes: []
tags: [ledger, bidirectional-judge, git-subject-line, goal-numbering, head-exception, conflict-sweep, cost-curve, goal-063]
---

## 做了什么

**两件**，都做成可判：

1. **台账判据从单向变双向**：`tests/tooling/goal_commit_chain.py`（谓词）+
   `tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`（5 条用例），判「主题行
   点名某终态 GOAL 的每个提交，都在该 GOAL 的 `## CI 台账` 里」。**与正向判据共用同一
   受判面**（import `_terminal_goals_in_scope` / `_ledger_commits` / `_CUTOFF_SEQ` /
   `_CUTOFF_DATE`）—— 不另造一套。
2. **存量跨记录矛盾聚合**：`packages/application/memory/conflict_sweep.py`
   （`conflicts_among` / `conflict_summary` / `conflict_rows` / `conflict_sweep`）+
   `memory.read` 的可选参数 `sweep_conflicts`（**缺省载荷逐字不变**）。

## 为什么这样做

### 一、单向判据只挡住了它能看见的那一半

GOAL-094 的判据判的是 `台账 ⊆ 迭代日志`。反方向 —— **提交链 → 台账** —— 零判据。
实测后果：GOAL-094 的链 **10** 个提交、台账 **6** 行，`e8a1500c` / `ca4565d7` /
`2c913d1f` / `f8c61422` 四个只改记录的提交不进表，而收口验证器仍报 **78 条判词全过 /
0 条不过**。**这不是「记录漏了」，是「没有那项检查」** —— 修记录的下一轮还会以别的面貌
漏，除非判据本身补上方向。

### 二、HEAD 必须是唯一的结构例外（否则判据不可满足）

一个提交的哈希**写不进它自己携带的内容**。若要求「链里每个提交都进台账」，补记 HEAD 的
那次写入本身又产生新 HEAD ⇒ **无终止**（GOAL-094 的散文正是卡在这里，最后靠「自指边界」
一段散文调和）。正确口径是「**除 HEAD 之外的全部**」：漏记**立刻可见**，而链**收敛**
（下一个提交补记上一个）。**这不是放宽**：受判的是一个之外的全部，不是随便漏几个。

### 三、两个归因坑，都是判据自己第一次跑就抓到的

- **`git log --grep` 搜整条消息**：`068e16c4` 的正文提到 GOAL-093 ⇒ 它出现在
  `--grep=goal093` 里，而它的主题是 `test(goal094)`。按整条消息归因会让**别人的提交**
  冒充本链成员 ⇒ 缺行被判成「有」。**只认主题行**（`%s`）。
- **编号 ≠ 序**：`GOAL-…-093` 的**序**是 61，主题写 `goal093`。首次实现按序取链 ⇒ 捞到
  `GOAL-…-062` 的 **8** 个提交，真链被报成 `phantom`（判词自相矛盾）。**序管祖父条款，
  编号管提交归因** —— 两个空间必须分开用。

### 四、O(n²) 的扫描不能摊进缺省读面

实测成本（三轮取最小）：n=50/100/200/400/800 ⇒ 0.0394 / 0.1707 / 0.6409 / 5.1567 /
**20.7839** 秒。规模翻倍 ⇒ 约 4 倍。所以扫描**只在显式请求** `sweep_conflicts` 时算：
「读一条记忆」的延迟不应取决于库有多大。要在门链里常态化，需先按 `scope` 分桶加索引。

## 可复用的坑

- **`is` 不能用来判「两个模块用的是同一个谓词」**：pytest 会以两个模块名加载同一个文件
  （`tests.tooling.x` 与 `test_x`），`SCOPE is _terminal_goals_in_scope` 在**同一份代码**
  上也判否。比 `__name__` + `__module__`。
- **规模门是两道不同的门**：`memory_read.py` 撞 450 行硬顶、`memory_read()` 撞 50 行
  函数顶 —— 用 `ast` 量出来再压注释，不要靠猜；`ruff check` 与 `ruff format --check`
  互不顶替。
- **宪章不得镜像状态枚举词**：把 `78 PASS / 0 FAIL` 写进 MAINLINE 会踩
  `test_no_goal_or_criterion_status_is_mirrored_in_the_charter`（`PASS` 是词表成员）。
  写「78 条判词全过 / 0 条不过」。
- **别用字符串替换改多行代码块**：`"…)    if _optional_arg(…)"` 这类拼接会静默把两行
  挤成一行（本轮实测踩到，靠 `ast.parse` 立刻发现）。改完**必须**重新 parse。

## 射程边界（本记忆**不**声称的）

- **`W-1`**：CI 浅克隆 ⇒ 判据在 CI 上 `skip`（`fetch-depth: 1` 是默认；六处 checkout
  均未声明 depth）。加 `fetch-depth: 0` 属基础设施改动，**需用户决定**。本地真执法、
  CI 不执法。**`skip` 不是通过**：非浅克隆下空链**判红**。
- **`W-2`**：归因靠主题行约定 —— 主题不写 `goal<NNN>` 由 `untagged_code_commits` 单独判
  （改了 `.cursor/` 之外却无名 ⇒ 判红），但「写了**错的**编号」判不出（需人工语义）。
- **`W-3`**：存量扫描不自动执行（没有门链常态化它）；本轮交付的是**能力 + 成本读数**。
- **`W-4`**：聚合复用写入时的三种可机械判形态 —— 需要世界知识的矛盾不判（与 GOAL-083
  `W-2` 同一条边界）。

## 怎么做与复现

```bash
# 1) 正反向台账判据
uv run --frozen --no-sync python -B -m pytest \
  tests/tooling/test_goal_ledger_covers_every_commit.py \
  tests/tooling/test_goal_commit_chain_reaches_the_ledger.py -q
# ⇒ 14 passed

# 2) 按压①：删掉 GOAL-094 台账里的 80e844b1 行 ⇒ 判红并点名它
#    按压②：把 GOAL-094 移出受判面（祖父条款生效）⇒ 同一份残缺台账变绿
#    两次都按 raw sha256 复原（git diff 不作逐字节证据：.gitattributes 会归一化行尾）
sha256sum -c scratch/goal095-press-baseline.sha256

# 3) 存量矛盾聚合
uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_conflict_sweep.py -q
# ⇒ 9 passed
```

**判据为什么不能由真树的绿证明**：真树在补记录前后都是「合法」的两种状态；「它会不会咬」
只能由**按压**证明 —— 而「删一行就红」与「移出受判面就绿」两个方向缺一不可：只有前者
时，判据可能恒判（把所有 GOAL 都算进来）；只有后者时，判据可能恒过。

## 适用边界

- 判的是「提交是否被记账」，**不**判台账里 run 结论对不对（那由 CI 侧取证）。
- 判的是「同一个 scope 内两条现行记录是否说法相反」，**不**判该不该消解、由谁消解
  （消解是产品行为变更，需拍板）。
- `R-M1` 未收口 ⇒ 本轮**不**宣称项目安全；投递语义**不是**「恰好一次」。

## 来源

- `tests/tooling/goal_commit_chain.py`（谓词，新建）
- `tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`（5 条用例，新建）
- `tests/tooling/test_goal_ledger_covers_every_commit.py`（既有 8 条 + 1 条挂钩判据）
- `packages/application/memory/conflict_sweep.py`（新建）/ `tests/application/memory/test_conflict_sweep.py`（9 条）
- `.cursor/plans/rechecks/RECHECK-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md`
  （第三节 = 两向按压的判词原文与 `sha256`）
- `.cursor/plans/goals/GOAL-20261022-094-goal-ledger-judge-and-the-model-written-report.md`
  （台账补至 10 行 = 10 个提交）
