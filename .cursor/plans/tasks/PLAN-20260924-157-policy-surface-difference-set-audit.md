---
id: PLAN-20260924-157
slug: policy-surface-difference-set-audit
title: 策略面 ↔ 声明面双向差集审计：35 条能力逐条终态 + 机械完备性判据（GOAL-014 EC-03）
status: DONE
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 建档授权（2026-09-24 用户 goal 模式指令）的 **EC-03**：
    「**策略面审计（双向差集）**：`policy.yaml` 每条规则 vs `roles.yaml` / `skills.yaml` /
    `tool_providers.yaml` / `examples/protocols/*.yaml` 声明的能力做双向差集，逐条判成
    **该放行 / 该拒绝 / 该登记** 三选一终态（零待定），依据可核对；差集表落仓库内文档，
    并配**可复跑的机械完备性判据**」。本 EC **完全在授权内、离线**（只读 YAML，零出网、
    零真实调用、不改任何产品代码/策略面/合约/快照）。
    **本 PLAN 明文不做**：改 validator / 门禁 / 快照 / 测试断言使其通过；skip/删除测试或
    降低断言强度；`git add -A`；伪造或夸大验证证据；**在授权范围外放宽任何策略面**；
    改 `test_m2_audit.py` 的镜像一致性判据。
    **本 PLAN 的结论是一条如实判定**：协议可达面上**没有第二个 `W-A`**（该放行 = 0），
    另有一条**口径问题**（读类能力是否成类预放行）**需用户拍板** —— 本 EC **不**自行扩大
    授权，**不**替用户决定，只把它作为唯一的「需拍板」项登记。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-159-policy-surface-difference-set-audit.md
memory_entries:
  - .cursor/memory/entries/MEM-20260924-126-reachable-surface-vs-declaration-surface.md
  - .cursor/memory/entries/MEM-20260924-127-press-restore-needs-byte-check.md
---

# PLAN-20260924-157 — 策略面 ↔ 声明面双向差集审计（GOAL-014 EC-03）

## 目标

把 `examples/config/policy.yaml` 的规则面与四个**使用声明面**做双向差集，逐条给一个
**三选一终态**（该放行 / 该拒绝 / 该登记，零待定），并让「差集表 ↔ 机制」的一致性
由一个**离线可复跑**的判据守住 —— 目的是证明 `W-A` 暴露的是**一类**问题，
且**没有第二个同类活缺口埋着**。

## 计划开始前的定案（写死）

- **D-1｜策略面只取 `capability:`**：`policy.yaml` 的规则有两种形状 —— 带 `capability:`
  （能力）与带 `action:`（门面动作，如 `TOOL_PACK_INSTALL_OR_UPDATE` /
  `MOUNT_DOCKER_SOCKET`）。`action:` 与能力不同命名空间，**不进本表**。同理**不取**
  `scope:` 的值（`project` / `approved_domains` / memory tier 都不是能力），
  **不取** provider 的 `network_domains`（域名串不是能力）。
- **D-2｜声明面 = 四个使用面，词表除外**：`roles.yaml` 的 `requested_capabilities`、
  `skills.yaml` 的 `capabilities`、`tool_providers.yaml` 的 `capabilities`、
  `examples/protocols/*.yaml` 的 phase `required_capabilities`。
  `capabilities.yaml` 是**词表**（注册可用能力名）——并入声明面会让差集**退化成空集**，
  故只作参照系、不参与比较；本 PLAN 为此写了一条**回归护栏**（见 AC-4）。
- **D-3｜判定基准是「协议可达」，不是「有人声明」**：只有出现在某 phase 的
  `required_capabilities`（或该 phase 所引合约的 `required_capabilities`）的能力，
  才会变成 `ToolRequirement` 进而被 `PolicyEvaluator` 判 —— 这与
  `packages/application/protocol_compile/requirements.py` 的 `phase_capabilities()`
  **同口径**。roles / skills / tool_providers 上的声明是**供给声明**（谁具备什么），
  本身不构成一次策略求值。这条把「活缺口」与「潜在缺口」分开。
- **D-4｜读类口径**：末段 ∈ {`read`, `inspect`, `validate`}，且若该能力被某 provider 声明，
  该 provider 的 `effect_class` 必须是 `READ_ONLY`（否则按写/执行类处置）。
- **D-5｜判定必须是机制的、不是散文的**：每条终态由**机械条件**推出（判据里是
  `expected_state()`），文档只是个表格载体 —— 判据重算后逐行比对文档，两边不一致就红。

## 验收条件

- [x] **AC-1｜差集表落仓库内**：`docs/architecture/POLICY_SURFACE_AUDIT.md` 承载 35 行表
      （6 条策略面独有 + 29 条声明面独有），列为
      `能力 / 差集侧 / 声明面 / 协议可达 / 读类 / 终态 / 依据`，并写明口径与判定条件。
