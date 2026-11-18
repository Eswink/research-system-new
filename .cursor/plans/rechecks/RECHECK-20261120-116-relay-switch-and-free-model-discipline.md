---
id: RECHECK-20261120-116
slug: relay-switch-and-free-model-discipline
title: GOAL-115 cycle 1 复检 —— 换站落地 / 零价纪律 / 会话头缝 / PRD 判据
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-20
updated_at: 2026-11-20
plan_id: PLAN-20261120-116
parent_goal: GOAL-20261119-115
owners:
  - root-agent
verify_paths:
  - examples/config/llm_endpoints.yaml
  - examples/config/models.yaml
  - packages/domain/models.py
  - adapters/relay/protocols.py
  - adapters/relay/completions.py
  - adapters/openhands/llm_factory.py
  - tests/loaders/test_free_model_only_policy.py
  - tests/tooling/test_relay_pins_are_cleared.py
  - tests/tooling/test_prd_gap_analysis_recorded.py
  - tools/goal098_model_independence.py
---

# RECHECK-20261120-116

## 结论

**PASS_WITH_WARNINGS**。三件交付（EC-01 换站 + 零价纪律、EC-02 旧 pin 清零、EC-07 PRD
差距分析）各有**实跑证据**与**反向按压**；两条 warning 见下（`W-1` 读面投影未做、
`W-2` 全量 m0 见证在本复检写成时尚未取到终态 —— 见「未覆盖」）。

## 检查结果

| # | 判据 | 判法 | 结果 |
| --- | --- | --- | --- |
| R-1 | 四个零价模型**都**支持标准 `tool_calls` | 逐个 `POST /chat/completions` + `tool_choice: required`，读 `finish_reason` 与 `tool_calls` | PASS（4/4；`hy4-flash-free` 需 `max_tokens ≥ 2048`，否则 reasoning 吃满预算） |
| R-2 | 零价集合与配置逐字一致 | `GET /go/v1/models` ⇒ 按 `cost.text.*.price` 全 0 筛 ⇒ 4 个，与 `models.yaml` 九个块的名字集合相同 | PASS |
| R-3 | 两条腿**真的发出** `x-opencode-session` | relay：`tools/m12_relay_smoke.py` probe ok=True；OpenHands：`build_llm(...).completion(...)` 返回 `OK` | PASS |
| R-4 | 去掉该头 ⇒ 请求**真的**失败（不是"配了就行"） | OpenHands 腿去掉 `extra_headers` ⇒ `LLMBadRequestError: Request is missing x-opencode-session`；relay 腿裸 `curl` 同 | PASS（反证咬合） |
| R-5 | 凭据不能经该缝偷渡 | 域构造期拒绝 `authorization` / `x-api-key` / `anthropic-version`（大小写不敏感）+ 控制字符 | PASS（四条逐条实跑） |
| R-6 | 旧站标识在受判面零命中 | `test_relay_pins_are_cleared.py` 扫 `git ls-files` 的 200+ 受判文件；四个标记逐条注入反证臂 | PASS（9 passed；反证 4/4 命中） |
| R-7 | 零价判据咬得住 | 把 `hy4-flash-free` 换成夹具里的收费名 `deepseek-v4-pro` ⇒ 判据点名判红 | PASS |
| R-8 | PRD 文档四节 + 引用密度 | `test_prd_gap_analysis_recorded.py`：四节齐、去重 23 条 `file:line`（要求 ≥20）、`## 6. 来源` 收尾、INDEX 登记 | PASS |
| R-9 | 非 ZDR 事实**被写下** | §5.1 点名 `iceman-contributor-free` 且含「ZDR」 | PASS |
| R-10 | 独立性约束未被换站破坏 | 用产品解析器判：写作组 ∩ 评审组 = ∅；`reviewer_a` ≠ `reviewer_b`；作者 ∉ {写作, 三评审}；创新点评审 ∉ 写作组 | PASS（四个约束逐条实跑，其中作者那条另有反证臂：把作者指向评审 A ⇒ False） |
| R-11 | 影响面不回归 | `tests/adapters/{relay,openhands}` + `tests/loaders` 227 绿；`tests/{architecture,application/preflight,api}` 1102 passed / 4 skipped | PASS |
| R-12 | 钉值判据同轮更新，且**不是放宽** | `goal098` 从"断言某个厂商模型名"改成"用产品解析器判目标不相交"（更强：交集非空即红）；`goal108` 的 `FREE_MODELS`/`LAN_HOST` 跟随站点演进，判法（逐字命中 + 数量相等）未变 | PASS（两个验证器实跑：`goal108` 87/0、`goal098` 104/0） |

## 反向按压（每条都实跑过）

| 臂 | 按压 | 期望 | 实测 |
| --- | --- | --- | --- |
| A-1 | 去掉 `x-opencode-session` | 请求失败 | `400 MissingSessionID` / `LLMBadRequestError` |
| A-2 | `models.yaml` 写收费名 | 零价判据红并点名 | `['deepseek-v4-pro']` |
| A-3 | 产品路径写旧地址 | pin 判据红 | 四个标记各 1 命中 |
| A-4 | 作者与评审 A 同模型 | 独立性判 False | `False` |
| A-5 | PRD 去掉所有 `file:line` | 引用计数为 0 | `set()` |

## 警告

- **`W-1`（对应 GOAL 残余 `W-3`）**：`LLMEndpoint.extra_headers` **未投影进 endpoint 读面**。
  它进域对象、进 sqlite 往返、进两条出网腿，但 `LlmEndpointReadDto` 里看不到。
  代价：一个 `400 MissingSessionID` 在控制面上看起来像"配置对而请求失败"。
  没做的理由：投影会连带 OpenAPI 快照 + `web/src/types.ts` + e2e 夹具三处同步，
  而 EC-01 判的是配置与出网。**这是缺口，不是成就。**
- **`W-2`**：`tools/goal098_closeout_assertions.py` 逼近 450 行硬门（433 行），
  本轮为此把独立性判据拆进 `tools/goal098_model_independence.py`。拆分是尺寸约束下的
  正确落点，但它意味着"断言集自己读得出来"这条要跨两个文件 —— 已在断言集里用
  `_load_model_independence()` 显式加载（先写 `sys.modules` 再 `exec_module`）。

## 未覆盖

- **全量 m0 见证**：本复检写成时门仍在跑（首轮抓到 5 条真判负：lint / format / mypy /
  pytest / framework-validate，全部由本轮自己的新文件引起，已逐条修复）。
  终态读数记在 GOAL 的「CI 台账」与迭代日志里，**不在本文件里冒充**。
- **真实双评审 run（EC-04）**：本 cycle 射程不含它。
- **`iceman-contributor-free` 的 ZDR 状态**：只有 provider 的文字口径，
  没有机器可读字段 ⇒ 判据不判，只记录。

## 无可复用事实

本轮**没有**沉淀新的工程记忆条目：换站与"配置往返"的形态已在 `MEM-20261014-218` 里，
会话头缝是新发现但**尚未在真实 run 上验证**（只有 probe 与单请求），
现在写进记忆会把"未验证的机制"写成"经验"。待 EC-04 真跑之后再沉淀。
