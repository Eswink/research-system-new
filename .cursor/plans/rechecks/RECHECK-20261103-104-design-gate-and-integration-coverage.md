---
id: RECHECK-20261103-104
slug: design-gate-and-integration-coverage
title: GOAL-104 复检 —— 悬空样式判据 / 四组合设计门禁 / 十一相元素级像素 / 联调补齐 / 路由覆盖判据
status: COMPLETED
result: PASS
created_at: 2026-11-03
updated_at: 2026-11-03
plan_id: PLAN-20261103-104
parent_goal: GOAL-20261103-104
owners:
  - root-agent
verify_paths:
  - apps/web/src/features/runs/PhaseProgress.tsx
  - apps/web/src/features/runs/PhaseProgress.module.css
  - apps/web/src/features/command-center/CommandCenterPage.module.css
  - apps/web/src/layout/ConsoleLoading.module.css
  - apps/web/src/features/shared/LivePage.module.css
  - apps/web/tests/unit/css-token-references.test.ts
  - apps/web/tests/e2e/design-fidelity.spec.ts
  - apps/web/tests/e2e/design-outlines.json
  - apps/web/tests/e2e/stub-routes-integration.ts
  - apps/web/src/features/runs/ReviewPanelSection.tsx
  - apps/web/src/features/projects/ProjectDirectionEditor.tsx
  - apps/web/src/features/projects/ProgramsSection.tsx
  - apps/web/src/api/programsClient.ts
  - apps/web/tests/unit/backend-route-coverage.test.ts
  - apps/web/tests/unit/unconsumed-registry.test.ts
  - apps/web/tests/unit/unconsumedRegistry.ts
  - docs/frontend/UNCONSUMED.md
  - tools/verify_goal104_closeout.py
  - tools/goal104_closeout_assertions.py
  - tools/charter_parse.py
  - .github/workflows/m0-quality.yml
---

# RECHECK-20261103-104

## 复检范围

GOAL-20261103-104 的七条 EC 逐条取证。**两路以上**（`verify_paths` 列出的每个文件都是
一条独立的取证路径；产品面与判据面各取一次）。

## 检查结果

### 逐条读数

| EC | 判据 | 读数 | 结论 |
| --- | --- | --- | --- |
| EC-01 | `npx tsx --test tests/unit/css-token-references.test.ts` | 3/3 绿（token 面 / 类名面 / 反证臂） | PASS |
| EC-01 | 反证：注入 `var(--not-a-token)` | 判据点名 `features/runs/PhaseProgress.module.css: var(--not-a-token) is not defined in tokens.css nor locally` | PASS（随后还原） |
| EC-01 | 三处修复 vs 缺陷形态 | `styles.muted` 仅存于 `phaseStyles`；两个 `--bg` 均为 `--bg-app`；`--text-dim` 零命中 | PASS |
| EC-02 | win32 `npx playwright test design-fidelity` | 3/3 绿（144 张 win32 基线） | PASS |
| EC-02 | linux 容器内同套件 | 3/3 绿（144 张 linux 基线，与 win32 逐名配对） | PASS |
| EC-02 | `design-outlines.json` 的 `run-timeline-phases` | 11 个 `phase-node`，11 个相 id 全异，`phase-progress-unavailable` 零命中 | PASS |
| EC-02 | 反证：只改颜色（DOM 不动） | 结构签名**绿**、整页像素**绿**（0.36% < 2%）、元素级像素**红**（563 px） | PASS |
| EC-02 | `design-outline-guard.spec.ts` | 6/6 绿（含「只改颜色 ⇒ 不误报」） | PASS |
| EC-03 | `pnpm --dir apps/web test` | 97 条绿（含新增 6 条路由判据） | PASS |
| EC-03 | `npx playwright test`（全量） | 106/106 绿 | PASS |
| EC-03 | `npx tsc --noEmit` / `npx eslint src --max-warnings 0` | 无错 | PASS |
| EC-04 | 两个判据文件合计 | 6/6 绿 | PASS |
| EC-04 | 反证：白名单路径写错 | 判红并点名 `GET /health-typo` | PASS（随后还原） |
| EC-04 | 反证：白名单理由改成 `-` | 判红并点名 `GET /health` | PASS（随后还原） |
| EC-05 | `tools/verify_goal104_closeout.py --verdict-only` | 全 PASS、判词不含绝对路径 | PASS |
| EC-05 | `_VERIFIERS` / `IN_SCOPE` 两处登记 | 各 1 条命中 | PASS |
| EC-06 | `MAINLINE.md` 四处记账 | 程序表序 72 / 阶梯行收录 / 进展行 / 修订行 5 格 | PASS |
| EC-07 | `W-7` / `W-5` 核对 | `runs-on: ubuntu-24.04` ×1、`timeout-minutes: 30` ×1；无回退形态 | PASS |
| 执行纪律 5.9 | 凭据四面审计（`tools/credential_audit.py`） | **`offenders=0`（四面全部 0）**：`tracked` 5055 文件（`e7d189a0` 那一轮）/ 命中 105 / **放行 105 / offenders 0**；`records` 1092 文件 / 命中 5 / 放行 5 / **offenders 0**；`config_db` 1 文件 / 命中 0 / **offenders 0**；`logs` 938 文件 / 命中 0 / **offenders 0**。终态行 `PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）` | PASS |

