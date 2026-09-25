---
id: RECHECK-20260925-175
plan_id: PLAN-20260925-174
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-016-cycle4 + 只读 git 枚举（判据内建双形态计数器）
baseline_ref: cycle 3 推送 tip `8814b49`
checked_head: 当前树（5 个 docs 文件 + 1 个新判据；**无产品代码改动**）
---

# RECHECK-20260925-175 — D-07(b) + D-08(b) + D-09(a) 文档固化（GOAL-016 cycle 4）

## 检查范围

① 新判据是否存在、是否实跑、是否**可被按压**（AC-1）；② `ADR-0031` 的 `Status` 是否
**逐字未动**且既有「待拍板」判据未被破坏（AC-2）；③ 非 ASCII 枚举陷阱是否被钉进判据
（AC-3）；④ diff 是否**零越界**（AC-4）；⑤ doc 一致性门（AC-5）；⑥ m0 与记录（AC-6）；
⑦ 并发写者文件未被卷入。

## 检查结果

### 一、AC-1｜判据「实跑 + 可按压」

- **文件**：`tests/tooling/test_landed_decisions_are_citable.py`（151 行，6 条用例）。
- **实跑**：`uv run --frozen --no-sync python -B -m pytest
  tests/tooling/test_landed_decisions_are_citable.py -q` ⇒ **`6 passed in 0.22s`**；
  `egress guard: judged 0 connection attempt(s); blocked 0`（零出网）。
- **判据断言的事实**（逐条）：
  1. **非 ASCII 现实 ↔ 清单双向**：清单里没有的（现实有、文档没写）与文档写了但现实没有的
     都算失败；
  2. **枚举陷阱**：朴素 `git ls-files` 的非 ASCII 数为 **0** 且 `\3` 转义形态**确实存在**
     （证明「数出 0」是转义所致，而非真的没有），同时 `-c core.quotepath=false` 数为 **30**；
  3. **`ADR-0032` 结构**：`Status: Accepted`、含 §13 引文、含「不重命名」口径、
     列入 `docs/INDEX.md`；
  4. **按压态**：从清单里删掉一条真实路径 ⇒ 判据**报出**；往现实里塞一条
     `docs/新路径.md` ⇒ 判据**报出**（这条用内存比对，不落盘）；
  5. **`ADR-0031` 仍 `Proposed`**：第 3 行 `Status: Proposed` 且全文**无** `Status: Accepted`，
     并**已含** `否证条件` 节；
  6. **`MODEL_COMPATIBILITY.md`**：含「维持派生视图」「必须先出 ADR」「Canonical State」「回滚」。
- **先红后绿的两处**（**修的是文档措辞，不是判据**）：
  - `UNRENAMED_CLAUSE` 在 `ADR-0032` 里被**断行**成两行 ⇒ 连续子串匹配不到
    ⇒ 把 §13 引文收进**同一行**；
  - `PRECONDITION_CLAUSE` 期望 `必须先出 ADR`，文档原文是「必须先出**一份** ADR」
    ⇒ 改文档为 `**必须先出 ADR**（且该 ADR 至少写清三件事）`。
  **判据侧一个字未放宽**（未加 `in`、未去空白、未降为前缀匹配）。

### 二、AC-2｜`ADR-0031` 未被越权拍板

- `Status:` 行（第 3 行）仍为 **`Proposed`**；`git diff` 的 `docs/adr/ADR-0031-*.md`
  补丁**不含**该行。
- `grep -c "Status: Accepted"` 在 `ADR-0031` 上 = **0**（判据里也作为硬断言）。
- **既有判据同轮全绿**：`pytest tests/tooling/test_toolpack_capability_policy_pending.py
  tests/architecture/python/test_real_deliverable_contract_same_source.py -q`
  ⇒ **`18 passed`**（「待拍板」「已定向」「可分别决定」的口径未被本次补写破坏）。

### 三、AC-3｜枚举陷阱被钉进判据（假绿口子已封）

- **朴素枚举**：`git ls-files` ⇒ 非 ASCII **0** 条（`core.quotepath` 默认把非 ASCII
  转义成 `\NNN`）⇒ 若判据只用朴素枚举，就会**永远绿**（清单恒等于空集）。
- **正确枚举**：`git -c core.quotepath=false ls-files` ⇒ 3389 条中 **30** 条含非 ASCII。
- 判据**同时**断言两个数 ⇒ 「转义导致的 0」本身成为判据的一部分（**反假绿**）。
- 该陷阱已同步写进 `ADR-0032` 的 Evidence 一节（**枚举命令必须带
  `-c core.quotepath=false`**）。

### 四、AC-4｜diff **零越界**

`git status --porcelain` 逐条核对，本 cycle 的改动集**恰好**是：

| 文件 | 性质 |
| --- | --- |
| `docs/adr/ADR-0031-toolpack-capability-policy.md` | 补「否证条件」节 |
| `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md` | **新建** |
| `docs/architecture/MODEL_COMPATIBILITY.md` | 增 §9（D-08(b) 决定） |
| `docs/architecture/DOMAIN_MODEL.md` | §5 加指针段 |
| `docs/INDEX.md` | 登记 `ADR-0032` + 给 `ADR-0031` 行加注 |
| `tests/tooling/test_landed_decisions_are_citable.py` | **新建**判据 |

