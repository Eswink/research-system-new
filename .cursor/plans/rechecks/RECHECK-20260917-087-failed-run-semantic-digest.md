---
id: RECHECK-20260917-087
plan_id: PLAN-20260917-087
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle4
baseline_ref: 186963c
checked_head: 65d1ebd+worktree
---

# RECHECK-20260917-087 — 失败 run 的冻结语义 digest（GOAL-004 cycle 4 = EC-04）

## 检查范围

PLAN-20260917-087 声称的交付面：① `manifest.frozen` payload 带**语义 digest**
（排除 `frozen_at`，与快照 digest 同一 producer）；② 执行期失败收敛（`except ValueError`）
的 run 行与成功路径**同判据**地带上 `manifest_semantic_digest`，落行走**同一个**域方法
`ResearchRun.with_manifest`；③ 读面（`GET /runs/{id}` 与列表）暴露该字段；④ "从事件链
重放 run 行"能补齐这项（重放用例走产品代码的同一个映射）；⑤ 旧事件/未冻结 run 读回 None
（不回填、不猜测）。

**未覆盖**（见告警）：本轮不做历史回填（旧 `manifest.frozen` 事件没有 `semantic_digest`，
对应 run 行读回 None，重建行为与今天一致）；`FAILED → 重建续跑` 的**执行期**结局不在本轮
判据内（m12 协议在执行期本身会失败，属 EC-06 的缺口）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 事件带语义 digest（AC-01） | 应用用例 3：payload 的 `semantic_digest` 与 `RunManifest.semantic_digest()` 逐字相同、`!= digest`、字段漂移会改它；`EVENT_MODEL.md` 写明 payload 键 | PASS |
| 失败收敛同判据（AC-02） | API 用例 2：`run_ready_client` 下 m12 协议冻结成功、执行期收敛 `FAILED`，该行经**同一个断言函数**（`_assert_frozen_semantic_digest`）成立——非空、`sha256:` 前缀、`!= manifest_digest`；成功路径（基础夹具 + 受控模板）用同一函数同样成立，且两条同协议 run 的语义 digest 不同（覆盖 `run_id`，非常量） | PASS |
| 读面如实暴露（AC-02/AC-03） | API 用例：`GET /runs/{id}` 的 `manifest_semantic_digest == str(row.manifest_semantic_digest)`；`docs/api/openapi.m13.json` 重生成（+11 行）、`apps/web/src/api/types.ts` 与浏览器夹具同步 | PASS |
| 事件相等（AC-03） | API 用例：`GET /runs/{id}/events` 的 `manifest.frozen` payload `digest`/`semantic_digest` 分别等于 run 行的两个 digest | PASS |
| 重放一致（AC-03） | API 用例：只凭事件 payload（`FrozenManifestRefs.from_payload`）+ 产品域方法（`with_manifest`）重建 run 行的四项冻结引用（快照 digest / 语义 digest / `pricing_version` / `pricing_digest`）与 canonical 行完全相同，且语义 digest **非空** | PASS |
| 真的被消费（AC-03） | API 用例：把这条 FAILED run 停成 `PAUSED` 后 `POST /runs/{id}/resume` ⇒ 冻结语义守卫**不再**报 `lacks a semantic digest`、也不报 `drifted`，重建一路走到执行（该协议自身的执行期失败 `phase declares no task contract`，见 EC-06）；换一个语义 digest ⇒ `continuation=NONE` + `drifted`（守卫既用它放行也用它拒绝） | PASS |
| 诚实边界（AC-04） | API 用例：preflight WARN 被拒（从未冻结）⇒ `manifest_digest` 与 `manifest_semantic_digest` 同为 None；`from_payload` 对非字符串/空串一律当作"没有这一项"（旧事件读回 None，不回填） | PASS |
| 门禁与记录（AC-05） | 定向：`tests/api` 全量 **418 passed**（含新增 7）；`tests/domain tests/application tests/contracts tests/postgres tests/e2e` 一次复跑 **1629 passed / 4 skipped**（197.19s）；web 门（lint 0 error / typecheck / unit 76 / build / stub e2e 83 / live e2e 36）全绿；m0 见下；RECHECK-087 + MEM-062 + GOAL/ALL_PLAN 记账 | PASS |

