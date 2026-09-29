---
id: RECHECK-20260929-252
slug: goal-026-ec04-compensation-and-transactional-outbox
title: GOAL-026 EC-04 复检：发件箱失败注入原子性（两条写路径实测不对称）+ 去重边界 + 补偿可复核 + exactly-once 机械否认
plan_id: PLAN-20260929-251
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-252 — GOAL-026 EC-04 复检

**复检口径**：不采信判据自己的叙述，也**不采信代码注释**；本文件给出**可复核观察面**
（命令 / 判词行 / raw `sha256` / 实测计数）。**未实跑的不记通过**。

## 检查结果

### 1. 发件箱原子性（**失败注入**，实测）

- 交付：`tests/adapters/sqlite/test_outbox_atomicity.py`（**5 例**）。
- 注入机制：SQLite **授权回调**（`set_authorizer`）在「写 `outbox_events` 表」时返回
  `SQLITE_DENY` —— **不拼任何 SQL 文本**，也不改产品代码。注入点在提交块内**最后一条语句**
  （`persist_new_lease`：先写租约行 → 再改任务状态 → **最后发事件**）。
- 实测（`scratch/goal026_ec04_probe.py` 的 `q2`）：
  `fault=on: raised DatabaseError('not authorized') denied=1` /
  `counts = (0, 0, 1) status = ['QUEUED']` ⇒ **租约行与任务状态一起回滚**（all-or-nothing）；
  `fault=off: counts = (1, 1, 1) status = ['LEASED']` ⇒ **正控制**（三件同时可见，证明上一条
  不是「什么都不写」）。判据另断言 `fault.denied == 1`（故障真的触发过）与
  「回滚后还能重新 claim ⇒ 失败的尝试不留毒」。

### 2. **两条写路径的原子性实测不同**（本轮最有价值的发现）

- **引擎路径**（`OutboxWriter`，写调用方事务内）：如上，all-or-nothing。
- **发布器路径**（`SqliteOutboxEventPublisher.publish`，**自提交**）：实测同一调用块内
  后续失败**不会**把事件带走 —— 两个连接都看得见那一行
  （`q1 counts on same conn = (1, 0, 0)` / `q1 counts from second conn = (1, 0, 0)`）。
- **该文件原来的注释声称相反**（`adapters/sqlite/event_publisher.py:47-56` 旧文本：
  「including rolling back together with other writes when a LATER operation in the same
  caller-managed `with conn:` block fails」）⇒ 按实测**就地更正**（**仅注释**，零行为变更；
  PA-1 F7 的耐久性理由原样保留，另写明代价与「要与业务写同生共死请用 `OutboxWriter`」）。
  判据里显式写明「按实测钉住，**不按注释钉**」。

### 3. 去重面与投递边界（实测）

- 同一 `event_id` 重复发布 ⇒ **只留一行**，且内容是**首次**那份（`decode_envelope` 读回比对
  `payload == {"marker": "first"}`）⇒ 去重键 = `event_id` 的**结构化**证据（含防篡改）。
- 投递边界：`pending()` / `published` / `mark_published()` 逐条对账 —— 标记一条**恰好**减少一条、
  总表不减、重复标记**幂等**、空集是 no-op；受判面下界 = 待投递条数 `≥ 2`。
- **如实登记**：仓内**没有**按事件物化业务事实的应用消费者（发布器 docstring 自己写着
  「本实现是持久化 outbox，不是消息总线；投递/订阅属后续阶段」）⇒ 「至少一次投递 + 消费端
  按 `event_id` 去重」只证到**存储面**；**消费端去重未取证**（`R26-5`）。

### 4. 补偿：可复核的**执行**面 + 缺失面登记（实测）

- 交付：`tests/application/run_orchestration/test_compensation_boundary.py`（**3 例**）。
- **执行**：`compensate_failed_resume` 把 `RUNNING` 的 run 放回 **`PAUSED`**，并发**恰好一条**
  `run.resume_failed`；payload 键集合**恰好** `{run_id, failure_type, message, compensated_to}`
  且 `compensated_to == PAUSED`；原实例不可变（证据保留）。
- **不产生第二次副作用**：对已停车的 run 再补一次 ⇒ **结构化拒绝** `InvalidTransitionError`，
  且事件数不变（1）。
