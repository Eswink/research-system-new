---
id: RECHECK-20260920-116
plan_id: PLAN-20260920-116
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle3
baseline_ref: dd989b7
checked_head: 18794a1
---

# RECHECK-20260920-116 — 供应链登记与凭据纪律（EC-03 复检）

## 检查范围

不采信实施叙述：按 EC-03 判据在**当前树**上真跑，逐条做**先红后复原**的反证，门禁以
**完整 m0（23 项）**为准而不是「定向套件绿」。检查面：

- **URL 策略**：五类地址（localhost / 环回全段 / 私有 / 链路本地 / 保留）逐类拒绝且点名；
  公网 https 放行；豁免语义不变；**唯一裁决点**不新增第二处；
- **出站 0**：被拒 URL 与缺凭据两条路径都不得触网（记录型 transport 证明）；
- **登记入库**：真实端点 + 模型经**既有 API** 写进配置面，读回可判，**行里无密钥**；
- **明文审计**：仓库跟踪文件 / `.cursor/plans` 记录 / 配置面 DB / 日志四面扫描，命中即红；
- **重启边界**：生产解析器的进程级语义 + 文档/UI/代码三面同源；
- **无凭据诚实行为**：`/test`、`/health`、`/discover-models` 在无凭据时点名失败、不触网。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 URL 策略补严 | `tests/application/test_endpoint_policy.py`（**31 条**；含 `TestReservedAndLoopbackClasses` 13 条 + `test_link_local_owns_its_switch` 2 参数：8 个保留类地址逐个拒、环回全段拒、拒因点名、`allowed_hosts` 豁免仍可用、公网 IPv6 放行） | PASS |
| AC-02 出站 0 | `tests/application/test_endpoint_test.py::TestZeroOutbound`（4 条：多播被拒 / 环回被拒 / 缺凭据 三情形各断言 `gateway.calls == ()`；第 4 条是**对照**，放行时 `method_calls("probe_endpoint") >= 1`，否则前三条是空断言） | PASS |
| AC-03 登记入库 | `scratch/ec03-register-real-supply-chain.py`（实跑，日志 `scratch/ec03-register-real-supply-chain.log`）：端点 `e7f210a2-2c4f-4ea6-bc3f-814b3cd7837e`（`protocol=ANTHROPIC`、`base_url=https://apihub.agnes-ai.com`、`credential=missing`）+ 模型 `5bec513d-6382-4725-8777-92e3b6c76f9b`（`agnes-2.5-flash`、`context_window_tokens=512000`、`thinking_intensity=MAX`）；**二跑走复用路径**（`reused`，无重复行） | PASS |
| AC-04 明文审计 | `tools/credential_audit.py` + `tests/tooling/test_credential_audit.py`（4 条）；实测 `tracked 3146 files / 94 hits 全放行 / 0 offenders`、`records 259 / 3 / 0`、`config_db 1 / 0 / 0`、`logs 147 / 0 / 0` ⇒ PASS | PASS |
| AC-05 重启边界同源 | `tests/architecture/python/test_credential_boundary_wording.py`（2 条：三面同源 + 禁止不实声明）+ `tests/api/test_llm_endpoints_api.py::test_credential_does_not_survive_a_restart` / `::test_registry_resolver_starts_empty_for_each_process` + `apps/web/tests/e2e/endpoint-credential-boundary.spec.ts`（2 条：中英读面） | PASS |
| AC-06 无凭据如实失败 | 同 AC-03 脚本：`POST /test → 200 {"ok": false, "error_category": "CONFIGURATION", "error_message_redacted": "credential resolution failed: credential_ref not found: 'endpoint:e7f210a2…'"}`；`GET /health → 422 Credential Missing`；`POST /discover-models → 422` | PASS |
| AC-07 门禁 | 定向套件 + `ruff format/check` + 规模门 + **m0 全量 23 项** + 治理 `validate.py`（见「门禁」节） | PASS |

**配置面行（只读复读，密钥列不存在）**：

```text
llm_endpoints  endpoint_id=e7f210a2-…  endpoint_json={"api_style":"chat_completions",
  "base_url":"https://apihub.agnes-ai.com","credential_ref":"endpoint:e7f210a2-…",
  "enabled":true,"id":"e7f210a2-…","max_retries":1,"name":"agnes-apihub","protocol":"ANTHROPIC",
  "request_timeout_seconds":120}
models         model_id=5bec513d-…  model_json={"capabilities":{},
  "context_window_tokens":512000,"display_name":"agnes-2.5-flash (declared by operator)",
  "enabled":true,"endpoint_id":"e7f210a2-…","id":"5bec513d-…","model_name":"agnes-2.5-flash",
  "thinking_intensity":"MAX"}
```

