---
id: RECHECK-20260919-112
plan_id: PLAN-20260919-112
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle6
baseline_ref: 2cbc80c
checked_head: WORKTREE
---

# RECHECK-20260919-112 — `tool_pack.*` 二选一终态（GOAL-20260919-007 cycle 6 = EC-06）

## 检查范围

EC-06 允许两条路：(a) 既有边界内实现，(b) ADR 草案（Proposed）+ 权威登记 + 声明面同源收敛。
**本轮选 (b)**（理由见下），逐条对表：

| EC-06（b）要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| ADR 草案在树，`Status: Proposed` | `docs/adr/ADR-0031-toolpack-capability-policy.md` | 判据第 1 条：含 `Status: Proposed`、**不得**含 `Status: Accepted` |
| 权威登记（`docs/INDEX.md` 唯一入口） | `docs/INDEX.md` ADR 列表新增一行 | 判据第 2 条：条目行内含 `Proposed` |
| 声明/文档同源收敛 | 控制面 API 文档 / 控制台页面图 / live 夹具注释 三处 + ADR 自身 | 判据第 3 条：三处**同时**出现 `tool_pack` 与 ADR 文件名 |
| **不得只改注释/文案充数** | 判据的第 4 组：行为断言 + 反证 | 见「反证与实测」；**零产品代码改动**（`git diff --stat` 可核） |
| `Status` 不得写成 Accepted | — | 判据第 1 条同一断言（F-1 反证下变红） |
| 尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 / 治理 | 见「门禁」 | 见「门禁」 |

## 检查结果

### 为什么是 (b)：两条 (a) 的实现路径都命中 `escalation_triggers`

`tool_pack.*` 的"缺口"今天不是"没实现"，而是**实现到位、策略未定**：

- ① 给 `examples/config/policy.yaml` 加 `tool_pack.*` 的 `allow` 规则 ⇒ 从默认 deny 变成
  默认允许 = **放松核心安全策略**（GOAL 授权明确把"默认 deny 姿态不得放松"写进约束）；
- ② 让 `tool_pack.update` 走"待批准" ⇒ 必须改 `ToolPackLifecycle._require_decision` 对
  `REQUIRE_APPROVAL` 的处理（今天**只拦 DENY**）并决定审批语义 ⇒ **产品决策**。
  这条更危险的一面是：不配套改 `_require_decision` 就接通规则，结果是**静默放行**，
  比现状更差（ADR Context 第 4 条已点明）。

两条都留给用户拍板；EC-06 明文允许 (b)，故本轮交付 (b)。

### 草案今天说了什么（ADR-0031）

两个**可分别拍板**的决策面：

- **D1（`tool_pack.*` 能力策略）**：词表要不要收这四个能力名；`policy.yaml` 给
  allow / require_approval / 维持 DENY；若选 require_approval 是否同时要求生命周期
  **阻断 + 登记**；那条按构造不可匹配的 `action: TOOL_PACK_INSTALL_OR_UPDATE` 是删除、
  改写还是保留（保留就得让调用方真的传 `action`）。选项 D1-A（维持现状/运维显式放行）、
  D1-B（词表 + require_approval + 生命周期真处理）、D1-C（词表 + allow_with_constraints）
  各写了做法/收益/代价。
- **D2（「事实名 → 合约名」声明权）**：真实会话交付 `session_message`，示例合约要
  `analysis_report`，验收门是**字面包含**判定。映射由谁声明、写在哪、验收门是否保持字面
  判定（改判定 = Canonical 语义边界）。选项 D2-A（合约/计划侧声明）、D2-B（验收门支持
  别名）、D2-C（维持现状并如实呈现）。

`Trigger` 段给出三个"必须拍板"的时刻；`Consequences` 段写明草案期间的边界（默认 DENY 保持、
夹具层放行不得读作产品允许、循环内**不得**为了"让写面跑通"而放松）。

### 同源收敛：一处索引 + 三处声明面

| 面 | 收敛成什么 |
| --- | --- |
| `docs/INDEX.md` | ADR-0031 一行，行内标 `Proposed / 待拍板` |
| `docs/api/CONTROL_PLANE_API.md` | console 操作入口那条：原"未放宽产品策略"后**接上** ADR 指针与 `Proposed` |
| `docs/frontend/CONSOLE_PAGE_MAP.md` | ops/integrations 缺口登记那条：同上 |
| `tests/api/console_api_app.py` | 夹具策略类 docstring：夹具层放行**不等于**产品允许，处置待拍板 + ADR 指针 |

