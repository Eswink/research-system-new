---
id: PLAN-20260920-123
slug: live-drift-sample-as-judged-record
title: 漂移实测样本成为可判记录：把 live 探到的「返回 model 名 vs 声明值」从散落的散文变成判据能重算的事实，并写明单样本证明力边界（EC-03）
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-009
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-009 cycle 3 = EC-03（漂移实测样本）。授权来源：2026-09-20 用户 goal 模式指令 frontmatter `authorization.ref` 第 (1) 条（live 调用**次数取最小必要**、不重复重跑）与 AGENTS.md §4（漂移必须可见；结论口径停在「可重复配置」）。**本 PLAN 不发起任何真实调用**：样本复用 cycle 1 的**同一次** live probe（run `142f7e77-cd4d-4044-a953-79296509fd54`），判据全部离线可判。不改 Policy/eligibility、不新增依赖、不改 pin、不把凭据写进 CI、不修改任何门禁或断言强度。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-123-live-drift-sample-as-judged-record.md
memory_entries: MEM-097
---

# PLAN-20260920-123 — 漂移实测样本成为可判记录（GOAL-009 cycle 3 = EC-03）

## 目标

把 cycle 1 带出来的漂移样本从**散文**变成**判据能重算的事实**：

1. **样本可判**：runbook 里的样本行（声明值 / 返回标识 / 判定 / run id / 时间）由**判据**
   重新代入 `assess_model_drift` **重算**——改一个字符就红，而不是「文档里写着 MATCH」；
2. **与读面同源**：判据同时钉住**读面**的 drift 字段确实由**同一个**域函数算出
   （`services/api/routers/models.py` 的 `_probe_result_dto`），防止将来出现「并行的 `==` 比较」；
3. **边界如实**：单次样本的证明力边界（`一致` ≠ 永不漂移）、以及**漂移未持久化**
   （读面只在**探测过的那个进程**里显示它）——两条都写成可判/可读的事实；
4. **不新增调用**：样本是 cycle 1 的同一次 probe，**不额外发起 live 调用**。

## 先探明再动手（cycle 1 与本次只读勘察已确认的事实）

1. **样本已在手**（cycle 1，**无凭据值**）：run id `142f7e77-cd4d-4044-a953-79296509fd54`；
   probe 段 `verified and ok`；`returned_model_identifier = agnes-2.5-flash`；
   声明值 `examples/config/models.yaml` 的 `agnes_flash.model_name = agnes-2.5-flash`；
   判定 **一致**；口径 `REPEATABLE_CONFIGURATION`。
2. **判定函数只有一处**：`packages/domain/model_drift.py` 的 `assess_model_drift`（纯函数，三态），
   `ModelDriftState` 的完整口径在 `packages/domain/enums.py`（「未知 ≠ 无漂移」）。
3. **读面路径**：`services/api/routers/models.py` 的 `_probe_result_dto` 里
   `drift=drift_dto(assess_model_drift(model.model_name, result.returned_model_name))`
   ⇒ 读面的 drift **就是**这个函数的结果。
4. **三态离线已被覆盖**：`tests/api/test_models_api.py` 已有 MATCH / DRIFT / UNKNOWN 三条
   （用 `FakeModelGateway`）⇒ 本 PLAN **不需要**再证三态可达，需要证的是
   **live 样本本身**被如实记录且可重算。
5. **样本当前只在散文里**：`docs/integration/LIVE_MODEL_RUNBOOK.md` §6 的表格 +
   `RECHECK-20260920-121`。**没有任何判据**会在样本被改错时变红——这正是本 PLAN 要补的洞。

## 口径（先写死）

- **样本 = 一次观测，不是模型属性**。判据只判「这一次的两个值代入判定函数得到什么状态」，
  **不**判「该端点永不漂移」。
- **`UNKNOWN` 不是漂移**（`is_drift` 只为 `DRIFT` 为真）；判据必须把这条钉住。
- **不新增 live 调用**；样本来源写死为 cycle 1 的 run id。
- **判据判同源，不判文笔**：只核对「值与重算结果」，不核对措辞。

## 验收条件

- **AC-1 样本可重算**：新增判据从 runbook §6 **解析**出（声明值, 返回标识, 判定, run id），
  代入 `assess_model_drift` **重算**，断言重算状态 == 文档写的判定。
- **AC-2 反证**：把 runbook 里的返回标识改成另一个值 ⇒ 判据 **RED**（重算得 `DRIFT` 而文档写
  `MATCH`）；复原 ⇒ **GREEN**。
- **AC-3 读面同源**：判据断言 `services/api/routers/models.py` 的 drift 由
  `assess_model_drift` 产生（防并行比较），且 `ModelDriftStateLiteral` 与域枚举三态一致。
- **AC-4 边界如实**：runbook §6 里能读出「单次一致**不**等于永不漂移」与「漂移未持久化」
  两条边界；判据对这两条**只在场**判（不判文笔）。
