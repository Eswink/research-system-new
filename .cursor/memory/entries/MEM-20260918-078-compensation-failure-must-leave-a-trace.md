---
id: MEM-20260918-078
title: "补偿失败不能只留在遥测：静默降级要落一条 canonical 痕迹，且要如实回答'当时 canonical 停在哪'"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-105-resume-compensation-failure-visibility.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-105-resume-compensation-failure-visibility.md
supersedes: []
tags:
  - reliability
  - observability
  - run-lifecycle
  - honesty-boundaries
  - governance
---

# 补偿失败要留痕：`except: pass` 是"事实只存在于日志里"

## 做了什么

GOAL-006 cycle 6（EC-06 选 (b)）把守护线程的补偿失败从静默降级变成**读面可判的 canonical 事实**：

- 新事件 `run.resume_compensation_failed`（`EventType` 追加成员），由
  `run_terminals.publish_compensation_failure(publish, run_id, failure, canonical_state)` 构造，
  payload 四键：`run_id` / `failure_type` / `message` / `canonical_state`；
- `services/api/scheduler.py::_compensate_failed_resume` 的失败路径**先发事件再吸收异常**
  （"单 run 失败不拖垮整轮"的既有语义不变）；连事件都发不出去时只剩遥测（地板，显式登记）；
- 读面判定沿用 `GET /runs/{id}/events` ⇒ 不动 DTO / OpenAPI / 路由。

## 为什么这样做

- **`except: pass` 会让"补偿没做成"只存在于遥测/log**：运营读事件链时看到的是"这条 run 卡在
  `RUNNING`"，没有任何一条 canonical 事实解释为什么。EC-06 的判据就是"读面能判"，不是"日志里有"。
- **`canonical_state` 必须如实**：补偿失败时的诱惑是写 `compensated_to: PAUSED`（和里面那条
  成功事件同形），但那一刻 run **没有**回到停车——`PAUSED` 是伪造。发的是"补偿失败时仍停在哪"。
- **地板也要写**：事件走的是同一条发布面，发布面挂了就什么都不剩。把地板写成显式边界，
  好过在文档里暗示"必然留痕"。
- **可见 ≠ 自动恢复**（本轮实测得到的边界）：补偿失败若发生在**落库**这一步，canonical 行已停
  在前一步写的 `RUNNING`，而 `_dispatch_due` 只扫 `PAUSED` ⇒ 下一轮不会自动捞回来。事件是痕迹，
  不是修复；自动修复属新机制与产品决策。

## 怎么做与复现

```bash
# 形状 + 文档同源（payload 键集合与契约文本声明行互钉）
uv run --frozen --no-sync python -B -m pytest \
  tests/application/run_orchestration/test_resume_compensation_failure_event.py -q
# 读面：真跑一轮调度，只打坏"补偿的落库"
uv run --frozen --no-sync python -B -m pytest \
  tests/api/test_compensation_failure_visibility_api.py -q
# 接线 + 地板（整轮不中断）
uv run --frozen --no-sync python -B -m pytest \
  tests/application/ops/test_retry_dispatch_scheduler.py -q
```

反证（五条，先红后复原）：把失败路径改回 `except: pass`；从 payload 删 `canonical_state`；
从契约文本的声明行删一个键；从 `EVENT_MODEL.md` 删「不含任务级归因」；去掉留痕外层 try/except。

## 适用边界（踩过的坑）

- **声明行要是"一行"**：payload 键集合写成契约文本里的一条标记行（`payload 键（判据按这一行核对）：`），
  判据按这一行解析并与**实际发出的键**对照——多写少写都红。散在段落的词不算声明。
- **同一族事件的字段不要"后来居上"**：新事件的 `failure_type` / `message` 描述的是**补偿**这次的
  失败，与被补偿的那次失败不是一件事；两个事件都留着，读的时候别混。
- **改 `service.py` 前先看行数**：它贴着 450 行硬上限，本轮按"随改动搬代码"纪律收紧了三处 docstring
  才放得下新方法（无行为改动）。
- **`EventType` 追加成员会被域门禁数到**：`tests/domain/test_m5_domain_increments.py` 的
  `DOCUMENTED_EVENT_TYPES` 与计数（37 → 38）要同步，且词表 `EVENT_MODEL.md` 必须一起加。
- 相关：[[MEM-20260918-073]]（一次读 = 一条语句 = 一个快照）、[[MEM-20260918-077]]（点名要可机器校验）、
  [[MEM-20260918-075]]（页面消费读面的两渠道判据）。

## 来源

- PLAN-20260918-105 / RECHECK-20260918-105（GOAL-20260918-006 cycle 6 = EC-06）。
- 上游：RECHECK-20260917-090 W-3（无任务级归因）/ W-4（守护线程补偿失败静默降级）/ W-5（响应仍 200）。
