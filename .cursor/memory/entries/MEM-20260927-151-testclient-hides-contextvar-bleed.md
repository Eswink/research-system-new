---
id: MEM-20260927-151
title: "TestClient 会让 contextvar 串扰类判据不可证伪（每请求各起任务）——这类判据必须用 ASGITransport + 同任务 await"
status: ACTIVE
created_at: 2026-09-27
updated_at: 2026-09-27
scope: repository
confidence: 0.95
review_after: 2027-03-27
source_plans:
  - .cursor/plans/tasks/PLAN-20260927-205-principal-attribution-cannot-be-forged.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260927-206-principal-attribution-cannot-be-forged-recheck.md
supersedes: []
tags: [adversarial-self-check, contextvar, falsifiability, testclient-trap, goal-021, ec-03]
---

## 做了什么

给 GOAL-021 EC-03（主体归因不可伪造）写判据时，先写的是 `TestClient`（同步）版本。
**按压发现它不可证伪**：把 `PrincipalAuthMiddleware` 的 `finally: reset_current_principal(token)`
去掉后，判据**依然全绿**。改成 `httpx.ASGITransport` + **同任务 `await`** 后，
同一按压得到 **4 failed**。

## 为什么这样做

- **`TestClient` 每个请求在自己的任务/portal 里跑** ⇒ 请求内 `contextvar.set()` 的值
  **不会回传**给调用方 ⇒ 「写请求设的主体残留给下一个读请求」这一现象**在 TestClient 下看不到**
  ⇒ 判据给出**假绿**。这不是产品安全，是**观测装置的分辨率不够**。
- 三层实测（`scratch/goal021-ec03-probe-driver-shape.py`）：

  | 形态 | 基线（有 reset） | 按压（去掉 reset） | 可证伪？ |
  | --- | --- | --- | --- |
  | `TestClient`（同步） | `read=None` | `read=None` | **否** |
  | `ASGITransport` + 同任务 `await` | `read=None` | `read=service:probe-principal` | **是** |

- **并发形态另有陷阱**：`asyncio.gather` 的结果**取决于父任务上下文**——
  干净 ⇒ **0 violations**；已污染 ⇒ **20 violations**（子任务**继承**父上下文）。
  ⇒ 「并发 0 violations」在没有写明前提时**不构成**「并发安全」结论。

## 怎么做与复现

```bash
# 驱动形态对账（决定性实验：TestClient 不可证伪 / ASGITransport 可证伪）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec03-probe-driver-shape.py

# 并发前提对账（干净 0 / 已污染 20）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec03-probe-concurrency-precondition.py
```

**按压形态**：把 `finally: reset_current_principal(token)` 换成 `pass`；
用 `ASGITransport` 的判据 ⇒ **4 failed**；复原后 `sha256` 一致
（`ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`）⇒ 15 passed。

## 适用边界

- 结论针对**请求级 `contextvar` 串扰**这一类判据；对**返回值 / 响应体 / DB 状态**类判据，
  `TestClient` 通常够用（但它仍会把**异常传播 / lifespan** 的行为差异化）。
- `ASGITransport` **不出站**（纯 ASGI 调用），不违反默认门离线。
- 「同任务 `await`」是必要条件：把读写放进**两个** `asyncio.run`（或不 await 就返回）
  同样看不到残留。
- 并发用例**只能作补充覆盖**，且**必须写明前提**（父上下文干净），
  **不得**单独读作「并发安全」。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260927-205-principal-attribution-cannot-be-forged.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260927-206-principal-attribution-cannot-be-forged-recheck.md`
- 探针：`scratch/goal021-ec03-probe-shape.py`、`scratch/goal021-ec03-probe-driver-shape.py`、
  `scratch/goal021-ec03-probe-concurrency-precondition.py`
- 相关：`MEM-20260926-141`（判据自身恒真 ⇒ 本条是它的一个**具体失效模式**）、
  `MEM-20260927-149`（枚举来自代码）、`MEM-20260927-150`（按出口判泄漏）