---
id: RECHECK-20260921-128
plan_id: PLAN-20260921-128
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-21
completed_at: 2026-09-21
reviewer: root-agent-goal-010-ec02
baseline_ref: 8d3afd4
checked_head: 本次收口提交（实现 + 本 RECHECK 同一次提交落地）
---

# RECHECK-20260921-128 — 证据链真实性（GOAL-010 EC-02）

## 检查范围

**不采信实施叙述**：从 EC-02 的**原始验收条件**重新核对——「`EVIDENCE_COVERAGE ≥ 1` 由
**真实可查的来源**满足（检索 / 制品 / 外部源），**不得由模型自述充当**」+
「来源记录**可读**（`GET /runs/{id}/evidence` + 其 SourceRecord 的 origin/trust_label 可取
且指向**非模型自述**的对象）」+「**反证**：去掉来源 ⇒ 判拒」+
「**不得**用『计数 ≥ 1』当作证据真实性的替代判据」+「**不得**放宽验收门」。
逐条核对：判别性质、真跑证据、反证的成对性、爆破面、门禁。

## 检查结果

### 1. 判别性质（AC-1）：可判、且模型自述**不可能**满足

判别性质写在**编排边界**：一条 source 计入 `EVIDENCE_COVERAGE`，
**当且仅当它的对象不是本任务自己产出的 artifact**（`artifact_id ∉ self_artifact_ids`）。
- **为什么模型自述不可能满足**：模型的自述**必然**是它自己的产出 ⇒ 必然落在
  `self_artifact_ids` 里 ⇒ 恒被排除。这不是约定，是构造性的。
- **判定是集合成员判定，不是 id 前缀启发式**：前缀会随生产者变化而失效；
  集合判定对新增生产者稳健。自述来源恒为 `{task_id}:{name}`，工具结果是
  `tool-result:...`，声明输入由组合根以独立 id 种入——三者**命名空间不相交**（实测确认）。
- **不碰 Domain、不碰门**：`packages/domain/acceptance.py` 只读 `inputs.evidence_source_count`
  这个整数（`:144-155`），「什么算来源」的判据在编排层 ⇒ 本次**零改动** Domain 与 gate。

### 2. 真跑证据（AC-2，**实跑**，非推断）

判据文件 `tests/e2e/test_evidence_chain_source_live.py`（本 PLAN 新增），
以**单条命令内联前缀**开门（`set -a; . ./.env; set +a` 后 `RESEARCHOS_AGENT_RUNTIME=openhands`），
跑前自检 `EnvCredentialResolver().has('LLM_MAIN_KEY')` ⇒ **True**（只问存在性，未物化值）。

**样本**（`scratch/ec02-live/ec02-live-source.json`，本 GOAL 的 EC-02 首份样本）：

- run `a2a1bfbf-fea1-44a5-bfd0-ac3396d5d054`，终态 **`SUCCEEDED`**，`failures` **为空**；
- `GET /runs/{id}/evidence` 的**读面**给出 **4** 条来源，`source_origin` 为：
  两个 `{task_id}:analysis_report`（`trust_label=GENERATED`，模型自述）+
  **两个 `input-corpus:console_demo_v1`（`trust_label=USER_PROVIDED`，非模型自述）**；
- 被引用的对象：`GET /artifacts/input-corpus:console_demo_v1` ⇒ `created_by=composition-root`、
  `state=VERIFIED`、`verified=true`、`digest=sha256:c295a71d…`（= 仓库文件
  `examples/inputs/console-demo-corpus-v1.json` 的字节 digest，**可独立重算**）。

⇒ **满足覆盖的那条来源确实是非模型自述的对象**，且它经**既有读面**可取（不是读库/读代码间接凑）。

### 3. 反证成对（AC-3，**三次压制**，均有先红后绿）

| 压制 | 改什么 | 结果 |
| --- | --- | --- |
| ① 去掉**协议声明** | `examples/protocols/sort_analysis_v1.yaml` 的 `inputs:` 移除 | 同源判据 **RED**（`test_protocols_declare_exactly_the_tabulated_inputs`）+ vertical slice **6 个用例 RED**（review 任务覆盖归零 ⇒ 判拒）；复原 ⇒ 全绿 |
| ② 去掉**种入** | `M7Harness.__init__` 的 `seed_run_inputs` 移除 | vertical slice **6 个用例 RED**（`declared input artifact … is not in the artifact store`）；复原 ⇒ 全绿 |
| ③ 撤掉**收紧** | `evidence_source_count` 改回 `len(self.evidence)` | `tests/application/evidence/test_provenance.py` **3 个用例 RED**（`1 != 0`）；复原 ⇒ 全绿 |

压制 ③ 是 AC-4 要的那条：**撤掉收紧 ⇒ 判据红**，证明收紧**真的在判据里生效**，
而不是「实现改了、判据没看见」。三次压制后 `git diff` 只剩意图内改动。

