---
id: PLAN-20261030-101
slug: goal-101-narrative-quality-and-verifier-coverage
title: GOAL-101 子计划 —— 叙述质量弱口径 + 验证器主文件负判扫描 + run 归属校验
status: DONE
created_at: 2026-10-30
updated_at: 2026-10-30
parent_goal: GOAL-20261030-101
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: >-
  .cursor/plans/rechecks/RECHECK-20261030-101-goal-101-narrative-quality-and-verifier-coverage.md
memory_entries:
  - .cursor/memory/entries/MEM-20261030-234-false-negatives-live-on-the-wrong-face.md
---

# PLAN-20261030-101

## 背景与靶子

序 68（GOAL-100）的残余 `U-2` 把「叙述质量与事实一致性无判据」连续第四轮登记下来
（承 096 `U-1` → 097 `U-2` → 099 `W-5` → 100 `U-2`），它同时是阶梯「报告」行的 `下一级`。
本轮把它做成**可机械判的弱口径**，并顺手按住两处**记录面结构腐化**（都是「判据绿着而
资产坏了」那一类）。

### 靶子 1（核心）：叙述质量的可机械判口径

**建档实测**：`packages/application/deliverable/manuscript.py` 的 `validate_manuscript`
只判四件事 —— 八键齐备 / 正文无数字（引用标记除外）/ 引用不越界 / 无孤儿引用。
**没有一条判「写得对不对」或「`[2]` 是否真的支持那句话」。**

**做法**（三条，全部确定性纯函数：零出网 / 零模型 / 零时钟）：

1. **引用—主张相关**：`Results` 至少带一个 `[n]`，且每条被引条目的 `title` 与正文
   共享至少一个实词（去停用词后）。**射程**：只说「不是无关」，**不说**「支持」。
2. **节间不重复**：`abstract` 与 `conclusion` 的归一化句子集合不重合。
3. **节非空洞**：每节（`title` 除外）词数 ≥ 8 —— 阈值**实测而来**（三套夹具八节实测
   下界 9 词），不是拍脑袋。

**分层（做的时候定下的取舍）**：品质判据挂**装配面**（`assemble_manuscript`），
**不**塞进 `validate_manuscript`。理由（实测）：塞进结构入口会让「编号越界」这类结构用例
因为夹具正文写得短而红 —— 第一版接到 `validate_manuscript` 上就产生 **5 处**连带红，
判词指向了错误的面。分开后两类判负各自点名、互不掩蔽。

### 靶子 2：验证器主文件里的断言不在负判扫描面内

**建档实测**：`test_closeout_verifiers_run_their_own_assertions.py` 的负判扫描**只跑**
`assertion_verdicts(root, toolbox)` 模块，而 `progress-records-this-goal` /
`progress-row-names-the-recheck` 住在 `verify_goal0NN_closeout.py` **主文件**里。
实测后果：**14 个验证器各 2 条假负 = 28 条**，全部「绿在扫描面外」。

修法（**先修后扩**，否则扩面即全红）：

1. 读取面提为共享 helper `tools/charter_progress.py`（活跃面**或**归档；按**行的形状**认，
   不按小节标题 —— 实测 082…087 四份归档没有小节标题）；
2. 17 个验证器改走 `TOOLBOX.progress_rows`（此前 098 曾手工加过一次归档回退，只有它有）；
3. 新增 `tests/tooling/test_verifier_main_files_report_no_negative.py`：主文件侧面的
   负判扫描 + 射程下界 + 一条**两向**反证臂（归档里 ⇒ 绿；两处都没有 ⇒ 红）。

### 靶子 2.5：charter 读取器连续三轮的同一拒绝码

**建档实测**：`charter_parse._W_ITEM` 只认 `- **`W-N`**`（加粗），而本仓 **87/109**
条残余写的是不加粗形态 ⇒ GOAL-098/099/100 **三轮**各自登记过 `REFUSED RESIDUAL_EMPTY`。
修法：两种形态都认（加粗仍照旧解析），附回归钉 + 反证臂。

### 靶子 3（余量）：run 归属的机械校验

