---
id: PLAN-20260815-015
slug: m10-evidence-memory-retrospective
title: M10 Evidence / Memory / Provenance — Retrospective Reconstruction
status: DONE
created_at: 2026-08-15
updated_at: 2026-08-16
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "DOC-R1 Documentation Recovery & Reconciliation：为缺失 Plan 的 M10 阶段创建 retrospective stage record"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260815-015-m10-evidence-memory-retrospective.md
memory_entries: []
---

# PLAN-20260815-015 — M10 Retrospective Reconstruction

> RETROSPECTIVE_RECONSTRUCTION: true
>
> 本记录由 2026-08-16 DOC-R1 文档恢复/校正任务依据 git history（commit
> `900c1b1`）、`docs/roadmap/M10_COMPLETION_RECORD.md`（2026-08-15 原开发
> 窗口产出）、当前代码/测试与可执行 validator 事后重建。M10 开发窗口
> （2026-08-15）当时未创建独立任务计划与复检文件（`git log --all --`
> `'*m10*'` 与 plans/tasks 全历史均无匹配）；本记录不声称这些文件在开发时
> 已存在，也不虚构当时的讨论、评审或测试结果。所有陈述均可由
> `M10_COMPLETION_RECORD.md`、commit `900c1b1` 或当前工作区证据支持。

## 目标（M10 定义，来自 `docs/roadmap/MILESTONES.md` M10 节）

Evidence / Memory / Provenance：让研究结论有据可查、长期记忆可治理，
落地 ADR-0003/0017 与 AGENTS.md §8。Inputs：M7 的 MemoryStore Port；
M1 的 `SourceRecord / Claim / Evidence / EvidenceRelation / MemoryRecord /
MemoryWriteProposal` Domain 实体；`EventPublisher`。

## 验收条件（retrospective 重建记录自身的验收）

- [x] AC-01：本记录全部陈述可由 git history、`M10_COMPLETION_RECORD.md`、
      当前代码/测试或可执行 validator 直接支持；无虚构的讨论、评审或
      测试结果。
- [x] AC-02：M10 的 DoD（MILESTONES M10 完成条件）逐项有当前证据。
- [x] AC-03：重建记录通过 governance validator（章节/ID/状态机）与
      bundle validator（链接/版本引用）。
- [x] AC-04：retrospective 性质在文件头显式标注
      `RETROSPECTIVE_RECONSTRUCTION: true`。

## 实际实现范围（来源：M10_COMPLETION_RECORD.md + commit `900c1b1`）

- WP-A Evidence & Provenance Ledger：`EvidenceLedger` Port
  （register_source/register_evidence/register_claim/update_claim/
  attach_relation/get_*/relations_for_claim/has_source/claims）+
  `FakeEvidenceLedger`；`promote_claim_to_verified`（PROPOSED→VERIFIED
  唯一升级入口，gate PASS + 合法 provenance 前置）；
  `register_evidence_with_contradiction_check`（REFUTES→DISPUTED，旧证据
  保留）；M7 编排接入（SourceRecord 登记 + CLAIM_VERIFIED 事件）。
- WP-B Governed Memory Lifecycle：`evaluate_memory_proposal` /
  `commit_memory` 全链路 gate（schema→provenance→contradiction→policy→
  curator/automatic→commit，复用 PolicyEvaluator）；`MemoryRecord.active`
  生命周期字段；`MemoryWriteProposal.supersedes`；`deactivate_memory`
  （tombstone）/ `delete_memory`（+MEMORY_DELETED）/ `supersede_memory`；
  `MemoryStore.deactivate` Port 增量。
- WP-C Derived Index & Consistency：`RetrievalIndex` Port
  （rebuild/upsert/remove/search/entries/clear + `content_hash_of` 等价
  契约）+ `FakeRetrievalIndex` / `InMemoryRetrievalIndex`；
  `check_index_consistency`（5 类 drift 只读检测）+ `rebuild_index`
  （显式修复路径）。
