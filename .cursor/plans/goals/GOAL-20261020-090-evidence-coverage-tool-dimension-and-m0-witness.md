---
id: GOAL-20261020-090
slug: evidence-coverage-tool-dimension-and-m0-witness
title: 覆盖门的工具维（堵 GOAL-089 W-6）+ m0 见证把顺序纪律变成机器事实
status: ACHIEVED
created_at: 2026-10-20
updated_at: 2026-10-20
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    用户 2026-10-20 的指令逐字：「走你推荐的吧，然后给出能自我反复迭代的提示词。」
    「你推荐的」= 我在上一轮分析里给出的组合：**C 作为本轮最小收口**（不动 `TrustLabel`、
    不动 `count_retrieved_sources` 口径，只在合约面加一条更直接的要求）+ **A 作为下一轮的
    通用修复**（给 `TrustLabel` 加取值 —— 那撞 GOAL-081 受判面，属用户此前明写要「停下
    登记」的那类决定，故本轮**不**做）。同一条消息里还包含「要不要把 m0 顺序纪律做成判据」
    的授权（我的问句 + 用户的「走你推荐的吧」覆盖了该问句，且本轮交付即该判据）。
    授权要点：(a) 全部决策权下放，只有「改产品边界 / 放宽任何判据 / 动冻结面 / 新增
    `TrustLabel` 取值」才停下登记。(b) 每一步必须有**机械判据**。(c) 每轮必须让科研能力
    阶梯前进（`tests/tooling/test_mainline_research_ladder_advances.py` 强制）。
    (d) **不做**：改 `TrustLabel` 语义（留作 A，下一轮）/ `count_retrieved_sources` 口径 /
    读面认证 / `R-M1` / 宣称项目安全 / 宣称投递语义为「恰好一次」（**明确否认**）。
    (e) push-to-main-for-CI（只推 `main`、不 force、不重写历史）。
objective: >
    堵住 GOAL-089 实测登记的 `W-6`：跨相输入的 `trust_label` 由**产出方**的声明推导
    （`producer_trust_label` 只看「声明了 `run_chain` + 能力面落在带 `network_domains` 的
    provider 上」），于是**只为把 provider 排除出会话工具面**而声明 `run_chain` 的会话格
    （其产出是模型写的字）会被推成 `RETRIEVED` ⇒ 下游检索格的
    `minimum_retrieved_sources` **可被一条与被测能力无关的跨相边单独满足**。本轮的形状是
    给 `EVIDENCE_COVERAGE` 加**第三个正交维度** `minimum_tool_evidences`（只数**带
    `tool_refs`** 的证据 ⇒ 问的是**调用事实**，不能被声明事实间接满足），并在出厂检索格
    上声明它。同轮把 GOAL-089 收口时「多跑三次全量 m0」暴露出的**顺序纪律**（散文没咬住）
    变成机器事实：`tools/run_m0_with_witness.py` 跑完门后写**树内见证**（HEAD + 受判面
    脏文件 + 各自 `sha256`），判据重算当前树指纹与见证比对。
