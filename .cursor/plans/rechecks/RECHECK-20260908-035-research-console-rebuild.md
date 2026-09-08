---
id: RECHECK-20260908-035
plan_id: PLAN-20260908-033
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-08
completed_at: 2026-09-08
reviewer: root-agent-independent-pass
baseline_ref: 9f39dd3
checked_head: working-tree-on-9f39dd3
---

# RECHECK-20260908-035 — Research Console 全站重建独立复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260908-033-research-console-rebuild.md`。
- 验收条件：AC-01 至 AC-08；复检从原始目标重查，不继承实现阶段的完成声明。
- 变更范围：`apps/web/`（tokens/base 样式、AppShell/Sidebar/TopBar、共享组件、
  类型化 hash 路由、i18n zh+en、preferences、协议草稿编辑器
  `features/protocol/editor/`、Playwright e2e）、`packages/application/protocol_authoring/`、
  `packages/application/ports/protocol_draft_store.py`、`adapters/{sqlite,postgres}/protocol_draft_store.py`、
  `adapters/contracts/protocol_text_loader.py`、`services/api/{routers,dto}/protocol_drafts.py`、
  `services/api/routers/runs.py`（草稿修订引用扩展）、`services/api/{composition,pg_composition}.py`（注入）、
  `adapters/postgres/migrations/013_protocol_drafts.sql`、`docs/{frontend,references,api}`、
  `docs/INDEX.md`、`.cursor/plans/`（计划 + 本复检）。
- 保留边界：Domain 状态机、ProtocolDefinition Schema、RunManifest 语义、既有 REST
  契约（仅增量扩展）、`FRAMEWORK_MANIFEST.json`（未修改）、`docker-compose.personal.yml`
  等生产部署文件、无关用户改动。
- 基线：Git HEAD `9f39dd3`，未 commit、未 push、未刷新 FRAMEWORK_MANIFEST.json。
- 门禁环境：Docker Desktop（postgres-test 容器 healthy）；DSN 键经进程环境钉定
  （`RESEARCHOS_POSTGRES_DSN`＝postgres-test 凭据、其余 DSN 键空串），阻断 litellm
  import 时 `load_dotenv()` 将操作员 `.env` 的 personal-production DSN 注入测试进程
  （PA-1 F-1 已知门禁环境非封闭问题的再现与处置，见 Findings F-01）。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围、Canonical State 与安全边界 | 当前 diff；Domain 状态机/Schema/状态机未改；013 migration 只增表；模板只读白名单；YAML strict loader（SafeLoader 子类 + 重复键拒绝）；错误脱敏；无新凭据面；CSP 未放宽 | PASS |
