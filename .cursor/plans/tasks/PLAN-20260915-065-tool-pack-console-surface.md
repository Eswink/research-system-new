---
id: PLAN-20260915-065
slug: tool-pack-console-surface
title: ToolPack console 操作面 + live e2e 链（EC-02 前端收口）
status: DONE
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

- [x] AC-01：`ops/integrations` 出现 ToolPack 面板，列出已安装 pack（id / state / 生效 digest /
  capabilities）；空列表是正确状态而不是错误态。
- [x] AC-02：安装表单把 manifest JSON 提交给 `POST /tool-packs/install`；成功后面板出现该 pack；
  422（digest mismatch / 未知 capability）的 detail **在面板内可见**。
- [x] AC-03：pending 呈现——扩张更新提交后出现待批准横幅（含 `diff` 明细与 pending digest），
  表中生效 digest **保持不变**；点批准后横幅消失、生效 digest 变为新值。
- [x] AC-04：吊销——理由必填（空理由按钮禁用），成功后行状态为 REVOKED 且动作消失。
- [x] AC-05：stub 套件用**有状态替身**（`stub-routes-toolpacks.ts` + reset），覆盖上述四条路径。
- [x] AC-06：live e2e 链（真实 uvicorn）：install → 扩张（pending，读面 digest 不变）→
  approve-update（digest 变化）→ revoke（终态）；登记进 `live-specs.ts`。
- [x] AC-07：`pageSupport.GAPS.integrations` 与 `CONSOLE_PAGE_MAP.md` 的缺口描述收敛为
  "ToolPack 已可安装/批准/吊销"（仍缺 provider 凭据绑定与 schema 漂移比对）。
- [x] AC-08：设计基线重生成并目检（win32 + linux 像素；结构签名 JSON 更新为真实新增节点），
  且**结构签名这次判红**——`ops-integrations` +18 个节点，输出见「证据」。
- [x] AC-09：全量门禁：stub e2e 72 / live e2e 33 / web unit 76 / eslint（0 error）/
  tsc / 根 eslint / m0 23 项（`PASS: profile=m0; 23 deterministic checks`）。
- [x] AC-10（**范围收窄，见状态历史**）：本 PLAN 的十条 AC 全绿；GOAL 级 EC-02 仍有
  **一个未交付子句**——"健康复核记录 schema digest 并可比对漂移"（无真实探测面，
  与 provider 凭据绑定同属后续 cycle），因此 EC-02 本轮**保持 PARTIAL**，
  GOAL 记账已写明剩余范围。

## 实施清单

- [x] WP-A 客户端与类型（`toolPacksClient.ts` + `types.ts` 增补 + `client.ts` 四方法）
- [x] WP-B 面板与表单（pending 横幅、行内错误、吊销理由）
- [x] WP-C 替身路由 + stub 用例（6 条）
- [x] WP-D live 用例 + `live-specs.ts` 登记 + Python 生成的 manifest fixture + 同步守卫
- [x] WP-E 文案收敛 + 基线重生成目检 + 全量门禁 + 记录

## 证据

| 声称 | 命令 / 观察 | 结果 |
| --- | --- | --- |
| 面板 + 四条路径在 stub 下可用 | `pnpm exec playwright test tool-pack-write`（有状态替身） | 6 passed |
| 扩张在界面上**未生效**直到批准 | 同套件：提交扩张后横幅出现 + `toolpack-diff-<id>` 含 `audit.write`，`toolpack-digest-<id>` 的 `title` **仍是旧 digest**；点批准后横幅消失、`title` = 新 digest | PASS |
| 422 detail 落在面板内 | stub：篡改 `license` → `toolpack-install-error` 含 "digest mismatch"，且该 pack 未进表；live：同一断言打在真实 uvicorn 上 | 两侧 PASS |
| live 全链（真实 HTTP + 真实 SQLite） | `pnpm exec playwright test --config playwrightLive.config.ts tool-pack-write` | 2 passed |
| live 的 digest 是真口径 | fixture 由域代码生成（`manifest_document`）并由 `tests/tooling/test_console_toolpack_fixtures.py` 守住"仓库文件 == 域现算" + vocabulary 校验 | 2 passed |
| 终态不可重装 | live：吊销后同 id 再 `POST /install` → **409** | PASS |
| 结构判据真的拦住了整块新增（AC-08） | 未设 `UPDATE_OUTLINES` 时跑 `design-fidelity`：红，`drifted = ["ops-integrations"]`，节点差 **+18 / -2**（`section kids=3→4`、`div testid=toolpack-panel`、`toolpack-install-form`、`textarea`、`toolpack-note`…）；输出存 `scratch/cycle3-design/outline-red-output.txt` | PASS（首次真实拦截） |
| 同一改动像素判据仍不报警 | 同一次运行里 33 条像素用例全绿（2% 阈值）⇒ 与 cycle 1 的实测结论一致（结构管增删、像素管面积） | PASS（缺口已知） |
| 基线重生成且跨平台一致 | `UPDATE_OUTLINES=1 … design-fidelity` 重生成（1 行变更）；`bash scratch/verify_linux_outlines.sh` → `host routes=33 linux routes=33 drifted=[]` / `PASS: 33 条结构签名跨平台一致（win32 == linux）` | PASS |
| 像素基线（两平台）重生成 + 目检 | `bash scratch/gen_linux_baseline_route.sh ops-integrations`（pinned noble 容器）+ 本机 `--update-snapshots`；两张图目检：面板/表单/空态渲染正确、无溢出 | PASS |
| 全量门禁 | stub e2e 72 / live e2e 33 / web unit 76 / `pnpm lint` 0 error（1 条既有 soft warning）/ `tsc --noEmit` 通过 / `tests/tooling+api+application` 1890 passed / m0 23 项 | PASS |

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：cycle 2 交付后端写面后，EC-02 的剩余项是"用户能操作"
  与"live 链证明它真的能用"；本轮把 pending 的呈现语义先写清楚（AC-03 是核心：
  **生效版本与待批准版本在界面上不能混**）。