同一族错误**第四次**出现（096/097/099/100）。`tools/check_ledger_run_attribution.py`：
读 `## CI 台账` 的**那一张表**，对每行断言「某个 run 的 `head_sha` 以本行提交开头」
**或**「本行显式带 `covered_by`」。**出网面** ⇒ 默认门不跑，`--online` 才查 GitHub；
静态判据 `test_ledger_run_attribution_stays_offline.py` 钉住「不在默认门 + 顶层不 import
网络库 + 静态模式零出网」。

## 完成的工作

| WP | 内容 | 判据 |
| --- | --- | --- |
| WP1 | `manuscript_quality.py`（三条判据 + `NOT_JUDGED`） | `test_manuscript_quality.py` 21 passed |
| WP2 | `docs/architecture/MANUSCRIPT_QUALITY.md`（判什么 / 不判什么 / 为什么可机械判） | docs-consistency PASS |
| WP3 | 装配面接入（`validate_manuscript_quality`） | 测试里**源码级**钉住那一行调用 |
| WP4 | `tools/charter_progress.py` + 17 个验证器改造 | 逐验证器 `--verdict-only` ⇒ 0 FAIL |
| WP5 | 主文件负判扫描 + 两向反证臂 | `test_verifier_main_files_report_no_negative.py` 4 passed |
| WP6 | `charter_parse` 残余两形态 | `test_next_round_charter.py` 21 passed |
| WP7 | `check_ledger_run_attribution.py` + 静态判据 | 8 passed；在线读数存档 |
| WP8 | `test_record_locators_are_unambiguous.py`（两条方法纪律） | 6 passed |
| WP9 | 收口资产（验证器 + 断言集 + 两处登记） | `verify_goal101_closeout.py` 0 FAIL |
| WP10 | 宪章记账（序 69 / 阶梯 / 两表各 3 行） | mainline 四件判据全过 |

## 做的时候发现的事实（如实登记）

1. **夹具被新判据打红 5 处**：那些夹具用 `T1` / `T2` 这种两字符假标题、且整篇正文
   每节同一句话 —— 新判据**正确地**打红了它们。处置：改**夹具**（用真形状的标题与
   互不相同的节），**不改判据**。这是本轮「按压不是放宽」的具体例子。
2. **在我自己修 `covered_by` 解析时误报过 3 轮**（同一本台账里找不到覆盖者 /
   覆盖者不是后代 / 明写无 run 却挂着 run）。每一次都是我读台账的**面**不对
   （读了状态历史当台账 / run 链接其实指向覆盖者 / `covered_by` 用了等号形态）——
   不是台账错。修的是**解析器**，并且每次都在文档里写清「为什么这条不是放宽」。
3. **6 条真实台账缺陷**（在线读数）：GOAL-091 三行（`7f5446ab` 名下挂着 `eff7c34d`
   的 run 两条 + `aec28e2c` 无 run 无 covered_by）、GOAL-099 三行（`covered_by` 写成
   `<HEAD>` 占位符）。**本轮不改写历史台账** —— 只登记读数（改历史 = 编造当时的事实）。
4. **编号口径矛盾**：本轮提示词标题写「序 69 / GOAL-101」，正文 §二/§七 写「序 70 /
   GOAL-102」。按仓库实况（程序表 68 行、GOAL 编号 1…100 全占用、GOAL-102 不存在）判为
   **序 69 / GOAL-101**，并在 GOAL 正文里写明这条更正与判据。

## 验收条件

| # | 条件 | 证据 |
| --- | --- | --- |
| 1 | 叙述质量 ≥2 项落地（含引用—主张对齐），各带反证臂 | `tests/application/test_manuscript_quality.py` 21 passed |
| 2 | 口径文档在树 | `docs/architecture/MANUSCRIPT_QUALITY.md` |
| 3 | **真的被装配路径调用** | 装配面 `validate_manuscript_quality(sections, facts.references)`；源码级判据 + 真文件按压 |
| 4 | 17 个验证器 0 假负；扫描覆盖主文件；共享 helper | `test_verifier_main_files_report_no_negative.py` 4 passed；逐验证器 0 FAIL |
| 5 | 一条反证臂（断言失配 ⇒ 判红） | 同文件 `TestTheMainFileCriterionBites` 两向 |
| 6 | run 归属校验器 + 静态判据 + 10 GOAL 读数 | `test_ledger_run_attribution_stays_offline.py` 8 passed；在线读数存档 |
| 7 | 两条方法纪律成了机械判据 | `test_record_locators_are_unambiguous.py` 6 passed |
| 8 | 收口资产 + 两处登记 | `verify_goal101_closeout.py` 67 判词 0 FAIL |

