---
id: PLAN-20260920-119
slug: live-model-runbook
title: 真实端点 runbook 与「哪些面仍是 demo」清单：登记步骤、凭据注入与轮换、重启边界、Fake↔真实切换与回退（EC-06）
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 6 = EC-06（文档与 runbook）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (2)(3)(4) 条（声明参数如实记录 / 凭据只从环境变量或 Credential boundary 读取、不得写入仓库或记录、不得回显 / 默认 runtime 保持 Fake、真实 runtime 仅显式配置时启用）与 AGENTS.md §11（默认 CI 离线）与 §14（完成任务时的报告义务）。本 PLAN 遵守：不新增依赖、不改 pin、不改 Policy、不改默认 runtime；**文档里不出现任何凭据值、不写可用的凭据字面量**；无凭据时 live 相关步骤如实标注为「需操作者注入」。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-119-live-model-runbook.md
memory_entries:
  - .cursor/memory/entries/MEM-20260920-092-new-judges-must-be-pressed-by-falsification.md
---

# PLAN-20260920-119 — 真实端点 runbook（GOAL-008 cycle 6 = EC-06）

## 目标

把「怎么把真实端点接起来、怎么退回去、哪些面还是假的」写成**可判的文档**——
判据不判「文笔」，判「**同源**」：文档里出现的每个路径、变量名、命令，
都必须在代码里**真实存在**；漏掉四类内容中的任一类，判据红。

四类内容（EC-06 判定细则）：

1. **登记步骤**：**DB 路径**（配置面 SQLite 的哪张表、哪个文件）与 **YAML 路径**
   （`examples/config/*.yaml` 的哪几个文件、哪些键）；
2. **凭据注入与轮换**：只经环境变量或 Credential boundary；轮换 = 换环境变量 + 重新
   注入（**不落盘**）；
3. **重启后重输的边界**：进程内注册表随进程消失 ⇒ 重启后必须重新注入；
4. **Fake↔真实切换与回退**：怎么开（显式配置）、怎么退（去掉配置即回默认 Fake）；
5. **「哪些面仍是 demo」清单**：把仍是 Fake/demo 的面逐条列出来（清单本身可判：
   列出的符号必须在代码里存在）。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **配置面在 SQLite 的两张表**：`llm_endpoints(endpoint_id, endpoint_json, created_at)` 与
   `models(model_id, model_json, created_at)`（`adapters/sqlite/…`；默认 DB
   `data/research-os-control.db`，**gitignored**）⇒ 「DB 路径」必须写成「运行期生成、可能不存在」，
   否则判据会拿一个 clean checkout 里必然不存在的路径当「同源」。
2. **YAML 面在 `examples/config/`**：`llm_endpoints.yaml`（`main` / `agnes-anthropic`）、
   `models.yaml`（`agnes_flash` 声明 512000 / MAX）、`model_profiles.yaml` ⇒ 「YAML 路径」
   是这组文件里的具体键。
3. **凭据 ref 是目录里声明的**：端点 `credential_ref: LLM_MAIN_KEY`（`examples/config/llm_endpoints.yaml`），
   `EnvCredentialResolver` 按**变量名**解析；API 侧是进程内注册表
   （`RegistryCredentialResolver`，`credential_ref` = `endpoint:<id>`）⇒ 轮换与重启边界
   两套面都要写（环境变量面 / API 注册面）。
4. **runtime 切换开关已存在**：`RESEARCHOS_AGENT_RUNTIME`（`services/api/settings.py:144`，
   默认空串 = Fake）；非法取值装配期 fail-closed 点名（`tests/api/test_runtime_selection_surface.py`）。
5. **门与口径已存在**：`live_run_gate.py`（两条开门条件）、`live_run_record.py`
   （`NOT_VERIFIED` / `REPEATABLE_CONFIGURATION`）、`docs/integration/LLM_ENDPOINTS.md` §11
   ⇒ runbook 要与它们**同源**（引用同一批符号），不能另起一套说法。
6. **`docs/INDEX.md` 有集成文档清单**（第 124–130 行附近是 `integration/*.md` 的列表）⇒
   新文档要在那里登记一行。
