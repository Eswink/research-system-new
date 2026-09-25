# ADR-0031 — ToolPack 能力策略与「事实名 → 合约名」声明（ToolPack Capability Policy）

Status: Proposed
Date: 2026-09-19
Deciders: Eswink（single owner）— **待拍板**：本 ADR 是草案，不构成已接受的决策
Scope: `examples/config/policy.yaml`（平台默认策略）、`examples/config/capabilities.yaml`（能力词表）、
`packages/application/tool_plane/lifecycle.py`（`ToolPackLifecycle._require_decision`）、
`packages/domain/acceptance.py`（验收门的 artifact 名判定）、
`adapters/openhands/runtime_adapter.py`（会话交付物的键名）
（关联 ADR-0005、ADR-0014、ADR-0018、ADR-0019、ADR-0030）

## Context

ToolPack 的供应链写面（`GET /tool-packs` + `install` / `approve-update` / `revoke`）已经在树，
控制台入口也在树；它按**能力名**求值策略。但平台策略面与它之间有一段**声明与事实不符**的
空隙，且这段空隙今天同时是"安全的"和"不可用的"：

1. **平台策略没有任何 `tool_pack.*` 规则**。`examples/config/policy.yaml` 的
   `default_effect: DENY`，allow 列表里没有 ToolPack 相关能力 ⇒ 真实部署下
   `tool_pack.install|update|revoke` 一律判 DENY，控制台写面 403。
   现状下能跑通写链的**只有** live 夹具（`tests/api/console_api_app.py` 在夹具层放行四个
   能力），**产品策略未放宽**——这一点在 RECHECK-20260915-065 W-1 已如实登记。
2. **唯一的"意图声明"是死的**：`policy.yaml` 里有一条
   `action: TOOL_PACK_INSTALL_OR_UPDATE`（`require_approval` 段），但
   `ToolPackLifecycle._require_decision` 构造 `PolicyRequest` 时**只传 `capability=`**，
   而 `PolicyRule.matches` 在规则声明了 `action` 时要求 `request.action` 相等 ⇒
   **该规则按构造不可能匹配**。也就是说："我们打算把 ToolPack 安装纳入待批准"这句话
   写在策略文件里，策略面却从不消费它。
3. **能力词表不含 `tool_pack.*`**：`examples/config/capabilities.yaml` 的 48 项里没有它。
   写面 manifest 若声明未知能力会被 422，而生命周期**自身求值的能力名从不做词表校验**
   ⇒ 词表管得住"被声明的能力"，管不住"被求值的能力"。
4. **`_require_decision` 只拦 DENY**：`REQUIRE_APPROVAL` 既不阻断也不登记。因此今天若把
   第 2 条那条规则"接通"，结果是**静默放行**——比现状更差。
5. **"事实名"与"合约声明的 artifact 名"之间没有映射**：真实会话交付的键名是
   `session_message`（`adapters/openhands/runtime_adapter.py`），而演示合约要
   `analysis_report`（`examples/contracts/task_contracts.yaml`）；验收门是**字面包含**判定
   （`packages/domain/acceptance.py`），所以真实 runtime 的链**必然**在验收门判拒
   （EC-03 已固定该行为是"链在正常工作"，不是缺陷）。"谁能声明 `analysis_report`"
   是一个**产品决策**，adapter 明确不自行发明。

这三件事共同构成 GOAL-006「人工面」留下的 `tool_pack.*` 产品决策面：**不是"没实现"，
而是"实现到位、策略未定"**。循环内能做的只有两件事：如实登记 + 把可选方案与代价摆出来。
**放开默认策略（第 1 条）与改变验收语义（第 5 条）都属核心安全策略变更，需本 ADR 拍板。**

## Decision needed

请决策者就以下**两个**决定作出选择（可分别决定）：

**D1（ToolPack 能力策略）**：平台默认策略对 `tool_pack.install` / `tool_pack.update` /
`tool_pack.revoke`（以及派生名 `tool_pack.update.expanded`）应当如何处置？具体要定：
(a) 是否把这四个能力名写进 `examples/config/capabilities.yaml` 词表；
(b) `policy.yaml` 给它们 `allow` / `allow_with_constraints` / `require_approval` / 维持 DENY；
(c) 若选 `require_approval`，是否同时要求 `ToolPackLifecycle` **对 REQUIRE_APPROVAL 采取
阻断 + 登记**（否则等于静默放行，见 Context 第 4 条）；(d) `action:
TOOL_PACK_INSTALL_OR_UPDATE` 这条**不可匹配**的规则是删除、是改写成能力名规则，还是保留
（保留则必须修 `PolicyRequest` 传 `action` 的路径）。

**D2（事实名 → 合约名的声明权）**：真实会话产出的 `session_message` 与合约声明的
`analysis_report` 之间是否需要一层**显式映射**？如果需要，映射由谁声明、写在哪里
（合约侧声明可接受的别名？运行时侧声明产出满足哪个契约名？两侧都不动、由计划/编译期
声明"本阶段产出即该 artifact"？），以及**验收门是否保持字面判定**（改判定 = 改 Canonical
语义边界）。

