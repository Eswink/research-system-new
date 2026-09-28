---
id: RECHECK-20260929-244
slug: goal-025-ec04-closeout
title: GOAL-025 EC-04 复检：收口验证器进树 + 射程纯收紧 + 标准断言集复用（含自举复检与残余面）
plan_id: PLAN-20260929-243
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-244 — GOAL-025 EC-04 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
关键结论用**第二条路径**复核（判词集直接跑一遍 + 逐条读断言源码）。**未实跑的不记通过**。

## 检查结果

### 1. 收口验证器进树并入必备清单（AC-1）
- 交付：`tools/verify_goal025_closeout.py`（**447 行**）—— 复用
  `tools/closeout_recheck_assertions.py` 的公共判词（`standard_verdicts` / `Verdict` / `emit`），
  只写 GOAL-025 特有断言；**不重写**公共面一行。
- **四道门（本验证器）**：`ruff format --check` = `1 file already formatted`；
  `ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 1 source file`；
  规模 **447 行**（≤450）且**无超 50 行函数**。
- **射程纯收紧**：`tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE`
  由 **4 → 5** 条（新增本验证器）；该判据的「必备清单 ⊆ 推导射程」断言**单调**
  （只增不减）⇒ 收紧不是放宽。三件套（射程门 / 断言集在树 / 两树入口）**25 passed**。
- **自举复检（当前树）**：`uv run … python -B tools/verify_goal025_closeout.py --root . --verdict-only`
  ⇒ **37 判词**（标准面 18 + 本轮特有 19）。收口前唯一一条红是
  `ec04-latest-recheck-resolves`（`latest_recheck` 尚未指向本文件）；本文件落地后该条转绿。

### 2. 残余与未覆盖面（AC-4）
- 验证器**逐条断言**：12 条承继残余（`R-M1` / `R-D1` / `R-B1` / `R-N1` / `R-F1` / `R-F2` /
  `W-4` / `W-5` / `W-6` / `W-10` / `W-11` / `W-12`）+ 本轮六条 `G24-1`…`G24-6`
  （其中 `G24-4` / `G24-5` 必须同时出现「需用户拍板」）+ 五条未覆盖范围
  （**读面未认证** / 多租户 / BOLA / 部署面未验证 / **R-M1 未收口**）逐条出现在 GOAL 正文里。
- **读法**：这些断言只证「登记**在位**」，**不**证「残余已被解决」—— 两者是不同命题。

### 3. 按压（本验证器自身必须先红后绿，承 MEM-141 / MEM-152）
- **基线**：`--root . --verdict-only` ⇒ **37 PASS / 0 FAIL（EXIT=0）**。
- `V1` GOAL 的 `EC-02` 状态由 `PASS` 改成**未终态取值** ⇒ `FAIL ec04-ec01-to-ec03-are-pass ->`
  `未终态：[…]`（失败消息逐条点名三个 EC，其中 `EC-02` 那一项即被按压的取值；36 PASS / 1 FAIL；
  **逐字判词**见留档 `scratch/goal025-ec04-press-matrix.log`）。
- `V2` GOAL 的 `latest_recheck` 指向不存在的路径 ⇒ **两条**红：标准面的
  `FAIL records-declare-existing-rechecks ->`（点名该 GOAL）与本轮的
  `FAIL ec04-latest-recheck-resolves ->`（35 PASS / 2 FAIL）⇒ 说明标准面**也**覆盖了这一条。
- `V3` 派生面塞入未登记框架路由 `/__press-probe` ⇒ `FAIL ec03-derived-face-equals-the-registry ->`
  `派生面有而清单没有：['/__press-probe']` 且 `FAIL ec03-derivation-floors-are-pinned ->`
  `下界 40 / 快照 GET 64 / 框架 5`（35 PASS / 2 FAIL）。
- **逐字节复原（raw `sha256` / 二进制读写）**：GOAL 回到
  `a079de569a0674c96a4fa95f1a28229c55099ed2a970c14319688e111a1b4cd2`、派生面回到
  `ae9bf121fdc4f4b1ae15e488d13d8f1707bc2b9a4dce5ef7bc12e6ed1f3aa888`（两处 `MATCHES_BASELINE True`）
  ⇒ 复绿 **37 PASS / 0 FAIL**。证据 `scratch/goal025-ec04-press-matrix.log`（**二进制写盘**）。
- **读法**：按压施加在**被判对象**上（GOAL 状态 / 复检路径 / 清单字面量），
  不是「改验证器源码让自己的断言变红」⇒ 证的是「验证器真的在读树」。

### 4. 两树与终态（AC-2 / AC-3）- **两树复检**：干净 checkout 必须是**已提交的收口树** ⇒ 该步在收口提交之后跑，
  结果以「收口补记」落 GOAL 迭代日志与状态历史（`TWO-TREE PASS` / 逐行相同 / `sha256` 相同）。
- **as-is m0**：见 GOAL 迭代日志与状态历史（终态行 `PASS: profile=m0; 23 deterministic checks`，
  **记录写入之后**才跑）。
- **治理**：`validate.py` = `Cursor 治理验证通过`。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的四条验收（验证器进树并入射程 / 两树同结论 / as-is m0 与治理、
台账到终态 / 残余与未覆盖逐条）全部有实跑证据；GOAL-024 收口时登记的四条未证伪面
（`G24-2` 响应头面 / `G24-6` 正控制 / `G24-3` 白名单可派生性 / `G24-1` 四源）在本 GOAL 内
**收口或收窄**，其中 `G24-1` 的**真实 runtime / 工具面**部分仍为待取证项。

**警告（如实留位，不消解）**：

- `W-1`：收口验证器断言的是**登记面与形状**（清单分区 / 条数下界 / 集合相等 / 状态取值），
  **不是**「这些判据在真实环境里不再会红」。它是**自洽性**判据，不是安全性判据。
- `W-2`：`ec03` 的「派生面 == 人工清单」是**重算**（读树内快照 JSON 与两处 AST 字面量），
  但**不执行**被判据模块自己的函数 ⇒ 若某判据模块内部逻辑被改坏而清单不变，
  本验证器**看不见**（那由该模块自己的判据负责）。
- `W-3`：五条未覆盖范围与 12 条承继残余都是**在位断言**（字符串出现）——
  「登记在位」不等于「已处置」；GOAL-018 已结清的 13 条 `D-NN` 不因本 GOAL 而被重新验证。
- `W-4`：本 GOAL 的四条交付都在**默认离线链**（Fake runtime + SQLite 域存储）上成立；
  真实 runtime / 真实工具面 / 真实中转站 / 部署面（K8s、配置了快照根的环境）仍**未验证**。
- `W-5`：`G24-4`（`LineageNodeDto.label` 字段语义）与 `G24-5`（把隐私条款做成运行时拦截器）
  **本轮未处置**（需用户单独拍板）⇒ 二者**原样保留**。
- `R-M1` 未收口：**不得**据此宣称项目安全；本复检只覆盖被点名判据在本机默认离线链上跑到的那几面。