- **缺失面（结构化）**：`COMPENSATE` / `COMPENSATING` 在 4 个产品根（`packages` / `adapters` /
  `services` / `apps`，扫描面下界 `_MIN_SCANNED = 400`）的 `.py` 里**只出现在域定义**
  `packages/domain/session_state.py`（判据断言命中集合**恰好等于**该文件）⇒
  **该会话态无产品驱动**；`compensation_actions` **产品代码零命中**、仍登记在
  `docs/storage/DATABASE_SCHEMA.md` ⇒ 「非幂等副作用的补偿」是**登记边界**，本轮**不实现**。

### 5. exactly-once 的机械否认（实测）

- 交付：`tests/architecture/python/test_delivery_semantics_wording.py`（**6 例**）。
- **受判面（实质面）**：`AGENTS.md` / `docs` / `packages` / `adapters` / `services` /
  `apps/web/src` / `tests` / `.cursor/plans/{tasks,rechecks}` / `.cursor/memory`，
  实测**扫描 2605 个文件**、`exactly[ _-]once` **20 条出现** ⇒ 分类
  **`DENIAL` 14 + `EXEMPT` 6 + `AFFIRMATIVE` 0**（肯定式 ⇒ 判红）。
  下界：文件 `≥2500`、条数 `≥16`。
- **豁免是**有界**的**：表长 `≤ _MAX_EXEMPT (=8)`（实测 6）、理由非空 `≥20` 字符、
  **必须全部被用到**（不许留不生效的条目当暗余量），键 = (路径, **整行内容**) ⇒ 行一改就失效。
- **否定词窗有界**：本行 **±6 行**且**两侧按段落截断**（遇空行即止）—— 记录 / 文档的软换行会把
  「明确不做」「立即 BLOCKED」留在上一行或下一行。
- **规则文本面**（`.cursor/plans/goals/**`，27 个文件）**单列**，排除理由写在明处（GOAL 记录
  **就是禁令文本本身**，逐行分类属范畴错误）；另一条判据要求「**凡引用了该词的 GOAL 文件，
  必须同时写出禁令词表里的词**」⇒ 排除不是静默跳过。
- **正控制**：两条已知否认行（`AGENTS.md:175`「禁止假装实现…」、
  `ADR-0016:5`「不宣称 exactly-once」）必须被判成 `DENIAL`（证明词表在用，不是摆设）。
- **CJK lemma**（「恰好一次」）在产品 + 文档面**零命中**；同一判据要求检测器在它确实出现的地方
  （`.cursor/` 与 `tests/`，实测 **12 个文件**）找得到 ⇒ 「零命中」不是「检测器坏了」。
- **口径串在位**：`docs/architecture/WORKFLOW_RELIABILITY.md` 含 `at-least-once` / `idempotency` /
  `outbox` 三串；`docs/adr/ADR-0016-…md` 含后两串（正文**没有** `at-least-once` 字面 —— 实测，
  因此按**逐文档实测**清单断言，而不是「每个文档三串都要有」）。

### 6. 两向按压 + 逐字节复原（实测）

**按压矩阵**（留档 `scratch/goal026-ec04-press-matrix.log`，二进制写盘 / `CR` 计数 0 / 4088 字节）：

| 按压 | 位置（**产品代码**） | 按压态 `sha256` | 实测红（原样） | 复原 |
| --- | --- | --- | --- | --- |
| **A** 事件写进另一个事务 | `adapters/sqlite/workflow_claim.py::persist_new_lease`（在 `outbox.publish` 前加 `conn.commit()` ⇒ 业务写提前提交） | `33a42f3b13680047…` | `1 failed, 4 passed`；`AssertionError: 事件写失败后不得留下租约行或事件行` | raw `sha256` 回到 `e5a21a8cc5271e69…`（== 基线）⇒ `5 passed` |
| **B** 关掉去重 | `adapters/sqlite/event_publisher.py::publish`（`INSERT OR IGNORE` → `INSERT OR REPLACE` ⇒ 重复投递不再被忽略、而是**覆盖**已存在的那一份） | `b1294d41ebc8125d…` | `1 failed, 7 passed`；`AssertionError: 已存在的事件不得被后来的内容顶掉`（**既有** `test_event_publisher.py` 三条仍绿 —— 它们只断言行数） | raw `sha256` 回到 `82b98d909315c956…`（== 基线）⇒ `5 passed` |