| G-02 | AC-01 设计基准 | `docs/references/design/protocol-visual-editor/`（6 设计文件 + ARCHIVE_NOTE）；`docs/frontend/CONSOLE_REBUILD.md`（11 路由清单 + 设计控件→真实契约映射 + 验收基准）；`docs/INDEX.md` 两处挂链；docs_consistency_check PASS | PASS |
| G-03 | AC-02 设计系统与外壳 | tokens.css 逐值复用；双主题/双密度/中英文切换持久化（`ros.console.preferences` 唯一 localStorage 面）；AppShell/Sidebar/TopBar；hash 路由刷新恢复（e2e 断言）；web lint/typecheck/test 46 pass/build 全绿 | PASS |
| G-04 | AC-03/AC-07 协议草稿后端 | 存储契约 8 tests（InMemory/SQLite 同语义：CRUD/乐观并发 412/幂等重放/修订不可变/跨 reopen 持久化）；服务 9 tests（schema 定位错误/重复键拒绝/体积限制/模板白名单）；API 10 tests（模板目录/校验零副作用/CRUD/428/412/重放/404）；链路 4 tests（修订启动冻结 manifest、修订 2 不改写冻结运行、404/422 边界）；`pytest tests/postgres` 63 passed（013 migration 真实 PG 应用）；mypy 728 files 0 errors；ruff 全绿 | PASS |
| G-05 | AC-04 编辑器闭环 | 状态机 7 tests（dirty/canSave/canStart P1 门禁/迟到响应丢弃/stale 报告/conflict 保留草稿）；转换 4 tests（真实协议解析/往返不丢字段/解析失败不静默/枚举回退）；e2e 5 passed（Form/YAML 切换保留内容→Identity 区渲染、保存→saved、Start 门禁禁用）；api.startRun 接受 `{draft_id, draft_revision}`，服务端同链 Compile→Preflight→Freeze | PASS |
| G-06 | AC-05 全站迁移 | 11 路由全部接入外壳（Sidebar 真实页面；空页不造）；TeamPage/RunPanel/EndpointsHome 空态补齐；error/loading/403 语义保留；旧聚合页拆分为独立域页面；DryRunPanel/useDryRun/ReportView/ProjectionTable 删除（被编辑器取代）；production-boundaries 5/5（无货币数学/无判定词/无厂商 SDK/无循环依赖） | PASS |
| G-07 | AC-06 浏览器验收 | Playwright 1.56.1（精确 pin）+ Chromium 141；确定性 API 替身（page.route，无真实后端/付费 LLM/凭据）。首次签署后补充轮（同日，同基线）补齐 AC-06 其余子项：**e2e 67 passed**＝44 张截图基准（11 路由 × dark/light × normal/compact × zh/en，`toHaveScreenshot` maxDiffPixelRatio 0.02，基准入库 `tests/e2e/screenshots.spec.ts-snapshots/`）+ 3 键盘可达/焦点恢复（Tab 首停为侧边导航项且 :focus-visible 焦点环非 none；模板面板打开焦点入面板、Esc 与关闭按钮关闭后焦点恢复到触发按钮）+ 15 屏宽断言（1440/1280/1024/768/390 × 3 代表路由 `scrollWidth − clientWidth ≤ 1` 无横向溢出）+ 既有 5 项闭环断言；两次连续完整运行均 67/67，基准比对稳定；伴随实现补强：模板面板 Esc 关闭、autoFocus 入面板、关闭后焦点恢复（useEffect commit 后恢复）。复检签署保持有效：补充内容未触碰 Domain/API/Schema/安全边界，仅前端 e2e 与编辑器面板交互增强，重跑受影响面（web lint/typecheck/test 46/build、e2e 67、production-boundaries 5、governance validator）全部 PASS | PASS |
| G-08 | AC-08 全量门禁 | `run_all_checks.py --profile m0 --keep-going` 返回 0：**23/23 deterministic checks PASS**；Python 收集 3059 passed / 6 skipped（0 failed）；web test 46 pass；typecheck/build、bundle/governance validators、hook/learning/framework evals、docs consistency、release-assets-immutable 全部 PASS | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | 门禁环境（非产品缺陷，已处置） | litellm import 时 `load_dotenv()` 将操作员 `.env` 的 personal-production DSN（旋转密码@15432）注入测试进程，`tests/postgres` parity 套件在完整 m0 内连接失败（standalone 通过）——PA-1 F-1"门禁环境非封闭"的再现 | 按 RECHECK-20260906-032 先例，在运行器进程环境钉定 DSN 键（测试 DSN / 空串），未修改仓库代码；完整 m0 复跑 23/23 PASS。操作员侧长期方案（.env 与分段门禁隔离）记入 BACKLOG 建议 |
| F-02 | 门禁环境（瞬态，复跑通过） | Windows 文件锁偶发：`evolution_state.json.tmp → os.replace` PermissionError 使 framework evals 单次失败 | 独立复跑 `run_cursor_framework_evals.py` PASS；最终完整 m0 内 PASS |
| F-04 | 验收覆盖（已关闭） | 首次签署的 G-07 仅覆盖 e2e 5 项，未覆盖 AC-06 声明的截图基准、双密度/中英文视觉、目标屏宽与键盘/焦点恢复子项（弱验证） | 同日补充轮补齐：44 截图基准 + 15 屏宽 + 3 键盘焦点断言并两次复跑稳定；G-07 证据已更新，本复检重新签署为 PASS |
| F-03 | 边界（已修复） | 初版 `services/api/routers/runs.py` 直接 import `adapters.contracts.protocol_text_loader`，违反 `.importlinter.api`（routers 不得 import adapters）；应用层 `text_loader.py` 初版含函数内 import adapters，违反 `.importlinter.application` | 改为应用层 `ProtocolTextLoader` Protocol + DraftService 构造器注入（composition root 装配 adapters 实现）；lint-imports 3 kept / 0 broken |

## 决策与偏差（复检期间）

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-08 | 首次签署后同日补充 AC-06 缺口（截图基准/屏宽/键盘焦点）并更新 G-07 证据 | 复检自查发现 G-07 为弱验证（验收器指出）；按验收条件补齐而非延后 | 仅前端 e2e 与模板面板交互增强；受影响面重跑全 PASS；结论维持 PASS，签署更新为补充轮后版本 |

## 结论

- 结果：`PASS`。
- 理由：AC-01 至 AC-08 的 hard gate 均有独立、可复现的运行证据；最终完整 m0 profile
  23/23 PASS（Python 3059 passed/6 skipped、web 46 pass、e2e 5 passed、bundle/
  governance/docs validators、release-assets-immutable）。
- 安全结论：模板只读受控目录（不接受任意路径）；YAML 安全加载（SafeLoader 子类 +
  重复键拒绝 + 体积限制）；错误脱敏；无新凭据面；浏览器持久化仅偏好；CSP/网络/
  Memory 写入/运行权限边界未放宽；冻结运行不可被草稿修订改写（E2E 断言）。
- 兼容性结论：Domain/API 既有契约仅增量（旧 `protocol_path` 请求保留兼容）；
  013 migration 只增表且在隔离 PG 验证；回退应用后草稿数据保留；`FRAMEWORK_MANIFEST.json`
  未修改；未 commit/push。
- 后续动作：将 PLAN-20260908-033 标记 `DONE` 并更新 ALL_PLAN；litellm dotenv 门禁
  封闭性长期方案建议登记 BACKLOG（F-01，操作员 .env 与分段门禁隔离）。