## 本轮真跑暴露并修掉的缺陷

- **`W-0`｜`maxDiffPixels: 0` 在 CI 上是假红。** 第一版元素级判据用零容差，本地两个平台
  都绿，而 **CI ubuntu 报 60 px 不同**（同一个 `phase-track-dark-normal-zh-linux.png`、
  同一份代码）—— 字体抗锯齿在不同机器上仍有差异。实测三个读数：CI 噪声 **60 px**、
  本机噪声 **93 px**、真实颜色改动 **563 px**（元素共 131,262 px）。改为
  **`maxDiffPixels: 196`（0.15%）**：噪声过不去、颜色改动一定判红。改完重跑两平台全绿，
  且**反证臂仍然判红**（470 px > 196）。这条是本轮「只产 win32 基线就推」之外的**第二个**
  平台陷阱：容差本身也有平台差。

- **`W-0`｜我自己在「还原注入」时改错了另一条规则。** 反色值注入的还原脚本用了
  `border-left: 3px solid var(--success);` 作为宽锚，把 `.failed` 那条**本来正确**的
  `var(--danger)` 一并改成了 `--success` ⇒ `run-phase-progress.spec.ts` 的
  「四态着色互不相同」判红（三个不同颜色而非四个）。**判据抓到了**，但归因一开始指向
  「新基线靠颜色骗过」，实际是**改动副作用**。教训与记录一致：跨类成对改动禁宽锚替换。
  修法：按 `.failed {` 块精确定位还原，`git diff` 只剩新增的 `.muted`。

## 反证臂汇总（**判据咬得住**的证据）

| 判据 | 注入 | 极性 |
| --- | --- | --- |
| `css-token-references`（token 面） | `var(--not-a-token)` | 红 |
| `css-token-references`（类名面） | （见 EC-01 实测） | 红 |
| `backend-route-coverage` | 白名单路径 `/health-typo` | 红 |
| `unconsumed-registry` | 白名单理由 `-` | 红 |
| `design-fidelity`（元素级像素） | `.succeeded` 边框色改 `--danger` | **红** |
| `design-fidelity`（结构签名） | 同上（DOM 未动） | 绿（**应当**绿） |
| `design-outline-guard` | 只改颜色 | 绿（**应当**绿） |
| `credential-faces-clean` | 把一个非白名单的 `sk-proj-…` 串写进受跟踪文本文件 | **红**
  （`offenders={'tracked': 1}`、`credential-audit` 退出 1、判词点名该文件与模式名） |

