---
id: RECHECK-20260915-062
plan_id: PLAN-20260915-062
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-002-closeout
baseline_ref: bc4a9aa
checked_head: bc4a9aa+worktree
---

# RECHECK-20260915-062 — GOAL-20260915-002 收口复检（cycle 8）

## 检查范围

GOAL-20260915-002 的六个退出标准（EC-01~06）在**当前树**上是否仍然成立：OpenAPI 快照
里的路径与方法、`pageSupport` 的收敛文案、源码里的诚实边界标记、live 清单登记、
设计基线与路由清单。另核验 EC-06 的"每 cycle CI 六 job 全绿"。

**不在范围内**：历史 cycle 的实现过程复演、历史 RECHECK 的判定重审（只做"当前树是否
支持该结论"的一致性核验）、产品能力新增（本 cycle 只动记录面）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| EC-01 G9 项目级血缘 | OpenAPI 含 `/projects/{project_id}/lineage` (get)；`pageSupport` 的 `GAPS.globalLineage` 含"项目级血缘已接入"；`lineage_projection` 仍保留 `NOT_RECORDED` 诚实边界；live 清单含 `project-lineage` | PASS |
| EC-02 G12 项目级成本预测 | OpenAPI 含 `/projects/{project_id}/cost-forecast` 与 `/cost/daily` (get)；`pageSupport` 中"不绘制预测"表述已消失；`series_projection.py` 仍是 `MEAN_OF_VALUED_DAYS`；live 清单含 `project-cost-forecast` | PASS |
| EC-03 G8 工作区快照 | OpenAPI 含 `/workspace-snapshots/{digest}/files`、`/workspace-snapshots/{left}/diff/{right}`、`/runs/{run_id}/workspace-snapshots` (get)；诚实边界 `RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT` 仍在 `pageSupport`；live 清单含 `workspace-snapshots` | PASS |
| EC-04 G7 ops 写面 | OpenAPI 含 alert-rules(get,post)/`{rule_id}`(patch,delete)/incidents(get,post)/assign(post)/close(post) 五条路径与写方法；`pageSupport` 的告警与事故 reason 记录了写路径且两页 `level: "full"`（无 disabledOperations）；live 清单含 `ops-write` | PASS |
| EC-05 G15 tool-provider 注册治理写面 | OpenAPI 含 5 条注册面路径与写方法（含 approve/revoke/health-check 的 post）；`GAPS`/`SUPPORT` 中 `ops/integrations` 的 `disabledOperations: ["install",…]` 已消失；`packages/domain/tool_registry.py` 仍以 `trust_for()` 由状态推导信任级别；live 清单含 `registry-write` | PASS |
| EC-06 G2 项目删除语义 | OpenAPI 含 `/projects`(get,post) 与 `/projects/{project_id}`(patch,delete)；`portfolio/projects` 的 `disabledOperations: ["delete"]` 已消失且"归档即终态"表述不再存在；契约里 delete 的描述含 `409` 与 `级联`；live 清单含 `project-registry` | PASS |
| EC-06 另一半：每 cycle CI 六 job 全绿 | 不用记录文本，改由 GitHub API 现读 `actions/runs/<id>/jobs`：cycle 1 `34960364156`、cycle 2 `34969935719`、cycle 3 `34978272057`、cycle 4 `34984686466`、cycle 5 `35002027768`、cycle 6 `35011288950`、记录提交 `35013114804`、cycle 7 `35018256116` —— **8 个 run 每个都是 6 job 全 success** | PASS |
| 证据面脚本 | `python scratch/verify_goal002_closeout.py` → **59 条断言全 PASS**，末尾 `PASS: EC-01..EC-06 证据面与当前树一致` | PASS |
| 设计门禁清单未被削弱 | 33 条规范路由仍在 `design-fidelity.spec.ts`；`portfolio-projects` 双平台基线文件存在（本轮 cycle 7 重生成） | PASS |
| 全量套件与门禁 | API **361 passed**、契约 **359 passed / 56 skipped**、stub e2e **59 passed（15 files）**、live e2e **31 passed（9 files）**、web 单测 **76 passed**；本地 m0 = `profile=m0; 23 deterministic checks`；治理 validate 绿 | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