### 4. 爆破面（AC-5）：逐个点名 + 各自如何满足新口径

| 声明 | 值 | 谁在跑它 | 收紧后 | 如何满足 |
| --- | --- | --- | --- | --- |
| `console_demo_deliverable` | min 1 | console demo / EC-03 离线链 / EC-01·EC-02 live 判据 | **会改判** | 协议两个 phase 声明 `input-corpus:console_demo_v1`；组合根（`services/api/composition.py` + 三个测试装配点 + `M7Harness`）种入 |
| `sort_analysis_review` | min 1 | `tests/api/run_fixtures.py`、`tests/e2e/scenario_catalog.py` 两处夹具 | **会改判** | 协议 review phase 声明 `input-corpus:sort_analysis_v1`；同上种入。**刻意不声明**上游 `analysis_report`——那是另一个 agent 的产出，仍是模型自述 |
| `domain_discovery` | min **10** | **没有任何 run 路径**：`minimum_sources: 10` 全仓只在 `tests/domain/test_tasks_acceptance.py:223`（手搭 `CriterionInputs`，不经 run）与 catalog 文件出现 | **不改判** | 如实登记：它的 min 10 **从未在 run 面上被行使过**（既没被满足过，也没被违反过）⇒ 本 cycle 不为它造来源；要真被行使需检索类工具结果（`literature.search` 的真实接线），**登记为残余** |

### 5. 未见放宽（AC-6）：逐文件核对

- `packages/domain/acceptance.py`：**零改动**（比较语义未动）。
- `examples/contracts/task_contracts.yaml`：**零改动**（`minimum_sources` 未被调低）。
- 唯一动过的判据是 `tests/e2e/scenario_catalog.py::_review_contract` **加了一条
  `ARTIFACT_EXISTS review_decision`**——这是**收紧**不是放宽（见 W-1），且理由独立成段。

## 警告（W 列表，如实登记，不掩盖）

- **W-1（判据面的唯一改动，须人工复核）**：`sort_analysis_review` 合约新增
  `ARTIFACT_EXISTS review_decision`。**为什么**：F-12 场景（review 只回一个字符串、
  产不出制品）此前**仅仅**因为旧口径 `len(evidence)` 才判拒；口径收紧后覆盖**如实**通过，
  于是「review 什么都不产出也算过」这个洞暴露出来。它从来不是覆盖判据该管的事，而是该
  合约**欠声明**（协议写了 `outputs: [review_decision]`，合约却没要求它存在）。
  补上后空复核仍判拒，理由指向它自己没交货。**但这是一处 play 内容改动，独立复核应重点压它**：
  若把这条判为「为让测试过而改判据」，则本 cycle 的 AC-6 需要重判。
- **W-2（live 调用 4 次，超「最小必要」）**：本 EC 的真实调用实际发了 **4** 次
  （1 次判据文件自身的读面字段名写错、1 次 DTO 字段名写错、1 次终检、1 次样本落盘）。
  **归因**：全部是**判据/读面胶水的缺陷**，不是端点缺陷；没有任何一次是为了「换个结果再试」。
  但仍**超出**「最小必要」——如实记录，不辩解。
- **W-3（来源口径的诚实边界）**：声明输入证明的是「**交付物与它被供应的输入之间有可核验的
  grounding 关系**」，**不**证明任务**真的读了**那份输入。后者只有工具观测能证，
  而 live 判据里的工具是**惰性**的（`InertExecutor` 恒返回 `"inert"`）。
  **不得**把前者写成后者。
- **W-4（`inputs` 的语义边界）**：`ProtocolPhase.inputs` 今天只解析**外部供应**的输入制品，
  **不**解析 phase 间产物引用（上游产出是另一个 agent 的输出，仍属模型自述，
  按定义**不该**计入覆盖）。若将来要表达「本 phase 消费上游产物」，需要一个**不同的**字段或
  用途区分，不能复用 `inputs` 而不改语义。
- **W-5（来源挂 claim 的语义借用）**：`GET /runs/{id}/evidence` 的投影**只经 claim relations** 走
  （`services/api/run_evidence.evidence_of_run`），所以声明输入的 evidence 必须
  `attach_relation(SUPPORTS)` 才可读。`SUPPORTS` 在这里的**确切含义是 grounding**，
  不是「输入证明了交付物的结论」。这是一次**语义借用**，须在文档里写明（已在
  `result_handler.register_declared_input_sources` 的 docstring 与协议注释中写明）。
