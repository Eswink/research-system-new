---
id: RECHECK-20261107-107
slug: four-targets
title: GOAL-107 复检 —— 四靶并行（前端补全 / 引用分布 / 外部评审面板 / 脚本执行权威）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-07
updated_at: 2026-11-07
plan_id: PLAN-20261107-107
parent_goal: GOAL-20261107-107
owners:
  - root-agent
verify_paths:
  - apps/web/src/features/reports/ManuscriptPanel.tsx
  - apps/web/src/features/projects/ProgramsSection.tsx
  - apps/web/src/api/types.ts
  - packages/application/deliverable/citation_distribution.py
  - packages/application/deliverable/manuscript_panel.py
  - packages/application/experiments/script_authority.py
  - packages/application/experiments/governed.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
  - tools/verify_goal107_closeout.py
  - tools/goal107_closeout_assertions.py
---

# RECHECK-20261107-107

## 复检范围

GOAL-20261107-107 的十四条 EC 逐条取证。**两路以上**（`verify_paths` 列出的每个文件都是
一条独立的取证路径；产品面与判据面各取一次）。

四靶的分工与各自的**射程边界**（本轮把边界写在前面，收口时逐条核对有没有越界）：

| 靶子 | EC | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- | --- |
| C 前端补全 | EC-01…03 | 后端已就绪的能力在页面上可用（改稿并排 diff、程序页三件） | 不宣称「前端功能完备」——只补这三处 |
| B 引用分布 | EC-04…05 | 一条命令算分布 + 一个明确的语料门 | **不宣称「引用充分性已判」**：三个阈值仍 `None`（n=1 < 3） |
| A 外部评审面板 | EC-06…08 | 带归因的第三方判词落既有读面，advisory | **不宣称「叙述质量已判」**：`NOT_JUDGED` 五项逐字不动，面板是另一个判者，不是确定性判据 |
| D 脚本执行权威 | EC-09…11 | `SHIPPED`/`AUTHORED` 闭集 + 既有策略约束真的生效 | **不宣称「生成级已启用」**：`AUTHORED` 出厂默认关闭，启用另需一次决定 |

## 检查结果

十四条 EC 逐条取证。**每条都给了可重跑的读数**，不是「模块存在」。

### 靶子 C｜前端补全（EC-01…03）

- **EC-01 改稿并排 diff**：`pnpm --dir apps/web test:e2e -- revision-diff.spec.ts` ⇒ 2 passed。
  ① 含 v1+v2 的 run ⇒ `revision-diff` 在场，且 `span[class*="diffAdded"]` 与
  `[class*="diffRemoved"]` **各有行**（按 class 核对 —— 行文本本身不带 `ADDED` 前缀，
  那是 `DiffLineRow` 的既有形态）；② 只有 v1 的 run ⇒ 面板**不渲染**。
- **EC-02 程序页三件**：`programs-completion.spec.ts` ⇒ 3 passed。有决定的程序逐条渲染
  `#0 CONTINUE` / `#1 STOP`，`cited_facts` 默认收起、点开逐条可见；没有决定的程序显示
  明确空态且 `[data-testid^="program-decision-"]` **计数为 0**；表单提交真的发出一次 POST。
- **EC-03 基线**：`design-outline-guard.spec.ts` ⇒ **6 passed**（含四条反证臂）；
  `design-fidelity.spec.ts` ⇒ 3 passed；`design-outlines.json` 只动 `portfolio-projects`
  一条（`git diff --stat` = 1 insertion / 1 deletion）。
- 全套：`pnpm --dir apps/web test:e2e` ⇒ **112 passed**。

### 靶子 B｜引用分布（EC-04…05）

- `pytest tests/application/test_citation_distribution.py` ⇒ **8 passed**（四条判据 + 三条门
  边界 + 短语料参数化）。
- **实测语料读数**（`tools/citation_corpus_report.py --root .`）：
  `3142b142` 57 句 / 6 标记 / 3 条；`6446406a` 39 句 / 9 标记 / 3 条 ⇒ **2 份**，
  `gate: CLOSED`（`2 of 3`）。阈值三项仍 `None`。
- 语料发现方式**不是** glob：`manuscript*.md` 实测 0 命中，真实手稿是内容寻址 blob
  （无扩展名），入口按 artifact id 的 `:manuscript.md` 后缀 + digest 取字节。

### 靶子 A｜外部评审面板（EC-06…08）

- `pytest tests/application/test_manuscript_panel.py` ⇒ **15 passed**。
- 三条 rubric 逐条对应 `NOT_JUDGED` 第 1/2/3 项；`VERDICTS` 三态闭集；未知 rubric 与空
  正文各**点名拒绝**。
- **设施失败独立一类**：`_failing_gateway()` 排三次 `PortTimeoutError` ⇒ 三条判词全是
  `PANEL_UNAVAILABLE`、`reviewer_model is None`、`is_judgement is False`；摘要把它单列。
- **advisory 边界**：`as_review_findings` 只构造 `ReviewFinding`（`review_type =
  manuscript_panel`、`reviewed_by = model:<endpoint>/<returned>`）；模块不 import
  `Decision`、不出现 `Decision(`。
