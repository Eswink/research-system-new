---
id: GOAL-20261010-043
slug: closeout-recheck-assets-must-run-their-own-assertions
title: 收口复检资产**自身**可信 —— 三处验证器声明自己的断言集却加载 037 的那份（自有断言**从未运行**），且 GOAL-040 的断言集**今天直接崩溃**（按文本匹配已被正当改签名的调用）
status: ACHIEVED
created_at: 2026-10-10
updated_at: 2026-10-10
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-10-10 用户会话指令（goal 模式，MAINLINE 战役常驻入口）：本 GOAL 是 MAINLINE
    程序表**序 11**，由本次 replan 的**实测读数**驱动（本次触发要求：「若勘察发现更实的缺口
    ⇒ 优先它，并附复核命令与读数」）。authorization 原文要点：
    (0) **授权承继（2026-10-06 用户明确下放全部权限给驱动、只保留总目标）**⇒ 本战役的授权
    边界由驱动自定，仍受仓库宪法约束（AGENTS.md §2/§3/§5/§7/§9/§10/§11/§12/§13/§14、
    `.cursor/rules/` 20/21、`goals/README.md` 的 GOAL 格式契约、本 frontmatter 的
    forbidden / escalation_triggers）。**关键区分写死**：「权限下放」= **可以决定**
    （含改产品语义、新增判定种类），**不等于**可以放宽**判据、门禁、阈值或断言**。
    (1) **立题依据（实测，见「事实层结论」）**：(a) `tools/verify_goal038/039/040_closeout.py`
    **声明** `ASSERTIONS = "tools/goal0NN_closeout_assertions.py"` 却**加载**
    `goal037_closeout_assertions.py` ⇒ 三处的**自有断言从未在收口复检里运行**
    （实测：`verify_goal040_closeout.py --verdict-only` 的 73 条判词里，其自有断言名
    命中 **0**）；(b) 直接调用 `goal040_closeout_assertions.assertion_verdicts` ⇒
    **`ValueError: substring not found`** —— 它按**文本**匹配
    `_non_success_terminal(program, existing, last)`，而 GOAL-041 已**正当地**给该函数加了
    `programs` 形参 ⇒ 复检资产**随被引代码演进静默失效**（红的方式还是**崩溃**，不是判负）。
    (2) **为什么这属于质量轴**：轴定义是「产出的**可判定性**：结论有来源支持 / 实验可复现 /
    覆盖充分，且与评审联动」。**收口复检资产本身**就是「结论有来源支持」那条链的承重件 ——
    它若**没跑**或**崩了**，前面所有 GOAL 的「独立复检 PASS」都会退化成**未经检验的宣称**。
    (3) **本 GOAL 只做这一条**（不做数量目标）：让**复检资产自身可执行、可自证、不随被引代码
    静默失效** —— 三处加载面修正 + 崩溃面修正 + **机器判据**钉住「声明与实载一致」。
    (4) **明确不做**（已决定，不再重开）：默认 runtime 改真 / 读面认证 / 多租户·RBAC·
    BOLA·BFLA / D 组审批通道 / `G24-5` 运行时拦截器 / 部署面验证 / `R26-2/3/4/6` /
    把 destructive 能力改 allow / 为凑数扩承接面 / 放宽任何既有判据的断言 /
    宣称项目安全（`R-M1`）/ 宣称投递语义为「恰好一次」（**明确否认**）。
    **另外明确不做**（本轮特有）：**不重写**任何历史 GOAL 的 `latest_recheck` 结论
    （已收口的 GOAL 状态是历史事实）；**不**追溯宣称「当时那轮复检无效」——
    只把**今天**可判的事实修好并登记残余。
    (5) **全局禁令（贯穿全 GOAL，触犯即 BLOCKED）**：**放宽任何既有判据的断言**；
    **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**）；
    **让「加载错断言集」静默通过**（那正是本轮要消灭的形态）；
    **把崩溃当成「判负」**（复检资产必须可执行 —— 崩了就不是判据）。
    (6) **改既有判据的申报纪律（承 `MEM-20261009-210`）**：任何对**既有**判据文件的改动必须
    ① 逐条枚举改动面；② `git diff --numstat` 删除行读数；③ 逐条比对谓词是否等同；
    ④ 收窄受判面**显式申报**，**不得**称「强度不变」；⑤ 属同轮同步集之外 ⇒ 在 RECHECK 里如实登记。
    (7) **来源与授权口径**：来源 = 用户授权 + push-to-main-for-CI 口径（只推 `main`、
    **不 force**、**不重写历史**、**不推旁支**）；默认姿态不变（默认 runtime **Fake**、
    默认 CI **离线**、观测隐私按 AGENTS.md §10）。
    (8) **边界（承继）**：GOAL-001…042 全部**只读**（003/011 BLOCKED，其余 ACHIEVED）；
    GOAL-018 的 13 项 `D-NN` 已结清、**不重开**；GOAL-019…042 的未覆盖范围**原样保留**；
    GOAL-042 的 `T-1`…`T-3` / GOAL-041 的 `S-1`…`S-3` / GOAL-040 的 `R-1`…`R-3` /
    GOAL-039 的 `Q-1`…`Q-3` / GOAL-038 的 `P-1`…`P-3` / GOAL-037 的 `O-1`…`O-5` /
    `R26-*` 终态**原样保留**，本轮**只追加**。
