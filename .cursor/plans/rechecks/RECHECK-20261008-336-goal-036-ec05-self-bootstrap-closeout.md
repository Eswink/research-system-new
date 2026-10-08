---
id: RECHECK-20261008-336
slug: goal-036-ec05-closeout-recheck
title: 独立复检：GOAL-036 cycle 3（EC-05）自举收口（两树 + 归档 + m0 + 治理）
plan_id: PLAN-20261008-335
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
verify_paths:
  - path: 当前树（主干工作树，含本轮未提交的交付面）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-036-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ `--base-ref`，用后移除）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-036-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20261008-336 — GOAL-036 cycle 3（EC-05）独立复检

复检对象：`PLAN-20261008-335`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。

**本复检的两路**（`verify_paths` 的落实）：① **当前树**（主干工作树）与 ② **干净 checkout**
（`git worktree add --detach @ --base-ref`，同一份复检脚本、同一组断言、只比对判词行）；
两路各自的留档证据 = 判词归档
`.cursor/plans/goals/evidence/GOAL-20261008-036-verdict-current.txt`（当前树）与
`.cursor/plans/goals/evidence/GOAL-20261008-036-verdict-clean.txt`（干净树）
—— 互不相同、都在树（第 4 节给形态读数）。

## 检查结果

### 1. 验证器进树（AC-1）

| 读法 | 读数 |
| --- | --- |
| 复用标准断言集 | 是（调用 `standard_verdicts(root)`；**一行未重写**） |
| 本轮断言落点 | `tools/goal036_closeout_assertions.py`（EC-02 承接链 / EC-03 真用 / EC-04 登记面 / 判据面例数下界 / 归档形态 / 射程面，函数均 ≤ 50 行） |
| `--verdict-only` 判词计数（起草中间态，本条为**起草自纠的取证**） | **65 PASS / 6 FAIL**，红项逐条：例数下界起草错误 ×1（原写 `10`，实测 **7** ⇒ 下界不可能满足 = 判据永红）、归档未生成 ×2、本轮两份记录未写 ×2、残余标记未定格 ×1 |
| 残余标记面的**假绿**取证（起草期实测） | 裸子串 `M-1` / `M-2` 被 `MEM-160` / `MEM-20261008-197` **偶然命中** ⇒ 残余登记面在**未写任何残余**时判绿；收紧为**回引号形态** `` `M-1` `` 后，同一中间态**逐条判红**（上面的 `residuals-enumerated` 六项一次报出） |
| `--verdict-only` 判词计数（收口态） | **71 判词 / 0 FAIL** |
| 非判词行 / 绝对路径 | **0 / 0**（纯度与路径无关两条契约成立） |

### 2. `IN_SCOPE` 纯收紧（AC-2）

两个新脚本已加入必备清单（`+2` 行，只增不删）；`tests/tooling/test_tooling_scripts_meet_product_gates.py`
**8 passed**。两脚本四道门（独立重跑）：

| 门 | 读数 |
| --- | --- |
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `2 files already formatted` |
| `mypy`（strict） | `Success: no issues found in 2 source files` |
| 规模（450 行 / 函数 50 行） | `tools/goal036_closeout_assertions.py` **250** 行 / `tools/verify_goal036_closeout.py` **192** 行 |

### 3. 两树复检（AC-3）

| 轮次 | `--base-ref` | 读数 |
| --- | --- | --- |
| 首轮 | `43a8e80`（本轮交付面未提交、归档尚未生成） | **`TWO-TREE RED`**（bootstrap 时序，非失败）：current **71 判词 / 2 FAIL**（只有两份归档缺失）、clean **71 判词 / 5 FAIL**（另有本轮交付面四项未提交：`IN_SCOPE` 两脚本、两份记录、残余标记）⇒ `COMPARE identical=False`；**两份归档由此写出**（`current` `d97bb522…` / `clean` `3b4777a6…`） |
| 次轮 | `1551d2f`（本轮交付面与归档已提交） | **`TWO-TREE PASS`**，两路 **71 判词**、`sha256` **相同** `8ad58ebc…`、`COMPARE identical=True` |