- [x] **AC-2｜零待定**：35 行**全部**落在「该放行 / 该拒绝 / 该登记」三选一内；
  文档与判据两侧都无「待定 / 待确认 / 含糊 / TBD / TODO / ?」字样。
- [x] **AC-3｜双向完备**：差集 == 表格能力集（两个方向都断言：差集有而表缺、表有而差集无）；
  无重复行。
- [x] **AC-4｜词表不参与声明面**：声明面与策略面读到的名字**必须都在词表内**
  （防止把 `scope` 值、域名当能力读进来）；词表里必须存在「仅词表」的名字
  （一旦把 `capabilities.yaml` 算进声明面，这些名字消失、差集退化 ⇒ 立刻红）。
- [x] **AC-5｜核心断言**：**协议可达面上没有第二个 `W-A`** —— 8 条协议可达能力
  （`artifact.read` / `artifact.write` / `code.execute` / `evidence.read` /
  `literature.read` / `literature.search` / `workspace.read` / `workspace.write.code`）
  **全部**被非 `deny` 规则覆盖（6 条 `allow` + 2 条 `allow_with_constraints`）。
  判据直接对机制断言（不依赖差集表），并另有一条护栏守住 `W-A` 的修复面不许回退
  （`evidence.read` / `literature.search` 的放行规则被拿掉 ⇒ 红）。
- [x] **AC-6｜成对按压（红-绿）**：4 组按压，每组「注入 ⇒ 红，还原 ⇒ 绿」，
      还原**逐字节**（`git diff --stat` 为空，见证据）。

## 实施清单

- [x] **WP1｜预研测量**（`scratch/goal014_c3_diffset_probe.py` /
      `goal014-c3-diffset-probe.txt`）：先量出两侧差集与每条能力的**声明处**，
      确认规模 6 + 29 = 35、协议可达面 8 条，再谈判定。
- [x] **WP2｜逐条判定**（`scratch/goal014_c3_classify_probe.py` /
      `goal014-c3-classify-probe.txt`）：按 D-3/D-4 的机械条件给每条能力算终态，
      核对「该放行 = 0」，并把 15 条读类潜在缺口挑出来。
- [x] **WP3｜文档落表**（`docs/architecture/POLICY_SURFACE_AUDIT.md`）：口径、三个终态
      （含机械判定条件）、结论、35 行表、交集 9 条、复跑方式。
- [x] **WP4｜机械判据**（`tests/application/preflight/test_policy_surface_difference_set.py`，
      7 个用例）：重算差集 + 逐行比对文档 + 终态闭环 + 词表护栏 + 核心断言 + 修复面护栏。
- [x] **WP5｜成对按压**（`scratch/goal014_c3_press.py` /
      `goal014-c3-press-final.txt`）：4 组红-绿，含「注入后必须**只有**目标断言红」的隔离按压。
- [x] **WP6｜RECHECK + 回写**：RECHECK-159、本 PLAN 置 `DONE`、GOAL-014 回写
      （EC-03 `PASS` + 进度表 + 台账 + 子计划/记忆登记）。

## 结论（本 EC 的实质产出）

- **该放行 = 0 条** ⇒ 协议可达面上**没有第二个 `W-A`**：8/8 协议可达能力都有非 `deny` 规则。
- **该拒绝 = 20 条**：14 条声明面独有的写/执行/提议类（协议不可达 ⇒ 落 `default_effect: DENY`
  即正确）+ 6 条策略面独有的未使用护栏/门面规则（`external.publish` / `memory.write` /
  `network.academic` / `network.public` / `package.install` / `workspace.delete`）。
- **该登记 = 15 条**：声明面在用、**协议尚不要求**的**读类**能力（`agent_run.read` /
  `budget.read` / `citation.inspect` / `citation.validate` / `claim.read` / `dataset.read` /
  `deliverable.read` / `experiment.read` / `experiment_plan.read` / `provenance.read` /
  `research_map.read` / `research_state.read` / `review.read` / `run.read` / `target.read`）。
- **唯一需拍板项（不是本 GOAL 能自行决定的）**：**读类能力是否成类预放行** ——
  (a) 成类预放行（一次 `allow` 覆盖整类读能力，`W-A` 不会再以同一形态发生）；
  (b) 维持逐条放行（`W-A` 的先例就是逐条拍板）；
  (c) 保持 fail-closed 不动（协议要用时再放行）。本 GOAL 的授权**只**覆盖 `evidence.read`
  一条 ⇒ 这里**只登记、不扩大**。

## 证据

- **差集与判定**（`scratch/goal014-c3-diffset-probe.txt` / `goal014-c3-classify-probe.txt`）：
  策略面 15 个能力名（6 独有 + 9 交集）、声明面 38 个名字、差集 35 条；
  协议可达 8 条**全部**已在 `allow` / `allow_with_constraints` 覆盖。
- **判据实跑**（离线）：`pytest tests/application/preflight/test_policy_surface_difference_set.py -q`
  ⇒ **7 passed**，`egress guard: judged 0 connection attempt(s); blocked 0`（零出网）。