objective: >-
    让 MAINLINE 序 11（质量轴）落成**复检资产自身可信**：① **勘察定稿** —— 实测三处
    「声明 / 实载不一致」与 GOAL-040 断言集的崩溃（读数逐条，含崩溃类型与消息）
    → ② **加载面修正** —— 三处验证器改为加载**自己**的断言集（与 GOAL-041/042 的既有形态
    对齐），改后**仍能跑完** → ③ **崩溃面修正** —— `goal040_closeout_assertions.py` 不再按
    **文本**匹配易漂移的调用签名：改为**结构判据**（AST / 与签名无关的特征），使其在
    GOAL-041 已改签名之后**仍可执行**（受判面**只许等价或更宽**，不得借机放宽）
    → ④ **机器判据钉住形态** —— 新增判据：**每个收口验证器「声明的断言集」必须等于
    「实际加载的」**，且**被点名的每个断言集必须可执行**（`assertion_verdicts` 能在本树
    跑完不崩）⇒ 该形态**在构造上不可能再通过** → ⑤ **自举收口**（复用既有机器）。
    **硬约束**：不复核历史 GOAL 的终态；受判面**非空**；判据**两向**（该红时红 / 不该红时不红）；
    m0 条数**仍是 23**；判词归档**进树**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**）。
