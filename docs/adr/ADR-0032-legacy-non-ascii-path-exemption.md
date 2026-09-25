# ADR-0032 — 既有非 ASCII 路径的豁免（Legacy Non-ASCII Path Exemption）

Status: Accepted
Date: 2026-09-25
Deciders: Eswink（single owner）
Scope: `AGENTS.md` §13（Repository Path Naming）、`tests/architecture/module_file_naming.py`
（`LEGACY_PATH_EXCEPTIONS`）、`docs/architecture/POLICY_SURFACE_AUDIT.md`（同名口径的先例）

## Context

`AGENTS.md` §13 规定**新建或重命名**的仓库路径必须使用「有意义的英文语义名」，
仅使用 ASCII 字母、数字与按语境需要的 `-` `_` `.`。该规则**实施晚于**本仓的一部分文件：
当时已有一批路径使用中文文件名。2026-09-25 实测（`git -c core.quotepath=false ls-files`）：

- 已跟踪路径 **3389** 条，其中含非 ASCII 字符的 **30** 条；
- 这 30 条**全部**是**历史资产**（迁移脚本、个人生产复审记录与工具、控制台重建期的计划文件），
  其中 14 条同时被 `tests/architecture/module_file_naming.py` 的 `LEGACY_PATH_EXCEPTIONS`
  登记（那是**另一条更窄**的规则：源码文件名 / 目录名的 snake_case 等约束）。

**枚举它们有一个陷阱（实测）**：`git ls-files` 默认受 `core.quotepath` 影响，非 ASCII 路径
会被转义成 `"tests/worker/test_\350\256\241\345\200\217\350\247\202v1.py"` 这种形态
⇒ 用「路径里有没有非 ASCII 码点」去判，会得到 **0 条**（**假绿**）。
必须用 `git -c core.quotepath=false ls-files`。本条记录在下方「Evidence」里，
因为「怎么数」本身就是这条决定的一部分。

## Decision

**这些既有路径按豁免处理，不重命名。** 具体三条：

1. **不批量重命名**（依据 `AGENTS.md` §13 的明文：「既有历史路径不会仅为满足本规则而批量重命名」）。对这些文件，**豁免**不与规则冲突——规则约束的是**新建 / 重命名**，
   而豁免恰是**不重命名**。
2. **豁免不等于放宽规则**：**新建**路径（以及任何被重命名的路径）仍**必须**满足 §13；
   本 ADR **不**修改、**不**弱化 `AGENTS.md` §13 或任何门禁的强度。
3. **豁免有显式清单**：30 条路径逐条在下文列出；`tests/architecture/module_file_naming.py`
   的 `LEGACY_PATH_EXCEPTIONS` 是**另一条**规则的清单（14 条非 ASCII 源码路径 +
   12 条 TypeScript PascalCase 历史名），两者**不互相替代**，也**都不得**用来放行新文件。

## 为什么不重命名

- **触碰不可变历史资产**：其中的迁移脚本（`adapters/postgres/migrations/010_GPU显存计量宽度v1.sql`、
  `adapters/postgres/migrations/011_GPU时间精度v1.sql`、`adapters/postgres/migrations/012_执行用量重放v1.sql`）
  已被应用过，重命名会改写「迁移的标识」；个人生产复审记录（`docs/operations/`、
  `tools/PA1R*`）是当时的验收证据，改名会让既有记录里的引用指向不同的对象。
- **引用面大、收益为零**：这些路径被 import、被计划/复检记录、被 m0 的 check 名称、
  被 SHA-256 清单（`release-assets-immutable`）引用；改动它们要么制造大量无意义 diff，
  要么直接与「不可变资产」判据冲突。**产品行为与安全性一行都不会因此改变。**
- **规则的目标已达成**：§13 要防的是「**新**路径继续长成非 ASCII 形态」——
  这一条由规则的适用范围与既有判据把守，不需要靠历史重命名来证明。

## 边界与约束（明确不因本 ADR 而松动的部分）

