---
id: RECHECK-20261021-092
slug: goal-092-the-next-round-charter-is-read-not-remembered
title: GOAL-092 复检 —— 下一轮 charter 由上一轮的残余与阶梯机械派生（读取器 + 反证臂 + 真用一次）
status: COMPLETED
result: PASS
created_at: 2026-10-21
updated_at: 2026-10-21
plan_id: PLAN-20261021-092
parent_goal: GOAL-20261021-092
owners:
  - root-agent
verify_paths:
  - tests/tooling/test_next_round_charter.py
  - tools/next_round_charter.py
  - tools/verify_goal092_closeout.py
  - .cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md
memory_entries:
  - MEM-20261021-226
---

# RECHECK-20261021-092 — GOAL-092

## 检查结果

**PASS**。五个 EC 全部达成。交付一条**确定性读取器**（零出网 / 零模型 / 零时钟），把
「上一轮的输出 → 下一轮的 charter」从**人的记忆**换成**文件的读数**；九条拒绝臂逐条在
**合成树**上按压（改事实，不改断言）；并用它的产出一连串产物真的写了序 60 这一轮，
GOAL-091 的七条残余 **7/7** 有处置。

## 一、建档实测的三处缺口（先钉缺口存在）

| # | 缺口 | 实测读数 | 修法 |
| --- | --- | --- | --- |
| 1 | 衔接**靠人** | `.cursor/plans/goals/evidence/` 下**没有任何**「下一轮输入」类制品；历轮靠驱动方读 GOAL 报告后手写提示词 | 新增读取器，把下一轮输入变成**树内制品**（可读、可判、可复核） |
| 2 | `W-NN` 编号只是**弱约定** | GOAL-090 只有 `W-6` 一条（前面没有 `W-1…W-5`）；GOAL-091 用 `W-1…W-7` ⇒「删了一条」与「本来就少」不可区分 | 读取器显式判**连续性**（断号 ⇒ `RESIDUAL_GAP` 并**报出读到的序列**） |
| 3 | 阶梯的「下一级」**没有消费者** | `test_mainline_research_ladder_advances.py` 只判阶梯自洽，全仓**没有代码**读它当输入 | 读取器把「收录本 GOAL 的域 + 它们的下一级」逐条读进骨架 |

## 二、既有判据改动逐条申报

基线 `9a5d1214`（本轮起点）。**改动只有两处，都是纯收紧**（新增受判对象 + 合并重复注释；无一条条目被移除）：

| 文件 | `numstat`（+/-） | 改了什么 | 性质 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **+8 / −40** | `IN_SCOPE` **增加 4 条**（`next_round_charter.py` / `charter_parse.py` / `goal092_closeout_assertions.py` / `verify_goal092_closeout.py`）；同时把 `IN_SCOPE` 内 **39 行逐轮重复的登记注释**（「…EC-05：同上」/「收口验证器 + 断言集（纯收紧 ⇒ 只增不删）」）合并成 2 行 | **纯收紧 + 注释合并**。删除行**逐条核算**：基线 `IN_SCOPE` **134** 条、现在 **138** 条、**移除 0 条**、新增恰为上述 4 条；`LEGACY_OUT_OF_SCOPE` **38 条逐条相同**（程序化比对，见「七」第 4 条）。**没有**任何断言/阈值被改 |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 纯新增 | `_VERIFIERS` 增加 `tools/verify_goal092_closeout.py` | **纯收紧**：新验证器必须跑自己的断言集 |

**零改动声明**：无任何既有断言、词表、扫描面或阈值被改；`PRODUCT_ROOTS`、
m0 条数（23）、`test_mainline_*.py` 三条宪章判据、`test_python_source_limits.py`、
`test_two_tree_recheck_entry.py`、`tools/` 的既有登记条目 **一字未动**。

## 三、五条提示词判据 × 读数