7. **「仍是 demo」的面**：组合根仍注入 `FakeAgentRuntime`（默认）、`FakeBudgetLedger`、
   `FakeToolProvider`、`FakeWorkspaceBackend`、`FakeWorkflowEngine`、`FakeModelGateway`、
   `FakeMemoryStore` 等（AGENTS.md §11 的契约要求：Fake **不删**；方向是 runtime 可配置）⇒
   清单列这些**符号**，判据判它们存在。
8. **本机仍无凭据**（cycle 5 复核）：六项候选环境变量全 absent ⇒ 文档里的 live 步骤
   只能标注为「需操作者注入」，**不得**写成「已验证」。

## 口径（先写死，避免实施时漂移）

- **判据判同源，不判文笔**：四类内容各自要有**可判的存在性**（小节存在 + 其中的
  路径/变量/命令/符号在代码里找得到）。找不到 ⇒ 红；**不**允许把判据写成「文档里出现了某些词」。
- **运行期产物不是源码路径**：`data/research-os-control.db` 这类 gitignored 运行期文件
  必须在文档里**显式标注**为运行期生成，并进判据的白名单（**带理由**）；白名单是**逐条**的，
  不是通配。
- **凭据纪律**：文档只写**变量名**与**边界**，不写值、不写示例 key；判据里不出现任何凭据值形态。
- **默认仍是 Fake**：runbook 必须写明「不配置 = Fake」与回退步骤；把真实 runtime 设成默认
  是本 GOAL 的 forbidden 项，文档不得暗示默认已切换。
- **不做事**：不改配置面 schema、不加新端点/模型、不改门与口径代码（本轮只写文档 + 判据 +
  `docs/INDEX.md` 登记）。

## 验收条件

- **AC-01 文档存在且被索引**：`docs/integration/LIVE_MODEL_RUNBOOK.md` 存在；
  `docs/INDEX.md` 有对应行（判据按行读，不按「提及」）。
- **AC-02 五类内容逐项可判**：五个小节各自存在（缺任一 ⇒ 红），且每节至少有一条
  **同源事实**被判据核对。
- **AC-03 同源判据**：文档里出现的
  - 仓库路径（`packages/…`、`services/…`、`adapters/…`、`apps/…`、`examples/…`、`docs/…`、
    `tests/…`、`.cursor/…`）**必须存在**（运行期产物按逐条白名单豁免）；
  - 环境变量名（`RESEARCHOS_*` 与目录里声明的 `credential_ref`）**必须在代码里出现**；
  - pytest 目标路径**必须存在**；
  - 「仍是 demo」清单里的符号**必须在代码里存在**。
- **AC-04 反证**（先红后复原）：
  - F1：把文档里某个路径改成不存在的路径 ⇒ 同源判据红；
  - F2：把某个环境变量名改错一个字符 ⇒ 判据红；
  - F3：删掉「重启后重输的边界」小节 ⇒ 内容判据红；
  - F4：从 `docs/INDEX.md` 删掉登记行 ⇒ 索引判据红；
  - F5：把 demo 清单里的某个 Fake 换成不存在的符号 ⇒ 判据红。
- **AC-05 凭据纪律**：文档与判据里不出现任何凭据值形态（复用既有
  `tools/credential_audit.py` 的四面扫描口径，本轮至少覆盖「文档 + 判据」两处）。
- **AC-06 门禁**：定向套件 + **m0 全量 23 项** + 治理 `validate.py` / `validate_bundle` /
  `docs_consistency_check`。

## 实施清单

### WP-A — runbook 文档

- `docs/integration/LIVE_MODEL_RUNBOOK.md`：五节（登记 / 凭据注入与轮换 / 重启边界 /
  Fake↔真实切换与回退 / 仍是 demo 的面），全部引用真实符号与真实路径。
- `docs/INDEX.md`：登记该文档（集成文档清单 + 快速问答各一行）。
- 提交：`docs(integration): add the live-model runbook (registration, credentials, restart, switching, demo faces)`

### WP-B — 同源判据

