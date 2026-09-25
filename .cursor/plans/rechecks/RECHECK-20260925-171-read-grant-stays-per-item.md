---
id: RECHECK-20260925-171
plan_id: PLAN-20260925-170
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-016-cycle2 + 只读取证（git status / git diff 对策略面文件）
baseline_ref: cycle 1 推送 tip `1e2af55`
checked_head: 当前树（判据 + 记录；**策略面与产品代码零改动**）
---

# RECHECK-20260925-171 — D-02(b) 口径判据（GOAL-016 cycle 2）

## 检查范围

① 判据是否真的判「逐条形态」而不是散文（AC-1）；② 否定判据是否**可被按压**（AC-2）；
③ 「该登记 15 条」是否**齐、全为读类、且一条都没被放行**（AC-3）；④ 读类放行是否**逐条可枚举**
（AC-4）；⑤ 策略面是否**逐字节未动**（AC-5）。

## 检查结果

### 一、AC-1｜逐条形态（结构否定）

- 断言面：策略面全部 `capability:` 的值必须**都是能力词表
  （`examples/config/capabilities.yaml`，46 项）的精确成员**；且**没有**任何规则的能力是另一个
  能力的**段前缀**（谓词 = `other.startswith(name + ".")`）。
- **为什么判前缀就够**：一条规则的 `capability` 是**一个字符串**，天然只命名一个能力；
  「一条规则覆盖一类」只能以**前缀**（`read` 覆盖 `read.x`）或**通配**（`read.*`）的形态出现
  ⇒ 判这两者即闭合。
- **实测**：`unknown == []`、`prefix_grants([]) == []`（策略面 15 条 `capability:` 规则里
  无一条是另一条的段前缀）。

### 二、AC-2｜否定判据可被按压

- `category_forms()` 的口径：含 `*` / `?`，或以 `.` 结尾。
- **按压（内存内字典，不落盘）**：注入 `read.*` ⇒ 命中 `["read.*"]`；
  注入 `literature.` ⇒ 命中 `["literature."]`。
- ⇒ 该断言**不是恒真**：一个恒返回空列表的实现会被按压判红。
- **如实登记一次自身返工**：首轮 `ruff format --check` 判红（三处可合并的 `assert` 消息）
  ⇒ 跑 `ruff format` 后复跑判据仍 `4 passed`。**未**加豁免、**未**改阈值。

### 二·补｜本轮 m0 首跑的两条红（一条自己的、一条环境的）

**首跑终态行**：`FAILED: 2 check(s): python/typecheck=1, python/tests=1`（代管后的树）。
两条红**性质不同**，分别处置：

1. **`python/typecheck` = 本 cycle 自己的缺陷（已修）**——
   `tests/application/preflight/test_read_grant_is_per_item.py:55: error: Returning Any from
   function declared to return "dict[str, Any]"  [no-any-return]`。
   修法：`policy_body()` 改为先 `.get("policy")` 再 `assert isinstance(body, dict)`
   （**加**了一道形状守卫，不是加豁免）。修后 `mypy` = `Success: no issues found in 1015
   source files`。**教训**：定向套件绿不等于全量绿——`mypy` 只在全量门里跑。
2. **`python/tests` = 环境 / 上游瞬时故障（判据与代码均未动）**——
   `tests/e2e/test_run_chain_retrieval_live.py::test_live_run_chain_retrieval_lands_a_real_identifier`
   判红，判词 `assert 'FAILED' == 'SUCCEEDED'`，run 的失败原因逐字为
   `eutils connection failure: [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation
   of protocol (_ssl.c:1010)`。
   **成对对照**：同一条用例在 **cycle 1 的 m0**（约 30 分钟前、**同一代码路径**）是
   **通过**的（`4471 passed, 19 skipped`，该行显示 `.`）；本机持有有效凭据 ⇒ 该用例
   **不 skip、真的出网**调 NCBI eutils。
   ⇒ 归类 **(ii) 环境专属 / 上游瞬时**，处置 = **按既有 flake 配方复跑**，
   **不动判据、不改 skip 条件、不放宽任何阈值**（`D-11` 明文不在本 GOAL 授权内）。

### 二·补2｜live 用例的三跑剖面与 (ii) 类登记（本轮新增观察项 `W-7`）

**三跑剖面（同一棵树，判据与代码在整个过程中一字未动）**：

| 跑 | 终态行 | `python/tests` 的判词 |
| --- | --- | --- |
| 第 1 跑 | `FAILED: 2 check(s): python/typecheck=1, python/tests=1` | `eutils connection failure: [SSL: UNEXPECTED_EOF_WHILE_READING]` |
| 第 2 跑 | `FAILED: 1 check(s): python/tests=1` | `run-chain capability step failed: previous step carries no 'ids' ids for run-chain tool literature_read` |
| 第 3 跑 | **`PASS: profile=m0; 23 deterministic checks`** | —（该用例通过） |

- **两次失败是不同签名**（上游 TLS 中断 / 真实 LLM 未按合约携带 `ids`）⇒ 不是同一缺陷复发，
  而是**外部依赖的非确定性**在负载下显形。
- **成对隔离跑（可复现命令）**：
  `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_run_chain_retrieval_live.py -q`
  ⇒ **`1 passed`（连跑两次：`14.81s` / `37.31s`）**，`egress guard: judged 3 connection
  attempt(s); blocked 0`。
- **干净基线对照（逐字节）**：`git diff 1e2af55 --stat -- tests/e2e packages adapters services
  examples` **为空** ⇒ 该用例及其整条链**与本 cycle 完全无关**；而 `1e2af55` 的 m0
  （cycle 1）中它是**通过**的。
