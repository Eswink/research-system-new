# POLICY_SURFACE_AUDIT.md — 策略面 ↔ 声明面双向差集审计

本文件是 `GOAL-20260924-014`（策略面一致性）**EC-03** 的交付物：把 `examples/config/policy.yaml`
的每条规则与实际声明面上出现的能力做**双向差集**，逐条给一个**终态**，证明
`W-A`（真实控制面对 `sort_analysis_v1` 的 `evidence.read` 判 `DENY`）暴露的是**一类**问题，
且**没有第二个同类活缺口埋着**。

判据与本文档**同源**：`tests/application/preflight/test_policy_surface_difference_set.py`
重新计算差集与本文档逐行比对（双向完备 + 终态闭环 + 逐行依据可核对）。改声明面而不改本文档
⇒ 判据红；把某个终态改成待定 ⇒ 判据红。

## 口径（写死，判据与本文档一致）

1. **策略面**：只取 `examples/config/policy.yaml` 每条规则的 `capability:` 字段。
   **不取** `action:`（`TOOL_PACK_INSTALL_OR_UPDATE` / `MOUNT_DOCKER_SOCKET` 等是**门面动作**，
   与能力不同命名空间，不在本表的比较范围内）；**不取** `scope:` 的值（`project` /
   `approved_domains` / memory tier 都不是能力）。
2. **声明面 = 四个使用声明面**：`examples/config/roles.yaml` 的 `requested_capabilities`、
   `examples/config/skills.yaml` 的 `capabilities`、`examples/config/tool_providers.yaml`
   的 `capabilities`、`examples/protocols/` 各协议的 phase `required_capabilities`。
   **`examples/config/capabilities.yaml` 是词表**（注册可用能力名），不是使用声明；
   并入差集会让"声明面"退化成全集、差集变空 —— 故只作参考，不参与比较。
3. **协议可达**（本表的判定基准）：能力出现在某份出厂协议的 phase `required_capabilities`，
   **或**出现在该 phase 所引合约的 `required_capabilities`（`packages/application/protocol_compile/requirements.py`
   的 `phase_capabilities()` 正是按这两处聚合的）。只有**协议可达**的能力会变成
   `ToolRequirement` 进而经 **同一张** `_CAPABILITY_SCOPE` 表被 `PolicyEvaluator` 判定；
   roles / skills / tool_providers 上的声明是**供给声明**（说明"谁具备什么"），
   本身不构成一次策略求值。
4. **读类**：能力名最后一段 ∈ {`read`, `inspect`, `validate`}，且若该能力被某个 provider 声明，
   该 provider 的 `effect_class` 必须是 `READ_ONLY`（否则按写/执行类处置）。
5. **终态只判差集内的条目**：两侧都出现的交集能力已由现网规则处理，不进表、不判终态
   （交集 9 条见文末）。

## 三个终态（互斥、闭合）

| 终态 | 含义 | 判定条件（机械） |
| --- | --- | --- |
| **该放行** | `W-A` 同类**活缺口**：协议可达却没有非 `deny` 规则覆盖 ⇒ 该协议在真实控制面必 `FAIL` | 协议可达 ∧ 无 `allow` / `allow_with_constraints` 规则 |
| **该拒绝** | 现状即正确：写/执行类落 `default_effect: DENY` 对；未使用的护栏/门面规则保留对 | （协议不可达 ∧ 非读类）∨ 策略面有规则而声明面无人使用 |
| **该登记** | **潜在**同类缺口：读类、声明面在用、协议尚不要求 ⇒ 是否**成类预放行**是口径问题，需拍板 | 协议不可达 ∧ 读类 ∧ 声明面在用 |

**没有第四个状态**：本表**零条**停留在「待定 / 待确认 / 含糊」。

## 结论

- **该放行 = 0 条** ⇒ **协议可达面上没有第二个 `W-A`**：8 条协议可达能力
  （`artifact.read`、`artifact.write`、`code.execute`、`evidence.read`、`literature.read`、
  `literature.search`、`workspace.read`、`workspace.write.code`）**全部**已被非 `deny` 规则覆盖
  （6 条 `allow` + 2 条 `allow_with_constraints`）。