- 事件扩展：`CLAIM_DISPUTED`、`MEMORY_DELETED`（事件清单 32→34）。

## 非目标

- 不绑定具体 embedding 模型（derived index 可替换）；不做 UI；不做
  多租户隔离（M18）；不把向量索引当 Canonical State（ADR-0002 边界）；
  EvidenceLedger 持久化归属 M14（PostgreSQL Canonical State）。

## Dependencies

- Hard：M7 DONE（2026-08-14）；M10 计划经 Plan Mode 批准（原开发窗口
  Cursor Plan `M10 Evidence Memory Provenance`，2026-08-15）。
- 并行组 1：M8（2026-08-14 DONE）、M9（2026-08-15 DONE）、M11
  （2026-08-15 DONE）与 M10 互不阻塞。

## Architecture boundaries

- 新增 `EvidenceLedger` / `RetrievalIndex` 为 inward-owned Port
  （`packages/application/ports/`，17 Port 名，contract registry 同步）；
  application use case（`packages/application/evidence/`、
  `packages/application/memory/`）只经 Port 与 Fake/InMemory 实现交互；
  `InMemoryRetrievalIndex` 为确定性 token 检索，无 embedding 依赖。

## 主要 implementation artifacts

| 类型 | 位置 |
| --- | --- |
| EvidenceLedger Port + Fake | `packages/application/ports/evidence_ledger.py`、`adapters/fakes/evidence_ledger.py` |
| RetrievalIndex Port + 实现 | `packages/application/ports/retrieval_index.py`、`adapters/index/`、`adapters/fakes/retrieval_index.py` |
| Evidence use cases | `packages/application/evidence/`（claim promotion、contradiction check） |
| Memory gate + lifecycle + consistency | `packages/application/memory/`、`packages/domain/memory.py`、`packages/application/ports/memory_store.py` |
| M7 编排集成 | `packages/application/run_orchestration/{result_handler,phase_runner,claim_promotion,usage_recording}.py` |
| 事件扩展 | `packages/domain/events.py`、`docs/architecture/EVENT_MODEL.md` |

## Git commits

- `900c1b1`（2026-08-15）feat(m10): evidence-backed memory with
  independent-review hardening（45 files，+3117/-37；含 gate pipeline、
  EvidenceLedger/RetrievalIndex Port、独立复审修复项，与完成记录逐项吻合）。

## Tests / validation

- `tests/application/memory/`（6 文件：gate / index_rebuild / consistency /
  negative_result / lifecycle / gate_adversarial）；
- `tests/application/evidence/`（2 文件：provenance / contradiction）；
- `tests/contracts/test_evidence_ledger_contract.py`、
  `tests/contracts/test_retrieval_index_contract.py`（registry 驱动，
  Fake + InMemory 双实现）；
- `tests/e2e/test_claim_verification.py`（gate PASS → Claim VERIFIED +
  CLAIM_VERIFIED 事件；ledger 未装配安全降级）；
- 全量 pytest 1448 passed（含 M10 新增 88 tests）；m0 profile 18/18
  deterministic checks PASS（记录于 M10_COMPLETION_RECORD.md 验证命令节）；
  ruff / mypy strict（308 source files）全绿。
- 独立复审：`M10_COMPLETION_RECORD.md`「独立复审记录」节——5 项缺陷
  （3 BLOCKER + 2 MAJOR）已修复并有对抗性回归测试（16 项新增）；
  并发边界（单进程语义、跨进程并发归 M14）诚实记录。
- 本重建记录的有效性验证由 RECHECK-20260815-015 于 2026-08-16 重跑
  m0 profile / validators 后判定。

## DoD（MILESTONES M10 完成条件逐项核对）

- [x] MemoryWriteProposal 全链路测试（无 provenance 拒绝、policy deny、
      curator 通过三类路径）——`tests/application/memory/test_gate.py`。
