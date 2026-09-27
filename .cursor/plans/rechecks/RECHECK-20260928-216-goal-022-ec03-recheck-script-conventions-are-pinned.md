---
id: RECHECK-20260928-216
slug: goal-022-ec03-recheck-script-conventions-are-pinned
title: GOAL-022 EC-03 独立复检：六条口径 4/6 有机械判据 + AST 声明确实存在 + INDEX 登记 + 按压两红与逐字节复原
plan_id: PLAN-20260928-215
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-216 — GOAL-022 EC-03（复检脚本规范）

## 检查结果

**复检口径**：不复用 PLAN 的叙述；每项给出**可复核观察面**。**未实跑的不记通过**。

### 一、交付面

| # | 观察 | 结果 |
| --- | --- | --- |
| 1.1 | 规范页 `docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md` | 在位；raw `sha256` = `d80446dee9653aafa42646f2d08c9db9e182dd487e4eb1567b4ed0f6be5b73cc` |
| 1.2 | 判据 `tests/architecture/python/test_recheck_script_conventions_are_pinned.py` | 在位；raw `sha256` = `d37381b4a4eac13c2f66da75c5108994520d3772e986cd3190f6bf4c49ed3888`；`ruff format --check` clean、`ruff check` passed |
| 1.3 | 定向套件 | **6 passed** |
| 1.4 | 新增依赖 | **零**（判据只用标准库 `ast` / `pathlib`） |

### 二、六条口径的覆盖（逐条可判）

| # | 口径 | 检查形态 | 结果 |
| --- | --- | --- | --- |
| 2.1 | ① 共用解释器 | 判据（行为） | `test_both_trees_use_the_same_interpreter` **在位** |
| 2.2 | ② `--verdict-only` 纯度 | 判据（行为） | `test_impure_output_is_refused_not_filtered` **在位** |
| 2.3 | ③ 文本 vs 二进制读写 | **可复跑检查** | 小节 `### ③ 的可复跑检查` 在位；本机实测 `byte-identical False` |
| 2.4 | ④ 落点断言（`--root` 参数化） | 判据（行为） | `test_both_trees_agree_when_assertions_agree` **在位**（以任意 `tmp_path` 为树） |
| 2.5 | ⑤ 进程卫生 | **可复跑检查** | 小节 `### ⑤ 的可复跑检查` 在位 |
| 2.6 | ⑥ 路径无关输出 | 判据（行为） | `test_path_dependent_verdict_is_refused_not_normalized` **在位** |
| 2.7 | **计数** | 有机械判据者 | **4 / 6**（下界 3 ⇒ 满足「至少半数」） |

### 三、「条款不得悬空」的判法

| # | 观察 | 结果 |
| --- | --- | --- |
| 3.1 | 被点名的判据如何核验 | **AST 读声明**（`ast.parse` 找 `FunctionDef`），**不**用「文本里出现过这个名字」 |
| 3.2 | 为什么这样判 | 承 `MEM-20260925-141`：文本判会被注释 / 字符串里的同名字线喂饱 |
| 3.3 | 改名会怎样 | 判据文件或测试函数改名 ⇒ `test_every_named_judge_points_at_a_real_declaration` 判红（**本节 4.1 实测**） |

### 四、按压面（复检**独立**重跑）

| # | 观察 | 结果 |
| --- | --- | --- |
| 4.1 | 把规范页的 `### ⑤ 的可复跑检查` 标题改写 | **2 failed, 4 passed**：`test_items_without_a_judge_carry_a_reproducible_check` + `test_every_item_is_covered_by_either_a_judge_or_a_check` 同时判红 |
| 4.2 | 逐字节复原 | 规范页 raw `sha256` 与按压前**一致**（`d80446de…`） |
| 4.3 | 复原后复跑 | **6 passed** |

### 五、INDEX 登记

| # | 观察 | 结果 |
| --- | --- | --- |
| 5.1 | 本页登记 | `docs/INDEX.md` 的 Architecture 节含 `architecture/RECHECK_SCRIPT_CONVENTIONS.md` |
| 5.2 | 顺带发现并补登记 | `architecture/LOCAL_GATE_PROTOCOL.md` **此前未登记**（同族遗漏）⇒ 一并补上，**未改该文档内容**（其被 `test_record_face_is_covered_by_the_gate.py` 点名的一节**一字未动**） |
| 5.3 | `DOCS-CHECK` | `DOCS-CHECK PASS: 6 deterministic checks`（新增登记未触发 backtick-ref 判红） |

### 六、零改动面

| # | 观察 | 结果 |
| --- | --- | --- |
| 6.1 | 六个受保护判据（自 `2f87812` 起） | 全部 **UNCHANGED** |
| 6.2 | `LOCAL_GATE_PROTOCOL.md` 被点名的那一节 | **未触碰**（只补了一行 INDEX 登记） |
| 6.3 | 产品代码 / 依赖 | **零**改动 |

### 七、本次复检**未**复核的面

- EC-01 / EC-02 / EC-04 **不在**本复检范围（各由自己的 RECHECK 承载）。
- **m0 全量门**不在本脚本内跑（按 MEM-145 顺序，记录写完之后单独跑）。
- **判据在 Linux 侧**未逐条复验（会跑在 CI 的 `quality-ubuntu-latest` 上）。
- **规范页第 ③ / ⑤ 条的可复跑检查**：第 ③ 条本机实测；第 ⑤ 条的 `tasklist` 检查**未**在
  本复检里独立重跑（其判据侧对应物 —— 入口超时连整棵树杀 —— 由 EC-01 的入口与
  其判据覆盖）。

## 结论

**`PASS_WITH_WARNINGS`**。EC-03 的七项验收全部成立且有**实跑证据**：
规范页在树且 **INDEX 已登记**、**六条口径逐条在位**、**4/6 条有机械判据**（下界 3）、
被点名的判据按 **AST 读声明**核验（**改名即判红**）、无判据的两条**各有可复跑检查**、
**按压 2 红 + 逐字节复原**、第 ③ 条的可复跑检查**在本机可复现**。
**既有判据零改动、`LOCAL_GATE_PROTOCOL` 被点名的一节一字未动、产品代码与依赖零改动。**

**警告（如实登记）**：

- **`W-1`**：判据钉住的是**小节标题字面**与**判据函数名**。改规范页文案或重命名测试函数
  会判红 —— 那是**预期**（条款不得悬空），但代价是**改文案要同步改判据的映射**；
  这是刻意的耦合，不是缺陷。
- **`W-2`**：`test_at_least_half_of_the_items_have_a_mechanical_judge` 的**下界是 3**
  （六条的一半）。它是**规范页自定的下界**，**不是**外部标准；把某条的判据删掉换成
  「可复跑检查」仍可能让计数**恰好满足** —— 计数只保证**下限**，不保证**逐条强度**。
- **`W-3`**：第 ③ 条的可复跑检查在**非 Windows** 平台会输出 `True`（危害不出现）
  ⇒ 该条在别的平台是「不适用」而非「已验证」；本复检**只在本机实测过**。
- **`W-4`**：第 ⑤ 条的 `tasklist` 检查是**手工可复跑检查**，**没有**机械判据
  ⇒ 六条里只有 4 条被门自动覆盖。
- **`W-5`**：`LOCAL_GATE_PROTOCOL.md` 的补登记**超出 EC-03 的最小范围**（它是同族遗漏）。
  已如实登记在此；**未改该文档内容**，因此不构成对既有门禁的影响。

**未覆盖范围（承 GOAL-022 的边界，原样保留）**：读面未认证 / 多租户与 RBAC 未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）。
