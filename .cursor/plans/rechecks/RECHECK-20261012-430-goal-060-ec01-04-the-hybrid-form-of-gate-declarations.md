---
id: RECHECK-20261012-430
slug: goal-060-ec01-04-the-hybrid-form-of-gate-declarations
title: 独立复检：GOAL-20261012-060 cycle 1（EC-01…EC-04）—— 闸门声明的混合式
plan_id: PLAN-20261012-429
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/domain/program.py（`HybridGateDeclaration` 值对象 + 互斥清单同轮）
  - path: 独立重跑判据（域 10 + 推进面 5 + 产品路径 4 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-060-press-two-way.txt
---

# RECHECK-20261012-430 — GOAL-20261012-060 cycle 1 独立复检

复检对象：`PLAN-20261012-429`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-gate-hybrid.py` —— 四段读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 三条声明的**类型**逐个读出 | 单序号 = `int \| None`；条件式 = `tuple[str, ...] \| None`；多点 = `tuple[int, ...] \| None` |
| 2 | **互斥判词** | `human_gate_at_index and human_gate_on_verdicts are mutually exclusive`（同时声明 ⇒ 点名拒绝） |
| 3 | 三段机制**已全在** | 注册 `register_declared_gate` / 判定 `declared_gate_trigger` + `declared_gate_verdict` / 桥 `declared_gate_evaluation` + `gate_outcome` |
| 4 | 混合式**改动前零命中** | 三根对 `human_gate_on_verdicts_at_indexes` **零命中**（⇒ 组合维度不存在） |

### 2. EC-02 混合式可声明（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/domain/test_program_hybrid_gate.py -q`
⇒ **10 passed**。逐条复核：

- `HybridGateDeclaration` 值对象：两维**缺一不可**（`at_indexes` / `on_verdicts` 空 ⇒ 点名拒绝；
  空字符串同样拒）—— 「只声明一半」在**构造上**写不出来；
- **越界 / 重复**由 `_validate_hybrid_gate` 点名拒绝（要看 `max_runs` ⇒ 与序 23 同处一层）；
- **既有互斥未解除**：混合式**同列**互斥清单（三条各自与它并存 ⇒ 逐条点名拒绝；
  三条**彼此之间**的互斥**也仍成立** —— 反证臂钉住）；
- 序 24 的时限面与混合式**正交**（可同时声明）。

### 3. EC-03 两维各自点名（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_program_hybrid_gate_on_the_run_path.py tests/e2e/test_hybrid_gate_on_the_http_face.py -q`
⇒ **9 passed**。逐条复核：

- **三态可区分**（受判面 = 三个形态，缺一即「各自点名」不成立）：只序号维 ⇒ 判词含
  `at_indexes=[1, 3]` 且**不含** `on_verdicts`；只条件维 ⇒ 含 `on_verdicts=['REJECT']` 且
  **不含** `at_indexes`；两维都命中 ⇒ **两条都点名**（显式并列）；
- **两反证臂**：两维都不命中 ⇒ 照常 `CONTINUE`（不是「声明了就停」）；未声明 ⇒
  逐字走结论面（缺省形态不变）；
- **两库同契约**：SQLite 两列（加法式补齐）+ PG 两列（迁移 `025` 只加列）；两臂各一例
  （声明 ⇒ 两维原样读回；未声明 ⇒ `None`）；
- **产品路径**：经既有 HTTP 面建程序时声明 ⇒ 建程序回执回显 + 读面回显 + 推进真停
  （`WAIT_FOR_APPROVAL`，不起新轮）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal060_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（19 passed） |
| `W-1` 混合式不再互斥 | **RED**（1 failed） |
| `W-2` 序号维被忽略（只判条件维） | **RED**（3 failed） |
| `W-3` 条件维被忽略（只判序号维） | **RED**（3 failed） |
| `W-4` 缺省形态被改动（未声明也拦） | **RED**（2 errors） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**复检时的一处如实登记**：`W-1` 的首版锚点带尾换行（单行锚点被 `_join` 补了换行）⇒
**按压模式未命中**（脚本以断言失败退出、**未**静默跳过）⇒ 改单行 `_flat` 后四条全红。

### 5. 既有断言集的**改签申报**（一条，如实登记）

`tools/goal059_closeout_assertions.py` 的 `ec02-the-router-passes-the-declaration-through`
原按**字面写法**钉路由（`gate_nudge_after_seconds=payload.…` / `=program.…`）；
GOAL-060 把声明转换抽进 `declared_gate_fields` 之后该锚点**假红**
（`test_every_named_assertion_set_reports_no_negative_on_this_tree` 当场抓到）。
**改判关系**（写侧读 `payload.`、读侧读 `program.`），**逐条申报**：

- `git diff --numstat tools/goal059_closeout_assertions.py` ⇒ **+5 / -3**（删除行读数 = **3**）；
- **谓词逐条比对**：改前 = 两条**完整赋值串**的字面存在性；改后 = 两侧**属性访问**的存在性
  —— **受判面未收窄**（仍要求两侧各自的引用在场；少任一侧仍红）；
- **两向实测**：把读侧 `program.gate_nudge_after_seconds` 换成 `None` ⇒ 该条 **RED**
  （先红），复原 ⇒ 绿（不该红时不红）。

### 6. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **重复基名自纠**：域与推进面两份判据**一度同名** ⇒ pytest `import file mismatch`
  （**基线就不绿**，被基线门当场抓到）⇒ e2e 那份改名为 `test_hybrid_gate_on_the_http_face.py`
  （仓库的判据文件基名**唯一**惯例）；
- 例数下界钉进收口断言集（10 / 5 / 4 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：混合式**可声明**（值对象两维缺一不可）、
**两维各自点名**（三态可区分 + 两条反证臂）、**缺省形态逐字不变**（未声明 ⇒ 逐字走结论面）。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：`W-1` 首版锚点**未命中**（脚本硬失败）；**登记理由**：
  这正是「判据不得恒假」与「反证脚本必须真的会响」两条纪律的**现场兑现**。
- **`W-2`（可读性边界）**：两维命中时判词**显式并列**（`； 且 `）—— 这是本形态成立的前提
  （否则读者会把「两维都停」读成「一维停」）；**代价**：判词比单维形态长。
- **`W-3`（未覆盖）**：**同一点上两条声明互斥**的既有纪律**未解除**（本轮**有意**不解除 ——
  那是同一维度上的重复声明）；`Z-1` 的**混合式**之外的更复杂组合（如三维以上 / 表达式）
  **未做**。
- **`W-4`（承继）**：`Z-3` 的通知外发 / 升级链；`W-2` 的内容级检测；`CC-3` 等残余
  **原样保留**；本 GOAL **不**推进其中任何一条。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
