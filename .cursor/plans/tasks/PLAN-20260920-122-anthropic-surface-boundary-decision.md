---
id: PLAN-20260920-122
slug: anthropic-surface-boundary-decision
title: run 自身消费哪一面：给「run 走 main（OPENAI_COMPATIBLE）/ anthropic 面由 probe 段驱动」一个一等、可判的终态（EC-02，取 (b)），并给出改绑步骤、影响面与判据草案
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 2 = EC-02（run 自身消费 anthropic 面的口径，二选一终态）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（授权 live-gated 真实调用，**次数取最小必要**）与第 (3) 条（默认 runtime 保持 Fake、默认 CI 离线；live 分支必须显式 `RESEARCHOS_AGENT_RUNTIME=openhands` 才开门）。EC-02 明文允许 (a) 改绑 / (b) 把边界写成一等（读面/文档同源）并给出改绑步骤、影响面与判据草案——**二选一，不得留模糊状态**。本 PLAN 遵守：不新增依赖、不改 pin、不改 Policy/eligibility、不把真实 runtime 设为默认、不把凭据写进 CI；**本 PLAN 不修改任何门禁或断言强度**；**不发起真实调用**（取 (b)，判据全部离线可判）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-122-anthropic-surface-boundary-decision.md
memory_entries:
  - .cursor/memory/entries/MEM-20260920-096-local-gate-reads-worktree-ci-reads-commit.md
---

# PLAN-20260920-122 — anthropic 面口径（GOAL-009 cycle 2 = EC-02）

## 目标

给「**一次 run 自身消费哪一面**」一个**一等、可判的终态**，并让这个终态**经得起改绑**：

1. **决策有据**：(a) 改绑 / (b) 写成一等边界，**二选一**，理由用**实测证据**支撑（不是偏好）；
2. **边界可判**：把「run 走 `main`（`OPENAI_COMPATIBLE`）；`agnes-anthropic`（`ANTHROPIC`）
   由 live 判据的 **probe 段**驱动」做成**同源判据**——一改绑就红，逼着决策被重新审视，
   而不是靠注释或口头约定；
3. **改绑有路径**：给出**步骤 + 影响面 + 判据草案**，且影响面写的是**实测到的**耦合点
   （哪个测试断言了绑定、哪个 mock 只讲 OpenAI、前端哪一列会变），不是泛泛而谈；
4. **读面同源**：读面**已经**暴露 `model.endpoint_id` 与 `endpoint.protocol` ⇒ 边界**本来就可读**，
   本 PLAN 只是把它**钉住**并写清楚。

## 先探明再动手（cycle 1 与本次只读勘察已确认的事实）

1. **run 实际消费的模型不是 `agnes_flash`**（cycle 1 的 F-10）：协议两个 phase 要
   `domain_researcher` / `scientific_reviewer` ⇒ `domain_a → research_alpha`、
   `reviewer_a → reviewer_gamma`（`examples/config/agents.yaml`）；`agnes_flash` **只**被
   EC-04 判据的 **probe 段**用到 ⇒ **(a) 的改绑靶子是 `research_alpha` / `reviewer_gamma`**。
2. **读面已暴露协议**：`LlmEndpointReadDto.protocol`（`services/api/dto/endpoints.py`）与
   `ModelReadDto.endpoint_id`（`services/api/dto/models.py`）⇒「哪个模型走哪一面」**现在就能读**。
3. **耦合点 A（测试断言绑定）**：`tests/loaders/test_contract_loaders.py` 的
   `test_load_models_from_fixture` 断言 `models["research_alpha"].endpoint_id == "main"`。
4. **耦合点 B（离线 mock 只讲 OpenAI）**：`tests/e2e/test_ec03_real_runtime_offline_chain.py`
   的 `_MockRelayHandler` 自称「最小 **OpenAI-compatible** 端点」（`GET /models` +
   `POST /v1/chat/completions`）；而 `tests/e2e/live_run_support.py` 的 `point_catalog_at`
   **只换 `base_url`、保留 `protocol`** ⇒ 把 run 的模型改绑到 `ANTHROPIC` 会让这条既有门禁
   把 **Messages 形态**请求打到 OpenAI 形态的 mock 上。
5. **耦合点 C（前端列）**：`ModelCatalogTable` / `ModelDetails` / `ModelInspector` 都渲染
   `endpoint_id` ⇒ 改绑会改**读面文案**，可能牵动设计基线。
6. **风险 D（该路径从未真跑）**：`ANTHROPIC` 的**执行**路径（`llm_factory` 加 `anthropic/`
   前缀 → OpenHands → litellm）在 live 上**从未被 run 消费过**——cycle 1 里被 live 消费的是
   `OpenAIChatGateway` 的 probe 段，不是 run 的 LLM 路径。

## 决策（先写死，实施时不再漂移）

