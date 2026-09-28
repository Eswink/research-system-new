---
id: RECHECK-20260928-234
slug: goal-024-ec03-boundary-clauses-pinned
title: GOAL-024 EC-03 复检：两条条款逐字落在两份文档 + 四条未覆盖面逐条在位 + 被点名判据文件存在性 + DOCS-CHECK 绿
plan_id: PLAN-20260928-233
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-234 — GOAL-024 EC-03 复检

**复检口径**：不复用 PLAN 叙述；每条给出可复核观察面（命令 / 逐字锚点 / 文件路径）；
**未实跑的不记通过**；警告逐条留位。

## 检查结果

### 1. 两条条款（AC-1）
- 锚点逐字：`条款 ①（canonical 允许持有用户输入）` / `条款 ②（非 canonical 出口不得含内容）`
  —— 两份文档**都**包含（判据 `test_the_two_clauses_are_stated_in_both_documents`）。
- **反证**：`missing_anchors("这里没有条款", CLAUSE_ANCHORS)` 实跑判红并点回两条锚点
  ⇒ 文档被编辑改坏时抓得住。
- 条款措辞与 GOAL 授权里的界线一致（canonical 允许持有用户输入；非 canonical 出口不得含内容），
  且**没有**出现「读面不得含内容」这种被 cycle 1 否决的错句（读面是白名单口径）。

### 2. 受判面与口径（AC-2）
- OBSERVABILITY 新节给出：**6 条受判出口**（OTLP traces/metrics wire、应用日志、读面响应、
  失败载荷、磁盘制品）+ **读面白名单口径** + **5 个被点名的判据文件**。
- `test_the_pinning_judge_names_itself_and_every_named_judge_file_is_referenced` 逐条核对
  「文档点名」与「文件存在」两件事分别成立。

### 3. 未覆盖面（AC-3）
- OBSERVABILITY 全称四条（`未覆盖面 1..4`）+ THREAT_MODEL 同口径四条，逐条在位。
- 四条与 GOAL 的 EC-03 文本一一对应：debug mode 受控采样 / 真实 collector 与生产部署面 /
  CI 产物面 / `R-M1`。

### 4. 零夸大与登记（AC-4）
- 零夸大锚点：OBSERVABILITY `**不作安全结论**`、THREAT_MODEL `**本节不是安全结论**`
  各一条在位；THREAT_MODEL 另带「**不得**据此宣称「项目安全」」。
- `docs/INDEX.md` 两处登记锚点在位；`tools/docs_consistency_check.py` 实跑
  `DOCS-CHECK PASS: 6 deterministic checks`。
- 既有文档节**未被改写**：只追加（`git diff` 面为纯新增；§6 授权面草案与 M15/M16 段无改动）。

### 5. 判据自洽（AC-4）
- 新判据 145 行（≤450）；`ruff format --check` / `ruff check` = `All checks passed!`；
  `mypy` = `Success: no issues found`；`tests/observability/` 全目录 **100 passed, 1 skipped**。

## 结论

**PASS_WITH_WARNINGS**。EC-03 的两条条款、四条未覆盖面、受判面口径与 INDEX 登记**逐条成立**，
且判据能对「改名 / 条款被改写」判红。**条款不悬空**：被点名的 5 个判据文件都存在且各自在跑。

**警告（逐条留位）**：

- `W-1` **锚点是逐字匹配**：条款文字一旦被"润色"（哪怕语义等价）就会判红。这是**故意**的
  （条款即契约），但代价是文档措辞变动需要同步判据 —— 记为已知摩擦点。
- `W-2` **未覆盖面只登记两条通道的"未验证"**：文档不承诺任何"将来也不会"的命题；
  真实 collector / 生产部署面仍**未验证**（`R-M1` 未收口）。
- `W-3` 本轮的"条款"是**文档 + 判据**层面的形态，**不是**运行时强制：产品代码里没有
  「非 canonical 出口不得含内容」的运行时拦截器（有的话就是新能力，超出本 GOAL 授权）。
- `W-4` 与 EC-01/EC-02 同口径的残余警告仍然有效（`RECHECK-232` 的 `W-1`…`W-7`），
  本文件不重复登记、也不消解。
- `R-M1` **仍未收口**：本文件与两份文档都**不作**任何项目安全结论。