顺带澄清一处**文档与实现不符**：`docs/storage/DATABASE_SCHEMA.md` 的 Tool 草图写着
`tool_pack_manifests`，树里没有这张表（已落地的是 `tool_packs`）。该文档是**草图**
（`research_runs`、`artifacts` 等同样不是物理名），所以处置不是逐条改名，而是加一行
"草图名 ≠ 物理名"的注记并点出实际表名 —— 见 W-5。

### 判据证明的不是文案：三组行为断言

`tests/tooling/test_toolpack_capability_policy_pending.py`（**10 passed**）除了读文件，
还**实跑求值器与 use case**：

1. **真实平台策略仍判 DENY**：`examples/config/policy.yaml` 经 `NativePolicyEvaluator`，
   对 `tool_pack.install` / `.update` / `.revoke` 三个能力的判词都是
   `used default policy effect`（拒绝来自 default deny，不是某条规则）；
   并且平台策略里**没有任何** `tool_pack.*` 能力规则（结构断言）。
2. **那条 action 规则确实不可匹配**：从真实策略里取出该规则，断言
   `matches("tool_pack.install", None, …) is False`，只有显式传 action 才为 `True`；
   再走**公共 use case**（`ToolPackLifecycle.submit` + 记录型求值器）证明生命周期发出的
   请求 `action is None`，且**被拒**（`PermanentPortError`）。
3. **验收门仍按字面名判**：真实合约 `console_demo_deliverable` 的
   `ARTIFACT_EXISTS: analysis_report`，对 `{"session_message": …}` 判**不通过**、
   对 `{"analysis_report": …}` 判通过 —— 没有别名映射（D2 未拍板前的既有行为）。

## 反证与实测

三处注入（每处跑完即复原，工作树现值 = 复原后状态）：

| # | 注入 | 实测结果 |
| --- | --- | --- |
| F-1 | ADR `Status: Proposed` → `Accepted` | **1 failed**：`test_the_decision_record_is_a_proposal_not_a_decision` —— "草案必须是 Proposed：它还没被人工拍板" |
| F-2 | 删掉 live 夹具 docstring 里的 ADR 指针 | **1 failed**：`test_every_declaration_surface_points_at_the_same_record` 点名 `console_api_app.py 必须指向同一份决策记录（同源收敛）` |
| F-3a | 给 `policy.yaml` 加**带 scope** 的 `tool_pack.install` allow 规则 | **1 failed**：`test_platform_policy_declares_no_tool_pack_capability_rule`；`DENY` 那条**没红**（见 W-3 的实测细节） |
| F-3b | 同上但**不带 scope** | **3 failed**，其中一条是**行为红**：`test_the_lifecycle_never_asks_with_an_action` 报 `DID NOT RAISE PermanentPortError` —— 即 `lifecycle.submit(...)` 真的安装成功了，证明这条判据走的是**产品路径**而不是文本比对 |

F-3b 的行为红是本轮最有价值的一条证据：判据不是"注释对不对"，而是"策略一改，产品行为就变"。

## CI 失败分类与修复（SOP ⑥）

本轮**无 CI 红**。cycle 5 的教训（derive 提交带新 PLAN、ALL_PLAN 行在其后 ⇒ 本地绿、
CI 红）已在本轮开工前落实：**PLAN-20260919-112 与 ALL_PLAN 行同提交**（`d9537cb`）。
本条推送（tip `fcc8538`）的 M0 run 与 Push-on-main run 按闭合约定在回合汇报给出终态。

## Warnings（不阻断，如实登记）

- **W-1**：本轮交付的是**草案**。`Status: Proposed` 期间，真实部署下 `tool_pack.*` 仍 403，
  控制台写面仍不可用 —— EC-06 判的是"二选一终态已落地（登记形态 + 行为未变）"，
  **不是**"写面已可用"。
- **W-2**：`policy.yaml` 里那条 `action: TOOL_PACK_INSTALL_OR_UPDATE` **仍不可匹配**。
  本轮刻意不动产品策略；它是 D1(d) 的待拍板项。
- **W-3（实测细节，值得留档）**：策略规则的 `scope` 是**严格相等**匹配，而生命周期请求
  **不传 scope** ⇒ 任何带 `scope` 的 allow 规则都**不会**命中生命周期（F-3a：加了
  `scope: project` 的 allow 规则，DENY 判定安然无恙）；反之不带 scope 的 allow 规则会
  **立刻生效**（F-3b 里 `submit` 直接成功）。也就是说"运维显式放行"（D1-A）必须写成
  **不带 scope** 的规则，或由调用方补 scope —— 这条没有写在任何文档里，是实测出来的。
