---
id: GOAL-20261023-095
slug: the-ledger-judge-reads-both-directions
title: 台账判据补上反方向（提交链 → 台账），并让证据域的存量矛盾可聚合
status: ACHIEVED
created_at: 2026-10-23
updated_at: 2026-10-23
owners: [root-agent]
authorization:
  source: user-request
  ref: >-
    用户 goal-mode 指令（序 63）：给「台账纪律」补上反方向 —— 现有判据只判
    「台账 ⊆ 迭代日志」，反方向「提交链 → 台账」完全没有判据；同轮必须让阶梯前进一格
    （宪章 `test_mainline_research_ladder_advances.py` 强制）。用户下放全部决策权：
    可新建/修改代码、测试、判据、记录、配置；提交并推送到 main 触发 CI。
    必须停下登记 BLOCKED 的情形：改产品边界 / 放宽任何既有判据 / 动冻结面 /
    新增或改 `TrustLabel` 取值 / 改 CI workflow / 叙述质量的判定口径。
    push-to-main-for-CI：只推 `main`、不 force、不重写历史、不推旁支；
    `RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` 逐命令传，**不进** `.env`。
objective: >
    让「台账纪律」从**单向**变成**双向**：新增一条判据，对受判面内每个终态 GOAL，
    用 git 主题行取该 GOAL 的提交链，逐条比对 `## CI 台账`，缺席的**逐条点名**
    （HEAD 结构上除外 —— 一个提交写不进它自己携带的内容）；零 run 与只改记录的提交
    **不豁免**。判据与既有正向判据**共用同一受判面**（`_CUTOFF_SEQ` / `_scope_reason`），
    空真即判红，并在真实树上两向按压取证（删一行 ⇒ 判红并点名；移出受判面 ⇒ 变绿；
    两次都按 raw `sha256` 逐字节复原）。同轮把 GOAL-094 缺席的四个提交补进台账，
    使判据从第一天起就有真实受判对象。同时推进阶梯「证据」域一格：把「写入时判
    新提案 vs 现行记录」扩到**存量**的跨记录矛盾聚合（确定性纯函数 + 读面显式请求
    + **实测成本曲线**作为交付的一部分）。
