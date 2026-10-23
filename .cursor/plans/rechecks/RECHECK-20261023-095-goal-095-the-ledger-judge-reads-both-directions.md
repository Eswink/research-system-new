---
id: RECHECK-20261023-095
slug: goal-095-the-ledger-judge-reads-both-directions
title: GOAL-095 复检 —— 台账判据的反方向 + 证据域的存量矛盾聚合
status: COMPLETED
result: PASS
created_at: 2026-10-23
updated_at: 2026-10-23
plan_id: PLAN-20261023-095
parent_goal: GOAL-20261023-095
owners:
  - root-agent
verify_paths:
  - tests/tooling/goal_commit_chain.py
  - tests/tooling/test_goal_commit_chain_reaches_the_ledger.py
  - tests/tooling/test_goal_ledger_covers_every_commit.py
  - packages/application/memory/conflict_sweep.py
  - adapters/canonical/memory_read.py
  - tests/application/memory/test_conflict_sweep.py
memory_entries:
  - MEM-20261023-229
---

# RECHECK-20261023-095 — GOAL-095

## 检查结果

**PASS**。五件交付面都成立且**可判**：① 台账判据从**单向**变**双向** —— 反方向判据
用 git 主题行取链、与 `## CI 台账` 逐条比对、缺席的**逐条点名**，且与正向判据**共用
同一个受判面**（不另造一套）；② 判据**真的会咬**（两向按压：删一行 ⇒ 判红并点名；
移出受判面 ⇒ 变绿；两次按 raw `sha256` 逐字节复原）；③ GOAL-094 的四个缺席提交
**补进台账**（一提交一行，真实 run id），判据**一行未因它而改**；④ 证据域前进一格
（存量矛盾聚合，确定性纯函数 + 读面可选键 + 实测成本曲线）；⑤ 记录面齐备。

## 一、建档实测的缺口（读数在动手前取得）

| # | 缺口 | 实测读数 |
| --- | --- | --- |
| 1 | 判据只有**一个方向** | `ledger_problems` 只比「台账 → 日志」；`提交链 → 台账` **零判据** |
| 2 | 后果可见 | GOAL-094 链 **10** 个提交、台账 **6** 行；`e8a1500c` / `ca4565d7` / `2c913d1f` / `f8c61422` 四个只改记录的提交不在表里；收口验证器仍 **78 PASS / 0 FAIL** |
| 3 | 归因手段有坑（实测） | `git log --grep=goal093`（搜**整条消息**）返回 `068e16c4`，而它的主题是 `test(goal094)` |
| 4 | 编号与序是两个空间（实测） | `GOAL-…-093` 的**序**是 61、主题写 `goal093`；按序 62 取链捞到 `GOAL-…-062` 的 **8** 个提交，真链被报成幽灵 |
| 5 | 证据域只在写入时判 | `gate._content_conflict_check` 只比「新提案 vs 现行记录」；存量里早已并存的相反记录无人看，读面逐条报 `USE` |

**第 3、4 两条是本轮**写判据时**由判据自己抓到的**（第一次跑就红，判词逐条点名），
不是事后从文档里读来的 —— 这正是「判据先于结论」的价值。

## 二、EC 逐条判定

| EC | 判据 | 读数 | 判定 |
| --- | --- | --- | --- |
| EC-01 | `tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`（5 条）+ 正向文件挂钩 1 条 + 既有 8 条 | **14 passed** | **PASS** |
| EC-02 | 两向按压（见第三节） | 判红点名 + 移出受判面变绿 + 逐字节复原 | **PASS** |
| EC-03 | GOAL-094 台帐 10 行 = 10 个提交；cycle 4 `commits` 格扩展 | 正反向同时绿 | **PASS** |
| EC-04 | `conflict_sweep.py` + 读面可选键 + 9 条判据 + 成本曲线 | **9 passed**；848 passed 零回归 | **PASS** |
| EC-05 | 记录面（GOAL / PLAN / RECHECK / ALL_PLAN / 宪章 / 见证） | `validate.py` 无 095 相关错误；mainline 三判据 **20 passed** | **PASS** |

## 三、两向按压（核心证据）

**按压 1 —— 从 GOAL-094 台账删掉 `80e844b1`**（它仍在链里）：

