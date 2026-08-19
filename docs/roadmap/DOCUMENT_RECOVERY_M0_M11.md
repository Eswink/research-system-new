# DOC-R1 — M0–M11 Documentation Recovery & Reconciliation 最终报告

- 日期：2026-08-16
- 范围：M0–M11 文档恢复、重建与校正；不开发产品功能、不改变 Milestone
  路线、不提前执行 IG-1/M12
- 事实优先级：当前代码/Schema/Port/Tests > Git history > `.cursor/plans` >
  deterministic validation > ADR/Architecture > Roadmap/BACKLOG > README/说明文档

## 1. Inventory

完整分类矩阵见 [M0_M11_DOCUMENT_MATRIX.md](M0_M11_DOCUMENT_MATRIX.md)
（Phase 1 产物）。摘要：

| 分类 | 数量 | 说明 |
| --- | --- | --- |
| PRESENT | 主要部分 | M0–M7 证据链（10 对 plan/recheck、MEM、matrix）、CODEX_BOOTSTRAP.md（M0–M7 定义完整保留）、24 份 ADR、全部 upstream qualification 文档 |
| MISSING | 2 | `M11_COMPLETION_RECORD.md`、`COMPLETION_MATRIX_M0_M11.md`（统一矩阵） |
| STALE | 8 | MILESTONES M11 状态、BACKLOG（M8/M9/M11）、INDEX/README/CHANGELOG 头部、PORTS.md（14→17 Ports）、SYSTEM_ARCHITECTURE.md（模块数/端口）、M8/M9/M10 记录缺 Git Evidence |
| CONTRADICTORY | 2 | MILESTONES M11=PLANNED vs 已完成；INDEX 头部 M0–M7 vs Evaluation 节已含 M11 |
| BROKEN_REFERENCE | 4 | PORTS.md 14 处缩写路径、MODEL_PROBE.md 不存在的测试文件、DETERMINISTIC_SERIALIZATION.md 缩写路径、INDEX 裸文件名 |
| RECOVERABLE_FROM_GIT | 0 | 无文档被意外删除（CODEX_BOOTSTRAP.md 在 `d1e27ba` 后仍存在；`git log --all --diff-filter=D` 仅 bootstrap 早期 `BOOTSTRAP_MANIFEST.json`） |
| RECONSTRUCTABLE | 2 | M10 plan/recheck、M11 completion record（见 §3） |
| UNKNOWN | 0 | 全部阶段有代码/Git/测试证据支撑完成事实 |

## 2. 从 Git 原样恢复的文档

**无。** 调查确认不存在"意外删除后可恢复"的文档：

- `CODEX_BOOTSTRAP.md` 从未被删除（工作区存在，M0–M7 定义完整，仅
  Post-M7 为指向 MILESTONES 的指针——与 `d1e27ba` 提交描述一致）。
- M10 的 plan/recheck 与 M11 的 completion record 在 Git 历史中**从未
  存在**（`git log --all -- '*m10*'` 零匹配；`--diff-filter=D` 无相关
  删除记录），无法"恢复"，只能重建。

## 3. 根据 repository evidence 重建的文档

所有重建件均显式标注来源，不伪装成原始历史文件：

| 文件 | 性质 | 证据来源 |
| --- | --- | --- |
| `.cursor/plans/tasks/PLAN-20260815-015-m10-evidence-memory-retrospective.md` | `RETROSPECTIVE_RECONSTRUCTION: true` | `M10_COMPLETION_RECORD.md`（原开发窗口产出）、commit `900c1b1`（45 files，+3117/-37）、当前代码/测试 |
| `.cursor/plans/rechecks/RECHECK-20260815-015-m10-evidence-memory-retrospective.md` | retrospective validation，PASS | 2026-08-16 实际重跑 bundle/governance validator + 证据核对 |
| `docs/roadmap/M11_COMPLETION_RECORD.md` | `Reconstructed from repository evidence` | PLAN-20260815-014（DONE）、RECHECK-20260815-014（PASS）、commits `0846765`/`0cc6361`、`docs/references/upstream/M11_EVAL_HARNESS_QUALIFICATION.md`、`docs/architecture/EVALUATION.md` §8 |

