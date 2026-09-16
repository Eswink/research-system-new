---
id: RECHECK-20260915-065
plan_id: PLAN-20260915-065
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle3
baseline_ref: ed4ed59
checked_head: ed4ed59+worktree
---

# RECHECK-20260915-065 — ToolPack console 操作面 + live 链（GOAL-003 cycle 3 / EC-02）

## 检查范围

PLAN-20260915-065 声称的交付面：`toolPacksClient.ts` + `types.ts`/`client.ts` 四方法、
`ToolPackPanel`/`ToolPackInstallForm`/`ToolPackPendingBanner`/`ToolPackRevokeControl`/
`toolPackColumns`/`toolPackCopy`、`IntegrationsPage` 挂载、有状态替身
`stub-routes-toolpacks.ts` + 6 条 stub 用例、域代码生成的 live fixture
（`tests/tooling/test_console_toolpack_fixtures.py` 守同步）+ 2 条 live 用例 +
`live-specs.ts` 登记、`pageSupport`/`CONSOLE_PAGE_MAP`/`CONTROL_PLANE_API` 文案收敛、
两条设计基线重生成。**未覆盖**：GOAL 级 EC-02 的"健康复核 schema digest + 漂移比对"
（本轮范围收窄，见 W-4）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| pending 与生效版本在界面上不混（AC-03 核心） | stub：扩张提交后 `toolpack-pending-<id>` 出现且 diff 含 `audit.write`，`toolpack-digest-<id>` 的 `title` **仍是旧 digest**；点批准后横幅 `toHaveCount(0)`、`title` = 新 digest | PASS |
| live 上同样成立（真实 digest、真实 SQLite） | `live-tool-pack-write.spec.ts`：install(201 INSTALLED) → 扩张（读面 `pack.digest` 不变、`pending.digest` = 候选）→ approve（`pack.digest` 变）→ revoke（REVOKED、`catalog_digest_active=false`） | PASS |
| 终态真的终态 | live：吊销后同 id 再 install → **409**；stub：REVOKED 行只剩理由文本、没有动作按钮 | PASS |
| 422 detail 在面板内，不被吞 | stub（篡改 `license`）与 live（同一 fixture 篡改）都断言 `toolpack-install-error` 含 `digest mismatch`；错误经 `useAsyncAction` → `ApiError.message = problem.detail` | PASS |
| 吊销理由必填 | stub：空理由按钮 `toBeDisabled`；后端仍会 422（两侧语义一致） | PASS |
| live fixture 的 digest 是真口径而非手写 | fixture 由 `manifest_document()` 生成；`test_console_toolpack_fixtures.py` 守"仓库 JSON == 域现算"+"capability ∈ 平台词表"（2 passed） | PASS |
| 结构判据首次真实拦截（AC-08） | 未设 `UPDATE_OUTLINES` 跑 `design-fidelity`：**红**，`drifted=["ops-integrations"]`，节点 **+18 / -2**（新 `section`、`div testid=toolpack-panel`、安装表单、textarea、`toolpack-note` 等）；输出存 `scratch/cycle3-design/outline-red-output.txt` | PASS |
| 像素判据对同一改动仍不报警 | 同一次运行 33 条像素用例全绿（阈值 2%）⇒ 结构判据补的正是这块盲区 | PASS（缺口已知，非本轮引入） |
| 基线重生成 + 跨平台一致 | `UPDATE_OUTLINES=1 …design-fidelity` 重生成（diff = 1 行）；容器 `verify_linux_outlines.sh` → `host routes=33 linux routes=33 drifted=[]` / `PASS: 33 条结构签名跨平台一致（win32 == linux）` | PASS |
| 像素基线两平台重生成 + 目检 | `gen_linux_baseline_route.sh ops-integrations`（pinned `v1.56.1-noble`）+ 本机 `--update-snapshots`；两张 PNG 目检：面板/表单/空态/脚注渲染正确、无溢出、无缺少的样式 | PASS |
| 全量门禁 | stub e2e **72 passed**（+6）/ live e2e **33 passed**（+2）/ web unit **76 passed** / `pnpm lint` 0 error 1 warning（既有 400 行 soft warning）/ `pnpm typecheck` 通过 / `tests/tooling+api+application` **1890 passed, 1 skipped** / 全量 pytest **3436 passed, 8 skipped** / m0 `PASS: profile=m0; 23 deterministic checks` | PASS |
| 文档与文案收敛 | `pageSupport.GAPS.integrations` 改为"已可操作（…待批准版本在横幅里、表中 digest 始终是生效版本…）"；`CONSOLE_PAGE_MAP` 的 `#/ops/integrations` 段与 G15 行同步；`CONTROL_PLANE_API` 增 console 段；`docs_consistency_check` 10 passed | PASS |
| 安全扫描（sealed） | Mimosa deep scan `scan-2026-09-16T07-54-46.761Z-26a2733ef0fc`，seal `sha256:67261e0898df1e02f610d46387c98b21336907d5c0c20a27571af9d2b0abc9fa`：**36 findings，与上一轮扫描（06:17 同项目）计数相同，且按文件名过滤后与本轮改动相关的命中为 0**（既有项为 pickle/yaml 反序列化、随机性、`postgres/db.py` 环境变量→SQL 等） | PASS |
| CI（本 cycle 提交 `ce28e05`） | run **35071216707**：eval-gate 07:58:06Z / collector-quality 07:59:51Z / container-quality 08:01:43Z / console-frontend 08:04:13Z / quality-ubuntu-latest 08:04:18Z / **quality-windows-latest 08:09:07Z** —— 六个 job 全 `success`，无重跑 | PASS |