- **两向**：两次按压中各只有**目标**用例红 ⇒ 「不该红时不红」。
- **复原逐字节**：两次 raw `sha256` 均回到基线；`git status --short` 中两个按压文件**均已消失**。
- **口径说明（如实登记）**：GOAL 的反证口径写的是「关掉**消费者**去重」，但仓内**没有**消费者
  ⇒ 按压 B 打在**唯一被实现的去重键**（存储边界上的 `event_id`）上；消费端去重仍未取证。
- **既有判据逐字节未改**；新判据**无 skip / xfail**。

### 7. 四道门与定向套件（实测）

- `ruff format --check`（3 新文件 + `adapters/sqlite/event_publisher.py`）= `4 files already formatted`；
- `ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 4 source files`；
- 规模门 = **1070 passed**（上轮 1067 + 本轮 3 个新文件）；
- 定向套件（`tests/adapters/sqlite` + `tests/application` + `tests/architecture/python` + 规模门）
  = **2211 passed, 1 skipped**。
- **首轮被抓到的本人错误**：`ruff` 报 2 处超长行（含一处 `os.path.dirname` 四连）；`ruff format`
  重排 1 个文件；**判据首版**的否定词窗只看**上一行**、且词表缺「否认 / 不做 / BLOCKED」⇒
  13 条记录面出现被误判 `AFFIRMATIVE`（**判据自己红**）⇒ 改为 ±6 行按段落截断 + 补词表
  ⇒ 归零。**未**为了变绿而放宽 AFFIRMATIVE 的判定（该断言至今是硬断言）。

## 结论

**EC-04 = PASS_WITH_WARNINGS**（`PLAN-20260929-251` 的 AC-1…AC-7 全部成立且有实跑证据）。
§7 两项义务在**单节点 SQLite + 授权回调注入**的射程内**成立**：
「**transactional outbox**」（引擎路径实测 all-or-nothing；去重键 = `event_id`；投递边界逐条对账）、
「**compensation for non-idempotent actions**」（唯一可调用的补偿**执行可复核**且**不可重复施加**；
非幂等副作用的补偿**登记为缺失** —— 未实现，也不宣称）。
第 ④ 项（exactly-once 的机械否认）在**有界显式声明**的面上成立（0 条肯定式），
口径串在可靠性文档里在位。

**如实登记的警告（`W-1`…`W-7`）**：

- `W-1` **两条写路径的原子性不同**（引擎 all-or-nothing；发布器自提交 ⇒ 同一调用块内的后续失败
  **不带走**事件）。产品注释已按实测就地更正（**仅注释**、零行为变更）。但**既有判据文件**
  `tests/adapters/sqlite/test_event_publisher.py` 的**模块 docstring 仍复述旧说法**（本轮实测为假）——
  本 GOAL **不修改既有判据** ⇒ 只登记；两条口径因此暂时不一致，读者以本复检与判据为准。
- `W-2` **没有应用级事件消费者** ⇒ 「至少一次投递 + 消费端按 `event_id` 去重」只证到**存储面**；
  消费端去重**未取证**（`R26-5`，实现属新能力）。
- `W-3` 故障注入是**授权回调级**（拒绝写表），不是真实磁盘满 / 提交冲突；且只压在 **claim** 路径
  （`submit` / `complete` 路径未压）⇒ 「所有写路径都原子」**未取证**。
- `W-4` exactly-once 面是**有界面**（2605 文件）+ **有界窗口**（±6 行、段落截断）+ **豁免表**
  （6/8）。它证明的是「**这个面上**没有肯定式声明」，**不是**「全仓没有」；记录面（GOAL 文本）
  只到「引用即须写禁令」这一强度。
- `W-5` `services/api/worker_gateway/auth.py:22` 的 `returned to the worker exactly once`
  是**肯定式**短语，按豁免登记（判为「响应形状声明、非事件投递语义」）。它**未被任何判据证明**
  ⇒ 将来要么证明、要么改写。
- `W-6` PG 侧（`tests/postgres/test_outbox_pg.py`）**仍只在全绿路径**；失败注入未在 PG 侧做
  （需真实 PG + 事务级注入）⇒ 跨适配器的原子性一致性未取证。
- `W-7` 补偿只覆盖「恢复失败的 canonical 状态回滚」；**非幂等副作用**（工具调用 / 工作区写入 /
  外部发布）**无补偿**，`compensation_actions` 只在文档（`R26-4`）。
- `R-M1` 未收口（Mimosa 钩子 `scanner_enobufs` 未得完整结论）⇒ **不得**据此宣称项目安全。

**未覆盖范围（承 GOAL-026）**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
`R-M1` 未收口。