- `tests/architecture/python/test_runbook_same_source.py`：AC-02/AC-03 的可判化 + 运行期产物白名单。
- 提交：`test(architecture): pin the runbook to the code (paths, env vars, commands, demo symbols)`

### WP-C — 反证、记录与收口

- F1–F5 先红后复原；RECHECK-119；子 PLAN 收口；GOAL 回写（EC-06）；
  收口后 GOAL 进入**终止判定**（EC-01…EC-06 全 PASS；live 分支的 skip 已在 EC-04/EC-05 登记）。
- 提交：`docs(goals): close GOAL-008 cycle 6 -- EC-06 ...`

## 证据

逐条 AC 与 F1–F5 的注入/观察/复原对照、以及反证抓出的两个**判据缺陷**见
`.cursor/plans/rechecks/RECHECK-20260920-119-live-model-runbook.md`。摘要：

- **AC-01**：`docs/integration/LIVE_MODEL_RUNBOOK.md` 存在；`docs/INDEX.md` 的 Integrations
  清单有**条目行**（不是「某处提过」）。
- **AC-02**：五个小节逐条存在；「重启边界」点名 `RegistryCredentialResolver` 与 `_registry`
  （落到机制而不是口号）；切换小节点名 `RESEARCHOS_AGENT_RUNTIME` / `openhands`。
- **AC-03**：`tests/architecture/python/test_runbook_same_source.py` **10 passed**
  ——引用的仓库路径全部存在（含 13 个 `adapters/fakes/*.py`）、大写变量名全部在代码里出现、
  pytest 目标存在、demo 符号存在。
- **AC-04**：F1–F5 **先红后复原**（每步 `git diff --quiet` 复核）。**其中 F2/F4 第一次没红**，
  因为判据自己有洞（跨行反引号配对吞 token；索引判据只判「全文出现过」）——按缺陷修判据
  （`affc063`），修完立刻红。这条经过写进了 **MEM-092**。
- **AC-05**：文档只写变量名与边界，不写值、不写示例 key。
- **AC-06**：定向 `10 passed`；DOCS-CHECK PASS（6 checks）；治理两件绿；
  **m0 全量 23 项 4201 passed / 12 skipped（489.62s，代码树 `affc063`）**。
  其后仅 `.cursor/**` 记录改动，`validate.py` / `validate_bundle` / `docs_consistency_check`
  单独复跑绿（**未**重跑全量 m0，如实登记）。

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 6 = EC-06）：`status: IN_PROGRESS`。
  只读勘察确认 8 条事实（配置面两张表 + 默认 DB 是运行期产物 → YAML 面在 examples/config →
  两套凭据面（环境变量 / 进程内注册表）→ runtime 开关已存在 → 门与口径已存在（文档须同源）→
  `docs/INDEX.md` 的集成清单位置 → demo 面的 Fake 符号族 → 本机仍无凭据）。

## 影响报告

- **Domain/API/schema 变化**：无（本轮只写文档 + 判据 + 索引登记）。
- **安全/凭据变化**：无新凭据面；文档只写变量名与边界，不写值、不写示例 key。
- **兼容性/迁移风险**：无（纯新增文档与判据）。
- **上游版本影响**：无（不引入依赖、不改 pin）。
- **下一项任务**：EC-06 已收口 ⇒ **GOAL-008 进入终止判定与收口**（EC-01…EC-06 全 PASS +
  独立 RECHECK + 残余登记 + 干净 checkout 封印 + CI 台账，按 GOAL「终止与收口」小节执行）。

- 2026-09-20 实施与复检（WP-A…WP-C）：`status: DONE`，`latest_recheck` 指向
  RECHECK-20260920-119（**PASS_WITH_WARNINGS**，W-1…W-6）。runbook 五节 + `docs/INDEX.md`
  登记 + 同源判据落地；F1–F5 全部先红后复原，**且反证抓出判据自身两个洞**（F2 跨行反引号配对、
  F4 宽判「全文出现过」）并按缺陷修判据。**live 步骤仍未实测**（无凭据 ⇒ 门两条都关着），
  runbook 里如实标注。EC-06 是本 GOAL 最后一个 EC ⇒ 收口后进入 GOAL 终止判定。