| 提示词判据 | 落点 | 读数 |
| --- | --- | --- |
| 1. 对 GOAL-091 真文件跑，`W` 列表与正文逐条一致（不丢不增） | `test_the_w_list_matches_the_goal_body_verbatim` / `test_the_produced_text_carries_every_residual_and_no_summary` | 残余 **7/7**，逐条原文（含续行）相同、顺序相同；判据**自己**写了一份切分（不用被测实现的输出当期望） |
| 2. **反证**：删掉一条 `W` ⇒ 产出随之少一条 | `test_removing_the_last_residual_makes_the_output_one_shorter` / `test_output_follows_the_content_not_a_cached_list` | 删整条 `W-7` ⇒ 产物少一条且自报「共 6 条」；改写正文 ⇒ 产物跟着改；旧正文不再出现在产物里 |
| 3. **反证**：`status` 非终态 ⇒ 点名拒绝 | `test_a_non_terminal_goal_is_refused_by_name`（`ACTIVE` / `DRAFT` / `PAUSED` 三参数） | 三次都 `exit 2`、`REFUSED GOAL_NOT_TERMINAL`、点名叫到那个 status、**不创建 `--out`** |
| 4. **反证**：指向不存在的 RECHECK ⇒ 点名失败 | `test_a_missing_recheck_is_refused_by_name`（+ 归属 / 结句两条） | `REFUSED RECHECK_MISSING`；另两条：`RECHECK_NOT_THIS_GOAL`、`RECHECK_NOT_PASSING` |
| 5. **确定性**：同输入 ⇒ 逐字节相同 | `test_two_runs_on_the_same_input_are_byte_identical` / `test_writing_through_the_cli_is_binary_and_reproducible` | 两次 `sha256` 相同；落盘两次 `read_bytes()` 相同且都不含 `\r` |

**另有四条提示词未点名但同族的拒绝臂**（都是「静默跳过」的形态）：
`RESIDUAL_GAP`（删 `W-2` 留断号 ⇒ 报出 `[1, 3, 4, 5, 6, 7]`）、`LADDER_NOT_RECORDED`
（阶梯无域收录本 GOAL）、`RESIDUAL_EMPTY`（残余节清空且无「无残余」标记）、
`NEXT_ID_INVALID`（下一个编号形态非法）。

## 四、产物与「真用一次」的读数

**产物**：`.cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md`
`sha256:2776ad06134269876a384f163dbe9aba4500f962b64da275bd8a0d23cbd17024`
（两次独立运行 `sha256` 相同）。

**它读出的事实**（进产物）：

- 残余 **7 条**（`W-1`…`W-7`），逐条原文；
- 阶梯：命中 **复检** 一行（`下一级` = 「评审的判词驱动下一轮修订…」）；
- CI 台账：**6 行** = 全 success **5** + 无 run **1** + 判红 **0** ⇒ 结论「全绿」。

**七条残余的处置**（全部进 GOAL 的「上一轮残余的处置」表，逐条见该节）：

- **做掉 2 条**：`W-6`（见证看不见未跟踪文件）⇒ 本轮**先 `git add` 全部受判文件再跑门**；
  `W-7`（脚本进射程后才被判）⇒ 本轮四个新脚本/收口资产**从第一行起**就在 `IN_SCOPE` /
  `_VERIFIERS` 里；
- **承接 1 条**：`W-4`（中转站瞬时失败打掉一位评审者）⇒ 读面已如实点名 `UNKNOWN`；
- **不做 4 条**：`W-1` / `W-2` / `W-3` / `W-5`，各给理由（前三条属产品结构改动或人判，
  第四条是**事实性边界**）。

## 五、两向按压（真装上的读数）

