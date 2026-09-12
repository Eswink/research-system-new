---
id: RECHECK-20260912-040
plan_id: PLAN-20260912-040
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-12
completed_at: 2026-09-12
reviewer: independent-review-agent + root-agent-gate-evidence
baseline_ref: 2214479
checked_head: b86c693
---

# RECHECK-20260912-040 — 后端组成浮现与前后端接缝闭合独立复检

独立复检代理逐 AC 对抗性核查（不采信实现阶段完成声明；实跑定向测试 + 文档
逐路由 diff + 治理不变量实弹验证），根级收口门禁由主代理以实际命令输出补全。
AC-01~AC-04 可验证部分全部与代码/测试结果吻合，无 BLOCKER。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260912-040-frontend-backend-seams-and-surfacing.md`。
- 变更范围：WP-A `6d844e3`、WP-B `2022b02`、WP-C `d5abf18`、WP-D `af5df14`
  + 计划开立 `cc4c95d` + 扫描处置 `b86c693`。
- 边界：041（9 GAP 页新域/项目注册表）与 042（预算调整/真 pause-resume/实验
  队列/Diff/预测）零扩建；M18/M19（多用户/RBAC/身份）不触碰；example 树零
  `/api`（example-isolation 实跑证明）；pageSupport/CONSOLE_PAGE_MAP 保持诚实标注。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | `_assemble_sqlite` 注入 SqliteArtifactStore（blob 默认 `data/artifact-blobs`）/MemoryStore/ExperimentStore/WorkerRegistry；同实例共享编排与读端点；两 store 实现 Port；contract suite 注册 SqliteWorkerRegistry；artifact 写路径 `with self._conn` 事务化；evidence/claims 先 `get_run_or_error` → 404；`GET /health` + compose 改用 | `pytest test_composition_sqlite_persistence + test_experiment_store_sqlite + test_inspection_api + test_worker_registry_contract` = 52 passed（18 skip=无 PG）；`test_artifact_survives_reassemble` 实测重启持久 | PASS |
| AC-02（WP-B） | 八路由实存（approvals/roles·templates/custom/agents clone/DELETE×4）；CatalogOverrideStore Port+SQLite；draft delete 齐 Port/InMemory/SQLite/PG + 契约用例；compatibility role/profile 投影非恒空 + 空态用例；custom/clone 不在幂等豁免、无 Key → 422 实弹验证；引用 409 | `pytest test_wp_b_surface + test_protocol_draft_store_contract` = 17 passed；`git diff --stat 6d844e3 2022b02` 25 files +1151/-42 无文档虚增 | PASS |
| AC-03（WP-C） | example-console/data 直接 import 树外为 0（仅 exampleChrome 桥）；TEAM_REFERENCE_PROTOCOL 已删（grep 0）；SettingsPage 消费 isOperationDisabled；死组件（Tooltip/DataViewFrame/useCombinedView/Donut/Heatmap/useOperations hook）删除且零悬空 import；新 data-import 静态边界测试真实扫描 | `node --test production-boundaries.test.mjs` = 6/6；tsc 干净；`npm test` = 70/70 | PASS |
| AC-04（WP-D） | openapi 再生零漂移（快照含 9 新路由操作）；CONTROL_PLANE_API 72 提供路由逐条对照 `create_app().openapi()` = 0 高估、22 未提供标注确认不存在；CONSOLE_PAGE_MAP G 表与代码一致；store 缺失诚实 503 无 PG-only 伪装残留；mypy 759 源 0 错；ruff product roots 0；domain 无 vendor 类型 | `pytest test_openapi_snapshot` = 2 passed（运行后 git status 干净，字节覆写比较）；mypy/ruff 实跑 0；全仓 `pytest tests/api` DSN 固化 = 237 passed | PASS |

## 警告（不影响判定）

1. **F-1（已修于本收口 commit）** `services/api/routers/experiments.py` 模块
   docstring 残留「仅 PG canonical state；SQLite 503」——WP-A 双支持后过期，
   已更新为「SQLite 与 PG 双支持；未配置仍 503」。
2. **F-2（已补）** CONTROL_PLANE_API.md 漏记 3 条既存在路由
   （`GET /projects/{id}/runs`、`GET/PUT /projects/{id}/settings`）——低估方向，
   已在 Runs 节补全。
3. **F-3（已注）** 状态历史 WP-B「241 passed」为当时计数；test_wp_b_surface
   合并 orphan 用例后 DSN 固化复跑 237 passed，已在状态历史注明口径。
4. **F-4（记录，可接受）** `services/api/custom_catalog.py` 在 composition root 之外
   import `adapters.contracts.*`（与既有 `catalog_merge` 同模式：schema/domain
   loader 非 Port 旁路；不在 `.importlinter.api` 受限源内；team 路由自身零
   adapter import）。已登记入计划「已知风险」，收紧契约时一并显式豁免。
5. **F-5（已同步）** 计划范围原文表述「从 probe capability assertions 投影」与
   实现（合并目录 role/profile 声明投影）不符——已修正范围表述，与偏差记录一致；
   `endpoint_healthy_hint` 恒 None 属实（DTO 默认值，无设置点）。
6. **F-6（核真）** 三条偏差登记全部核对为真：endpoint DELETE 不 forget 凭据
   （CredentialResolver Port 无 forget 面，进程内重启即散）；draft delete 物理删
   修订；dev 路径 `/cluster/workers` 诚实返回 `{"workers": []}`。
7. 本 session 内 Mimosa PreToolUse 多次返回 scanner_enobufs 未完整扫描结论
   （Write/Edit 兼容放行）；项目级密封深度扫描已补跑并逐条处置
   （scan-2026-09-12T13-05-21 seal `sha256:d01ee46b…`：PLAN-040 新文件零命中，
   唯一产品树 HIGH 为既有 SafeLoader 子类误报，见 docs/audits/PA1_MIMOSA_REVIEW.md
   2026-09-12 节）；coverage 仍 static_only，不宣称「安全」。
8. m0 分组实跑：python 6、typescript 9、framework 8 全绿；stub e2e 30/30、
   live e2e 10/10（含新增 health/custom-role/clone/参考协议/审批历史面）。

## 结论

PLAN-20260912-040 AC-01~AC-04 全部满足；文档/计划一致性偏差在收口 commit 修正。
主树产品代码无新增安全 high（密封扫描 0 命中本批文件；唯一产品树 HIGH 为既有
SafeLoader 误报，已登记）。判定 **PASS_WITH_WARNINGS**，PLAN-040 关闭；下一项为
PLAN-20260912-041（GAP 新域与页面翻 live）。
