---
id: PLAN-20260915-065
slug: tool-pack-console-surface
title: ToolPack console 操作面 + live e2e 链（EC-02 前端收口）
status: IN_PROGRESS
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 3 = EC-02 的前端收口（后端写面已在 cycle 2 交付，RECHECK-064 记 PARTIAL）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-065-tool-pack-console-surface.md
memory_entries:
  - MEM-20260915-040-pending-must-be-visible-in-ui
---

# PLAN-20260915-065 — ToolPack console 操作面（GOAL-003 cycle 3 / EC-02 收口）

## 目标

cycle 2 把 ToolPack 供应链做成了**后端**写面（`/tool-packs` 四条路由 + 目录消费），
但 `pageSupport.GAPS.integrations` 仍如实写着"console 尚无操作入口"，EC-02 因此记
**PARTIAL**。本轮把这条链补到用户手上，并给出 live e2e 链（EC-02 的 verify 项）：

```text
ops/integrations 页面
  ├─ 已安装 ToolPack 表：id / 状态 / 生效 digest / capabilities / 待批准标记
  ├─ 安装表单：manifest JSON（含 digest）→ POST /tool-packs/install
  ├─ 待批准横幅：显示 diff（新增 capability / network domain / credential）+ 批准按钮
  └─ 吊销动作：理由必填 → POST /tool-packs/{id}/revoke
```

## 口径（这轮最容易做错的地方）

1. **"待批准"必须在界面上与"已生效"分开**：pending 不是"正在生效的版本"。
   横幅要展示 `pending.diff` 的具体新增项（用户不需要读 JSON 才知道批什么），
   并且表里的 digest 列**始终是生效版本**——若把 pending digest 显示成当前版本，
   这个 UI 就在撒谎。
2. **安装的输入是完整 manifest 文档**（含 `digest`）：控制面会重算并要求一致。
   表单必须让这件事可见——即 422 的 detail 原样呈现（"digest mismatch" 是用户要看的
   反馈，不是被吞掉的错误）。
3. **拒绝的原因要落在行内**：409（内置 id / 终态 / 无待批准）、422（内容或 capability
   非法）都显示在动作附近，不弹全局 toast。
4. **不新增后端语义**：本轮只做投影与动作；如果发现后端缺字段（例如需要 diff 明细），
   优先用 cycle 2 已经返回的 `pending.diff`，**不得**为了让 UI 好写而改后端语义。

## 范围

- 新增：`apps/web/src/api/toolPacksClient.ts`、`apps/web/src/features/integrations/ToolPackPanel.tsx`
  （+ 表单/待批准横幅，按 50 行函数与既有拆分风格拆小文件）、`apps/web/tests/e2e/stub-routes-toolpacks.ts`、
  `apps/web/tests/e2e/tool-pack-write.spec.ts`（stub）、`apps/web/tests/e2e/live-tool-pack-write.spec.ts`（live）。
- 修改：`IntegrationsPage.tsx`（挂面板）、`stub-routes.ts`（注册替身）、
  `tests/e2e/live-specs.ts`（登记 live 套件）、`pageSupport.ts`（GAPS.integrations 收敛）、
  `docs/frontend/CONSOLE_PAGE_MAP.md`（G15 行）、`docs/api/CONTROL_PLANE_API.md`（console 行，如有）。
- **设计基线**：`ops-integrations` 页面会真实变化 ⇒ 必须重生成 win32 + linux 的像素基线
  与 33 路由结构签名基线，并**目检**（这正是 cycle 1 交付的结构判据第一次在真实改动上生效）。

## 验收条件

- [ ] AC-01：`ops/integrations` 出现 ToolPack 面板，列出已安装 pack（id / state / 生效 digest /
  capabilities）；空列表是正确状态而不是错误态。
- [ ] AC-02：安装表单把 manifest JSON 提交给 `POST /tool-packs/install`；成功后面板出现该 pack；
  422（digest mismatch / 未知 capability）的 detail **在面板内可见**。
- [ ] AC-03：pending 呈现——扩张更新提交后出现待批准横幅（含 `diff` 明细与 pending digest），
  表中生效 digest **保持不变**；点批准后横幅消失、生效 digest 变为新值。
- [ ] AC-04：吊销——理由必填（空理由按钮禁用或 422 可见），成功后行状态为 REVOKED 且动作禁用。
- [ ] AC-05：stub 套件用**有状态替身**（`stub-routes-toolpacks.ts` + reset），覆盖上述四条路径。
- [ ] AC-06：live e2e 链（真实 uvicorn）：install → 扩张（pending，读面 digest 不变）→
  approve-update（digest 变化）→ revoke（终态）；登记进 `live-specs.ts`。
- [ ] AC-07：`pageSupport.GAPS.integrations` 与 `CONSOLE_PAGE_MAP.md` 的缺口描述收敛为
  "ToolPack 已可安装/批准/吊销"（仍缺 provider 凭据绑定与 schema 漂移比对）。
- [ ] AC-08：设计基线重生成并目检（win32 + linux 像素；结构签名 JSON 更新为真实新增节点），
  且**结构签名这次必须判红**——这是 cycle 1 判据的第一次真实拦截，记录其输出。
- [ ] AC-09：全量门禁：stub e2e / live e2e / web unit / eslint / tsc / 根 eslint / m0 23 项。
- [ ] AC-10：RECHECK-065 + MEM-040 + GOAL 记账；EC-02 由 PARTIAL → PASS（若 AC-01~09 全绿）。

## 实施清单

- [ ] WP-A 客户端与类型（`toolPacksClient.ts` + `types.ts` 增补）
- [ ] WP-B 面板与表单（pending 横幅、行内错误、吊销理由）
- [ ] WP-C 替身路由 + stub 用例
- [ ] WP-D live 用例 + `live-specs.ts` 登记
- [ ] WP-E 文案收敛 + 基线重生成目检 + 全量门禁 + 记录

## 证据

（WP 完成后回填：命令 + 真实输出）

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 2 交付后端写面后，EC-02 的剩余项是"用户能操作"
  与"live 链证明它真的能用"；本轮把 pending 的呈现语义先写清楚（AC-03 是核心：
  **生效版本与待批准版本在界面上不能混**）。

## 影响报告

（完成后回填）

## 已知风险

- **基线重生成是本轮最大的流程风险**：页面必然变化 ⇒ 结构签名与像素基线都要重生成；
  若忘记重生成，结构判据会红（这是正确行为，但会浪费一次全量 e2e）。
- **pending 语义在 UI 上容易被简化成"待处理"**：必须显示 diff 明细与"生效版本未变"，
  否则用户会以为已经升级。
- **manifest JSON 表单的可用性**：本轮以 JSON 文本框为最小可用形态（不造可视化编辑器），
  并在文案里说明"digest 必须与内容自洽，服务端会重算"——避免用户以为随便填一个 digest 就行。