- **三条判定条件逐条成立**（LOCAL_GATE_PROTOCOL.md 第 2 节 (ii)）：
  ① 「本机之外不出现」——同 tip 的 CI run `36095270268` 六 job 全绿（CI 无有效凭据 ⇒
  该用例**跳过**）；② 触发输入是**机器输入**（本机持有有效凭据 ⇒ 用例**不 skip、真出网**调
  NCBI eutils 与出厂 LLM 端点；真实 LLM 的输出形状非确定）；③ 判据描述的**行为是对的**
  （真实研究链必须落到真实 PMID）。
  ⇒ **分类 = (ii)**；动作 = 登记为环境项（附可复现命令 + 成对输出），**以 CI 在推送树上的
  终态为权威证书**。
- **登记为 `W-7`**（见 GOAL-016「承继的诚实边界」节）：默认门的结论在本机**取决于环境里
  有没有凭据** + 上游是否可用 —— 这是 `D-11` 证据面上的**第二个数据点**；
  **`D-11` 不在本 GOAL 授权内** ⇒ 只登记，**不得**改 skip 条件 / 判据 / 阈值。

### 三、AC-3｜证据面（15 条「该登记」）

- 从 `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表读出终态为「该登记」的行
  （跳过定义表的 `**该登记**` 行）⇒ **恰好 15 条**：
  `agent_run.read`、`budget.read`、`citation.inspect`、`citation.validate`、`claim.read`、
  `dataset.read`、`deliverable.read`、`experiment.read`、`experiment_plan.read`、
  `provenance.read`、`research_map.read`、`research_state.read`、`review.read`、`run.read`、
  `target.read`。
- 断言三件：**数量 == 15**（防「清单被删空仍绿」）、**全部为读类**（末段 ∈
  {`read`, `inspect`, `validate`}）、**没有一条出现在策略面的任何 `capability:` 里**
  ⇒ 「未取成类预放行」有可核对的证据。

### 四、AC-4｜读类放行逐条可枚举

- 对每条读类放行断言：存在**精确命名**它的放行规则，**且**不被任何前缀规则同时覆盖。
- **实测**载体：策略面的读类放行 = `workspace.read` / `artifact.read` / `evidence.read` /
  `literature.read`（逐条各一条规则）。

### 五、AC-5｜零策略面改动（逐文件取证）

- `git status --short examples/config/policy.yaml
  packages/application/preflight/policy_check.py` ⇒ 输出**行数 0**。
- `git diff --stat -- <这两个文件>` ⇒ **为空**。
- 本 cycle 的改动集只含：判据文件（新增）、本 PLAN / 本 RECHECK / MEM-135、
  `ALL_PLAN.md`、`.cursor/memory/INDEX.md`、GOAL-016。
- 判据只**读**这两个文件（按压用内存内字典）⇒ 「零策略面改动」不靠口头承诺。

### 六、质量门禁（本地）

- `ruff check` = `All checks passed!`；`ruff format --check` = `1 file already formatted`。
- 规模 / 命名门禁 + 定向回归：`tests/application/preflight/` +
  `tests/tooling/test_python_source_limits.py` +
  `tests/architecture/test_module_file_naming.py` ⇒ **`1083 passed`**；
  新文件 **179 行**（软阈值 300 行以内）。
- `egress guard` 判词 = `judged 0 connection attempt(s); blocked 0`（判据零出网）。
- m0 终态行：见下方「附：m0 终态行」。

## 附：m0 终态行

- **代管后的树**（`R-3` 的文件临时移出）**第 3 跑 = `PASS: profile=m0; 23 deterministic
  checks`**（退出码 0）；代管脚本逐字节复核**一致**：`size=69944` /
  `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`。
  日志：`scratch/goal016-c2c-m0-quarantined.log`；
  轮次输出：`scratch/goal016-c2c-m0-quarantine-run.txt`。
- **前两跑留档（用于 (ii) 类归因）**：
  `scratch/goal016-c2-m0-quarantined.log`（`FAILED: 2 check(s)`）与
  `scratch/goal016-c2b-m0-quarantined.log`（`FAILED: 1 check(s)`）。
- **as-is 的树**：唯一预置红 = `framework/validate_bundle`（`R-3`），与本题改动无关。
- **口径**：代管后的终态行**不得**读成「as-is 本机全绿」。
- **记录时序声明**：第 3 跑在**冻结树**上跑；本节与 GOAL-016 台账行的补写发生在该跑**之后**，
  属**只写记录**（不改判据 / 产品代码 / 门禁 / 依赖）。

## 结论

- **AC-1…AC-5 全部成立** ⇒ **GOAL-016 EC-02 = PASS**。
- **PASS_WITH_WARNINGS 的两条警告**：
  - **W-1｜本判据不判「该不该放行」**：它只判放行的**形态**。某个读能力是否**应该**放行
    仍是一次一次的判断（D-02(b) 的已知代价：每次新增读能力都要走一次授权）。
  - **W-2｜`R-3` 仍在**：本机 as-is m0 的唯一预置红仍来自仓库外 / gitignored 的并发写者文件
    （`framework/validate_bundle`），与本 cycle 无关；本 RECHECK **不**宣称本地全绿。
    `R-3` 的处置属 **D-10**（**需另行授权**），本 GOAL 只引用不改。
- **未改动**：策略面（`policy.yaml` / `_CAPABILITY_SCOPE`）、产品代码、门禁、阈值、
  依赖 pin、运行时默认值。
