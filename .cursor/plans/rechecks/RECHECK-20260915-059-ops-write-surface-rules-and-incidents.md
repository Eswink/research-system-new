---
id: RECHECK-20260915-059
plan_id: PLAN-20260915-059
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-002-cycle5
baseline_ref: 05bcf04
checked_head: 05bcf04+worktree
---

# RECHECK-20260915-059 — ops 写面：告警规则 CRUD + 事故处置（GOAL-002 cycle 5 / EC-04）

## 检查范围

PLAN-20260915-059 声称的交付面：`OpsStore` 持久面（域 + Port + SQLite）、
7 条写/读规则端点（规则 CRUD、事故 declare/assign/close）、**写面被读面消费**的证据
（静音标记不隐藏、事故回链、候选扣减）、前端两页的写面板与 `pageSupport` 收敛、
stub/live e2e、`ops-alerts` / `ops-incidents` 设计基线。其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 状态机口径 | `packages/domain/ops_control.py`：OPEN→ASSIGNED→CLOSED，可重复指派，OPEN 可直接关闭；非法迁移抛 `InvalidTransitionError`（→409）；`Incident.open` 用 `!=` 比较（持久面解出的是普通 str，`is not` 不可靠）——该缺陷在首轮被用例抓出并修正 | PASS |
| 规则 CRUD 语义 | `tests/api/test_ops_control_api.py`：201 建规、PATCH 改名/启停/清空范围、DELETE 204 后 404、未知 id 404、非法 kind/severity 422、空补丁 422 | PASS |
| 事故处置语义 | 同文件：declare 201、assign 转 ASSIGNED、close 写 resolution 并转 CLOSED、**已关闭再处置 409**、空 assignee/resolution 422、未知 id 404 | PASS |
| 未配置即锁定 | 同文件：`deps.ops_store = None` 时读面 `rules_available=false`、写面 503 + 原因（不伪造成功） | PASS |
| **写面被读面消费（规则）** | `tests/api/test_ops_view_api.py`：规则命中后告警带 `muted=true` + `muted_by=<rule id>`，**告警条数不变**（静音不是隐藏），`muted_count` 与列表自洽；停用规则后标记消失 | PASS |
| **写面被读面消费（事故）** | 同文件 + 控制面用例：登记事故后来源 run 的告警带 `incident_id`；关闭后标记消失；已登记的 run 从 `candidates` 移出、留在 `incidents` | PASS |
| 读面口径改写是交付而非放水 | `tests/api/test_ops_view_api.py` 顶部注明：`rules_available` 由 False 变 True 是本轮 EC 的交付物（写面 + 装配），不是为过门禁改断言；用例同时把"不可用"路径移到显式 `None` 装配的用例里 | PASS |
| 装配两侧同源 | `services/api/composition.py`、`pg_composition.py` 的配置面 store 组各加一项；`tests/api/conftest.py` 与 `tests/api/run_fixtures._run_ready_sqlite_stores` 同侧加入 `SqliteOpsStore`（live harness 因此具备真实写链） | PASS |
| 全量 API 无回归 | `pytest tests/api -q` → **336 passed**（含 run-ready 装配引入 ops store 后的所有既有用例） | PASS |
| OpenAPI 快照一致 | `tools/gen_openapi.py` 重生成（+763 行）；新增路径断言 **5 条**；新增 `test_openapi_contains_ops_write_methods` 断言写方法集合（get/post/patch/delete 逐条比对） | PASS |
| 前端真的能写 | stub e2e `ops-write.spec.ts` 5 用例：静音标记仍列出两条告警；新建规则 → 静音计数 2；停用 → 回到 1；删除 → 0；候选登记 → 候选清空；指派 → 行内出现处理人；关闭 → 行内显示结论且**不再有处置动作** | PASS |
| 真实装配面同性质 | live e2e `live-ops-write.spec.ts` 3 用例（真实 uvicorn HTTP）：规则 POST/PATCH/422/DELETE/404；事故 declare→assign→close→**重复关闭 409**；告警读面 `rules_applied>0` 且 `muted_count` 与逐条 `muted` 自洽、`muted_by` 只在 muted 时出现 | PASS |
| 读面可用性口径同步 | `live-api-workflow.spec.ts` 的 ops 段由 `rules_available=false` / `workflow_available=false` 改为 `true` 并补 `candidates` 形状断言（旧断言已不成立）；细节链路由新 live spec 承担 | PASS |
| 清单单一来源仍成立 | 新增 live spec 只改 `tests/e2e/live-specs.ts` 一处；`--list` 复核 stub **50 tests / 13 files**、live **28 tests / 7 files** | PASS |
| 既有 e2e 未被搅动 | 全量 stub 套件 **50 passed**；全量 live 套件 **28 passed**（含 3 条新写链） | PASS |
| 设计基线 | `ops-alerts` / `ops-incidents` 的 win32（本地）与 linux（pinned noble 容器）重生成并目检：告警表 + 静音规则面板、事故登记表 + 候选表（含"登记为事故"按钮）渲染正确，无裁列/溢出 | PASS |
| 前端门禁 | 根 `npx eslint .` = 0 error（2 条既有 soft warning，`stub-routes.ts` 因拆分由 424 → 358 行）；web `tsc --noEmit` 通过；单测 76 passed | PASS |
| Python 门禁 | 本地 m0 共 **4 次**全部红过才绿：① `python/format-check`（用脚本手改的 `tests/api/test_ops_control_api.py` 未跑 `ruff format`）→ ② `python/tests` 的 50 行/函数上限（`test_openapi_contains_control_plane_paths` 加断言后 52 行）→ ③ `typescript/boundaries` 循环依赖（`OpsAlertRulesPanel` ↔ `opsViewColumns`）→ ④ 命名门禁（独立模块 `OpsChips.tsx` 的导出叫 `EnabledChip`，文件名须与唯一组件导出同名）→ 逐条修复后 **m0 = `profile=m0; 23 deterministic checks`** | PASS（先失败后修复） |
| 轮内自证的边界（本轮新发现） | 用 `scratch/cycle5-baseline-drift/measure.py` 按 Playwright 判据（pixelmatch，YIQ 阈值 0.2）量化"旧基线 vs 新渲染"：ops-alerts **1.02%**、ops-incidents **0.93%**，均低于 `maxDiffPixelRatio: 0.02` ⇒ **门禁不会报警**。本轮据此改为主动删除基线强制重生成并目检（见 W-1） | PASS（含告警） |

