# M0–M11 Document Matrix — DOC-R1 Inventory

本矩阵由 DOC-R1 文档恢复/校正任务（2026-08-16）建立，对 M0–M11 各阶段
及关键文档逐项分类。分类依据（事实优先级）：

1. 当前实际代码、Schema、Port 与 Tests；
2. Git history / commits / tags；
3. `.cursor/plans` 中已有 Plan / Recheck / Review；
4. deterministic validation 与 DoD evidence；
5. ADR / Architecture；
6. Roadmap / BACKLOG；
7. README / explanatory docs。

不依据聊天记忆或旧 Markdown 猜测历史。分类值：

- `PRESENT`：文档在库且与当前事实一致；
- `MISSING`：应当存在但当前与 Git 历史中均不存在；
- `STALE`：文档存在但内容落后于当前实现；
- `CONTRADICTORY`：文档内部或与权威来源状态冲突；
- `BROKEN_REFERENCE`：引用目标不存在或不可解析；
- `RECOVERABLE_FROM_GIT`：可从 Git 历史原样恢复；
- `RECONSTRUCTABLE`：无法恢复原件，但可由 repository evidence 重建
  （重建件必须标注 `Reconstructed from repository evidence`）；
- `UNKNOWN`：无任何可验证证据。

## 1. 里程碑证据链（plan / recheck / memory / completion record）

| Stage | Plan | Recheck | Memory | Completion Record | 分类 | 修复计划 |
| --- | --- | --- | --- | --- | --- | --- |
| M0 | `PLAN-20260814-009`（retrospective） | `RECHECK-20260814-009` | `MEM-20260814-009` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M1 | `PLAN-20260811-001` | `RECHECK-20260811-001` PASS | `MEM-20260811-001` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M2 | `PLAN-20260812-003` | `RECHECK-20260812-003` PASS | `MEM-20260812-003` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M3 | `PLAN-20260811-002` | `RECHECK-20260811-002` PASS | `MEM-20260811-002` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M4 | `PLAN-20260812-004` | `RECHECK-20260812-004` PASS | `MEM-20260812-004` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M5 | `PLAN-20260812-005` | `RECHECK-20260812-005` PASS | `MEM-20260812-005` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M5R | `PLAN-20260812-006` | `RECHECK-20260812-006` PASS | `MEM-20260812-006` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M6 | `PLAN-20260813-007` | `RECHECK-20260813-007` PASS | `MEM-20260813-007` | 见 COMPLETION_MATRIX 行 | PRESENT | 无 |
| M7 | `PLAN-20260814-010`（retrospective）+ `-011` | `RECHECK-20260814-010`/`-011` | `MEM-20260814-010`/`-011` | `M7_COMPLETION_RECORD.md` | PRESENT | 无 |
| M8 | `PLAN-20260814-012` | `RECHECK-20260814-012` PASS + `-013` 独立复审 | `MEM-20260814-012` | `M8_COMPLETION_RECORD.md` | STALE | 记录补 Git Evidence 与 risks 段；MILESTONES 节内补完成状态段 |
| M9 | `PLAN-20260815-013` | `RECHECK-20260815-013` PASS | 无 MEM | `M9_COMPLETION_RECORD.md` | STALE | 记录补 Git Evidence；BACKLOG 状态改 DONE |
| M10 | 无（Git 历史从未存在） | 无（仅记录内嵌复审段落） | 无 MEM | `M10_COMPLETION_RECORD.md`（详尽） | RECONSTRUCTABLE | 按记录 + commit `900c1b1` 重建 retrospective plan/recheck（PLAN/RECHECK-20260815-015） |
| M11 | `PLAN-20260815-014` | `RECHECK-20260815-014` PASS | 无 MEM | 无（Git 历史从未存在） | RECONSTRUCTABLE + CONTRADICTORY | 新建 `M11_COMPLETION_RECORD.md`；MILESTONES 状态 PLANNED→DONE |

