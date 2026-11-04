---
name: criterion-authoring
description: Use when adding or changing a criterion in this repo — a test, an assertion, a validator rule, or a gate — especially when a targeted suite is already green and you are about to run the full m0 profile. Covers the probe-first order, the four static gates, the size limits, the press-and-restore drill, and the witness sealing order. Not for loosening an existing gate or for adjusting a threshold to make something pass.
---

# Criterion Authoring

新判据自身的缺陷**只有全量门能抓到**。定向套件绿是必要条件，不是交付条件。

## 顺序（不可跳步）

1. **probe**：`uv run --frozen --no-sync python -B -c '...'` 先跑通最小复现，确认夹具/接口的真实行为。不要凭读代码写断言。
2. **定向套件**：`uv run --frozen --no-sync python -B -m pytest <files> -q`。必须用仓库 `.venv`——系统 Python 会伪造 mypy / lint-imports 的假红。
3. **静态门**（改动文件）：`ruff check`、`ruff format --check`、`mypy`。三道是**不同**的门：`ruff check` 的行宽 100 与 `ruff format` 是两回事。
4. **全量 m0**：`uv run --frozen --no-sync python -B tools/run_m0_with_witness.py`。新判据文件自己的三类缺陷只在这里暴露：mypy 可选类型未收窄、显式清单未登记、函数超 50 行（含 `test_`）。
5. 判 m0 **只看终态行** `PASS: profile=m0; 23 deterministic checks`；`grep -c` 零匹配会以 exit 1 误报失败。

## 硬规则

1. **用仓库的 `Fake*` 类**，不手搓 `__getattr__` dummy。手搓 dummy 与 Protocol 不匹配时只报 `arg-type`，而这条只在全量 mypy 出现。
2. **strict mypy 下 `# type: ignore` 是 syntax error**。需要窄化时用 `cast`，不要用 ignore。
3. **规模门先量再动手**：`git show HEAD:<file> | wc -l`。贴线文件（本仓 450 行上限）加行时必须同时腾出等量行——把函数抽到**已有归属**的文件，不压注释换行。
4. **按压证明**：改真值 ⇒ 确认**恰好**预期条数变红 ⇒ 复原并核 `sha256`。多红或少红都说明判据打偏了。
5. **判据不得被收窄**：改判据让它变绿是最后手段，且必须写进记录并说明为什么旧判据本身是错的。
6. **见证在记录定稿之后封**：记录定稿 → 跑 m0 → **只提交见证** → 不再改树。先跑门后写记录等于记录从未被门覆盖。
7. **记录面本身是受判面**：先写记录再跑门。解释一条禁令时**不要复制禁令字面量**——自己的扫描会因引用而判红。

## 反证臂的最低要求

一条判据至少三种臂：正向（该过）／反证（该红）／边界（邻近但不同）。反证臂必须落在**出厂目录之外**，并且按压后确认它**真的红了**——判据调用会 skip 的函数时，判据自己也 skip，而 skip 不是红。

## 陷阱

- **`tools/` 不在产品门禁射程内**：新脚本必须显式登记分类清单，否则「没有分类」判据红；登记后才受四道门约束。
- **共享协议声明/DTO 改动会打到所有组合根**：定向套件绿 ≠ 全量绿。
- **索引不得后写覆盖**：新增登记项要追加，不要重排序既有条目。
- **一次推送一个 cycle**：CI 的 `cancel-in-progress` 会取消在飞的 m0 run。
