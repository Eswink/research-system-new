---
id: RECHECK-20260924-159
plan_id: PLAN-20260924-157
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: root-agent-goal-014-ec03 + 可复跑探针三份（scratch/goal014_c3_*.py）
baseline_ref: 6d574c7（cycle 2 纠错后的绿 tip）
checked_head: 当前树（cycle 3 文档 + 判据 + 4 组按压落盘）
---

# RECHECK-20260924-159 — GOAL-014 EC-03 策略面双向差集审计（cycle 3）

## 检查范围

① 差集表与判据是否**同源**（判据重算、文档只作载体）且**双向完备**（两个方向都断言）；
② 「零待定」是否真的零（文档 + 判据两侧）；③ 核心断言是否**对机制**断言而不是对文档断言；
④ 判据自身有没有**空断言**（恒真断言 = 没断言）；⑤ 有没有为了让判据通过而改门禁 / 策略面 /
合约 / 快照 / 既有断言；⑥ 本地 m0 与用例数归因。

## 检查结果

### 一、判据与文档同源，且双向完备

判据 `tests/application/preflight/test_policy_surface_difference_set.py` **自己重算**差集
（读同一批 YAML、同一套口径），再把结果与文档 `docs/architecture/POLICY_SURFACE_AUDIT.md`
的表格逐行比对：`test_the_difference_set_and_the_table_are_two_way_complete` 同时断言
「差集有而表缺」与「表有而差集无」两向，并断言无重复行。⇒ 文档不能单独漂移。

**逐列机械断言**（`test_each_row_state_matches_the_mechanical_rule`）：35 行的
**声明面 / 协议可达 / 读类 / 终态 / 差集侧**列**全部**要与机制算出的值相等。
其中**声明面列是本复检当场补上的**：初稿只断言后四列，声明面列（`roles、skills` 之类）
会**静默漂移**（例如某能力从 skills 撤走但仍在 roles ⇒ 差集与终态都不变，列却写着旧值）。

**空断言复核**（本复检专门查的一类）：初稿里 `test_the_registry_vocabulary_is_not_...`
写的是 `not (vocabulary_only & set(difference_set()))` —— 因为
`vocabulary_only := vocabulary − declared()` 与 `difference_set()` 的**策略面独有**侧
本就可能有交集（那 6 条策略面独有恰好都在词表里），该式**恒真**，等于没断言。
**已在提交前改掉**（改法见第四节），并且改后由 press2 / press3 两组按压证明它有内容。

### 二、零待定是真的零

- 文档侧：35 行终态列**只**出现「该放行 / 该拒绝 / 该登记」三种取值（`grep` 可核）。
- 判据侧：`test_every_row_has_exactly_one_terminal_state_and_no_pending_token` 逐行断言
  取值 ∈ `STATES`、不含 `("待定", "待确认", "含糊", "TBD", "TODO", "?")` 任一词、依据非空。
- **负向实测**（press1）：把某行终态改成 `待定` ⇒ **2 failed**（终态闭环 + 逐行判定）；
  还原 ⇒ **7 passed**。

### 三、核心断言是对机制断言的

`test_no_protocol_reachable_capability_lacks_a_rule` **不读文档**：它自己算
`reachable()`（协议 phase ∪ 所引合约的 `required_capabilities`，与
`protocol_compile/requirements.py::phase_capabilities()` 同口径），再对 `policy.yaml`
的 `allow` / `allow_with_constraints` 求覆盖，断言**空集**。
⇒ 任何人给协议加一条没人放行的能力，这里当场红（不依赖文档同步，文档也会因缺行另判红）。

另有一条**修复面护栏**（`test_allowed_capabilities_are_not_reported_as_gaps`）：
`evidence.read` / `literature.search` 必须仍**协议可达**、仍被放行规则覆盖、且不在差集内
—— 三向同时断言，防止 `W-A` 的修复被悄悄回退。

### 四、成对按压（4 组，含一组**隔离**按压）

| 按压 | 注入 | 结果（注入后） | 还原后 |
| --- | --- | --- | --- |
| press1 | 文档某行终态改 `待定` | 2 failed（终态闭环 + 逐行判定） | 7 passed |
| press2 | `skills.yaml` 加**词表外**能力 `tooling.experiment` | 2 failed（双向完备 + 词表护栏） | 7 passed |
| press3 | `skills.yaml` 加**词表内**未声明能力 `gpu.use` | **1 failed（只有双向完备）** | 7 passed |
| press4 | 文档塞一条陈旧行 `ghost.capability` | 2 failed（双向完备 + 逐行判定） | 7 passed |

**press3 是隔离按压**：它证明「双向完备」与「词表护栏」是**两条各自有内容**的断言
（不是一条顶两条）；press4 覆盖「表有而差集无」那一向。四组还原后
`git diff --stat`（`examples/config/skills.yaml`、`docs/architecture/`）**为空**。