## 2. Roadmap / 导航文档

| 文档 | 分类 | 事实 | 修复计划 |
| --- | --- | --- | --- |
| `CODEX_BOOTSTRAP.md`（根） | PRESENT | M0–M7 定义完整保留（L50-56 标注 canonical）；仅 Post-M7 为指向 MILESTONES 的指针；与 d1e27ba 提交描述一致 | 无 |
| `docs/roadmap/MILESTONES.md` | STALE + CONTRADICTORY | L92 M11 状态 PLANNED（commit `0846765`/`0cc6361` 已完成，RECHECK-014 PASS）；M8 节内缺完成状态 blockquote（M9/M10 有） | M11→DONE + 完成段；M8 补完成段 |
| `BACKLOG.md`（根） | STALE | M8（L183-184）/M9（L185）/M11（L187）仍标 PLANNED；段首"以下均为未来设想"声明过期；头部状态止于 M0–M7 | 状态改 DONE；更新头部与过期声明 |
| `docs/roadmap/COMPLETION_MATRIX_M0_M7.md` | PRESENT（将被取代） | 9 行全覆盖、链接有效；尾部声明"不记录 M8 及以后" | 头部加"已被 COMPLETION_MATRIX_M0_M11.md 取代为唯一权威"指针，历史行不动 |
| `docs/roadmap/` 下 M7/M8/M9/M10 四份 `*_COMPLETION_RECORD.md` | PRESENT（M8/M9/M10 部分 STALE） | M8/M9/M10 均缺 Git Evidence（commit hash）段；M8 缺独立 risks 段；链接全部有效 | 补 Git Evidence 段；M8 补 risks 段 |
| `docs/roadmap/M11_COMPLETION_RECORD.md` | MISSING（RECONSTRUCTABLE） | 历史从未存在；证据充分（PLAN-014、RECHECK-014 PASS、commits、M11_EVAL_HARNESS_QUALIFICATION.md） | 新建，标注 `Reconstructed from repository evidence` |
| `docs/roadmap/COMPLETION_MATRIX_M0_M11.md` | MISSING | 统一完成矩阵不存在 | 新建（唯一权威，12 行） |
| `docs/INDEX.md` | STALE + CONTRADICTORY | 头部止于 M0–M7（M8–M11 已完成）；零 M10 引用；Evaluation 节已含 M11（自相矛盾）；裸文件名 `eval_result.py`/`eval_gate.py` 缺 `../` | 状态更新；补 M10/M11 记录条目；Evaluation 节理顺；路径修正 |
| `README.md`（根） | STALE | "当前工程状态"止于 M0–M7 | 更新为 M0–M11 completed |
| `CHANGELOG.md`（根） | STALE | 最新条目为 2026-08-14 M7 收尾，缺 M8/M9/M10/M11 | 补 4 条（日期 + commit + 摘要） |
| `.cursor/plans/ALL_PLAN.md` | PRESENT | 与 tasks/ 目录一致；M10 plan 不存在（非索引错误） | 重建后补 M10 条目（retrospective 标注） |
| `.cursor/memory/INDEX.md` | PRESENT | 14 条 MEM 全部存在；M9/M10/M11 无 MEM（覆盖缺口） | 不补 MEM；缺口记入最终报告 |

## 3. 架构 / 集成 / 可靠性 / 安全 / 评估文档