## 告警

- **W-1（新发现，产品级）**：平台默认策略 `examples/config/policy.yaml` **没有**
  `tool_pack.*` 规则 ⇒ `default_effect: DENY`，真实部署下 console 写面（以及任何
  调用 lifecycle 的路径）会 403。live 用例第一次运行即撞上
  `policy denied capability tool_pack.install for pack live_console_pack`（面板如实显示）。
  本轮**在夹具层**放行（`tests/api/console_api_app.py::_ConsoleToolPackPolicy`，
  只放行四个能力、不放宽产品策略），并在 `CONTROL_PLANE_API.md` / `CONSOLE_PAGE_MAP.md`
  写明。**待产品决策**：是加 allow 规则，还是把 policy.yaml 里既有的
  `action: TOOL_PACK_INSTALL_OR_UPDATE`（现在语义上没被消费——lifecycle 只传 capability、
  且 `_require_decision` 只对 DENY 阻断）改成"REQUIRE_APPROVAL → 登记为待批准"。
- **W-2**：替身 `stub-routes-toolpacks.ts` 里的内容 digest 是**镜像实现**（canonical JSON
  → sha256，`node:crypto`），不是域口径的权威副本；它只保证 stub 场景自洽。权威口径由
  后端测试与 live 用例证明（live 用的是域代码生成的 digest）。
- **W-3**：面板的 manifest 输入是 JSON 文本框（计划里已声明的最小可用形态）；
  没有可视化编辑器，也没有本地 schema 校验（只解析 JSON 形状），字段级错误仍由服务端 422 给。
- **W-4**：GOAL 级 EC-02 仍有未交付子句——"健康复核记录 schema digest 并可比对漂移"
  （provider 侧；需要真实探测面，与 provider 凭据绑定同族）。本轮 AC-10 已收窄并把
  该项写进 GOAL 后继入口，**EC-02 保持 PARTIAL**。
- **W-5**：`catalog_digest_active` 由后端以 `state is INSTALLED` 投影（cycle 2 口径），
  不是"目录合并确实执行过"的独立证据；UI 列名沿用"目录"（与注册表列同措辞）。

## 结论

result: **PASS_WITH_WARNINGS**

交付面成立：pending/生效分离在 stub 与 live 两侧都被断言（含 digest 不变→变化），
422 detail 落在面板内，终态不可重入；结构判据第一次在真实改动上拦红（+18 节点），
像素判据同一次运行不报警——两条判据的互补关系在真实改动上得到验证。W-1 是**产品级
新发现**（默认策略未放行 `tool_pack.*`），已如实登记而不在循环内改产品策略。