## 4. 修正的 stale / contradictory 文档

| 文件 | 修正内容 |
| --- | --- |
| `docs/roadmap/MILESTONES.md` | M11 状态 PLANNED→DONE（2026-08-15）；M8 节补完成状态 blockquote；M11 节补完成状态 blockquote；"下一阶段推荐"由 M8 更新为 M12（附历史说明） |
| `BACKLOG.md` | 头部状态更新为 M0–M11 completed + IG-1 齐备；M8/M9/M11 状态 PLANNED→DONE（附 commit）；"以下均为未来设想"声明收窄至 M12+ |
| `docs/INDEX.md` | 头部状态与快速问答更新；补 `M10_COMPLETION_RECORD.md`/`M11_COMPLETION_RECORD.md`/统一矩阵条目；Evaluation 节裸文件名补 `../`；阶段工程记录节补 M10 retrospective |
| `README.md` | 当前工程状态更新为 M0–M11 completed（含 17 Ports、37 domain 模块、M8–M11 适配器清单）；开发入口更新 |
| `CHANGELOG.md` | 补 M8/M9/M10/M11 四条（日期 + commit + 摘要）+ DOC-R1 条目 |
| `docs/architecture/PORTS.md` | Port 清单 14→17（补 ToolPackStore/EvidenceLedger/RetrievalIndex，标注 M8/M10 增补）；14 处 `ports/` 缩写路径全部修正为 `packages/application/ports/`；Fake 覆盖与 contract 矩阵计数同步 |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | §3 domain 模块数 29→37 + 新增 application/adapters 目录；§4 移除不存在的 Evaluator 端口，补 ToolPackStore/EvidenceLedger/RetrievalIndex 与 M11 说明；§7 补 M8–M11 能力平面增补段 |
| `docs/integration/MODEL_PROBE.md` | 悬空引用修正为实际文件 `tests/application/test_run_probe.py` |
| `docs/architecture/DETERMINISTIC_SERIALIZATION.md` | `validate_bundle.py` 补全路径 |
| `docs/roadmap/` 下 M8/M9/M10 三份 `*_COMPLETION_RECORD.md` | 各补 Git Evidence 段（`4c2c16d`/`4156238`+`b8560ee`/`900c1b1`）；M8 补风险登记段 |
| `docs/roadmap/COMPLETION_MATRIX_M0_M7.md` | 头部加"已被 COMPLETION_MATRIX_M0_M11.md 取代为唯一权威"指针；历史行未动 |
| `.cursor/plans/ALL_PLAN.md` | 加入 PLAN-20260815-015（retrospective 标注） |

未修改任何 ADR（M8–M11 决策已由完成记录承载，无 superseding 需求）。

## 5. 无法恢复的历史信息

- M10 原开发窗口（2026-08-15）的独立 plan/recheck 文件：从未存在，
  不可恢复；retrospective 重建已在 §3 完成。
- M11 原开发窗口的 completion record：从未存在，不可恢复；已重建。
- M9/M10/M11 的工程记忆条目（MEM）：`.cursor/memory/entries/` 最新为
  M8（MEM-20260814-012）。DOC-R1 范围不补 MEM（属 `.cursor/memory` 治理
  流程），缺口记入 §8 remaining risks。
- 各阶段开发窗口内的讨论、评审过程与时间线细节：无记录、不重建。

## 6. Completion Matrix

统一完成矩阵：`docs/roadmap/COMPLETION_MATRIX_M0_M11.md`（唯一权威，
M0–M11 含 M5R 共 12 行，每行含 Scope/Implementation/Plan/Review/
Completion Record/Git Evidence/Status）。

完成状态摘要：