exit_criteria:
  - id: EC-01
    criterion: >-
      **工具维落地**：`AcceptanceCriterion.minimum_tool_evidences`（可选，缺省 `None` ⇒
      既有行为**逐字不变**，负值构造期拒绝）；`CriterionInputs.tool_evidence_count`；
      求值器按**三维正交**判定（计数维 / 性质维 / 工具维各缺即判负，判词**点名缺哪一维**）；
      加载器解析；`schemas/task-contract.schema.json` 登记；计数函数
      `count_tool_evidences`（判据 = `Evidence.tool_refs` 非空）接进验收门。
      判据：`tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_evidence_coverage_tool_dimension.py -q` ⇒ 10 passed。
    status: PASS
  - id: EC-02
    criterion: >-
      **两向按压**（在**真文件**上，不是夹具）：(a) 把出厂合约的
      `minimum_tool_evidences: 1` 摘掉 ⇒ 判据判红并点名「检索格没有声明工具维」；
      (b) 把 `count_tool_evidences` 改成恒返回 `0` ⇒ 判据判红（`assert 0 == 1`）。
      两向都用 raw `sha256` **逐字节复原**并复绿。
    verify: >-
      按压记录在 `RECHECK-20261020-090` 的「按压」节；复原后 `10 passed`。
    status: PASS
  - id: EC-03
    criterion: >-
      **出厂检索格真的声明了工具维**：`examples/contracts/task_contracts.yaml` 的
      `research_question_retrieval` 升到 `1.1.0` 并声明 `minimum_tool_evidences: 1`；
      判据读**产品数据文件**（不是夹具）断言该声明在场 ⇒ 被改回两维会立刻判红
      （受判对象必须存在：空真的绿不算收口）。
    verify: >-
      `test_the_shipped_retrieval_contract_declares_the_dimension` 在 EC-02 的按压 (a) 下判红。
    status: PASS
  - id: EC-04
    criterion: >-
      **m0 见证把顺序纪律变成机器事实**：`tools/run_m0_with_witness.py` 跑门前算受判面指纹
      （HEAD + 脏文件路径/状态/`sha256`）、跑后写
      `.cursor/plans/goals/evidence/M0-WITNESS.json`（**树内**、可复核、红绿都照记）；
      `tests/tooling/test_m0_witness_matches_the_tree.py` 重算当前树指纹比对。
      **三态语义必须分得开**：(i) 见证不存在 ⇒ 判红并点名该跑哪个入口；
      (ii) 指纹不等 ⇒ 判红并**逐条点名**差在哪个文件（路径 + 状态 + digest）；
      (iii) 指纹相等 ⇒ 判过；见证为红时**照实**报告（覆盖关系成立 ≠ 门一定是绿的）。
      **自我指涉边界**：见证文件本身**不在**受判面（否则写见证这个动作会让它自我失效 ——
      本轮实测到，见「迭代日志」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_m0_witness_matches_the_tree.py -q`；按压：改
      `schemas/task-contract.schema.json` 一个字节 ⇒ 判红并点名该文件的两版 `sha256`。
    status: PASS
  - id: EC-05
    criterion: >-
      **收口**：记录写完（GOAL / PLAN / RECHECK / 阶梯 / 程序表 / 进展记录）→ 记录面判据
      → **最后**跑全量 m0 并由见证入口写正式见证 → 之后**不再改树** → 提交推送 →
      CI 到终态（逐提交台账，`cancelled` / 零 run 如实登记）+ 阶梯「复检」或「证据」域
      收录本 GOAL + 凭据审计四面 `offenders=0` + 残余与未覆盖范围逐条。
    verify: >-
      见证的 `terminal_line` = `PASS: profile=m0; 23 deterministic checks`；
      `test_m0_witness_matches_the_tree.py` 全绿（指纹相等）；
      治理 `validate.py` = `Cursor 治理验证通过`。
    status: PASS
budget:
  max_cycles: 8
  per_cycle_minutes: 90
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator / 门禁 / 快照 / 测试断言使其通过
    - 放宽任何既有判据的断言、词表、扫描面或阈值
    - 把受判面写成交集、并集掩蔽或写法清单
    - 收窄既有受判面而不逐条申报（逐条枚举 + `numstat` 删除行读数 + 谓词比对）
    - >-
      **改 `TrustLabel` 的取值或语义**：那是 A（下一轮的通用修复），撞
      `test_cross_phase_inputs.py` 的受判面与 GOAL-081 的判据；本轮只加**正交的新维度**，
      不动既有标签
    - >-
      **改 `count_retrieved_sources` 的口径**：B 方案被否（会挡掉「上游检索给下游用」的
      正当形态）；性质维必须逐字保持不变
    - >-
      **让工具维退化成性质维的翻版**：判据必须是 `tool_refs` 非空这条**调用事实**；
      若改成「按来源计数」或「按 label 判」，本轮就白做
    - >-
      **把见证放进 `scratch/`**：那在 gitignore 里 ⇒ 不算树内证据（判据有专门一条钉它）
    - >-
      **把见证文件自身算进受判面**：写见证会改变它所描述的树 ⇒ 自我失效（本轮实测）
    - 为让判据变绿而**改出厂目录**制造差异
    - 把 `RESEARCHOS_AGENT_RUNTIME` 或 `RESEARCHOS_LIVE_E2E` 写进 `.env`
    - >-
      把真实凭据（`sk-…` / `cpk-…` 等）写进**任何 tracked 文件**；
      判据自证 = `tools/credential_audit.py` 四面 `offenders=0`
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 新增任何依赖
    - 宣称项目安全（`R-M1` 未收口）；宣称投递语义为「恰好一次」（**明确否认**）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 `fix_policy` 上限
  - >-
    **真实凭据出现在 tracked 文件里**（含记录）—— **立即 BLOCKED** 并清理
  - >-
    **需要新增 `TrustLabel` 取值或改其语义** —— 停下登记（那是 A，需用户拍板）
child_plans:
  - .cursor/plans/tasks/PLAN-20261020-090-goal-090-tool-dimension-and-m0-witness.md
latest_recheck: .cursor/plans/rechecks/RECHECK-20261020-090-goal-090-tool-dimension-and-m0-witness.md
memory_entries: []
---

## 目标与退出标准

**一句话**：把 GOAL-089 实测到的两处「散文咬不住」的缺口变成机器事实 ——
覆盖门的性质维可被跨相边间接满足（`W-6`），以及 m0 的证据与它实际覆盖的那棵树可脱节。

**为什么这两件事在同一轮**：它们同源。`W-6` 是**同一条**「声明事实被当成调用事实」的
形态（`producer_trust_label` 不问产出方本次是否真的执行过调用）；而 GOAL-089 收口时
多跑三次 m0，也是因为「门跑过了」被当成「覆盖当前树」——同样是**把过程事实当成结论**。
两处都靠「问一个**只能由真实发生**来回答的问题」修掉：前者问 `tool_refs` 是否非空，
后者问当前树的指纹是否与见证相等。

## 本 GOAL 的射程边界（先写清楚，避免越判）

- **只新增**：`EVIDENCE_COVERAGE` 的第三个可选维度、一个纯计数函数、一条出货合约声明、
  一个见证工具与一份见证文件；
- **不改**：`TrustLabel` 取值与语义、`producer_trust_label` 的推导、`count_retrieved_sources`
  的口径、任何既有合约的既有维度、任何 HTTP 面；
- **不静默回落**：声明了新维而计数未知 ⇒ fail-closed 点名；见证不存在 ⇒ 判红点名入口；
- **无 live run**：本 GOAL 受判面不触网，不声称任何模型行为（如实登记）。

## 循环入口协议

按 `.cursor/plans/goals/README.md` 的 7 步判定续点（以「文件 + 工作树 + 远端实况」为准，
**禁止凭记忆假设**）。每步完成后立即回写本文件。

## 单 cycle SOP

沿用宪章与既有 GOAL 的既定纪律（记录 → 记录面判据 → 全量 m0 → 治理 → 显式路径提交 →
批量推送 → CI 到终态 → 纠错 → 回写）。**本 GOAL 特有**：

- **先钉缺口存在，再钉修补有效**：若只写「加了工具维就判负」，读者无从判断那个缝是否
  真实 —— 故第一条判据先证明「只有跨相来源时前两维确实通过」（`W-6` 的形态）。
- **钉住判据赖以成立的结构事实**：`tool_refs` 是两类证据的判别依据；若将来跨相输入开始
  带 `tool_refs`，该判据判红提醒改写依据，而不是让工具维静默退化。
- **两向按压都在真文件上**，且用 raw `sha256` 逐字节复原（`git diff` 不足以当逐字节证据）。
- **顺序纪律当受判对象走**：记录写完 → 记录面判据 → **最后**跑 m0 写见证 → 不再改树。

## CI 失败分类与纠错

沿用既有四类（lint/typecheck / 产品测试失败 / flake-env / 基础设施）。基础设施红须三条取证；
时序型 flake 按既有纪律 `rerun-failed-jobs`，**不改阈值**，首轮红如实登记。
**零 run ≠ cancelled**，如实登记 + `covered_by`。

## 终止与收口

- **ACHIEVED**：EC-01…EC-05 全 PASS + 独立 RECHECK + 本文件收口（`latest_recheck` 为
  **仓库相对路径**）+ CI 台账到终态 + 残余与未覆盖范围逐条 + **阶梯记账成立**（宪章
  `依据 GOAL` 与 `进展记录` 各收录本 GOAL）+ 正式见证的 `terminal_line` 全绿。
- **BLOCKED**：命中任一 `escalation_triggers` / 同一失败签名超过 `fix_policy` 上限 /
  `max_cycles` 触顶 / 连续 `no_progress_stop_cycles` 轮未推进任何 EC。
- **ABORTED**：用户撤销。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PLAN-20261020-090 | `2b37f8a8`… | 工具维判据 10 passed；两向按压各判红并逐字节复原；受影响套件 1270 passed / 72 skipped | 见「CI 台账」 | 2（见下） | EC-01…EC-04 达成 | 收口（EC-05） |

**本轮修掉的两处自己造成的缺陷**（都是判据先抓到，不是事后才发现）：

1. **见证自我指涉（位置）**：初版把 `.cursor/` 整个算进受判面，而见证文件本身落在
   `.cursor/plans/goals/evidence/` ⇒ 写见证这个动作改变了它所描述的树 ⇒ `--skip-run`
   写完立刻判红。修法 = `SELF_REFERENTIAL` 白名单（被描述者不参与描述），与宪章
   「自我指涉边界在收口 tip 那一行闭合」同一手法。
2. **见证自我指涉（时刻）**：更根本的一处 —— 见证在门**跑完之后**才写，而判据
   **本身就在门里**跑 ⇒「本次运行里见证尚不存在」是**结构必然而非缺陷**；把它判红会让
   「跑一次门」永远无法自证覆盖（判据成了自己的反例）。修法 = **第三态**：见证入口在
   `subprocess.run` 之前写 `M0-WITNESS.in-progress`、`finally` 里删；判据见标记在场 ⇒
   `pytest.skip` 并**点名理由**（可见的跳过，不是静默通过）。单列判据
   `test_the_in_progress_state_is_a_real_third_state_not_a_silent_pass` 钉住该语义
   （含「标记必须在 `finally` 删除」「两边路径逐字一致」两条反证）。
3. **`--skip-run` 写出的见证没有终态行**：`test_the_witness_records_a_terminal_line`
   判红并点名「runner 没有跑到终态 ⇒ 这次运行不能作为覆盖证据」。这条红是**正确**
   的 —— 它正是「跑过 ≠ 跑完了」的机械表达，故保留该行为，不用 `--skip-run` 冒充正式见证。
4. **见证指纹绑错了对象（两次 CI 判红才定下口径）**：

   **第一次**（`effbe9e5`）：指纹只记 `git status` 的**脏文件清单**。本地有 24 个未提交
   改动、CI 是干净检出 ⇒ 同一提交两处指纹永远不等。修法 = 改按文件内容算。

   **第二次**（`67ea1e87`）：改成「工作树字节的 sha256」后 CI **仍然红**，差 **489 个文件**
   且**内容相同、hash 全不同** —— 根因是本仓 `.gitattributes` 为 `* text=auto eol=lf`：
   Windows 检出 CRLF、Linux 检出 LF。**修法 = `git hash-object`**（git **归一化后**的
   blob 哈希），它与平台行尾和工作树是否干净都无关。旁证：把 4526 个受判面文件的
   blob 哈希与 `git ls-tree HEAD` 比对，**只有**我当时正在编辑的那 1 个文件不一致。

   **两次的共同教训**：判据的正确性必须在**另一种工作树形态**下也成立（干净检出 /
   另一平台），否则「本地绿」只是本地那一棵树的绿。第二版我还加了一条断言禁止
   `read_bytes()` 出现在指纹函数里 —— 因为那个写法**看起来**完全合理。
   本地跑门时工作树有 24 个未提交改动，而 CI 是**干净检出**（0 个脏文件）⇒ 同一个提交
   在两处的指纹**永远不相等** ⇒ 判据在 CI 上恒红（`effbe9e5` 的 M0 两个 quality job
   就是这样红的；本地 23/23 全绿却没能预测到它）。修法 = 指纹改按**文件内容**算
   （`git ls-files` 的受判面路径 × 工作树字节的 sha256）⇒ 干净检出与「已提交 + 工作树同
   内容」给出**同一个**指纹；只有**内容**变了才变。旁证：把同一文件按相同字节重写
   （改 mtime 不改内容）⇒ 指纹不变。并单列判据
   `test_the_fingerprint_does_not_depend_on_git_dirtiness` 钉住该语义（结构上禁止
   `dirty` / `status` 字段回到指纹里）。
5. **`main` 68 行撞规模门**（工具脚本过四道门 ⇒ 50 行上限）：拆成 `_run_gate` /
   `_record` / `main` 三个，行为逐字不变。

## 真跑读数

**无真实 LLM 运行**：本轮的受判面是**覆盖门的求值逻辑**与**本地门的见证机制**，
两者都不触网、不需要模型。`count_tool_evidences` 是纯函数（只读 `Evidence.tool_refs`）。
如实登记：**本轮没有任何 live run**，因此不声称任何模型行为。

## 残余与未覆盖范围

- **`A` 未做（明写）**：`producer_trust_label` 仍会把「声明了 `run_chain` 但本次未执行
  调用」的会话格推成 `RETRIEVED`。本轮的工具维**只挡住检索格**（出厂合约声明了它），
  不是**通用修复** —— 别的合约若只声明性质维，同一形态仍敞开。通用修复需要改
  `TrustLabel` 语义（撞 GOAL-081 受判面），属需用户拍板项。
- **见证只覆盖本地树**：CI 覆盖推送后的树，两者对象不同；见证不替代 CI。
- **见证不校验 23 项都执行完**：那是终态行的职责，见证只抄录它。
- **`W-6` 的根因未除**：本轮是「加一维直接判」，不是「修掉那条推导」。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-20 | **ACTIVE** | **建档**：承 GOAL-089 的 `W-6` 残余（其 `escalation_triggers` 明写「改 `TrustLabel` ⇒ 停下登记」）与用户「走你推荐的吧」的授权，按上一轮分析里的「C 先收口、A 下一轮」落地。 |
| 2026-10-20 | **ACHIEVED** | EC-01…EC-05 全达成。工具维三维正交且两向按压判红并逐字节复原；出厂检索格声明并升版 1.1.0；m0 见证三态语义成立、自我指涉边界经实测修掉。如实登记 `A` 未做、见证边界三条。 |
