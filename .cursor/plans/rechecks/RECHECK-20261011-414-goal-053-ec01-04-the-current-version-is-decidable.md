---
id: RECHECK-20261011-414
slug: goal-053-ec01-04-the-current-version-is-decidable
title: 独立复检：GOAL-20261011-053 cycle 1（EC-01…EC-04）—— 链式取代的「当前版本」可判定
plan_id: PLAN-20261011-413
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（cycle 1 全部交付）
    evidence: adapters/canonical/memory_read.py + services/api/dto/memory.py（`terminal` 键与两处同源）
  - path: 独立重跑判据（`tests/api/test_memory_chain_end.py` + 既有 `test_memory_api.py`）
    evidence: scratch/g053-press.txt（基线 GREEN + 四按压 RED + 复原一致）
---

# RECHECK-20261011-414 — GOAL-20261011-053 cycle 1 独立复检

复检对象：`PLAN-20261011-413`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. EC-01 勘察定稿（独立重跑探针）

`uv run --frozen --no-sync python -B scratch/probe-chain-supersede.py`（**读面口径** =
`_memory_row`，不手拼参数）⇒ 六条读数与 GOAL「事实层结论」表**逐条一致**：

| # | 事实 | 独立读数 |
| --- | --- | --- |
| 1 | 「不做传递闭包」的旧文档 | 已随本轮**改写**（改成指向 `terminal_versions` —— 那条不再「明确不做」） |
| 2 | A 的替代品是死的 | `mem-a: superseded_by=['mem-b']` 而 `mem-b: active=False` |
| 3 | 载荷无字段可答「当前版本」 | **本轮已补**（`terminal`）—— 旧的 13 键里确实没有 |
| 4 | 两侧处置同值 | `mem-a` 与 `mem-b` 都 `SUPERSEDED`，`reason` 各只点名**直接**后继 |
| 5 | 前向也只一层 | `mem-c: supersedes=['mem-b']`（**不**含 `mem-a`） |
| 6 | 写者语义 | `git diff --numstat b2ba09a~1 b2ba09a -- packages/application/memory/lifecycle.py` ⇒ **零改动**（符合「不改写入语义」）|

### 2. EC-02 链的终点（独立重跑）

**四态**（`CURRENT` / `SUCCEEDED` / `CYCLE` / `OUT_OF_VIEW`）**七个形态逐条实测**：
单条 ⇒ `CURRENT`；链 A⊂B⊂C ⇒ A/B 都 `SUCCEEDED→['mem-c']`、C `CURRENT`；环 ⇒ `CYCLE` 且点名环上 id；
自指 ⇒ `CYCLE→['a']`；跨范围（后继不在本查询范围）⇒ `OUT_OF_VIEW`；**菱形**（A→{B,C}→D）
⇒ `SUCCEEDED→['d']`（**不是**环 —— 初版 BFS 会误报）；双终点 ⇒ `SUCCEEDED→['b','c']`（逐个点名）。

**既有键逐字不变**：`git diff` 后 `supersedes` / `superseded_by` 仍是**直接**链接
（新用例里**逐条**断言 `superseded_by == ["mem-b"]`、`supersedes == ["mem-b"]`）。

### 3. EC-03 同源与一致（独立重跑）

两处取值**同一批纯函数**：HTTP 读面 `_record_dto` 调 `packages.application.memory.disposition`
的 `terminal_versions`（**应用层** —— HTTP 面不得 import 适配器）；
`tests/architecture` **287 passed**（分层契约 `2 kept, 0 broken`）。
新用例 `test_the_http_face_carries_the_chain_end_too` 逐条比 `terminal_state` / `terminal_ids` 与
编排面同值。OpenAPI 快照同轮重生成（`+12 / -0`，纯附加，判据一字未改）。

### 4. EC-04 两向反证（独立重跑 `scratch/goal053_press.py`）

| 按压 | 读数 |
| --- | --- |
| **BASELINE**（未按压） | **GREEN**（18 passed） |
| `P-1` 终点算错（取直接后继） | **RED**（2 failed） |
| `P-2` 退回直接链接 | **RED**（3 failed） |
| `P-3` 既有键改名 | **RED**（3 failed） |
| `P-4` 链上有环却静默 | **RED**（1 failed） |
| 复原 | 四条 `sha 复原一致=True`（二进制读写） |

归档：`.cursor/plans/goals/evidence/GOAL-20261011-053-press-two-way.txt`
（**747 B / 15 行 / `CR=0`** / `sha256 e33739554f9dca42…`）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | +/- | 改了什么 | 谓词比对 | 删除行读数 |
| --- | --- | --- | --- | --- |
| `tests/api/test_memory_api.py` | +28 / -9 | 「既有 13 字段」那条的**新增字段集**从四样扩到六样；两段断言抽成命名函数 | **等价偏强**：受判形态**未变**（仍是「剔除新增后 == 那 13 个**逐字**」），且新增字段**另有正证**（逐条点名在场）⇒ **未**放宽 | `9` |

**射程分类（逐条）**：① 属**同轮同步集**里的**加法**（该文件是本轮**必须**改的 ——
新增字段若不同步进「既有字段集」就会把**新键**误报成「既有键被改」）；
② **无一处收窄受判面**；③ 删除行**全部**是被替换的旧断言文本（`9` 行），谓词逐条比对见上表。

## 结论

**result: PASS_WITH_WARNINGS**。EC-01…EC-04 逐条独立成立：勘察读数与 GOAL 表逐条一致；
四态 + 菱形/自指/跨范围共**七个形态**实测正确；两个读面**同源同值**（分层契约 2 kept, 0 broken）；
四向反证**基线绿 + 全红 + 复原一致**；既有键逐字不变；快照同轮。

### Warnings

- **W-1（两处设计经实测修正，如实登记）**：① **`DANGLING` 支不可达**（后继不可能在批外 ——
  `successors` 的值全部来自批内 `record.id`）⇒ 换成**可达**的 `OUT_OF_VIEW`（跨 `scope` 实测）；
  ② **菱形 ≠ 环**（BFS 的「见过集合」会误报 ⇒ 改 DFS 三色）。两处都**不是**设计出来的，
  是实测推翻了设计。
- **W-2（`OUT_OF_VIEW` 的语义边界）**：它回答的是「这条**已不生效**却看不见后继」——
  **不**区分「被删除」「跨范围」「过期清理」。更细的区分需要读**删除审计**面，本轮**不做**。
- **W-3（HTTP 面的时点判定仍未做；承 `DD-1`）**：HTTP 面**仍不**做「按时点判时效」。
- **W-4（其他读面未普查；承 `DD-2`）**：本轮仍只对齐**记忆**的两个读面。
- **W-5（一致性判据只在记忆面；承 `DD-3`）**：**未**做全仓通用的一致性判据。
- **W-6（承继残余原样保持）**：`CC-1`…`CC-3` / `W-2` / `BB-3` / `Z-1` / `Z-3` / `AA-*` /
  `Y-*` / `X-*` / `W-1`·`W-3` / `V-*` / `U-*` / `T-*` / `S-*` / `R-*` / `Q-*` / `P-*` /
  `O-1`·`O-3`·`O-4`·`O-5` / `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全
  （`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
