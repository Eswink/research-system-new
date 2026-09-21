---
id: PLAN-20260922-131
slug: offline-gate-structural-judge
title: 把「默认门离线」做成整轮结构判据：公网出站发生即红（GOAL-010 EC-05）
status: IN_PROGRESS
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260921-010
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260921-010 cycle 5 = EC-05（出站结构判据，承 `RECHECK-121` W-7）。授权来源：2026-09-21
    用户 goal 模式指令 frontmatter `authorization.ref`——(2) **默认姿态不变**（默认 runtime 保持 Fake、
    默认 CI 离线，AGENTS.md §11）；(5) push-to-main-for-CI（只推 main、不 force、不重写历史）。
    安全口径照抄 GOAL：服务端 URL 仅 http/https，发请求前校验 host 并拒绝 localhost/环回/私有/保留
    （**复用既有 `endpoint_policy`，不新造判据**）；凭据只从环境变量读取；观测隐私不记录完整 Prompt。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    新增依赖、改上游 pin；把真实 runtime 设为默认；把凭据写进 CI；用「本次没观测到出站」充当判据。
    **触到 Domain / Canonical State 边界即 BLOCKED**，留人工拍板。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-131 — 默认门离线的整轮结构判据（GOAL-010 EC-05）

## 目标

把「**默认门离线**」从**约定**变成**结构判据**：在不显式开门（不声明 live 开关）的默认测试运行里，
**任何一次通向公网目的地的出站尝试都会让发起它的用例判红**——判据**不依赖人工观察**，
也**不依赖凭据是否可解析**（这正是 `RECHECK-121` W-7 暴露的缺口）。

反证必须成立：**关掉守卫** ⇒ 常驻证物 RED；复原 ⇒ GREEN。**不得**用「这一轮没看到出站」充当判据。

## 验收条件

- **AC-1 整轮覆盖**：判据的作用域是**一轮默认测试运行**（不是某条用例、某条代码路径）：
  任何用例里发生的公网出站尝试都被判红，且**点名**发起者（nodeid）与目的地。
- **AC-2 不依赖环境**：同一套件在「凭据**可**解析」（`.env` 已进进程）与「凭据**不可**解析」
  两种状态下**同结论**——W-7 的红正是「凭据可得性驱动的环境签名」，这一条必须被封住。
- **AC-3 反证成对且**被压过：**常驻证物**（对**不可路由**的保留地址发起的真实连接尝试**被拦下**）
  + **非空转正对照**（对环回/私网目的地的连接尝试**不被**拦）。按压（关掉守卫）⇒ 证物 RED；
  复原 ⇒ GREEN。两向都留证据。
- **AC-4 不误伤既有套件**：判据开启后默认全量测试**全绿**（docker / postgres / observability /
  distributed 等既有依赖环回或私网目的地的套件不受影响）；若真有合法公网出站，**先如实登记**
  再决定（不得默默放行）。
- **AC-5 口径单一来源**：目的地分类**复用** `packages/application/model_relay/endpoint_policy.py`
  的既有 host 判据（不新造第二套分类、不改它的判定语义）；**Domain 一字不动**。
- **AC-6 门禁与记录**：规模门禁自查（50 行函数 / 450 行文件）→ 定向套件 → m0 全量 23/23 →
  治理 `validate.py` 绿 → 独立 RECHECK（含 W 列表）→ GOAL 回写（EC-05 状态 / 迭代日志 /
  `child_plans` / `latest_recheck` / `memory_entries`）。

## 证据（derive 阶段实测；**只读代码/配置/日志，未发起任何真实调用**）