- [x] 删除后索引重建一致性测试——`test_index_rebuild.py`（clear→rebuild
      等价、delete/deactivate 无 ghost、tombstone 不索引）。
- [x] 同一 Claim 冲突证据检测测试——`test_contradiction.py`
      （REFUTES→DISPUTED、SUPPORTS 不触发、DISPUTED 幂等、旧证据保留）。
- [x] negative result 记忆用例——`test_negative_result.py`
      （写入/检索/contradiction/tombstone 四路径）。
- [x] 独立复审 PASS + m0 profile 全绿——完成记录独立复审节 + 18/18
      deterministic checks PASS。

## 发现过的重要问题

- M10 开发窗口未创建独立 plan/recheck 文件（本次重建的动因），亦无
  M10 工程记忆条目（`.cursor/memory/entries/` 最新为 M8 的
  MEM-20260814-012）。重建不补 MEM（DOC-R1 范围约束），缺口记入
  `docs/roadmap/DOCUMENT_RECOVERY_M0_M11.md` remaining risks。

## 最终状态

- 状态：DONE（以 git `900c1b1`、M10_COMPLETION_RECORD.md 逐项证据与
  m0 profile 可执行门禁为证）。

## 对下一阶段提供的 Contract

- M12 集成点 = 真实 run 的 claim 升级与记忆写入复用 M10 use case；
  EvidenceLedger 持久化 P1 债归 M14；RetrievalIndex 持久化 / 真实
  embedding P2 债在 M12 前评估。

## 已知非阻断技术债

- EvidenceLedger 持久化（P1 → M14）；RetrievalIndex 持久化 / 真实
  embedding（P2 → M12 前评估）；跨进程并发语义（P2 → M14 PostgreSQL
  事务）——均已在 `BACKLOG.md` 登记。

## 实施清单（重建动作）

- [x] STEP-01：从 git log（`900c1b1`）/ 完成记录 / 目录结构提取 M10
      实现证据。
- [x] STEP-02：核对 MILESTONES M10 DoD 并逐项落证据。
- [x] STEP-03：创建本 retrospective 计划并登记 ALL_PLAN。
- [x] STEP-04：执行 retrospective recheck（RECHECK-20260815-015，
      2026-08-16 实际重跑 validators/门禁）。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 实现范围 | git | `900c1b1`（45 files，+3117/-37） | 存在 |
| EV-02 | 完成事实 | doc | `docs/roadmap/M10_COMPLETION_RECORD.md`（WP-A/B/C、DoD 逐项证据、独立复审 5 缺陷表） | 存在 |
| EV-03 | Port 契约 | file | `packages/application/ports/{evidence_ledger,retrieval_index,memory_store}.py` + contract registry | 存在 |
| EV-04 | 测试 | test | `tests/application/memory/`（6）、`tests/application/evidence/`（2）、`tests/contracts/test_{evidence_ledger,retrieval_index}_contract.py`、`tests/e2e/test_claim_verification.py` | 存在 |
| EV-05 | DoD 核对 | check | 2026-08-16 重跑 m0 profile + validate_bundle + governance | 见 RECHECK-20260815-015 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-16 | — | IN_PROGRESS | DOC-R1 创建 M10 retrospective 重建记录 | 本计划创建 |
| 2026-08-16 | IN_PROGRESS | DONE | RECHECK-20260815-015 PASS（2026-08-16 实际重跑） | RECHECK 文件 |

## 影响报告

- Domain/API/schema：无（本记录为纯文档重建，产品变更见 commit `900c1b1`）。
- 安全/凭据：无。
- 兼容性/迁移：无。
- 上游版本：无（M10 无新增上游依赖；embedding provider 为 future
  dependency，不实现）。
- 下一项任务：M10 停在阶段边界；并行组 1（M8/M9/M10/M11）全部 DONE，
  IG-1（M12 entry）前置齐备；M12 立项需用户显式启动，本重建不自动开工。