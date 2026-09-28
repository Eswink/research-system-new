---
id: RECHECK-20260928-230
slug: goal-024-ec02-content-canary-end-to-end
title: GOAL-024 EC-02 复检（部分）：默认离线链上的内容金丝雀 —— 绝对面零命中 + 载体白名单 + 每条通道可见性正控制 + 两向反证；读面未观测（EC-02 仍未达成）
plan_id: PLAN-20260928-229
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-28
completed_at: 2026-09-28
owners:
  - root-agent
---

# RECHECK-20260928-230 — GOAL-024 EC-02 复检（部分交付）

**复检口径**：不复用 PLAN 叙述；每项给出可复核观察面；**未实跑的不记通过**。
**结论只说交付了什么**：EC-02 的**读面**部分**没有观测**（`NOT_YET_OBSERVED` 已写在判据源码里）
⇒ **EC-02 仍未达成、不得记 PASS**；本文件只复核已交付的那一半。

## 检查结果

### 一、交付面

| 交付物 | 观察面 | 结论 |
| --- | --- | --- |
| `tests/observability/content_canary_support.py`（**212 行**，函数均 ≤ 50 行） | 7 条合成金丝雀（per-import 随机）+ 默认离线 harness（Fake runtime + SQLite 域存储 + 真实 OTLP sink 只发 loopback + 制品根指向临时目录）+ 纯函数扫描器 | 成立 |
| `tests/observability/test_privacy_content_canary_end_to_end.py`（**246 行** / **10 例**） | 绝对面零命中 / 载体白名单 / 每条通道可见性正控制 / 允许键反证 / 日志行反证 / canonical 不判红 / 措辞无关 / 出口分区完整 / 终态如实登记 | 成立 |
| 观测面实跑 | 运行真的产生了 OTLP wire（`research_os.` 前缀可见）+ 制品 blob 命中 `artifactbody`；本次运行**应用日志 4 条**（日志面零命中**非空真**） | 成立 |
| 出网纪律 | `tests/egress_guard.py`：`judged 168 connection attempt(s); blocked 0`（全为 loopback 测试接收器） | 成立 |

### 二、反证两向（承 MEM-159）与按压复原（承 MEM-152）

| 反证 | 观察到的红 | 复原 |
| --- | --- | --- |
| 内容塞进**允许键** `endpoint_id`（经 `sanitize_attributes` 保留） | `hits(...) == ['artifactbody']` 且失败消息含键名 `endpoint_id` | 纯函数断言，无树内改动，无需复原 |
| 内容写进**日志行** | `hits(...) == ['toolarg']` 且点名出口 `application-log` | 同上 |
| 内容进 **canonical** / 声明过的载体 | **不判红**（制品正文在 blob 上、遥测与日志零命中） | — |

**四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；
规模 212 / 246 行、超 50 行函数 **0**；`mypy` = `Success: no issues found in 2 source files`。
**既有隐私判据逐字节未改**；`tests/observability/` 全目录 **81 passed, 1 skipped**。

## 结论

**部分交付，EC-02 仍未达成**：绝对面（遥测 traces/metrics wire、应用日志、失败载荷）**零命中**且有
**每条通道的可见性正控制**；载体白名单（制品 blob 只承载制品正文）成立；两向反证成立。
**未交付**：读面 HTTP（`read-face-http`）的扫描 —— 需要应用级装配（`TestClient` + 路由表），
已在判据源码里登记 `NOT_YET_OBSERVED`，下一 cycle 补齐；**补齐前 EC-02 不得记 PASS**。

## 如实登记的警告

- **`W-1`（最要紧）读面未观测**：6 条受判出口里 `read-face-http` **没有**被本 cycle 扫描
  （登记理由在判据源码里）；「全部受判出口零命中」**尚不成立**。
- **`W-2`｜两个分支都收敛到 `FAILED`**：默认 Fake runtime 的交付物声明与合约不合 ⇒ 验收门判拒
  （门**没有**被放宽）。零命中命题因此覆盖的是**判拒路径**；`SUCCEEDED` 路径未验。
- **`W-3`｜金丝雀注入面窄**：本轮真正沿默认链注入的是**制品正文**；任务输入 / prompt /
  工具参数 / 工具输出 / 证据正文 / 失败消息六条金丝雀**已构造但未被注入到运行**（只在正控制与
  反证里使用）⇒ 「六源全部注入」未达成。
- **`W-4`｜OTLP 原始字节不区分信号**：测试接收器不按信号分桶保存原始 payload ⇒ 两个 wire 出口
  扫的是**同一份合并字节**（保守、更严，但两条出口不是独立样本）。
- **`W-5`｜`shutdown can only be called once`**：全目录跑时该 warning 出现（SDK 生命周期提示，
  非失败）；未追因。
- **`W-6`｜`stdout-stderr` 仍是 EC-01 的豁免出口**：本轮额外扫了它，但它不在受判集合内。
