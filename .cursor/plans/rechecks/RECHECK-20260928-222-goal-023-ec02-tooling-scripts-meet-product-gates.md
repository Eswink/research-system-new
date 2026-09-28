---
id: RECHECK-20260928-222
slug: goal-023-ec02-tooling-scripts-meet-product-gates
title: GOAL-023 EC-02 复检：被点名的 tools/ 脚本真的过了四道门（真红→绿 + 三向按压各只红一道 + 射程显式分类）
plan_id: PLAN-20260928-221
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-222 — GOAL-023 EC-02 复检

**复检口径**：不复用 PLAN 的叙述；每项给出**可复核观察面**；**未实跑的不记通过**。
本轮最要紧的一件事是：**受判对象不是空的** —— 判据交付时它的第一个受判对象**本来就是红的**，
所以「判据今天真的在执法」不需要等到将来才成立（这正是 GOAL-022 `RECHECK-214` 的 `W-1`
留下的口子，承 MEM-156）。

## 检查结果

### 一、首个受判对象的「真红 → 绿」（可复跑、零写盘）

用 `--stdin-filename` 对**修复前**的提交内容复测（`git show HEAD:tools/two_tree_recheck.py`
管道进 `ruff check`），所以这条证据**不依赖**任何历史日志：

| 观察 | 修复前 | 修复后（当前树） |
| --- | --- | --- |
| `ruff check` | **1 条错误**：`complex-structure: main is too complex (14 > 10)` | `All checks passed!` |
| 超 50 行函数（AST，`end_lineno - lineno + 1`） | `[('main', 53)]` | `[]` |
| 文件行数 | 301 | 329 |
| `main` / `report` | 53 / —— | **21 / 19** |
| 既有行为判据（`test_two_tree_recheck_entry.py`） | —— | **11 passed**，断言**一字未改** |

**结论**：判据拿到的是「**真红 → 绿**」，**不是**「受判集合为空」的空真。

### 二、四道门真的机械执行（AC-1）

| 门 | 命令（既有配置原样生效） | 被测脚本集结果 |
| --- | --- | --- |
| 格式 | `ruff format --check` | 通过 |
| lint | `ruff check`（`max-complexity = 10`、行宽 100） | 通过 |
| 类型 | `mypy`（`strict = true`） | `Success: no issues found in 2 source files` |
| 规模 | AST：函数 ≤ 50 行 / 文件 ≤ 450 行 | 通过 |

**`mypy` 的豁免问题已实测关闭**：建档时实测 `mypy <被测脚本>` 稳定通过
⇒ **必须**机械执行，**没有**「不能稳定执行」的登记理由。

### 三、射程有界且分类显式（AC-2）

| 观察 | 结果 |
| --- | --- |
| 必备清单（**写在判据源码里**） | `IN_SCOPE` = `tools/two_tree_recheck.py`、`tools/closeout_recheck_assertions.py` |
| 规范页点名（**推导**） | `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` 里出现的 `tools/**.py` = 同两条 |
| 历史遗留登记 | **37** 条，**逐条带理由**（PA-1R 历史资产 / 取证探针 / 上游调研 / M12 里程碑 / GOAL-015 专属 / 历史 CLI / 实验门禁） |
| 完整性 | `tools/` 下 **39** 个 `.py` =射程内 **2** + 登记在案 **37**，**无未分类** |
| 增删显式 | `test_scope_partitions_every_tools_script_explicitly` 会对**未分类的新脚本**判红；也会对**陈旧的清单条目**判红 |
| 不扫整目录 | 实测 `tools/` 既有 `ruff check` **73 条**错误、`ruff format --check` **10 个文件**待重排 ⇒ 扫整目录等于逼改历史资产 |

### 四、反证三向 + hermetic 四门检测（AC-4）

| # | 按压 | 判据结果（`8 例` 中的红集） | 是否隔离干净 |
| --- | --- | --- | --- |
| A | 去格式化（单引号） | 仅 `test_in_scope_scripts_are_formatted` 红（`1 failed, 7 passed`） | **是**（lint 仍绿） |
| B | 重新引入复杂度（`report()` 加 9 段 if/elif ⇒ `complex-structure 14 > 10`） | 仅 `test_in_scope_scripts_pass_ruff_check` 红（`1 failed, 7 passed`） | **是**（格式 / 规模仍绿） |
| C | 把 `report()` 撑过 50 行（临时 32 行注释 ⇒ 52 行） | 仅 `test_in_scope_scripts_respect_the_size_limits` 红（`1 failed, 7 passed`） | **是**（`ruff check` 仍绿） |
| D | hermetic：`tmp_path` 人造坏脚本 | 四道门**各自**报出问题：格式 `File would be reformatted`、lint `unused-import: os imported but unused`、类型 `mypy 不通过`、规模 `有超过 50 行的函数：['broken']` | ——（不写仓库） |

**逐字节复原**：A/B/C 三次按压后，`tools/two_tree_recheck.py` 的 raw `sha256`
均回到 `1e867ea51ac575a0363d8a48236acc8013d94d9a4e00597604dbc7d2373c8dd2`；
复原后 `8 + 11 = 19 passed`。

### 五、零改动面与自洽门（AC-5）

