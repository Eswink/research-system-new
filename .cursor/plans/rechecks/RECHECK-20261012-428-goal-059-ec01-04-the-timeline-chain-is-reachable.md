---
id: RECHECK-20261012-428
slug: goal-059-ec01-04-the-timeline-chain-is-reachable
title: 独立复检：GOAL-20261012-059 cycle 1（EC-01…EC-04）—— 等待面的时限链在产品面上可达
plan_id: PLAN-20261012-427
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-12
completed_at: 2026-10-12
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: services/api/dto/programs.py（两个 DTO +1 可选键）+ adapters/sqlite/program_store.py（列 + 加法式补齐）
  - path: 独立重跑判据（新用例 14 + 4 + 1 例 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261012-059-press-two-way.txt
---

# RECHECK-20261012-428 — GOAL-20261012-059 cycle 1 独立复检

复检对象：`PLAN-20261012-427`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-nudge-reachability.py` —— 三段读数
**与改动前逐条相反**（这就是本轮的靶子：三层全断）：

| # | 事实 | **改动前**读数 | **复检时**读数 |
| --- | --- | --- | --- |
| 1 | 声明面两个 DTO | 键 **不在**（`False` / `False`） | 键 **都在**（`True` / `True`） |
| 2 | 落库面 round-trip | `60` ⇒ **`None`**（`silently dropped = True`） | `60` ⇒ **`60`**（`False`） |
| 3 | 出口面 `services/` | **零命中** | `composition.py:170/171` + `routers/programs.py:278/279` |

### 2. EC-02 界可声明、可落库（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_program_nudge_bound_reachability.py tests/postgres/test_program_store_pg.py -q`
⇒ **19 passed**。逐条复核：

- `ProgramCreateDto` / `ProgramDetailDto` 各 +1 **可选**键（缺省 `None` ⇒ 既有请求逐字不变）；
- SQLite：`_SCHEMA` 加列 + `_ensure_compatible_schema` **加法式**补齐（旧库文件也能用）
  + `_encode_program` / `_decode_program` 带上 + **两条** SELECT（`get` / `for_project`）带列；
- PG：迁移 `024` **只加列** + `_PROGRAM_SELECT` / `INSERT` 带列 + `_decode_program` 读回；
- **域校验逐字未动**：非正整数仍点名拒绝（`positive integer` —— 绕过 DTO 直构域对象也拒）。

### 3. EC-03 出口可注入（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_program_nudge_bound_on_the_run_path.py -q`
⇒ **4 passed**。逐条复核：

- 经**既有 HTTP 面**声明界 ⇒ 建程序回执回显 + 读面披露（**经落库**读回，不是进程内回显）；
- 注入记录型出口后推进 ⇒ **出口真的收到**一条通知（`declared_bound_seconds` = 声明值）；
- **只读判定面仍只读**（`program_waiting.py` 里无 `.nudge(` 也无 `NudgeSink` —— 既有判据钉住）；
- **序 25 的三态纪律一字未动**（未超期 / 未注入 ⇒ 空串；失败 ⇒ 点名）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal059_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（26 passed） |
| `V-1` 落库面去掉新列 | **RED**（4 failed） |
| `V-2` 声明面摘掉新键 | **RED**（8 failed） |
| `V-3` 出口面不交下去 | **RED**（2 failed） |
| `V-4` 三态纪律被改动（缺省也送） | **RED**（1 failed） |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**复检时的一处自纠（如实登记）**：首轮 `V-3` / `V-4` **按 GREEN** —— 两条反证臂**失效**
（`V-3` 打的是组合根的字段声明，而实例属性赋值照样生效；`V-4` 的受判面当时不含端口契约套件）
⇒ 按「该红时红」的一级纪律改判据面（`V-3` 改打**推进路由的交出点**、`V-4` 把
`test_nudge_exit_on_the_run_path.py` 纳入受判面）后**四条全红**。

### 5. 判据面自检（防假绿）

- **基线门**在脚本内（未按压不绿 ⇒ 非 0 退出）；
- **PG 判据两向实测**：临时把 `INSERT` 的值换成 `None` ⇒ **RED**（1 failed）⇒ 该判据**会响**；
- 例数下界钉进收口断言集（14 / 4 / 5 —— **纯收紧**）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：三段接线**各自可复核**
（探针读数 + 用例 + 按压），且**缺省形态逐字不变**（未声明界 ⇒ 不报；未注入 ⇒ 不送）。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：`V-3` / `V-4` 的首轮形态**按 GREEN** ⇒ 该轮的两条反证臂
  **一度失效**；已按纪律修正（见 §4）。**登记理由**：这正是「判据不得恒假」这条纪律的
  **现场兑现**，不是事后补记。
- **`W-2`（未覆盖）**：**真实外发**（邮件 / webhook / IM）**未做**；出口是**进程内 seam**，
  复检只在**注入记录型实现**的形态下取证 —— 「信号到了实现」**不**等于「人收到了」。
- **`W-3`（未覆盖）**：**投递保证 / 重试 / 去重**未做（端口语义逐字未动）。
  **投递语义不是「恰好一次」**（口径只能是 at-least-once + idempotency + deduplication）。
- **`W-4`（承继）**：`Z-1` 的**混合式**（序 28）/ `W-2` 的内容级检测 / `CC-3` 等残余
  **原样保留**；本 GOAL **不**推进其中任何一条。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。
- **`W-6`（观测隐私）**：送进端口的载荷**只含**结构化摘要（标识 / 计数 / 判词片段），
  **不含**内容原文 / Prompt / 凭据（§10 口径；复检逐字段核对 `NudgeNotice` 未变）。

**不得**把本复检读作项目安全结论（`R-M1`）。