exit_criteria:
  - id: EC-01
    criterion: >-
      **勘察定稿（读数逐条）**。(a) **声明 / 实载不一致**：逐条给出六个验证器「声明的
      `ASSERTIONS`」与「`_load_assertions` 实载的文件名」对拍（037/041/042 一致；
      **038/039/040 不一致**）；(b) **自有断言从未运行**：实测
      `verify_goal040_closeout.py --verdict-only` 的判词里其自有断言名命中 **0**；
      (c) **崩溃实测**：直接调用 `goal040_closeout_assertions.assertion_verdicts` ⇒
      `ValueError: substring not found`（点名其按文本匹配的锚点
      `_non_success_terminal(program, existing, last)` 与真实源码
      `_non_success_terminal(program, existing, last, programs)` 的差异）；
      (d) 可复用的缝：GOAL-041/042 的 `self-loads-its-own-assertions` 自指判词形态。
    verify: >-
      `rg -n "^ASSERTIONS = " tools/verify_goal0*_closeout.py` 与
      `rg -A2 "def _load_assertions" tools/verify_goal0{38,39,40}_closeout.py`（逐条对拍）；
      `uv run --frozen --no-sync python -B tools/verify_goal040_closeout.py --root . --verdict-only`
      ⇒ 判词里自有断言名 **0** 命中；直接调用 `assertion_verdicts` ⇒ **崩溃**（逐字消息）。
    status: PASS
  - id: EC-02
    criterion: >-
      **加载面修正（三处）**：`verify_goal038/039/040_closeout.py` 改为加载**各自**的断言集；
      三处改后**仍能跑完**（不因加载新断言集而红）且**自有断言真的出现在判词里**
      （逐条点名：断言名命中数 ≥ 该断言集的条数下界）。若暴露为 FAIL ⇒ 修断言集的
      **可执行性**，**不得**放宽谓词迁就。
      **建档时的子句已修正（如实登记，不淡化）**：初版写的是「判词数**只增不减**」——
      实测该子句**不成立**且**不该成立**：换加载面必然改变判词数（037 的断言集 **34** 条、
      038/039 各 **21** 条、040 **20** 条）⇒ 修正后 goal040 的判词数 **73 → 59**（变**少**）。
      真正的要求是「**跑自己的**断言」而不是「条数变多」；原写法把**正确的收窄**误判成缺陷。
      组合覆盖不丢失：037 的 34 条由 **037 自己的验证器**继续运行。
    verify: >-
      三个验证器在本树各跑一次 ⇒ 均**不崩溃**且**各自的自有断言名在判词里命中**
      （`ec02-three-new-kinds` / `scope-declares-this-rounds-scripts` 等）。
    status: PASS
  - id: EC-03
    criterion: >-
      **崩溃面修正（语义稳定的判据）**：`goal040_closeout_assertions.py` 里按**文本 index**
      匹配调用签名的判据改为**结构判据**（AST 或与签名无关的特征）；
      受判面**等价或更宽**（逐条比对说明书里的谓词；**不得**借机放宽）。
    verify: >-
      直接调用 `assertion_verdicts` ⇒ 跑完不崩；逐条谓词比对写在 RECHECK 里。
    status: PASS
  - id: EC-04
    criterion: >-
      **机器判据钉住形态（该形态不可能再通过）**：新增判据 —— ① 对**每个**收口验证器，
      「声明的断言集路径」必须**等于**「`_load_assertions` 实载的路径」（AST 读，不靠文本巧合）；
      ② **被点名的每个断言集**必须可执行（能在本树调通 `assertion_verdicts` 不抛异常）。
      **两向**：造一个合成的「声明 A 实载 B」形态 ⇒ 判据**必须报红**；真实树 ⇒ 绿。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling -q` ⇒ 全绿 + 新用例。
    status: PASS
  - id: EC-05
    criterion: >-
      **自举收口（复用既有机器）**。① 收口验证器进树并加入
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`（**纯收紧**）；
      ② 两树复检（`--script-mode shared` + `--base-ref`）+ 判词归档进树（**二进制写盘**、`CR=0`）；
      ③ as-is m0 **23/23**（在**全部记录写入之后**，独占、仓库 `.venv`、不接管道）；
      ④ 治理 `validate.py` 绿 + `tests/tooling/test_mainline_program_is_intact.py` 绿
      （**本 GOAL 的 id 已在程序表序 11**，进展记录行指向真实 RECHECK 文件）；
      ⑤ CI 台账**逐提交**；⑥ 承继残余逐条在位；⑦ 未覆盖范围逐条明写。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal043_closeout.py --root .
      --verdict-only` ⇒ 全 PASS / 0 FAIL；`tools/two_tree_recheck.py --script-mode shared
      --base-ref <含交付面的提交>` ⇒ `TWO-TREE PASS`；as-is m0 终局行
      `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度（含 `xfail` / 条件跳过式规避）
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - >-
      **让「加载错断言集」静默通过**（本轮要消灭的形态）；**把崩溃当成「判负」**
      （复检资产必须可执行 —— 崩了就不是判据）
    - >-
      **重写任何历史 GOAL 的 `latest_recheck` 结论**（已收口的 GOAL 状态是历史事实）；
      **追溯宣称「当时那轮复检无效」**（只把今天可判的事实修好并登记残余）
    - >-
      **同轮同步面**：仅当本轮修正**必需**时，允许对**既有**登记面做**加法 / 搬迁登记**
      （谓词、阈值、受判形态一字未改），并**逐条枚举进本清单**。
    - >-
      **改既有判据的申报纪律（承 `MEM-20261009-210`，逐条自证）**：任何对**既有**
      判据 / 测试文件的改动必须 ① **逐条枚举**改动面；② 用
      `git diff --numstat <base> HEAD -- <file>` 给出**删除行读数**；③ **逐条比对谓词是否
      等同**（不得只写「强度未降」—— 那是一句**需要自证**的断言）；④ **收窄受判面必须
      显式申报**（写明收窄了什么与理由），**不得**称「强度不变」；⑤ 属**同轮同步集之外**
      的形态 ⇒ 命中 `escalation_triggers`，在 RECHECK 里**如实登记**。
    - >-
      **宣称项目安全**（`R-M1` 未收口）；**宣称投递语义为「恰好一次」**（**明确否认**；
      口径只能是 at-least-once + idempotency + deduplication）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
  - 需要改**同轮同步集以外**的既有判据断言
child_plans:
  - .cursor/plans/tasks/PLAN-20261010-369-goal-043-ec01-04-closeout-assets-run-own-assertions.md
  - .cursor/plans/tasks/PLAN-20261010-371-goal-043-ec05-self-bootstrap-closeout.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-372-goal-043-ec05-self-bootstrap-closeout.md
memory_entries: []
---

# GOAL-20261010-043 — 收口复检资产自身可信

> **主线归属**：`.cursor/plans/goals/MAINLINE.md` 程序表**序 11**（轴 = **质量**；依赖序 10 ——
> 已 ACHIEVED）。**本行是 replan 的产物**（`replan_every_goals: 3` 在序 8/9/10 收口后到期），
> 已在 MAINLINE「修订记录」留痕。

## 目标与退出标准

