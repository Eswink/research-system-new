---
id: PLAN-20261101-103
slug: phase-events-and-frontend-visible-chain
title: GOAL-103 子计划 —— 相级事件 + 读面补字段 + 前端十一相与手稿链
status: DONE
created_at: 2026-11-01
updated_at: 2026-11-01
parent_goal: GOAL-20261101-103
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md
memory_entries:
  - .cursor/memory/entries/MEM-20261101-236-project-config-needs-a-per-run-hook.md
  - .cursor/memory/entries/MEM-20261101-237-declared-but-never-constructed-judge-the-call-site.md
---

# PLAN-20261101-103

## 背景与靶子

GOAL-20261101-103 的八个 EC（缺口是建档实测的，靶面不在本计划重新推导）。按**提交面**
分成四个 cycle，每个 cycle 可独立验收：

1. **cycle 1（后端读面）**：相级事件 + `RunDetailDto.phases`（EC-01）+ 两个漏字段
   （EC-02）。这是**同一条** DTO/OpenAPI/types.ts 同步面，拆开做会撞
   `test_openapi_snapshot`。
2. **cycle 2（前端）**：十一相进度条（EC-03）+ 制品标签与手稿视图（EC-04）。两件都动
   `apps/web`，且都会改 `design-outlines.json` 基线 ⇒ 同轮重生成一次。
3. **cycle 3（后端收尾 + meta）**：`retmax` 项目级 + 强口径论证（EC-05）+ 负判射程
   补代（EC-06）。
4. **cycle 4（收口）**：验证器与断言集（EC-07）+ 宪章记账（EC-08）。

## 交付面（checkbox）

### cycle 1 —— 后端读面

- [x] EC-01a `EventType` 加 `PHASE_STARTED` / `PHASE_COMPLETED`，`EVENT_MODEL.md` 同步
- [x] EC-01b `phase_runner` 在组首发 `phase.started`、组末发 `phase.completed`
      （失败/停车/重排不发 completed）
- [x] EC-01c `PhaseProgressDto` + `RunDetailDto.phases`，从冻结协议正文反推相分组
- [x] EC-01d 判据：发射时序（started 先于组内首个 task.created；completed 在末任务之后）、
      失败组不发 completed、payload 键逐条在场
- [x] EC-01e 反证臂：摘掉发射点 ⇒ 判据判红（子进程按压，逐字节复原）
- [x] EC-02a `ArtifactDto.supersedes`（Python + TS + OpenAPI 重生成）
- [x] EC-02b `ReviewFindingDto.reviewer_model`（同上三处）
- [x] EC-02c 两个读面判据各一条（含「域里有值 ⇒ 读面必须给」）

### cycle 2 —— 前端

- [x] EC-03a `NAMED_SSE_EVENTS` 加两个相级事件名
- [x] EC-03b RunPanel 十一相节点（`data-testid="phase-node-<id>"` + `data-phase-state` + 四态着色）
- [x] EC-03c 点击展开该相制品列表
- [x] EC-04a ArtifactBrowser 19 类后缀 → 人类可读标签（中英双语；未命中显示原 id）
- [x] EC-04b ReportsPage 渲染 `manuscript.md` Markdown 正文 + 编辑决定 + 投稿包链接
- [x] EC-04c `types.ts` 加 `EditorialDecisionDto`
- [x] EC-04d i18n 两份语言键集齐
- [x] EC-04e `design-outlines.json` 同轮重生成（逐条申报理由）

### cycle 3 —— 后端收尾 + meta

- [x] EC-05a 序 70 能力域仍为 `复检`（判据钉住不回退）
- [x] EC-05b `ProjectSettings.retmax: int = 3` + 四级回落（显式 > 项目 > env > 默认）
- [x] EC-05c `MANUSCRIPT_QUALITY.md` `## 7. 强口径判定`（五项逐条论证）
- [x] EC-06a 早期一代三个可跑验证器纳入负判射程
- [x] EC-06b 一条反证臂（合成树让早期验证器报负 ⇒ 判红）

### cycle 4 —— 收口

- [x] EC-07 验证器 + 断言集 + `_VERIFIERS` / `IN_SCOPE` 登记 + 四道门
- [x] EC-08 宪章记账（序 71 / 阶梯 / 两表各 3 行 / ALL_PLAN）

## 复检