**bootstrap 时序如实登记**：判词归档由**被归档的那个入口**写出 ⇒ 首轮必然红于「归档不存在」
（两棵树都还没有归档文件）；次轮（`--base-ref` 指向**含归档**的提交）才 `TWO-TREE PASS`。
**未**为让首轮变绿而删掉存在性断言。

### 4. 判词归档进树（AC-4）

| 读法 | 读数 |
| --- | --- |
| 落点（在树） | `.cursor/plans/goals/evidence/GOAL-20261008-036-verdict-current.txt`（当前树）与 `.cursor/plans/goals/evidence/GOAL-20261008-036-verdict-clean.txt`（干净树） |
| 形态（**次轮定格**） | 两份各 **2566 B / 71 行 / `CR=0`（逐字节判）/ `FAIL` 0 条**；两份 `sha256` **相同** `8ad58ebc2b53163f61b57de9e26059ac4e7058c259187328fb5e834376e923c5` |
| 首轮（bootstrap）形态 | 两份各 71 行、含 FAIL 行（current 2600 B / clean 2712 B）—— 由**首轮自己**写出，次轮被**同字节**改写为上面的定格形态；两轮都如实登记 |

（归档的**内容**不做一致性断言 —— 输入即输出；一致性由入口的 `COMPARE` 回答，见第 3 节。）

### 5. as-is m0（AC-5）

在**全部记录写入之后**独占跑（`--profile m0 --keep-going`、仓库 `.venv`、
`uv run --frozen --no-sync python -B`、不接管道）：终局行与 `passed/skipped` 读数在收口提交回填
（日志落点 `scratch/`，gitignored）。

### 6. 治理与宪章（AC-6）

`validate.py` ⇒ 绿；`tests/tooling/test_mainline_program_is_intact.py` ⇒ 绿（本 GOAL 的 id
在程序表序 4、进展记录行指向真实 RECHECK 文件）。

### 7. CI 台账（AC-7）

见 GOAL 的「CI 台账」节（逐提交、含本批真红 / 取消的如实登记与自我指涉边界封闭）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 逐条独立成立；**无产品缺陷**
（本 cycle 零产品改动：只新增 `tools/` 机械面与记录）。

### Warnings

- **W-1（bootstrap 时序是本 EC 的固有形态）**：判词归档由**被归档的那个入口**写出 ⇒
  首轮必红（归档不存在），次轮才全绿。这不是缺陷，但**必须如实登记**（否则「首轮红」
  会被误读成失败）；本节与 PLAN 的 AC-3 都写明了。
- **W-2（起草期两条自纠**）：本轮新增断言集里有两处**起草错误**在编入树之前被门链自己抓到
  —— ① 例数下界取了未实测的 `10`（实测 7 例）⇒ 判据永红；② 残余标记用裸子串 ⇒ 被
  `MEM-160` 偶然命中而**假绿**。两条都**修的是判据/断言本身**（收紧到可满足、可证伪的形态），
  未触碰任何既有判据；取证见第 1 节。
- **W-3（承继残余原样保持）**：GOAL-035 的 `N-1`…`N-6`、GOAL-034 的 `W-1`…`W-4`、
  GOAL-033 的 `W-1`…`W-6`、GOAL-032 的 `W-1`…`W-8`、历史 `tools/` 的旧 lint 与旧脚本
  —— 逐条**原样保持**，本轮只追加 `M-1`…`M-5`。
- **W-4（GOAL 级未覆盖范围）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；本轮残余 `M-1`…`M-5`（登记表余量 / 多评审者聚合 / 读面未认证 /
  跨 run 读取未实跑 / 结论未证影响科学决策）**未覆盖**；**不得**据此宣称项目安全；
  **不得**宣称投递语义为那四个字（**明确否认**；口径只能是 at-least-once + idempotency +
  deduplication）。
- **W-5（自我指涉边界）**：本节的收口提交自身不产生可引用的 CI 结论 ⇒ 以「末条提交 +
  覆盖说明」封闭，**不得循环引用**（承 GOAL-032…035 同款）。
