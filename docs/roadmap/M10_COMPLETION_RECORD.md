# M10 — Evidence / Memory / Provenance 完成记录

- 日期：2026-08-15
- 范围权威：`docs/roadmap/MILESTONES.md` M10 节
- 前置：M7 DONE；M10 计划经 Plan Mode 批准（Cursor Plan `M10 Evidence Memory Provenance`）
- 结论：**M10 DoD 全部满足**

## Git Evidence

- `900c1b1`（2026-08-15）feat(m10): evidence-backed memory with
  independent-review hardening（45 files，+3117/-37；含 gate pipeline、
  EvidenceLedger/RetrievalIndex Port、独立复审 5 缺陷修复）。

## 交付摘要

| Work Package | 交付 | 落点 |
| --- | --- | --- |
| WP-A Evidence & Provenance Ledger | `EvidenceLedger` Port（register_source/register_evidence/register_claim/update_claim/attach_relation/get_*/relations_for_claim/has_source/claims）+ `FakeEvidenceLedger`；`promote_claim_to_verified`（PROPOSED→VERIFIED 唯一升级入口，gate PASS + 合法 provenance 前置）；`register_evidence_with_contradiction_check`（REFUTES→DISPUTED，旧证据保留）；M7 编排接入（SourceRecord 登记 + CLAIM_VERIFIED 事件） | `packages/application/ports/evidence_ledger.py`、`adapters/fakes/evidence_ledger.py`、`packages/application/evidence/`、`packages/application/run_orchestration/{result_handler,phase_runner,claim_promotion,usage_recording}.py` |
| WP-B Governed Memory Lifecycle | `evaluate_memory_proposal`/`commit_memory` 全链路 gate（schema→provenance→contradiction→policy→curator/automatic→commit，复用 PolicyEvaluator）；`MemoryRecord.active` 生命周期字段；`MemoryWriteProposal.supersedes`；`deactivate_memory`（tombstone）/`delete_memory`（+MEMORY_DELETED）/`supersede_memory`；`MemoryStore.deactivate` Port 增量 | `packages/application/memory/`、`packages/domain/memory.py`、`packages/application/ports/memory_store.py`、`adapters/fakes/memory_store.py` |
| WP-C Derived Index & Consistency | `RetrievalIndex` Port（rebuild/upsert/remove/search/entries/clear + `content_hash_of` 等价契约）+ `FakeRetrievalIndex`/`InMemoryRetrievalIndex`；`check_index_consistency`（5 类 drift 只读检测）+ `rebuild_index`（显式修复路径） | `packages/application/ports/retrieval_index.py`、`adapters/index/`、`adapters/fakes/retrieval_index.py`、`packages/application/memory/consistency.py` |
| 事件扩展 | `CLAIM_DISPUTED`、`MEMORY_DELETED`（清单 32→34，`docs/architecture/EVENT_MODEL.md` 与事件清单测试同步） | `packages/domain/events.py`、`docs/architecture/EVENT_MODEL.md`、`tests/domain/test_m5_domain_increments.py` |

## DoD 逐项证据

| DoD 项（MILESTONES M10） | 证据 |
| --- | --- |
| MemoryWriteProposal 全链路测试（无 provenance 拒绝、policy deny、curator 通过三类路径） | `tests/application/memory/test_gate.py`：provenance 未登记→stage=provenance 拒绝；policy deny（FakePolicyEvaluator 注入）→stage=policy 拒绝；PROJECT tier + curator_approved=True→commit + MEMORY_PROPOSED/MEMORY_COMMITTED 事件；另有 schema 空白拒绝、supersedes 引用完整性、绕过 pipeline 直调 store 被 Fake 白名单拒绝（防御纵深） |
| 删除后索引重建一致性测试 | `tests/application/memory/test_index_rebuild.py`：clear→rebuild 等价（entries content_hash 一致）、delete/deactivate 后 index 无 ghost、tombstone 不索引；`tests/application/memory/test_consistency.py`：5 类 drift 逐类检出 + rebuild 收敛 + checker 只读性 |
| 同一 Claim 冲突证据检测测试 | `tests/application/evidence/test_contradiction.py`：REFUTES 命中 VERIFIED/PROPOSED→DISPUTED；SUPPORTS 不触发；DISPUTED 幂等；旧 evidence/relation 保留；CLAIM_DISPUTED 事件 payload（claim_id/evidence_id/relation/actor/scope）审计字段 |
| negative result 记忆用例 | `tests/application/memory/test_negative_result.py`：NEGATIVE_RESULT 记忆经 gate 写入（ledger 已登记 provenance）可查询可检索；与 REFUTES claim 关联转 DISPUTED；deactivate 后 tombstone 保留（不被静默删除） |
| 独立复审 PASS + m0 profile 全绿 | m0 profile 18/18 deterministic checks PASS（本机 Windows：ruff/mypy strict/dependency-boundaries/pytest 1448/TS 全套/validate_bundle/governance/learning/hook evals）；独立 recheck 见 `.cursor/plans/rechecks/`（完成后追加） |