- **AC-5 run id 可追溯**：样本行里的 run id 与 cycle 1 的记录
  （`RECHECK-20260920-121`）一致——防止样本被换成另一个 run 却没人发现。
- **AC-6 本地门禁绿**：受影响定向套件 + `make validate-all`（m0，CI 同形配置）+ 治理。

## 实施清单

- [x] WP1 读面同源核对（AC-3）：读 `_probe_result_dto` 与 `ModelDriftStateLiteral`。
- [x] WP2 写判据 `tests/architecture/python/test_live_drift_sample_same_source.py`（AC-1/3/4/5）。
- [x] WP3 反证 AC-2（先红后复原，两次输出留证）。
- [x] WP4 把 runbook §6 的样本行改成**可解析**形态（判定写成状态字面量 + 保住两条边界行）；
      同步 `docs/integration/LLM_ENDPOINTS.md` §8（Drift Fingerprint）如需要。
- [x] WP5 本地验证（AC-6）→ RECHECK → DONE → ALL_PLAN → 回写 GOAL-009 → commit/push/CI。

## 验收条件对照

| AC | 判据 | 结论 |
| --- | --- | --- |
| AC-1 样本可重算 | 判据从 §6 解析三元组并重算 | ✅ `test_documented_state_matches_a_fresh_assessment` |
| AC-2 反证 | 改坏 ⇒ RED，复原 ⇒ GREEN | ✅ 实测 `1 failed, 7 passed` → `18 passed`，`git diff` 无残留 |
| AC-3 读面同源 | 判据钉住 router 用同一域函数 + DTO 三态齐全 | ✅ 3 条用例 |
| AC-4 边界如实 | 两条边界在场（单次一致 ≠ 永不漂移 / 未持久化） | ✅ 2 条用例 |
| AC-5 run id 可追溯 | 样本 run id 必须出现在 `RECHECK-20260920-121` | ✅ 1 条用例 |
| AC-6 本地门禁绿 | 定向套件 + m0（CI 同形）+ 治理 | ✅ 47 passed；m0 **23/23**（4221 passed / 12 skipped）；`validate.py` 绿 |

## 证据

（执行时逐条填入。）

### WP1 读面同源

实测（只读，2026-09-20）：

- `services/api/routers/models.py:24` `from packages.domain.model_drift import assess_model_drift`；
  `:151` `drift=drift_dto(assess_model_drift(model.model_name, result.returned_model_name))`
  ⇒ 读面 drift **就是**域函数的结果，**没有**第二处 `==` 比较。
- `services/api/dto/models.py:77` `ModelDriftStateLiteral = Literal["MATCH", "DRIFT", "UNKNOWN"]`；
  `:80-89` `ModelDriftDto{state, declared_model_name, returned_model_name, detail}`；
  `:82-85` 文档串已写「`UNKNOWN` = 未探到 —— **不等于**无漂移」。
- `packages/domain/enums.py:155-167` `ModelDriftState(StrEnum)` 三态与 DTO 字面量**逐字一致**；
  `packages/domain/model_drift.py:33-35` `is_drift` **只为** `DRIFT` 为真。

⇒ 这三条被 WP2 的判据钉住（AC-3）。

### WP4 文档可解析化

`docs/integration/LIVE_MODEL_RUNBOOK.md` §6 的样本行改为固定标签 + 状态字面量：

- 漂移判定行由「**一致**（实测返回标识 == 声明值）——见下「证明力边界」」改为
  「**`MATCH`**（一致）——…；由 `assess_model_drift` **重算**得出，判据见
  `tests/architecture/python/test_live_drift_sample_same_source.py`」⇒ 判据可按标签取到状态字面量。
- 新增一条边界段「**另一条边界（本节的样本与它无关，但必须一起读）**：漂移判定**不持久化**……」
  ⇒ AC-4 的第二条边界（第一条「单次一致 ≠ 永不漂移」原已在「证明力边界」段）。

### WP3 反证

2026-09-20 实测，两次运行的原始结论：

1. **改坏**：把 §6 的 `| 返回 model 名 | \`agnes-2.5-flash\` |` 改成
   `` | 返回 model 名 | `agnes-2.5-flash-drifted` | ``（仅此一处），
   `uv run --frozen --no-sync python -B -m pytest tests/architecture/python/test_live_drift_sample_same_source.py -q -p no:randomly`
   ⇒ **RED**：`1 failed, 7 passed`，失败点
   `test_documented_state_matches_a_fresh_assessment`，消息为
   `the runbook says 'MATCH' but re-deriving from declared='agnes-2.5-flash' / returned='agnes-2.5-flash-drifted' gives 'DRIFT'`。
   ⇒ 文档写死判定、而非重算的路径**已被堵住**：改样本必红。
