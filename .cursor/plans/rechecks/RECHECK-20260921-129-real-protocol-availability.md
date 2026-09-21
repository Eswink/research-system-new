---
id: RECHECK-20260921-129
plan_id: PLAN-20260921-129
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-21
completed_at: 2026-09-21
reviewer: root-agent-goal-010-ec03
baseline_ref: 8cbdd62
checked_head: 本次收口提交（判据强化 + 本 RECHECK + GOAL 回写同一次提交落地）
---

# RECHECK-20260921-129 — 真实协议的可用性（GOAL-010 EC-03）

## 检查范围

**不采信实施叙述**：从 GOAL-010 里 EC-03 的**原始判据**重新核对——
「所选**协议 id 出现在 run 的 canonical 事实里**（不是只出现在测试文件里）」+
「该协议文件在仓库中**存在且被登记**（加载器可解析）」+
「**反证**：把 canonical 事实里的协议标识改回 demo 协议 ⇒ 判据必须红」+
「**不得**为了让 run 跑通而把 `required_capabilities` 降到不成立」+
「**回退路径**必须写明（不涉及 Domain / Canonical State）」。
另加一条**目标级**核对：真实执行体下用**真实协议**跑到 `SUCCEEDED` 的那一次样本。

## 检查结果

### 1. 协议在册、可解析、登记面同源（verify 第 2 条）

- 文件 `examples/protocols/real_research_task_v1.yaml`，`id: real_research_task_v1_0_1`，
  **1 个 phase**（`single_agent` / `domain_researcher` / `artifact.read`）。
- **加载器可解析**：经产品路径 `POST /projects/example-project/compile` ⇒ `200 {status: PASS}`，
  唯一 finding 是 **INFO** 级 `DAG_ORPHAN_PHASE`（单 phase 无后继）——**如实**，不是缺陷。
- **登记面同源**：模板面 `services/api/routers/protocol_drafts.py` 新增 `real-research-task`；
  协议 id ↔ 合约 id ↔ 声明输入 id 三处逐字一致，且由同源结构判据
  `tests/architecture/python/test_declared_input_sources.py` 的协议映射钉住
  （该判据在 EC-02 已被压过：去掉映射 ⇒ 红）。
- **能力要求没有被削**：`required_capabilities: [artifact.read]` 取自 `policy.yaml` **已授予**集
  （`default_effect: DENY`），不是删空绕过 preflight；没有触碰
  GOAL frontmatter escalation 第 11 条（「删/削能力以过 preflight = 放宽」）。

### 2. canonical 事实里的身份（判据本体）

判据文件 `tests/api/test_real_protocol_identity.py`（4 用例）。**三个面互相钉死**：

| 面 | 取值处 | 断言 |
| --- | --- | --- |
| canonical run | API 读面（`runs_store` **优先**，`services/api/run_access.py`） | `protocol_id` == 文件自己声明的 `id:` |
| 被解析的字节 | 同上（`protocol_body_digest`） | == 该正文的 sha256（产品自己的读取器算） |
| 冻结正文 | **库**（`run_ready_deps.runs_store.get_run(...).protocol_body`） | 含它自己声明的 id |

**为什么不是「回读一个字段」**：只读 `protocol_id` 会被「run 记录照抄入参」这种平凡实现满足；
E-1/E-2 的失败形态是**登记面指向 A、run 装配 B**——只有把**文件自己的声明**与**被解析的字节**
一起钉住才会被抓出来。冻结正文经**库**回读（不是内存注册表），顺带把「重启续跑可恢复」这一半也钉了。

### 3. 目标级证据：真实执行体 + 真实协议 ⇒ `SUCCEEDED`（1 次）

live 载荷（`tests/e2e/test_real_protocol_run_live.py` 写到 `tmp_path` 的
`ec03-live-real-protocol.json`，**逐字**）：

```
run_id f9bef830-0ee3-4f05-8d40-ca57c1f5e643 | state SUCCEEDED | failures []
protocol_id real_research_task_v1_0_1
protocol_body_digest sha256:06c1c4d64296ae70a78340bbd90cf42f6bfb0c538c0a04158613092db2dc1d2b
artifacts [a7f7a896-c606-4742-900a-7ffa542a9038:analysis_report, input-brief:real_research_v1]
deliverable_id a7f7a896-…:analysis_report | declared_artifact analysis_report
fact_name session_message | contract_id real_research_deliverable
```