> **D2 已定向（2026-09-21，用户指令）**：用户以 goal 模式指令建档 `GOAL-20260921-010`
> 并把它的一条退出标准定为「真实交付物契约」，给出二选一并要求「**受控、声明化、可审计**」，
> 判据是「一次真实 run 在真实执行体下验收门 PASS 且终态恰为 `SUCCEEDED`」，
> 反证是「删掉映射/契约 ⇒ 回到 REJECT」。**本 ADR 的两个决定是可分别决定的**，
> 而 **D1（`tool_pack.*` 能力策略）仍未决** ⇒ 本文件整体**保持 `Status: Proposed`**，
> 结构判据（`tests/tooling/test_toolpack_capability_policy_pending.py`）**不需要任何修改**。
>
> **D2 取 D2-A 形态**（「维持字面判定，映射由合约/计划侧声明」——ADR 原文列为**不改 Canonical
> 语义**的选项）：**验收门一字不改**（`packages/domain/acceptance.py` 仍按字面名匹配，
> D2-B 的别名映射**不做**）；交付物的键名改由**已在 `AgentSessionSpec.task_contract` 里的
> 合约声明**决定（声明恰一个 artifact 名 ⇒ 用该名；零个或**多个互不相同**的名字 ⇒ **不猜**，
> 回落事实名）。**声明权归合约**，adapter 只读声明、不发明映射；载荷登记
> `fact_name` / `declared_artifact` / `contract_id` 使「这个名字是谁声明的」**可判**。
> 实施与判据见 `PLAN-20260921-127`（GOAL-010 EC-01）。
>
> **本定向只覆盖 D2**：D1 的四项子决定（词表 / 策略效果 / `REQUIRE_APPROVAL` 是否阻断登记 /
> 那条不可匹配的 `action:` 规则）**仍然待拍板**，本 ADR 不因 D2 定向而被整体接受。

## Options

### D1-A 维持 `default_effect: DENY`，运维显式放行（现状）

- 做法：不动 `policy.yaml`；真实部署由运维在项目策略/运行环境显式放行。
- 收益：默认姿态不动（fail-closed 保持）；零新语义。
- 代价：控制台写面在真实默认下**不可用**（403），必须有一次显式运维动作；
  "意图声明"（`action:` 规则）继续不可匹配 ⇒ **声明与事实不符**持续存在。

### D1-B 写进词表 + `require_approval`，并让生命周期真正处理 REQUIRE_APPROVAL

- 做法：词表补四个能力名；`policy.yaml` 把它们放 `require_approval`；
  `_require_decision` 对 `REQUIRE_APPROVAL` 阻断并登记待批准（复用既有审批面）。
- 收益：与控制台"待批准横幅"语义一致；默认 deny 姿态不放松（待批准 ≠ 放行）。
- 代价：**改行为**（生命周期首次出现"拒绝并登记"的分支）；需要决定审批的落点
  （谁批、批多久、审批记录存哪）；工作量与回归面最大。

### D1-C 写进词表 + `allow_with_constraints`（例如要求 pin digest + 非内置 pack id）

- 做法：默认允许，但约束绑定既有供应链事实（`tool_pack_digests` 必须有有效 digest、
  pack id 非内置保留名）。
- 收益：控制台写面开箱可用；约束落在**已有读面**上，不新增状态。
- 代价：默认姿态从"拒绝"变成"允许"——**这是放松**，必须由用户明确拍板；
  且约束的强制点在生命周期而非策略面，需要新的判据。

### D2-A 维持字面判定，映射由合约/计划侧声明

- 做法：验收门不改；需要 `analysis_report` 的合约，其产出名由上游（协议/计划/合约）
  与运行时**协商成同一个名字**，或由计划显式声明"本阶段产出登记为该 artifact 名"。
- 收益：Canonical 语义不变；验收门保持"所见即所判"。
- 代价：需要一个**声明面**（写在哪、谁校验），否则依旧是隐性约定。

### D2-B 验收门支持别名/映射

- 做法：`acceptance.py` 引入 artifact 名映射（字面名 → 别名集合）。
- 收益：真实会话产物可直接满足声明式合约。
- 代价：**改 Canonical 判定语义**（"artifact 存在"的判据变成"某个别名存在"），
  影响所有既有合约与证据链的可解释性；属 Canonical 边界变更。

### D2-C 维持现状并如实呈现

- 做法：不改任何语义；把"真实会话产物名 ≠ 合约声明名 ⇒ 判拒"作为**正常结果**登记
  （EC-03 已如此固定），需要映射的产品决策留待未来。
- 收益：零风险；诚实。
- 代价：真实 runtime + 声明式合约的组合**开箱不可通过**验收门。

## Trigger（何时必须拍板）

- ToolPack 写面要进**真实部署的默认路径**（不是夹具/演示）时 —— D1 必须已定；
- 真实 runtime 要交付**声明式合约**要求的研究产物（不是演示合约）时 —— D2 必须已定；
- 任何"把 `tool_pack.*` 写进词表或策略"的改动之前（否则会先撞上不可匹配的 `action:` 规则，
  或直接放松默认姿态）。

