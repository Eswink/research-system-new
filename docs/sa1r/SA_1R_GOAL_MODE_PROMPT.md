# SA-1R — Research OS M0–M11 Independent Full-System Re-audit（Goal Mode 适配版）

执行 Research OS 的 **SA-1R — Independent Full-System Re-audit**，并严格适配当前项目 Goal 模式。

## 0. Goal 模式接入（优先于一切）

本任务是长期审计目标，必须挂载到当前 session 的 Goal 机制上运行，不是一次性问答。

1. **启动时先调用 `get_goal`**：
   - 若已存在 active Goal 且其 objective 与本审计一致：**复用**，绝不创建第二个 Goal，绝不重写 objective。
   - 若无 active Goal：调用 `create_goal` 创建一个且唯一一个 Goal，objective 写入如下最终完成条件（可精简）：
     `SA-1R：独立复核 docs/audits/SYSTEM_AUDIT_M0_M11.md 的 M0–M11/IG-1 全系统审计；所有 BLOCKER 独立重验并关闭、无新未关闭 BLOCKER、SA-1 regression 对原缺陷有判别力、frozen Contracts 未破坏、security/reliability/research-truth/provenance 边界成立、IG-1 真实链通过、m0 质量门满足；输出 SA-1R 与 M12 Entry 判定；停止在 M12 Entry Gate，不开始 M12。`
   - `max_goal_rounds` 由审计工作量决定（建议 40–60），不得小到迫使提前草率完成。
2. **每一轮开始时先调用 `get_goal`**：读取 `revision` / `phase` / objective，确认没有新的用户变更，再从当前 workspace、最近测试结果、Git 状态和已确认 finding 继续。
3. **不要重新定义 Goal**：除非用户显式改变任务范围，否则禁止 `update_goal(action=edit)` 修改 objective 或 round cap。
4. **Goal 只在全部 Exit Criteria 实际满足后才完成**：调用 `update_goal(action=complete)` 并输出 Final Evidence。
5. **只有以下情况才调用 `update_goal(action=blocked)`** 并写明 `blocked_reason`：
   - 必须改变冻结核心架构；
   - destructive / irreversible operation；
   - 重大 security boundary change；
   - license / compliance issue；
   - 仓库事实无法解决的重大路线分歧。

   Test failure、复杂度、剩余工作都不是 blocker；除此之外一律继续执行，不报告 blocked。
6. pause / resume 由用户控制；新一轮 Round 不改变审计范围，不从头重读本 Prompt。

---

## Scope

- 遵循当前仓库已经生效的：`AGENTS.md`、Cursor Rules / Skills、工程知识库、`docs/roadmap/MILESTONES.md`、Completion Records、ADR、Architecture、DOC-R1、IG-1、SA-1 Audit Record、当前实际代码和测试。
- 不要复述用户要求；不要输出"我将…… / 让我…… / 接下来…… / Let me... / I'll first..."式执行叙事；不要先写长篇审计计划；不要先建立覆盖所有章节的大型 todo；不要 breadth-first 扫描整个仓库。
- 每个 action 至少完成一件事：验证一个已有 finding / frozen Contract；构造一个可失败反例；定位一个 production path；排除一个具体 bypass；修复一个已复现根因；获得一个可重复验证证据；关闭一个 Exit Criterion。
- 如果一个动作不能减少当前审计不确定性，就不要做。

事实优先级：

1. 当前 production code / schema / runtime wiring；
2. 已冻结的 M0–M11 / IG-1 Contracts 与正式 DoD；
3. 可重复执行结果、Fault Injection、deterministic validation；
4. Git diff / history；
5. SA-1 Finding / Regression evidence；
6. ADR / Architecture / Completion Records；
7. 开发阶段总结与历史 PASS。

SA-1 的 Finding severity、Root Cause、FIXED、Regression、BLOCKER closure、PASS、M12 READY 都只是待验证 claim，不是事实。

---

## First Action

第一次 repository action 只做一件事：读取正式 **SA-1 Audit Record**：

`docs/audits/SYSTEM_AUDIT_M0_M11.md`

第一步只提取：

- 所有 BLOCKER；
- 高风险 MAJOR；
- claimed root cause；
- claimed fix；
- claimed regression；
- deferred risk；
- SA-1 final exit claims。

第一步不要并行：扫描全仓、重跑所有 tests、读取全部 M0–M11 Completion Records、重新阅读整个 Architecture、重新执行 SA-1 全部步骤。
取得 SA-1 Finding inventory 后，立即从最高风险 BLOCKER 开始独立验证。

---

## Execution Strategy

