---
id: MEM-20260920-093
title: "GOAL 收口的干净 checkout 封印配方（三层判据 + 两棵树同结论）；以及 Docker 后端审计用例的负载偶发红：隔离/整文件复跑 + 重跑一次全量，两轮结果都记"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-120-goal-008-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-120-goal-008-closeout-recheck.md
supersedes: []
tags:
  - goal-closeout
  - clean-checkout
  - seal
  - flake
  - docker
  - falsification
---

# 收口封印配方 + 负载偶发红的处置（GOAL-20260920-008 收口，cycle 7）

## 做了什么

GOAL-008 六条 EC 全 PASS 后做收口复检：**三层判据脚本 + 合并判据套件 + 干净 checkout 封印**，
最后写「收口结论」并置 `ACHIEVED`。

## 为什么这样做（可复用结论）

1. **收口复检要回证据面，不读结论文本**。三层判据的分工（本 GOAL 与 GOAL-007 同形）：
   - **A 交付物在树**：每条 EC 的关键文件 + 其中必须出现的**符号**（枚举成员、函数名、
     文档小节标题、前端 `data-testid`）；
   - **B 判据用例在树**：每条 EC 的判据文件里按名找到**代表用例**；
   - **C 登记面一致**：EC 表逐行 PASS、`latest_recheck` 指向存在且 `result: PASS*` 的 RECHECK、
     child_plans 存在且 DONE、`memory_entries` 文件存在、ALL_PLAN 有对应行。
   ⇒ 「记录里写了 PASS」不会让它绿，**文件真的在**才会。脚本第一版就因为把 EC-02 的判据
   路径指向 `tests/application/…`（真实位置在 `tests/architecture/python/…`）而**当场红**——
   这正是它有效的证据。
2. **干净 checkout 封印 = 两棵树结论必须一致**。做法：`git clone --no-hardlinks` 到仓库外、
   `checkout <tip>`、`git status` 干净、`git ls-files` 计数与源树相等，然后跑**同一份**脚本与
   **同一份**合并判据套件。性质是「**不引入新绿、也不引入新红**」——若克隆树更绿，
   说明源树有未提交/未跟踪的依赖；若更红，说明本地有脏状态。
   两个如实披露点：① 克隆树没有 `.venv`，用**主仓库的解释器**跑（依赖是安装物，不是仓库内容），
   cwd = 克隆树；② 收口循环自身的记录不在该 tip 里（它们产生于克隆之后），与 GOAL-007 同情形。
3. **合并判据套件要在同一进程里跑**：跨套件污染只在「两个套件同进程」时出现
   （本 GOAL 撞过「同一测试文件被两个模块名加载 ⇒ SDK `Action` 子类重复定义」，
   GOAL-007 撞过「函数内局部类 ⇒ `<locals>` 毒化判别联合」，还撞过「定义在函数内」的同族问题）。
   三个变体都只在合并跑时暴露，m0 的字母序有时恰好掩盖它们。
4. **Docker 后端的审计/实验用例有负载偶发红**：本轮收口 m0 第 1 次红 1 条
   （`test_success_run_produces_pass_audit`，可复现性审计判 `FAIL`），**隔离复跑绿、整文件复跑绿、
   重跑全量 m0 也绿**。处置顺序（与 GOAL 的失败分类一致）：
   ① 隔离复跑 → ② 整文件复跑 → ③ 按基础设施类**重跑一次全量** → ④ **两轮结果都记录**，
   并把「已知偶发」写进残余，而不是把它当成绿灯忽略、也不假装修好了（没有确定的根因可修）。
5. **能力边界要逐字写**：本 GOAL 的 EC-04/EC-05 的 live 分支在本机**没有发生过**（无凭据）。
   收口结论里必须写明 skip 与原因，**不得**写成「已实测通过」——GOAL 的 ACHIEVED 条款明文要求。

## 怎么做与复现

```sh
# 三层判据（当前树 / 另一棵树）
uv run --frozen --no-sync python -B scratch/verify_goal008_closeout.py
GOAL008_ROOT=<clone> uv run --frozen --no-sync python -B scratch/verify_goal008_closeout.py

# 干净 checkout 封印
git clone --no-hardlinks . <seal-dir> && cd <seal-dir> && git checkout <tip>
# 用主仓库解释器、cwd = 克隆树跑合并判据套件；对照两棵树的 passed/skipped

# 全量 m0（本地；偶发红按「重跑 1 次 + 记录两轮」处置）
sh scratch/run-m0-goal008-cycle5.sh
```

## 适用边界

- 三层判据是**存在性**证据：它证明交付物与判据还在、登记面自洽；
  **不**证明行为正确（行为由各 EC 的判据套件与实跑负责），**不**证明 W 列表的完备性。
- 干净 checkout 封印**不覆盖**：CI 环境（那是另一条独立证据）、依赖安装面（用主仓库解释器）、
  以及收口循环自身产生的记录。
- Docker 后端偶发红的登记是**诚实边界**：它没有被修，只是被记录；若重复命中且能给出确定根因，
  应按缺陷修并更新本条。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-120-goal-008-closeout-recheck.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-120-goal-008-closeout-recheck.md`（A/B/C 65 checks、W-1…W-7）
- 脚本：`scratch/verify_goal008_closeout.py`（只读、gitignored）
- 相关：[[MEM-20260920-092]]（新判据必须先被反证压一遍）、
  [[MEM-20260920-091]]（结论口径做成穷举词表）
