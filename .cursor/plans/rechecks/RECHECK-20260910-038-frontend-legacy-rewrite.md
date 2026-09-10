---
id: RECHECK-20260910-038
plan_id: PLAN-20260910-036
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-10
completed_at: 2026-09-10
reviewer: independent-judge-agent + root-agent-gate-evidence
baseline_ref: 632bc3c
checked_head: working-tree-on-632bc3c
---

# RECHECK-20260910-038 — 前端最早一批遗留页面与组件重写独立复检

独立复检代理逐文件对抗性核查（不采信实现阶段完成声明），根级门禁由主代理以实际命令输出补全。
AC-01 至 AC-06 全部 PASS。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260910-036-frontend-legacy-rewrite.md`。
- 变更范围：`apps/web/src/features/setup/`（向导全树重写）、`apps/web/src/LiveConsole.tsx`、
  `apps/web/src/features/operations/useCluster.ts` 与 `ComputePage.tsx`（一行）、
  `apps/web/src/features/protocol/editor/`（外壳视觉层）、`apps/web/src/layout/TopBar.module.css`、
  `apps/web/src/i18n/`（setup 键切片 + editor.*.tip）、`apps/web/tests/e2e/` 基线一张、`.cursor/plans/`。
- 保留边界：`wizardApi.ts` 与 `tests/unit/wizard-flow.test.ts` 对 HEAD 零 diff（复检代理 git diff 确认）；
  `ClusterPanel.tsx` 零 diff；Domain/API/schema/migration 零改动
  （`git status --porcelain -- services packages adapters migrations` 为空）。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | 零裸元素与诚实性分支 | 复检 grep：features/setup 无裸 `<button`；全部 Button/cx("btn")；CSS 全走 module + var(--token)，无裸色值；i18n 全覆盖（仅 wizardApi 诊断串按契约保留英文、UI 以 mono 技术细节呈现）；DoneStep 失败分支 probe-failure + Retry/Finish Anyway 在位；"配置可重复"非"完全可复现" | PASS |
| AC-02 | testid 与逻辑契约 | 10 个 data-testid 全部在位（复检逐文件行号）；wizardApi.ts 与 wizard-flow.test.ts 零 diff；design-fidelity 以 relay-wizard 断言通过 | PASS |
| AC-03 | useCluster 迁移 | useResource("cluster") 实现；消费字段保持；ComputePage 仅 void 一行；70/70 单测 | PASS |
| AC-04 | 编辑器外壳对齐 | Sections .input 完整控件规格；segment 半径/间距；vrShort 16px；active hover 抑制；tip 键 + title 接线 | PASS |
| AC-05 | 顶栏间距 | TopBar.module.css .right gap 14px（含 RECHECK-037 溯源注释） | PASS |
| AC-06 | 门禁 | 复检代理实跑 typecheck/lint/单测 70/70/backend-clean；主代理实跑 build ✓、test:e2e 30/30 ✓、test:e2e:live 3/3 ✓、根 eslint . ✓、根 typecheck ✓、depcruise 0 violations（857 modules）；快照仅 library-setup 一张变化并获视觉走查批准 | PASS |

## 补充核查

- setupZh.ts / setupEn.ts 键集合双向差集为空（各 67 键）。
- 视觉走查五图（scratch/frontend-legacy-rewrite-20260910/step*.png）：四步 + 失败分支渲染
  与控制台设计一致，无溢出、无未样式区域。

## 发现（非阻断）

- F-1（Low）：select 下拉箭头与 checkbox 为浏览器原生控件外观（Win32 浅色），与参考设计同源
  （参考树同样使用原生 select/checkbox），快照容差内通过；如需完全自绘另立任务。
- F-2（Info，范围外）：ComputePage 刷新按钮仍是 v1 裸 button + zh 三元式（本计划一行 diff 之外），
  属 ops 页残留样式债务，建议纳入下一轮 usage-driven 清单。
- F-3（Info）：scratch 走查脚本与截图为工程证据，gitignored，不入产品树。

## 结论

PASS。PLAN-20260910-036 全部 AC 有独立证据支持；偏差（i18n 切片、DIRTY mono 令牌、
useCluster 死字段移除）已在计划偏差记录中留痕。
