---
id: PLAN-20261107-107
slug: four-targets
title: GOAL-107 子计划 —— 四靶并行（前端补全 / 引用分布 / 外部评审面板 / 脚本执行权威）
status: IN_PROGRESS
created_at: 2026-11-07
updated_at: 2026-11-07
parent_goal: GOAL-20261107-107
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261107-107-four-targets.md
memory_entries: []
---

# PLAN-20261107-107 —— 四靶并行

GOAL: `.cursor/plans/goals/GOAL-20261107-107-four-targets-frontend-citations-panel-script-authority.md`

## 背景

用户 2026-11-07 拍板「四个选项都做」。四个靶子在勘察后确认互相独立，按**风险递增、
价值递增**排序执行：C（前端，确定性）→ B（分布读数，确定性）→ A（外部面板，引入模型
调用，用户已授权）→ D（脚本执行权威，安全面）。

## WP 分解

| WP | EC | 交付 | 关键文件 |
| --- | --- | --- | --- |
| WP-1 | EC-01 | 改稿并排 diff | `apps/web/src/features/reports/ManuscriptPanel.tsx`、`apps/web/src/features/workspace/ArtifactDiffPanel.tsx`（导出 `DiffBody`/`DiffLineRow`） |
| WP-2 | EC-02 | 程序页补全 + TS 类型漂移 | `apps/web/src/features/projects/ProgramsSection.tsx`、`apps/web/src/api/types.ts`、`apps/web/src/api/client.ts` |
| WP-3 | EC-03 | 基线重录 | `apps/web/tests/e2e/design-outlines.json`、像素基线 |
| WP-4 | EC-04 | 分布读数 | `packages/application/deliverable/citation_distribution.py`、`tests/application/test_citation_distribution.py` |
| WP-5 | EC-05 | 分布入口 | `tools/citation_corpus_report.py`、`IN_SCOPE` 登记 |
| WP-6 | EC-06 | 面板机制 | `packages/application/deliverable/manuscript_panel.py`、`tests/application/test_manuscript_panel.py` |
| WP-7 | EC-07 | 面板落 canonical + 读面 | `packages/domain/evidence.py`（用既有 `ReviewFinding`）、装配点、`ReviewPanelSection.tsx` |
| WP-8 | EC-08 | §7 文档同步 | `docs/architecture/MANUSCRIPT_QUALITY.md` |
| WP-9 | EC-09 | 执行权威闭集 | `packages/application/experiments/script_authority.py` |
| WP-10 | EC-10 | 策略约束执行面 | `packages/application/experiments/governed.py` |
| WP-11 | EC-11 | 对抗性反证臂 | `tests/application/test_experiment_script_authority.py` |
| WP-12 | EC-12 | 文档同步 | 实验脚本说明 + `docs/frontend/` |
| WP-13 | EC-13 | 收口资产 | `tools/verify_goal107_closeout.py`、`tools/goal107_closeout_assertions.py`、两份登记 |
| WP-14 | EC-14 | 宪章记账 | `.cursor/plans/goals/MAINLINE.md`、`ALL_PLAN.md` |

## 约束

- **不改**：`NOT_JUDGED` 五项、十一相相集、角色/能力词表、`.github/workflows/**`、
  策略规则文件、任何判据阈值。
- **新增判据必须有反证臂**，且按压后确认真的红。
- `AUTHORED` **出厂默认关闭**；本轮只建机制。
- 面板判词是 advisory，**不产生 `Decision`**。
- 引用阈值三个常量**保持 `None`**（n=1 < 3）。

## 验证

1. 每个 WP 收口：定向套件 + `ruff check` / `ruff format --check` / `mypy` + 规模门。
2. 前端 WP：`pnpm --dir apps/web lint && typecheck && test && build` + `test:e2e`。
3. 记录面：`uv run --frozen --no-sync python -B -m pytest tests/tooling -q -p no:randomly`。
4. 全量 m0 重封（记录写完之后、不再改树）：
   ```
   env -u RESEARCHOS_AGENT_RUNTIME -u RESEARCHOS_LIVE_E2E -u RESEARCHOS_LIVE_LLM \
       RESEARCHOS_POSTGRES_DSN= RESEARCHOS_POSTGRES_TEST_DSN= \
       uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
   ```
   判据只有终态行：`PASS: profile=m0; 23 deterministic checks`、`PASS [` **24** 行、
   0 FAILED、`tree changed during the run: False`。
5. 两树复检：`tools/two_tree_recheck.py --script tools/verify_goal107_closeout.py --root . --script-mode shared`。

## 提交纪律

- 主题点名 `goal107`（改 `.cursor/` 之外的任何文件必须点名）。
- **绝不 `git add -A`**；`.git/index.lock` 残留时 `rm -f` 后重试。
- 一个 cycle 一次推送（`cancel-in-progress` 会取消在飞 run）。
- 台账「一提交一行」，CI 读数绑到它实际发生的那个提交；同一次 push 的多个提交只有
  一个 M0 run ⇒ 前者写「与 `xxx` 同一次 push（无独立 run）」。

## tip 债纪律

反方向判据会把**被推离 HEAD 的提交**逐个点名。实测（序 73…75）这笔债会**连环**：
补 A 的提交把 B 推离 HEAD，补 B 又把 A 推离。唯一终结点 = **把下一环的行预先写进
同一提交**，而不是一个一个补。

## 验收条件

- 十四条 EC 全部 PASS（见 GOAL frontmatter），每条都有可重跑的取证命令；
- 每个新增判据都有**反证臂**，且两向按压后确认真的红；
- 不改任何既有判据的阈值（`maxDiffPixels: 196`、整页 2%、`MIN_SECTION_WORDS = 8`）；
- `NOT_JUDGED` 五项 / 十一相相集 / 角色 27 / 能力 47 **逐字不动**；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`。

## 实施清单

- [x] 归档序 72 两行 + 修 `verify_goal104/105` 的归档兼容（`320faa78`）
- [x] 付清 `20c2c84d` 与 `320faa78` 两笔 tip 债（`9ddd6360` + 本轮）
- [x] GOAL-107 建档（frontmatter / 七章节 / 十四 EC）
- [x] 子 PLAN / RECHECK 建档 + `ALL_PLAN` 登记
- [x] 宪章：程序表序 75 + 阶梯「报告」「实验」行 + 进展/修订各一行
- [ ] WP-1…3 靶子 C（前端补全，EC-01…03）
- [ ] WP-4…5 靶子 B（引用分布，EC-04…05）
- [ ] WP-6…8 靶子 A（外部评审面板，EC-06…08）
- [ ] WP-9…11 靶子 D（脚本执行权威，EC-09…11）
- [ ] WP-12…14 文档 / 收口资产 / 宪章收口（EC-12…14）

## 证据

（每个 WP 收口时追加：取证命令、读数、以及反证臂的按压结果。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-07 | IN_PROGRESS | 建档：序 75；归档已在 `320faa78` 完成；十四个 EC 待推 |

## 影响报告

（收口时填写：Domain / API / schema 变化、安全与凭据变化、兼容性与迁移风险、上游版本影响。）