收口复检：`tools/verify_goal103_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，`verify_paths` ≥ 2 路，见 GOAL 的 `latest_recheck`）。

## 影响报告

（逐 cycle 回填。首行写「预判」，收口时改成「实测」。）

- **Domain/API/schema**：`EventType` 新增两个成员（**纯加性** ⇒ 旧 reader 忽略即兼容，
  与 `EVENT_MODEL.md` §5 的向后兼容演进一致）；`RunDetailDto` / `ArtifactDto` /
  `ReviewFindingDto` 各新增**可空**字段（缺省值 ⇒ 旧客户端不破坏）；OpenAPI 快照与
  `types.ts` 同轮重生成。
- **安全/凭据**：零变化（无新凭据、无新出网、无新工具面）。相级事件 payload 只有
  相身份与制品 id，**不含内容**（§10 的 digest/size/type 口径不适用——这里连内容摘要
  都没有，只有标识）。
- **兼容性/迁移**：零 migration（相进度由既有制品 + 冻结协议正文推出，不落新表）；
  `retmax` 是可选字段（缺省 `3` ⇒ 调用表逐字段不变）。
- **上游**：零依赖变化。

## 验收条件

| EC | 判定 | 证据 |
| --- | --- | --- |
| EC-01 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-02 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-03 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-04 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-05 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-06 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-07 | **PASS** | 见 RECHECK-20261101-103 的判词表 |
| EC-08 | **PASS** | 见 RECHECK-20261101-103 的判词表 |

## 实施清单

（与「交付面」逐条对应；勾选状态随 cycle 推进。）

## 证据

（全部为**真实执行**的读数，非"文件在树"。）

- **Python 定向套件**：`test_phase_progress_events.py` **10 passed**（含两条子进程按压：
  `pressed_code=1, restored_code=0, restored_digest_matches=True`）/
  `test_run_detail_phases.py` **14 passed** / `test_read_face_field_completeness.py` **8 passed** /
  `test_retmax_project_setting.py` **18 passed** / `test_manuscript_quality_strong_criterion.py`
  **5 passed** / `test_verifier_main_files_report_no_negative.py` **7 passed**。
- **契约**：`test_openapi_snapshot.py` **8 passed**（快照经 `tools/gen_openapi.py` 重生成）。
- **浏览器（Playwright + stubbed API）**：`run-phase-progress.spec.ts` **4 passed** /
  `run-artifact-chain-labels.spec.ts` **3 passed** / **全量 web e2e 105 passed**（含
  `design-fidelity` 与 `design-outline-guard` 的五条反证臂）。
- **早期一代判词首次可见**：026 ⇒ 4 条、028 ⇒ 5 条、029 ⇒ 10 条 = **19 条**（此前 0 条在射程内）。
- **收口验证器**：`tools/verify_goal103_closeout.py --root . --verdict-only` ⇒ **84 判词全 PASS / 0 FAIL**。
- **真跑取证（十一相）**：`tests/e2e/test_goal103_phase_events_product_path.py` **5 passed** ——
  恰好 11 `phase.started` + 11 `phase.completed`、相集合逐字等于协议、时序按 `occurred_at`
  成立、DAG 拓扑序成立；该判据抓到一个合成协议碰不到的实现缺陷（`experiment` 相无任务行
  ⇒ 读面曾把它读成「未开始」），已修（`W-0`）。
- **路由级读面**：`tests/e2e/test_goal103_read_face_http.py` **5 passed**（两个补字段经真实
  `GET /runs/{id}/artifacts` / `/reviews` 回得来，且值是真的归因/父指针）。
- **Charter**：`test_mainline_program_is_intact` / `test_mainline_research_ladder_advances` /
  `test_mainline_archive_is_continuous` / `test_short_archive_revision_rows_are_registered` /
  `test_record_tables_are_structurally_sound` ⇒ **35 passed**。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-01 | CREATED | 建档（承 GOAL-20261101-103）。四个 cycle 按提交面划分。 |
| 2026-11-01 | DONE | 四个 cycle 全部交付；八条 EC 全 PASS；收口复检 `RECHECK-20261101-103` PASS。 |

## 可复用事实

1. **`ruff format` 会把多行 tuple 强制展开**（去尾逗号也没用）：想省行只能写成单行 tuple
   或少写一条。本轮在 `phase_runner.py`（450/450 零余量）与 `phase_capabilities.py`
   上各撞一次，最后靠**把行为拆成独立模块**（`phase_progress.py` / `apply_retmax` 移入
   `phase_call_arguments.py`）而不是压缩注释来解决。
2. **「声明了但从未构造」的机械形态**：字段/函数在树 ≠ 接线在。本轮把每条接线的判据都
   写成「源码里点名调用行」（`run_phases_dto(` 在 router、`apply_retmax(declared, deps.retmax)`
   在能力步、`_with_project_retmax(` 在 runner_wiring）—— 只断言字段存在会让死字段判绿。
3. **项目级设置在进程级装配面取值会串项目**：`CapabilityDeps` 只造一次，而 `retmax`
   是项目级 ⇒ 取值点必须晚于「run 属于哪个项目」（`RunContext.project`）。这条形态对
   任何「装配一次、用到多次」的配置面都成立。
4. **判据自己的射程要先精确到行**：`ladder-next-level-not-claimed` 第一版扫「提到本 GOAL
   的所有行」，把修订记录里那句「把 X 写进去属于伪造」也扫成了违规 —— 判据要限定到
   **它真正要判的那一行**。
5. **CSS module 的类名被哈希**：判「有状态色」要判**计算后的颜色**
   （`getComputedStyle(node).borderLeftColor`），判类名只会在构建细节上打转（第一版实测
   全部解析成空串）。
6. **stub harness 默认 JSON 序列化**：`GET /artifacts/{id}/content` 的 Markdown 会被包成
   带引号的 JSON 串（既不是真后端行为，也会让"渲染正文"这条判据在假输入上变绿）⇒ 加
   `bodyKind: "text"`。
