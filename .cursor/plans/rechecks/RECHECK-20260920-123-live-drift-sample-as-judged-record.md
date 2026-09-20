---
id: RECHECK-20260920-123
plan_id: PLAN-20260920-123
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-009-cycle3
baseline_ref: 3f90fd0
checked_head: 3f90fd0
---

# RECHECK-20260920-123 — 漂移实测样本成为可判记录（EC-03 复检）

## 检查范围

**不采信实施叙述**：本复检自己解析 runbook、自己重算判定、自己**压**判据，
并逐条核对「文档写的」与「代码算的」是不是同一个东西。

- **A 判据面**：`tests/architecture/python/test_live_drift_sample_same_source.py`
  是否**真的**在判（不是恒绿、不是空转）；
- **B 重算面**：文档写的 `MATCH` 是否**等于**两个值代入 `assess_model_drift` 的结果；
  以及「判定函数只有一处」是否属实；
- **C 读面同源面**：读面的 drift 是否**真的**由同一个域函数产生；
- **D 反证面**：改坏样本是否**真的**红、复原是否**真的**绿、有无残留；
- **E 门禁面**：定向套件 + 全量 m0（CI 同形配置）+ 治理；以及 **CI 的反馈**。

## 检查结果

### A 判据面（8 checks 全绿；并且**压**过两条不同的路径）

`pytest tests/architecture/python/test_live_drift_sample_same_source.py tests/architecture/python/test_runbook_same_source.py -q -p no:randomly`
⇒ **18 passed in 0.95s**（本文件 8 条 + 既有的 runbook 判据 10 条）。

**判据不空转**，两条独立的可压路径都实测过：

| 压法 | 期望 | 实测 |
| --- | --- | --- |
| 改坏样本值（见 D） | 红，且**只有**重算那条红 | ✅ `1 failed, 7 passed`，红的正是 `test_documented_state_matches_a_fresh_assessment` |
| 解析路径遇到**不存在的标签** | 抛错并**点名**缺哪个标签（不静默返回空串） | ✅ `the runbook sample no longer has a row labelled '不存在的标签'` |

第二条尤其重要：如果解析失败静默返回空串，「判据没在看」就会伪装成「判据通过」。
`_cell()` / `_token()` 都对缺失**点名报错**，因此这个伪装路径**不存在**。

另外核对：解析四个标签的实际取值（与 cycle 1 的记录一致）
`run id = 142f7e77-cd4d-4044-a953-79296509fd54` / `返回 = agnes-2.5-flash` /
`声明 = agnes-2.5-flash` / `判定 = MATCH`。

### B 重算面（文档 == 重算）

| 项 | 核对方式 | 结论 |
| --- | --- | --- |
| 文档写的判定 | 从 §6 按标签解析 `漂移判定` 单元格 | `MATCH` ✅ |
| 重算的判定 | `assess_model_drift('agnes-2.5-flash', 'agnes-2.5-flash').state.value` | `MATCH` ✅ |
| 声明值的出处属实 | 读 `examples/config/models.yaml` 的 `agnes_flash.model_name` | `agnes-2.5-flash`，与 §6 括号里写的一致 ✅ |
| 判定函数**只有一处** | `rg` 全仓 `assess_model_drift` 的定义点 | 仅 `packages/domain/model_drift.py:46` ✅ |
| 三态口径属实 | 读 `packages/domain/enums.py:155-167` | `MATCH`/`DRIFT`/`UNKNOWN` 三态，且明写「未知**不等于**无漂移」✅ |
| `UNKNOWN` **不算**漂移 | `packages/domain/model_drift.py:33-35` + 判据内实测 | `is_drift` **只为** `DRIFT` 为真 ✅ |

### C 读面同源面（读面确由同一域函数产生）

| 项 | 核对方式 | 结论 |
| --- | --- | --- |
| 读面调用同一个函数 | `services/api/routers/models.py:24` 的 import + `:151` `drift=drift_dto(assess_model_drift(model.model_name, result.returned_model_name))` | ✅ |
| 没有并行的 `==` 比较 | 判据断言 import 行**在**文件里（防有人改成手写比较） | ✅ |
| DTO 字面量三态齐全 | `services/api/dto/models.py:77` `Literal["MATCH","DRIFT","UNKNOWN"]` 与域枚举逐字一致 | ✅ |

⇒ 「读面说 MATCH」**不是**靠人写对表格维持的：它是同一个纯函数的输出，判据把这条钉住。

### D 反证面（**先红后绿**，实测，两次运行留证）

| 步 | 动作 | 观察 |
| --- | --- | --- |
| 1 | 把 §6 的 `| 返回 model 名 |` 单元格由 `` `agnes-2.5-flash` `` 改成 `` `agnes-2.5-flash-drifted` ``（**仅此一处**） | 判据 **RED**：`1 failed, 7 passed`；消息 `the runbook says 'MATCH' but re-deriving from declared='agnes-2.5-flash' / returned='agnes-2.5-flash-drifted' gives 'DRIFT'` —— 且**同一文件其余 7 条仍绿** ⇒ 定位精确 |
| 2 | 把该行改回 `agnes-2.5-flash` | 判据 **GREEN**：`18 passed in 0.95s` |
| 3 | 复核 `git diff docs/integration/LIVE_MODEL_RUNBOOK.md` | 只剩 WP4 的**意图内**改动（判定行改写 + 新增「不持久化」边界段），**无**残留漂移值 ✅ |

