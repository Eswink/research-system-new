---
id: RECHECK-20260914-047
plan_id: PLAN-20260914-047
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-14
completed_at: 2026-09-14
reviewer: root-agent-gate-evidence
baseline_ref: 2d520f7
checked_head: working-tree (pre-commit)
---

# RECHECK-20260914-047 — 制品内容 Diff 独立复检

GOAL-20260912-001 cycle 7（EC-04 第二批）派生计划的复检。本 cycle 的关键语义决定是
**把"文件 diff"收敛为"制品内容 diff"**（控制面没有 workspace 快照枚举面，
`WorkspaceBackend` 只在 CLI 参考链装配），并把"不可比"做成**一等事实**
（`available=false` + 显式 reason + 200），而不是回一个空 diff 冒充"无差异"。
复检以「本地全门命令输出 + 定向 e2e + live 真实 HTTP」为权威证据，重点对抗核查三处
诚实性：二进制不被"看起来一样"地判等、超限不截断冒充全量、live 正向链不是空列表假绿。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-047-artifact-content-diff.md`
  （`parent_goal: GOAL-20260912-001`，EC-04 第二批）。
- 变更范围：应用层 `packages/application/artifacts/diff.py`；API
  `routers/artifacts.py`（+83 行）与 `dto/artifacts.py`（+29 行）；前端 workspace
  4 文件 + 3 个 client/types + CSS；`docs/api/CONTROL_PLANE_API.md`、
  `docs/api/openapi.m13.json`（+163 行）、`docs/frontend/CONSOLE_PAGE_MAP.md`、
  `navigation/pageSupport.ts`；live 装配 `tests/api/console_api_app.py`；
  playwright 两个配置；测试 10（应用层）+ 4（API）+ 2（stub e2e）+ 2（live e2e）。
- 边界：不做文件系统 diff / 不做 ReproducibilityAudit / 不落库；真 pause-resume 执行
  协调、实验队列、memory capability policy（G16）属后续 cycle；无新表、无迁移。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 纯函数覆盖 变更/相同/二进制/超限/非 UTF-8/截断；无副作用 | `pytest -q tests/application/test_artifact_diff.py` = 10 passed；模块无 IO、无 store 依赖（只 import `difflib`/`dataclasses`/`enum`） | PASS |
| AC-02（WP-B） | 404/503/410/200+unavailable 分支；identical 语义；openapi 零漂移 | `pytest -q tests/api/test_artifacts_api.py tests/application/test_artifact_diff.py` = 21 passed；`test_openapi_snapshot` 2 passed（再生后无漂移） | PASS |
| AC-03（WP-C） | workspace 页可选两侧 + 渲染；不可比原因可见；三处文档同步；web 门全绿 | stub e2e `workspace-diff.spec.ts` 2/2；`pnpm --dir apps/web lint`（--max-warnings 0）+ `typecheck` 绿；unit 73 passed；pageSupport G8 / CONSOLE_PAGE_MAP G8 / CONTROL_PLANE_API 同步 | PASS |
| AC-04（WP-D） | 本地全门 + stub/live e2e + m0 + CI 终态 | 全量 pytest 3297 passed/6 skipped/0 failed（DSN 固化，postgres 用例实跑）；m0 23/23 PASS（`uv run` + 测试容器 + DSN 固化）；live 套件 17/17；ruff check/format + mypy 4 文件 Success；CI run 见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍是 RECHECK-042/043/044/045/046
   登记的**同 2 项** timing flake；其余 job 的终态见 GOAL 迭代日志。按 fix_policy 不放宽
   断言、不 skip、不改 workflow（治理面）。
2. **W-2（WARNING，新增）** live 正向链依赖 **test-only 装配注入的受控制品**
   （`console_api_app.LIVE_DIFF_ARTIFACTS`）。实测该 live 链的 m12 参考协议在 Fake 执行下
   run 终态 FAILED、`GET /runs/{id}/artifacts` 恒 0 条（无后台 worker）。因此 live 用例
   证明的是"真实 HTTP + 真实 diff 计算 + 真实 404 语义"，**不**证明"真实执行产物可被
   diff"——后者要等真实执行链在 live 装配里可用（已记入 MEM-20260914-024）。
3. **W-3（WARNING，新增）** diff 是**内容级**比较，不携带"文件路径/工作区快照"语义：
   两侧是 content-addressed 制品，响应里以 `comparison=ARTIFACT_CONTENT` + note 标注，
   pageSupport G8 也写明"文件树与文件级快照 Diff 无 API"。若用户期待的是"两次 run 的
   工作区文件差异"，那属于未交付能力（无 API），不是本 cycle 的静默降级。
4. **W-4（INFO）** 实现与计划文字的差异已在计划「证据」节如实记录：`diff_texts(...)`
   → `diff_artifacts(DiffSide, DiffSide)`（规避 ruff PLR0913，语义等价）；live 证据来源
   从"参考链产出"改为"受控 fixture 注入"。
5. **W-5（INFO）** 安全扫描口径：本次 commit/push 时 Mimosa 未返回完整扫描结论
   （`scanner_enobufs`），按既有兼容策略继续且**不宣称项目安全**；完整性审计待专门运行
   （GOAL EC-06 已列）。
6. **W-6（INFO）** stub e2e 用**用例内路由覆盖**（`stubApi` 之后再 `page.route`）而不是
   改全局 `stub-routes.ts` 的 `/runs/{id}/artifacts` 503 替身，以免搅动 design-fidelity
   基线（win32 + linux 共 33+ 张）。代价是 `workspace-diff.spec.ts` 自带 2 份 fixture；
   如后续更多页面需要制品数据，应把 503 替身升级为有状态替身并一次重生成基线。

## 结论

PLAN-20260914-047 AC-01~AC-04 全部满足；W-1 为既有范围外项，W-2/W-3 为本 cycle
**已知边界**且已在响应字段、页面与文档中如实标注（非伪装实现）。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-04 仍为**部分交付**
（本批交付 artifact 内容 diff；真 pause-resume 执行协调、实验队列、memory capability
policy G16 三项未交付），转入 cycle 8 候选。