- **不得**用本 ADR 为**任何新**的非 ASCII 路径开脱；新增即判红（规则 + 判据都不动）。
- **不得**新增第二个豁免清单；需要豁免的新条目必须走**修订本 ADR**。
- **不得**把本 ADR 读成「`AGENTS.md` §13 已被放宽」——它记录的是一次**一次性**的历史豁免。
- 本 ADR **零代码改动**：不重命名、不改 `AGENTS.md`、不改任何门禁或判据。

## Consequences

- 30 条历史路径**保持原名**，引用它的 import / 记录 / 清单**全部不变**。
- 「豁免」从口头口径变成**可引用的依据**：后续审计只需引用本 ADR + 实跑一次
  `git -c core.quotepath=false ls-files`，不必跨记录拼理由。
- **若这 30 条中的某一条因别的原因被重命名**（例如该模块整体重写）：新名字**必须**满足
  §13，且**同步**更新本 ADR 的清单（若该条同时属于 `tests/architecture/module_file_naming.py`
  的 `LEGACY_PATH_EXCEPTIONS`，一并更新）——清单与现实的漂移由判据
  `tests/tooling/test_landed_decisions_are_citable.py` 把守。

## Evidence / References

- 规则来源：`AGENTS.md` §13（Repository Path Naming）——「既有历史路径不会仅为满足本规则而
  批量重命名；一旦任务本身要求重命名该路径，新的名称必须满足本节」。
- 枚举命令（**必须**带 `-c core.quotepath=false`）：
  `git -c core.quotepath=false ls-files` ⇒ 3389 条中 **30** 条含非 ASCII。
- 判据：`tests/tooling/test_landed_decisions_are_citable.py`
  （实跑 `git` 数出来、与本文清单**双向**比对、并按压「清单被删空」与「新增非 ASCII 路径」
  两种形态）。
- 先例：`docs/architecture/POLICY_SURFACE_AUDIT.md`（同名豁免口径：把「不做什么」写成
  逐条清单而不是散文）。
- 同源登记：`docs/INDEX.md`。
- 拍板：`GOAL-20260925-016` 的 **D-09 → 取 (a)**（用户 2026-09-25 按
  `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板：「出一份 ADR 记录豁免，
  **不重命名**」）。

### 豁免清单（30 条，逐条可核对）

计划与复检记录（8 条）：

```text
.cursor/plans/m14_债务与_not-verified_收口计划_8f4a7bc8.plan.md
.cursor/plans/m16_分布式执行_1657b1d6.plan.md
.cursor/plans/rechecks/RECHECK-20260905-030-个人生产续审v2.md
.cursor/plans/rechecks/RECHECK-20260906-031-源码封存子门禁v1.md
.cursor/plans/rechecks/RECHECK-20260906-032-个人生产最终复审v1.md
.cursor/plans/research_console_全站重建_9c821507.plan.md
.cursor/plans/控制台高保真重建_9be64bbc.plan.md
.cursor/plans/根目录分类归档_2913593b.plan.md
```

源码与迁移（6 条）：

```text
adapters/execution/容器归属v1.py
adapters/postgres/migrations/010_GPU显存计量宽度v1.sql
adapters/postgres/migrations/011_GPU时间精度v1.sql
adapters/postgres/migrations/012_执行用量重放v1.sql
packages/application/m12_reference/恢复生命周期v1.py
packages/application/m12_reference/证据重放v1.py
```

运行与工具（9 条）：

```text
services/worker/计量观测v1.py
docs/operations/PA1R发布记录v1.json
docs/operations/PA1R独立个人生产复审v1.md
tools/PA1R发布真相v1.py
tools/PA1R密钥审计v1.py
tools/PA1R恢复闭包v1.py
tools/PA1R故障演练v1.py
tools/PA1R质量门禁v1.py
tools/PA1R运行演练v1.py
```

测试（7 条）：

```text
tests/adapters/execution/test_容器归属v1.py
tests/adapters/execution/test_重放计量v1.py
tests/adapters/test_重连事务边界v1.py
tests/postgres/test_GPU显存宽度v1.py
tests/tooling/test_个人生产续审v2.py
tests/tooling/test_恢复生命周期v1.py
tests/worker/test_计量观测v1.py
```