exit_criteria:
  - id: EC-01
    criterion: >-
      反方向判据在树且**不改既有 8 条判据**：`tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`
      存在，import 正向判据的 `_terminal_goals_in_scope` / `_ledger_commits` / `_CUTOFF_SEQ` /
      `_CUTOFF_DATE`（**不另造受判面**）；`test_goal_ledger_covers_every_commit.py` 的既有
      8 条用例逐条仍在；正反向合计 ≥ 12 条用例通过。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_goal_ledger_covers_every_commit.py
      tests/tooling/test_goal_commit_chain_reaches_the_ledger.py -q` ⇒ 14 passed；
      `git diff --numstat tests/tooling/test_goal_ledger_covers_every_commit.py` 的删除行
      只出现在 import 块与末尾追加点（既有 8 个 `def test_` 逐字未动）。
    status: PASS
  - id: EC-02
    criterion: >-
      判据**真的会咬**（两向按压，均在真实树上）：
      ① 删掉 GOAL-094 台账里的 `80e844b1` 行 ⇒ 判红且判词点名
      `80e844b1 feat(goal094): cross-goal ledger judge + the model-written report`；
      ② 把 GOAL-094 移出受判面（祖父条款生效）⇒ 同一条残缺台账**变绿**；
      ③ 两次都按 raw `sha256` 逐字节复原（`git diff` 不作为逐字节证据）。
    verify: >-
      按压记录在本 GOAL 的 `## 两向按压` 一节；复原后
      `sha256sum -c scratch/goal095-press-baseline.sha256` 全 OK。
    status: PASS
  - id: EC-03
    criterion: >-
      GOAL-094 的台账在**新判据下**通过：`e8a1500c` / `ca4565d7` / `2c913d1f` / `f8c61422`
      四个提交一提交一行补进 `## CI 台账`（每行有真实 run id 与结论），且它们同时出现在
      某条 cycle 行的 `commits` 格里（正向判据仍绿）；判据本身**一行未改**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_goal_commit_chain_reaches_the_ledger.py
      tests/tooling/test_goal_ledger_covers_every_commit.py -q` ⇒ 14 passed（含正向 8 条）。
    status: PASS
  - id: EC-04
    criterion: >-
      证据域前进一格：`packages/application/memory/conflict_sweep.py` 提供
      **跨记录**矛盾聚合（确定性纯函数，零出网/零模型/零时钟）；三条边界与写入时判定
      逐条一致（同 scope 才比 / `active=False` 不参与 / 已声明不重复报）；
      `memory.read` **只在显式请求** `sweep_conflicts` 时附 `conflicts` 键
      （缺省载荷逐字不变）；**成本曲线实测**并写入本 GOAL。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/memory/test_conflict_sweep.py -q` ⇒ 9 passed；
      `uv run --frozen --no-sync python -B -m pytest
      tests/adapters/canonical/ tests/application/memory/ -q` ⇒ 全绿（零回归）。
    status: PASS
  - id: EC-05
    criterion: >-
      记录面收口：本 GOAL 的迭代日志 / CI 台账 / 状态历史齐备；宪章程序表新增序 63、
      阶梯「证据」行升级并收窄 `下一级`、进展记录与修订记录各追加一行（两表 ≤ 3 行）；
      PLAN / RECHECK 在树且治理检查通过。
    verify: >-
      `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
      ⇒ 无 GOAL 相关错误；`uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_mainline_program_is_intact.py
      tests/tooling/test_mainline_research_ladder_advances.py
      tests/tooling/test_mainline_archive_is_continuous.py -q` ⇒ 全绿。
    status: PASS
budget:
  max_cycles: 14
  per_cycle_minutes: 150
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 真实凭据出现在 tracked 文件里（含记录）—— **立即 BLOCKED** 并清理
  - 需要改 `.github/workflows/**`（判定为基础设施冻结面）
child_plans:
  - .cursor/plans/tasks/PLAN-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md
memory_entries:
  - MEM-20261023-229
---

# GOAL-20261023-095 — 台账判据补上反方向

## 目标与退出标准

见 frontmatter。**一句话**：把「台账纪律」从单向（台账 ⊆ 迭代日志）补成双向
（提交链 → 台账），并同轮让证据域的存量矛盾可聚合。

### 为什么这一轮是必要的（建档实测）

| # | 缺口 | 实测读数（本轮动手前取得） |
| --- | --- | --- |
| 1 | 判据只有**一个方向** | `test_goal_ledger_covers_every_commit.py` 的 `ledger_problems` 只比「台账 → 日志」；`提交链 → 台账` **没有任何判据** |
| 2 | 后果可见 | GOAL-094 的链 **10** 个提交、台账 **6** 行；`e8a1500c` / `ca4565d7` / `2c913d1f` / `f8c61422` 四个**只改记录**的提交不在表里，而收口验证器仍报 **78 PASS / 0 FAIL** |
| 3 | 归因手段本身有坑 | `git log --grep=goal093`（搜**整条消息**）返回 `068e16c4`，而它的主题是 `test(goal094)` —— 按整条消息归因会让别人的提交冒充本链成员 |
| 4 | 编号与序是两个空间 | `GOAL-…-093` 的**序**是 61、主题写 `goal093`；按序取链会捞到 `GOAL-…-061` 的 9 个提交，把真链报成幽灵 |
| 5 | 证据域只在写入时判 | `gate._content_conflict_check` 只比「新提案 vs 现行记录」；两条**早已并存**的相反记录无人看，读面逐条报 `USE` |

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的「循环入口协议」幂等重入：读迭代日志最后一行 +
工作树/远端实况判定续点。**同一时刻只允许一个驱动持有本 GOAL。**

## 单 cycle SOP

① derive（从剩余 EC 圈最小主题、写子 PLAN）→ ② 执行 → ③ 本地验证（m0 + 定向套件）
→ ④ commit（显式路径）→ ⑤ push + CI 并记录真实终态 → ⑥ 纠错 → ⑦ 记录 + 下一轮。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff / mypy 报错 | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest 断言 | 读失败输出定位；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、DSN 注入、作业 20 分钟超时） | 按既有配方重跑；不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 | 等窗口重跑 1 次；仍败 → BLOCKED |
| 治理/安全门禁 | Mimosa / validator 命中 | 按处置文档修或登记误报；**不得绕过**；不得宣称安全 |

## 终止与收口

五个 EC 全 PASS + 独立 RECHECK PASS/PASS_WITH_WARNINGS + CI 到终态 ⇒ `ACHIEVED`。
触预算或命中 `escalation_triggers` ⇒ `BLOCKED` 并留人工决策。

## 两向按压（EC-02 的核心证据）

**按压 1 —— 从 GOAL-094 台账删掉 `80e844b1`**（它仍在提交链里）：

```
GOAL-20261022-094（序 62）：1 个提交不在台账（链 10 个，台账 9 个）：
80e844b1 feat(goal094): cross-goal ledger judge + the model-written report
1 failed, 4 passed
```

⇒ 判红并**点名**该提交（前缀 + 主题），且在册提交数从 10 掉到 9 可见。

**按压 2 —— 把 GOAL-094 移出受判面**（祖父条款生效，台账**仍然残缺**）：

```
in scope  : [('GOAL-20261022-094', ['80e844b1'])]
excluded  : []
```

⇒ 同一条残缺台账**变绿**。这证明祖父条款**真的在起作用**，判据不是恒判也不是恒过。

**一个偏差，如实登记**：任务口径预期「`_CUTOFF_SEQ` 改成 63 ⇒ 判据变绿」。实测**是判红**
（4 failed），因为 63 会把序 61 与 62 **一起**踢出受判面 ⇒ 受判面**为空** ⇒ 空真守卫点名
`受判面为空 ⇒ 本条失去判据对象（空真不算通过）`。**这是守卫正确工作**（空集合不是通过）。
故「祖父条款真在门控」改用受判面非空的等价写法取证：**只排除 GOAL-094**（台账仍残缺）
⇒ 变绿。两版合起来：63 版证明**守卫不空转**，排除 094 版证明**条款真的在起作用**。

**两次均按 raw `sha256` 逐字节复原**（`git diff` 不作逐字节证据：`.gitattributes`
会归一化行尾）：

```
a9d5298a285285c57543f85e1fe600e12a0c61e5c5f224baeff0a1d79cd2bd32
  .cursor/plans/goals/GOAL-20261022-094-goal-ledger-judge-and-the-model-written-report.md
ad9cc0c1df374900c9ba032988bc4e93a7584fac48468b4a6221f0d37ffbd05c
  tests/tooling/test_goal_ledger_covers_every_commit.py
c96781dadaeac24bf3ba428b7708e68b16fadb218d2f3c06777c100068f6d567
  tests/tooling/test_goal_commit_chain_reaches_the_ledger.py
c9ee898b52c78bb902139a7b5a503a65e474afd69a0e6fec78bb32ea8362d098
  tests/tooling/goal_commit_chain.py
```

基线存于 `scratch/goal095-press-baseline.sha256`（gitignored）；`sha256sum -c` 全 OK。

### HEAD 为什么是唯一的例外（结构必然，不是豁免）

一个提交的哈希**写不进它自己携带的内容**。若要求「链里每个提交都进台账」，那么
补记 HEAD 的那次写入本身又产生新 HEAD ⇒ 无终止（GOAL-094 的散文正是卡在这里）。
受判面因此定为「链里除 HEAD 之外的全部」：漏记**立刻可见**（`80e844b1` 就是这样被抓到
的），而链**收敛** —— 下一个提交补记上一个。这不是放宽：受判的是**除一个之外的全部**，
而不是「随便漏几个」。

## 成本曲线（EC-04 的交付之一，实测）

`conflicts_among` 是两两比较（O(n²) 次纯文本判定）。本机实测（取三轮最小值）：

| 记录数 n | 对数 n(n-1)/2 | 耗时（秒） |
| --- | --- | --- |
| 50 | 1 225 | 0.0394 |
| 100 | 4 950 | 0.1707 |
| 200 | 19 900 | 0.6409 |
| 400 | 79 800 | 5.1567 |
| 800 | 319 600 | 20.7839 |

**结论（写进接口而不是留在散文里）**：规模翻倍 ⇒ 耗时约 4 倍。因此扫描**不进**缺省
读面，只在调用方显式请求 `sweep_conflicts` 时计算 —— 「读一条记忆」的延迟不应取决于
库有多大。若将来要在门链里常态化，需要先加索引（按 `scope` 分桶，把 `n²` 摊到各桶）。

## 迭代日志

（**逐 cycle 一行**，不把多次修复压成散文。每行的「修复」是**真的改掉**的东西。）

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261023-095 | `1797c683` → `4b7fdf50` → `ff6deb0d` → `6db5f5b4` → `c5a15935` （**HEAD 不写进自己的台账** —— 结构必然，见 `## 两向按压`；下一个提交补记上一个）| 正反向 **14 passed**；存量聚合 **9 passed**；`tests/adapters/` + `tests/application/memory/` **266 passed**；`tests/tooling/` + `tests/application/memory/` **1829 passed / 1 failed**（唯一红 = m0 见证未重封，属记录顺序的正常态）；mypy **1319 files 无问题**；ruff check / format 全绿 | PENDING | 建档：反方向判据（新建 `goal_commit_chain.py` + `test_goal_commit_chain_reaches_the_ledger.py`，正向文件只加 import 与一条挂钩判据）+ GOAL-094 补四行 + 存量矛盾聚合（`conflict_sweep.py` + 读面可选键）+ 成本曲线 | 无（五个 EC 待收口复检） | 收口 |

## CI 台账

（**逐提交逐 job**，一个提交一行。**零 run ≠ cancelled**：`cancel-in-progress` 造成的
`cancelled` 与「同批推送被 GitHub 合并成一个 run」的 `无 run` 是**两种不同**的形态，
分别登记；后者用 `covered_by` 指名它被哪一条 run 覆盖。）

| 提交 | run | 结论 | 说明 |
| --- | --- | --- | --- |
| `1797c683` | [M0 39933470022](https://github.com/Eswink/research-system-new/actions/runs/39933470022) / [Push 39933470100](https://github.com/Eswink/research-system-new/actions/runs/39933470100) | **八 job 全 `success`**；Push `success` | 本轮全部交付面（反方向判据 + GOAL-094 补四行 + 存量矛盾聚合 + 记录 + 宪章序 63 + 阶梯「证据」行）。本地 m0 已先绿：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、0 FAILED、`tree changed during the run: False`。凭据审计四面 `offenders=0` |
| `4b7fdf50` | [M0 39939638989](https://github.com/Eswink/research-system-new/actions/runs/39939638989) | **八 job 全 `success`** | **封印提交**（只改记录）：台账补 `1797c683` 的真实 run id + 迭代日志点名它 + 状态历史追加；并对**封印后的记录树**重跑全量 m0 重封见证（24 行通过、0 FAILED、`tree changed during the run: False`）。零 run 不豁免、只改记录的提交也不豁免 |
| `ff6deb0d` | [M0 39944550344](https://github.com/Eswink/research-system-new/actions/runs/39944550344) | **八 job 全 `success`** | **只改记录**：把「`_CUTOFF_SEQ` 改 63 实测**判红**（空真守卫）而非预期变绿」这个偏差逐字写进 GOAL 与 RECHECK，并补上受判面非空的等价取证（只排除 GOAL-094 ⇒ 变绿）。零 run 不豁免、只改记录的提交也不豁免 |
| `6db5f5b4` | [M0 39951252433](https://github.com/Eswink/research-system-new/actions/runs/39951252433) | **八 job 全 `success`** | **只改记录**：补 `4b7fdf50` 的台账行与 cycle 格 —— 反方向判据在 HEAD 前移后**自己抓到了这个缺口**（它是对作者而非对 GOAL-094 生效）。这正是「链收敛」的形态：每个新提交补记上一个，只豁免 HEAD 自己 |
| `c5a15935` | [M0 39957875639](https://github.com/Eswink/research-system-new/actions/runs/39957875639) / [Push 39957875220](https://github.com/Eswink/research-system-new/actions/runs/39957875220) | **八 job 全 `success`**；Push `success` | **只改记录**：收口 tip（台账补 `6db5f5b4` + 状态历史追加 ACHIEVED）。当时它是 HEAD ⇒ 结构例外、不被自己的台账要求；**下一轮推送使它前移后，反方向判据立刻点名它**（`1 个提交不在台账（链 5 个，台账 4 个）`），本行即按该点名补记 —— 判据在作者身上生效，不是补绿 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-23 | **ACTIVE** | **建档**：承用户 goal-mode 指令（序 63）。建档实测五处缺口（见「为什么这一轮是必要的」）。`max_cycles: 14`。CI 侧历史可得性定为**方案 B**（见下）。 |
| 2026-10-23 | **ACTIVE** | **收口面落地**：EC-01…04 判据面全绿（14 + 9 例）；两向按压各判红/绿并按 raw `sha256` 逐字节复原；GOAL-094 补四行后正反向同时绿。CI 台账待推送后回填。 |

| 2026-10-23 | **ACHIEVED** | 五个 EC 全达成。**CI 到终态**：`1797c683` 八 job 全 `success` + Push `success`（[M0 39933470022](https://github.com/Eswink/research-system-new/actions/runs/39933470022)）。**本地 m0**：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24**、0 FAILED、`tree changed during the run: False`。**凭据审计**四面 `offenders=0`。**阶梯前进**：证据域升级为「写入时检测 **+** 存量可聚合」，`下一级` 收窄为「矛盾的处置闭环」。残余如实留（`W-1`…`W-4` / `R-1`…`R-3`）。 |

## CI 侧的历史可得性：选 B（并登记为残余）

**决策**：判据在**取不到链**（浅克隆）时 `pytest.skip` 并点名理由（`W-1`），
**不改** `.github/workflows/m0-quality.yml`。

**理由**（逐条）：

1. `actions/checkout` 默认 `fetch-depth: 1`（实测 `m0-quality.yml` 六处 checkout 均未声明
   depth）⇒ CI 里只有 HEAD 一个提交，任何「数这一轮有多少提交」的判据在 CI 上**空真**。
2. 加 `fetch-depth: 0` 属**基础设施改动**，而本轮授权把「改 CI workflow」列为**必须停下
   登记 BLOCKED** 的情形 ⇒ 不在本轮单方面改。
3. 因此选 B 并**如实登记**：本地真执法、CI 不执法。**需要用户决定**是否加
   `fetch-depth: 0`（那会让本判据在 CI 上同样真执法）。

**为什么不选 C**（只判「台账提交在 `git cat-file` 里存在」）：它判不出「漏记」——
漏掉的提交恰恰**不**在台账里，弱形态对它们是**恒真**的。

**`skip` 不是通过**：`pytest` 的 skip 在 `-q` 输出里可见、`-rs` 会给出理由；而**非浅克隆
下的空链会判红**（`test_the_empty_chain_is_named_not_skipped` 钉住这一点）。