| 项 | 按压形态 | 读数 |
| --- | --- | --- |
| 产物是读出来的（不是硬编码） | 删整条 `W-7` | 产物少一条 + 「共 7 条」→「共 6 条」 |
| 同上（第二向） | 改写某条残余正文 | 产物里出现 `PROBE-REWRITTEN-BODY`，旧句消失 |
| 拒绝不产半成品 | 三种非终态 | `exit 2` 且 `--out` 文件**不存在** |
| 复检的**归属**也要判 | 改 `parent_goal` | `RECHECK_NOT_THIS_GOAL` |
| 复检的**结论**也要判 | 改 `result: REVISE` | `RECHECK_NOT_PASSING` |
| 编号连续性 | 删 `W-2` 但不改编号 | `RESIDUAL_GAP` 并报出读到的序列 |
| 阶梯记账 | 宪章阶梯行改指别的 GOAL | `LADDER_NOT_RECORDED` |
| 判定面不得被工具代填 | 读产物 | `objective: <待填：判断>` 逐字在场 |
| CI 读数是分类不是假设 | GOAL-091 真台账 + 一份含「判红」的合成台账 | 前者「全绿」；后者 `red == 1` 且结论「有判红」 |
| 口径与宪章判据同源 | 同一份宪章两边各读一次 | 阶梯行**逐条相同**、进展记录**行数相同** |

## 六、m0 与见证（顺序纪律的两种工作树形态）

**顺序**（本轮**先 add 再跑门**，这是 `W-6` 的直接回应）：

```text
写全部记录（GOAL / PLAN / RECHECK / MEM / 阶梯 / 程序表 / 进展 + 修订 / 归档 / 战役级核算）
  → git add 全部受判文件（含**新增**的 13 个文件）
  → 记录面判据（tests/architecture/python + tests/tooling）
  → 最后跑 tools/run_m0_with_witness.py
  → 之后不再 git add 任何受判文件
  → 提交推送
```

**读数**（正式见证 `.cursor/plans/goals/evidence/M0-WITNESS.json` 与 runner 日志）：