五条 EC 的机器可检定义见 frontmatter `exit_criteria`（官方口径以那里为准，本节只做导览）：

| EC | 主题 | 一句话判据 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 勘察定稿 | 六处验证器「声明 vs 实载」逐条对拍（038/039/040 不一致）+ 自有断言 0 命中 + 崩溃实测 | PASS |
| EC-02 | 加载面修正 | 三处改为加载**各自**的断言集；改后**跑完不崩**且**自有断言真的在判词里**（判词数必然**变少** —— 见 EC-02 的修正登记） | PASS |
| EC-03 | 崩溃面修正 | 按文本 index 匹配调用签名的判据改**结构判据**；受判面等价或更宽 | PASS |
| EC-04 | 机器判据钉住 | 「声明 == 实载」+「被点名的断言集可执行」；**合成反例必红** | PASS |
| EC-05 | 自举收口 | 验证器进树 + 两树 + 归档 + m0 23/23（记录之后）+ 治理绿 + 宪章判据绿 + 台账逐提交 | PASS |

**全局禁令（贯穿全 GOAL）**：不得**放宽任何既有判据的断言**；不得让**加载错断言集**静默通过；
不得把**崩溃**当成判负；不得**重写历史 GOAL 的复检结论**；不得宣称项目安全（`R-M1`）；
不得宣称投递语义为「恰好一次」（**明确否认**）。

## 事实层结论（建档勘察；**每条都有复核命令与读数**）

> 全节读数在**仓库 `.venv`** 下取得（`uv run --frozen --no-sync`）。

### 1. 现状：三处验证器**没在跑自己的断言**

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 1.1 | 声明与实载**不一致**（逐条对拍） | `rg -n "^ASSERTIONS = " tools/verify_goal0*_closeout.py` + `rg -A2 "def _load_assertions" …` | `037`/`041`/`042` **一致**；`038`/`039`/`040` **不一致**（都实载 `goal037_closeout_assertions.py`） |
| 1.2 | **自有断言从未运行** | `uv run … tools/verify_goal040_closeout.py --root . --verdict-only` | 判词里其自有断言名（`ec02-three-new-kinds` 等）命中 **0** |
| 1.3 | 自有断言**本身**是绿的（不是坏判据，只是没跑） | 直接调 `goal037/038/039` 的 `assertion_verdicts` | `037`: 34 条 / FAIL **0**；`038`: 21 条 / FAIL **0**；`039`: 21 条 / FAIL **0** |
| 1.4 | **GOAL-040 的断言集今天崩溃** | 直接调 `goal040_closeout_assertions.assertion_verdicts(root, toolbox)` | **`ValueError: substring not found`** |
| 1.5 | 崩溃根因（逐字） | `tools/goal040_closeout_assertions.py:151` vs 源码 | 它 `runner.index("_non_success_terminal(program, existing, last)")`；而 GOAL-041 已**正当**把该调用改成 `_non_success_terminal(program, existing, last, programs)`（多轮推进需要）⇒ **文本匹配随被引代码演进静默失效** |
| 1.6 | 已有**自指**判词的形态（可复用） | `tools/verify_goal041_closeout.py` / `verify_goal042_closeout.py` | 各带 `self-loads-its-own-assertions`（读自身源码判加载面）⇒ **本轮把它一般化并钉住全部收口验证器** |

### 2. 可复用的缝

| # | 事实 | 命令 / 落点 | 读数 |
| --- | --- | --- | --- |
| 2.1 | 断言集的公开面统一 | 每个 `tools/goal0NN_closeout_assertions.py` | `assertion_verdicts(root, toolbox) -> list[VerdictLike]` |
| 2.2 | 验证器的加载面统一 | 每个 `tools/verify_goal0NN_closeout.py` | `ASSERTIONS` 常量 + `_load_assertions()`（**本轮要钉的就是这两者的相等**） |
| 2.3 | AST 读判据的既有手法 | `tools/closeout_recheck_tools.py` | `defines` / `module_literal`（按 AST 读，不靠文本巧合） |
| 2.4 | `tools/` 四道门的射程清单 | `tests/tooling/test_tooling_scripts_meet_product_gates.py::IN_SCOPE` | 逐条显式登记（**只增不删**） |

### 3. 判据面现状（改动前先数）

| # | 事实 | 落点 | 读数 |
| --- | --- | --- | --- |
| 3.1 | 收口验证器共 6 个（037…042） | `tools/verify_goal*_closeout.py` | 037/038/039/040/041/042 |
| 3.2 | 本轮**预期**改动面 | 三处 `verify_goal0{38,39,40}` + 一处 `goal040_closeout_assertions.py` + 新增判据 + `IN_SCOPE` | 逐条枚举进 RECHECK（含 `numstat`） |
| 3.3 | **不**改历史 GOAL 的复检结论 | `.cursor/plans/goals/GOAL-0{38,39,40}*.md` / 各自 RECHECK | 只读；本轮**不**触碰 |

