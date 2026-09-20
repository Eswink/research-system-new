---
id: RECHECK-20260920-117
plan_id: PLAN-20260920-117
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle4
baseline_ref: 183f588
checked_head: 3eef7c3
---

# RECHECK-20260920-117 — 漂移可见性三态（EC-05 复检）

## 检查范围

不采信实施叙述：按 EC-05 判据在**当前树**上真跑，逐条做**先红后复原**的反证，门禁以
**完整 m0（23 项）**为准。检查面：

- **判定**：三态（一致 / 漂移 / 未知）各自可判，且「未知」**不得**退化成「一致」；
- **比较规则**：只做 `strip()` 精确比较；大小写/别名/日期后缀差异一律 `DRIFT` 并点名两值；
- **读面（API）**：`ProbeResultDto.drift` 三态可达，detail 含两个原值，无凭据/原始响应体；
- **读面（页面）**：三态渲染互不混淆，`UNKNOWN` 文案自带「未知 ≠ 无漂移」，中英各一套；
- **文档**：`MODEL_PROBE.md` / `LLM_ENDPOINTS.md` §8 写明三态、严格口径与「漂移不是熔断」；
- **live 分支**：无凭据 ⇒ 真实 probe 不跑，如实记 skip（**skip 不是 PASS**）。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 域分类器 | `tests/domain/test_model_drift.py`（**9 passed**：三态 + `None`/空串/全空白 ⇒ UNKNOWN + 首尾空白 ⇒ MATCH + 大小写差异 ⇒ DRIFT + 日期后缀 ⇒ DRIFT + 空声明值被拒） | PASS |
| AC-02 API 读面 | `tests/api/test_models_api.py` 新增 3 条（同名 ⇒ `MATCH`；异名 ⇒ `DRIFT` 且 detail 含两个值；失败 ⇒ `UNKNOWN` 且显式断言 `!= "MATCH"`）+ 词表同源判据（域枚举 ↔ DTO `Literal` ↔ 字段存在） | PASS |
| AC-03 页面三态 | `apps/web/tests/e2e/models-drift-visibility.spec.ts`（**4 passed**：MATCH / DRIFT 点名两值 / UNKNOWN 反义 + 不得出现 Match\&agree / 中文 UNKNOWN）；web `lint`（`--max-warnings 0`）/`typecheck`/unit 绿 | PASS |
| AC-04 反证 | F1（域 UNKNOWN 退化为 MATCH）**3 red**；F2（DTO 摘掉 drift）**3 red**；F3（UNKNOWN 用 MATCH 文案渲染）**1 red**（中文那条），全部复原后绿 | PASS |
| AC-05 诚实边界 | 文档两处（`MODEL_PROBE.md` 漂移判定节 + `LLM_ENDPOINTS.md` §8）+ 页面中英文案同源；live skip 事实见下 | PASS |
| AC-06 门禁 | 定向套件 + web 三件套 + OpenAPI 快照重生成（+47 行，drift 门绿）+ `design-fidelity` 2 passed 且基线零 diff + **m0 全量 23 项** + 治理 `validate.py` | PASS |

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | `assess_model_drift` 的 `UNKNOWN` 分支改判 `MATCH` | `tests/domain/test_model_drift.py` **3 failed**（`None` / 空串 / 全空白 三个参数） | 9 passed |
| F2 | 从 `ProbeResultDto` 摘掉 `drift` 字段 | `tests/api/test_models_api.py` **3 failed**（KeyError: 'drift'） | 15 passed |
| F3 | 把中文 `UNKNOWN` 的文案换成 `MATCH` 那句 | e2e **1 failed**（中文那条；英文那条不受影响，因为只注入了一处文案） | 4 passed |

三处注入均以**逐字节还原**收尾（`git diff --quiet` 复核「与 HEAD 一致」）。

### 设计对照门（零 diff 的射程）