```
GOAL-20261022-094（序 62）：1 个提交不在台账（链 10 个，台账 9 个）：
80e844b1 feat(goal094): cross-goal ledger judge + the model-written report
1 failed, 4 passed
```

**按压 2 —— 把 GOAL-094 移出受判面**（祖父条款生效，台账**仍然残缺**）：

```
in scope  : [('GOAL-20261022-094', ['80e844b1'])]
excluded  : []
```

⇒ 同一条残缺台账**变绿**。这证明祖父条款**真的在起作用**，判据既不是恒判也不是恒过。

**按压 2 的两种写法（如实登记一个偏差）**：任务口径写的是「把 `_CUTOFF_SEQ` 临时改成 63
⇒ 判据变绿」。实测**不是**变绿 —— 改成 63 会把序 61 与 62 **一起**踢出受判面 ⇒ 受判面
**为空** ⇒ 四条判据全部按「空真不算通过」判红：

```
AssertionError: 受判面为空 ⇒ 本条失去判据对象（空真不算通过）
AssertionError: 序 61 必须在受判面内 —— 它的记账粒度正是本判据的第一个真实受判对象
AssertionError: 受判面内没有任何链 ⇒ 受判区间为空（空真不算通过）
4 failed, 8 passed
```

**这不是判据坏了，是空真守卫在正确工作**（受判面为空时判据失去对象，必须点名而**不是**
静默通过）。因此「祖父条款真的在起作用」改用**语义等价而受判面非空**的写法取证：**只把
GOAL-094 移出受判面**（台账**仍然残缺**）⇒ 同一条残缺台账**变绿**（`in scope` 报
`['80e844b1']`、`excluded` 空）。两者合起来才完整：63 那一版证明**守卫不空转**，
排除 094 那一版证明**条款真的在门控**。两版均已复原。

**逐字节复原**（`git diff` **不**作逐字节证据：`.gitattributes` 会归一化行尾）：

```
a9d5298a285285c57543f85e1fe600e12a0c61e5c5f224baeff0a1d79cd2bd32  GOAL-20261022-094-…md
ad9cc0c1df374900c9ba032988bc4e93a7584fac48468b4a6221f0d37ffbd05c  test_goal_ledger_covers_every_commit.py
c96781dadaeac24bf3ba428b7708e68b16fadb218d2f3c06777c100068f6d567  test_goal_commit_chain_reaches_the_ledger.py
c9ee898b52c78bb902139a7b5a503a65e474afd69a0e6fec78bb32ea8362d098  goal_commit_chain.py
```

`sha256sum -c scratch/goal095-press-baseline.sha256` ⇒ 四文件全 `OK`。

### HEAD 的唯一例外（结构必然，如实登记）

一个提交的哈希**写不进它自己携带的内容**。要求「链里每个提交都进台账」会让补记 HEAD
的那次写入又产生新 HEAD ⇒ 无终止（GOAL-094 的散文正是卡在这里）。受判面因此是
「链里除 HEAD 之外的全部」：漏记**立刻可见**，而链**收敛**（下一个提交补记上一个）。
**这不是放宽** —— 受判的是「除一个之外的全部」，不是「随便漏几个」。

## 四、既有判据有没有被改（逐条申报）

`git diff --numstat tests/tooling/test_goal_ledger_covers_every_commit.py` 的**删除行**：

| 删除处 | 内容 | 为什么不是放宽 |
| --- | --- | --- |
| import 块 | 新增 `pytest` / `goal_commit_chain` 的 import（后续又被 ruff 清掉未用的两条） | 只是取依赖；**谓词与常量一字未动** |
| 文件末尾 | 追加「反方向」分隔注释与一条**挂钩**判据 | **纯新增**；既有 8 个 `def test_` 的断言、阈值、扫描面**全部未动** |

**结论**：既有 8 条判据的**断言与射程零改动**（`git diff` 逐行可核：删除行只出现在
import 区）。新增判据是**更严**的（多判一个方向），不是放宽。

## 五、新增判据自己的两向反证（不只真树绿）

`test_the_chain_predicate_bites_both_ways_on_synthetic_chains` 在**合成链**上跑**同一条
谓词**：`unledgered(chain, ["a"*8], head) == []`（正例）／`unledgered(chain, [], head)`
点名 `a*40`（缺行）／HEAD 缺失**不算**漏（与「漏记」严格区分）／`phantom` 抓到别人的
提交。另配 `test_the_attribution_reads_the_subject_line_and_the_goal_number` 钉住
「主题行 + 编号」两个归因条件。