### 4. 本轮**不**碰的面（逐条明写）

- 已收口 GOAL 的终态与复检结论（历史事实，**不重写**）；
- 三处断言集**内容**的既有谓词（只改**可执行性**，不放宽）；
- 读面认证 / 多租户 / 部署面 / D 组审批通道 / `R-M1`（未覆盖范围原样保留）。

## 决策登记（逐条状态）

| # | 决策 | 状态 |
| --- | --- | --- |
| ① | 三处加载面怎么修 | **已定**：改为加载**各自**的断言集（与 041/042 的形态对齐） |
| ② | goal040 崩溃面怎么修 | **已定**：把**文本 index** 判据改为**结构判据**（AST / 与签名无关的特征），受判面**等价或更宽** |
| ③ | 判据钉在哪 | **已定**：`tests/tooling/`（新增判据：声明==实载 + 被点名断言集可执行；**合成反例必红**） |
| ④ | 历史结论 | **已定**：**不**重写；只登记「今天是可判事实」与残余 |
| ⑤ | 承接面 | **不动**（不需要新能力） |

## 循环入口协议（幂等重入）

驱动方进入时，按「迭代日志」最后一行 + 工作树/远端实况判定续点（与 `goals/README.md`
同一条协议）：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件；**同时只允许一个驱动持有 ACTIVE GOAL 的推进权**。

## 单 cycle SOP

- **① derive**：从剩余 EC 圈定最小主题；写子 PLAN（`parent_goal: GOAL-20261010-043` +
  投影 `ALL_PLAN`）。
- **② 执行**：每 WP 独立 commit，**只用显式路径**，**绝不** `git add -A`。
- **③ 本地验证**：先写记录 → 立刻跑治理 → 记录面判据 → 全量门；m0 按组、**独占**、
  仓库 `.venv`、`uv run --frozen --no-sync python -B`、**不接管道**；受影响定向套件
  （`tests/tooling`）。
- **④ commit**；**⑤ push + CI**（仅 main、不 force、批量推送、逐提交台账）；
  **⑥ 纠错**；**⑦ 记录 + 下一轮**。

**本轮特有纪律**：**复检资产必须可执行**（崩了不是判据）；**声明必须等于实载**；
受判面**只许等价或更宽**；**不重写历史结论**；**改既有判据必须走自证清单**
（`MEM-20261009-210`）；受判面不得是交集（承 `MEM-160`）；留档二进制写盘、判词归档进树；
台账逐提交；新记录落地后立刻跑治理。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷；修产品优先，**禁改断言迁就** |
| flake/env | 已知签名（OTLP 端口、teardown race、DSN 注入、fake-IP、`evolution_state` WinError 5、共享 DSN 污染、draft-contract 顺序） | 按既有配方重跑 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 / **Docker registry 5xx 或限流**（`execution image not found`） | 等窗口重跑 1 次；仍败 → 记录三条取证后 BLOCKED |
| 治理/安全门禁 | validator / Mimosa / 记录面判据 | 修或登记；**不得绕过** |
| 资源阈值型偶发 | CI 上 RSS 类阈值偶发红 | 分类 (ii)：`rerun-failed-jobs`；**绝不动阈值** |
| 快照漂移 | OpenAPI / 结构签名类 | **按生成器重新生成** |

## 终止与收口

- **ACHIEVED 前置**：五条 EC 全 `PASS` + 独立 RECHECK `PASS`/`PASS_WITH_WARNINGS` +
  本文件收口；收口动作照 `MEM: goal-closeout-procedure` 并声明 `verify_paths` ≥ 2 路、
  **用本 GOAL 的工具自举**跑收口复检。
- **BLOCKED**：命中 `escalation_triggers` 或 `budget.max_cycles` 触顶（20）。
- **ABORTED**：用户明确取消目标。
- **no_progress_stop_cycles = 2**：连续 2 个 cycle 未推进任何 EC ⇒ 停并记 BLOCKED。

## 残余与受限面（承继 + 本轮）

### 承继残余（原样保留，不重开）

`R-M1`（未宣称项目安全）；`G24-5`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
GOAL-037 的 `O-1`…`O-5`；GOAL-036 的 `M-1`…`M-5`；GOAL-035 的 `N-1`…`N-6`；
GOAL-034…032 的 `W-*`；历史 `tools/` 目录仍有旧 lint 与无机器门的旧脚本；
GOAL-019…042 的未覆盖范围原样保留。