`design-fidelity` **2 passed**，`design-outlines.json` 与 34 路由像素基线**零 diff**。
原因与 MEM-088 同类：漂移块只在**探测之后**渲染（`probe.result !== null`），
路由基线里既没有探测也没有结果 ⇒ 该分支对设计门不可见。渲染级判据是自带 stub e2e（F3 可咬）。

### live 分支：**如实 skip**（不是 PASS）

- 判据来源：cycle 3 的实跑（`scratch/ec03-register-real-supply-chain.log`）已核实本机
  候选环境变量全 `absent`、`endpoint:*` 命名环境变量 0 个；本 cycle 未新增凭据。
- 因此**真实 probe 一次都没跑**：`drift` 的 live 语义（真实 provider 回报什么标识）**未被实测**。
- 本 cycle 的绿全部来自**离线判据**（域 / API / 页面 / 文档）；按判定细则，这不能算
  「漂移可见性已对真实端点验证」，只能算「离线可判部分成立」。

## Warnings（不阻断，如实登记）

- **W-1 live 语义未实测**：见上节。真实 provider 可能不返回 `model` 字段（⇒ `UNKNOWN`）或返回
  带渠道后缀的名字（⇒ `DRIFT`），两种都**没有实测样本**；离线判据只证明了「判定与渲染正确」，
  不证明「对某个真实中转站的判定是对的」。
- **W-2 只对比模型标识，不对比底层版本**：`system_fingerprint` 是另一条独立信号（有/无已在读面
  分开呈现），本 cycle **没有**把 fingerprint 的前后差异纳入漂移判定。跨次探测的 fingerprint
  变化（同一 ID 但版本变了）因此仍不可见。
- **W-3 未持久化**：drift 只活在 probe 响应里（`ProbeResultDto`）。关掉页面即丢；
  「上周探到过漂移」无法回看。把 returned name / drift 落到行里是**另一个决策**
  （要同时想清楚它与 `ModelRuntimeFingerprint` 的关系），本轮按 PLAN 口径不做。
- **W-4 严格口径的代价**：只差大小写、或 provider 加了日期后缀（`model-a-2026-09-20`）都记
  `DRIFT`。这是**刻意的**（本仓无法证明同一性），但真实中转站上可能噪声偏多，读面需要人来判。
- **W-5 `UNKNOWN` 的三种来源未在文案里区分**：没探测 / provider 没回名字 / 探测失败在 DTO 上
  是三态中的同一态（`ok` 与 `returned_model_name` 可区分后两者，页面也显示 `ok`），
  但漂移块本身只说「未探到」。**不是**谎言，只是粒度较粗。
- **W-6 与 W-2/W-3 同源的既有边界**：`_probe_fingerprint` 只在 provider 给了
  `system_fingerprint` 时构建指纹；没给时 `fingerprint=None` 且
  `provider_fingerprint_available=false`（页面如实显示 unavailable，未美化）。

## 结论

**PASS_WITH_WARNINGS**。EC-05 的可判部分全部成立，且每条关键判据都有独立反证（F1–F3）：

1. **三态可判**：`MATCH` / `DRIFT` / `UNKNOWN` 在域层有唯一判据、在 API 有 DTO、在页面有三套
   互不混淆的文案；
2. **「未知 ≠ 无漂移」被两处**独立**钉住**：域层（`UNKNOWN` 是独立枚举值 + F1）与页面
   （反义文案 + F3 反向断言不得出现 `Match`/`agree`）——任一侧退化都会被判据抓住；
3. **严格口径写进文档而不只留在代码**：只做 `strip()`、大小写差异记 `DRIFT`，
   并写明理由（无法证明同一性 ⇒ 不替 provider 打包票）；
4. **漂移是可见性不是熔断**：不改 eligibility、不自动禁用（文档同步）；
5. 残余 6 条如实登记，其中 **W-1（live 语义未实测）** 是**能力边界**——
   本机无凭据，EC-04/EC-05 的 live 部分只能等凭据注入；W-2/W-3（fingerprint 未纳入、
   drift 未持久化）是**已知缺口**，需要单独决策后才做。
