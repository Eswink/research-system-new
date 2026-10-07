---
id: RECHECK-20261008-316
slug: goal-033-ec03-resume-coverage-declaration
title: 独立复检：GOAL-033 cycle 3（EC-03）续跑覆盖矩阵机械化
plan_id: PLAN-20261008-315
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-316 — GOAL-033 cycle 3（EC-03）独立复检

复检对象：`PLAN-20261008-315`。**独立重跑**下列判据与按压，不引用 PLAN 结论当证据。

## 检查结果

### 1. 声明集逐条核（**复检自己重数的**，不看 PLAN 的汇总）

| 读法 | 读数 |
| --- | --- |
| 声明集规模 | **14**（`grep -c "DeclaredCase("` 与 `len(DECLARED_CASES)` 两个读法一致） |
| `HANDLED` | **2**（≥ 下界 2） |
| `REFUSED` | **6**（≥ 下界 6） |
| `NOT_THIS_ENTRY` | **5**（≥ 下界 5；另有一条 `boundary-sqlite-vs-pg-attachment` 也属此面 ⇒ 实际 6） |
| 走 `reason` 的条目 | 1（理由长度 ≥ 30 字符） |

> 复检注：判定面的**下界**与实际条数不必相等（下界是防写窄，不是等式）；复检确认三类
> 都**非空**且各自达到下界。

### 2. 判据重跑

```
tests/tooling/test_resume_coverage_declaration_matches_source.py ...... [100%]  6 passed
```

**幽灵引用面**：复检**逐条**把 13 个 `evidence` 的 `文件::用例名` 拿去目标文件里找函数定义
（独立于判据的实现）⇒ 全部命中，零幽灵。

### 3. 与源码对账（复检独立核）

- 入口 `services/api/run_resume.py` 里的 `ResumeAttempt(refusal="…")` 字面量：**2 条**
  （`run orchestration service is not configured` / `rebuilt preflight does not pass; refusing to resume`）
  ⇒ 两条都在声明集里有**恰好一条**归属（`source_literals`）。
- 复检确认**边界**：异常路径是**拼装**的（`dependency_prefix()` + 异常名）⇒ 无逐条字面量，
  声明集按**情形**归属（`refused-unresolvable-source` / `refused-semantic-drift`）——
  这不是漏项，是**如实划界**。

### 4. 按压独立重跑

```
BASELINE_GREEN 6 passed
P1_RED exit=1 1 failed, 5 passed
P2_RED exit=1 3 failed, 3 passed
RESTORED True resume_coverage_declaration.py 6f40eef99d10->6f40eef99d10
FINAL_MATCHES_BASELINE True 6 passed
```

- **复检确认了 P2 的返工**：首版 P2 用字符串切片删条目 ⇒ 被条目内多行 `reason=(...)` 的
  `),` 骗到 ⇒ 产出**语法错** ⇒ `exit=2`（**收集错**）。**那读数不可用**（它不是判红）。
  改为 AST 定位后 `exit=1 3 failed`。
- `RESTORED True` 带 sha ⇒ 二进制安全写盘生效。

### 5. 既有判据零改动

`git diff --numstat -- tests/e2e`: **空**（`test_research_continuity_coverage_matrix.py`
一字未动）；`git status --short` 对 `tests/**` 只有新增。

### 6. 门

`ruff check` / `ruff format --check` / `mypy`（两个新文件）绿；
`tests/tooling` **1364 passed**（含本轮 6 例）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-7 独立重跑成立；**无产品缺陷**。

### Warnings

- **W-1（判据自身的两次假信号，均已在轮内修）**：① 首版按**散文关键词**对账 ⇒ 换成
  英文口径就误判（改了措辞也算「覆盖丢了」）；② 按压 P2 的**字符串切片**产出语法错
  ⇒ `exit=2`（收集错）被当成「判红」读。两条都是**判据/工具的形态**问题，不是产品缺陷；
  已分别修成 `source_literals` 字段与 AST 定位，并沉淀记忆 `MEM-20261008-196`。
- **W-2（声明集的完备性边界）**：声明集枚举的是**入口源码可枚举的结局面**。
  「还有没有我没枚举到的结局」不由本判据证明 —— 它由「与源码对账」（AC-3）+「判据落点
  真实存在」（AC-2）两条**共同**逼近，**不构成**「已穷尽宇宙」的宣称。
- **W-3（异常路径不做逐条字面量对账）**：拼装的异常拒绝（`前缀 + 异常名`）只按**情形**
  归属。若将来有人把某条异常改成字面量 `ResumeAttempt(refusal=…)`，AC-3 的
  `_SOURCE_REFUSALS` 需要同步（否则会漏对账）—— 这条边界写在判据的注释里。
- **W-4（不覆盖行为重跑）**：本判据判「声明集与源码/判据文件对得上账」，
  **不重跑**那些行为判据（各自文件即判据）。
- **W-5（未覆盖范围照旧）**：读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 /
  `R-M1` 未收口。**不得**据此宣称项目安全；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