### `R26-*` 终态表（承继，逐条保持）

| 项 | 终态 | 理由 |
| --- | --- | --- |
| `R26-1` 死信人工恢复 | **GOAL-032 + GOAL-033 收口** | 本轮不动 |
| `R26-5` 应用级消费者 | **更正已落**（GOAL-032 EC-02） | 按偏移量物化的消费者仍不存在 |
| `R26-2` / `R26-3` / `R26-4` / `R26-6` | **保持** | 条件不满足 |
| `R26-7` / `R26-8` | **保持** | 树外证据 / GOAL 正文投影 |

### 本轮新增残余（收口时逐条定格；`U-1`…`U-3`）

- `U-1`（**只修三处 + 加判据，不重跑历史收口复检**，未覆盖）：本轮让**今天**的加载面
  与可执行性正确并**钉住形态**；**不**重跑 GOAL-038/039/040 的收口复检（那要重建当时的
  树状态；且历史结论不重写）。
- `U-2`（**部分闭合**：三个实例全修 + **一类**已机器化）：`goal031`（字面量搬家）/ `goal038/039/040`（加载面）/ `goal040`（调用签名漂移）三处已修；新判据 `test_every_named_assertion_set_reports_no_negative_on_this_tree` 让「**断言集在本树上有判负**」**可被机器发现**（不要求条数不变、不禁文本锚点本身）。**未覆盖**：断言集内部仍可能用文本锚点 —— 只是它们**当前**没有失配；本判据**不**禁止这种写法。
- `U-3`（**`tools/` 射程之外的旧脚本仍无机器门**，未覆盖；承历史登记）：只对 `IN_SCOPE`
  里逐条登记的脚本有四道门。

### 未覆盖范围（逐条明写，不得据此宣称安全）

**读面未认证**；**多租户未做** / **RBAC 未做** / **BOLA·BFLA 未做**（M18 deferred）；
**部署面未验证**；**D 组审批通道未接通**（`external.publish` / `package.install` /
`git.commit` / `workspace.delete` 触达即 BLOCKED）；**`R-M1` 未收口**；`G24-5` 未做；
**`R26-2/3/4/6` 未做**；**应用级按偏移量物化的消费者仍不存在**；**不得**据此宣称项目安全；
**不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
deduplication）。

### 本 GOAL 两条「已收口 vs 未覆盖」分界（逐条明写）

- **复检资产可靠性**：**已收口** = 六处收口验证器的「声明 == 实载」+ 被点名断言集**可执行**，
  且该形态由**机器判据**钉住；**未覆盖** = 历史收口复检的重跑（`U-1`）与旧脚本射程（`U-3`）。
- **崩溃面**：**已收口** = GOAL-040 的断言集改结构判据后可执行且受判面等价或更宽；
  **未覆盖** = 其它历史断言集里可能存在的同类文本锚点（`U-2`）。

## CI 台账（逐提交）

> 口径：无 `gh` CLI ⇒ `git credential fill` 取令牌走 REST API，按 `head_sha` 遍历全部 run
> + `/jobs`；**空集合 = 未取证**；`cancelled` 如实登记 + 原因 + `covered_by`。
> **自我指涉边界**：台账提交自身不产生可引用的 CI 结论（明写并以「末条提交 + 覆盖说明」
> 封闭，**不得循环引用**）。

| commit | run/结论 | 备注 |
| --- | --- | --- |
| `59c0e31`（replan + 建档） | `38010532994` **Push on main / CodeQL success**；`38010533708` **M0 cancelled** —— `cancel-in-progress`（被 `d709f3c` 的推送取消）⇒ `covered_by 38011239724` | 程序表序 11 + 五 EC + 事实层读数 |
| `d709f3c`（cycle 1 = EC-01…EC-04） | `38011239724` **M0 success**（8 job 全 success）+ `38011239702` **Push on main / CodeQL success** | 加载面 + 崩溃面（AST）+ 机器判据；本地 m0 23/23（5325 passed） |
| `637ce67`（cycle 2 提交 A = EC-05 首轮） | `38012945487` **M0 failure** —— **真红且已修**（见下）| 验证器 + 断言集 + `IN_SCOPE` |
| `f1ca193`（cycle 2 提交 B = 两树归档） | **无自己的 run**（同批推送） | 两份判词归档进树；⇒ `covered_by 38015753637` |
| `90ad612`（cycle 2 · **GOAL 收口** = 本批 HEAD） | `38015753637` **M0 success**（8 job 全 success）+ `38015753446` **Push on main / CodeQL success** | **GOAL 收口提交**；覆盖 `637ce67` / `f1ca193` 的代码面；**实测取证** |

