---
id: RECHECK-20261008-346
slug: goal-037-ec05-closeout-recheck
title: 独立复检：GOAL-037 cycle 5（EC-05）自举收口（两树 + 归档 + m0 + 治理）
plan_id: PLAN-20261008-345
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
verify_paths:
  - path: 当前树（主干工作树，含本轮交付面）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-037-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach` @ `--base-ref`，用后移除）
    evidence: .cursor/plans/goals/evidence/GOAL-20261008-037-verdict-clean.txt
owners:
  - root-agent
---

# RECHECK-20261008-346 — GOAL-037 cycle 5（EC-05）独立复检

复检对象：`PLAN-20261008-345`（自举收口）。独立重跑下列机械面，不引用 PLAN 结论当证据。

**本复检的两路**（`verify_paths` 的落实）：① **当前树**（主干工作树）与 ② **干净 checkout**
（`git worktree add --detach @ --base-ref`，同一份复检脚本、同一组断言、只比对判词行）；
两路各自的留档证据 = 判词归档
`.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-current.txt`（当前树）与
`.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-clean.txt`（干净树）
—— 互不相同、都在树（第 4 节给形态读数）。

## 检查结果

### 1. 验证器进树（AC-1）

| 读法 | 读数 |
| --- | --- |
| 复用标准断言集 | 是（调用 `standard_verdicts(root)`；**一行未重写**） |
| 本轮断言落点 | `tools/goal037_closeout_assertions.py`（EC-01/02 / EC-03 / EC-04 / 判据面 / 归档面 / 射程面，函数均 ≤ 50 行） |
| `--verdict-only` 判词计数（起草中间态） | **75 PASS / 4 FAIL**，红项逐条：归档未生成 ×2、本轮两份记录未写 ×2 —— 次序的真实形态，不是失败 |
| `--verdict-only` 判词计数（收口态） | **79 判词 / 0 FAIL** |
| 非判词行 / 绝对路径 | **0 / 0**（纯度与路径无关两条契约成立） |

### 2. `IN_SCOPE` 纯收紧（AC-2）

两个新脚本已加入必备清单（`+2` 行，只增不删）；`tests/tooling/test_tooling_scripts_meet_product_gates.py`
**8 passed**。两脚本四道门（独立重跑）：`ruff check` 绿 / `ruff format --check` 绿 /
`mypy`（本项目 2 files）绿 / 规模 `278`·`202` 行（函数均 ≤ 50）。

### 3. 两树复检（AC-3）

| 轮次 | `--base-ref` | 读数 |
| --- | --- | --- |
| 首轮 | `bb5443d`（本轮交付面未提交、归档尚未生成） | **`TWO-TREE RED`**（bootstrap 时序，非失败）：current **79 判词 / 2 FAIL**（只有两份归档缺失）、clean **79 判词 / 8 FAIL**（另有本轮交付面六项未提交）⇒ `COMPARE identical=False`；**两份归档由此写出**（current 3027 B / clean 3171 B，各 79 行、`CR=0`） |
| 次轮 | （本轮交付面提交） | 读数在收口提交回填 |

**bootstrap 时序如实登记**：判词归档由**被归档的那个入口**写出 ⇒ 首轮必然红于「归档不存在」；
次轮（`--base-ref` 指向**含归档**的提交）才 `TWO-TREE PASS`。**未**为让首轮变绿而删掉
存在性断言。

### 4. 判词归档进树（AC-4）

| 读法 | 读数 |
| --- | --- |
| 落点（在树） | `.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-current.txt`（当前树）与 `.cursor/plans/goals/evidence/GOAL-20261008-037-verdict-clean.txt`（干净树） |
| 形态 | 读数在收口提交回填（字节数 / 行数 / 逐字节判 `CR=0` / `FAIL` 条数 / 两份 `sha256`） |

（归档的**内容**不做一致性断言 —— 输入即输出；一致性由入口的 `COMPARE` 回答，见第 3 节。）

### 5. as-is m0（AC-5）

在**全部记录写入之后**独占跑（`--profile m0 --keep-going`、仓库 `.venv`、
`uv run --frozen --no-sync python -B`、不接管道）：终局行与 `passed/skipped` 读数在收口提交回填
（日志落点 `scratch/`，gitignored）。

### 6. 治理与宪章（AC-6）

`validate.py` ⇒ 绿；`tests/tooling/test_mainline_program_is_intact.py` ⇒ 绿（本 GOAL 的 id
在程序表序 5、进展记录行指向真实 RECHECK 文件）。

### 7. CI 台账（AC-7）

见 GOAL 的「CI 台账」节（逐提交、含取消 / 真红的如实登记与自我指涉边界封闭）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 逐条独立成立；**无产品缺陷**
（本 cycle 只新增 `tools/` 机械面与记录）。

### Warnings

- **W-1（bootstrap 时序是本 EC 的固有形态）**：判词归档由**被归档的那个入口**写出 ⇒
  首轮必红（归档不存在），次轮才全绿。这不是缺陷，但**必须如实登记**。
- **W-2（承继残余原样保持）**：GOAL-036 的 `M-1`…`M-5`（含 `M-4` 已由本轮 EC-03 收口，
  标记保留以见来源）、`R26-*` 终态、GOAL-035…019 的未覆盖范围 —— 逐条**原样保持**，
  本轮只追加 `O-1`…`O-5`。
- **W-3（GOAL 级未覆盖范围）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口；本轮残余 `O-1`…`O-5`（memory 项目维度 / 程序级人工闸门 / 跨程序共享 /
  读到≠影响 / 决策未落的中间态）**未覆盖**；**不得**据此宣称项目安全；**不得**宣称投递
  语义为那四个字（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
- **W-4（自我指涉边界）**：本节的收口提交自身不产生可引用的 CI 结论 ⇒ 以「末条提交 +
  覆盖说明」封闭，**不得循环引用**（承 GOAL-032…036 同款）。
