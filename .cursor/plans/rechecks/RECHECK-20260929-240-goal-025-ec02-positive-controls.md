---
id: RECHECK-20260929-240
slug: goal-025-ec02-positive-controls
title: GOAL-025 EC-02 复检：6 条载体正控制 + 3 条取不到路由的机械事实 + 4 个源的结构化陈述（含按压与逐字节复原）
plan_id: PLAN-20260929-239
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-240 — GOAL-025 EC-02 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
**未实跑的不记通过**；警告逐条留位。

## 检查结果

### 1. 6 条无正控制载体建正控制（AC-1）
- 交付：`tests/observability/positive_control_support.py`（**250 行**）+
  `test_privacy_positive_controls.py`（**196 行 / 11 例**），实跑 **11 passed**。
- **必做面不是另写一份清单**：`test_carrier_matrix_covers_every_registry_entry_without_control`
  从 GOAL-024 的登记**推出**必做集合（`DECLARED_CONTENT` 里 `kinds` 为空的行 ∪
  `UNEXERCISED_DECLARED` ∪ `UNEXERCISED_ZERO_HIT`）并与矩阵比对 ⇒ 登记面一变，这里立刻红。
- **逐条正控制（实跑）**：模板 ×2（换入金丝雀模板目录）／记忆（经 `POST /memory/proposals`，
  provenance 走已登记的 evidence source）／交付物（seed `<run>:deliverable.json`）／
  库 ×2（经 `POST /projects/{id}/library`）—— 每条都**看到**它声明承载的金丝雀。
- **下界**：`MIN_POSITIVE_CARRIERS = 6`；按压 Q3 证明「把一条正控制降级成机械理由」会判红
  （承 MEM-160：必做面不许靠改判收缩）。
- **未动参考资产**：`examples/protocols/` 一字未改（模板正文用**换入注入实例**提供），
  避免改到被别的套件复用的夹具失败形态。

### 2. 3 条取不到路由的判定化（AC-2）
- `/library/{resource_id}`：经**产品写面**建条目后**可取到**（200 且回它声明的正文）——
  从 GOAL-024 的 `UNEXERCISED_DECLARED` 状态变成实取。
- 2 条 workspace 快照路由：断言 `deps.workspace_snapshots is None`（离线装配无快照读面），
  并**真跑**这两条路由 ⇒ 实测 **503**（产品守则：未配置快照根不返回空树）。
  **无 `skip` / `xfail`**（`pytest -q` 输出中本轮 11 例全为通过，无跳过）。

### 3. 四个无注入面源的结构化陈述（AC-3）
- `task_input`：`StartRunCommand` 的自由文本面只有 `notes`（离线链为空 `{}`）与 `protocol_body`
  （= `prompt_text` 源）⇒ 没有独立的「任务输入」承载体（结构断言，实跑）。
- `tool_arguments` / `tool_output`：Fake runtime **无工具面**（`execute_tool` / `call_tool` /
  `invoke_tool` / `tools` 四个属性全无），而 `RuntimeEventKind.TOOL_CALL_REQUESTED` **真实存在**
  ⇒ 断言不是空转。
- `failure_message`：失败分支的 runtime **结构化输出为空** ⇒ 无用户文本通道；并实跑离线失败
  分支，断言失败载荷**非空**（面被真的观测到）且**零金丝雀**。
- 四条各带一条**非空的待真实 runtime 取证理由**（真实 runtime / 工具面 / 凭据）⇒ 「未验证」被收窄为
  「离线可判定的部分已判定 + 剩余部分逐条登记」。

### 4. 按压、复原与终态（AC-4）
- **按压（源码级，先红后绿）**：Q1 抽空一条机械理由 ⇒ `这些行没有理由:[…]`；
  Q2 下界 6→7 ⇒ `正控制载体只有 6 条 < 下界 7`；Q3 正控制降级 ⇒
  `正控制载体只有 5 条 < 下界 6`。
- **逐字节复原（承 MEM-152）**：三处均以 Edit 施加 / 复原，`sha256` 用**二进制读**计算、
  证据用**二进制写**盘；复原后回到
  `d9f85f1cb79dfc0b1fbe10985be26e8d77ce84a29257b2c8612611d9e24f2faf`（`MATCHES_BASELINE True`），
  复绿 11 passed。证据：`scratch/goal025-ec02-press-matrix.log`。
- **四道门**：`ruff format --check` / `ruff check` = `All checks passed!`、
  `mypy` = `Success: no issues found in 2 source files`、规模 **250 / 196 行**（≤450）；
  规模门定向跑 **2 passed**。
- **既有判据逐字节未改**（只新增文件）；`tests/observability/` 全目录
  **124 passed, 1 skipped**（cycle 1 后为 113 + 1 ⇒ **+11** 恰为本轮新判据）。
- `m0` / 治理 / CI 台账：见 PLAN-20260929-239 的「证据」与 GOAL 迭代日志（**记录写入之后**才跑）。

## 结论

**PASS_WITH_WARNINGS**。EC-02 的三条验收（载体正控制 / 取不到路由判定化 / 源结构化陈述）
**全部有实跑证据**；残余 `G24-6` 在本轮**收口**，`G24-1` 的**离线可判定部分收窄**、
剩余部分逐条登记为待真实 runtime 取证项（真实 runtime 面）。

**警告（如实留位，不消解）**：

- `W-1`：正控制证明的是「**出口能承载并呈现内容**」（route-level capability），
  **不是**「这些载体的内容在真实装配下一定到达这里」。模板正控制走的是**换入的注入实例**，
  不是产品内置模板目录里的真实模板 —— 产品目录本身**不带**金丝雀（这是有意的：不动参考资产）。
- `W-2`：`tool_arguments` / `tool_output` 的机械证据是**属性面断言**（Fake 上不存在工具调用面）
  加上「枚举里确有该 kind」。它证明「默认离线链上不存在承载体」，**不**证明
  「真实工具面启用后工具参数不会经非 canonical 出口外泄」。
- `W-3`：`task_input` 的断言落在 `StartRunCommand` 的**字段面**；若将来新增自由文本字段，
  本判据**不会自动红**（字段是显式列举的），需要人工同步该断言。
- `W-4`：`failure_message` 的「产品生成」结论锚在**「该分支的结构化输出为空」**上；
  它对**真实 runtime 的失败文本**（可能含异常消息 / 端点回包）**不成立** ⇒ 已登记为待取证项。
- `W-5`：库条目的 `content_ref` 指向制品 id；本轮只判定 `description` 承载的内容，
  **`content_ref` 指向的正文是否可经该路由取回未判定**。
- `W-6`：workspace 快照的 503 是**离线装配**的事实；**配置了快照根的真实部署面未验证**
  （快照树 / diff 是否泄漏内容不在射程）。
- `R-M1` 未收口：**不得**据此宣称项目安全；本复检只覆盖被点名判据在本机默认离线链上跑到的那几面。
