---
id: MEM-20260928-156
title: "判据「受判集合为空」时它尚未生效：必须在第一条真实受判记录上按压一次，才算把这条义务收口"
status: ACTIVE
created_at: 2026-09-28
updated_at: 2026-09-28
scope: repository
confidence: 0.9
review_after: 2027-03-28
source_plans:
  - .cursor/plans/tasks/PLAN-20260928-217-goal-022-ec04-closeout-two-tree-self-bootstrap.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260928-218-goal-022-closeout-recheck.md
supersedes: []
tags: [press-testing, vacuous-green, self-bootstrap, closeout, goal-022, ec-04]
---

## 做了什么

GOAL-022 的 EC-02 交付了一条记录面判据（`tests/architecture/python/test_declared_recheck_paths_have_evidence.py`）：
**收口复检**必须用 `verify_paths` 声明**每一路**跑法，且每路各自有独立、被正文引用的证据。
它交付时**受判集合是空的** —— 受判起点是 GOAL 建档日，此前没有新收口复检 ——
于是它的复检如实登记了 `W-1`：**判据今天没有真实执法对象**，
「会不会在第一条真实记录上生效」**未收口**。

EC-04（收口轮）把这件事**实证收口**了，做法分三步：

1. **让受判集合不再为空**：EC-04 自己的收口复检记录 `RECHECK-20260928-218`
   （`slug: goal-022-closeout-recheck`、`created_at: 2026-09-28`）**就是**第一条受判记录；
   实测扫描面 **4 → 5** 条、**受判集合 0 → 1** 条、`outstanding = 0`；
2. **在它身上按压**：把该记录 frontmatter 的 `verify_paths` **整块抹掉** ⇒
   判据判红 `1 failed, 8 passed`，失败消息**逐字点名这条记录**
   （`缺少 verify_paths（收口复检必须声明它跑过的每一路）`）；
3. **逐字节复原**：按 raw `sha256` 复原同一文件（前后一致）⇒ 判据判绿 `9 passed`。

## 为什么这样做

**「判据在 `tmp_path` 夹具上绿」与「判据在仓库里真的执法」是两件事。**
夹具证明的是**逻辑**成立；只有一条**真实受判记录**被按压并判红，才证明这条义务
**已经在生效**。受判集合为空时的绿是**空真**（vacuously true）—— 它不是假绿，
但它**不能**被读成「已经管住了」。

这条形态在别处也成立：任何「新加一条门禁 / 判据 / 校验」的交付，
交付当时的绿灯只说明**没人违规**，不说明**违规会被抓到**。
差额只能靠「**第一条真实受判对象 + 按压**」补上。

**自举**是补这个差额的最省形态：让**收口轮自己的记录**充当那条受判对象
（收口复检本来就该有 `verify_paths`）⇒ **不注入任何合成物**、不动既有记录、
不需要额外夹具，就能在真实数据上按压一次。

## 怎么做与复现

```bash
# ① 看受判集合是否为空（判据的公开面，不是记录的自述）
uv run --frozen --no-sync python -B -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location('j', 'tests/architecture/python/test_declared_recheck_paths_have_evidence.py')
m = importlib.util.module_from_spec(spec); sys.modules['j'] = m; spec.loader.exec_module(m)
allr = list(m.closeout_records(m.RECHECKS_DIR))
print('scan face =', len(allr), '| obligated =', len([r for r in allr if m.is_obligated(r[1])]))
"

# ② 按压：抹掉受判记录的 verify_paths ⇒ 期望红（失败消息须点名该记录）
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_declared_recheck_paths_have_evidence.py -q

# ③ 复原：raw sha256 必须与按压前逐个字符一致（不要用 git diff 判）
sha256sum .cursor/plans/rechecks/RECHECK-20260928-218-goal-022-closeout-recheck.md
```

实测判词：按压后 `1 failed, 8 passed`；复原后 `9 passed`；
`declared_path_problems(本条) = []`、`outstanding = 0`。

## 适用边界

- 只在「**受判集合由记录组成、且记录可写**」的判据上成立。
  受判集合由**不可变历史**组成（例如 `created_at` 早于建档日的历史记录）时，
  **不得**为了凑一条受判对象去回填它们 —— 那等于改写历史。
  若受判集合**结构上**永远为空，那说明判据**该判别的对象不存在** ⇒ 应重新设计，而非按压。
- 按压**必须逐字节复原**（raw `sha256`），且复原后要重跑一次确认绿；
  只按「我改回来了」判断会漏掉行尾 / 编码 / 空行的漂移（承 `MEM-20260927-152`）。
- 自举能证明「判据对**这一条**记录执法」，**不**证明判据的断言集完备，
  也不证明**别的**记录不会漏声明。它是**下限证据**，不是覆盖率证明。
- **不得**由本条推出任何安全结论；它只是**过程质量**的形态。

## 来源

- `PLAN-20260928-217`（EC-04 收口轮：自举两树复检 + 本实证）
- `RECHECK-20260928-218`（收口复检：`三、自举实证` 一节逐项留档）
- 被收口的 `W-1` 出自 `RECHECK-20260928-214`（EC-02 复检的「最要紧的诚实边界」）
- 相关：`MEM-20260928-155`（按压记录面判据 = 注入一条记录）、
  `MEM-20260927-152`（按压/复原必须二进制读写）