**不含**：`AGENTS.md`、`examples/config/policy.yaml`、`packages/application/preflight/`、
任何域 / 服务 / 适配器代码、任何门禁脚本、任何 rename、任何 `Status` 改动。

### 五、AC-5｜doc 一致性门（**先红后修，未动门禁**）

- **首跑**：`DOCS-CHECK FAILED: 2 finding(s)` —— `ADR-0032` 里两条 `[backtick-ref]` 指向
  不存在的路径：
  - `adapters/postgres/migrations/010…012`（用省略号写的**缩写**，非真实路径）
    ⇒ 改为逐条写出真实文件名（`010_GPU显存计量宽度v1.sql` 等三条）；
  - `tests/tooling/test_legacy_non_ascii_paths_are_exempt.py`（**我先前臆想的文件名**）
    ⇒ 改为真实判据 `tests/tooling/test_landed_decisions_are_citable.py`。
- **复跑**：`DOCS-CHECK PASS: 6 deterministic checks`。
- **门禁侧零改动**：`tools/docs_consistency_check.py` 不在 diff 内；**未**加任何忽略名单。

### 六、AC-6｜m0 与记录

- 见「附：m0 终态行」（树与跑法分开写清）。
- 本 PLAN / 本 RECHECK / `MEM-20260925-137` 与 GOAL-016 的回写同轮完成。

### 七、并发写者文件未被卷入

- 工作树里三处**他人**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
  `packages/domain/model_drift.py`、`services/api/dto/models.py`）**不在**本 cycle 的改动集里
  ⇒ **未**被 `git add`、**未**被提交（提交前三张名单逐条比对）。

## 附：m0 终态行

- **代管后的树**（`R-3` 的文件 `scratch/self-governance-bootstrap-prompt.md` 临时移出）：
  **`PASS: profile=m0; 23 deterministic checks`**（退出码 **0**，**首次即通过**；
  `PASS [` 行数 = **24** = 23 项 + 计数之外的 `release-assets-immutable`，
  与 `LOCAL_GATE_POLICY` 的既有口径一致；`FAIL` 行数 = **0**）。
  逐字节复核**一致**：`size=69944` / `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`。
  日志：`scratch/goal016-c4-m0-quarantined.log`；
  轮次输出：`scratch/goal016-c4-m0-quarantine-run.txt`。
- **as-is 的树**：唯一预置红 = `framework/validate_bundle`（`R-3`），与本 cycle 改动无关
  （未在本 cycle 重跑 as-is；上一轮实测为 **22/23**，本轮改动**不触碰**该红项的成因）。
- **口径**：代管后的终态行**不得**读成「as-is 本机全绿」。
- **记录时序声明**：本轮 m0 在**冻结树**上跑，且**已包含本 cycle 的全部产物**
  （5 个 `docs` 文件 + 判据 + PLAN / RECHECK / MEM / `ALL_PLAN` / `INDEX` / GOAL-016 的
  EC-04 段）。该跑**之后**的写入**只有两处**，都是**关于 CI 的台账回填**
  （GOAL-016 的 cycle 3 台账行 + 「待回填」段）——**不改**判据 / 产品代码 / 门禁 /
  阈值 / 依赖 / 文档措辞；回填后**重跑治理 `validate.py` = `Cursor 治理验证通过`**
  （见下）。

## 附：治理门（回填后复跑）

- `uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
  ⇒ **`Cursor 治理验证通过`**（`ALL_PLAN` / Task Plan / Recheck / Memory 交叉引用一致；
  GOAL 循环记录结构合规；未发现明显凭据材料）。
- **首跑曾红**（如实登记）：`工程记忆缺少章节 ## 为什么这样做 / ## 怎么做与复现 /
  ## 适用边界 / ## 来源: MEM-20260925-137` ⇒ 按既有章节集重写该 MEM
  （**未**改校验器、**未**加豁免）⇒ 复跑通过。

## 结论

- **AC-1…AC-6 全部成立** ⇒ **GOAL-016 EC-04 = PASS**。
- **PASS_WITH_WARNINGS 的三条警告**：
  - **W-1｜D-07 的 `Proposed` 仍是未拍板项**：本轮补的是**「否证条件」**（何时该改判），
    **不是**拍板。`ADR-0031` 仍 `Proposed`；谁要它变成 `Accepted` 谁先给出否证条件
    所要求的证据。**不得**把本轮读成「`tool_pack.*` 已获准」。
  - **W-2｜D-09 的豁免只管既有 30 条**：新建非 ASCII 路径**仍判红**（规则与判据都未动）；
    且本轮**未**验证「新路径确实被拦」——该验证属既有的命名门禁，**不在**本 EC 范围。
  - **W-3｜`R-3` 仍在**：as-is 本机 m0 的唯一预置红仍来自仓库外 / gitignored 的并发写者文件
    （`framework/validate_bundle`）；处置属 **D-10**（**需另行授权**），本 GOAL 只引用不改。
- **未改动**：产品代码、策略面、门禁、阈值、判据口径、运行时默认值、任何 `Status`、任何路径名。