**取 (b)**：维持现有绑定，把边界写成一等且**可判**；**同时**把 (a) 的步骤/影响面/判据草案
写成可直接执行的文档。

**为什么不是 (a)**（理由全部是上面实测到的耦合，不是偏好）：

- (a) 会让**耦合点 A**（既有断言）与**耦合点 B**（既有门禁的 mock 协议）同时失效；
  修 B 需要让 mock 学会 Messages 形态或给该用例显式指定端点——那是**改测试与门禁的射程**，
  而本 GOAL 的 fix_policy **明文禁止**「修改门禁/测试断言使其通过」，两者的边界在**时间压力下
  极易混淆**；本 PLAN **主动避开**这个风险面。
- (a) 的收益（run 走 ANTHROPIC）**无法在不发起真实调用的情况下**验证（**风险 D**），
  而「次数取最小必要」是授权口径；先把它写成**可判的草案**，需要时按授权开一次即可。
- (b) **不是**「什么都不做」：它要求边界**可判**（改绑即红）、改绑**有路径**、
  影响面**有实测依据**——这三条都是真交付，(a) 反而**没有**解决「边界是否被写下来」的问题。

**留痕**：(a) 的判据草案写进文档后，将来任何人改绑都会先撞上**同源判据的红**，
从而被迫读那段影响面——这正是「不得留模糊状态」要的效果。

## 验收条件

- **AC-1 同源判据存在且可判**：新增判据（拟
  `tests/architecture/python/test_anthropic_surface_boundary.py`）断言：
  (i) 协议两个 phase 的 `required_roles` 解析到的 agent → 模型，其 `endpoint_id` 指向的端点
  **协议为 `OPENAI_COMPATIBLE`**（即 run 腿走 OpenAI 面）；
  (ii) 登记的 `agnes-anthropic` 端点 `protocol == "ANTHROPIC"` 且 `enabled`；
  (iii) EC-04 live 判据的 probe 段引用的端点常量**恰是** `agnes-anthropic`；
  (iv) 文档含改绑小节，且其引用的仓库路径/符号**可解析**。
- **AC-2 反证**：把 `models.yaml` 里 `research_alpha.endpoint` 临时改成 `agnes-anthropic`
  ⇒ **AC-1 的 (i) 必须红**；复原后复绿。
- **AC-3 改绑路径完整**：文档给出**可执行**的改绑步骤、**实测**影响面（耦合点 A/B/C/D）、
  以及**判据草案**（改绑后如何验收：(A|B) 二选一都写清楚）。
- **AC-4 读面同源**：文档声明「读面已暴露 `model.endpoint_id` 与 `endpoint.protocol`」，
  并在判据里核对这两个字段确实存在（防止读面回退）。
- **AC-5 本地门禁绿**：受影响定向套件 + `make validate-all`（m0 23 项，按 cycle 1 已确立的
  CI 同形配置）+ 治理 `validate.py` / `validate_bundle` / DOCS-CHECK。

## 实施清单

- [x] WP1 读面核对：确认 `LlmEndpointReadDto.protocol` / `ModelReadDto.endpoint_id` 在 API 上
      真的可达（跑既有 endpoints/models 套件即可，不必新起服务）。
- [x] WP2 写同源判据 `tests/architecture/python/test_anthropic_surface_boundary.py`（AC-1）。
- [x] WP3 反证 AC-2（先红后复原），把两次输出留证。
- [x] WP4 文档：在 `docs/integration/LLM_ENDPOINTS.md` 写「run 腿 / probe 腿」边界小节 +
      改绑步骤 + 实测影响面 + 判据草案（AC-3）；必要时在 runbook 交叉引用。
- [x] WP5 本地验证（AC-5）→ 写 RECHECK → 置 DONE → 投影 ALL_PLAN → 回写 GOAL-009
      （EC-02 状态 / 迭代日志 / 状态历史）→ commit（显式路径）→ push → CI 到终态。

## 证据

（执行时逐条填入。）

### WP1 读面核对

`LlmEndpointReadDto.protocol`（`services/api/dto/endpoints.py`）与 `ModelReadDto.endpoint_id`
（`services/api/dto/models.py`）**均已存在**；判据里各有一条断言防止它们被改掉
（`TestTheBoundaryIsReadableAtTheReadFace` 两条 **PASS**）。⇒ 边界**本来就可读**，
本 PLAN 只是把它钉住，**未新增任何读面字段**。

### WP2 判据

`tests/architecture/python/test_anthropic_surface_boundary.py` ⇒ **10 passed**。
其中 `test_protocol_roles_resolve_to_at_least_one_model` 是**判据自身的前提**：
解析链必须真的解析出模型（否则后续断言是空集合上的 vacuously true）。

### WP3 反证（**先红后绿**）

