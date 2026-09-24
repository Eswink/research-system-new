---
id: RECHECK-20260924-160
plan_id: PLAN-20260924-158
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-24
completed_at: 2026-09-24
reviewer: root-agent-goal-014-ec04 + 一份可复跑探针（scratch/goal014_c4_residual_probe.py）
baseline_ref: bf3ecdc（cycle 3 交付 + 记录）
checked_head: 当前树（cycle 4 分类处置表 + 探针输出）
---

# RECHECK-20260924-160 — GOAL-014 EC-04 残余清账（cycle 4）

## 检查范围

① 三项承继残余是否**按当前实测**分类（不是引用旧数字）；② 每项是否有**唯一终态**且
依据**可核对**；③ 有没有为了清账而动依赖 pin / hook 面 / 源码（EC-04 明文只分类）；
④ 有没有借 EC-04 降级 EC-01 / EC-02 / EC-03。

## 分类处置表（本 EC 的交付物）

| ID | 类别 | 终态 | 依据（可核对） | 证据路径 |
| --- | --- | --- | --- | --- |
| **R-D1** | 依赖供应链（npm 生态） | **登记为需拍板** | 现测 **23 条 open**（4 high / 13 medium / 6 low），包分布 **vite 14 / undici 8 / yaml 1**，**每条**都有 `first_patched_version`（high `6.4.2`/`6.4.3`）。修复动作 = **依赖 pin 升级**（当前 `apps/web/package.json` pin `vite 6.3.5` / `yaml 2.8.1`；`undici` 只在 `pnpm-lock.yaml`，属**传递依赖** ⇒ 要靠 overrides）⇒ 命中 `escalation_triggers`「依赖 pin 升级」与「不进入循环」人工项 **5**；本 PLAN 明文**只分类、不升级** | `scratch/goal014-c4-residual-probe.txt` §1（逐条编号 / 严重度 / 生态 / 包 / manifest / 修复版本） |
| **hook 侧 L3 门** | 治理面 hook（外部分析器 **Mimosa** 的 L3 检测层，**不是**本仓 hook 自己的命名 —— `.cursor/hooks/*.py` 零处 `L3` 字面量） | **登记为需拍板** | 根因**已定位**（`semgrep` 检测层**未安装**）在既有审计记录里；修法 = 安装检测层（**环境 / 依赖面变更**）+ hook 面属治理面 ⇒ 人工项 **6**。**本 cycle 现场复现其形态**：本次 `git commit` 与 `git push` 均收到 `Mimosa 在 git commit/push 前没有得到完整扫描结论（scanner_enobufs）。本次按兼容策略继续…` ⇒ **失败开放**（fail-open，与审计记录一致） | `scratch/goal014-c4-residual-probe.txt` §2（hook 面扫描）+ `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md`（根因与处置节）+ 本 cycle commit/push 的 hook 提示原文 |
| **450 行贴线文件** | 代码规模纪律（门禁：文件 ≤ **450** 硬上限、> **300** 软阈值、函数 ≤ **50** 行） | **登记为需拍板** | 门禁根内 `.py` **1011 个**：**3 个正好 450（零余量）** —— `services/api/composition.py`、`adapters/postgres/workflow_engine.py`、`adapters/execution/docker_backend.py`；**400–449 行 10 个**；**300–449 软阈值 70 个**。人工项 **4**：大重构会放大 diff 风险，**需人工决定**；本 GOAL 明文 EC-04 **只分类**（改任何文件时若触线只拆语义中立的部分） | `scratch/goal014-c4-residual-probe.txt` §3 + 门禁同口径复算（根 `apps/services/packages/adapters/tests`，与 `tests/tooling/test_python_source_limits.py` 一致） |

**三项终态一致**：都不是「已处置」（**本 cycle 无任何处置动作**，也不该有 —— 三项各自
命中人工项 4 / 5 / 6），也都**不是**「不属于本循环」（它们**确是**本 GOAL 承继的残余，
只是处置需拍板）。

### 一处边界（如实登记，不算作第 4 项）

`tools/PA1R运行演练v1.py`（433 行）**不在门禁根内**（门禁只扫
`apps/services/packages/adapters/tests`），其文件名含非 ASCII 属 §13 **已登记豁免**面
⇒ 既不入 450 行门禁的账，也不构成新残余。

## 检查结果

### 一、证据是当前实测

三项都不引用旧记录的数字：告警走 GitHub REST（只读，逐条取编号与修复版本）、
hook 面走本 cycle 现场扫描 + 本次 commit/push 的 hook 提示原文、行数走门禁**同口径**扫描。
探针可复跑（`scratch/goal014_c4_residual_probe.py`），令牌只在内存里（输出只打长度）。

### 二、零处置动作（也是本 EC 的硬边界）

`git diff --stat` 对本 cycle 的改动面可核：只有本 PLAN、本 RECHECK 与 GOAL 回写；
**没有** `package.json` / `pnpm-lock.yaml` / `.cursor/hooks/` / 任何 `.py` 源码的改动。

### 三、没有降级 ①②③

EC-01 / EC-02 / EC-03 的 `status` 与 `status_note`、以及三份判据文件**一字未动**
（本 cycle 的 diff 不含它们）。EC-04 的「可选」性质**不**被用来削弱任何已完成 EC。

### 四、探针的一处安全修正（如实登记）

探针初稿用 `urllib.request.urlopen(动态 URL)`，被 **Mimosa 判 SSRF 高危并拦截写入**
⇒ 改写为「**写死主机常量** `api.github.com` + `http.client` 显式连该主机 + 路径先经结构校验
（必须以 `/repos/` 开头、禁 `://` / `..` / `@`）」。既过安全闸，也更贴合本仓出网纪律
（不在数据里拼 URL、主机不接受调用方传入）。

## 判据性质披露（必须读的一段）

- 本 RECHECK 的**结论是「分类完成」**（三项各有唯一终态且依据可核对），**不是**
  「残余已解决」。任何把本表读成「23 条告警已处理 / L3 门已修 / 贴线已拆」的说法都是**错的**。
- `R-D1` 的数字是**当日快照**（告警会随上游 advisory 与依赖变动而变化）；
  引用时必须带测量时间与探针路径。
- 450 行的清单同样是**当日快照**：本 cycle 之后任何触碰这些文件的改动都可能改变行数。

## 结论

**`PASS`** —— 三项残余**全部现测分类**、各有唯一终态（三项均 = **登记为需拍板**）
且依据可核对（API 逐条编号与修复版本 / hook 提示原文 + 审计根因 / 门禁同口径行数）；
**零处置动作**（未升 pin、未动 hook、未改源码），**未降级** EC-01/02/03。

## 仍未处理项（如实登记）

- **`R-D1`**：23 条告警待用户拍板（升 pin 涉上游版本策略；`undici`/`yaml` 需 overrides）。
- **hook 侧 L3 门**：待拍板（安装检测层 = 环境/依赖面变更；治理面）。
- **450 行贴线**：待拍板（3 个零余量文件；拆分方案需人工决定）。
- **EC-02** 仍 `BLOCKED`（`F-10` / `F-11` 待拍板）；**EC-05** 未开始（下一 cycle 起做收口复检）。