- **W-6（SourceRecord 读面是本次新增的）**：加字段之前 `SourceRecord` 在 `services/` 里
  **零命中**——即 EC-02 的判据用语「其 `origin`/`trust_label` 可取」**此前根本无法满足**。
  本次给 `EvidenceDto` 加了 `source_origin` / `source_trust_label` / `source_access_time`
  三个只读字段（取不到时为 `null`，不伪填充）。**反向风险**：这是 API 面的**扩展**，
  旧客户端不受影响，但**新判据依赖它** ⇒ 若有人移除这三个字段，EC-02 的 live 判据会红。
- **W-7（`domain_discovery` min 10 仍未行使）**：见爆破面表。**不是**本 EC 达成的证据，
  也**不是**它失败的证据——是**未覆盖面**。
- **W-8（`evidence_source_count` 的缺省退路）**：`ResultRegistration` 若**不传**
  `self_artifact_ids`（缺省空集），计数会退化成旧口径。生产两条路径都传了
  （`register_session_result` / `registration_from_experiment`），但**构造 `ResultRegistration`
  的第三方代码**（如测试）若漏传，会得到一个偏松的计数。登记为**已知薄弱面**。
- **W-9（与 WP2b 原文的偏离：拒绝发生在哪一层）**：WP2b 写的是「解析不到真实对象 ⇒ **preflight**
  判『输入 Artifact 不完整』并拒绝进 RUNNING」，**实际落在登记期 fail-closed**（
  `register_declared_input_sources` 的 `InvalidInputError`）。**实质相同**：不伪填充、
  没进 RUNNING、run 落 `FAILED`（真跑的压制 ② 给出过 run 级证据：`declared input artifact … is
  not in the artifact store`）。**差别是诊断更晚也更钝**——run 直接是 `FAILED` 且
  `manifest_digest: null`，而不是一条「输入不完整」的 preflight 拒绝。**未修**：改 preflight
  会动到 EC-01 已达成的那条路径，超出本 cycle「WP2a…WP2e」的授权范围；如实登记。
- **W-10（本 cycle 自己造成又修好的两条回归 R-1 / R-2）**：见下节——**全量 m0 抓出来的**，
  不是推断出来的。两条都是**修好的**，登记为 W 是因为它们改变了「本 cycle 有多干净」的口径：
  **定向套件全绿并不足以证明没有回归**，正是全量 m0 才抓出来。
- **W-11（本地 m0 的 recipe 少了 `--keep-going`）**：本 cycle 第一次跑的本地 m0 用的是
  `--profile m0`（**没有** `--keep-going`，与 `make validate-all` 的调用**不一致**），
  于是它在第一个失败处**停下**，只跑了 6/23 项就报「1 check(s) failed」——
  **红是真的，但覆盖面被截断了**。最终证据用的是 `--keep-going` 的全量跑。
  登记：本地复跑 m0 应当**照抄 Makefile 的 `--keep-going`**，否则会低估失败面。

## 本 cycle 自己造成、又被自身门禁抓出并修好的两条回归（如实记录）

**两条都不是推断出来的，是全量 m0 抓出来的**。共同根因是同一类疏忽：**改了共享面，却没把
所有依赖它的装配点/夹具一起改**。

### R-1：PG 组合根漏种声明输入（`python/tests` 红）

**现象**：本 cycle 第一次全量 m0 的 `python/tests` 红 —— `1 failed, 4277 passed, 15 skipped`，
唯一失败是 `tests/postgres/test_m13_pg_run_e2e.py::test_pg_stores_run_to_succeeded`：
PG 存储下跑 `console_demo_research_v1.yaml` 的 run 终态是 **`FAILED`**（断言要 `SUCCEEDED`），
且 `manifest_digest: null` / `execution.execution_backend: null` ⇒ **死在执行之前**。

**根因（实测，不是推断）**：`console_demo_research_v1.yaml` 新增的 `inputs:` 声明作用于**每一个**
组合根，而我当时只给 **SQLite** 组合根与几个测试 harness 种了输入制品。
对同一个 `_make_pg_deps` 装配直接点名探测 ⇒ **`ARTIFACT COUNT: 0`**、
`HAS DECLARED INPUT: False` ⇒ 登记输入时 fail-closed ⇒ run `FAILED`。

**修法**：`services/api/pg_composition.py` 的 `build_postgres_assembly` 与 SQLite 组合根**同一职责**
（`seed_declared_inputs(c["artifacts"])`）；可重入性**先验证过**（`put` 是 upsert 且把行重置为
`STAGED`，`mark` 才做 `STAGED → VERIFIED`，故 put+mark **合起来**可重跑）。
**修后**：`tests/postgres/test_m13_pg_run_e2e.py` ⇒ **1 passed**；全量 m0 的 `python/tests` ⇒
**4278 passed / 15 skipped / 0 failed（516.22s）**。