## 实施清单

- [x] WP1 `manuscript_quality.py`（三条纯函数 + `NOT_JUDGED`）
- [x] WP2 `docs/architecture/MANUSCRIPT_QUALITY.md`
- [x] WP3 装配面接入（`validate_manuscript_quality`）+ 分层（结构入口不带品质判据）
- [x] WP4 `tools/charter_progress.py` + 17 个验证器改造
- [x] WP5 主文件负判扫描 + 两向反证臂
- [x] WP6 `charter_parse` 残余两形态 + 回归钉
- [x] WP7 `check_ledger_run_attribution.py` + 静态判据 + 在线读数
- [x] WP8 `test_record_locators_are_unambiguous.py`（两条方法纪律）
- [x] WP9 收口资产（验证器 + 断言集 + `_VERIFIERS` / `IN_SCOPE` 登记）
- [x] WP10 宪章记账（序 69 / 阶梯弱口径 / 两表各 3 行 / ALL_PLAN）

## 证据

| 类别 | 命令 | 读数 |
| --- | --- | --- |
| 品质判据 | `pytest tests/application/test_manuscript_quality.py` | 21 passed |
| 手稿系回归 | `pytest tests/application/test_manuscript_{assembler,assembly,reference_order}.py` | 全过 |
| 主文件负判 | `pytest tests/tooling/test_verifier_main_files_report_no_negative.py` | 4 passed |
| 验证器清单 | `pytest tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 11 passed |
| run 归属 | `pytest tests/tooling/test_ledger_run_attribution_stays_offline.py` | 8 passed |
| 方法纪律 | `pytest tests/tooling/test_record_locators_are_unambiguous.py` | 6 passed |
| charter 读取器 | `pytest tests/tooling/test_next_round_charter.py` | 21 passed |
| 收口验证器 | `python -B tools/verify_goal101_closeout.py --root . --verdict-only` | 67 判词 / 0 FAIL |
| 宪章四件 | `pytest tests/tooling/test_mainline_*.py tests/tooling/test_record_tables_are_structurally_sound.py` | 全过 |
| 全量 mypy | `python -B -m mypy` | 1370 源文件干净 |

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-30 | IN_PROGRESS → **DONE** | 十个 WP 全部落地；两条真文件按压均翻向且逐字节复原；17 个验证器从 28 条假负收到 0 |

## 影响报告

- **Domain / API / schema 变化**：**无**。本轮不新增表 / 列 / DTO / 路由；`validate_manuscript`
  的签名与判词一字未改（品质判据是**另一个入口**）。
- **安全 / 凭据变化**：**无**。`check_ledger_run_attribution.py` 只读 `GH_TOKEN` 或
  `git credential fill` 的已存凭据，**不写**任何凭据；它**不在**默认门。
- **兼容性 / 迁移风险**：**无迁移**。既有夹具改了 5 处（真形状标题 / 各节不同），
  那是**夹具**不是契约；合同的 `research_manuscript` 措辞一字未改。
- **上游版本影响**：**无**（未新增依赖）。
- **可观察的行为变化**：手稿装配多了一道品质门 —— 正文与引用完全无关时，
  报告相交 `EXECUTION_FAILURE` 并点名条号（此前会静默出一份「结构合规」的稿）。

## 可复用事实

1. **分层比合并更安全**：把品质判据塞进结构入口，会让结构用例因夹具正文短而红（实测 5 处）；
   拆成两个入口后两类判负各自点名。
2. **「归档是正常结果」必须写进断言**：只读活跃面的断言，在归档惯例下必然产生假负。
   共享 helper + 「活跃面**或**归档」是唯一不漂移的写法。
3. **读台账要窄到那一张表**：`## CI 台账` 小节里常有别的表，按「反引号哈希开头」收行
   会把状态历史当台账（实测 4 条假红）。
4. **判据收紧前先看夹具**：三条新判据一上来打红 5 处既有夹具 —— 先判断「夹具不真实」
   还是「判据错」，本轮全部是前者。

## 残余

与 GOAL 正文的「残余与未覆盖范围」一致（`W-1`…`W-4` / `U-1`…`U-3` / `R-1`…`R-3`），
不在此重复。最要紧的一条：**叙述质量的强口径仍未判**。