- **W-4**：判据测试钉的是**今天的事实**。拍板后一旦实施（改策略/改词表/改
  `_require_decision`/改验收语义），这条判据**会红**，实施者必须同时更新本记录与 ADR
  状态 —— 这是刻意设计（改行为先改记录），但要写明，免得被当成"测试碍事"。
- **W-5**：`DATABASE_SCHEMA.md` 的"草图名 ≠ 物理名"是**全局**现象（`research_runs` vs
  `runs`、`artifacts` 等）。本轮只加注记、未逐条改名 ⇒ 该文档仍是草图口径，不是物理
  表清单。
- **W-6**：D2 未拍板前，"真实 runtime 产出的研究物 → 声明式合约"这条组合**必然**在验收
  门判拒（EC-03 已固定该行为是链在正常工作）。本轮只是把它登记进了 ADR，**没有**解除。
- **W-7**：本轮**零产品代码改动**（改动面 = 1 个新 ADR + 4 个文档/夹具注释 + 1 个新测试
  文件）。"工具面没变"是**因为没改**，不是因为"实测没坏"。
- **W-8**：判据里"事实名仍来自 adapter"用的是**文本包含**（`session_message` 出现在
  `runtime_adapter.py`），强度低于 EC-03 那条端到端用例；真正的行为证明在
  `tests/e2e/test_ec03_real_runtime_offline_chain.py`。
- **W-9**：Mimosa 侧本轮沿用兼容策略（`scanner_enobufs`：提交/推送前未拿到完整扫描结论）
  ⇒ **不得**把本轮任何 PASS 读作"项目安全"。

## 结论

EC-06 **PASS_WITH_WARNINGS**：二选一判成 **(b) ADR 草案 + 权威登记 + 同源收敛**，理由是
(a) 的两条实现路径分别踩到"放松默认 deny"与"改审批语义"两条 escalation 线；ADR-0031
（`Status: Proposed`）把 **D1（`tool_pack.*` 能力策略）** 与 **D2（事实名 → 合约名声明权）**
两个决策面连同选项与代价摆出来，并写明触发条件与草案期间的边界。声明面四处同源收敛到该
ADR（含索引唯一入口），另澄清 `DATABASE_SCHEMA.md` 的草图名/物理名关系。**判据不是文案**：
三条行为断言（真实策略判 DENY 且判词来自 default、那条 action 规则不可匹配且生命周期请求
不带 action、验收门按字面名判拒）+ 三处注入反证，其中 F-3b 出现**行为红**
（`DID NOT RAISE`：加了无 scope 的 allow 规则后 `submit` 真的成功）。**零产品代码改动**，
默认 deny 姿态、能力词表、验收语义、生命周期决策处理均未触碰。W-1…W-9 如实登记，
其中 W-1（仍是草案）、W-3（scope 严格相等这条实测细节）、W-4（实施时判据必红，是刻意设计）
必须留档。

## 门禁

| 门 | 结果 |
| --- | --- |
| 判据测试 | `tests/tooling/test_toolpack_capability_policy_pending.py` **10 passed**（F-1/F-2/F-3a/F-3b 下各自变红） |
| 尺寸门（450 行 / 50 行函数） | **950 passed**（较上轮 +1 = 新增判据文件） |
| `ruff check` / `ruff format --check` | 绿（首跑红 1 处超长行，已折行） |
| `mypy`（新增文件） | `Success: no issues found in 1 source file` |
| 受影响套件 | `tests/{tooling,api}` **1543 passed**（钉 `RESEARCHOS_POSTGRES_DSN` 到 test DSN；不钉时 `tests/api/test_worker_plane_composition.py` 3 条因 operator `.env` 被 `load_dotenv` 注入而连不上库 —— 环境问题，同一批在 m0 全量下通过） |
| m0（23 项） | **PASS: profile=m0; 23 deterministic checks** |
| 治理 `validate.py` | 绿（ALL_PLAN 投影 / PLAN 章节 / RECHECK 章节 / GOAL 循环记录 / VERSION 单源） |
| 改动面 | `git diff --stat`：**零产品代码**；`docs/adr/` 1 个新文件、4 个文档/夹具注释、1 个新测试文件 |