### `637ce67` 的那次 red：**真红**（不是基础设施），且由**我自己的新判据**抓出

**逐字**：`FAILED tests/tooling/test_closeout_verifiers_run_their_own_assertions.py::test_the_verifiers_list_partitions_every_verifier_explicitly - AssertionError: ('这些验证器没被分类（新增时必须显式决定）', ['tools/verify_goal043_closeout.py'])`

**成因**：本轮新增了 `tools/verify_goal043_closeout.py`，但**忘了把它登记进 `_VERIFIERS`** ——
正是**本轮刚立的射程分区判据**把它报了出来（**判据当场兑现价值**）。
**处置**：登记 + 把清单下界 `_MIN_VERIFIERS` 12 → 13；本地复跑 7 passed、**全量 m0 23/23**；
`90ad612` 的 CI **M0 success** 复取证。**未动任何阈值 / 未放宽判据**（只补登记）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | `PLAN-20261010-373`（收口后补正） | （见 CI 台账） | **第三个实例（收口后新实测）**：`goal031_closeout_assertions.py` 的 `ec03-run-completed-carries-the-skip-facts` 按**文本**要求在 `phase_runner.py` 里出现 `"skipped"` —— 而 GOAL-042 EC-03 把该载荷抽成**唯一构造点** ⇒ 字面量**搬了家**（行为逐字保持）⇒ 该判据**盯错位置**判负（实测：goal031 验证器 1 条判负）。**处置**：改**结构判据**（`_run_completed_carries_the_skip_facts`：接受两种形态，任一缺 ⇒ 判负）⇒ goal031 **80 判词 / 0 判负**；并把该**类**机器化 —— 新判据 `test_every_named_assertion_set_reports_no_negative_on_this_tree`（**断言集在本树上不得有判负**）+ P-3 按压（改回纯文本 ⇒ 必红）；**13 个验证器现全部可执行且 0 判负** | （见 CI 台账） | — | `U-2` 的**一类**已闭合（文本锚点失配可被机器发现）；`U-1`/`U-3` 仍登记 | GOAL 收口维持 |
| 2 | `PLAN-20261010-371` | `637ce67` / `f1ca193` | EC-05 五条 AC 全 PASS：收口验证器 **57 判词 / 0 FAIL**（标准断言集**一行未重写**；判词集**逐条覆盖**本 GOAL 的 EC：加载面三处 + 结构判据两条 + 机器判据三条主函数名）+ `IN_SCOPE` **纯收紧**（+2 行；判据 8 passed）+ **两树 `TWO-TREE PASS`**（两路 **57 判词** / `sha256` 相同 `85688b62…`）+ 归档定格（两份各 **2094 B / 57 行**、`CR=0`）+ 治理 + 宪章判据 + **as-is m0 23/23**（5325 passed, 228 skipped）| （见 CI 台账）| **两处判据自纠**：子串搜索误判 docstring 引述 ⇒ 改 AST 且排除 docstring；区间写法与逐条匹配打架 ⇒ 取首尾锚点 | 五条 EC 全 PASS；GOAL 收口。**m0 抓到并已修一处**（我自己的新判据抓到我自己的漏登记：新增 `verify_goal043` 未进射程清单 ⇒ `partitions` 判据报红 ⇒ 登记 + 下界 12→13）| GOAL 收口（`RECHECK-20261010-372`）|
| 1 | `PLAN-20261010-369` | （见 CI 台账） | EC-01…EC-04 全 PASS：**复检资产自身可信** —— ① 勘察读数（六处验证器声明/实载对拍 ⇒ 038/039/040 不一致；自有断言 0 命中；goal040 断言集崩溃）；② **加载面修正**（三处改为加载各自的断言集）⇒ 三处验证器各跑通（goal038/039 各 60 PASS、goal040 59 PASS，**0 FAIL**），且**自有断言名真的出现在判词里**；③ **崩溃面修正**：goal040 的文本 index 判据改 **AST 结构判据**（`_first_call_line` 按被调名取行号，与实参无关）⇒ 不再随签名演进崩溃，受判面等价（仍要求两者都在场）；④ **机器判据**（新增 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`，**7 passed**）：声明==实载（AST 读，含两种世代形态）+ 被点名断言集**可执行** + **射程分区不得漏项**（031…042 在射程 / 015·023…030 逐条登记为旧一代，理由非空）；⑤ 两向反证 **P-1/P-2 全红**（P-1 复现历史加载缺陷 / P-2 复现崩溃缺陷）+ 二进制复原 raw `sha256` 一致 + 归档进树（110 B / `CR=0`）；⑥ **如实修正建档子句**：EC-02 初版写「判词数只增不减」—— 实测**不成立且不该成立**（换加载面必然改变条数：037=34 / 038=39=21 / 040=20 ⇒ 73→59），已改为「**跑自己的**断言」并把该修正写进 EC-02 正文 | （见 CI 台账）| 门抓到我的两处行宽 + 一处格式 ⇒ 已修 | EC-05（自举收口）待做 | cycle 2（EC-05 收口）|
| 0 | —（replan + 建档） | （见 CI 台账） | 只读勘察（0 改动）+ **两条实测读数**（六处验证器声明/实载对拍 ⇒ 038/039/040 不一致；`goal040` 断言集**崩溃** `ValueError: substring not found`）；五条 EC 全 PENDING；MAINLINE 程序表**新增序 11** | （见 CI 台账） | — | 五条 EC 全 PENDING；加载面/崩溃面的修法（①②）待 cycle 1 落 | cycle 1（EC-02 加载面 + EC-03 崩溃面 + EC-04 判据） |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | ACHIEVED（+ 收口后补正 cycle） | **收口后新实测到第三个实例并当场修**：`goal031` 的断言按文本要求在 `phase_runner.py` 找 `"skipped"` 字面量，而 GOAL-042 把该载荷抽成**唯一构造点**（行为逐字保持、字面量搬家）⇒ 盯错位置判负。**已修**为结构判据（接受两种形态）⇒ goal031 **80 判词 / 0 判负**；并把该**类**机器化（新判据：断言集在本树**不得有判负**）+ P-3 按压必红。**13 个收口验证器现全部可执行且 0 判负**。**不重写历史结论**；`U-1`/`U-3` 仍登记。 |
| 2026-10-10 | ACHIEVED | **GOAL 收口（cycle 2 = EC-05 自举收口）**：五条 EC 全 PASS。收口面 = 验证器 + 本轮断言集进树（复用标准断言集**一行未重写**）、`IN_SCOPE` **纯收紧**、两树 **`TWO-TREE PASS`**（两路 **57 判词** / `sha256` 相同 `85688b62…`）、判词归档进树（两份各 2094 B / 57 行 / `CR=0`）、as-is m0 **23/23**（记录写完之后：5325 passed, 228 skipped）、治理 + 宪章判据绿、CI 台账逐提交。**一处时序如实登记**：两树首轮红（bootstrap：归档在提交之后才存在）。**收口后不再推进本 GOAL**；残余 `U-1`…`U-3` 与未覆盖范围逐条明写；**不得**宣称项目安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。独立复检：`RECHECK-20261010-372`（PASS_WITH_WARNINGS）。 |
| 2026-10-10 | ACTIVE | **cycle 1（EC-01…EC-04）收口**：**复检资产自身可信** —— 三处验证器（038/039/040）此前**声明自己的断言集却加载 037 的那份** ⇒ 自有断言从未运行；**已修**为加载各自的断言集（三处现各跑通：60/60/59 PASS、0 FAIL，自有断言名真的出现在判词里）；**并修崩溃面**：GOAL-040 的断言集按文本匹配一个已被正当改签名的调用 ⇒ `ValueError: substring not found`；改为 **AST 结构判据**（按被调名取行号）⇒ 不再随签名演进失效。**新增机器判据**（声明==实载 + 断言集可执行 + 射程分区不漏项，7 passed，含两种世代形态）；两向反证 P-1/P-2 全红 + raw `sha256` 复原一致。**一处建档子句如实修正**：EC-02 初版「判词数只增不减」实测不成立（换加载面必然改变条数）⇒ 改为「跑自己的断言」。EC-05 待收口。**不得**宣称安全（`R-M1`），**不得**宣称投递语义为那四个字（**明确否认**）。 |
| 2026-10-10 | ACTIVE | **replan + 建档（cycle 0）**：MAINLINE 程序表**新增序 11**。只读勘察 + **两条实测读数**：(a) `verify_goal038/039/040_closeout.py` **声明**各自断言集却**加载** `goal037_closeout_assertions.py` ⇒ 三处自有断言**从未运行**（实测 goal040 验证器判词里其自有断言名 **0** 命中）；(b) 直接调 `goal040_closeout_assertions.assertion_verdicts` ⇒ **`ValueError: substring not found`**（按文本匹配一个已被 GOAL-041 正当改签名的调用）⇒ 复检资产**随被引代码演进静默失效**。五条 EC 全 `PENDING`。**不做数量目标**；**不重写历史结论**；**不得**据此宣称项目安全，**不得**宣称投递语义为「恰好一次」（**明确否认**）。 |