| 文档 | 分类 | 事实 | 修复计划 |
| --- | --- | --- | --- |
| `docs/architecture/PORTS.md` | STALE + BROKEN_REFERENCE | 声称 14 Port 全集（当前 17，缺 evidence_ledger/retrieval_index/tool_pack_store，M10 增补）；14 处 `ports/*.py` 缩写路径从 repo root 不可解析（实际 `packages/application/ports/`） | Port 清单 14→17；路径全部修正；保留 M5 基线描述 |
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | STALE | §3 domain 模块数 29→37（M8–M11 增补）；§4 关键端口含不存在的 Evaluator（M5 D4 已排除），缺收编 Port | 模块数修正；端口清单校正并补 M11 evaluation 说明 |
| `docs/integration/MODEL_PROBE.md` | BROKEN_REFERENCE | 引用一个不存在的 probe 测试文件（已修正为 `tests/application/test_run_probe.py`） | 已修复（Phase 4） |
| `docs/architecture/DETERMINISTIC_SERIALIZATION.md` | BROKEN_REFERENCE | `validate_bundle.py` 缩写路径不可解析 | 补全路径 |
| `docs/architecture/AGENT_RUNTIME.md` 等其余 18 份 architecture 文档 | PRESENT | 抽查一致（AGENT_RUNTIME 端口签名与代码逐字一致；其余未发现 stale 描述） | 无 |
| `docs/adr/`（24 份） | PRESENT | 无冲突；M8–M11 决策已由完成记录承载，无 superseding 需求 | 无（不修改 ADR） |
| `docs/integration/`、`docs/reliability/`、`docs/security/`、`docs/evaluation/`、`docs/governance/` | PRESENT | 链接与内容一致（EVALUATION.md §8 已含 M11 实现映射） | 无 |
| `docs/references/upstream/`（M8/M9/M11 qualification 等） | PRESENT | 全部存在且被 INDEX 引用 | 无 |

## 4. 验证设施

| 设施 | 分类 | 事实 | 修复计划 |
| --- | --- | --- | --- |
| `.cursor/skills/system-spec-check/scripts/validate_bundle.py` | PRESENT | 已覆盖 markdown 链接存在性、INDEX 反引号引用（.md/.yaml/.json）、schema 交叉引用 | 无（不修改 validator 逻辑） |
| `.cursor/skills/governance-check/scripts/validate.py` | PRESENT | 已覆盖 .cursor 资产与 plan/recheck/memory 交叉引用 | 无 |
| 文档一致性检查（INDEX 完整性 / milestone 状态冲突 / dangling plan-ref / 反引号代码引用） | MISSING | 现有 validator 均未覆盖 | 新建 `tools/docs_consistency_check.py` + 测试 + Makefile target + CI 接入 |

## 5. 恢复判定汇总

- `RECOVERABLE_FROM_GIT`：无。`CODEX_BOOTSTRAP.md` 未被删除；M10 plan/recheck
  与 M11 completion record 在 Git 历史中从未存在（`git log --all --diff-filter=D`
  与 `git log --all -- '*m10*'` 均已验证）。
- `RECONSTRUCTABLE`：M10 plan/recheck（证据：`M10_COMPLETION_RECORD.md` +
  commit `900c1b1`）；M11 completion record（证据：PLAN-014、RECHECK-014、
  commits `0846765`/`0cc6361`、M11_EVAL_HARNESS_QUALIFICATION.md）。
- `UNKNOWN`：无（所有阶段均有代码/Git/测试证据支撑完成事实）。

## 6. 修复顺序

1. Phase 2：重建 M10 retrospective plan/recheck（PLAN/RECHECK-20260815-015）；
2. Phase 3：新建 M11_COMPLETION_RECORD.md + 统一 COMPLETION_MATRIX_M0_M11.md；
3. Phase 4：架构文档校正（PORTS / SYSTEM_ARCHITECTURE / MODEL_PROBE /
   DETERMINISTIC_SERIALIZATION）；
4. Phase 5：导航与状态同步（MILESTONES / BACKLOG / INDEX / README / CHANGELOG）；
5. Phase 6：确定性文档一致性检查设施；
6. Final：DOCUMENT_RECOVERY_M0_M11.md 报告 + 完整 quality gate。

本矩阵与修复计划在 docs/roadmap/DOCUMENT_RECOVERY_M0_M11.md（DOC-R1 最终
报告，本任务同步创建）完成后即归档为该报告第 1 节（inventory）的事实来源。