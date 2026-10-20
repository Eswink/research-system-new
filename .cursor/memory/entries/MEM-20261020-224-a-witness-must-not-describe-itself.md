---
id: MEM-20261020-224
title: "顺序纪律失效在条文之外：给动作装一份可重算的见证，并让见证不落在它自己描述的受判面里"
status: ACTIVE
created_at: 2026-10-20
updated_at: 2026-10-20
scope: repository
confidence: 0.9
review_after: 2027-04-20
source_plans:
  - .cursor/plans/tasks/PLAN-20261020-090-goal-090-tool-dimension-and-m0-witness.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261020-090-goal-090-tool-dimension-and-m0-witness.md
supersedes: []
tags: [m0, gate-ordering, witness, self-reference, vacuous-truth, goal-090, w-6, evidence-coverage]
---

## 做了什么

两条同源的缺陷被同一种手法修掉：

1. **`W-6`（GOAL-089 实测）**：`producer_trust_label` 只看「产出方声明了 `run_chain` +
   能力面落在带 `network_domains` 的 provider 上」，**不问产出方本次是否真的执行过调用**
   ⇒ 一个只为把 provider 排除出**会话工具面**而声明 `run_chain` 的会话格（其产出是
   **模型写的字**）被推成 `TrustLabel.RETRIEVED`。下游检索格的
   `minimum_retrieved_sources` 因此可被一条**与被测能力无关的跨相边**单独满足。
   修法：给 `EVIDENCE_COVERAGE` 加第三个**正交**维度 `minimum_tool_evidences`，只数
   **带 `tool_refs`** 的证据（工具证据登记必带 provider/tool，跨相输入的 `tool_refs` 为空）
   ⇒ 它问的是**调用事实**，不能被声明事实间接满足。

2. **m0 顺序纪律（GOAL-089 收口多跑三次全量 m0，约 48 分钟）**：m0 的证据只在它实际运行
   的那棵树上成立；`docs/architecture/LOCAL_GATE_PROTOCOL.md` 写了顺序，但**只靠人记住**。
   修法：`tools/run_m0_with_witness.py` 跑门前算受判面指纹（HEAD + 脏文件路径/状态/`sha256`），
   跑后写**树内**见证；判据重算当前树指纹并比对。

## 为什么这样做

**这类纪律的失效发生在条文之外**：写「先跑记录面判据再跑全量门」并不能阻止「跑完门又提交了
一条记录」——后者是**动作的次序问题**，不是文本问题。所以正确形态不是再加一句规范，而是让
**动作本身留下可重算的见证**，然后让判据去问「当前状态与见证一致吗」。

**两处缺陷其实是同一个错误**：都把「声明/曾经发生」当成「此刻成立」。
`producer_trust_label` 把「声明了 run_chain」当成「检索发生过」；m0 的终态行把「曾经跑过」
当成「覆盖现在这棵树」。

**第一条判据必须先证明缺口存在**：如果只写「加了工具维就判负」，读者无从判断那条缝是否真实
（可能永远没人能走进去）。所以先写一条断言「只有跨相来源时前两维**确实通过**」，把 `W-6`
的形态钉住，再加第三条维度证明它被挡住。

## 怎么做与复现

1. **见证工具的自我指涉陷阱**（本轮实测、判据抓到）：初版把 `.cursor/` 整个算进受判面，
   而见证文件落在 `.cursor/plans/goals/evidence/` ⇒ **写见证这个动作改变了它所描述的树**
   ⇒ `--skip-run` 写完立刻判红。修法 = `SELF_REFERENTIAL` 白名单，**被描述者不参与描述**。
2. **三态语义必须分得开**（否则「没跑过」会被读成「覆盖当前树」）：
   见证不存在 ⇒ 判红点名入口；指纹不等 ⇒ 判红并**逐条点名**差在哪个文件（路径 + 状态 +
   digest）；指纹相等 ⇒ 判过，且见证为红时**照实**报告（覆盖关系成立 ≠ 门一定是绿的）。
3. **「跑过」≠「跑完了」**：`--skip-run` 写出的见证没有终态行，判据**必须**判红。
   不要为了让调试路径变绿而放宽这一条 —— 它正是这个区分本身。
4. 复跑：
   ```bash
   uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
   uv run --frozen --no-sync python -B -m pytest tests/tooling/test_m0_witness_matches_the_tree.py -q
   ```
5. 按压（改一个受判字节 ⇒ 判红并点名两版 `sha256`；逐字节复原后复绿）。

## 适用边界

- **工具维只挡住声明了它的合约**。出厂检索格已声明（`research_question_retrieval` 1.1.0），
  但别的合约若只声明性质维，同一形态仍敞开。**通用修复**需要改 `TrustLabel` 语义
  （撞 GOAL-081 的受判面，属需用户拍板项）—— 不要把本轮的「加一维直接判」当成通用修复。
- **见证只覆盖本地树**：CI 覆盖推送后的树，两者对象不同；见证不替代 CI。
- **见证不校验 23 项都执行完**：那是终态行的职责，见证只抄录它。
- **`--skip-run` 生成的不是正式见证**（无终态行，判据会红）。它是调试路径。
- 不得据此宣称项目安全（`R-M1` 未收口）。

## 来源

- `PLAN-20261020-090` / `RECHECK-20261020-090`（本轮两向按压与逐字节复原读数）
- `GOAL-20261019-089` 的 `W-6` 残余条目（缺口的出处）
- `docs/architecture/LOCAL_GATE_PROTOCOL.md`「记录面覆盖」一节（顺序条款）
- 同族记忆：[[record-face-is-gated-run-the-gate-last]]（记录面受门覆盖：门必须最后跑）、
  [[governance-done-plan-requirements]]（DONE 的必需事实）、
  [[judgment-file-defects-only-full-m0-catches]]（新判据自身的缺陷只有全量门抓到）
