---
id: RECHECK-20261011-418
slug: goal-055-ec01-04-a-program-gate-can-be-declared-at-several-points
title: 独立复检：GOAL-20261011-055 cycle 1（EC-01…EC-04）—— 程序级闸门的多点声明
plan_id: PLAN-20261011-417
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: packages/domain/program.py（`human_gate_at_indexes`）+ 两根落库 + 推进面第三支
  - path: 独立重跑判据（域 8 + 推进面 5 + 两根 3）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-055-press-two-way.txt
---

# RECHECK-20261011-418 — GOAL-20261011-055 cycle 1 独立复检

复检对象：`PLAN-20261011-417`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-multi-gate.py` —— 四组读数与 GOAL 表逐条一致：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 闸门字段**共 2 个** | `human_gate_at_index: int | None`（**一个固定序号**）+ `human_gate_on_verdicts: tuple[str, ...] | None`（**条件式**）|
| 2 | 两者**互斥** | `mutually exclusive` 引文在位（「two gate declarations would make 'why did it stop' unreadable」）|
| 3 | **结构上不可能**多点 | 字段类型是**单个**可选整数 ⇒ 第二个序号**无处可写** |
| 4 | **机制三段已全在** | `register_declared_gate` / `declared_gate_verdict` / `declared_gate_pending` 三条 `def` 逐条 OK |

### 2. EC-02 多点可声明（独立重跑）

域新增 `human_gate_at_indexes: tuple[int, ...] | None`；三处校验**逐条点名**：
非空（`()` 与 `None` 语义不同）/ 逐点在 `1..max_runs` / **不得重复**；三条声明**互斥**（混用 ⇒ 点名）。
**两根都落库**：SQLite 新列 + **加法式列补齐**（`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`，
与 `eval_report_store` 同一手法 ⇒ **旧库文件也能用**，受判面 = 先建旧表再打开 store）；
PG 迁移 `022_program_multi_point_gate.sql`（`ADD COLUMN IF NOT EXISTS`，只加列）。
**DTO + 快照同轮**（`+28 / -0`，纯附加）。

### 3. EC-03 推进面逐点生效（独立重跑）

`declared_gate_trigger` 加**第三支**（一组序号，任一点命中即触发）+ `_multi_point_trigger`
**点名是哪一点**触发的；`declared_gate_verdict` 的被引事实也把第三种形态**逐条点进来**。
新用例 5 条：第 1 点拦 / **中间轮不拦**（受判面可区分）/ 最后一点拦 / 未声明逐字 / 判词形态可区分。

### 4. EC-04 两向反证（独立重跑 `scratch/goal055_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（14 passed） |
| `R-1` 多点**只认第一个** | **RED**（1 failed） |
| `R-2` **越界被接受** | **RED**（1 failed） |
| `R-3` **重复被接受** | **RED**（1 failed） |
| `R-4` **未声明形态被改动** | **RED**（2 failed） |
| 复原 | 四条 `sha 复原一致=True`（二进制读写） |

归档：`.cursor/plans/goals/evidence/GOAL-20261011-055-press-two-way.txt`
（**722 B / 15 行 / `CR=0`** / `sha256 de221cf19e77a3a4…`）。

### 5. 两条门禁当场抓到本轮问题（如实登记）

| 门 | 逐字 | 处置 |
| --- | --- | --- |
| SQLite 共享连接门禁 | `写路径出现裸 commit（或在 with 块外提交）：[('program_store.py', '_ensure_compatible_schema')]` | 登记进**构造期 bootstrap 白名单** —— 与既有 `eval_report_store._ensure_compatible_schema` **同类同形**（也是 `__init__` 里调的本连接初始化）。**不是**放宽：那条门禁的射程是**并发写路径**，构造期 bootstrap 本来就在白名单语义内 |
| 严格 mypy（`attr-defined`） | `Module "…test_program_waiting_on_the_run_path" does not explicitly export attribute "_Harness"` | 在 harness 模块**显式 `__all__`**（跨文件复用的名字要**声明**，不是把私有名当公共 API）|

**另两处判据面自纠（自查，如实登记）**：① 判词是 **f-string** ⇒ AST 拆成 `Constant` 分片，
且**片段本身可能只是某个分片的一部分**（`本轮命中`）⇒ 按「集合成员」核对**永远失配**
（本轮的 5 条判据一开始全假红）；改成**子串**核对（`_contains`）。
② `_ensure_compatible_schema` 是**方法**（缩进 > 0）⇒ 要求**模块级**定义会**恒假**；
改成 `_defines_method`（含类方法）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_shared_connection_transaction_scope.py` | 见 `git diff --numstat` | `_BOOTSTRAP_COMMIT` 白名单 **+3 行**（新增一条）| **纯收紧**（`offenders == _BOOTSTRAP_COMMIT` 是**等号**：白名单**多了**一条不存在的会红）| **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | 见 `git diff --numstat` | 加模块级 `__all__`（4 个名字）| **等价**（不改任何断言；只声明可复用性）| **0** |

**射程分类（逐条）**：① 两条都**不属**声明过的同轮同步集 ⇒ 命中 `escalation_triggers` 第 5 条
形态，在此**如实登记**；② **无一处收窄受判面**（白名单是**声明面**、`__all__` 是**导出面**）；
③ 删除行读数 **0**（两处都是纯加法）。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察读数与 GOAL 表逐条一致；
多点声明在三层（域 / 两根 / DTO+快照）都落地且**旧库可用**；推进面逐点生效且**点名触发者**；
四向反证**基线绿 + 全红 + 复原一致**。

### Warnings

- **W-1（只做序号维度）**：本轮**不**把多点与条件式混成一条声明（互斥**不解除**）——
  「第 1 轮停，且当判词为 X 时也停」这种**混合式**仍未做（那是第三种形态）。
- **W-2（`Z-3` 未做）**：催办 / 升级 / 超时**未做** —— 多点闸门让「停在哪些点」可声明，
  但**停多久、要不要催**仍未做。
- **W-3（历史库的列补齐是加法式的）**：旧库由 `_ensure_compatible_schema` 补列；
  若某库的 `research_programs` 表**被外部工具**改过形态（缺更多列），本补齐**只补这一列**。
- **W-4（承继残余原样保持）**：`W-2` 的内容级检测 / `CC-1`…`CC-3` / `BB-3` /
  `DD-1`…`DD-3` / `AA-*` / `Y-*` / `X-*` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` /
  `P-*` / `O-1`·`O-3`·`O-4`·`O-5` / `R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
