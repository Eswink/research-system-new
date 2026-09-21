---
id: MEM-20260922-105
title: "收口复检脚本的可复用形态（实测）：五层判据 + 逐层按压；七处判据错误全部是同一类（读法比事实松）：子串当身份、固定列号、空表当字符串、标题措辞当结构、只在正文找、名字关键字全域扫；干净树上的差异要报「跳过」不能报「通过」"
status: ACTIVE
created_at: 2026-09-22
updated_at: 2026-09-22
scope: repository
confidence: 0.9
review_after: 2027-09-22
source_plans:
  - .cursor/plans/tasks/PLAN-20260922-132-goal-010-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260922-132-goal-010-closeout-recheck.md
supersedes: []
tags:
  - closeout
  - recheck
  - verification
  - governance-drift
  - goal-010
---

# 收口复检脚本的可复用形态（GOAL-010 EC-06 实测）

## 做了什么

写了一支**独立的收口复检脚本**（`scratch/verify_goal010_closeout.py`：**只读 / 只用标准库 /
不 import 仓库代码**，因此可以在干净 checkout 里用主树的解释器跑，也不可能与被测代码「同谋通过」），
在一棵目标结束时判五层：**A 交付物**（承重文件与符号在位）、**B 判据用例**（代表性用例按名定义）、
**C 登记面**（EC 表、`latest_recheck`、`child_plans`、`memory_entries`、`ALL_PLAN` 投影、残余字样）、
**D 凭据面**（key 值在被跟踪文件里 0 命中、磁盘副本都在已登记集合内、`.env` 无 runtime 开关）、
**E 默认姿态**（默认 runtime 仍是 Fake、判据放行面未被放宽、workflow 无 `secrets.`、预热门在位）。
然后在**当前树**与**干净 checkout**上各跑一遍核对同结论，并**逐层按压**。

## 为什么这样做

- **收口复检最容易被写成「把结论抄一遍」**：真正有信息量的是**能变红**——所以每层都必须被单独压红过
  一次（本轮的 P-1…P-5 五发全部先红后绿）。
- **判决必须能从事实推出，而不是从措辞推出**：第一版 113 条里 18 条红，**16 条是脚本自己的判据写错**；
  它们**全部属于同一类**——「读法比事实松」或「读法比事实窄」，而没有一条是记录真的错了。
- **干净树的差异要如实分类**：干净树没有 gitignored 的 `.env`，凭据面**比不了**——
  报 `PASS` 等于把「没比对过」读成「比对通过」；独立一个 **SKIP** 计数才诚实。

## 怎么做与复现

1. **五层与它们各自的反证**（照抄这个骨架即可）：
   A 改掉承重符号 ⇒ 该条红；B 改掉用例名 ⇒ 该条红；C 把 `latest_recheck` 写成**裸 ID** ⇒ 红
   （**这就是 GOAL-009 收口时抓到的真实漂移**）；D 在仓根放一个名字像凭据的文件 ⇒ 红；
   E 把判据的 `ALLOWED_KINDS` 加一类 ⇒ 红。**按压后 `git status` 必须无痕。**
2. **七处判据错误的更正**（每一处都是「让判据更准」而不是更松）：
   - **子串不是身份**：`symbol in source` ⇒ 把开关名改成 `…_MAP_PRESS` 后**按压不红**，
     而且注释里留着旧名字会让「已消失」的符号判在。改成**标识符边界**正则
     `(?<![A-Za-z0-9_])…(?![A-Za-z0-9_])`——**只挡词字符、不挡点**，因为文档里写的是成员访问
     `runtime_adapter._declared_deliverable_name`。（同一错误类别见 [[network-judge-traps-and-egress-sources]]。）
   - **状态列取最后一格**，不要按固定列号：状态常写成 `**PASS**（附注）`，固定取第 3 格会把
     「判据」列当状态（本仓 EC 表正是四列）。
   - **`memory_entries: []` 不是字符串**：逐字符遍历会让 `[` / `]` 变成两个「未登记的记忆条目」。
   - **plan id 要从文件名切三段**（`PLAN-20260922-132`），切两段会切出 `PLAN-20260922` 而在
     `ALL_PLAN` 里找不到行。
   - **W 列表的形态/标题在各份 RECHECK 里不同**（表格行 `| W-1 |`、加粗条目 `- **W-1 …**`、
     `## Warnings`、`### 7. W 列表`、`## 警告（W 列表）`）⇒ 判「有没有 **W-1** 这一条」，
     不要判标题措辞。
   - **残余字样要在整个目标记录集里找**（GOAL + 子 PLAN + RECHECK），有些残余只登记在子 PLAN
     （例：`ALLOW_PUBLIC_NETWORK` 在 PLAN-131 与 `AGENT_RUNTIME.md`，不在 GOAL 正文）。
   - **凭据副本的扫描范围要窄**：按文件名关键字全域扫会把 `.env.example`（模板）与
     `services/api/tool_provider_credentials.py`（产品模块）误报成「未登记副本」；
     只看**仓根与 `secrets/`**，并排除 `*.example` / `*.template`。
3. **干净树的造法与判读**：`git clone --depth 1 --branch main file:///D:/<repo> <仓外目录>`——
   必须是**真 git 仓库**（`git ls-files` 是 D 层的输入；`git archive` 出的树会让 D 层**静默失效**）。
   两棵树的失败**必须是同一组同一原因**；干净树多出来的差异只允许是「本机专有资产缺失」，
   并如实报 **SKIP**。
4. **`memory_entries` 的两种写法**：GOAL 用全路径、早期子 PLAN 用裸 ID，治理 `validate.py` 两种都收
   ⇒ 比较要**按 ID**（`MEM-\d{8}-\d{3}`），否则同一件事的两种拼法会被读成漂移（如实登记，不改历史记录）。

## 适用边界

- 判的是**登记面与结构姿态**，**不重跑 live 也**不重读数据库：`EC-01/02/03` 那种「真实 run 恰好
  `SUCCEEDED`」的证据由当时的 RECHECK 与 canonical 事实为证（见 [[goal-closeout-procedure]]）。
- A 层的口径是**「被引用」不是「仍可用」**（功能面归 `m0/python/tests`）；D 层的「值 0 命中」
  在**没有 `.env` 的树上只能 SKIP**。
- E 层按**源码形态**判默认（空值 ⇒ `FAKE_RUNTIME`），它防的是「默认被改」而不是「行为被改」。

## 来源

- `scratch/verify_goal010_closeout.py`（五层判据 + SKIP 计数；docstring 写明三条自我约束）；
  `RECHECK-20260922-132`（两树结论表 / 五发按压表 / 七处判据错误的更正表 / W-1…W-5）。
- 前例：`scratch/verify_goal009_closeout.py` 与 `RECHECK-20260920-126`（同一形态的首版，
  当时也修过一次判据：EC 状态列的读法与 ALL_PLAN 链接文本的形态）。