- **该拒绝 = 20 条**：14 条声明面独有的写/执行/提议类 + 6 条策略面独有的未使用护栏/门面规则。
- **该登记 = 15 条**：声明面在用、协议不可达的**读类**能力（`agent_run.read`、`budget.read`、
  `citation.inspect`、`citation.validate`、`claim.read`、`dataset.read`、`deliverable.read`、
  `experiment.read`、`experiment_plan.read`、`provenance.read`、`research_map.read`、
  `research_state.read`、`review.read`、`run.read`、`target.read`）。

**需拍板的一条口径**（不是本 GOAL 能自行决定的）：**读类能力是否成类预放行**——
(a) 成类预放行（一次 `allow` 覆盖整类读能力，`W-A` 不会再以同一形态发生）；
(b) 维持逐条放行（`W-A` 的先例就是逐条拍板放行）；
(c) 保持 fail-closed 不动（协议要用时再放行，代价是每次都要一次拍板）。
本 GOAL 的授权**只**覆盖 `evidence.read` 一条，**不**自行扩大。

---

## 差集表（35 行 = 策略面独有 6 + 声明面独有 29）

| 能力 | 差集侧 | 声明面 | 协议可达 | 读类 | 终态 | 依据 |
| --- | --- | --- | --- | --- | --- | --- |
| `agent_run.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `audit.write` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `budget.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `citation.inspect` | 声明面独有 | roles、skills、tool_providers | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `citation.validate` | 声明面独有 | roles、skills | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `claim.read` | 声明面独有 | roles、skills | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `dataset.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `decision.propose` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `deliverable.edit` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `deliverable.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `deliverable.write` | 声明面独有 | roles、skills | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `evidence.propose` | 声明面独有 | roles、skills | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `evidence.write` | 声明面独有 | roles、tool_providers | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `experiment.execute` | 声明面独有 | roles、skills | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `experiment.read` | 声明面独有 | roles、skills | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `experiment_plan.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `experiment_plan.write` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `external.publish` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |
| `git.diff` | 声明面独有 | roles、tool_providers | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `idea.review` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `idea.write` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `memory.write` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |
| `network.academic` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |
| `network.public` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |
| `package.install` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |
| `protocol.propose` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `provenance.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `research_map.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `research_state.read` | 声明面独有 | roles、skills | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `review.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `review.write` | 声明面独有 | roles、skills | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `run.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `statistics.execute` | 声明面独有 | roles | 否 | 否 | 该拒绝 | 声明面有、协议不可达；写/执行/提议类 ⇒ 落 `default_effect: DENY` 即正确 |
| `target.read` | 声明面独有 | roles | 否 | 是 | 该登记 | 声明面在读、协议尚不要求；**读类**是否成类预放行需拍板（`W-A` 的先例是逐条放行） |
| `workspace.delete` | 策略面独有 | （无） | 否 | 否 | 该拒绝 | 策略面有规则而四个声明面无人使用；未使用的护栏/门面规则，现状即正确 |

**两侧都有（交集，不在差集内，9 条）**：`artifact.read`、`artifact.write`、`code.execute`、
`evidence.read`、`literature.read`、`literature.search`、`workspace.read`、
`workspace.write.code`、`workspace.write.notes` —— 它们已被 `policy.yaml` 的
`allow` / `allow_with_constraints` 覆盖，属于「已经处理过」的那一类
（`evidence.read` 正是 `W-A` 被拍板放行后的结果）。

## 复跑方式（零出网）

```bash
PYTHONPATH=. uv run --frozen --no-sync python -B -m pytest \
  tests/application/preflight/test_policy_surface_difference_set.py -q
```

差集与逐行终态的**重算**在同名判据文件内（读同一批 YAML，用同一套口径）；
本文档只承载人类可读的表格与判定依据，判据负责断言两者一致。