- **无归因不进票**：`aggregate_panel` 把三条全列为 `ineligible`、`voters == 0`。
- §7：`test_manuscript_quality_strong_criterion.py` ⇒ **5 passed**（`NOT_JUDGED` 五项、
  §7 表格 5 行、`len(NOT_JUDGED) == 5` 全部仍绿）。

### 靶子 D｜脚本执行权威（EC-09…11）

- `pytest tests/application/test_experiment_script_authority.py` ⇒ **15 passed**。
- `AUTHORED_ALLOWED_BY_DEFAULT is False`；`AUTHORED` 未放行时点名拒绝；显式
  `authored_allowed=True` 才过（拒绝不是恒真）。
- 白名单：非闭集路径、绝对路径、`../` 三种形状全部点名拒绝；白名单命中但摘要为空 ⇒
  「carries no digest」拒绝（pin 不是摆设）。
- 三条约束各有拦住与放过两臂；`..` 即使归一后在前缀内也拒。
- **既有缺陷已闭**：`governed.py` 的 `_enforce_policy` 现在读 `evaluation.constraints` 并调
  `_enforce_constraints`；`ALLOW_WITH_CONSTRAINTS` 不再等于放行。
- 零回归：`test_experiment_script_comes_from_the_plan.py` ⇒ 17 passed。

### 收口面

- `tools/verify_goal107_closeout.py --root .` ⇒ **84 判词 / 0 FAIL**。
- 全量 m0：`PASS: profile=m0; 23 deterministic checks`、`PASS [` 24 行、0 FAILED、
  `tree changed during the run: False`。
- **两树复检 PASS**：`TREE current verdicts=84 sha256=474fcf27…` / `TREE clean verdicts=84 sha256=474fcf27…` / `COMPARE identical=True`。
- **CI 八 job 全 success**（`e1cb5f2d` 的 M0 `42386389966`）。

## 反证臂汇总（**判据咬得住**的证据）

每条都**实际按压过并确认判红**，然后复原并核回归。

| 判据 | 按压方式 | 预期 | 实测 |
| --- | --- | --- | --- |
| `test_adding_one_citation_moves_both_readings` | `marks=sum(...)` → 常量 `6` | 2 条红 | **恰好 2 条**（这条 + 摘要分布） |
| `test_the_gate_opens_exactly_at_the_declared_corpus_size` | 语料 0/1/2 三档 | 全不足 | 3 passed（参数化） |
| `test_a_gateway_failure_never_becomes_a_judgement` | 设施失败 → `SUPPORTED` | 2 条红 | **恰好 2 条**（这条 + 摘要单列） |
| `test_authored_is_off_by_default` | `AUTHORED_ALLOWED_BY_DEFAULT = True` | 1 条红 | **恰好 1 条** |
| `revision-diff.spec.ts` 第二条 | 让 v2 缺席时用 v1 顶替 | 判红 | **判红** |
| `programs-completion.spec.ts` 第二条 | 空态分支永不命中 | 判红 | **判红** |
| `design-outline-guard.spec.ts` 四条 | 注入面板 / 视口外节点 / 多一行 / 少一节点 | 各判红 | 4 条各自判红（基线未污染） |

**一次失败的反证臂尝试（如实登记）**：第一次按压改稿面板时把 `ready` 改成恒真 —— **没有
判红**，因为上层 `RevisionSection` 在 `manuscript_v2.md` 缺席时整块不渲染，那个 `ready`
根本走不到。改成按压**上层守卫**（伪造 v2）之后才咬住。这条说明「按压没红不等于判据强，
也可能是压错了地方」。

**一次夹具坑（如实登记）**：`FakeModelGatewayOptions(fail_timeout=True)` 只让**首调**失败，
而面板有 3 条 rubric ⇒ 后两次会成功并产出 `AMBIGUOUS` 判词，看起来像「设施失败被折算了」。
换成 `set_script("complete", [err] * 3)` 才建立正确前提。

## 结论

**PASS_WITH_WARNINGS**。十四条 EC 全 PASS，四靶各自的可证伪事实都在，反证臂全部按压过。

取 `PASS_WITH_WARNINGS` 而不是 `PASS` 的理由（四条残余都是**射程边界**，不是缺陷）：

1. **`W-1`**：引用阈值仍 `None`（语料 2 of 3）。本轮交付的是「有语料就能标定」的命令，
   不是阈值本身 —— 差的那一份语料要靠下一次真实 run。
2. **`W-2`**：面板是 advisory；它给的是「某个模型认为」，不是「论证成立」。
3. **`W-3`**：`AUTHORED` 出厂关闭；本轮到「可被安全放行」为止，启用另需一次决定。
4. **`W-4`**：三条策略约束只在**实验执行边界**生效；工具面与 preflight 仍不读它们 ——
   同一条声明在不同执行面上效力不一致，这是如实登记的缺口。

**不得宣称的三件事**见 GOAL 的 `R-1` / `R-2` / `R-3`。