```text
M0（08-11，3cc6130）→ M1（08-11，185a752）→ M3（08-11，7bfcd3c）→
M2（08-12，1035a64）→ M4（08-12，7c68e92）→ M5（08-12，c75db51）→
M5R（08-12/13，717545d+5fc23d0）→ M6（08-13，f4b2168）→
M7（08-14，782887d+52c8b8b）→ M8（08-14，4c2c16d）→
M9（08-15，4156238+b8560ee）→ M10（08-15，900c1b1）→
M11（08-15，0846765+0cc6361）
```

- 原开发窗口记录：M1–M6/M5R/M8/M9/M11（Plan + PASS Recheck）；
- Retrospective：M0（08-14）、M7（08-14）、M10（08-16，DOC-R1）；
- IG-1（M12 entry）前置四项（M8/M9/M10/M11 独立复审）全部齐备。

## 7. Validation Results

| 验证 | 结果 |
| --- | --- |
| `tools/docs_consistency_check.py`（新增，6 项确定性检查：INDEX roadmap 完整性 / milestone 状态一致性 / completion record dangling refs / 反引号代码引用可解析 / milestone 命名重复 / HEAD 状态标记） | PASS（6/6） |
| `tests/tooling/test_docs_consistency_check.py`（新增，8 项含正/负例 + 真实仓库冒烟） | 8 passed |
| `run_all_checks.py` framework 组接入 | `framework/docs_consistency_check` 已入列（CI `--profile m0` 自动覆盖，无需改 workflow） |
| `validate_bundle.py` | 见 §9 quality gate |
| `governance-check validate.py` | 见 §9 quality gate |
| 全仓 markdown 链接（既有 validator 覆盖） | 零损坏（调查确认；最终重跑见 §9） |

## 8. Remaining Risks

1. **M9/M10/M11 无工程记忆条目**：属 `.cursor/memory` 治理流程覆盖缺口，
   由后续工程流程按需补录（本任务按范围约束未补）。
2. **completion record 中的测试数量/回归指标**（1139/1298/1448/1610
   pytest 等）取自各阶段原开发窗口执行证据；DOC-R1 收尾 quality gate
   只重跑 validators 与文档检查，不逐项重放历史数字。数字变化时以最新
   全量回归为准，不影响完成判定（判定依据为可执行门禁而非记录数字）。
3. **`COMPLETION_MATRIX_M0_M7.md` 双矩阵并存**：已通过头部指针声明唯一
   权威关系；未来文档引用应指向 `COMPLETION_MATRIX_M0_M11.md`。
4. **docs 反引号引用检查存在豁免清单**（`d:\upstream`、OpenHands SDK
   路径、glob 模式、类名等），新增文档若使用未豁免的缩写路径会被新
   validator 拦截（预期行为）。
5. **CI 验证延迟**：新检查在本地与本机 pytest 已验证；GitHub Actions
   quality job 的首次全量运行在下次 push/PR 触发。

## 9. Quality Gate（DOC-R1 收尾执行）

按计划执行：`validate_bundle.py` + `governance validate.py` + 新 docs
check + ruff/mypy/pytest（m0 profile 相关子集）+ 全量 m0 profile。
结果记录于本次任务最终执行输出。

## 判定

**DOC-R1 PASS 条件核对**：

- [x] M0–M11 主要 Contract 可追溯：统一完成矩阵 + 各阶段 completion
      record + plan/recheck（原窗口或 retrospective）+ commit 证据齐备；
- [x] 完成证据可追溯：每阶段均有代码/测试/validator 可执行证据；
- [x] 导航可追溯：MILESTONES（唯一权威）→ BACKLOG（执行映射）→
      INDEX（含全部 M0–M11 关键文档）→ ALL_PLAN（与实际计划文件一致）；
- [x] 无伪造历史：重建件全部显式标注来源。

DOC-R1 停止于本报告；不自动开始 IG-1 或 M12。