---
id: RECHECK-20260915-063
plan_id: PLAN-20260915-063
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle1
baseline_ref: 692ef19
checked_head: 692ef19+worktree
---

# RECHECK-20260915-063 — 设计门禁结构判据（GOAL-003 cycle 1 / EC-01）

## 检查范围

PLAN-20260915-063 声称的交付面：`design-outline.ts` 的签名构建与归一化、
`design-outlines.json` 的 33 条路由基线、`design-fidelity.spec.ts` 的第二条主判据用例、
`design-outline-guard.spec.ts` 的反证与对照、跨平台一致性证据、像素-结构对照实验。
其它 EC 不在范围内。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 33 条路由签名入库且与当前渲染一致 | 未设 `UPDATE_OUTLINES` 时跑 `design-fidelity.spec.ts`：33 条路由的像素用例 + 结构用例全绿 ⇒ 基线不是"刚生成的"而是"当前渲染的" | PASS |
| 判据真的会红（整块新增） | 反证用例 1：向 `main` 注入一块可见面板 → `assertOutlines()` 抛"结构签名漂移：节点增删会命中此判据"；同时留下 `test-results/outline-guard/panel-{before,after}.png` | PASS |
| 判据不只看视口 | 反证用例 2：注入到 `document.body` 末尾（视口外，像素差 **0.000%**）→ 仍然判红 ⇒ 与可见性无关 | PASS |
| 判据覆盖最接近真实改动的形态 | 反证用例 3：列表多渲染一行（cycle 7 的项目列表多一行是同类改动，当时像素差 **0.079%** 未报警）→ 判红 | PASS |
| 判据覆盖删除 | 反证用例 4：删掉一行节点 → 判红（增与删对称） | PASS |
| **判据不退化成噪音** | 对照组：只改颜色（不改节点）→ 签名不变、`assertOutlines()` 不抛 | PASS |
| 易变字面量不制造假漂移 | 用例 6 四条断言：长数字 → `<n>`、ISO 时间戳（含 `+00:00` 残留）→ `<ts>`、UUID → `<uuid>`、连续空白折叠 | PASS |
| **跨平台一致性（ubuntu CI 可用）** | `scratch/verify_linux_outlines.sh`：在 pinned `mcr.microsoft.com/playwright:v1.56.1-noble` 容器里重算 33 条，拷回 `scratch/linux-outlines/design-outlines.json`，与 win32 基线逐字节 `cmp` + 逐键比对 ⇒ 输出 `PASS: 33 条结构签名跨平台一致（win32 == linux）`、`drifted=[]`；本轮复检再次 `cmp` = 一致、`host routes 33 / linux routes 33 / drifted []` | PASS |
| 单一基线文件（不产生 per-platform 快照） | `design-outlines.json` 单文件、键排序、2 空格缩进、尾换行（159,546 字节）；仓库内**无** `*-win32.*` / `*-linux.*` 结构快照文件 | PASS |
| 更新是显式意图 | 只有 `UPDATE_OUTLINES=1` 才写回基线；CI 配置不含该变量 ⇒ CI 永远只读校验 | PASS |
| 对照实验量化"同一改动的两个判据" | `scratch/outline-vs-pixel/measure.py`（YIQ 像素差，与门禁同口径，阈值 0.02）：可见面板 **2.618%**（像素判据会报警）／多一行 **0.079%**（不报警）／视口外 **0.000%**（不报警）；三者**结构判据全部判红** | PASS |
| 全量回归 | stub e2e **66 passed / 16 files**、live e2e **31 passed / 9 files**、web 单测 **76 passed**；根 eslint 0 error、`tsc --noEmit` 通过 | PASS |
| 本地 m0 | `scratch/run-m0-cycle12.sh` → `PASS: profile=m0; 23 deterministic checks` | PASS |
| 记录闭环 | PLAN-063 / RECHECK-063 / MEM-038 / INDEX 行 / ALL_PLAN 行 / GOAL-003 记账 | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

EC-01 的判定标准成立：**"整块新增内容"这一类改动从此必然判红**，而且判红不是靠
"看某个截图"，而是靠一条与面积、可见性、平台无关的机械判据。四类反证
（可见新增 / 视口外新增 / 多一行 / 删一行）全部命中，对照组（只改样式）不误报
⇒ 判据有分辨力而不是"见谁都红"。

本轮的关键判断有三条：

1. **互补而非替代**：像素判据仍是主判据（面积/布局/样式），结构判据只负责节点增删。
   两者都不覆盖的窄缝（页面中部的小面积**纯文案**改动）本轮**刻意不补**——
   补它需要文本指纹，而文本指纹会让门禁对日常改文案过敏，噪音成本高于漏报成本。
   这一点写进了 PLAN-063 的「已知风险」与 MEM-038 的「适用边界」，是**已知盲区**
   而不是未知盲区。
2. **跨平台必须证明**：首版 `toMatchSnapshot` 生成的是 `-win32.txt`，ubuntu CI 会
   直接缺文件（"本机能过"的典型陷阱）。改成单一 JSON 基线后，我没有假设"DOM 结构
   与平台无关"，而是在 pinned 容器里重算 33 条并逐字节比对——一致才敢让 CI 用它。
3. **对照实验而非声明**：四次容差盲区（1.73% / 1.02% / 0.79% / 0.48%）过去靠人工
   复现，本轮把它变成脚本化测量（0.079% / 0.000% / 2.618%），门禁的覆盖边界从此可复现。

## 告警（结转与新增）

- **W-1（新增）**：结构签名只覆盖节点增删与叶子文本。**纯文案修改**（替换而不增删节点）
  与**样式修改**不改签名；其中"页面中部的小面积文案改动"是像素判据与结构判据的
  共同盲区（像素占比 < 2%）。要覆盖需文本指纹判据，本轮评估为"噪音成本高于收益"，
  不做；登记为长期项。
- **W-2（新增）**：签名里的文本截断到 120 字符（控制基线体积），长文案后半段的变化
  不进入判据。
- **W-3（新增）**：基线 159 KB 且每次结构改动会产生较长 diff —— 有意如此
  （门禁价值就在于让人看见"多了什么"），但需要审阅者读 diff 而不是无脑重生成；
  目前没有机制强制"重生成前必须审阅"。与 `--update-snapshots` 同性质。
- **W-4（结转 RECHECK-062 W-2）**：替身 harness 不校验 `Idempotency-Key`
  ⇒ mutating 调用的该约束只有 live 套件能守。GOAL-003 EC-05 就是修它。
- **W-5（结转 RECHECK-062 W-3）**：live 套件文件规模规则（400 行 soft / 450 行 hard）
  靠人工守住，`live-api-workflow.spec.ts` 已在 400 行边界。
- **W-6（结转 RECHECK-062 W-6）**：`webServer` 复用的 uvicorn 不保证"重启后仍健康"，
  live 套件首次跑偶发失败需重跑（本轮未出现）。
- **W-7（结转）**:`test-results/` 每次 Playwright 运行被清空 ⇒ 反证用例留下的对照截图
  只能当轮测量，不能当长期证据；本轮已把测量结果写进记录与 MEM-038。
