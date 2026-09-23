---
id: RECHECK-20260923-153
plan_id: PLAN-20260923-152
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-recheck-script + root-agent-goal-013-ec02
baseline_ref: 27bf317（cycle 3 派生 = cycle 3 的起点）
checked_head: 当前树 + 干净 checkout（cycle 3 最后一条功能提交）
---

# RECHECK-20260923-153 — EC-02 第三批页面级 live：满 6/6（GOAL-013 cycle 3）

## 检查范围

三条新页面级用例（`portfolio/experiments`、`insights/reports`、`ops/integrations`）
**实跑**并与读面逐值比对；每条都做了**按页面**按压；用独立复检脚本在**当前树**与
**干净 checkout** 上各跑一遍（脚本沿用 cycle 1/2 的三条自我约束：**只读**、**只用标准库**、
**不 import 仓库代码**）。

## 检查结果

### 一、两棵树同结论（**并修掉了前两个 cycle 的方法缺陷**）

独立复检脚本 `scratch/verify_goal013_c3.py` 在当前树与干净 checkout 上**各跑一遍**：

| 树 | 结果 |
| --- | --- |
| 主树（当前） | `checked=50 failures=0` |
| 干净 checkout `78e60cf`（cycle 3 最后一条功能提交） | `checked=49 failures=4`：`E1 EC-02 is not marked PASS`、`F2 PLAN-152 not DONE`、`F3 PLAN-152 still has unchecked boxes`、`F6 recheck missing` |

干净树多出的四条红**内容**全是「尚未收口」这一类：PLAN 转 `DONE`、EC 状态回写、
本复检与记忆落盘，**都在收口提交里**，故干净树看不到；不是分歧。收口提交不含产品面改动
（脚本 G 组：`27bf317..HEAD` 无 `services/` / `packages/` / `adapters/` / `apps/web/src/` 改动）。

**本 cycle 发现并修掉的方法缺陷（如实记录，并已回改前两个 cycle 的记录）**：
三个复检脚本初版都用 `ROOT = Path(__file__).resolve().parents[1]`。从干净 checkout 里调用
**主树路径**的脚本时，`__file__` 指向主树 ⇒ `ROOT` 仍是主树 ⇒
**所谓「两棵树各跑一遍」实际是主树跑了两次**；两棵树输出一致不是「同结论」，是**同一棵树**，
而当时主树恰好处于未收口状态，让干净树该有的红**看起来**合理，缺陷因此隐身前两个 cycle。

修法：`ROOT = Path(os.environ.get("VERIFY_ROOT") or Path.cwd()).resolve()`。
修好后三对实测（本 cycle；`c3` 的计数含其后补的夹具纪律组）：

| 脚本 | 主树 | 干净 checkout |
| --- | --- | --- |
| `verify_goal013_c1.py` | `checked=219 failures=0` | `checked=218 failures=3`（`@f45d6ec`） |
| `verify_goal013_c2.py` | `checked=33 failures=0` | `checked=32 failures=3`（`@08daf1e`） |
| `verify_goal013_c3.py` | `checked=50 failures=0` | `checked=49 failures=4`（`@78e60cf`） |

⇒ 前两个 cycle 的**结论不变**（干净树多出的红仍是「尚未收口」时序项），
但它们的**证据方法此前是错的**，`RECHECK-20260923-151` 与 `-152` 已就地补「一之二」更正说明。
教训落 `MEM-20260923-120`（同一族：**判据指向的对象必须真的是它声称的那个**）。

### 一之二、三条用例实跑（`pnpm run test:e2e:live`）