**独立离线核对**（不采信载荷自述）：用**产品自己的读取器**取那份协议正文再算 sha256
⇒ `sha256:06c1c4d6…dc1d2b`，与载荷里的 `protocol_body_digest` **逐字相同**。即这次 live run
解析并冻结的**就是**那份文件。
**默认门如实**：不配 runtime 时该模块 **skip**（实测 `1 skipped`），不存在「没开门也过」的假绿。
**调用纪律**：本 cycle 真实调用**共 1 次**，`RESEARCHOS_AGENT_RUNTIME` 只作**单条命令内联前缀**，
**未**写入 `.env`；凭据值只从环境读、未回显、未落盘。
**离线可达性**（live 前置事实）：同一合约在**默认装配**下也到 `SUCCEEDED`，读面证据为
`{task}:analysis_report`（`GENERATED`）+ `input-brief:real_research_v1`（`USER_PROVIDED`）
——即覆盖门由**声明输入**满足（EC-02 收紧后的口径对新协议同样成立）。

### 4. 反证与压制（全部先红后绿）

| # | 压制对象 | 结果 |
| --- | --- | --- |
| 1 | 从 `validate_bundle.py` 注册表删掉新 schema 行 | 该检查**红**（`JSON Schema 注册表不一致: ['real_research_deliverable_v1.schema.json']`） |
| 2 | 把该 schema 的 `additionalProperties` 改回 `true` | 同一检查**红**（`禁止 additionalProperties=true`） |
| 3 | 身份判据的期望值改成 demo 协议的 id | 真实协议那条**红**（`'real_research_task_v1_0_1' == 'console_demo_research_v1_0_1'`），**demo 那条仍绿**（证明不是一刀切地红）|
| 4 | 离线跑 live 模块（不开门） | **skip**（`1 skipped`），不是静默通过 |

另有**常驻成对断言**（不依赖人工压制）：两份协议各起一次 run，身份 / 正文摘要 / 正文内容
三者互不相同且互不出现对方的名字 ⇒ 判据**不可能是常量**。

### 5. 爆破面（承认的射程边界）

- **终结态的证明力**：live 载荷只证明「终态 `SUCCEEDED` + 交付物用声明名」，
  **不**证明交付物正文的质量；验收门本身只判 `ARTIFACT_EXISTS` + `EVIDENCE_COVERAGE`，
  **都不读内容**（承 EC-01/EC-02 的口径）。
- **单次样本**：live 是**一次**取样，不是统计；它证明「可达」，不证明「稳定可达」。
- **Fake 离线的身份判据**不能替代 live：两者都留着（前者便宜、可常驻；后者才是真实执行体）。
- **默认装配缺 artifact store**（`/runs/{id}/artifacts` 如实 503）⇒ 离线那条可达性判据是用
  **evidence `source_ref`** 判的交付物名字，不是经 artifact 读面（见 W-6）。

### 6. 门禁与 CI 台账

**本地门禁**（每个提交前跑在工作树上，`--keep-going`，CI 同形配置）：

| 提交 | 内容 | m0 全量 | pytest |
| --- | --- | --- | --- |
| `a448fc3` | WP2 落地 | **23/23 PASS** | 4278 passed / 15 skipped |
| `004f916` | WP3 判据 | **23/23 PASS** | 4282 passed / 15 skipped |
| `2edb204` | WP4 live 模块 | **23/23 PASS** | 4283 passed / 16 skipped |
| 本收口提交 | WP5（判据强化 + 记录） | **23/23 PASS** | 4284 passed / 16 skipped |

治理 `validate.py` 每次全绿；`python/typecheck` **抓到过一次真问题**（WP3 首次：`services.api.deps`
不显式导出 `ApiDeps` ⇒ 判据文件 import 报错），改成从定义处 `services.api.composition` 导入后绿。

**CI**（每个推送提交，两个 workflow，逐 job 实查）：

| 提交 | M0 Quality Gates | Push on main（CodeQL） |
| --- | --- | --- |
| `15be1eb` derive | 35587567675 **success** | 35587567385 **success** |
| `8cbdd62` WP1 | 35589392128 **success** | 35589391669 **success** |
| `a448fc3` WP2 | 35593973258 **success**（6 job） | 35593972477 **success**（3 job） |
| `004f916` WP3 | 35597030860 **success**（6 job） | 35597030000 **success**（3 job） |
| `2edb204` WP4 | 35598711734 **success**（6 job） | 35598711199 **success**（3 job） |
| 本收口提交 WP5 | 见回合汇报（台账尾巴口径） | 见回合汇报 |

