---
id: MEM-20261030-234
title: "假负住在读错的那一面：归档后的进展行、加粗形态的残余、主文件里的断言"
status: ACTIVE
created_at: 2026-10-30
updated_at: 2026-10-30
scope: repository
confidence: 0.95
review_after: 2027-04-30
source_plans:
  - .cursor/plans/tasks/PLAN-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md
supersedes: []
---

# 假负住在读错的那一面

## 做了什么

序 69（GOAL-101）本该只做「叙述质量判据」。真正花时间的是**三个同族缺陷**：都是判据
**绿着**而资产坏了，坏法是**判据读错了面**（不是断言错、不是产品错）。

## 为什么这样做

因为这三个缺陷**都判成了绿**，而它们的共同点是「判据读错了面」——不是断言写错、
不是产品坏掉。只修一处会让它换个地方再出现：098 曾手工加过一次归档回退，
那正是「漂移已开始」的信号，而当时没有人把它提成共享面。

## 怎么做与复现

1. **归档后的进展行 ⇒ 2 条假负 × 14 个验证器 = 28 条**。宪章的归档惯例只保留最近 3 条
   进展记录；`verify_goal0NN_closeout.py` 的 `progress-records-this-goal` 只读**活跃面**
   ⇒ 任何 GOAL 的行一被移进 `archive/`，它自己的收口复检就报「没记账」。
   **识别手法**：断言问的必须是「**当初**有没有写这一行」（活跃面**或**归档），
   不是「它现在还在活跃面吗」—— 后者是归档惯例的**正常结果**。
   **只发生在一个文件上**（098 曾手工加过回退）说明这是「17 处各写一遍必然漂移」的形态
   ⇒ 提成共享 helper（`tools/charter_progress.py`）。**归档文件有两种写法**（有小节标题 /
   表格直接跟在大标题下）⇒ 按**行的形状**认（第二格是 GOAL id），不按小节标题认。

2. **残余条目只认加粗形态 ⇒ 连续三轮 `REFUSED RESIDUAL_EMPTY`**。
   `charter_parse._W_ITEM` 要求 `- **`W-N`**`，而本仓 **87/109** 条写的是不加粗的
   `- `W-N``。三轮驱动方各自登记了同一个拒绝码，**没有一次**去读正则 —— 都以为是
   「那份 GOAL 的残余节写空了」。**识别手法**：拒绝码反复出现时，先数**全仓**两种形态的
   条数（`grep -c`），再看正则。

3. **断言住在主文件 ⇒ 负判扫描永远看不见**。`test_closeout_verifiers_run_their_own_assertions`
   的三条扫描只跑**断言集模块**，而 `progress-*` 两条住在 `verify_goal0NN_closeout.py`
   主文件里 ⇒ 上面那 28 条假负「绿在扫描面外」很久。**识别手法**：扫描面要按**判词的
   来源**划分（主文件 ∪ 断言集），不是按「哪个文件看起来像判据」。

## 适用边界

- **拒绝码反复出现 ⇒ 先怀疑正则，不是内容**。同一 `REFUSED_*` 连续三轮出现，读它的
  匹配式比读被拒对象更快。
- **共享读取面 > 逐处回退**。一处手工加的归档回退（098）是**漂移已开始**的信号。
- **窄到那一张表**：`## CI 台账` 小节里常跟别的表（状态历史 / 判据分类），按「行首是
  hash」收行会把它们当台账（实测 4 条假红）。表头首格含「提交」之后才开始收。

## 适用边界（不要过度读）

- 本轮落地的叙述质量判据是**弱判据**（引用不是无关 / 节非空洞 / 摘要与结论不逐字重复）。
  「过不了就是错的，过了**不代表对**」—— 论证是否成立仍未判。
- run 归属校验器的 6 条历史台账缺陷**只登记不改写**：改当时写下的记录 = 往历史里编造。

## 来源

- PLAN：`.cursor/plans/tasks/PLAN-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md`
- RECHECK：`.cursor/plans/rechecks/RECHECK-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md`
- 判据：`tests/tooling/test_verifier_main_files_report_no_negative.py`（含两向反证臂）、
  `tests/tooling/test_next_round_charter.py::test_the_plain_residual_form_is_read_too`
- 实测读数：修前 14 个验证器 × 2 = **28** 条假负；本仓残余 **87/109** 条为不加粗形态。