## 六、成本评估（EC-04 的交付之一）

`conflicts_among` 是两两比较（O(n²) 次纯文本判定）。本机实测（三轮取最小）：

| n | 对数 | 秒 |
| --- | --- | --- |
| 50 | 1 225 | 0.0394 |
| 100 | 4 950 | 0.1707 |
| 200 | 19 900 | 0.6409 |
| 400 | 79 800 | 5.1567 |
| 800 | 319 600 | 20.7839 |

**结论写进接口而不是散文**：规模翻倍 ⇒ 约 4 倍。因此扫描**不进**缺省读面，只在
显式请求 `sweep_conflicts` 时计算。若要在门链里常态化，需先按 `scope` 分桶加索引。

## 七、射程与残余（逐条，不假装闭合）

- **`W-1`｜CI 浅克隆 ⇒ 判据在 CI 上 skip**。`actions/checkout` 默认 `fetch-depth: 1`
  （`m0-quality.yml` 六处 checkout 均未声明 depth）⇒ CI 里只有 HEAD，取不到链。
  加 `fetch-depth: 0` 属**基础设施改动**，本轮授权把「改 CI workflow」列为**必须停下
  登记**的情形 ⇒ 选**方案 B**（点名 skip），**本地真执法、CI 不执法**。
  **需要用户决定**是否加 `fetch-depth: 0`。**不选 C**（只判 `git cat-file` 存在性）：
  漏掉的提交恰恰不在台账里，弱形态对它们**恒真**。
  **skip 不是通过**：非浅克隆下空链会**判红**（`test_the_empty_chain_is_named_not_skipped` 钉住）。
- **`W-2`｜归因靠主题行约定**。提交主题不写 `goal<NNN>` 就归不了链 —— 该情形由
  `untagged_code_commits` 单独判（**改了 `.cursor/` 之外却无名** ⇒ 判红），但「写了一个
  **错的**编号」判不出（那需要人工语义）。射程边界，如实留。
- **`W-3`｜存量扫描不自动执行**。它只在显式请求时算；**没有**任何门链把它常态化。
  这一轮交付的是**能力 + 成本读数**，不是「每次读取都扫」。
- **`W-4`｜扫描复用写入时的三种形态**。需要世界知识的矛盾（同义改写 / 需要推演的比较）
  **不判** —— 与 GOAL-083 的 `W-2` 同一条边界，本轮**不**扩语义射程。
- **`R-1`**：`R-M1` 未收口 —— 本 GOAL **不**宣称项目安全。
- **`R-2`**：投递语义**不是**「恰好一次」（at-least-once + 幂等 + 去重）。
- **`R-3`**：判据依赖 `git` 可执行文件与完整历史。缺一者 ⇒ **点名**（skip 带理由 /
  非浅克隆空链判红），不静默通过。

## 八、验证读数汇总

```
台账判据（正 + 反）        14 passed
存量矛盾聚合                9 passed
memory 相关零回归         848 passed / 3 skipped
mainline 三判据            20 passed
mypy                     1319 source files, no issues
ruff check / format       全绿
规模门                    memory_read.py 447 行 / memory_read() 50 行
凭据审计                  四面 offenders=0
```

## 结论

**PASS**。五个 EC 全达成：台账判据从**单向**补成**双向**（反方向判据与正向**共用同一
受判面**，5 + 1 条新用例，既有 8 条断言零改动）、判据**真的会咬**（删一行 ⇒ 判红并点名
`80e844b1`；移出受判面 ⇒ 变绿；四次按压全部按 raw `sha256` 逐字节复原）、GOAL-094 的四
个缺席提交如数补齐且**判据未因它而改**、证据域前进一格（存量矛盾聚合成确定性纯函数 +
读面可选键 + 实测成本曲线）。残余与未覆盖范围逐条登记在第七节（`W-1`…`W-4` + `R-1`…`R-3`）。
`R-M1` 未收口 ⇒ 本复检**不**宣称项目安全；投递语义**不是**「恰好一次」。
**需用户决定的一项**：是否给 M0 的 checkout 加 `fetch-depth: 0`（`W-1`）。
