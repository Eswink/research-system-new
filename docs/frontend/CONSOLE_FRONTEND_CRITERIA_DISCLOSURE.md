# 前端判据性质披露（GOAL-20260923-013 EC-03）

**这是人读视图**；机器可读的**单一来源**是
[`apps/web/tests/unit/frontendCriteriaDisclosure.ts`](../../apps/web/tests/unit/frontendCriteriaDisclosure.ts)，
由 `apps/web/tests/unit/frontend-criteria-disclosure.test.ts` 机械核对
（完备性双向 / 两字段非空 / 披露与证据类型一致 / 本文件与登记册同源 ⇒ 两张表不可能各自漂）。

## 为什么这一栏必须存在

本 GOAL 的 live 判据形态是「**页面 == 读面**」：先经 HTTP 取读面，再与 DOM 逐值比对。
两侧**同源**（DOM 的值由读面响应导出）⇒ **改数据对它不敏感** —— 两边一起变，等式照样成立。
这类判据只有按压**页面那一段**（把组件渲染的值钉成常量）才会红。
把这件事写下来，是为了让后来者知道：**这条判据绿，不代表页面上的值是「对的」，
只代表「页面与读面一致」。**

**「等式数据不敏感」与「前提数据敏感」是两件事**：把某一侧的数据改成空，
红的会是成对反证的**前提**（`toBeGreaterThan(0)` / `toBe(true)` 这类自证），而不是等式本身。
登记册用 `premiseIsDataSensitive` 单独承载后者。

## 披露表

| # | 判据文件 | 判据（test 名） | 能被什么按压 | **不能**被什么按压 | 实际敏感面 | 证据（`scratch/`，不进仓库） |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `tests/unit/console-real-data-matrix.test.ts` | ① 矩阵完备：恰好 20 行，终态二选一，零条待定 | 改矩阵文本事实（行终态 / 缺口 token / 引文 / 删 LIVE:） | 改被点名 spec 的**断言强度**——本判据是结构判据，不读断言强弱 | structure | `scratch/goal013-c4-press-matrix-undecided.txt` |
| 2 | `tests/unit/console-real-data-matrix.test.ts` | ② 三方同源：非 full 路由无遗漏；收敛行在代码里确为 full；缺口引文逐字来自权威 | 改矩阵文本事实（行终态 / 缺口 token / 引文 / 删 LIVE:） | 改被点名 spec 的**断言强度**——本判据是结构判据，不读断言强弱 | structure | `scratch/goal013-c1-press-matrix.txt` |
| 3 | `tests/unit/console-real-data-matrix.test.ts` | ③ 收敛有证：每条收敛行点名的 live 用例存在、在白名单内、且真的驱动该路由并对 DOM 断言 | 改矩阵文本事实（行终态 / 缺口 token / 引文 / 删 LIVE:） | 改被点名 spec 的**断言强度**——本判据是结构判据，不读断言强弱 | structure | `scratch/goal013-c1-press-live-route.txt` |
| 4 | `tests/unit/console-real-data-matrix.test.ts` | ④ 不混写：收敛行不带缺口 token，保持行不带 LIVE: | 改矩阵文本事实（行终态 / 缺口 token / 引文 / 删 LIVE:） | 改被点名 spec 的**断言强度**——本判据是结构判据，不读断言强弱 | structure | `scratch/goal013-c4-press-matrix-mixed.txt` |
| 5 | `tests/e2e/live-plan-overview.spec.ts` | live: 概览页的四张指标卡 == 读面（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c1-pressA-page.txt` |
| 6 | `tests/e2e/live-plan-overview.spec.ts` | live: 读面为空时页面显示诚实空态（成对反证，不伪造数据） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c1-pressA-page.txt` |
| 7 | `tests/e2e/live-library-lineage.spec.ts` | live: 血缘页的三张表与合并摘要 == 读面（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c2-press-lineage-rows.txt` |
| 8 | `tests/e2e/live-library-lineage.spec.ts` | live: 库资源读面为空时显示诚实空态，且不渲染空表（成对反证） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c2-press-empty-text.txt` |
| 9 | `tests/e2e/live-govern-audit.spec.ts` | live: 审计页的事件行数 == 读面（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c2-press-audit-rows.txt` |
| 10 | `tests/e2e/live-govern-audit.spec.ts` | live: 事件读面为空时显示诚实空态，且不渲染事件行（成对反证） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c4-press-audit-empty.txt` |
| 11 | `tests/e2e/live-portfolio-experiments.spec.ts` | live: 实验表的逐行计数 == 读面（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c3-press-experiments.txt` |
| 12 | `tests/e2e/live-portfolio-experiments.spec.ts` | live: 指标为空的实验渲染 0，不补占位指标（成对反证） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c3-press-experiments.txt` |
| 13 | `tests/e2e/live-insights-reports.spec.ts` | live: 交付物读面非空时，报告页渲染的是读面的值（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c3-press-reports.txt` |
| 14 | `tests/e2e/live-insights-reports.spec.ts` | live: 无交付物的 run 显示读面给出的原因，且不渲染来源区块（成对反证） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c4-press-reports-empty.txt` |
| 15 | `tests/e2e/live-ops-integrations.spec.ts` | live: provider 目录逐行逐值 == 读面（页面 == 读面） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c3-press-integrations.txt、`scratch/goal013-c4-spotcheck-page.txt、`scratch/goal013-c4-spotcheck-data.txt` |
| 16 | `tests/e2e/live-ops-integrations.spec.ts` | live: 无法判定的 provider 如实显示 UNKNOWN，不伪装健康（成对反证） | 把组件渲染的值钉成常量（按页面按压） | 改读面数据（两侧同源，一起变 ⇒ 等式仍成立）；但成对反证的**前提**是数据敏感的 | page | `scratch/goal013-c3-press-integrations.txt`、`scratch/goal013-c4-spotcheck-page.txt`、`scratch/goal013-c4-spotcheck-data.txt` |

## 实测：抽查一次证明披露为真

披露说「数据不敏感、页面敏感」。`live-ops-integrations` 的第 1 条做过**成对**实跑：

| 按压方式 | 做法 | 实测 | 证据 |
| --- | --- | --- | --- |
| **按数据** | 把 provider id 在 `examples/config/tool_providers.yaml` 里改名（读面与页面**一起**变） | **2 passed**（等式仍成立 ⇒ 不敏感） | `scratch/goal013-c4-spotcheck-data.txt` |
| **按页面** | 把 `providerColumns` 的 `health` 渲染钉成常量 | **2 failed**（⇒ 敏感） | `scratch/goal013-c4-spotcheck-page.txt` |

同理，**离线矩阵判据**是**结构判据**：按压它的文本事实（行终态 / 缺口 token / 引文 / `LIVE:`）
会红（红证见上表），但**改被点名 spec 的断言强度不会红** ——
它只检查「存在 / 在白名单 / 驱动该路由 / 对 DOM 有断言」，不读断言强弱。
这是它的已知边界，语义正确性由 live 用例承载。
