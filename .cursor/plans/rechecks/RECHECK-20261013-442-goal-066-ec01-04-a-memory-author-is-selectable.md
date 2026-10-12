---
id: RECHECK-20261013-442
slug: goal-066-ec01-04-a-memory-author-is-selectable
title: 独立复检：GOAL-20261013-066 cycle 1（EC-01…EC-04）—— 记忆的作者可筛选
plan_id: PLAN-20261013-441
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-13
completed_at: 2026-10-13
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/application/ports/memory_store.py（`query` 第三维）+ 三适配器同契约
  - path: 独立重跑判据（选择面 10 例 + PG 1 例 + 序 17 回归 + 四向按压脚本）
    evidence: .cursor/plans/goals/evidence/GOAL-20261013-066-press-two-way.txt
---

# RECHECK-20261013-442 — GOAL-20261013-066 cycle 1 独立复检

复检对象：`PLAN-20261013-441`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-author-selectable.py` —— 四段读数与 GOAL 表逐条一致
（**改动后**）：

| # | 事实 | 独立读数（改动后） | 改动前 |
| --- | --- | --- | --- |
| 1 | `query` 形参 | `(self, tier=None, scope=None, **proposed_by**=None)` | 只有 `tier` / `scope` |
| 2 | 实跑 | 按作者选 **成功** | 读面报得出作者、按作者选 ⇒ **`TypeError`** |
| 3 | 先例（序 17 的 `scope` 第三维） | 在树（本轮**同一手法**） | 同 |
| 4 | 三适配器签名 | 三个**都**带第三维 | 三个**都缺** |

### 2. EC-02 查询面第三维（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/application/memory/test_memory_author_is_selectable.py tests/postgres/test_memory_conflict_timeliness_pg.py -q`
⇒ **13 passed**。逐条复核：

- Port `query` +1 **可选**形参；**三适配器同契约**（SQLite / PG **真库** / Fake **各自真筛**）；
- **缺省 ⇒ 不筛**（与「筛出空集」是两件事 —— 既有行为逐字不变）；
- **未知作者 ⇒ 空结果**（**不猜**、**不**回退成全选）；
- 作者与 `scope` **可并存**（两维各自独立）。

### 3. EC-03 消费面可传 + 点名（独立重跑）

`uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical/test_memory_read_dispositions.py tests/api -q`
⇒ **全绿**。逐条复核：

- `memory_read` **可传**作者 ⇒ 只读那一位的；载荷**点名** `proposed_by` 与 `filtered_out`
  （**筛掉了多少条** —— 与序 17 的披露形态**同源同形**）；
- **缺省载荷逐字相同**（两个键**只在传了作者时**才加）；
- **序 17 的 `scope` 支一字不动**（回归臂：`test_the_scope_disclosure_is_untouched`）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal066_press.py`）

| 按压 | 读数 | 被哪条判据抓到 |
| --- | --- | --- |
| **BASELINE**（未按压） | **GREEN**（50 passed） | — |
| `X-1` 查询面忽略作者筛 | **RED**（5 failed） | 选择面一组 |
| `X-2` 适配器不带该维度 | **RED**（1 failed） | `test_the_sqlite_adapter_shares_the_contract` |
| `X-3` 缺省形态被改动 | **RED**（19 failed） | 缺省 + 既有回归 |
| `X-4` 消费面不点名 | **RED**（1 failed） | 消费面点名臂 |

四条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`。
**一处两向核实**：`X-4` 首版锚点**不唯一**（`payload["filtered_out"]` 在该文件出现 **2** 次
⇒ 打到了序 17 的 `scope` 支、且按压成**空操作**按 GREEN）⇒ 按「批量替换先数命中数」纪律
改为打**作者支整段**（唯一）后 RED。

### 5. 既有断言集的**改签申报**（一条，如实登记）

`tools/goal049_closeout_assertions.py` 的 `ec03-the-read-face-accepts-a-scope` 原按**字面**
钉 `'args.get("scope")' in read_face`；序 34 把三个维度的解析收进 `_selection` /
`_optional_arg` 之后该锚点**假红**（`test_every_named_assertion_set_reports_no_negative_on_this_tree`
当场抓到）。**改判关系**，逐条申报：

- `git diff --numstat tools/goal049_closeout_assertions.py` ⇒ **+6 / -1**（删除行读数 = **1**）；
- **谓词逐条比对**：改前 = 那一行**字面**存在；改后 = 读面里出现 scope 维的**取值路径**
  （`args.get("scope")` **或** `_optional_arg(args, "scope")`）—— **受判面未收窄**
  （仍要求该维**被取值**；把取值点换成常量仍红）；
- **两向实测**：把 `_optional_arg(args, "scope")` 换成 `None` ⇒ 该条 **RED**（先红），
  复原 ⇒ 绿（不该红时不红）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：**作者成为可选维度**（三适配器同契约）、
**消费面可传且点名**（含筛掉条数）、**缺省形态逐字不变**、**序 17 的 `scope` 支一字不动**。

**WARN（逐条）**：

- **`W-1`（口径边界，非缺陷）**：未知作者 ⇒ **空结果**（**不**拒绝）—— 作者是**自由声明的标识**
  （与 `scope` 的**已知集合**不同，后者有域上的枚举面）⇒ 「你要的作者没有记录」与
  「该记录不存在」**在结果上不可分**（本 GOAL **不**新增作者注册面）。
- **`W-2`（有意不做的边界）**：**不**做**作者鉴权**（筛是**选择**，不是 ACL —— 与 `scope`
  的边界**逐字同形**）；**不**做**通配 / 模糊匹配**（**精确**匹配）；**不**给 HTTP 读面加该筛选
  （`GET /projects/{id}/memory` 的 `?scope=` 是序 17 做的，作者维**未**加）。
- **`W-3`（未覆盖）**：**内容级**冲突检测（`W-2` 的另一半）、**三维以上**闸门组合
  **未做**；`BB-3` / `DD-1`…`DD-3` 等残余**原样保留**。
- **`W-4`（承继）**：本 GOAL **不**推进上述任何一条；残余在 GOAL 的「残余与受限面」逐条在位。
- **`W-5`（未覆盖范围）**：读面**未认证**；**多租户 / RBAC / BOLA / BFLA**；**部署面**验证；
  **D 组审批通道**；`R-M1`（**未收口**）；`G24-5` 运行时拦截器 —— 逐条**照旧未覆盖**。

**不得**把本复检读作项目安全结论（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