| 面 | 结果 |
| --- | --- |
| `PRODUCT_ROOTS` | **零改动**（两处载体仍声明同一组五个根；`tools` 仍不在其中） |
| 既有 check 构成 / `.github/workflows/**` 作业结构 | **零改动** |
| m0 条数 | **仍 23**（新判据落在 `tests/**` ⇒ 仍在 `python/tests` 的收集面内） |
| 既有判据内容 | **零改动**（入口行为判据 11 例断言未改；规范钉条款判据 6 例未改） |
| 产品代码 / Domain / API / schema | **零改动** |
| 依赖 | **零新增**（判据用的 `ruff` / `mypy` 是既有开发依赖） |
| 新判据自身 | `ruff check` + `ruff format --check` + 规模门**全绿**（自洽，不靠豁免） |
| as-is m0 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`）；`PASS [` = **24**；**4658 passed / 21 skipped**（较交付前 **+9** = 新判据 **8 例** + 新文件进入规模门参数化面 **1 项**）；零 `FAILED` / `ERROR`；日志 `scratch/goal023-c2-m0.log`，文件时刻 `14:02:18` **晚于**本记录写入 `13:50:25` ⇒ 门在记录之后；跑完 `tasklist` python 进程 **0** |

### 六、本 cycle 内被自己的判据抓到的缺陷（如实登记）

新判据的**第一次自跑**判红 **`6 failed, 41 passed`**，根因**在判据自身**：
`doc_named_scripts()` 只按「前缀 `tools/` + 后缀 `.py`」取值，于是把规范页散文里的
**通配泛指** `tools/**.py` 当成了一条**真实脚本路径**加进射程 ⇒ 射程里出现一个不存在的文件 ⇒
格式 / lint / 类型 / 规模四道门**同时**判红。

- **抓到它的正是本判据自己的配对断言** `test_doc_named_scripts_exist_and_join_the_scope`
  （「点名的脚本必须存在」）⇒ 这是本判据**非空转**的一次额外实证；
- **修复**（`c2f3330`）：改为按**真实路径形态**匹配（`re.fullmatch`，不含通配符），
  并在 docstring 里写明「**通配写法不算点名**」；
- 修后 `8 passed`，`ruff check` + `ruff format --check` 绿。
- **口径**：这是**新增判据自身的缺陷**（不是产品缺陷），在**交付当轮**被发现并修掉；
  修复**未**触碰任何既有判据 / 门禁 / 阈值，也**未**为让它变绿而放宽任何检查。

### 七、本次复检**未**复核的面

- **历史遗留 `tools/` 脚本**：**仍不受任何判据覆盖**。本轮只把**被点名的** 2 条纳入射程；
  余下 37 条既无格式门也无类型 / 规模门（要收口得逐条改造历史资产 ⇒ 需另行授权）。
- **`tools/` 整体仍不在 `PRODUCT_ROOTS`**：因此若有人**不把新脚本加进清单也不在规范页点名**，
  新脚本就**逃逸**射程。本判据只保证「清单里已有的不会静默变质」，**不保证**「新脚本会被纳入」
  —— 后者靠 `test_scope_partitions_every_tools_script_explicitly` 对**未分类**判红来兜，
  但**绕过方式仍然存在**（把新脚本登记进 `LEGACY_OUT_OF_SCOPE` 只需写一行理由）。
- **`mypy` 的缓存面**：实测用的是既有 `.mypy_cache`；冷缓存下的耗时**未**单独测量。
- **跨平台**：全部实测在本机（Windows）；`ruff` / `mypy` 在别的平台上对同一文件是否同结论
  **未复验**（由 CI 的 ubuntu job 间接覆盖同一批判据，但**未**逐条对照）。
- **复杂度门的口径**：用的是 `mccabe` 的 `max-complexity = 10`；按压 B 实测 14 > 10 判红。

## 结论

**PASS_WITH_WARNINGS。** 五条验收（AC-1…AC-5）**全部成立且有实跑证据**：
四道门机械执行且对被测脚本集全绿；射程**有界且分类显式**（39 = 2 + 37，逐条理由）；
**首个受判对象是真的红的**（`main` = 53 行 / 复杂度 14 > 10）且已修掉
（`main` → 21 行，`ruff check` 转绿），既有 **11 例行为判据断言一字未改且全绿**
⇒ 判据拿到「真红 → 绿」；**三向按压各自只让一道门判红**、raw `sha256` 逐字节复原；
另有 hermetic 四门检测；新判据自洽通过既有规模与格式门；**`PRODUCT_ROOTS` / m0 条数 /
既有判据 / 产品代码 / 依赖全部零改动**。

**警告（如实登记）**：

- **`W-1`（最要紧）**：射程**只覆盖被点名的 2 条脚本**。历史遗留 **37** 条 `tools/` 脚本
  **仍然不受任何判据覆盖**（既无格式门也无类型 / 规模门）。整体口径**仍是**
  「`tools/` 不在 `PRODUCT_ROOTS`」—— 本条交付的是**有界射程里有机器门**，
  **不是**「`tools/` 已被门覆盖」。
- **`W-2`**：新脚本的纳入**不是自动的**。判据会对「**未分类**」判红，但把一个新脚本写进
  `LEGACY_OUT_OF_SCOPE`（带一行理由）就能让它继续逃逸。这防的是**静默逃逸**，
  **不是**「有人决定不纳入」——决定本身仍是显式的、需要写下来的。
- **`W-3`**：`mypy` 面用的是既有缓存；冷缓存耗时未测。跨平台同结论**未逐条复验**。
- **`W-4`**：按压用的是格式 / 复杂度 / 注释撑长三种**行为不变**的形态（Edit 做、逐字节复原）；
  **没有**做「删掉整段逻辑」这类会改变行为的按压 —— 那类按压与既有 11 例行为判据冲突，
  本判据的门也不是为此设计的。
- **`W-5`**：本条复检**不含**任何授权面 / 认证面新结论。`W-10` / `W-11` / `W-12` 与
  `R-M1` **原样保留**；**不得**引作安全结论。

**未覆盖范围（承 GOAL-023 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