| # | 事实 | 核对方式 | 对 EC-05 的含义 |
| --- | --- | --- | --- |
| E-1 | 被捕获的那次真实出站是 `GET https://apihub.agnes-ai.com/v1/models` ⇒ `200 OK`，发生在**全量 m0 期间**；触发条件是「前序 import 过 openhands-sdk ⇒ litellm `load_dotenv()` ⇒ `.env` 凭据进进程」 | `RECHECK-121` W-7（三轮表 + 失败用例名） | 缺口不是「某条路径忘了关门」，而是**整轮没有宪法**：出网由一个**谁也没 mock** 的路径发起 |
| E-2 | 既有的「零出站」判据是**逐用例 mock `socket.socket`**：`mock.patch.object(socket, "socket", _no_network)`，且断言的是**该用例关心的那条路径** | `tests/e2e/test_ec04_live_gate_offline.py::TestZeroOutboundWhileClosed` 等 | 判的是**路径**不是**运行**：没人想到的路径**天然逃逸**——W-7 就是这么漏的 |
| E-3 | host 分类**只有一份**判据：`endpoint_policy._host_kind` / `_is_reserved`（localhost / link_local / private / reserved / public / domain）；公开面是 `validate_endpoint_url` / `endpoint_url_refusal`，**入参是 URL**，没有「按 IP 判类」的公开助手 | `packages/application/model_relay/endpoint_policy.py`（全文） | 守卫要在 socket 层判**目的地 IP** ⇒ 需要把既有判据**暴露**（不是新写一套分类） |
| E-4 | pytest 配置：`testpaths = ["tests"]`，`pythonpath = ["."]`，**仓库根没有 conftest**；`tests/conftest.py` 是测试树的根配置（docker/gpu 的环境探测式 skip 就在那里） | `pyproject.toml:101-117`、`tests/conftest.py` | 守卫放 `tests/conftest.py`（或其引用的新模块）即**覆盖默认门收集到的全部用例**，且不需要新增根 conftest |
| E-5 | m0 的 `python/tests` = `python -m pytest --ignore=<boundary_test>`，**不给路径** ⇒ 走 `testpaths` | `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py:123-126` | 「默认门」的 python 面 = `tests/`；其它作业（`collector-quality` / `container-quality` / TS 四作业）各自是独立进程与独立根，**不在本判据射程内**（如实登记为边界） |
| E-6 | `.env.example` 里有 `ALLOW_PUBLIC_NETWORK=false`，但**全仓零消费者**（`rg` 只命中该文件） | `rg -n ALLOW_PUBLIC_NETWORK` | 它是**已声明未接线**的产品侧安全旋钮；把守卫的放行面挂在它上面会**改变它的语义**（产品策略 ≠ 测试门），**不采用**，如实登记 |
| E-7 | `.env`（gitignored）持凭据；操作者配方是 `set -a; . ./.env; set +a`；openhands-sdk 的 litellm 会**自行**把 `.env` 读进**任何 import 过它的进程** | `docs/integration/LIVE_MODEL_RUNBOOK.md`、`RECHECK-121` W-7 | AC-2 的两种进程状态**都能构造**：带 `.env` / 不带 `.env` 各跑一次 |
| E-8 | live 门的既有语汇是**显式命名开关**（`RESEARCHOS_AGENT_RUNTIME=openhands` + 凭据可解析），live 用例的声明方式是 **pytest marker `requires_live_llm`** | `services/api/runtime_support.py`、`pyproject.toml` markers、各 live 套件 `pytestmark` | 放行面应当**同源**：按 **marker** 放行（不是按环境变量），与既有门语汇一致且**不依赖环境** |

## 已知的**不可回避**取舍（定案必须选一个并写明代价）

1. **判据住在哪一层**：进程级 socket 守卫（**能判「发生」**，代价是一个新的 conftest 组件 +
   必须证明它不误伤既有套件）vs. 扫描式 validator（便宜，但**判的是代码形态**，
   满足不了「出站发生 ⇒ 红」——W-7 那种「谁也没想到的路径」正好逃逸）。
2. **放行面**：按 marker 放行（同源、非环境依赖）vs. 按环境变量放行（便宜，但**环境一变口径就变**，
   正是 EC-05 明文要避免的形态）。
3. **拦截语义**：**拦下并抛错**（出站根本不会发生，符合「默认门离线」的字面承诺）vs. **放行但记账**
   （能观测真实行为，但「离线」就不再是结构事实）。EC-05 要求前者；后者只允许出现在**按压**里。
4. **目的地分类的射程**：socket 层看得见的是**已解析的 IP**；**DNS 查询本身不经 `socket.connect`**
   ⇒ 本判据**不覆盖 DNS**（如实写进边界，不假装覆盖）。

## 候选面（WP1 在此表上定案）