- 2026-09-16 范围收窄（AC-10 改写，原因如实登记）：实施中发现两件计划外的事实——
  (1) live 链路第一次跑就撞上"平台默认策略没有 `tool_pack.*` 规则 ⇒ default DENY"，
  真实部署下 console 写面会 403（既有缺口，夹具层放行并记入 RECHECK-065 W-1）；
  (2) GOAL 级 EC-02 的第三个子句（健康复核 schema digest + 漂移比对）本 PLAN 未覆盖，
  且它与 provider 凭据绑定同属"需要真实探测面"的一类。为避免用"前端收口"冒充整个 EC-02，
  AC-10 由"EC-02 PARTIAL → PASS"收窄为"本 PLAN 十条 AC 全绿 + EC-02 保持 PARTIAL，
  剩余范围写进 GOAL"。这不是降低门槛，而是把没做的事写在明处。
- 2026-09-16 完成（DONE）：AC-01~09 全绿，AC-10 按收窄后的口径达成；
  RECHECK-20260915-065（PASS_WITH_WARNINGS）与 MEM-20260915-040 已写。

## 影响报告

- **Domain/API/schema**：无变更（本轮只消费 cycle 2 的四条路由；`services/api/**`、
  `packages/**` 未改）。
- **测试层新增**：`apps/web/tests/e2e/stub-routes-toolpacks.ts`（有状态替身，含 canonical
  JSON → sha256 的**镜像**口径）、`tool-pack-write.spec.ts`（6 条）、
  `live-tool-pack-write.spec.ts`（2 条）、`fixtures/toolpack-live-manifests.json`
  （域代码生成）、`tests/tooling/test_console_toolpack_fixtures.py`（同步守卫）、
  `tests/api/console_api_app.py` 的 `_ConsoleToolPackPolicy`（夹具层放行四个能力）。
- **安全/凭据**：无凭据引入；**默认策略语义未改**（`examples/config/policy.yaml` 未动），
  但本轮**发现**真实默认下 `tool_pack.*` 为 DENY（写成缺口 + RECHECK W-1 + GOAL 后继项）。
- **兼容性/迁移风险**：无数据迁移；页面新增一个面板 ⇒ 两条设计基线（结构签名、
  win32/linux 像素）已重生成；其他 32 条路由的基线未动（linux 脚本只覆盖目标路由）。
- **上游版本影响**：无新依赖、无 pin 变更。
- **下一项任务**：EC-02 剩余子句（健康复核 schema digest + 漂移比对）与 EC-03（ops 调度写面）
  由 GOAL 循环 ④ 起决定。


## 已知风险

- **基线重生成是本轮最大的流程风险**：页面必然变化 ⇒ 结构签名与像素基线都要重生成；
  若忘记重生成，结构判据会红（这是正确行为，但会浪费一次全量 e2e）。
- **pending 语义在 UI 上容易被简化成"待处理"**：必须显示 diff 明细与"生效版本未变"，
  否则用户会以为已经升级。
- **manifest JSON 表单的可用性**：本轮以 JSON 文本框为最小可用形态（不造可视化编辑器），
  并在文案里说明"digest 必须与内容自洽，服务端会重算"——避免用户以为随便填一个 digest 就行。