## 反证与实测

- **反证 A（事件 payload 键）**：把 `frozen_payload` 里的 `"semantic_digest"` 去掉 ⇒
  `test_frozen_payload_semantic_digest.py`（3 条）全红 + API 侧 `test_a_failed_run_carries_the_frozen_semantic_digest`、
  `test_the_frozen_event_carries_the_same_semantic_digest`、
  `test_the_run_row_is_replayable_from_the_event_chain`、
  `test_the_converged_digest_is_what_the_drift_guard_consumes` 全红 = **7 failed / 3 passed**。
- **反证 B（收敛分支参数）**：把 `FrozenManifestRefs.apply` 的语义 digest 参数改成 `None`
  ⇒ **3 failed / 4 passed**，其中守卫那条的失败文本正是**改动前的原缺口**：
  `frozen manifest lacks a semantic digest; fork run or revision required`
  ——这条缺口以前只在文档里，现在有可复跑的反证。
- **反证暴露了一处假绿（已修）**：反证 A 首跑时"重放一致性"用例**仍然通过**——两侧同时为
  None 时相等成立。修法是把"重放出来的语义 digest 非空"也钉进断言（判据只增强），
  之后再跑反证 A 该用例即红（7 failed，而不是 6）。这一条已进 MEM-062 的"踩过的坑"。
- **调试实录（测试替身 vs 产品缺陷）**：首跑时"守卫放行"那条用例报 `drifted`。用临时探针
  （spy `freeze_manifest`）打印重建前后 manifest 字段差异，定位到**用例的 `_park` 替身**
  漏复制 `pricing_version`/`pricing_digest`（定价引用参与语义 digest）——是守卫在正常工作，
  不是产品缺陷。修替身（补两个字段），**未动产品代码、未放宽断言**。
- **`_start` 夹具事实**：m12 协议在 `run_ready_client` 下"冻结成功 → 执行期失败收敛"，
  在基础 `client` 下同协议因未 pin 而**冻结被拒**（`manifest_digest is None`），所以
  "同判据"用例把成功侧放在基础夹具、失败侧放在 run-ready 夹具，两侧调**同一个断言函数**。
- **m0 复跑抓到的类型收窄问题（已修）**：复跑时 `python/typecheck` 红在
  `services/api/run_execution.py:109`（`Digest.parse` 收到 `str | None`）——原因是把
  `if self.digest is None:` 改写成"语义等价"的 `if not self.frozen:` 后 mypy 不再收窄。
  处置：恢复显式判空 + **删掉未被消费的 `frozen` 属性**（不是加 `# type: ignore`），
  复跑 typecheck 绿。

## 告警

- **W-1（旧事件无该键，不回填）**：本轮之前的 `manifest.frozen` payload 没有
  `semantic_digest`，对应 run 行读回 None ⇒ 那些 FAILED run 的重建仍被守卫以
  `lacks a semantic digest` 拒绝（与今天一致）。要改变这一点需要一次**显式回填**
  （重算 manifest 或标注"可重建"），属产品决策，本轮不做。
- **W-2（`FAILED → 重建` 的执行期结局仍是缺口）**：本轮的判据停在**冻结语义守卫**
  （不再被 `lacks a semantic digest` 挡住、并已走到执行）。重建后续跑若在执行期再失败，
  run 会被留在 `RUNNING` 且无补偿——这正是 EC-06（`resume_paused` 失败补偿）的范围；
  本轮的用例对该事实的耦合点是指令 `assert "task contract" in note`，EC-06 收口后这条
  断言需要同步更新。
