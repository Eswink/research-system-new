---
id: RECHECK-20260920-119
plan_id: PLAN-20260920-119
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-008-cycle6
baseline_ref: 099bd62
checked_head: affc063
---

# RECHECK-20260920-119 — 真实端点 runbook（EC-06 复检）

## 检查范围

不采信「文档写好了」这种叙述：按 EC-06 判据在**当前树**上真跑，并把判据本身
用**先红后复原**的反证压一遍。检查面：

- **存在与索引**：runbook 存在；`docs/INDEX.md` 的 Integrations 清单里有**条目行**；
- **五类内容**：登记（DB 路径 + YAML 路径）/ 凭据注入与轮换 / 重启后重输的边界 /
  Fake↔真实切换与回退 / 「哪些面仍是 demo」清单——缺任一类判红；
- **同源**：文档里引用的仓库路径都存在（运行期产物按逐条白名单豁免）、
  大写变量名都在代码里出现、pytest 目标都存在、demo 符号都在代码里存在；
- **凭据纪律**：文档只写变量名与边界，不写值、不写示例 key。

## 检查结果

### 判据（实测）

| AC | 判据 | 结果 |
| --- | --- | --- |
| AC-01 存在且被索引 | runbook 存在；`docs/INDEX.md` 的 Integrations 清单含 `- \`integration/LIVE_MODEL_RUNBOOK.md\`` | PASS |
| AC-02 五类内容 | `test_runbook_same_source.py` 判五个小节标题逐条存在 + 「重启边界」点名 `RegistryCredentialResolver` 与 `_registry`（落到机制，不是口号）+ 切换小节点名 `RESEARCHOS_AGENT_RUNTIME` / `openhands` | PASS |
| AC-03 同源 | 路径存在性（引用了 14 个仓库路径 + 13 个 `adapters/fakes/*.py`，全部真实存在）、变量名（`LLM_MAIN_KEY` / `RESEARCHOS_AGENT_RUNTIME` / `FAKE_RUNTIME` / `OPENHANDS_RUNTIME` / `MODEL_TOKENS` / `NOT_VERIFIED` … 全部在代码里出现）、pytest 目标存在、demo 符号存在 | PASS |
| AC-04 反证 | F1–F5 全部**先红后复原**（见下表） | PASS |
| AC-05 凭据纪律 | 文档只出现变量名（`LLM_MAIN_KEY`）与边界说明；无凭据值、无示例 key；`tools/credential_audit.py` 的既有四面扫描口径不受影响 | PASS |
| AC-06 门禁 | 定向 `10 passed` + `docs_consistency_check`（DOCS-CHECK PASS: 6 checks）+ 治理 `validate.py` / `validate_bundle` + **m0 全量 23 项**（`PASS: profile=m0; 23 deterministic checks`；**4201 passed / 12 skipped**，489.62s，代码树 `affc063`；cycle 5 为 4190/12 ⇒ 净增 11 条判据） | PASS |

### 反证（先红后复原，均在本轮实测）

| # | 注入的缺陷 | 观察到的红 | 复原后 |
| --- | --- | --- | --- |
| F1 | 把一个仓库路径改成不存在的（`adapters/sqlite/endpoint_store_v2.py`） | **1 failed** | 10 passed |
| F2 | 把环境变量名改错一个字符（`RESEARCHOS_AGENT_RUNTIMEX`） | **1 failed**（**第一次跑时没红——判据本身有洞，见下**） | 10 passed |
| F3 | 把「重启后重输的边界」小节改名 | **1 failed** | 10 passed |
| F4 | 把 `docs/INDEX.md` 的登记条目换成别的文档 | **1 failed**（**第一次跑时也没红——判据太松，见下**） | 10 passed |
| F5 | 把 demo 清单里的一个 `Fake*` 换成不存在的符号 | **1 failed** | 10 passed |

五处注入均以**逐字节还原**收尾（每步 `git diff --quiet -- <path>` 复核「与 HEAD 一致」，
脚本 `scratch/ec06-falsification.py` 把这一步作为**失败条件**而不是提示）。

### 反证抓出的两个判据缺陷（本轮最有价值的一段）

