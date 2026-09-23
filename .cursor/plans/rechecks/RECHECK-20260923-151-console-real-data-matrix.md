---
id: RECHECK-20260923-151
plan_id: PLAN-20260923-150
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-recheck-script + root-agent-goal-013-ec01
baseline_ref: 50afb3b（GOAL-013 建档）
checked_head: 当前树 + 干净 checkout `f45d6ec`（cycle 1 最后一条功能提交）
---

# RECHECK-20260923-151 — PLAN-20260923-150 逐页真实数据验收矩阵（GOAL-013 EC-01）

## 检查范围

**不采信**矩阵文档的自述与判据测试的「全绿」结论：用**独立复检脚本**
`scratch/verify_goal013_c1.py` 在**当前树**与**干净 checkout**上各跑一遍。脚本三条自我约束
（「独立」的落地方式）：**只读**、**只用标准库**、**不 import 仓库代码** ⇒ 不可能与被测代码
「同谋通过」，且可用主树解释器在干净树里跑。

七组判据（共 218 条）：**A** 矩阵完备（20 行 / 终态合法 / 零待定）、
**B** 三方同源（非 full 路由不得逃出矩阵；收敛行在 `pageSupport` 里确为 `full`）、
**C** 收敛有证（具名 live 用例存在 + 白名单内 + 真的 `page.goto` 该路由 + 对 DOM 断言）、
**D** 保持行点名缺口（缺口 token + 「」引文逐字来自权威）+ 不混写、
**E** 姿态与残余（`W-A` / 路径 (B) 记录 / `R-M1` / `R-D1` / `R-N1` 未消失）、
**F** 子 PLAN 收口（`DONE` + `latest_recheck` 是**仓库相对路径** + 该复检 `PASS` + 记忆记账）、
**G** 产物在位。

## 检查结果

### 一、两棵树同结论

| 树 | 脚本结果 | 说明 |
| --- | --- | --- |
| **当前树** | `checked=218 failures=0`（本复检与 PLAN 收口落盘后） | A/B/C/D/E/F/G 七组全绿 |
| **干净 checkout**（`f45d6ec`，仓外 `git worktree`） | `checked=218 failures=3` | 三条红**全部**是「尚未收口」这一类时序项：`F2 PLAN-150 not DONE`、`F3 PLAN-150 still has unchecked boxes`、`F6 recheck missing` —— 收口记录（PLAN 转 `DONE` + 本复检）正是在**收口提交**里落盘 |

⇒ 两棵树在**同一判据、同一判词**上给同一结论；干净树多出的三条红的**内容**与「待收口」一致，
不是分歧。收口提交只增加记录（PLAN 状态 + 本复检 + GOAL 回写 + 工程记忆），
**不含任何产品面改动**。

### 二、独立复检脚本自己撞到并修掉的一处问题（如实记录）

脚本初版用 `text.replace('"\n    "', "")` 把 `pageSupport.ts` 的**字符串拼接**接回整句，
而源码里的形态是 `" +` 换行 `"`（带 `+`）⇒ 该替换不生效 ⇒ **假红**一条
`D2 row 13 gap quote not verbatim in authority`（第 13 条 `ops/integrations` 的引文正好跨拼接边界）。
处置：改用 `re.sub(r'"\s*\+\s*\n\s*"', "", …)`，重跑后该条转绿、其余判据数字不变。
**判据测试（`console-real-data-matrix.test.ts`）用的正则一开始就是对的**，它没有假红——
两套实现的分歧由脚本侧的归一化缺陷解释，**不是**矩阵或权威面的事实问题。

### 三、逐页矩阵的实测事实

- 20 行（19 条原 `partial` + 1 条原 `gap`），**已收敛 1 / 保持 19 / 待定 0**。
- 唯一收敛项 `plan/overview`：`pageSupport` 等级实测为 `full`（脚本 B 组）
  ⇒ 判据的反向要求（收敛行必须真的收敛）成立，不是只改文档。
- 19 条保持行：每条都有缺口 token 且引文**逐字**出现在 `pageSupport.ts` 或
  `CONSOLE_PAGE_MAP.md`（脚本 D 组）⇒ 矩阵没有自造缺口事实。
- `plan/overview` 的页面级 live 用例实测：文件存在、suite `plan-overview` 在白名单内、
  `page.goto` 到 `#/plan/overview`、且对 DOM 断言（脚本 C 组）。

### 四、判据**能被什么按压、不能被什么按压**（GOAL-013 EC-03 的口径前置披露）

| 判据 | 能被什么按压 | **不能**被什么按压 |
| --- | --- | --- |
| ① 矩阵完备 | 改某行终态 / 加「待定」字样 | 与数据无关（纯文本面） |
| ② 三方同源 | 把某保持行的缺口改写成「已交付」（实测 ⇒ 红，判词点名 `held row 2 … must name a gap token`）；把收敛行改回 `partial` ⇒ 红 | 改引文里的**无关字**（引文仍逐字在权威里 ⇒ 绿，属预期） |
| ③ 收敛有证 | 把具名 live 文件改成不存在的文件名（实测 ⇒ 红）；把 spec 的 `page.goto` 目标换成别的路由（实测 ⇒ 红） | **改 spec 的断言强度不会红**——本判据是**结构判据**（存在/白名单/驱动路由/有 DOM 断言），不检查断言是否够强。这是它的已知边界 |
| live「页面 == 读面」用例 | **按页面**（把论断卡数值钉成常量 7 ⇒ 两条用例红，实测） | **按数据**——页面与读面**同源**，两边一起变 ⇒ 对同源数据按压不敏感；按数据只能移动成对反证的**前提**断言 |

⇒ **本 PLAN 新增的判据里，只有 live 用例是语义判据；矩阵那四条都是结构判据。**
结构判据负责「三处不可能各自漂移」，语义正确性由 live 用例与既有 live 套件承载。