⇒ 判据**真的**对样本敏感；「文档里的判定是手写死的」这条腐坏路径**已被堵住**。

### E 门禁面

- 受影响定向套件（`test_live_drift_sample_same_source` + `test_runbook_same_source`
  + `test_protocol_vocabulary` + `tests/domain/test_model_drift.py` + `tests/api/test_models_api.py`）
  ⇒ **47 passed**。
- `ruff check` / `ruff format --check` / `mypy`（新增/改动文件）⇒ 全绿（见 PLAN 的 WP5 证据）。
- 全量 m0（23 checks，**CI 同形配置**：`LLM_MAIN_KEY=""` 挡住凭据 + 测试 DSN pin）
  ⇒ 见下方「m0 结果」小节与 GOAL-009 迭代日志。
- **CI 反馈**：本轮推送的 CI 结论记入下方「CI 台账」小节（**不猜测绿**）。

#### m0 结果

命令（**CI 同形配置**：挡住本机凭据 + pin 测试 DSN，复现「CI 无 `.env`、无凭据」的条件）：

```text
LLM_MAIN_KEY="" RESEARCHOS_POSTGRES_DSN=<测试 DSN> RESEARCHOS_DATABASE_URL="" DATABASE_URL="" POSTGRES_DSN="" \
  uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py \
  --profile m0 --keep-going
```

**结果：`PASS: profile=m0; 23 deterministic checks`**（`4221 passed, 12 skipped`，`589.50s`；`FAIL` 计数 **0**）。
**一次跑完，无 stale 轮次、无红**（本轮新增文件先过了 `ruff` / `format` / `mypy` 再起 m0，
避免了 cycle 2 那种「m0 读到未修完的文件」的 stale 红）。

## Warnings（不阻断，如实登记）

- **W-1 样本是「一次观测」，不是模型属性。** 判据判的是「这一次的两个值代入判定函数得到什么」，
  **不**判「该端点永不漂移」。§6 已写死这条边界，`docs/integration/LIVE_MODEL_RUNBOOK.md`
  的「证明力边界」段也写了「单次样本**不能**把三态里的『一致』升级成永久结论」。
  本 cycle **没有**新增任何 live 调用——样本就是 cycle 1 的同一次 probe。
- **W-2 反证的边界：它不能发现「自洽的假样本」。** 若有人把**声明值与返回标识同时**改成另一对
  **彼此相等**的值，重算仍得 `MATCH`，判据不会红。兜住它的是 run id 交叉引用：
  样本行必须引用一个**在 `RECHECK-20260920-121` 里出现过**的 run id（判据已断言），
  所以假样本要么沿用真 run id（与 run id 对应的观测不符，靠人读得出），
  要么换一个 run id（判据当即红）。**这条仍是「同一 run 的记录」而非新证据**，如实登记。
- **W-3 判据对格式有耦合。** 它按**固定标签行**解析 §6；将来把标签行改名（例如
  「返回 model 名」改写成别的措辞）会让判据红。这是**设计意图**（标签是判据与文档之间的契约），
  但确实会让「只看 CI 红绿」的人误以为坏了。**处置口径**：改标签必须**同时**改判据，
  不得为了让判据不红而放宽它。
- **W-4 「漂移未持久化」只有文档口径，没有判据把守。** 判据只断言那句话**在场**
  （`不持久化`），**不**证明读面真的不持久化（那需要跨进程实测）。如实登记。
- **W-5 前端读面未被本判据覆盖。** `apps/web` 里渲染 drift 的组件**不在**本判据范围内
  （本判据钉的是 API 读面与域函数的同源）。若将来前端另写一套判定，本判据**不会**红。
- **W-6 CI 台账**：本轮推送的 run id / 结论记入下方小节；**未跑到终态的不记**。

## 结论

**result: PASS_WITH_WARNINGS**。EC-03 达到终态：漂移样本从**散文**变成**判据能重算的事实**
（改一个字符即红，复原即绿，无残留）、**读面同源**被钉住（防并行比较，防三态字面量漂移）、
`UNKNOWN ≠ 无漂移` 被实测钉住、两条证明力边界（单次一致 ≠ 永不漂移 / 判定不持久化）写在样本旁边。
**全程未改任何门禁或断言强度**；**未新增任何 live 调用**。
PLAN-20260920-123 可置 **DONE**。

**Warning 不阻断的理由**：W-1/W-2/W-4/W-5 是**如实登记的证明力边界**（判据管到哪、不管到哪），
**不是**被掩盖的失败；W-3 是**有意**的判据-文档契约；W-6 是 CI 台账的填写规则。
