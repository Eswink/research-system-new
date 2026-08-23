# M12 NCBI E-utilities Qualification — 真实学术文献检索 ToolProvider

- 日期：2026-08-22
- 范围：M12 First Real Research Workflow 的最小真实 Research Tool 切片（文献检索 / 读取 / 引用检查）
- 事实优先级：NCBI 官方文档 / 契约测试 / 运行行为 > 本文声明；任何协议变更必须重跑 contract suite

## 1. 上游与协议

| 项目 | 结论 |
| --- | --- |
| 服务 | NCBI E-utilities（`https://eutils.ncbi.nlm.nih.gov/entrez/eutils`） |
| 官方文档 | `https://www.ncbi.nlm.nih.gov/books/NBK25501/`（E-utilities Help） |
| 使用条款 | `https://www.ncbi.nlm.nih.gov/books/NBK25497/`（NLM Terms of Use；无 key 3 req/s、有 key 10 req/s 限流） |
| 协议 | HTTPS REST + JSON/XML；无 OAuth，凭据经 `api_key` query 参数（TOOL 域） |
| 采用形态 | REST adapter（`ProviderType.REST`，`adapters/research_tools/ncbi.py`），**不引入 MCP server**——E-utilities 无官方 MCP server，自建 stdio MCP 包壳只会增加进程边界，无隔离收益 |
| 使用端点 | `esearch.fcgi`（检索，retmode=json）、`efetch.fcgi`（读取，retmode=xml）、`elink.fcgi`（引用，retmode=json）、`einfo.fcgi`（健康，retmode=json） |
| resolution pin | `2026-08-22-eutils-api`（E-utilities 接口变更门禁；任何上游协议变更必须重跑 `tests/contracts/test_ncbi_provider_contract.py`） |
| 供应链登记 | `UPSTREAM_COMPONENTS.yaml`（id `ncbi_eutils`，ADOPTED/HTTP_API）、`docs/references/LICENSE_MATRIX.md`、ToolPack manifest `examples/contracts/toolpack_ncbi_eutils.yaml`（content digest `sha256:947cbb22…`） |

## 2. Adapter 边界（与 M8 ToolProvider Port 契约对齐）

- 参数经 ArtifactStore 传递：调用方写 `tool-args:{task_id}:{operation_key}`（JSON），adapter 读取并校验 `Digest.of_bytes(content) == call.argument_digest`（内容寻址防篡改）。
- 结果经 `spill_large_result` 落 ArtifactStore，`ToolResultRecord` 只留 `output_digest`（AGENTS.md §10 观测隐私：内容不进日志/遥测）。
- 凭据只经 `CredentialResolver` 按 TOOL 域引用解析（默认 `NCBI_API_KEY`），以 `api_key` 参数注入；禁止 token passthrough；异常消息统一 redaction。
- 限流遵守 ToS：`NcbiEutilsConfig.min_request_interval_seconds`（默认 0.34s ≈ 3 req/s 保守值，有 key 可调小），请求间强制间隔。
- **ToolResult 不直接成为可信 Evidence**：检索命中只是候选来源，必须经 M10 `SourceRecord` 登记与 `Evidence` 绑定后才可支撑 Claim（契约测试与 evidence 链测试分别锁定）。

## 3. 错误分类（FAILURE_MODEL 对齐）

| 场景 | 分类 | retryable |
| --- | --- | --- |
| httpx 超时 | `PortTimeoutError(TOOL_TIMEOUT)` | True |
| HTTP 429（限流） | `TransientPortError(TOOL_UNAVAILABLE)` | True |
| HTTP 5xx / 连接失败 | `TransientPortError(TOOL_UNAVAILABLE)` | True |
| HTTP 403（key 无效） | `PermanentPortError(TOOL_UNAVAILABLE)` | False |
| JSON/XML 解析失败、缺字段 | `PermanentPortError(TOOL_SCHEMA_MISMATCH)` | False |
| 参数 digest 不匹配、非法工具 id | `InvalidInputError`（VALIDATION_FAILURE） | False |

## 4. 测试与故障注入（17 项 contract suite）

- 成功路径：esearch（JSON）、efetch（XML 解析为结构化 article）、elink（PMC links）。
- 防篡改：参数 artifact digest 不匹配 → permanent；缺失参数 artifact → permanent。
- 故障注入：429 → transient；超时 → TOOL_TIMEOUT；连接失败 → transient；畸形响应 → TOOL_SCHEMA_MISMATCH。
- 凭据域：有/无 key 时的 `api_key` 参数断言（mock transport 捕获请求）；禁 passthrough。
- 健康：einfo 成功 → HEALTHY + schema digest；失败 → OPEN_CIRCUIT。
- 限流：间隔 0.2s 时连续两次请求耗时 ≥0.15s。
- 真实网络冒烟：`requires_live_llm` marker 手动运行（有 `NCBI_API_KEY` 时执行一次 `literature_search`）。

## 5. 升级门禁与退出计划

- 升级门禁：E-utilities 协议/字段变更 → 重跑 provider contract suite + ToolProvider contract suite；限流策略变更 → 更新 `NcbiEutilsConfig` 默认值并回归。
- 退出计划：若 NCBI 停止 E-utilities 或变更 ToS 不可接受，按 `dependency > adapter > shim > fork` 顺序评估替代（OpenAlex / arXiv API 等价 adapter），不进入 Domain。
- 不扩大范围：不批量接入其它科研服务；本切片仅服务 M12 Reference Workflow 的 `literature.search / literature.read / citation.inspect`。

## 6. 判定

NCBI E-utilities 满足 M12「真实 Research Tool production path」要求：官方 API + 明确 ToS/license + TOOL 凭据域隔离 + 超时/重试/限流/畸形处理 + 大结果 Artifact indirection + ToolResult 不直升 Evidence。**Qualification PASS。**