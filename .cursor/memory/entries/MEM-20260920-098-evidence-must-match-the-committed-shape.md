---
id: MEM-20260920-098
title: "证据必须对应提交的形态：产生观测的代码一旦被重构，观测即过期——50 行函数上限对测试文件同样有效"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-124-live-failure-path-semantics.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-124-live-failure-path-semantics.md
supersedes: []
tags:
  - testing
  - evidence
  - live
  - source-limits
  - goal-009
---

# 证据对应提交形态 + 50 行上限对测试同样有效（GOAL-009 cycle 4）

## 做了什么

GOAL-009 EC-04 要一条**实跑反证**：用**故意无效**的凭据跑一次，证明「门开但调用被拒 ⇒
run 落 `FAILED` 终态、失败原因非空、tokens 0、失败消息不含凭据值」。新增 live 用例
`tests/e2e/test_live_failure_paths.py::test_live_invalid_credential_fails_loudly_without_leaking`，
跑出 `1 passed`：**1 次出站** ⇒ `POST https://apihub.agnes-ai.com/v1/chat/completions`
⇒ **`401 Unauthorized`**，观察文件 `{"run_state":"FAILED","failure_count":1,"usage_entries":0,"credential_leaked":false}`。

随后全量 m0 **红了**，红项是
`tests/tooling/test_python_source_size_limits.py::test_python_source_size_limits[tests\e2e\test_live_failure_paths.py]`：
那个**用例函数 58 行**，超过本仓 **50 行**函数上限。

## 为什么这样做

两件都容易被做错：

1. **50 行上限对 `tests/**` 一样生效**（`test_python_source_size_limits.py` 的
   `PRODUCT_ROOTS` 含 `tests`）。写 live 用例时最容易把它写成一条长流水线
   （判门 → 发起 → 读终态 → 读失败 → 读用量 → 写观察文件），一写就超。
   处置是**拆函数**，**不是**调阈值。
2. **观测是「某个代码形态」的观测**。拆函数之后，那次 `1 passed` 的观测对应的是
   **拆之前**的文件——逻辑没变，但**提交进去的是拆之后的版本**。
   若把旧观测当证据记下来，就会出现「证据指向一个从未被提交的形态」，
   与 [[MEM-20260920-096]]（本地门读工作树、CI 读提交）是**同一类错**的另一面。

## 怎么做与复现

**写 live 用例时的默认形状**（每个函数都在 50 行内）：

```python
@dataclass(frozen=True, slots=True)
class _Reads: ...            # 观察快照

def _assert_gate_is_open() -> Any: ...   # 先判「门开」，否则失败可能来自门关
def _run_with(endpoint, submitted) -> _Reads: ...   # 发起 + 读回
def test_...() -> None: ...  # 只剩断言，十几行
```

**判据（push 之前自查）**：

```bash
# 1) 有没有函数超 50 行（含 tests/）
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_size_limits.py -q -p no:randomly
# 2) 若刚重构过「产生 live 观测」的代码 ⇒ 观测已过期，重跑一次（live 用例仍取最小次数）
```

**红项识别**：m0 的 `FAILED: 1 check(s): python/tests=1` + `存在超过 50 行的函数: [(name, N)]`
⇒ 拆函数，不要动阈值。

## 适用边界

- **适用于**：任何「代码跑出观测 → 观测被写进 RECHECK/GOAL」的路径（live 用例、
  基准脚本、探针）；以及 `tests/**` 下新增较大用例时的自查。
- **不适用于**：**纯文档/记录类**改动——它们不产生运行时观测，改文笔不影响证据。
  也不适用于「字段重命名但行为等价」的纯机械改写：那仍建议重跑，但不是硬要求。
- **不要**把这条读成「重构后必须无限重跑」：本仓的口径是**次数取最小必要**，
  所以**先拆完函数、再跑**，而不是跑完再拆。相关：[[MEM-20260920-096]]、[[MEM-20260920-097]]。

## 来源

- 红：m0 第 1 轮 `FAILED: 1 check(s): python/tests=1`
  （`test_python_source_size_limits[tests\e2e\test_live_failure_paths.py]`，函数 58 行）
- 绿：m0 第 2 轮 `PASS: profile=m0; 23 deterministic checks`（`4239 passed, 13 skipped`）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-124-live-failure-path-semantics.md` 的 **D 节 / m0 结果**
- 计划：`.cursor/plans/tasks/PLAN-20260920-124-live-failure-path-semantics.md`
- 目标：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