六个 EC 的判定标准在**当前树**上全部成立，且每一项都有可复现的现读证据（不是历史文本）：
EC-01 项目级合并血缘、EC-02 只吃已计价天的项目级成本预测、EC-03 digest 寻址的工作区
文件树与文件级 Diff、EC-04 ops 告警规则与事故处置写面、EC-05 tool-provider 注册治理面
（信任由状态推导 + pin 硬门 + 目录合并消费）、EC-06 项目删除语义（被引用 409 且列出引用、
不级联、合成行拒绝）。EC-06 的"每 cycle CI 六 job 全绿"用 GitHub API 逐 job 重读复核，
8 个 run 无例外。

**GOAL-20260915-002 判定 = ACHIEVED**（README 终止条款：六个 EC 全 PASS + 独立 RECHECK
PASS/PASS_WITH_WARNINGS + 本文件收口、`latest_recheck` 指向 RECHECK-20260915-062）。

收口的含义要说清楚：`pageSupport` 里原先的六个诚实缺口现在都变成了**有真实消费者**的
能力，但这不等于"缺口清零"——每项都带着范围注记（见 GOAL 的 EC 表），那些注记是能力
边界，不是待办占位。

## 告警（结转清单，原样保留）

收口**不使**以下告警通过；它们随 GOAL 收口结转到后继工作（GOAL 的「终止与收口」段）：

- W-1（**设计门禁的容差盲区**，本轮第三次复现）：页面整块新增内容（注册面板 / 项目行 /
  删除动作）后旧基线只差 0.48%~1.73%，均低于 `maxDiffPixelRatio: 0.02` ⇒ 门禁不会报警。
  量化脚本 `scratch/cycle{5,6,7}-baseline-drift/measure.py`；流程约束 = 页面改动必须
  主动删基线重生成 + 目检。
- W-2（**替身守不住 `Idempotency-Key`**，含反证）：`tests/e2e/stub-api.ts` 只按
  method+path 匹配，不校验请求头；去掉 `projectsClient.remove` 的该头后 stub 4 用例
  仍全绿。mutating 调用的这条约束只有 live 套件（真中间件）能守。
- W-3（worker 退出语义，继承 RECHECK-054 W-1）：SIGTERM 打不断阻塞中的 HTTP 读，
  退出上界 = 客户端 30s 超时。
- W-4（供应链面，继承 RECHECK-060 W-2/W-3/W-4）：capabilities 取值域不是授权边界；
  `pinned_revision` 只校验形态；健康复核不落 `observed_schema_digest`、看不出 schema 漂移。
- W-5（删除面，继承 RECHECK-061 W-3/W-4/W-5）：草稿引用计数有 200 上限；不做跨项目
  引用检查；活动项目回退是前端行为（后端无"当前项目"概念）。
- W-6（内存/记录面）：`scanner_enobufs` 期间提交/推送的 hook 扫描未取得结论，
  循环内以独立 Mimosa 密封扫描替代；**不主张项目整体安全**。
- W-7（未处理的历史缺口）：`infra/compose/research-validation.yaml` 的 evidence 目录供给
  缺口（GOAL-001 结转）。
- W-8（工程债）：`live-api-workflow.spec.ts` 已拆到 400 行仍接近 300 行 soft limit；
  未来 live 用例优先新开文件（`live-specs.ts` 登记一处）。

## 复现

```
# 收口复检脚本（EC-01~06 证据面 × 当前树）
python scratch/verify_goal002_closeout.py            # 59 条断言，末尾 PASS
# CI 逐 job 复核（GitHub API；不打印 token）
for run in 34960364156 34969935719 34978272057 34984686466 35002027768 35011288950 35013114804 35018256116; do
  curl -s -H "Authorization: token $(...)" \
    "https://api.github.com/repos/Eswink/research-system-new/actions/runs/$run/jobs"
done   # 每个 run 均 6 job success
# 全量套件
python -m pytest tests/api -q                        # 361 passed
python -m pytest tests/contracts -q                  # 359 passed, 56 skipped
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live && pnpm test   # 59 / 31 / 76 passed
# 本地门
sh scratch/run-m0-cycle12.sh                         # profile=m0; 23 deterministic checks
```