2. **复原**：把该行改回 `agnes-2.5-flash`，同两道判据同跑
   ⇒ **GREEN**：`18 passed in 0.95s`；`git diff docs/integration/LIVE_MODEL_RUNBOOK.md`
   只剩 WP4 的**意图内**改动（判定行 + 新增边界段），**无**残留的漂移值。

反证的**边界（如实）**：它证明的是「样本值被改 ⇒ 判据红」，
**不**证明判据能发现「两个值被同时改成另一对**自洽**的假样本」——
后者由 AC-5 的 run id 交叉引用（对照 `RECHECK-20260920-121`）兜住，仍是**同一 run** 的记录，不是新证据。

### WP5 本地验证（AC-6）

- **定向套件**：`tests/architecture/python/test_live_drift_sample_same_source.py`
  + `test_runbook_same_source.py` + `test_protocol_vocabulary.py` + `tests/domain/test_model_drift.py`
  + `tests/api/test_models_api.py` ⇒ **47 passed in 2.03s**。
  其中本轮的**两道同源判据**单跑 ⇒ **18 passed in 0.95s**。
- **静态门**：`ruff check` ⇒ `All checks passed!`；`ruff format --check` ⇒ `1 file already formatted`；
  `mypy` ⇒ `Success: no issues found in 1 source file`。
- **全量 m0（CI 同形配置）**：`LLM_MAIN_KEY=""` + 测试 DSN pin
  （`RESEARCHOS_POSTGRES_DSN` = 测试 DSN，`RESEARCHOS_DATABASE_URL` / `DATABASE_URL` / `POSTGRES_DSN` 置空）
  ⇒ **`PASS: profile=m0; 23 deterministic checks`**（`4221 passed, 12 skipped`，`589.50s`，`FAIL` 0 条），
  **一次跑完无 stale、无红**（先过 ruff/mypy 再起 m0，避开 cycle 2 的 stale 红）。
- **治理**：`validate.py` 绿（PLAN/ALL_PLAN/RECHECK/GOAL 四件套一致）。

### 未新增 live 调用（如实）

本 cycle 的**全部**判据都是**离线**的：读 runbook、读仓库文件、调用纯函数。
样本来源写死为 cycle 1 的同一次 probe（run `142f7e77-cd4d-4044-a953-79296509fd54`），
**没有**发起任何真实调用、**没有**改绑、**没有**改 config、**没有**改门禁或断言强度。

### WP2 判据

`tests/architecture/python/test_live_drift_sample_same_source.py`（新增，8 个用例）：

- 按**固定标签行**解析 §6（`| 返回 model 名 |` / `| 声明 model 名 |` / `| 漂移判定 |` / `| run id |`），
  解析失败**点名缺哪个标签**（不猜、不用宽松正则）；
- 代入 `assess_model_drift` **重算**，断言 == 文档写的状态字面量；
- 断言 `is_drift` 与三态口径一致（`UNKNOWN` **不**算漂移）；
- 断言读面同源（router 里由 `assess_model_drift` 产出、无并行比较）+ DTO 字面量三态齐全；
- 断言 run id 与 `RECHECK-20260920-121` 的记录**一致**（AC-5）；
- 断言两条边界段**在场**（只判在场，不判文笔）。

与既有 `tests/architecture/python/test_runbook_same_source.py` 同跑 = `18 passed`。

## 状态历史

- 2026-09-20 建档：`driver=client-goal / owner=root-agent`。承接 GOAL-009 cycle 3（EC-03）。
  **不发起任何真实调用**：样本复用 cycle 1 的同一次 probe。
- 2026-09-20 **DONE**：WP1→WP5 全部完成，AC-1…AC-6 全中。
  `RECHECK-20260920-123` = **PASS_WITH_WARNINGS**（W-1…W-6）。
  **未改任何门禁或断言强度、未新增依赖、未改 pin、未发起任何真实调用。**

## 影响报告

**Domain / API / Schema**：**无变化**。不新增/修改域实体、DTO、路由或迁移；
本 PLAN **读**既有域函数与读面 DTO，只新增**判据**与**文档可解析性**。

**安全 / 凭据**：无新增信任面，**不发起真实调用**，样本不含凭据值。把「样品可重算」钉住
之后，「读面说 MATCH」不再是靠人写对表格维持的——这是 AGENTS §4 要的那种**可见性**。

**兼容性 / 迁移风险**：无迁移。**风险**：解析 runbook 表格的判据可能因格式微调而误红
⇒ 处置是让判据**只依赖标签行**（`| 返回 model 名 |` 这类固定标签）并在解析失败时**点名缺哪个标签**，
而不是用宽松正则去猜；**不得**为了让判据不红而放宽它。

**上游版本影响**：无。不新增依赖、不改任何 pin。

**下一项任务**：WP1 读面同源核对 → WP2 判据 → WP3 反证 → WP4 文档 → WP5 收口并回写 GOAL-009 的 EC-03。