| 候选 | 形态 | 代价 | 已知风险 |
| --- | --- | --- | --- |
| (a) `tests/conftest.py` 里的**进程级 socket 守卫** | 包装 `socket.socket.connect` / `socket.create_connection`；目的地按既有 `endpoint_policy` 判类，**公网/保留 ⇒ 抛错并点名**；环回/私网/链路本地放行；当前用例带 `requires_live_llm` ⇒ 放行 | 一个新模块 + 必须实测「默认套件零公网出站」 | 误伤既有套件（docker/postgres/observability）；对 SSE/子进程内的出网不可见（子进程有独立解释器） |
| (b) 扫描式 validator（源码里出现未声明的出网调用点即红） | 静态规则，无运行成本 | 判**形态**不判**发生**；误报面大（网关、probe 本来就该出网） | **不满足** AC-1/AC-3，只能当补充 |
| (c) 继续扩既有 per-test mock | 每个新用例各自 mock | 零新架构 | **结构上无法**覆盖「没人想到的路径」——W-7 已证明 |

## 实施清单

- [ ] WP1 **定案（承重墙，先审后改）**：在候选面表上定案——判据形态、覆盖范围、分类来源（复用
      哪一处既有判据、是否需要把它暴露成公开助手）、放行面、拦截语义、**不做**边界（DNS / 子进程 /
      其它作业）。产出：定案 + 代价 + 回退路径。**先落记录再改代码**。
- [ ] WP2 **按定案落地**：守卫 + **常驻证物**（对不可路由保留地址的真实连接尝试被拦下）+
      **非空转正对照**（环回目的地不被拦）+ 文档同源（`docs/` 里「默认门离线」的表述指向该判据）。
- [ ] WP3 **测量（EC-05 的核心证据）**：在默认门（CI 同形配置）下跑全量，**如实记录公网出站尝试数**
      与发起者；再在**凭据已进进程**（`.env` 已载入）的同一套件上复跑，证明**结论不变**（AC-2）。
      任何非零出站**先如实登记**，不默默放行。
- [ ] WP4 **门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。

## 影响报告

- **产品面**：预计**零改动**。守卫住在测试树里；若 WP1 定案需要把既有 host 判据暴露成公开助手，
  那是 `endpoint_policy.py` 的**加性**改动（判定语义一字不改），并在 WP1 里写明理由与代价。
- **Domain / Canonical State**：不动。**OpenAPI / 快照 / 前端**：不动（无 DTO / 路由变化）。
- **CI**：默认 CI 仍离线；新增判据只在默认门里生效，live 用例按 marker 放行。
- **上游**：不新增依赖、不改 pin。
- **观测隐私**：守卫只记**目的地 IP/端口 + nodeid**，不记任何请求内容（AGENTS §10）。

## 不做（写死，防扩边）

- **不**改 `endpoint_policy` 的判定语义（只可能**暴露**，不重写）。
- **不**碰 `ALLOW_PUBLIC_NETWORK`（E-6：语义属于产品策略面）。
- **不**为了让守卫不误伤而放行私有网段以外的任何类别；任何放行都要**逐条写明理由**。
- **不**把守卫做成「本轮没观测到出站 ⇒ 绿」的形态（AC-1 明文禁止）。
- **不**在 CI 里注入凭据、不把 live 开关写进任何文件。

## 回退路径（写明）

纯测试面改动：回退 = 删掉守卫模块与 `tests/conftest.py` 的接线（+ 若做了暴露助手的加性改动则一并
撤销），**不涉及** Domain / Canonical State / 数据迁移 / 产品行为。回退后既有 per-test 判据
（E-2）**原样仍在**，即回退是「判据变弱」，不是「判据消失」——这一点必须在 RECHECK 里写明。

## 状态历史

- 2026-09-22 derive：由 GOAL-20260921-010 的 EC-05 派生（`parent_goal` 投影 ALL_PLAN）。
  **只读代码/配置/日志，未发起任何真实调用**，实测得 E-1…E-8 与候选面表。**承重墙定为 WP1**：
  核心问题是「**整轮**的零出站如何成为**结构**事实，而不是逐用例的路径断言」，以及
  「放行面怎么设计才**不依赖环境**」（EC-05 明文禁止把判据弱化成依赖环境的形态）。