| 用例 | 路由 | 读面 | 正向 | 成对反证 |
| --- | --- | --- | --- | --- |
| 第 4 条 | `#/portfolio/experiments?run=…` | `GET /runs/{id}/experiments` | 行数 == `experiments.length`；每行制品数 == `artifact_ids.length`、指标键数 == `keys(metrics).length` | `6666…6666` 的读面 `metrics` 为**空对象** ⇒ 指标列必须渲染 **0**，不得补占位 |
| 第 5 条 | `#/insights/reports?run=…` | `GET /runs/{id}/deliverable` | `available: true` ⇒ 渲染读面的 `objective` 与 `artifact_id` | `available: false` ⇒ 显示读面 `reason` **逐字**，且**不**渲染来源区块 |
| 第 6 条 | `#/ops/integrations` | `GET /tool-providers` | 行数 == `providers.length`；每行 `health` 由读面导出 | 读面 `UNKNOWN` 的那条必须如实显示 `UNKNOWN`、**不得**显示成 `HEALTHY` |

全套 live：**53 passed**（cycle 2 的 47 + 本批 6）。stub 套件：**96 passed**
（三条新 spec 被 `testIgnore` 正确排除）。

### 二、判据**能被什么按压、不能被什么按压**（GOAL-013 EC-03 的口径披露，第 3 批）

每条都做了**按页面**按压（把组件渲染的值钉成常量 ⇒ 判据必须红），红证落 `scratch/`：

| 判据 | 按压方式 | 实测 | 证据 |
| --- | --- | --- | --- |
| 实验表逐行计数 == 读面 | `metrics` 列渲染钉成常量 `7` | **红 2 条**（正向 + 反证都断言这一列） | `scratch/goal013-c3-press-experiments.txt` |
| 报告页渲染读面的值 | `objective` 段落钉成常量 | **红**（正向）；**成对反证保持绿** —— 它不读 `objective`，符合预期 | `scratch/goal013-c3-press-reports.txt` |
| provider 目录逐行逐值 / 不伪装健康 | `health` 钉成常量 `HEALTHY` | **红 2 条**（正向 + 反证）——反证正是「不得显示成健康」 | `scratch/goal013-c3-press-integrations.txt` |

**不能被什么按压**：**按数据**不敏感 —— 三条判据的两侧**同源**（DOM 的值由读面响应导出），
两边一起变。按数据只能移动**成对反证的前提**（`metrics` 全为空时前置断言失效）。
⇒ 与前两个 cycle 结论一致：**判据的对侧必须按页面**。

### 三、本 cycle 的两处前置事实（写用例时先查出来的，非缺陷）

1. **`#/portfolio/experiments` 消费的是 per-run 读面**（`GET /runs/{id}/experiments`），
   **不是**项目级 `GET /projects/{id}/experiments`。没有 `?run=` 时页面渲染的是
   「未选择运行」空态，**表根本不存在** ⇒ 第一版用例（用项目级读面且不带 `?run=`）
   实测**红**：`toHaveCount` 等不到任何行。改按 per-run 读面 + `?run=` 后转绿。
   **这条是「先确认读面归属」的必要性证据**，已落 `MEM-20260923-119`。
2. **`insights/reports` 的正向方向需要一份受控夹具**：实测四条 run 的
   `/runs/{id}/deliverable` 全部 `available: false`（live app 的 Fake 链不跑 M12 参考链，
   不产出 `deliverable.json`）⇒ 按 **D-4** 在 `tests/api/console_api_app.py` 按该文件
   既有夹具模式补一份受控交付物，**挂在既有 run** 上（新建 run 会改动 `run_count` 等
   既有读面数字，干扰别的 live 用例）。如实登记：该交付物是**夹具**，不是一次真实
   M12 参考链的产出；用例只判「读面 → DTO → 页面」，**不声称**「报告来自真实研究运行」。

### 四、本地门

| 门 | 结果 |
| --- | --- |
| `pnpm run test:e2e:live` | **53 passed** |
| `pnpm run test:e2e`（stub） | **96 passed** |
| web `lint`（`--max-warnings 0`）/ `typecheck` / `build` | 全绿 |
| `validate.py` | **绿** |
| `docs_consistency_check.py` | `DOCS-CHECK PASS: 6 deterministic checks` |
| `m0`（`MEM-20260923-116` 的配方） | 见第五节 |