## 否证条件（什么证据会否证本 ADR / 何时该改判）

本 ADR 挂着 `Proposed` 是**待拍板**，不是**可长期悬空**。下面给出**机械可判的出口**，
使「它到底还是不是一份草案」不再取决于谁记得它：

**①「D1 事实上已被决定」⇒ 应把本 ADR 转为已接受**。下列事实**同时**成立时：

1. `examples/config/policy.yaml` 出现任一 `tool_pack.*` 能力的**显式规则**
   （allow / allow_with_constraints / require_approval / deny 都算），
   **或** `ToolPackLifecycle` 的求值路径开始携带 `action=`（即那条 `action:` 规则变为可匹配）；
   **且**
2. 上述形态各有一条**判据**把守（策略面判据 + 行为判据，先红后绿）；
   **且**
3. D1 的四个子决定（词表是否收录 / 策略效果 / REQUIRE_APPROVAL 是否阻断并登记 /
   那条不可匹配规则的去留）都在 `docs/INDEX.md` 与三处声明面**同源**登记。
   ⇒ 到那时改本文件 `Status` 行，并把四个子决定逐条钉成引文。

**②「事实面消失」⇒ 应显式撤回**：ToolPack 写面被**整体移除**（控制台入口、生命周期、
读面一起下线），或产品明确决定**永不**在生产默认下开放该写面 ⇒ 本 ADR 针对的事实面
不再存在，应撤回而不是继续挂着。

**③「维持草案」的条件（= 今天）**：①② 都不成立 —— 策略面**仍无** `tool_pack.*` 规则、
求值**仍不**携带 `action=`、写面**仍在树且只在夹具层可用**。这三条本身就是**可实跑**的
判据（见 `tests/tooling/test_toolpack_capability_policy_pending.py` 的第 4 条「行为没变」）。

> **本节的来由**：`GOAL-20260925-016` 的 **D-07 → 取 (b)**（用户 2026-09-25 按
> `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板）：**本 ADR 维持 `Proposed`**，
> **不实施其内容**，并**补本节**以免它变成永远悬空的决策。
> 本节**不改 `Status` 行**、**不改任何行为**、**不加任何策略面规则**。

## Consequences（本 ADR 处于 Proposed 期间）

- 平台策略维持 `default_effect: DENY`，无 `tool_pack.*` 规则 ⇒ 控制台写面在真实默认下
  403，这是**已知且已登记**的行为，不是缺陷。
- 控制台/live 夹具层的放行**只服务测试链**，不得被读作"产品已允许"。
- 真实会话交付 `session_message` 必被声明 `analysis_report` 的合约判拒；该行为有专门用例
  固定，改动它必须先改本 ADR 的状态。
  **（2026-09-21 更新，D2 已定向）**：该前置已由上面的 D2 定向满足——**D2 这一半**已由用户
  拍板（见「Decision needed」的 D2 方框），因此交付物键名**不再**恒为事实名：合约声明恰一个
  artifact 名时交付物**就是**该名，验收门**仍按字面判定**（门本身未改）。
  **D1 未决，本 ADR 整体仍是 `Proposed`**；那条"专门用例"（离线全链的交付物裁决）已改为
  **双分支**：声明对齐 ⇒ 门 PASS；声明不对齐（零个或多个名字）⇒ 门 REJECT。
  **仍然成立**的约束：**不得**把 `tool_pack.*` 写进词表或策略、**不得**改验收门的判定语义。
- 循环内**不得**为了"让写面跑通"而加 allow 规则、改词表或改验收语义。

## Evidence / References

- 平台策略：`examples/config/policy.yaml`（`default_effect: DENY`；`require_approval` 段含
  不可匹配的 `action: TOOL_PACK_INSTALL_OR_UPDATE`）
- 能力词表：`examples/config/capabilities.yaml`（48 项，无 `tool_pack.*`）
- 生命周期：`packages/application/tool_plane/lifecycle.py`（四个能力名常量、`_require_decision`
  只拦 DENY）
- 策略匹配：`packages/domain/policy.py`（`PolicyRule.matches` 要求 action 相等）
- 供应链读面：`services/api/catalog_merge.py`、`packages/application/protocol_compile/compiler.py`、
  `packages/application/preflight/checks.py`（`SUPPLY_CHAIN_UNPINNED`）、`packages/domain/manifest.py`
- 验收门：`packages/domain/acceptance.py`（字面包含判定）
- 交付物键名：`adapters/openhands/runtime_adapter.py`（`session_message`）、
  `examples/contracts/task_contracts.yaml`（`artifact: analysis_report`）
- 既有登记：`RECHECK-20260915-065` W-1、`RECHECK-20260919-109` W-2、`MEM-20260915-040`
- 判据：`tests/tooling/test_toolpack_capability_policy_pending.py`（本 ADR 的结构判据：
  Proposed 状态、INDEX 登记、声明面同源、**行为未变**）
