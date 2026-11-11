---
id: MEM-20261112-241
title: "两条换站轮的可复用事实：verify 字段点名的文件可能不存在；门判「可解析」不判「有效」"
status: ACTIVE
created_at: 2026-11-12
updated_at: 2026-11-12
scope: repository
confidence: 0.95
review_after: 2027-05-12
source_plans:
  - .cursor/plans/tasks/PLAN-20261111-108-relay-swap-and-reliability.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261111-108-relay-swap-and-reliability.md
supersedes: []
tags: [criteria, credential, live-run, relay-swap, governance, evidence]
---

# 两条换站轮的可复用事实

## 做了什么

序 76 的收口轮：补建了 GOAL-108 的 EC-01 / EC-07 两个被点名的判据文件（含反证臂）、
给 live harness 的取证路径加了 `RESEARCHOS_LIVE_EVIDENCE` 改向出口（缺省不变）、
把「换站必须换 key + 401 的核验命令」写进两页集成文档；真跑四次，后两次
`SUCCEEDED`（十一相全绿、各 45 件产物、`missing_artifacts` 为空）。

## 为什么这样做

GOAL-20261111-108（序 76，换接入商 + 四个免费模型分工 + 四处静默停住收口）的收口轮
实测出两条**机制性**事实。它们都不是「本轮的 bug」——是**判据面与门面的结构性缺口**，
换任何一个接入商（或任何一次带 `verify:` 字段的 GOAL）都会再踩一遍。记录它们是因为
两条都有**可操作的核验步骤**，且都能在下次同类操作里直接复用。

## 怎么做与复现

### 事实一：EC 的 `verify:` 字段点名了一个从未落地的判据文件，而该 EC 标着 PASS

**实测**：GOAL-108 的 EC-01 与 EC-07 各自在 `verify:` 字段里点名了一个判据文件
（`tests/tooling/test_goal108_probe_readings.py` /
`test_goal108_live_harness_reads_the_switch.py`），**两个文件都不在树**，而那两条 EC
当时已标 `PASS`。`git log --all --diff-filter=A -- 'tests/tooling/test_goal108*'`
⇒ **零命中**：它们从未被创建过。

**为什么既有门没抓到**：`test_declared_recheck_paths_have_evidence.py` 判的是
**RECHECK** 的 `verify_paths`（复检面）；GOAL 正文 `exit_criteria` 里每条 EC 的
`verify:` 字段**没有**对应的「路径必须在树」判据。于是「写了文件名」和「文件存在」
之间有一段无人看守的缝——EC 可以标 PASS 而它的机械判据从未存在。

**修法（本轮落地）**：补建两个文件，且**补建时判据先红后绿**
（探针判据第一版把 frontmatter 里引用的标题名当正文切节，被自己的反证臂抓到；
switch 判据的反证臂只替换第一处 `hy3` 也假绿——**反证臂自身也要按压**）。
**可复用的纪律**：新 GOAL 建档时，`verify:` 字段里的每个路径在**建档的同一个提交**里
就该存在——最好由一条判据钉住「EC verify 字段引用的 `tests/` 路径必须在树」。

### 事实二：`live_run_gate` 判「凭据可解析」，不判「凭据有效」——过期 key 让门全开、每次调用 401

**实测**：换到局域网中转站后，`.env` 里的 `LLM_MAIN_KEY` 仍是**上一个接入商**的 key
（文件 mtime 2026-10-14 可证）。此时：

- `EnvCredentialResolver.has("LLM_MAIN_KEY")` ⇒ **True**（凭据「可解析」）；
- `live_run_gate` 三条件（显式开关 / runtime / 凭据可解析）**全满足** ⇒ 门**开**；
- 每一次真实调用 ⇒ **HTTP 401** `invalid api key`。

**判据口径**：门的三条件判的是**配置存在性**，不是**凭据有效性**；后者只能由一次
真实调用证明。所以「换接入商」这类动作的 checklist 必须包含：
`curl -H "Authorization: Bearer $LLM_MAIN_KEY" <base_url>/models` 应回 200——
401 就是 key 过期，**换 key 后必须新起进程**（`EnvCredentialResolver` 无参构造时
是环境快照，轮换不追认，见 `LIVE_MODEL_RUNBOOK.md` §8 的轮换表）。

**同轮的连带发现**：live harness 的取证文件写的是 **GOAL-106 已封存的读数路径**——
再跑一次 live 判据会把一个已完成 GOAL 的证据换成本次读数（实测：GOAL-106 的
`SUCCEEDED` 被换成 `FAILED`，其收口断言集的两条同向判据随之判负）。修法是给
`RESEARCHOS_LIVE_EVIDENCE` 一个改向出口、缺省不变（GOAL-106 的判据逐字不受影响）。

## 适用边界

- 不宣称「`verify:` 路径必须在树」已经机械化（那条判据本轮**没有**写——它属于
  判据面改动，留给下一轮；本轮只补建了两个文件并如实登记缺口）。
- 不宣称「凭据有效性已入门」：`live_run_gate` 的三条件**逐字未动**（改门是产品面
  + §9 姿态问题），只把**操作者侧的核验步骤**写进文档。

## 来源

- 任何一次「换接入商 / 换 base_url / 换 key」操作；
- 任何新建 GOAL 的 `exit_criteria` 带 `verify:` 字段时；
- 任何 live 判据要写读数文件时（先查目标路径是否是别的 GOAL 的封存读数）。