## 补充验证（provenance 测试套件 + 编排集成）

- `tests/application/evidence/test_provenance.py`：VERIFIED 升级前置（gate verdict PASS、evidence 可解析、source 已登记）；Agent 自述不能升级；register_session_result 登记 GENERATED SourceRecord + 合并 Claim/relations。
- `tests/e2e/test_claim_verification.py`：gate PASS → ledger 中全部 Claim VERIFIED + relations 引用完整 + CLAIM_VERIFIED 事件（run_id/task_id/reviewer 审计）；ledger 未装配时安全降级（Claim 保持 PROPOSED，无事件）。
- `tests/contracts/test_evidence_ledger_contract.py`、`tests/contracts/test_retrieval_index_contract.py`：新增 Port 的 contract suite 经 registry 驱动（Fake + InMemory 双实现）。

## 架构不变量核对（AGENTS.md §8 / M10 Architecture Invariants）

1. ToolResult/Agent output 不直接成为可信 Evidence：SourceRecord trust_label=GENERATED 显式非可信；VERIFIED 需 gate PASS + 已登记 source（provenance 套件锁定）。
2. Chat summary 不进入长期 Memory：唯一写入入口 = gate pipeline → MemoryStore.commit；应用层无其他 MemoryStore 消费路径；Fake 白名单为防御纵深。
3. VERIFIED Claim 必须追溯合法 Evidence：`promote_claim_to_verified` 强制 evidence 解析 + source 登记。
4. Memory 写入必须经过 proposal + provenance/policy gate：`commit_memory` 阶段链；三类拒绝路径测试。
5. Negative scientific result 是一等研究事实：NEGATIVE_RESULT 用例（写入/检索/contradiction/tombstone）。
6. Derived index 是 disposable projection：rebuild 等价、clear 后重建、checker 只读、修复=全量 rebuild（绝不反向修改 canonical）。
7. 不绑定 embedding/vector DB：`InMemoryRetrievalIndex` 确定性 token 检索，无 embedding 依赖；search 语义化记录为 M12 前评估的未来依赖。
8. MemoryStore 不拥有 Claim/Evidence truth：`EvidenceLedger` 独立 Port；Memory gate 只经 ledger 校验 provenance。
9. Writer/Reviewer/Runtime 不绕过 gate：phase_runner 只经 `promote_claim_to_verified`（authorized reviewer 标识）与 gate pipeline。
10. 不重复建立第二套模型：复用 M1 Domain 实体（SourceRecord/Claim/Evidence/EvidenceRelation/MemoryRecord/MemoryWriteProposal）、M5 PolicyEvaluator/EventPublisher Port、ADR-0018 Native Policy。

## Domain / API / Port 变化

- 新增 Port：`EvidenceLedger`、`RetrievalIndex`（inward-owned，M10 范围内最小 contract）；`packages/application/ports/__init__.py` 与 contract registry 同步（17 Port 名）。
- Domain 增量（向后兼容默认值）：`MemoryRecord.active: bool = True`；`MemoryWriteProposal.supersedes: list[str]`。
- `MemoryStore` Port 增量：`deactivate`（canonical tombstone，M10 lifecycle 语义）；FakeMemoryStore 同步。
- 事件清单 32→34：`claim.disputed`、`memory.deleted`；`docs/architecture/EVENT_MODEL.md` §1 与 `tests/domain/test_m5_domain_increments.py` DOCUMENTED_EVENT_TYPES 同步。
- 编排注入面：`OrchestrationDependencies`/`PhaseRunnerDeps` 增 `ledger: EvidenceLedger | None`（None=安全降级，不破坏现有 M7 测试 wiring）；`register_session_result` 签名改为 `RegistrationDeps` 参数对象（PLR0913 合规）；`_record_usage` 提取至 `usage_recording.py`（单文件 ≤300 行约束）。

## 技术债记录（BACKLOG 同步）

- EvidenceLedger 持久化（P1 → M14）：MVP 为进程内 Fake；跨 run 持久化落 PostgreSQL Canonical State 属 M14。
- RetrievalIndex 持久化 / 真实 embedding（P2 → M12 前评估）：确定性 token 检索仅证明可重建投影；语义检索与 embedding provider 绑定为 future dependency，不实现。

## 安全 / 凭据变化

无新增凭据域、无网络/外部服务依赖；gate 事件 payload 只含 memory_id/claim_id/evidence_id/relation 等审计标识（无 secret、无内容摘要）。

## M12 Readiness（MVP 判定依赖）