保持一条连续审计轨迹：

```text
SA-1 claim
→ production path
→ original failure invariant
→ independent counterexample
→ observed behavior
→ root cause validity
→ regression sensitivity
→ adjacent Contract
→ CLOSED / OPEN
```

然后进入下一项。不要每验证一个 finding 就重新总结整个 SA-1R。

SA-1R 不是"把 SA-1 再跑一次"，而是"攻击 SA-1 的结论，证明它经得住独立复核"。

---

## A. SA-1 Finding Revalidation

所有 SA-1 BLOCKER 逐个重新验证。对每项建立：

```text
Finding → Original invariant violated → Production path → Independent reproduction → Current behavior → Fix location → Regression test → Adjacent Contract → Verdict
```

只有同时满足：

- 原反例已不能成功；
- production path 确实修复；
- regression test 对该 bug 有判别力；
- 相邻冻结 Contract 未破坏；

才允许 `CLOSED`。

重点攻击以下假修复：只修症状、production path 未改、只改 test、special-case、hard-code、weaker assertion、fixture mutation、exception suppression、Policy/validation 放宽、threshold 降低、BLOCKER 被重新分类成较低等级来获得 PASS。发现即按当前真实严重度重新分类并处理。

---

## B. Regression-Test Sensitivity

SA-1 新增的关键 regression tests 不能只证明"现在代码能 PASS"，必须证明"旧 bug / 等价 mutation 会 FAIL"。

优先低风险方式验证：Git history / pre-fix diff；isolated historical revision / worktree（若仓库允许且安全）；minimal counterexample；targeted mutation。不要污染当前工作树来制造旧版本。重点抽查 BLOCKER 和高风险 MAJOR。

如果 regression test 在错误实现上仍 PASS：它不是有效的回归保护。修复测试判别力，而不是增加更多弱 assertion。

---

## C. Frozen Architecture Contracts

不要重新做完整 Architecture Review。只沿 `SA-1 fix seam + 高风险系统 seam` 抽查：

```text
Domain → Application → Port → Adapter
Protocol → Preflight → RunManifest → Run
Role → Skill → Capability → ToolResolver → ToolProvider
ExperimentPlan → ExecutionBackend → ExperimentRun → Metric → Artifact
Source → Evidence → Claim → Governed Memory
Research Result → Evaluation → EvalResult
```

寻找 SA-1 修复导致的：dependency inversion violation、framework/runtime type leakage into Domain、Adapter-owned canonical truth、duplicate model、shadow repository、parallel service、production bypass、Contract semantic drift。

实现改变冻结语义但没有正式 ADR / compatibility basis 的，视为真实 Contract regression。

---

## D. Reliability / Recovery Attack

不要机械重跑全部 reliability tests 后直接判绿。选择高价值 state transition 主动制造反例：

```text
duplicate dispatch / retry after uncertain completion / cancel-complete race / retry-result race /
lease expiry / runtime/process crash / repository-transaction failure / outbox failure /
restart-recovery / cleanup failure
```

最终必须检查 **canonical state**，而不仅是 API 返回值。重点寻找：duplicate fact、double execution、orphan lease、orphan process/container、stuck RUNNING、cancelled-but-completed、completed-but-retried、lost event、partial commit、inconsistent state after recovery。

已有测试 PASS 不是停止攻击的理由。

---

## E. Security Attack

- **Capability**：验证 exposure-time 与 execution-time authorization 都真实存在。主动尝试：denied capability、stale capability、Tool alias、provider collision、provider discovery、frozen ToolSet drift、direct runtime tool execution。upstream ALLOW 不得成为永久授权。
- **Credential**：保持 `LLM Relay Credential != Tool Credential`。主动搜索并制造 Secret-bearing paths：logs、exception、Artifact、Manifest、Session/Event、ToolResult、Memory、EvalResult / Reviewer input。不得因为经过某个 adapter 就失去 credential boundary。
- **Workspace / Execution**：攻击 `../` traversal、absolute path、symlink escape、cross-workspace access、host home、secret file、Docker socket、unsafe mount、unrestricted subprocess、network bypass。

任何真实 authority bypass：BLOCKER。

---

## F. Research Truth / Provenance Attack

以下关系必须始终成立：

```text
ToolResult != Evidence
Agent Output != Verified Claim
Reviewer Output != Scientific Truth
Memory != Arbitrary Agent Memory
Derived Index != Canonical State
```

重新执行一条真实 production chain：`Experiment → Artifact → Evidence → Claim → Evaluation → MemoryWriteProposal → Governed Memory`。

