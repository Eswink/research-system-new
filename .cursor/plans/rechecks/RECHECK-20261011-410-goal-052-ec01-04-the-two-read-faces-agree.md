---
id: RECHECK-20261011-410
slug: goal-052-ec01-04-the-two-read-faces-agree
title: 独立复检：GOAL-20261011-052 cycle 1（两个读面对齐 —— 四样补齐 / 同源同值 / 四向反证）
plan_id: PLAN-20261011-409
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
---

# RECHECK-20261011-410 — GOAL-20261011-052 cycle 1 独立复检

复检对象：`PLAN-20261011-409`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | **编排消费面**读面（修前） | `_memory_row` **13 键**，含 `contradictions` / `superseded_by` / `disposition` / `reason` |
| 1.2 | **HTTP 读面**（修前） | `MemoryRecordDto` **13 字段**，**无**那四样 |
| 1.3 | `rg` 反证（修前） | `rg -n "contradictions\|superseded_by" services/api/dto/memory.py` ⇒ **零命中** |
| 1.4 | **实跑**（修前） | 同一批记录经两个读面 ⇒ 键集差 = 那四样 |
| 1.5 | 正向有、反向无（修前） | HTTP 面有 `supersedes`（正向）、**无** `superseded_by`（反向）⇒ 序 18 的「两向都点名」只在编排面成立 |
| 1.6 | `validity` 时点语义（修前） | 只有显式给 `at` 的路由才填它 ⇒ 本轮**逐字保持** |
| 1.7 | **一致性无判据**（修前） | `rg -n "一致\|agree\|同源" tests/api tests/contracts` ⇒ **零命中** |

### 2. HTTP 读面补齐与同源（AC-2/AC-3，独立重跑）

**实跑矩阵**（`FakeMemoryStore` + 两个读面）：

| 记录 | 编排面 `disposition` | HTTP 面 `disposition` | 四样逐项相等 |
| --- | --- | --- | --- |
| 无冲突、未声明时效 | `USE` | `USE` | 是 |
| 声明冲突 | `CONFLICTED` | `CONFLICTED` | 是 |
| 被取代（反向有链接） | `SUPERSEDED` | `SUPERSEDED` | 是 |
| 既被取代又带冲突 | `SUPERSEDED`（优先级固定） | 同值 | 是 |

**既有 13 字段逐字不变**（判据逐条点名：剔除新增四样后，键集**恰好等于**改动前那 13 个）。
**`validity` 不猜**：不给时点 ⇒ `None`（**受判面用「已到复核期」的记录** —— 见下第 3 节）。

**同源**（**证据**）：HTTP 面**直接调**编排面那两个纯函数
（`disposition_of` / `_reason`）+ **同一**反向链接助手（`superseded_by_index`，本轮由私有
`_reverse_links` **改名公开**—— 它现在被两个面共用 ⇒ 属该模块的**对外面**）。
`rg -n "disposition_of\|_reason\|superseded_by_index" services/api/routers/memory.py` ⇒ 三处调用在场。

### 3. 四向反证（AC-4，独立重跑 —— **含基线门**）

| 步 | 读数 |
| --- | --- |
| **基线（未按压，必须绿）** | **GREEN**（`13 passed`）—— 「不该红时不红」的那一向 |
| `N-1` 两处不一致（HTTP 面处置被改动）| **RED**（1 例）|
| `N-2` HTTP 面凭空生造判定（不取既有纯函数）| **RED**（1 例）|
| `N-3` 既有键被改动（`provenance` 改名）| **RED**（9 例）|
| `N-4` 不给时点却填了 `validity`（猜）| **RED**（1 例）|