- M12 需要“研究结论有证据支撑、记忆可信”：M10 已交付证据账本（EvidenceLedger）、Claim 升级与矛盾处理、Governed Memory gate 与 lifecycle、可重建检索投影；M12 集成点 = 真实 run 的 claim 升级与记忆写入复用 M10 use case，无阻塞。
- M12 阻塞项不在 M10 范围：真实 relay 链路 usage 归账（P1，M12 清偿）、M8 工具面、M11 评测面。

## 验证命令（实际执行证据）

- `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → PASS（18/18 deterministic checks）
- `uv run --frozen --no-sync python -B -m pytest -q` → 1448 passed（含新增 M10 套件 88 tests）
- `uv run --frozen --no-sync ruff check packages adapters tests` → All checks passed
- `uv run --frozen --no-sync mypy packages adapters tests` → Success（308 source files）

## 独立复审记录（2026-08-15）

独立复审不采信开发阶段结论，全部重新从仓库事实与对抗性执行证据建立。
发现 5 项缺陷并已修复（详见 `tests/application/memory/test_gate_adversarial.py`
与 `tests/application/evidence/test_contradiction.py` 新增回归）：

| 缺陷 | 分类 | 根因 | 修复 |
| --- | --- | --- | --- |
| `supersede_memory` 绕过 MemoryWriteProposal gate 直调 `store.commit`（未授权 provenance + policy DENY 仍可入账） | BLOCKER | lifecycle use case 无 gate 装配点 | `supersede_memory` 增 `gate_deps`/`curator_approved`，经 `commit_memory` 阶段链提交；拒绝/失败不产生新记录 |
| `FakeMemoryStore()` 空白名单放行任意 provenance 直写 | BLOCKER | 防御纵深缺失（空集合被解释为放行） | 空 allowed_sources = deny-by-default；同 id 重复 commit 拒绝（防静默覆盖/事件风暴） |
| VERIFIED Claim 可绕过 `promote_claim_to_verified` 直写（ghost evidence / 未登记 source） | BLOCKER | 不变量只在升级函数内，canonical 登记面不设防 | `register_claim`/`update_claim` 强制 VERIFIED Claim 每条 relation 的 evidence 与 source 已登记（Port 契约同步声明） |
| REFUTES 争议证据无需已登记 source | MAJOR | contradiction use case 缺 provenance 前置 | REFUTES 的 evidence source 必须已登记，否则拒绝且不改 Claim 状态 |
| contradiction check 宽异常把 store 故障误判为"引用不存在"；commit 返回记录与提案不一致无校验；secret 样式内容原样入账 | MAJOR | 错误分类吞没 + 无 commit 前脱敏 | 只把 InvalidInputError 映射为引用缺失，其他 PortError 透传；`_verify_committed_record` 校验 adapter 返回；commit 前复用 `domain.redaction` 脱敏（sanitize before commit） |

### 并发边界（诚实记录）

M10 为单进程语义：Fake 内存实现 + 同 id 重复 commit 拒绝。跨进程并发
（同提案竞争 commit、delete vs update、rebuild vs mutation）依赖 M14
PostgreSQL 事务语义，已在 `BACKLOG.md` 登记为 P2→M14，不在 M10 范围。

### 复审验证证据

- `pytest tests/application/memory tests/application/evidence tests/contracts/test_evidence_ledger_contract.py tests/contracts/test_retrieval_index_contract.py tests/contracts/test_ports_persistence.py tests/e2e/test_claim_verification.py` → 103 passed（含新增 16 项对抗性回归）
- 对抗性探测脚本（10 探针，复审现场构造）：修复前 8 项可复现缺陷；修复后全部按预期拒绝/透传/脱敏
- ruff/mypy strict 覆盖修改文件全绿

### 兼容性风险清偿（2026-08-15）

| 风险 | 清偿方式 | 验证 |
| --- | --- | --- |
| `supersede_memory` 的 `gate_deps=None` 回退直调 `store.commit`（无治理路径存活） | `gate_deps` 改为必填 keyword-only，删除回退分支；唯一提交路径 = `commit_memory` gate 阶段链 | `tests/application/memory/test_lifecycle.py` supersede 用例全部经 gate 提交；全仓无 `supersede_memory` 无参回退调用方 |
| `FakeMemoryStore` 空构造 deny-by-default 语义缺契约级锁定 | `tests/contracts/test_ports_persistence.py` 新增 `test_empty_allowlist_denies_commit` 与 `test_duplicate_commit_rejected`（防实现回退为放行 / 防静默覆盖回归） | 契约套件 + 应用层对抗回归双重锁定 |

## 下一项任务

M10 停在阶段边界。并行组 1 剩余：M11（Evaluation Plane）；汇聚门
IG-1（M12 entry）需 M8+M9+M10+M11 全部独立复审通过。