关键 truth transition 不得直接构造下游成功状态。主动制造：missing provenance、corrupted Artifact、wrong Metric、unsupported Claim、contradictory Evidence、negative scientific result、deleted/superseded Memory、failed Evaluation infrastructure。

必须保持 `Scientific Negative Result != System Failure` 与 `Evaluation Infrastructure Failure != Research Quality Failure`。contradiction 不得 last-write-wins。deleted canonical state 不得通过 derived index / Eval stale input 复活。

---

## G. SA-1 Fix Secondary Regression

对每个重大 SA-1 fix 至少选择一个相邻 Contract 反向检查。重点：stricter Policy → 合法路径全部失败；stronger validation → resume/replay 破坏；cleanup fix → premature deletion；retry fix → legitimate retry 被禁止；evidence fix → negative result 被过滤；credential fix → scope 错误；Artifact fix → historical digest 破坏；Evaluator fix → benchmark leakage / false PASS。

不要只验证"原 bug 不见了"，必须验证 `fix + adjacent valid path` 仍然同时成立。

---

## H. Independent Blind-Spot Search

所有 SA-1 BLOCKER 重新验证后，再沿以下 seam 寻找 SA-1 可能遗漏的系统级风险（不要重新逐文件审计 M0–M11）：

```text
authorization → execution
execution → Artifact
Artifact → Evidence
Evidence → Claim
Claim/Evidence → Evaluation
Evidence/Claim → Memory
cancellation/retry → state
Credential → Tool/Runtime
RunManifest → version/digest
canonical → derived state
```

寻找 `locally valid + cross-contract invalid`，而不是一般代码风格问题。

---

## I. Test Trustworthiness

全局搜索和抽查：skip、xfail、empty/pass、NotImplemented、TODO、fake、mock、monkeypatch、hard-coded result、weak assertion、direct state construction。但关键词出现本身不算 finding，必须追踪是否影响关键 production guarantee。

高风险模式：Fake-only core path、direct VERIFIED Claim construction、direct successful Experiment construction、always-PASS evaluator、hidden expected answer、fake production adapter、assertion 只检查 `is not None` / `truthy`、异常被 catch 后默认为 PASS。必要时用 counterexample / mutation 验证测试敏感度。

---

## J. Supply Chain

重新验证关键 runtime / dependency 的：pinned version/revision、lockfile、source origin、license、optional vs required、adapter isolation。

重点确认：`docs/references/upstream/OPENHANDS_REVISION_LOCK.yaml` 中的 OpenHands revision = 实际 runtime qualification target。不要在 SA-1R 中顺手升级 OpenHands、升级 DeepSeek Harness、替换重大 runtime、引入新的核心 framework。DeepSeek Harness 若仍为 future candidate，保持 future scope。发现 upstream drift：记录并验证影响，不做无授权迁移。

---

## K. Repository / Documentation Consistency

验证当前代码与以下记录一致：Roadmap、Completion Matrix、Completion Records、Architecture、ADR、BACKLOG、`docs/INDEX.md`、IG-1、SA-1 Audit Record。

重点查：broken links、stale status、duplicate roadmap truth、future feature 写成 implemented、implemented feature 写成 future、dangling PLAN/review、generated/cache/debug artifact、accidental secret/config。不要重写历史记录来制造一致。文档必须描述真实系统，而不是反过来修改代码以匹配旧文档。

---

## L. Operational Smoke / Soak

执行合理范围的连续运行验证：repeated runs、repeated experiments、repeated evaluations、cancel/retry cycles、restart/recovery cycle。观察：process、container、workspace、lease、temp files、file descriptors、DB connections、memory/resource usage。

目标不是性能 benchmark，而是证明系统不是只在一次 clean run 下成立。持续增长的残留必须定位 ownership / cleanup root cause。

---

## M. IG-1 Production Chain Revalidation

重新执行 IG-1 最关键的真实链：

```text
Role / Agent → Skill → Capability → Tool → Experiment → Artifact → Evidence → Claim → Evaluation → Governed Memory
```

要求：production contracts、real critical adapters、正式 Policy、正式 Workspace/Execution、正式 provenance、非 always-PASS Evaluator、不直接构造下游最终状态、不用自由文本 summary 替代 typed state。同时至少验证一个 negative result / contradiction / failure path。证明 SA-1 fixes 没有破坏 IG-1。

---

## N. Full Quality Gate

只有 targeted re-audit 和真实修复稳定后，再执行完整质量门。按仓库当前正式定义运行适用的：deterministic validators、formatting/lint、type checking、architecture tests、Domain/Application tests、Port contract suites、adapter tests、security regressions、reliability/fault tests、M8–M11 regressions、IG-1 regression、documentation consistency、full `m0` quality profile。