### 五、m0 首轮的两次红与处置（如实记录：本复检初稿判 PASS 之后才跑 m0）

本复检的判据（A–G 组）与 web 门先跑；`make validate-all` 这一轮**首跑两红**，
两条都在本 cycle 的改动面内，处置如下：

| 红 | 判词 | 处置 |
| --- | --- | --- |
| `typescript/lint`（`eslint .`，覆盖 `apps/web/tests/**`） | `live-plan-overview.spec.ts:31` `["EC13_SNAPSHOT_DIR"] is better written in dot notation`；`console-real-data-matrix.test.ts:187` `Use the RegExp#exec() method instead` | **真缺陷、当轮修掉**：① 改点号取值（与既有 `live-experiments.spec.ts` 同写法）；② `LIVE:` 名字提取改用 `indexOf` + `split` —— 不用正则就不用 `String#match`，从而既不触 lint 的 `prefer-regexp-exec`，也不触安全扫描对 `.exec(` 的启发式（这两条规则在同一处直接冲突，绕开是唯一同时满足的写法） |
| `python/tests` | `MaxRetryError: HTTPConnectionPool(host='127.0.0.1', port=4318)` —— OTLP collector 未起 | **环境项、非代码缺陷**：CI 的 m0 在跑测试前用 `infra/compose/otel-evidence.yaml` 起 **pinned OTel collector**，本地首跑沿用了早前只起 postgres 的 compose。按 CI 的同一配方补起 collector 并以同一组环境变量（`RESEARCHOS_OTEL_COLLECTOR_ENDPOINT` / `RESEARCHOS_REQUIRE_COLLECTOR` / `RESEARCHOS_REQUIRE_POSTGRES` / DSN）重跑 |

**注意**：web 门里的 `pnpm run lint`（只 lint `src`）**不会**覆盖 `apps/web/tests/**`；
覆盖它的是根 `eslint .`（m0 的 `typescript/lint`）。本 cycle 的两条 lint 缺陷因此只在 m0
这一层暴露 —— 这条口径本身是可复用事实，已随 `MEM-20260923-115` 落库。

### 六、本地 m0 的终局：22/23，唯一那条红是本机环境的既有签名（不是本 cycle 的缺陷）

修掉 lint 两条后重跑：`typescript/*`（含此前两红的 `typescript/lint`）与 `framework/*`
**全部 PASS**，唯 `python/tests` 仍 exit 1。**但该 check 的自身数字是
`4413 passed, 17 skipped, 0 failed`** —— exit 1 来自**出站判据**在结束时判红：

```
egress guard: judged 794 connection attempt(s); blocked 10
egress guard: BLOCKED 198.18.0.230:443 by tests/api/test_runs_api.py::
  test_start_run_unprovisioned_control_plane_reports_actionable_failure
  :: preflight_support.py:43:build_endpoint_health <- … <- transport.py:108:_execute_request
```

（另 8 条 blocked 是 `tests/architecture/python/test_default_egress_guard.py` 的**故意探针**，
2 条来自上面这个用例。）

**归因（按既有配方，不动判据）**：

- `198.18.0.0/15` 是**本机 fake-IP 代理**的 DNS 段；该地址**不在仓库里**——
  仓库内 `198.18` 仅出现在文档与出站判据自己的测试文件（故意样本）中，
  实测来源是**解析了主机名**（用例只 `delenv` 了 DB 相关键，未清 LLM 端点键 ⇒
  组合根按本机 `.env` 的端点配置探测健康）。
- ⇒ 这是**本机环境签名**，同族于既有的「本地 m0 egress guard fake-IP red」记录。
- **最强归因证据是逐字节对照**：`git diff 50afb3b..HEAD -- '*.py'` **为空**——
  **Python 树与那次 CI 全绿（含 `python/tests`）的建档提交逐字节相同**，
  而本 cycle 的 876 行改动全在文档 / web 源码 / web 测试。
  ⇒ 该 check 的结果**在构造上**与本 cycle 的改动无关。
- **不改判据**（不放宽 `tests/egress_guard.py`、不加豁免名单）——CI 侧的权威判定由本次
  推送后的 m0 run 承担。

## 结论

`result: PASS`。**GOAL-013 EC-01 判 PASS**：EC-01 的三条离线判据（矩阵完备 / 三方同源 /
收敛有证）与它的两条成对反证全部实跑并先红后绿；20 条逐条有终态、零条待定、不混写、
每条的依据可独立复核（(a) 指向具名 live 用例、(b) 指向具名缺口且引文逐字来自权威）。
矩阵 **已收敛 1 / 保持 19 / 待定 0**。

**本 PLAN 不覆盖 EC-02…EC-05**：真实数据 live 链的其余域（`library/lineage`、`govern/*` 等
页面级用例）、判据性质披露的全面落地、`ops/matrix` 的单独处置与收口复检分别属后续 cycle。

## 仍未处理项（如实登记）

- `W-A` 真实控制面对 `sort_analysis_v1` 的 `evidence.read` 仍判 `DENY` —— **需拍板**。
- 路径 (B) 的「重新设计需要什么」5 条 —— **需拍板**。
- `R-M1` Mimosa 钩子侧 `scanner_enobufs` 未得完整结论 ⇒ **不得宣称项目安全**。
- `R-D1` 23 条 Dependabot 告警（4 high / 13 moderate / 6 low），本循环不处置。
- `R-N1` 30 条非 ASCII 路径按 AGENTS.md §13 登记豁免。
- `R-F1` 「渲染正确」已操作化为「页面 == 读面 + 成对反证」。
- `R-F2` live 用例因数据规模不足无法演示非空渲染时不得计入 ≥6。