两个 blob 里**都没有**密钥字段——只有 `credential_ref` 这个名字（凭据审计的 `config_db` 面
在登记**之后**复跑仍 0 命中，是对同一事实的第二条独立判据）。

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | `_host_kind` 的 reserved 分支短路（`and False`） | 保留类判据 **5 failed**（多播 / IPv6 多播 / CGNAT + 拒因点名 + 无开关） | 31 passed |
| F2 | 把 `is_private` 判据挪回 `is_link_local` **之前**（改动前的顺序） | `test_link_local_owns_its_switch` **2 failed**（`169.254.169.254` 与 `fe80::1` 都被归入 private，拒因与开关都错） | 31 passed |
| F3 | `run_endpoint_test` 对多播地址**不**短路（落到 gateway） | `test_refused_reserved_url_never_reaches_the_gateway` **1 failed**（`ok=True` ⇒ 请求真的发出去了） | 10 passed |
| F4 | 往**跟踪文件**里追加一行陌生杜撰键（`docs/INDEX.md`） | 审计 `exit=1`，点名 `docs/INDEX.md:216 [openai-style-key]` + `[assigned-secret]`，**不回显**匹配文本 | 逐字节还原后四面归零 |
| F5 | 删掉文档里「重启后需重新注入」这句 | 措辞判据 **1 failed**（`文档 §9 缺少措辞`） | 2 passed |
| F6 | 往文档塞入假持久化声明（`凭据由 Secret Store 托管`） | 措辞判据 **2 failed**（缺「不伪装 Secret Manager」+ `出现不实声明：'Secret Store'`） | 2 passed |
| F7 | 把注册表提成**类级**共享 dict（等价于「凭据被持久化」） | `test_credential_does_not_survive_a_restart` + `test_registry_resolver_starts_empty_for_each_process` **2 failed**（`has` 返回 True） | 14 passed |
| F8 | 摘掉 UI 里 `<CredentialBoundaryNotice/>` 的**挂载**（函数体保留） | `endpoint-credential-boundary.spec.ts` **2 failed**（抽屉里找不到 `endpoint-credential-boundary`） | 2 passed |

F4/F5/F6 由两个可复跑脚本驱动并留日志：`scratch/ec03-credential-audit-falsification.py`
（`…log`）、`scratch/ec03-wording-gate-falsification.py`（`…log`）；两者都断言「还原后与原
文件逐字节一致」。F1/F3 的反证记录在各自提交信息里（cycle 3 WP-A/WP-B）。

**F8 的射程必须写清**：摘掉挂载后**措辞判据仍绿**（它钉的是「文件里有这些字」，不是
「这些字被渲染」）⇒ 渲染级判据只有 e2e spec。这是两条判据的分工，不是冗余。

### 设计对照门（零 diff 的射程）

`pnpm --dir apps/web exec playwright test design-fidelity` **2 passed**，`design-outlines.json`
与 34 路由像素基线**零 diff**。原因不是「页面没改」：新文案住在**端点详情抽屉**里，
而 `library-endpoints` 的截图与结构签名都在**抽屉未打开**时取（`selected === undefined`
时抽屉内容不渲染）。⇒ 该分支由自带 e2e spec 覆盖（F8 可咬），设计基线**无需**按配方重生成。
与 MEM-20260920-088 同类：**新渲染分支可能落在既有门禁的盲区**。

### 复检**实测出的缺陷**（本轮先修后记）

- **link-local 空开关**（提交 `1e16c40`）：`_host_kind` 里 `is_private` 排在 `is_link_local`
  之前，而 CPython 把 `169.254.0.0/16` 与 `fe80::/10` 也算私有 ⇒ `link_local` 分支**不可达**，
  拒因点名错的类别，`EndpointUrlPolicy.allow_link_local` **永不生效**。默认都被拒，所以
  不是放行漏洞；但「声明了开关却不生效」与「拒因指错类别」都是读面谎言。已修 + F2 钉住。
- **审计工具的自证能力缺口**（提交 `eee4728`）：`--root` 之前不存在，反证只能落在真树上
  （往跟踪文件写探针再删）。现在 `--root` 可就地审计另一份 checkout（收口封印用），
  且「该扫而扫不成」（根不是 git 工作树）记 `not_a_git_tree` **判红**，不再静默通过。
- **G1（m0 拦下）**：`python/typecheck` 判红 —— 新用例里 `int(faces["x"]["files_scanned"])`
  配 `# type: ignore[arg-type]` 同时触发 `unused-ignore` 与 `call-overload`（`json.loads` 是
  `Any`，元素是 `object`），`offenders` 那行还触发 `attr-defined`。**按缺陷修**（提交 `5f43b98`）：
  改成 `_count` / `_offenders` 两个先断言类型再返回的助手，判据强度不变（断言失败即红），
  不用 ignore 掩盖读 JSON 的边界；**未动门禁、未降断言**。m0 本轮为 fail-fast：
  该检查一红即停，故修完后才重跑全量。

### 门禁

- `python/format-check` / `python/product-lint` / `python/typecheck`（**951 files**）/ `python/tests`：
  PASS（全量 m0 一次跑齐）。