仓库正式入口参考：`uv lock --check`；`uv sync --frozen --dev`；`pnpm install --frozen-lockfile`；`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`。其他 validator（`validate_bundle.py`、governance `validate.py`、`tools/docs_consistency_check.py`）按仓库当前定义执行。

不得因为耗时长静默跳过。无法执行 = `NOT VERIFIED`，不是 `PASS`。不要通过修改 gate 配置让质量门变绿。

---

## Finding Classification

- **BLOCKER**：M12 前必须关闭。包括 canonical-state corruption、security/credential bypass、provenance bypass、fake-only critical production path、false-PASS evaluator、unrecoverable reliability defect、severe state-machine corruption、frozen Contract regression。
- **MAJOR**：高影响但经证据证明不阻断当前 Entry。若延期必须明确影响、why non-blocking、containment、next gate。
- **MINOR**：非阻断技术债。
- **INVALID / NOT REPRODUCED**：SA-1 finding 经独立验证不成立或当前无法复现时使用，但必须给出具体证据，不能只改标签。

---

## Repair Rule

发现真实 BLOCKER / MAJOR：不要先写报告。直接执行：

```text
Reproduce → Root Cause → Minimal Fix → Regression Sensitivity → Adjacent Contract Regression → Cross-stage Regression → Re-audit
```

禁止：降低 Contract、降低 DoD、weaken Policy、weaken validation、修改 fixture 掩盖失败、threshold lowering、delete failing sample、hard-code case、suppress exception、Fake 替代 production path。修 root cause，不修审计表象。

普通失败、局部实现选择、可逆修改不需要用户确认。只有"必须改变冻结核心架构 / destructive-irreversible / 重大 security boundary / license-compliance / 仓库事实无法解决的重大路线分歧"才停下请求决策。

---

## Goal-Round Discipline

在后续 Goal Round：

- 先 `get_goal` 读取当前 `revision` / `phase`，确认无用户新指示；
- 从当前 workspace、最近测试结果、Git 状态和已确认 finding 继续；
- 不从头重读本 Prompt，不重做已关闭 finding，不再次生成全局计划，不重复解释 SA-1R 是什么，不因进入新 Round 就重新扫描仓库；
- 每一轮优先关闭当前最高风险未决项；
- 一个 finding 已有充分 closure evidence：标记关闭并移动到下一个；
- 修复产生新 regression：沿该 causal chain 继续，不重新展开整个系统；
- Goal 保持 active，直到全部 Exit Criteria 实际满足，才 `update_goal(action=complete)`。

---

## Exit Criteria

只有以下全部同时成立，才允许完成 active Goal：

1. SA-1 所有 BLOCKER 已独立验证关闭；
2. 没有新发现的未关闭 BLOCKER；
3. 高风险 MAJOR 已修复，或有可证明的非阻断依据；
4. Security boundary 成立；
5. Reliability / recovery boundary 成立；
6. Research Truth / provenance boundary 成立；
7. SA-1 regression tests 对原缺陷具有真实判别力；
8. SA-1 fixes 未破坏 M0–M11 / IG-1 frozen Contracts；
9. IG-1 production integration chain 真实通过；
10. operational smoke/soak 未出现阻断级泄漏；
11. full quality gate 与 `m0` 满足仓库正式要求；
12. Repository 能提供可追溯、可重复的审计证据。

如果仍有可执行工作：继续执行，不报告 blocked。如果某关键项未验证：不得用历史 PASS 替代。

---

## Final Evidence

最终只在全部审计工作结束后集中输出：

1. SA-1 Finding Revalidation Matrix；
2. 所有 BLOCKER 独立 closure evidence；
3. 新发现 BLOCKER / MAJOR / MINOR；
4. Architecture / frozen Contract re-audit；
5. Reliability / recovery evidence；
6. Security evidence；
7. Research Truth / provenance evidence；
8. Test Trustworthiness / mutation evidence；
9. SA-1 fix secondary-regression evidence；
10. Supply-chain / repository consistency；
11. operational smoke / soak evidence；
12. IG-1 production-chain evidence；
13. full quality gate / `m0` results；
14. remaining risks / technical debt；
15. `SA-1R: PASS / FAIL`；
16. `M12 Entry: READY / NOT READY`，逐项说明依据。

只有所有 Exit Criteria 都有实际证据时才允许：

```text
SA-1R: PASS
M12 Entry: READY
```

完成后调用 `update_goal(action=complete)`，停止在 M12 Entry Gate。不要开始 M12。