**一处中途偏差（如实登记，已修正）**：按压脚本走 Python 文本模式 ⇒ 写回时把行尾改成
**CRLF**；本仓 `.gitattributes` 是 `* text=auto eol=lf`，**`git diff` 对这类改动是看不见的**
⇒ 「`git diff` 为空」**不足以**证明逐字节还原。实测偏差存在
（`cmp` 报 `differ: byte 8`、CR 字节数 45 而 HEAD 为 0），已用
`git checkout -- examples/config/skills.yaml` 恢复 ⇒ `cmp` **BYTES IDENTICAL**、CR=0、
`git status` 不再列为修改。核对与口径落 `scratch/goal014-c3-press-restore-note.md`。

### 五、有没有为了让判据通过而动别的东西

- **零产品代码改动、零策略面改动、零合约/快照/门禁改动、零既有断言改动**。
  本 cycle 的两个新增文件：文档 1 + 判据 1（判据只读 YAML）。
- 判据离线：`egress guard: judged 0 connection attempt(s); blocked 0`（零出网）。
- 文档门 `tools/docs_consistency_check.py` ⇒ `DOCS-CHECK PASS: 6 deterministic checks`。

### 六、本地 m0 与用例数归因

- **m0 = 22 PASS / 1 FAILED**（`scratch/goal014-c3-m0.log`）。唯一未绿 =
  **环境型残余 `R-F3`**，判词只有一条：`framework/validate_bundle` ⇒
  `Markdown 本地链接不存在: scratch\self-governance-bootstrap-prompt.md`
  —— 那是**并发写者**的 gitignored 文件（**不是**本 cycle 的产物；本 cycle 的 scratch 文件
  名为 `goal014_c3_*.py` / `goal014-c3-*.txt`），与 `R-F3` 的既有签名一致；
  CI 检出无 `scratch/` ⇒ **CI 不受影响**。**未**出现本 cycle 新文件的任何判词。
- `python/tests` = **4429 passed / 19 skipped / 0 failed**（cycle 2 基线 4421 / 19）
  ⇒ **+8 passed / +0 skipped**，与**逐用例 ID 差集**的 **+8、零删除**逐项吻合
  （7 条本判据 + 1 条源文件规模门禁参数化）。
- `DOCS-CHECK PASS: 6 deterministic checks`；治理 `validate.py` = `Cursor 治理验证通过`。

## 判据性质披露（必须读的一段）

- 本判据只覆盖**出厂 YAML 声明面**（`examples/config` + `examples/protocols` +
  `examples/contracts`）。它**不**覆盖：数据库里的运行时声明、**`action:` 形状**的门面规则
  （`TOOL_PACK_INSTALL_OR_UPDATE` / `MOUNT_DOCKER_SOCKET` 等，与能力不同命名空间）、
  以及 `examples/config/capabilities.yaml` 里**既不声明也不被策略面覆盖**的名字
  （实测 2 条：`git.commit`、`gpu.use` —— 它们不属于差集、本表不判）。
- 「该登记 = 15 条」**不是已修**：它是把「读类能力是否成类预放行」这个**口径问题**
  显式登记下来，**需用户拍板**；本 GOAL 的授权只覆盖 `evidence.read` 一条。
  ⇒ 用本 EC 的成功去声称「策略面已无隐患」是**错的**，只能说「协议可达面上无活缺口」。
- 判据**故意**对声明面敏感：给四个声明面加任何未登记能力都会判红（设计意图，
  逼差集表同步更新），这是**治理面**行为，不是产品行为回归。

## 结论

**`PASS_WITH_WARNINGS`** —— ① 差集表与判据同源、双向完备（`AC-1`/`AC-3` 达成）；
② 35 行零待定（`AC-2` 达成，且有负向按压）；③ 核心断言对机制断言、协议可达面 8/8 有覆盖
（`AC-5` 达成）；④ 4 组成对按压齐备含隔离按压、逐字节还原（`AC-6` 达成）；
⑤ 未动产品代码 / 策略面 / 合约 / 快照 / 门禁。
**WARN**：读类成类预放行是**未决口径**（15 条该登记）；`action:` 形状规则不在本表射程内。

## 仍未处理项（如实登记）

- **需拍板**：读类能力是否成类预放行（(a) 成类 / (b) 逐条 / (c) 不动）——
  属「不进入循环 / 需人工拍板」里的**授权外策略面**。
- EC-02 仍 `BLOCKED`（待拍板 `F-10` / `F-11`）；本 cycle **未**触碰。
- EC-04 / EC-05 未动（下一 cycle 起做 EC-04 残余登记）。
