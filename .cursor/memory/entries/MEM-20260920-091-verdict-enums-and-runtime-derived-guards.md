---
id: MEM-20260920-091
title: "把结论口径做成**穷举词表**（并让越级宣称不可表达）；判据里的枚举守卫要走运行期枚举，别写两个字面量的同一性比较——mypy 的 comparison-overlap 连续两轮拦下它"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-118-first-live-gated-real-run.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-118-first-live-gated-real-run.md
supersedes: []
tags:
  - honesty
  - verdict-vocabulary
  - mypy
  - comparison-overlap
  - live-gate
  - agenets-md-section-4
---

# 结论口径做成词表 + 枚举守卫走运行期（GOAL-20260920-008 / cycle 5）

## 做了什么

AGENTS.md §4 要求「无法证明底层模型完全一致时标注『可重复配置』而非『完全模型可复现』」。
改动前这句话只是**文案**：`services/api/dto/models.py` 的 docstring 与页面
`ModelDetails.tsx` 的 `Configuration reproducible / provider fingerprint unavailable`。
本轮把它升成**类型上不可越级**的两态：

- `ModelReproducibilityVerdict`（`REPEATABLE_CONFIGURATION` / `NOT_VERIFIED`，穷举）；
- `LiveRunRecord`：一次 live run（或其如实 skip）的脱敏记录，
  **必填指纹项缺失 ⇒ 降级为 `NOT_VERIFIED` 并点名缺项**，provider 项缺失只登记不降级；
- `evaluate_live_run_gate`：两条开门条件（runtime 显式配置 + 凭据**可解析**），
  关门时**不碰 socket**、**不物化凭据**（只问 `CredentialResolver.has`）；
- 口径同源判据：六个口径面必须出现该档 + 全仓**肯定式**越级表述判红。

## 为什么这样做（可复用结论）

1. **「不得宣称 X」要落成「X 不可表达」**：只写文档，读面随时能被顺手美化；
   把结论收成穷举枚举后，任何想说「完全可复现」的读面都必须先**加一个成员**，
   而那一步有判据把守（成员集合恰好两态 + 成员名不得含 `FULL`/`EXACT`/`PROVEN` 等痕迹）。
2. **skip 必须有结构，不能是「什么都没有」**：无凭据时最容易被读成「跑过了没问题」。
   本轮把 skip 变成一条 `NOT_VERIFIED` 记录（**必须有理由**，构造期就拒空理由），
   并点名缺哪一个 `credential_ref`——「缺凭据」不是解释，「缺哪个凭据」才是。
3. **判据要判「宣称」，不要判「话题」**：全仓扫「完全可复现」会误伤每一句诚实否定
   （「不得宣称…」「…而非…」「≠」「无法证明…」）。规则定为：**加引号的提及**放行、
   同行含否定标记放行，其余判红。射程写在判据 docstring 里：它挡默认漂移，不挡恶意规避。
4. **空串是任何字符串的子串**：`after = line[end] if end < len(line) else ""` 之后写
   `after in QUOTE_CLOSE`，行尾短语会被判成「有引号收尾」而**偷偷放行**。
   边界处必须显式排除空串（本轮的规则自检就抓到这条）。
5. **枚举守卫走运行期，别写两个字面量的同一性比较**（连续两轮被 m0 拦下）：
   - cycle 4：`assert x is not ModelDriftState.MATCH` 写在 `is UNKNOWN` 之后 ⇒
     `comparison-overlap`（mypy 已把类型收窄成 `Literal[UNKNOWN]`）；
   - cycle 5：`assert ModelReproducibilityVerdict.NOT_VERIFIED is not (...REPEATABLE_CONFIGURATION)`
     ⇒ 同样 `comparison-overlap`；改成比较 `.value` **也**会被收窄成字面量类型继续报错。
   可行写法：`members = list(Enum)` + `len(members) == N` + `len({m.value for m in members}) == N`
   ——语义（两态不得合并）不变，且类型检查器不会把运行期集合收窄成字面量。

## 怎么做与复现

```sh
# 词表 + run 记录（skip 不是 PASS；缺项点名）
uv run --frozen --no-sync pytest -q tests/domain/test_reproducibility_verdict.py tests/application/model_relay/test_live_run_record.py

# 离线可判：门决策 + 零出站（拔掉 socket 仍能判） + 门控存在性
uv run --frozen --no-sync pytest -q tests/e2e/test_ec04_live_gate_offline.py

# 口径同源（必填面 + 否定豁免的越级判据）
uv run --frozen --no-sync pytest -q tests/architecture/python/test_reproducibility_wording.py

# 反证（先红后复原；脚本把「复原后仍有 diff」当失败）
uv run --frozen --no-sync python -B scratch/ec04-falsification.py
```

## 适用边界

- 适用于**任何「结论比证据强」的位置**：可复现性、能力声明、健康度、覆盖率、凭据存在性。
  做法是把结论收成穷举枚举 + 让越级表述在类型上不可表达，再用一条判据钉住成员集合。
- **live 分支在本机从未执行**（六项候选凭据环境变量全 absent）：本轮的绿只覆盖离线部分
  ——门开/关判定、skip 记录、词表、口径判据；「真实 run 会成功、归账会正向、制品可读」
  **仍未实测**（RECHECK-118 W-1）。
- 门只回答两个条件（runtime 配置 + 凭据可解析）：Policy/预算/端点健康由既有 preflight 负责，
  「门开着 ≠ run 一定跑得通」（W-3）。
- 目录里所有模型当前绑 `main`（OPENAI_COMPATIBLE 面），登记进目录的 `agnes-anthropic`
  只由 probe 段驱动 ⇒ 「一次 run 自身消费 anthropic 面」需要改模型→端点绑定（W-2）。
- 口径判据的引用-豁免是**行级**启发式：把肯定式宣称加引号写出来可绕过（W-4）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-118-first-live-gated-real-run.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-118-first-live-gated-real-run.md`（F1–F5、W-1…W-6）
- 代码：`packages/domain/enums.py`（`ModelReproducibilityVerdict`）、
  `packages/application/model_relay/live_run_record.py`、
  `packages/application/model_relay/live_run_gate.py`、
  `docs/integration/LLM_ENDPOINTS.md` §11
- 相关：[[MEM-20260920-090]]（未知 ≠ 无）、[[MEM-20260920-089]]（读面谎言要用措辞判据钉）