| 项 | 读数 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks` |
| `PASS [` 行数 | **24** |
| `FAILED` | **0** |
| `tree changed during the run` | `False` |
| 见证覆盖 | **4556** 个受判面文件（`--verify-only` 退出码 `0`） |

**CI 到终态**：见 GOAL「CI 台账」逐提交逐 job —— 前两轮各判红一次（都是**见证与树的绑定**
问题、都是我造成的树状态），最终 tip 八 job 全 `success`。

## 七、既有缺陷 / 真实发现（本轮）

1. **残余节的形状比想象的复杂**：GOAL-091 的残余节后面还跟着 `R-1…R-3` 一组，
   它们的**续行同样是缩进的** ⇒ 若不显式「非缩进行结束当前条」，最后一条会把残余风险
   整段吞进去。首版实现与首版判据辅助函数**都**踩了这个坑（判据先红，实现随后修）。
   这不是判据设计问题，是**真实形态**：记录里的「一组条目 + 另一组条目」共用缩进续行。
2. **规模门在写下时就咬住**：`next_round_charter.py` 首版 517 行 > 450 ⇒ 拆分出
   `charter_parse.py`（纯解析原语）。这**正是** `W-7` 想要的效果：脚本从第一行起就在
   射程内，门在**写完时**而不是「登记时」就判。
3. **收口断言集的函数也受 50 行门约束**：`_delivery_verdicts` 首版 52 行 ⇒ 拆成
   `_face_verdicts` / `_guard_verdicts`。**只有全量门抓得到**这一条（定向套件当时全绿）。
4. **登记清单把承载它的判据文件顶过 450 行**（`W-7` 的同族、但**方向相反**）：
   `IN_SCOPE` 加 4 条后 `test_tooling_scripts_meet_product_gates.py` 变成 **456 行**
   ⇒ 规模门判红。第一次的修法（把清单整体搬进新文件 `tests/tooling/tools_gate_scope.py`）
   被**另一条既有判据正确地判红**：`goal031/032/038` 三个历史断言集按**字面量**在
   原文件里读 `IN_SCOPE`（`module_literal(text, "IN_SCOPE")`）⇒ 搬家等于让它们
   全部失配。**那三条断言没有错**（它们问的是「本轮脚本是否在清单里」，位置是它们**当时**
   的事实）。⇒ **改用不做搬家的修法**：把 `IN_SCOPE` 内 **39 行逐轮重复的登记注释**
   （每条只写「同上」/「纯收紧 ⇒ 只增不删」）合并成 **2 行**，条目**一条不动**。
   读数：`+8 / −40`，基线 **134** 条 → 现在 **138** 条、**移除 0 条**、
   `LEGACY_OUT_OF_SCOPE` **38 条逐条相同**（程序化比对：`set` 差集为空、legacy 元组相等）。
   这是「**先试小改动、被真判据拦住就换道**」的一次实测，也是既有判据**有效**的证据。

## 七之二、CI 首轮判红（如实登记：**本地绿、CI 红**，根因在见证的内容面）

**首轮提交 `9326c788`**：`M0 Quality Gates` **2/8 job 判红**（`quality-ubuntu-latest` /
`quality-windows-latest`），两者同一个判据：

```text
FAILED tests/tooling/test_m0_witness_matches_the_tree.py::test_the_witness_is_for_the_tree_we_are_looking_at
  见证记录的 HEAD: 9a5d1214…；当前 HEAD: 9326c788…
  内容变了/新增（0 项）：[]
  见证里有而当前没有（1 项）：[('tests/tooling/tools_gate_scope.py', '')]
```

**根因**（不是判据错，是**我自己造成的树状态**）：本轮中途试过把 `IN_SCOPE` 清单整体搬进
新文件 `tests/tooling/tools_gate_scope.py`（为绕开 450 行门），该文件一度被我 `git add`；
发现历史断言集按字面量读原文件后**回退了这个方案**并删除了文件。但**当时的见证**记住了
它的名字（`sha256: ''` = 「被跟踪但工作树已删除」这一态）⇒ 本地那一次 `--verify-only`
读的是同一份见证与同一棵树，自然「覆盖成立」；CI 检出的是**提交后的树**，那个文件
**从未被提交** ⇒ 见证里有、树里没有 ⇒ 判据（正确地）判红。

**这一条同时复证了两件事**：

1. `W-6` 的形态**依然真实**（见证看不见「未跟踪」，但它**看得见**「曾跟踪后又删除」
   —— 那是 `files` 里 `sha256: ''` 的那一条）；
2. 「本地绿 ≠ CI 绿」的理由**具体可指**：见证绑定的是**内容清单**，而本地那棵树的内容
   与见证**互相自洽**（一起含那个空哈希条目）。**唯一可靠的取证是另一种工作树形态**
   —— 这次是 CI 本身。

**修法**（不碰判据）：重新跑一次 `tools/run_m0_with_witness.py`，让见证对着**没有那个
文件**的树重写。读数：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、
0 FAILED、`tree changed during the run: False`、覆盖 **4554** 个受判面文件
（上轮 4555，差的那一个正是被删的文件）、`--verify-only` 退出码 `0`。

## 八、残余风险与未覆盖范围

见 GOAL 正文的「残余与未覆盖范围（逐条）」与「战役预算触顶登记」两节 —— 本复检不重复，
但**逐条确认它们都在**：`W-1`…`W-5`（本轮自己的未覆盖面）、`R-1`…`R-3`（残余风险）。

## 结论

**PASS_WITH_WARNINGS 的两条已升为 PASS**，但以下三点如实保留、不夸大：

1. 读取器只覆盖**战役级**迭代；**产品内**「模型据上一轮结论提出新问题」仍无判据，
   且仍被 GOAL-082 EC-04 的未决取舍卡住。**不声称**迭代域的产品内那一面有进展。
2. `W-NN` 编号连续性是**新加的纪律**：历史 GOAL（如 GOAL-090 只有 `W-6`）直接喂进
   读取器会判 `RESIDUAL_GAP` —— 那是**正确**行为（无法区分「少一条」与「本来就少」），
   但意味着读取器只适用于**按新纪律写的** GOAL。
3. CI 台账的「全绿」是**按行分类**的机械读数，不独立取证 CI 本身。

**不得据此宣称项目安全**（`R-M1` 未收口）；投递语义**不是**「恰好一次」。