**把这一类钉住（结构判据，不是补丁）**：`tests/architecture/python/test_declared_input_sources.py`
的第三个用例改为**从文件本身推出**「控制面组合根」集合（`services/api/` **顶层**模块里既造
`ArtifactStore(` 又接进 `artifacts=` 的那些），要求**每一个**都种入，并断言集合**恰为**
`{composition.py, pg_composition.py}` —— 新增一个组合根会让判据变红，逼加它的人当场决定。
（job 平面 `worker_gateway/` 子包**不在**集合里：它服务 worker 会话，不是跑验收门的 run 平面。
这是**有意的**集合边界，不是漏网。）
**压制 ④**：把 PG 组合根的 `seed_declared_inputs(` 摘掉 ⇒ 该判据 **RED**
（`pg_composition.py 装配了 artifact 平面却没有种入 demo 协议声明的输入`）；复原 ⇒ 三用例全绿。

### R-2：前端夹具未跟上 DTO 新增字段（`typescript/typecheck` 红）

**现象**：同一轮 m0 继续跑下去，`typescript/typecheck` 红：
`apps/web/tests/unit/consoleFixtures.ts(23,14): error TS2739: … is missing the following
properties from type 'EvidenceDto': source_origin, source_trust_label, source_access_time`。

**根因**：W-6 给 `EvidenceDto` 加了三个**必填可空**字段（与同文件既有约定一致，如
`experiment_run_id: string | null`），而手写的前端单测夹具仍按旧形状字面量构造 ⇒ 类型不符。
**这是类型一致性缺陷，不是断言被削弱**。

**修法**：夹具补上三个字段，取值与产品语义**同形**——自产 evidence 的
`origin` 就是它自己的 `source_ref`，信任标签 `GENERATED`（后端 `register_source` 就是这么写的），
时间戳沿用该夹具组既有的 `2026-09-09T00:00:00Z`。**修后**：
`typescript` 组全绿 ⇒ `PASS: profile=typescript; 9 deterministic checks`。

**教训（同 R-1，已写进 `MEM-20260921-101` 第 4 条）**：一条**共享**的声明/DTO 改动会同时作用于
**所有**消费者；「谁要跟着改」必须用**结构判据或类型系统**钉住——本次两条都是**门禁**抓出来的，
这正是门禁存在的意义，但它们也说明**push 前必须跑全量 m0**，不能只跑受影响的定向套件。

## 最终门禁（AC-6）

| 门 | 结果 |
| --- | --- |
| 全量 m0（**`--keep-going`**，CI 同形配置：测试 DSN pin + 其余 DSN 键置空 + `LLM_MAIN_KEY=""`） | **`PASS: profile=m0; 23 deterministic checks`**（exit 0）；`python/tests` = **4278 passed / 15 skipped / 0 failed（513.38s）** |
| `typescript` 组单跑（修 R-2 后） | **`PASS: profile=typescript; 9 deterministic checks`** |
| 治理 `validate.py` | **通过**（先在它上面抓到三处真漂移：`ALL_PLAN` 状态投影 `IN_PROGRESS != DONE`、勾选未同步、`MEM-20260921-101` 缺 4 个必需章节——**逐条修掉后复跑通过**） |
| 凭据纪律 | 被跟踪文件里含凭据值的个数 = **0**（只输出命中数）；`.env` 中**不含** `RESEARCHOS_AGENT_RUNTIME`；live 开关只作**单条命令内联前缀**，跑后未留在环境或 `.env` |

23 项 = python 6 + typescript 9 + framework 8（`validate_bundle` / `validate` /
`validate_cursor_framework` / `validate_cursor_learning` / hook evals / framework evals / learning evals /
`docs_consistency_check`）+ `release-assets-immutable`。

**过程如实记录（W-11）**：本 cycle **第一次**本地 m0 用的是 `--profile m0`（**无** `--keep-going`），
它在第一个失败处停下、只跑了 6/23 项——红是真的，但**覆盖面被截断**。
最终证据用的是与 `make validate-all` 一致的 `--keep-going` 全量跑。这也说明**不是三次压制
或定向套件**能替代全量门：两条回归（R-1 / R-2）都只有全量跑才看得见。

## 结论

**PASS_WITH_WARNINGS**。EC-02 的四条判据（判别性质 / 真跑来源可读 / 反证成对 / 未见放宽）
**逐条有实测证据**；爆破面逐个点名且各自满足新口径；W-1（判据面的唯一改动）与
W-2（live 调用超最小必要）是两处**须人工复核**的登记项。
**本 cycle 自己造成并修好两条回归（R-1 / R-2）**，两条**都是全量 m0 抓出来的**（不是推断），
修后各自有**先红后绿**的证据，R-1 还新增了结构判据（压制 ④）。
**最终门禁**：`python/tests` 4278 passed / 15 skipped / 0 failed；`typescript` 组
`PASS: profile=typescript; 9 deterministic checks`；全量 m0 见「最终门禁」一节。