## 结论

result: **PASS_WITH_WARNINGS**

EC-04 的判定标准（"页面去掉对应 disabledOperations"）成立：`pageSupport` 中
`ops/alerts` 与 `ops/incidents` 的 `disabledOperations` 已删除、`level` 升为 `full`，
而这两页现在真的能写——规则落库后被收件箱消费（标记不隐藏），事故落库后被收件箱与候选列表消费。
写面的每个动作都有"写完再读"的证据，没有只断言 201/204 的空壳用例。

本轮同样**先红后绿**，而且红了**四次**：m0 依次被格式门（`ruff format` 漏跑）、
50 行函数上限（契约用例加断言后超限）、TS 循环依赖（面板 ↔ 列定义互相 import）、
命名门禁（独立模块文件名与唯一组件导出不同名）拦下——四道门都是真门，逐条修复后 23/23。
另一次排查是"设计门禁是否有盲区"的量化验证：门禁本身工作正常（把基线换成另一路由的图会失败），
但 **2% 的容差 + 抗锯齿排除**足以让"整页新增面板"这类改动落在容差内不报警——该事实已量化并
留在 `scratch/cycle5-baseline-drift/`，不掩盖、不夸大。

## 告警

- W-1（**设计门禁的容差盲区**，本轮实测）：新增整块面板后旧基线只差 1.02% / 0.93%
  （阈值 2%），门禁不会变红 ⇒ "页面改动必须主动重生成基线并目检"是流程要求而非兜底；
  若将来要紧这门禁，需要降低 `maxDiffPixelRatio` 或改为"关键区域裁切 + 更严阈值"，
  属独立决策（会带来大量基线维护成本）。
- W-2（规则只做标记，不抑制来源）：静音不改变告警的派生来源，失败 run 仍会被列出；
  真正"降噪"需要阈值/去重/静默期策略，本计划不做。
- W-3（`assignee` 是自由文本）：没有成员/角色校验，也没有 SLA、计时与升级链；
  指派只是记录事实。
- W-4（`IncidentsViewDto.incidents` 元素形状变更）：由"候选行"改为"事故行"，
  外部消费者必须按新 schema 升级（仓内前后端同版本发布，契约由 OpenAPI 快照固定）。
- W-5（门禁密集拦截=信息密度高，不是噪音）：本轮 4 次 m0 红分别命中格式、函数长度、
  模块依赖环、文件命名——说明"用脚本改文件后不跑 formatter""一个面板同时定义 chip 与列"
  这类顺手写法会被门禁抓住；下次新增共享组件时应直接放进**与组件同名**的独立文件，
  并在拆分后立刻跑 depcruise 与命名门禁。
- W-6（继承，未处理）：RECHECK-054 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读）仍开放。

## 复现

```
# 域 / API / 契约
python -m pytest tests/api/test_ops_control_api.py -q                 # 10 passed
python -m pytest tests/api/test_ops_view_api.py -q                    # 5 passed
python -m pytest tests/api -q                                         # 336 passed
python -B tools/gen_openapi.py && python -m pytest tests/contracts -q  # 3 passed
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm exec playwright test --list                        # 50 tests in 13 files
cd apps/web && pnpm exec playwright test --list --config playwrightLive.config.ts  # 28 tests in 7 files
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live             # 50 / 28 passed
# 设计基线（ops-alerts / ops-incidents；linux 在 pinned noble 容器内重生成）
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/ops-{alerts,incidents}-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh ops-alerts ops-incidents
# 门禁漂移量化（旧基线 vs 新渲染，Playwright 判据）
python scratch/cycle5-baseline-drift/measure.py                        # 1.02% / 0.93% ⇒ 不报警
# 本地门
sh scratch/run-m0-cycle12.sh                                           # profile=m0; 23 deterministic checks
```