| 步 | 动作 | 观察 |
| --- | --- | --- |
| 1 | `examples/config/models.yaml` 的 `research_alpha.endpoint` 改成 `agnes-anthropic` | **RED**：`assert not {'research_alpha': 'ANTHROPIC'}`；**只有** run 腿那条红（其余 9 条绿）⇒ 定位精确 |
| 2 | 复原为 `main` | **GREEN**：`10 passed` |
| 3 | `git diff examples/config/models.yaml` | **空** ⇒ 复原干净 |

### WP4 文档

`docs/integration/LLM_ENDPOINTS.md` 新增 **§12**（`## 12. run 腿与 probe 腿：现在走哪一面`
+ `### 12.1 现在走哪一面` / `### 12.2 改绑步骤` / `### 12.3 影响面（实测）` /
`### 12.4 改绑后的判据草案`），并把 §11 末尾那句「尚未做」改成指向 §12。
判据逐条核对：四个小节标题在场、反引号里的仓库路径**真的存在**、§12.3 **点名**三个实测耦合点。

### WP5 本地验证

- 定向：`tests/architecture tests/loaders tests/e2e/test_ec04_live_first_run.py
  tests/e2e/test_ec04_live_gate_offline.py` ⇒ **145 passed / 1 skipped**；
  判据 + loaders ⇒ **33 passed**。
- `ruff check` / `ruff format --check` / `mypy` ⇒ 绿（修了 1 处行宽 + 2 处 `str | None` 收窄）。
- **m0 首次针对本轮的红是 stale**：该轮在我修完行宽/类型**之前**启动，读到的是旧文件
  ⇒ `python/product-lint` + `python/typecheck` 红，**两条都指向我已修好的行**。
  如实记录，并按干净树重跑（结果见 GOAL-009 迭代日志）。
- 治理 `validate.py` 绿。

### WP6 收口（本 PLAN 自己产出的教训）

**CI 抓到一条我漏掉的东西**：cycle 1 的推送 `e16e458` 让 `framework/validate` 红——
`MEM-20260920-094` 缺章节。**CI 是对的**：我在本地把该条目改好了，但**改写没进暂存区**，
提交进去的仍是旧形态，本地门绿是因为它读了**未提交**的工作树。
处置：独立 fix 提交 `86e77d8`（**修记录**，不是放宽 validator）。
沉淀为 `MEM-20260920-096`（本地门读工作树 / CI 读提交）。

## 状态历史

- 2026-09-20 收口：**DONE**。EC-02 取 **(b)** 并达到终态，独立复检
  `RECHECK-20260920-122` = **PASS_WITH_WARNINGS**（W-1…W-6）。判据 10 checks 绿且**被压过**
  （改绑 ⇒ 红、复原 ⇒ 绿、`git diff` 空）。**CI 反馈**：cycle 1 的 `e16e458` 触发
  **run 35517481162 = failure**（`framework/validate`，`MEM-20260920-094` 缺章节）——
  **CI 是对的**，根因是**改写未进暂存区**（本地门读工作树 ⇒ 本地绿而提交红），
  以 `86e77d8` **修记录**收口，沉淀 `MEM-20260920-096`。**未改任何门禁或断言强度。**

- 2026-09-20 建档：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 2（EC-02）。
  **决策已定：取 (b)**，理由基于 cycle 1 的 F-10 与本次只读勘察的四个实测耦合点
  （A 断言绑定 / B mock 只讲 OpenAI / C 前端列 / D 该路径从未真跑）。**本 PLAN 不发起真实调用**。

## 影响报告

**Domain / API / Schema**：**无变化**。本 PLAN 不新增/修改域实体、DTO、路由或迁移；
它新增一个**判据**与一段**文档**。读面字段（`protocol` / `endpoint_id`）**已存在**，只是被核对。

**安全 / 凭据**：**无新增信任面**，**不发起任何真实调用**，不涉及凭据值。
「run 腿 = OpenAI 面 / probe 腿 = ANTHROPIC 面」被写成**可判**事实后，
「哪一面真的被 run 消费」不再依赖口头约定——这类**可见性**本身就是 AGENTS §4 想要的方向。

**兼容性 / 迁移风险**：无迁移、无配置改动。**风险是判据本身可能过严**（例如把「run 腿必须
是 OpenAI 面」钉成硬约束，将来正当改绑会被它挡下）⇒ 处置是**判据红时给出指向文档改绑小节的
提示**，而不是让人绕开判据；文档里同时写明改绑后应如何**同步更新判据**（这是有意的：改绑是
架构决策，应该撞门）。

**上游版本影响**：无。**不新增依赖、不改任何 pin**。

**下一项任务**：WP1 读面核对 → WP2 判据 → WP3 反证 → WP4 文档 → WP5 收口并回写 GOAL-009 的 EC-02。