- **成对按压**（`scratch/goal014-c3-press-final.txt`，4 组，全部还原后 7 passed）：

  | 按压 | 注入 | 判红断言 | 说明 |
  | --- | --- | --- | --- |
  | press1 | 文档某行终态改 `待定` | 终态闭环 + 逐行判定 | 2 failed |
  | press2 | `skills.yaml` 加**词表外**能力 | 双向完备 + 词表护栏 | 2 failed |
  | press3 | `skills.yaml` 加**词表内**未声明能力（`gpu.use`） | **只有**双向完备 | 1 failed ⇒ 两条断言各自有内容 |
  | press4 | 文档塞一条陈旧行 | 双向完备 + 逐行判定 | 2 failed（覆盖「表有而差集无」） |

  四组还原后 `git diff --stat`（`skills.yaml` + `docs/architecture/`）**为空**。
  **一处中途偏差已如实登记并修正**：按压脚本走 Python 文本模式 ⇒ 写回把行尾改成 CRLF，
  而本仓 `.gitattributes`（`* text=auto eol=lf`）**让 `git diff` 看不见这种改动** ⇒
  「`git diff` 为空」不足以证明逐字节还原。已用 `git checkout -- examples/config/skills.yaml`
  恢复，`cmp` 与 HEAD **BYTES IDENTICAL**、CR 字节数 0；核对与口径落
  `scratch/goal014-c3-press-restore-note.md`（教训并入 `MEM-20260924-127`）。
- **用例数归因**（逐用例 ID 差集 `scratch/g014-collect-c2.txt` → `g014-collect-c3.txt`）：
  **+8、零删除** = 7 条本判据 + 1 条源文件规模门禁对新增 `.py` 的参数化。
- **本地 m0（`scratch/goal014-c3-m0.log`）**：**22 PASS / 1 FAILED** —— 唯一未绿 =
  **环境型残余 `R-F3`**：`framework/validate_bundle` 报
  `Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md`
  （**并发写者的 gitignored 文件**，不是本 cycle 的产物；CI 检出无 `scratch/` ⇒ 不受影响）。
  `python/tests` **4429 passed / 19 skipped / 0 failed**；`DOCS-CHECK PASS: 6 deterministic checks`；
  治理 `validate.py` = `Cursor 治理验证通过`。

## 状态历史

- 2026-09-24：derive + 执行（GOAL-014 cycle 3）。先做WP1 预研把口径与规模量死（不做判定），
  再按 D-3/D-4 的机械条件逐条判定（WP2），随后落文档（WP3）与判据（WP4）—— 判据与文档
  **同源**：判据重算差集与逐行终态，文档只承载表格。WP5 做 4 组成对按压（含一组隔离按压，
  证明「双向完备」与「词表护栏」互不顶替）。**未改任何产品代码 / 策略面 / 合约 / 快照 / 门禁**
  （按压两处均逐字节还原）。本 EC 全程离线、零真实调用（不是「未跑」，而是**必须**离线）。
- 2026-09-24（同日修订）：判据初稿里有**一处空断言**（`not (vocabulary ∩ diff − vocabulary)`
  恒真，等于没断言）与**一处判词与机制不符**（`expected_state()` 对**交集**能力返回
  「该拒绝」，而文档的该拒绝条件只覆盖差集条目）。两处都在提交前改掉：词表护栏重写为
  「两个方向都不许混进来 + 仅词表集合非空 + 策略面独有非空」，「不在差集内」成为显式取值
  `OUTSIDE_DIFF`（文档口径第 5 条同步写上「终态只判差集内的条目」）。**另补一条机械断言**：
  文档的**声明面**列也要等于机制算出的声明处串（初稿只断言差集侧 / 协议可达 / 读类 / 终态
  四列，声明面列会静默漂移）。修订后判据 7 passed，**4 组按压在最终版本上重跑**、仍先红后绿。

## 影响报告

- **改动面**：新增文档 1（`docs/architecture/POLICY_SURFACE_AUDIT.md`）、新增判据 1
  （`tests/application/preflight/test_policy_surface_difference_set.py`）；**零产品代码改动**、
  **零策略面改动**、零合约/快照/门禁改动。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：无。本 EC 离线、只读 YAML、零出网（判据自带出站守卫计数为 0）。
- **兼容性/迁移风险**：新增判据**故意**对声明面敏感 —— 以后任何人给 `skills.yaml` /
  `roles.yaml` / `tool_providers.yaml` / 协议加一条**未登记**的能力，它会立刻判红
  （这是设计意图：差集表必须同步更新）。这**不是**产品行为变化，是治理面变化。
- **上游版本影响**：无（不新增依赖、不改 pin）。
- **下一项任务**：EC-04（残余账目登记：Dependabot 23 条 / hook 侧 L3 门 / 450 行临近文件）
  或 EC-05（收口复检）。EC-02 仍 `BLOCKED`（待用户拍板 `F-10`/`F-11`），EC-03 已达成本轮目标。