- **定向套件（带 DSN 钉桩）**：`tests/api + tests/application + tests/architecture + tests/tooling`
  **2292 passed / 2 skipped**，其中 2 条失败在补上 `RESEARCHOS_POSTGRES_DSN` 后转绿
  （`tests/api/test_worker_plane_composition.py` 两条需要**真 DSN** 构造 PG worker registry；
  只置空 DSN 会 `ValueError: PostgresWorkerRegistry requires dsn or connection`）。
  这是**已知的 DSN 钉桩条件**，不是本轮改动引入的回归——须与 m0 使用同一份钉桩配方。
- **web**：`lint`（`--max-warnings 0`）/ `typecheck`（`tsc --noEmit`）/ e2e 新增 spec 全绿；
  `design-fidelity` 2 passed 且基线零 diff。
- **本地 m0（profile=m0）**：**PASS: profile=m0; 23 deterministic checks**，
  测试计数器 **4131 passed / 11 skipped**（冻结树 `5f43b98`，耗时 479.71s；
  cycle 2 为 4097 passed ⇒ 本轮净增 34 条判据）。其后的记录类改动（本 RECHECK 的 G1 段、
  PLAN 证据计数、GOAL 状态历史与 CI 台账）**只改 `.cursor/**`**，已单独复跑
  `framework/validate_bundle` / `framework/docs_consistency_check` / 治理 `validate.py` 三门；
  **未**重跑全量 m0 —— 上述 23/23 与 4131 对应 `5f43b98`，这一点如实登记。

## Warnings（不阻断，如实登记）

- **W-1 注册面仍不校验 URL**：`POST /llm-endpoints` 直接落库，存疑 URL（多播 / CGNAT / localhost）
  仍可登记成功，**一跑就被拒**（probe / run / preflight 三处都过 `validate_endpoint_url`）。
  本轮按 PLAN 口径**不改**注册语义（改「注册即拒」是 API 行为决策，属 escalation）。判据只覆盖
  「被拒时出站 0」，不覆盖「注册时拒绝」。
- **W-2 全链路出站 0 只在 Fakes 上证明**：`TestZeroOutbound` 用的是记录型 Fake gateway。
  生产网关（httpx）在策略层之后的出站未做**网络级**观测；能把「没出网」证到 socket 层的只有
  live 轮次（本轮无凭据，见 W-6）。不得把 `calls == ()` 读成「已在真实网络上验证零出站」。
- **W-3 措辞判据不覆盖「是否渲染」**：见 F8 的射程说明；两条判据分工，e2e 是渲染级唯一判据。
- **W-4 UI 只改了**端点详情抽屉**一处**：录入向导（`library-setup` 路由）的文案未加边界声明
  （其代码注释自称「页面任何状态不保存明文 Key」，是真话但不是给用户看的读面）。
  同一事实已在端点详情 + 文档 + 解析器 docstring 三面可读；**向导面列为残余**。
- **W-5 审计工具的白名单是**值级**而非路径级**：`ALLOWED_SUBSTRINGS` 逐条给理由，但白名单
  本身是**人维护**的——新增一个真实凭据若恰好**包含**某个已放行子串（例如 `sk-test` 前缀），
  会被静默放行。当前 14 条都指向测试替身/占位串，风险低；**不是**零风险设计。
- **W-6 「凭据缺失」是当前事实而非永久状态**：本机候选环境变量全 `absent`，`endpoint:*` 命名
  的环境变量 0 个 ⇒ EC-04/EC-05 的 live 分支只能如实 skip。凭据一旦按 `credential_ref` 同名
  注入环境变量，同一套判据不需要改动即可放行。
- **W-7 `.env` 不在四面扫描范围内**：审计的 `tracked` 面只扫 `git ls-files`，而 `.env`
  是 gitignored（且 `git check-ignore` 确认被 `.gitignore:1` 覆盖）。这是**有意**的取舍——
  `.env` 本就是凭据的合法落点；但「本机存在一个真实 `DEV_LLM_API_KEY`」这类事实不会进审计
  报告，须靠「`.env` 必须保持 untracked」这条独立纪律兜住（本轮复核：`git ls-files` 无 `.env`）。

## 结论

**PASS_WITH_WARNINGS**。EC-03 的可判部分全部成立，且每条关键判据都有独立反证（F1–F8）：

1. **URL 策略**五类地址逐类拒绝、点名、出站 0；保留类**无放行开关**（只走 `allowed_hosts`）；
   实跑还揪出并修掉一个**空开关 + 错类别**缺陷（F2）；
2. **登记**经既有 API 走通并**幂等**（二跑复用同一行），配置面只有 `credential_ref` 名字，
   读面 `credential=missing`，三处调用在无凭据时全部点名失败且不触网；
3. **明文审计**四面逐面报数（0 命中）、放行项逐条给理由、真实树注入会咬（F4）；
4. **重启边界**由生产解析器语义（F7）+ 三面同源措辞（F5/F6）+ 渲染级 e2e（F8）三方钉住，
   文档里「加密 / Secret Store」这类不实口径已删除；
5. 残余如实登记 7 条，其中 W-1（注册面不校验）与 W-2（出站 0 只在 Fakes 上证明）是**能力边界**，
   W-4（向导面未加声明）与 W-5（白名单人维护）是**已知缺口**。