- **W-3（`from_payload` 的取值收窄是"静默丢项"）**：非字符串/空串一律读成 None（不抛错）。
  好处是旧事件、异构 payload 都能安全读；代价是**写错键名**也会静默变成"没有这一项"，
  只能靠用例钉住（本轮三条 payload 用例就是钉这个）。调用方若需要区分"缺失"与"写坏"，
  得自己校验 payload 结构。
- **W-4（读面字段的诚实边界已写进文档）**：`manifest_semantic_digest` 非空**不保证**
  重建成功（目录/契约漂移仍被拒）——已写进 `docs/api/CONTROL_PLANE_API.md` 的 Runs 段。
- **W-5（实现细节：只在守卫里"语义等价"的写法会被 mypy 拦）**：`apply` 的提前返回若写成
  `if not self.frozen:`（属性谓词）会丢 `str | None` 的类型收窄 ⇒ `python/typecheck` 红
  （`Argument 1 to "parse" of "Digest" has incompatible type "str | None"`）。最终保留
  `if self.digest is None:`，并**删掉没有被消费的 `frozen` 属性**（AGENTS/MEM-061 的
  "声明要么有消费者、要么被点名"同样适用于代码）。这条是 m0 复跑抓出来的，不是先验判断。

## 门禁

- 定向：`tests/api` **418 passed**（54.27s；新增 `test_failed_run_semantic_digest_api.py`
  7 passed）；`tests/application/run_orchestration/test_frozen_payload_semantic_digest.py`
  **3 passed**；`tests/domain tests/application tests/contracts tests/postgres tests/e2e`
  一次复跑 **1629 passed / 4 skipped**（197.19s；postgres 用例实跑非 skip，DSN 按固化配方）。
- web 门：`pnpm run lint` 0 error（1 条既有软告警：`live-api-workflow.spec.ts` 403 行）；
  `pnpm run typecheck`（根 + apps/web）绿；`apps/web` unit **76 passed**；`pnpm run build` 绿；
  stub e2e **83 passed**（4.9m）；live e2e **36 passed**（48.1s）。
- m0：三次实跑的完整序列——**①24/25**：唯一红项 `framework/validate` 的原因是
  **MEM-062 先于 RECHECK-087 写入**（治理交叉引用要求复检文件先存在），全量 pytest 本身
  3835 passed / 10 skipped 无红；**②24/25**：补齐记录后红项变成 `python/typecheck`
  （`run_execution.py:109` 的 `str | None` 收窄问题，见"反证与实测"末条，已修）；
  **③PASS**：`PASS: profile=m0; 23 deterministic checks`（全量 pytest **3835 passed /
  10 skipped**，477.88s，exit 0）。两次红都定位到具体原因并修复**产品/记录**，未改门禁。
- 文档同源：`docs/architecture/EVENT_MODEL.md`（`manifest.frozen` payload 键）、
  `docs/api/CONTROL_PLANE_API.md`（Runs 段新增字段语义 + 诚实边界）。

## 结论

`manifest.frozen` 事件与 run 行的**冻结语义**在失败收敛路径上补齐了：payload 带
`semantic_digest`（与 `digest` 同一 producer），收敛分支经唯一的 payload→引用映射
（`FrozenManifestRefs.from_payload`）读回四项引用并用**成功路径同一个** `with_manifest`
落行；读面 `GET /runs/{id}` 暴露 `manifest_semantic_digest`；重放用例证明"只凭事件链"
能把 run 行的冻结引用原样重建。守卫真的在用它（换值 ⇒ `drifted`）。**反证双跑**证明
两半都不是"从不开火的守卫"。

结果为 **PASS_WITH_WARNINGS**：W-1（旧事件不回填）与 W-2（重建后续跑的执行期结局属
EC-06）是如实的范围边界，W-3/W-4 是读面与字段语义的边界登记。**未宣称"失败 run 现在都能
续跑"**：本轮只保证冻结语义事实在失败路径上不再丢失、且被同一个守卫消费。