**工具面教训（本轮自造自修）**：初次 CI 轮询脚本只打印了 `head_sha` 命中的**第一个** run
（`awk` 取第一个 id），差点把「两个 workflow 都绿」写成只有一个绿——已改成遍历该 SHA 的**全部**
run 并重查，本表因此是逐 run 实查的结果。

### 7. W 列表（如实登记，不由本 cycle 修）

- **W-1** 规格外新增的 `schemas/real_research_deliverable_v1.schema.json` + `validate_bundle.py`
  注册表**一行**是本 cycle 唯一触及**受治理文件**的改动，须**人工复核**。依据：合约 schema 要求
  `output_schema` 必填 ⇒ 必须有个名字；仓库既有的新 schema 维护路径就是「同提交加文件 + 注册行」
  （先例 `4156238` 同提交加入 `export_bundle_v1`/`reproducibility_audit_v1`）；注册表仍是**双向**
  一致检查、已**按压**（删行 ⇒ 红）、校验逻辑 `git diff` 仅一行新增。两个被否的备选：
  (d) 只声明名字不建文件（悬空声明）、(a) 复用语义不符的已注册名（EC-01 抓的那类「名不副实」）。
- **W-2** `output_schema` 在产品代码里**是惰性的**：没有任何生产代码注入 `schema_check`
  （`packages/domain/acceptance.py` 的 `SCHEMA_VALID` 因此永不会被求值）⇒ 新 schema 文件是
  **声明而非被执行**的约束；「信封 7 键」这条耦合**没有门禁把守**，只写在文件描述里。
- **W-3** live 载荷**不含交付物正文与 `message_count`** ⇒「模型真产出了正文」是**推论**不是实测：
  `ARTIFACT_EXISTS: analysis_report` 通过 ⇒ `_deliverable()` 的**非空分支**成立（无消息时 adapter
  返回 `{}`，就登记不出这件制品）⇒ 会话至少有一条 MESSAGE 事件。补成实测数字需要第二次真实调用，
  按「最小必要」**不做**。
- **W-4** **计划文本与实现的偏差（更窄，不是更松）**：WP1 的回退段写成「把登记面与
  `live_run_support._PROTOCOL` 指回 demo」，实现**没有**改 `_PROTOCOL`（EC-01/EC-02 的证据是在
  demo 协议上取的，**不追溯改写**），EC-03 的判据改为在**调用点**显式传 `REAL_PROTOCOL`。
  回退因此更便宜（删掉新文件 + 模板项即可），但与计划文本不一致，如实登记。
- **W-5** `runs_store` 只挂在 `run_ready` 装配上（`make_base_deps` **不带**）⇒ 身份判据必须在
  `run_ready_client` 上跑；默认装配的 run 读面会**回落到内存注册表**。该分工**没有门禁把守**
  （改 `conftest` 会让判据静默降级到内存读）。
- **W-6** 默认装配**没有 artifact store**（`/runs/{id}/artifacts` 如实 503）⇒ 离线可达性判据经
  evidence `source_ref` 判交付物名字，不经 artifact 读面。
- **W-7** `domain_discovery` 的 `minimum_sources: 10` **仍无任何 run 路径行使过**（承 EC-02 W-7；
  本 cycle 新协议用的是 `1`）。
- **W-8** 30 条 tracked 非 ASCII 路径（AGENTS §13，承前几个 cycle，未动）。
- **W-9** 本 cycle 的**本地 m0 跑在工作树上**，树上同时存在**另一个并发进程**的三处未提交改动
  （`apps/web/src/features/models/ModelDetails.tsx`、`packages/domain/model_drift.py`、
  `services/api/dto/models.py`）。它们**不在**本 cycle 的任何提交里，本 cycle 也不对它们作任何声称；
  每个提交的**权威证书是 CI 在推送树上的结果**（§6）。

## 结论

**PASS_WITH_WARNINGS**。EC-03 的判据（协议 id 出现在 run 的 **canonical 事实**里）在
**离线身份判据（三面钉死 + 常驻反证 + 按压）**与**一次真实 run（`SUCCEEDED`，身份与字节摘要
逐字吻合）**两侧都成立；协议文件在册、可解析、登记面同源；能力要求未削；回退路径已在 PLAN-129
写明（配置面改动，不涉及 Domain / Canonical State）。W-1 是唯一需要人工过目的面（受治理文件一行）；
W-2/W-3 是**证明力边界**，已如实写死；W-4/W-5 是**实现与文本/装配**的偏差，均为更窄口径。