1. **F2 没红 ⇒ 判据在「没看」而不是「看过没问题」**：判据用 `re.findall(r"`([^`]+)`", 全文)`
   抽反引号 token，**跨行配对**会被 Markdown 代码围栏（```）打乱，于是文档里明明用反引号
   写着的 `RESEARCHOS_AGENT_RUNTIME` 根本没进 token 集合——变量名判据因此永远绿。
   改成**按行抽取**（行内代码本来就不跨行，代码围栏行跳过）后，F2 立刻红。
2. **F4 没红 ⇒ 判据太松**：原来只判「`docs/INDEX.md` 全文出现过该路径」，
   而快捷问答里的一句引用就能满足它——清单漏项（这份索引最容易漂的地方）反而放行。
   改成判 **Integrations 清单的条目行**（`- \`integration/LIVE_MODEL_RUNBOOK.md\``）后，F4 红。

两条都是**判据缺陷**，按缺陷修判据（不是放宽、也不是改文档）：`affc063`。
这件事本身的教训写进了结论：**新写的判据必须被反证压过一遍**，
否则「绿」可能只是「没看」。

## Warnings（不阻断，如实登记）

- **W-1 同源判据只覆盖「存在性」**：路径存在、变量名出现、符号存在——
  它**不**保证 runbook 描述的行为与代码行为一致（例如「重启后凭据要重输」是机制推断，
  不是本轮的实跑观测；机制侧另有判据：`tests/api/test_llm_endpoints_api.py` 的
  `test_credential_does_not_survive_a_restart`，但那是**另一条**判据，不在本判据射程内）。
- **W-2 大写变量名判据是启发式的**：规则是「全大写 + 至少一个下划线的 token 必须出现在代码里」。
  单个大写词（如 `ANTHROPIC`）不判——避免把普通术语误判成变量名。代价是漏掉单字变量名。
- **W-3 运行期产物白名单是人维护的**：目前只有 `data/research-os-control.db` 一条，
  且判据会检查「白名单条目仍然出现在文档里」（不留死条目），但**新**的运行期路径需要人来加。
- **W-4 demo 清单的完备性没判**：判据只保证「列出来的符号存在」，不保证「存在的 Fake 都被列出来」
  （漏列不会红）。清单是清点结果，不是穷举证明。
- **W-5 live 步骤仍是「未实测」**：runbook 第 4 节描述的开/关与回退流程，本机**没有**跑过
  （无凭据、未配 runtime ⇒ 门两条都关着）。文档如实标注了这一点，但「按文档能跑通」
  这件事本身仍未验证。
- **W-6 文档里的 HTTP 片段未执行**：`curl` 示例按既有路由（`services/api/routers/llm_endpoints.py`
  的 `/llm-endpoints`、`models.py` 的 `/models`）写成，路径由判据核对存在，
  但**请求体形态**（`@endpoint.json` / `@model.json`）没有实跑校对。

## 结论

**PASS_WITH_WARNINGS**。EC-06 的四类内容 + demo 清单**逐类可判**，同源判据把文档钉在代码上，
且每条判据都有反证；本轮反证**抓出并修掉了判据自身的两个洞**（F2/F4），这是这条 EC 最有价值的产出：

1. **登记步骤**：YAML 路径（`examples/config/llm_endpoints.yaml` / `models.yaml` /
   `model_profiles.yaml`）与 DB 路径（`data/research-os-control.db` 的 `llm_endpoints` / `models`
   两张表）分别写清，并注明 DB 是**运行期产物**（gitignored、clean checkout 不存在）；
2. **凭据注入与轮换**：两套面（环境变量 / API 注册表）分别写清 ref 形态与轮换动作；
3. **重启边界**：落到机制（`RegistryCredentialResolver._registry` 是内存字典 ⇒ 进程结束即消失），
   并明写「不伪装 Secret Manager」；
4. **Fake↔真实切换与回退**：`RESEARCHOS_AGENT_RUNTIME` 的开（`openhands`）/ 关（去掉变量）
   与回退三步检查；
5. **仍是 demo 的面**：13 个 Fake 逐条列出（符号由判据核对存在），并对照列出**已接通的真实件**，
   以及「真实端点上的 run 从未发生」这条如实边界。

残余 6 条如实登记；其中 W-1（判据只覆盖存在性）与 W-4（demo 清单完备性未判）是**射程边界**，
W-5/W-6（live 步骤与 HTTP 片段未实测）是**能力边界**（无凭据）。
