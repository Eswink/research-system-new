# Console 原型复刻与隔离示例数据交付记录（CONSOLE_REFERENCE_RECONSTRUCTION_DELIVERY）

授权计划：[PLAN-20260909-035](../../.cursor/plans/tasks/PLAN-20260909-035-console-reference-reconstruction.md)。
独立复检：[RECHECK-20260910-037](../../.cursor/plans/rechecks/RECHECK-20260910-037-console-reference-reconstruction.md)（PASS）。
设计来源：`project(1).zip`（SHA-256 `df70632fa6423d7d38984aeebfe5c6ab30d694043cbcf56b498c7cdeff54647a`，
归档于 [console-design](../references/design/console-design/ARCHIVE_NOTE.md)）。
上一轮交付（034）：[CONSOLE_DELIVERY.md](CONSOLE_DELIVERY.md)——本记录只覆盖本轮增量，不替代旧记录。

## 1. 交付内容

- **示例控制台（example-console）**：33 条路由的完整设计页面树
  （`apps/web/src/features/example-console/`），来自冻结原型源码的原生化移植
  （React 19 + TypeScript + CSS Modules，无 CDN/Babel runtime/iframe/eval）。
  数据全部来自 `data/*.json` 固定 fixture，状态为页内内存，切页即重置。
- **来源语义**：顶栏常驻 `SourceControl` 徽章（“示例数据 · 不写入后端”/“真实 API”）
  与 live/example 切换；`?source=` URL 参数可分享；auto 仅按
  `pageSupport` 登记的能力缺口选择示例，绝不按请求错误选择。
- **旧实时页面**：live 树（`LiveConsole` + features 各页）保持真实 API；
  compute 接入真实 ClusterPanel；endpoint 加载只门控首访接入与端点页。
- **协议编辑器**：live 草稿编辑器（ETag/幂等/模板 Compile→Preflight→Start）不变；
  示例协议页为 Form/源文档/分区/错误摘要/预检/确认门演示，启动按钮仅产生
  “示例门禁演示”页内回执。

## 2. 结构 / 交互 / 真实 API / 示例 / 缺口 分类

| 类别 | 内容 | 证据 |
| --- | --- | --- |
| 视觉结构 | 八域侧栏、紧凑顶栏、33 页设计布局 | 子代理对照 8 代表页 PASS；design-fidelity 33 路由基线 |
| 可用交互 | 搜索/过滤/选择/抽屉/Tab/确认门/局部编辑（示例内） | example-isolation e2e 3 项；console-shell 6 项 |
| 真实 API | run/timeline SSE、approvals decide（If-Match+幂等）、draft/compile/start、cluster、telemetry/cost/usage/claims/export、models probe、endpoints | test:e2e:live 3/3；pytest 24/24 |
| 示例数据 | 全部 example-console 页 + 顶栏工作区/Run 示例身份 | 33 路由零 /api 请求、零 pageerror 实测 |
| 后端缺口 | prompts/datasets/notebooks/reports/alerts/incidents/schedules/integrations/data-health/matrix/notifications 无 API；草稿预检、多项目、预算调整、文件浏览、Memory、账户等 | `pageSupport.GAPS` 逐页登记；live 态禁用并说明，示例态显式标记 |

## 3. 启动与切换方式

- 前端：`pnpm run dev`（vite :5173，`/api` 代理到后端）。
- 后端（本轮并行工作提供，非本任务范围）：`pnpm run dev:backend` /
  `dev:backend:status` / `dev:backend:stop`（tools/dev_backend.mjs）。
- 模式：顶栏徽章旁 “查看示例 / 真实操作” 按钮，或 URL `?source=example|live`；
  缺省 auto 按能力登记。示例页徽章与抽屉说明“切换页面将重置示例”。

## 4. 验证命令（本轮全部实测通过）

`pnpm run check`；`pnpm --dir apps/web typecheck|lint|test|build`；
`pnpm --dir apps/web test:e2e`（30 passed）；`pnpm --dir apps/web test:e2e:live`（3 passed）；
视觉对照采集 `node tools/console-reference/captureVisualCompare.mjs`。

## 5. 残余风险与回退

- 残余：兼容扩展页（compute/observability 示例态）无原型参考；顶栏徽章间距
  属 chrome 级视觉小项；示例文案为设计样例，不声明产品能力。
- 未做：Git 提交/推送、部署、后端扩建、Domain/API/schema 变更（授权边界外）。
- 回退：本轮改动全部位于 `apps/web/src|tests`、`tools/console-reference`、
  `.cursor/plans`、`docs/frontend`；按路径逐项恢复即可，无需 reset/clean；
  受保护六文件哈希与 protected-baseline.json 一致，未被覆盖。