## 两树复检

`tools/two_tree_recheck.py` 在干净 checkout 上跑同一份验证器，判词逐行 + `sha256` 与
工作树一致（见证据文件）。**判词不得含树的绝对路径**。

## 凭据面（执行纪律 5.9）

命令：

```bash
uv run --frozen --no-sync python -B tools/credential_audit.py
```

实测输出（四个面**逐个**报告，缺面时记 `not_present` 而非 PASS）：

```text
tracked    status=scanned        files= 5056 binary=395 hits=105 allowed=105 offenders=  0
records    status=scanned        files= 1092 binary=  0 hits=  5 allowed=  5 offenders=  0
config_db  status=scanned        files=    1 binary=  0 hits=  0 allowed=  0 offenders=  0
logs       status=scanned        files=  938 binary=  0 hits=  0 allowed=  0 offenders=  0
PASS: 四面扫描无明文凭据命中（放行项已逐条给理由）
```

- **`offenders=0` 在四个面上都成立**，这是本轮「安全/凭据：零变化」这句话的**实测依据**，
  不是断言。
- 命中数不为零（`tracked` 105 / `records` 5）但**全部落在 `ALLOWED_SUBSTRINGS` 白名单里**，
  每条都有理由（一次性容器口令 / `.env.example` 占位 / redaction 单测的杜撰串）。
  **放行数是单独统计的** —— 没用「没扫到」冒充通过。
- 本轮新增的 5 个读面/写面方法（`reviews` / `setDirection` / programs 四条 /
  `library.detail` / `memory.validity` / `retryTask`）与 3 个新判据文件**零凭据面变化**：
  没有任何新字段携带凭据，`--json` 的 `offenders` 列表为空（复核文件：
  `scratch/goal104-credential-audit.json`，本次运行 `sha256` 见下）。
- 输出文件的 `sha256`：`42e91ef8134e7534d511d6848b06f06e2a811f23c63b6c56c121d76d76d3cca5`
  （文本面的标准输出；机器可读面在同一轮次跑出，四面 `offenders` 同为 0）。
- **它现在是一条判据，不是一段散文**：`tools/goal104_closeout_assertions.py` 的
  `credential-faces-clean` 自己**跑**这次审计（`--json`），要求四个面都
  `status=scanned` 且 `offenders` 为空 —— **只看退出码不够**（少扫一面也退出 0，
  脚本契约明确「缺面记 `not_present` 而不写成 PASS」）。
- **两树复检抓到一个真缺陷**：第一版判据要求四个面都 `status=scanned`，而干净
  checkout 里 `data/**` 与 `scratch/**` 都是 gitignore 的 ⇒ `config_db` / `logs`
  必然 `not_present` ⇒ clean 侧判红（`not_scanned=['config_db','logs']`），两树对不上。
  按脚本**自己的契约**修：合法状态是 `scanned` 与 `not_present`；`not_a_git_tree`
  这类「该扫而扫不成」仍判红。**没有**放宽成「只看退出码」。
- **反证臂（实测，随后清理）**：把一个非白名单的 `sk-proj-…` 串写进受跟踪的
  `apps/web/tests/unit/credential-probe.sample.ts` 并 `git add` ⇒ `tracked` 面
  `offenders=1`、审计退出 1、验证器判
  `FAIL credential-faces-clean -> offenders={'tracked': 1} exit=1`。
  删除后四面回到 `offenders=0`。**这条判据咬得住**。

## 结论

七条 EC 全 PASS。残余四条（`W-1`…`W-4`）与未覆盖三条（`U-1`…`U-3`）在 GOAL 正文逐条
明写；两条声称边界（`R-1` / `R-2`）明写**不得宣称**的事：视觉回归未完全覆盖、
不是每条路由都有消费者（`/health` 与三条 client-only 方法是**登记**不是消费）。