### 五、本地 m0：首轮两红**都在本 cycle 自己的改动/记录上**，当轮修掉后转绿

首轮（`scratch/goal013-c3-m0.log` 首版）`FAILED: 2 check(s): python/tests=1, framework/validate=1`，
两条都是**真缺陷**，不是环境项：

| 红 | 判词 | 成因与处置 |
| --- | --- | --- |
| `python/tests` | `FAILED tests/tooling/test_python_source_limits.py::test_python_source_size_limits[testspi\console_api_app.py]`（该轮 `1 failed, 4411 passed`） | **真违规**：D-4 把受控交付物夹具（常量 + `_with_deliverable` + 注释）直接写进 `console_api_app.py`，把它推到 **470 行**，越过 `tests/tooling/test_python_source_limits.py:34` 的 **450 行硬上限**。⇒ 把夹具**拆成独立模块** `tests/api/live_deliverable_fixture.py`（含诚实边界说明），`console_api_app.py` 改为导入 + 调用 ⇒ **427 行**；尺寸门随后实测 `1007 passed` |
| `framework/validate` | `复检缺少检查结果或结论: RECHECK-20260923-153` | **真违规**：本复检加「一之二」更正小节时，把必需标题 `## 检查结果` **顶掉了**（`validate.py` 要求复检同时含 `## 检查结果` 与 `## 结论`）。⇒ 恢复标题 |

⇒ 修掉后重跑：`PASS: profile=m0; 23 deterministic checks`（`scratch/goal013-c3-m0.log`）。
配方沿用 `MEM-20260923-116`（清空 `LLM_MAIN_KEY` / `RESEARCHOS_DATABASE_URL`、钉 test DSN、
起 pinned collector 与 postgres-test），且**收口记录先落盘、再跑 m0**。

**如实登记**：本 cycle 的 m0 因此跑了**两轮**；第 1 轮的红**全部**落在本 cycle 自己新增的
夹具位置与记录结构上（不是产品代码、不是既有判据、不是环境）。第 2 轮前另跑了
`pnpm run test:e2e:live`（夹具搬家后）⇒ **53 passed**，确认拆分没有破坏夹具。

## 结论

`result: PASS`。**PLAN-20260923-152 达成**：三条页面级「页面 == 读面」用例实跑，
每条都有**按页面**先红后绿的按压记录，成对反证的前提均为**真断言**
（读面两侧确实不同、rich/bare 两侧都非空）。
**GOAL-013 EC-02 由 3/6 推进到 6/6**（6 域各 ≥1），EC-02 的域覆盖要求**已满足**。

## 仍未处理项（如实登记）

- `W-A` 真实控制面对 `sort_analysis_v1` 的 `evidence.read` 仍判 `DENY` —— **需拍板**。
- 路径 (B) 的「重新设计需要什么」5 条 —— **需拍板**。
- `R-M1` Mimosa 钩子侧 `scanner_enobufs` 未得完整结论 ⇒ **不得宣称项目安全**。
- `R-D1` 23 条 Dependabot 告警，本循环不处置。
- `R-N1` 30 条非 ASCII 路径按 AGENTS.md §13 登记豁免。
- `R-F1` 「渲染正确」已操作化为「页面 == 读面 + 成对反证」。
- `R-F2` 数据规模不足时不得计入 ≥6（本 cycle 的 `insights/reports` **不是**这种情况：
  它靠受控夹具满足了非空方向，且夹具身份已在记录与代码注释里**如实标注**）。
- **本 cycle 新增的诚实边界**：`insights/reports` 的交付物与三条用例的实验/健康态
  都是**受控夹具**；用例判的是「读面 → DTO → 页面」这一段，不声称页面上的数据
  来自真实执行或此刻的真实外部联通性。
