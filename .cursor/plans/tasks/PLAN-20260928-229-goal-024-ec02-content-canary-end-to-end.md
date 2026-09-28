---
id: PLAN-20260928-229
slug: goal-024-ec02-content-canary-end-to-end
title: GOAL-024 cycle 2（EC-02）：端到端内容金丝雀 —— 默认离线 Fake 链注入 + 受判出口逐面扫描 + 可见性正控制 + 反证红与逐字节复原
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-024
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-024 的 **EC-02**（端到端取证 + 反证 + 按压；本轮主干）。
    授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为「**新增金丝雀判据与夹具**（一律落
    `tests/**`）+ **修被新判据证明为真缺陷**（只允许收紧记录面）+ **文档同源更新**」；
    **不加新能力、不放宽任何判据、不改安全策略、不修改任何既有判据**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**、默认门**一律离线**。
    **本 PLAN 专属边界**：**不得**修改 `test_privacy_canary.py` / `canary_support.py` /
    `otlp_receiver.py`（**只读**，可 import）；**不得**改 `PRODUCT_ROOTS` / m0 条数（仍 `23`）；
    **不得**新增依赖；**不得**真实出网（跑链路全在本机进程内，OTLP 只发到 loopback 测试接收器）；
    金丝雀一律**测试内构造的合成串**；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **零命中（绝对面）**：沿默认离线 Fake 链跑一次真运行，对**无合法载体**的出口
      （OTLP traces wire / OTLP metrics wire / 应用日志 / stdout+stderr / 失败载荷中
      **非**该金丝雀的字段）扫描 ⇒ 内容金丝雀**零命中**。
    status: PASS
  - id: AC-2
    criterion: >-
      **白名单（有合法载体）**：制品正文与失败消息各自**只在契约声明要返回它的载体**上出现
      （制品 blob / `GET /artifacts/{id}/content` 路线 / run 事件里的失败消息），
      **其余路线一律零命中**；白名单**写在判据源码里**（承 MEM-158）。
    status: PASS
  - id: AC-3
    criterion: >-
      **可见性正控制（承 MEM-156）**：受判出口数 ≥ 1，且**每个**受判出口各有一条正控制
      （把金丝雀经该通道发送 ⇒ 扫描器**必须报出该出口**），否则判红；无生产点的出口
      （`stdout-stderr`）以通道级正控制证明可见。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证两向 + 按压复原（承 MEM-159 / MEM-152）**：①内容进**允许键**（`endpoint_id`）
      ⇒ 判红并**点名出口与键名**；②内容进**日志行** ⇒ 判红并点名出口；③内容进 **canonical**
      （SQLite 域表）⇒ **不**判红；每次按压 raw `sha256` + 二进制读写**逐字节复原**。
    status: PASS
  - id: AC-5
    criterion: >-
      **措辞无关（承 MEM-141）**：把金丝雀的措辞整体替换（同一 token、不同前后缀）⇒
      判据结论**不变**（以实测留档），证明扫描面不是靠话题词喂饱。
    status: PASS
  - id: AC-6
    criterion: >-
      新判据与新夹具自洽过门（`ruff` / `format` / 规模 450-50 / `mypy`）；既有隐私判据
      **逐字节未改**且仍全绿；as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`
      （**记录写入之后**）；治理 `validate.py` 绿；CI 台账到终态。
    status: DEFERRED
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-230-goal-024-ec02-content-canary-end-to-end.md
memory_entries: []
---

# PLAN-20260928-229 — GOAL-024 cycle 2（EC-02）：端到端内容金丝雀

**动因**：EC-01 只交付了**扫描面**（清单 + 分区 + 未分类判红），**没有**跑过一次真运行、
**没有**证明零命中。EC-02 是本 GOAL 的**主干**：沿默认（离线 Fake）运行路径把**用户内容**
打上唯一合成金丝雀，跑一次真运行，然后对**全部受判出口**逐面扫描。

**读面口径（cycle 1 台账已登记的修正，必须照此实现）**：不能写成「读面不得含内容」——
`GET /artifacts/{id}/content`、制品 blob、`GET /runs/{id}/events` 里的失败消息**契约本来
就是**返回/保存用户内容（**canonical 业务真相**）。受判命题因此是：

```text
内容只出现在「契约声明要返回/保存它」的那条载体上；其余出口（遥测 wire、应用日志、
stdout/stderr、失败载荷的其他字段、其他路由）一律零命中。
```

**白名单 = 判据源码里的显式声明**（承 MEM-158），**绝对面 = 没有合法载体的出口**。

## 验收条件

见 frontmatter `AC-1`…`AC-6`：绝对面零命中 / 白名单载体 / 每出口可见性正控制 /
反证两向与逐字节复原 / 措辞无关 / 门与记录。

## 实施清单

- [x] WP1：`tests/observability/content_canary_support.py` —— 合成金丝雀（per-import 随机）、
      默认离线 harness（真实 OTLP sink + SQLite 域存储 + tmp 制品根）、逐出口扫描器、白名单类型。
- [x] WP2：`tests/observability/test_privacy_content_canary_end_to_end.py` —— 零命中 / 白名单 /
      正控制 / 反证两向 / 措辞无关 / 非空转六组断言。
- [x] WP3：按压与反证记录（raw `sha256` + 二进制读写复原）+ 措辞替换对照留档。
- [x] WP4：记录（本 PLAN / RECHECK / MEM / GOAL 回写）+ 记录面判据 + as-is m0 + push + CI 台账。

## 证据

**无可复用事实**（本 PLAN 不沉淀工程记忆：读面口径已写入 GOAL 台账，复用性留待 EC-02 补齐后评估）；原始记录：运行时观测计数、逐出口命中数、反证失败消息、raw `sha256`、四道门、m0 终态行、CI run。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 2，EC-02）；读面按白名单口径。 |
| 2026-09-28 | DONE（部分） | 交付 `content_canary_support.py`（212 行）+ 判据（246 行 / 10 例）：绝对面零命中、载体白名单、每通道可见性正控制、两向反证、措辞无关。**读面（`read-face-http`）未观测**（判据源码里登记 `NOT_YET_OBSERVED`）⇒ **EC-02 仍未达成**；AC-6 的 m0 / CI 见 GOAL 迭代日志。 |

## 影响报告

- **Domain/API/schema**：无（只新增 `tests/**`）。
- **安全/凭据**：无新增凭据面；金丝雀为测试内构造的合成串；OTLP 只发到 loopback 测试接收器。
- **兼容性/迁移**：无。
- **上游版本影响**：无（零依赖改动）。