四条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261011-052-press-two-way.txt`（674 B / `CR=0`，
**含基线行**）。

### 4. 本轮实测到的**一处假反证臂**（如实登记，已修 —— **由本轮新增的基线门当场抓到**）

**`N-4` 初版是假反证臂**：`test_the_http_face_still_does_not_guess_validity` 初版用了一条
**没有任何时效声明**的记录 ⇒ 「不猜」与「拿挂钟猜」**两种行为都返回 `None`**
⇒ 该断言**区分不了两件事**，按压 `N-4` 报 **GREEN**（**反证臂失效**）。

**为什么这次能立刻发现**：本轮按 GOAL-052 frontmatter §8 的新增纪律，给反证脚本加了
**基线门 + 按压门**（基线必须绿、每条按压必须红，否则**非 0 退出**）⇒ 第一次跑就报
`SUMMARY presses=4 all_red_and_restored=False`。

**修法**：受判面换成**已到复核期**的记录 —— 若读面拿挂钟去猜，它会立刻报 `REVIEW_DUE`；
正确行为是 `None`（**未判定**）。修后 `N-4` **RED**。

**这一条比「判据恒假」更细**：**判据会响，但受判面选得区分不了两件事** ⇒
「有断言」≠「断言在下判断」（承 `MEM-20261009-210` 的同族纪律）。

### 5. 门链与下游同步

四道门全绿（`ruff check` / `ruff format --check` / `mypy` strict / 规模门）；
HTTP 判据 **13 passed**（原 10 + 3）。**OpenAPI 快照同轮重生成并提交**（`+24 / -0`）且
`tests/contracts/test_openapi_snapshot.py` **一字未改**、**8 passed**（承 `MEM-20261010-216`）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/api/test_memory_api.py` | **追加** 3 例 + 3 个直写助手（既有 10 例**一字未动**） | — | 见提交 | **0** |
| `services/api/dto/memory.py` | `MemoryRecordDto` **+4 字段** | **既有 13 字段一个不改名、不改语义**（纯**附加**）| `+13 / -0` | **0** |
| `services/api/routers/memory.py` | `_record_dto` **+4 赋值** + 反向链接扫描 | 既有赋值**逐字保留** | 见提交 | 见提交（`_record_dto` 的 return 体改写） |
| `adapters/canonical/memory_read.py` | `_reverse_links` → **`superseded_by_index`**（**改名公开**，两个面共用） | — | 见提交 | 见提交（仅改名，**判定一字未动**） |
| `docs/api/openapi.m13.json` | **同轮重生成**（生成器产出） | — | `+24 / -0` | — |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：HTTP 读面补齐**四样**（附加，
既有 13 字段逐字不变）、**两处同源同值**（直调同一批纯函数）、`validity` 时点语义**逐字保持**、
**四条反证全红且基线绿**。

### Warnings

- **W-1（HTTP 面的时点判定不在本轮；承 `DD-1`）**：本轮补齐的是**声明面**
  （冲突 / 反向 / 处置 / 理由）；HTTP 面**仍不**做「按时点判时效」（`validity` 只在显式给 `at`
  的路由填 —— **逐字保持**）。
- **W-2（其他读面未普查；承 `DD-2`）**：本轮对齐的是**记忆**的两个读面；
  仓里**别的**实体是否有同类差集**未普查**。
- **W-3（一致性判据只在记忆面；承 `DD-3`）**：**未**做全仓通用的一致性判据。
- **W-4（本轮实测到的假反证臂，已修；承 §8 的新增纪律）**：见第 4 节 ——
  判据**会响**但**受判面选得区分不了两件事**；修法是换受判面（用**有时效声明**的记录）。
  **登记为**「反证臂必须在**它的数据上**区分两件事」（承序 17 的 `K-2` 同族教训）。
- **W-5（`superseded_by_index` 改名公开，如实登记）**：原私有 `_reverse_links` 被两个面共用
  ⇒ 改名公开（**判定与算法一字未动**，只改可见性与名字）。
- **W-6（承继残余原样保持）**：GOAL-051 的 `CC-1`…`CC-3`；GOAL-050 的 `BB-1` / `BB-3`；
  GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
  GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
