# MIMOSA 收口后复核记录（GOAL-20260918-005 EC-01）

- 日期：2026-09-18
- 上游记录：`docs/audits/MIMOSA_DEEP_SCAN_20260917.md`（GOAL-20260917-004 EC-07 终态 a）
- 本轮范围：GOAL-004 收口结论表第 1 项（安全审计残留）——① 依赖 advisory **联网复核**
  （署名与结论）；② **干净 checkout** 重扫（可复核封印终态）；③ hook 侧
  `scanner_enobufs` **复现与根因**；④ 未覆盖范围写明。
- **本记录不主张「项目安全」**，也不以「扫描没报问题」作为任何结论的依据。PASS 的依据是
  **可复核的署名与封印**，以及**可重跑的命令**（§7）。

---

## 1. 干净 checkout 重扫

### 1.1 输入边界（导出配方）

GOAL-004 EC-07 的扫描输入是**工作树**（2748 个文件），其中包含 `.gitignore` 覆盖的
`scratch/`（未跟踪调试脚本）与 `artifacts/`（未跟踪第三方转储）——36 条 findings 里有
19 条落在这些非仓库内容上（RECHECK-091 W-3）。本轮把扫描输入换成**只含 tracked 内容**的
导出树：

```bash
git archive HEAD | tar -x -C <仓库外目录>
```

| 判据 | 实测 |
| --- | --- |
| 导出树文件数 | **3025** |
| `git ls-files` 条数 | **3025**（两者相等 ⇒ 导出 = tracked 集合） |
| 导出树内 `scratch/` | 不存在 |
| 导出树内 `artifacts/` | 不存在 |

导出目录：`C:\Users\googl\AppData\Local\Temp\goal005-clean-20260918125905`
（扫描根 = 该目录；仓库外，产物另存于 `~/.mimosa/security-scans/<projectId>/`）。

### 1.2 扫描与封印

```text
通道        MCP security_scan_start(project=<clean dir>, depth=deep)
scanId      scan-2026-09-18T05-00-08.268Z-e6e01fa153c8
projectId   project-5b8ffd83a55c49d5102c2557
seal        sha256:1e549272da4ebf65a87b02d195bf714ed3ef75b29b2db6d689331a617b51116d
runStatus   inconclusive        completeness  partial
source      limit 26749 / selectedFiles 1837 / parsedFiles 1837 / truncated false
totals      high 1 / medium 19 / low 5 / info 0 / businessLogic 0 = 25
```

**封印可复核性**（逐件重算 sha256 与 `seal.json.artifacts` 对照）：

| 产物 | 复算结果 |
| --- | --- |
| `scan-manifest.json` | OK（`sha256:99a563ef6266d477991…`） |
| `findings.json` | OK（`sha256:88861e9bca8f605811f…`） |
| `coverage.json` | OK（`sha256:400b2998acd953d1c91…`） |

### 1.3 与工作树扫描（2026-09-17）的差异

| 严重度 / 顶层目录 | 工作树扫描（36） | 干净 checkout（25） |
| --- | --- | --- |
| high / `artifacts/` | 2 | **0** |
| high / `packages/` | 1 | 1 |
| medium / `scratch/` | 17 | **0** |
| medium / `services/` | 1 | 1 |
| medium / `tools/` | 10 | 18 |
| low / `examples/` | 5 | 5 |

**这是判据有效性的正面证据**：同一台扫描器、同一天、同一份代码，只把输入边界从
「工作树」换成「tracked 导出树」，落在这两类非仓库内容上的 19 条 findings 全部消失
（`artifacts/` 2 条 HIGH + `scratch/` 17 条 MEDIUM），且 `tools/` 从 10 条升到 18 条
（旧扫描的输入选择在文件数上限下漏掉了部分 `tools/` 文件）。**输入边界改变了结论** ——
说明「未覆盖范围」不是套话，而是会实际改变 findings 集合的判据。

### 1.4 本轮的覆盖缺口（与上一轮同口径）

- `threatModel` 阶段仍是 `partial`：**0 入口 / 0 主体 / 0 授权面** ⇒ 越权、BOLA/BFLA、
  业务逻辑**不在射程**。
- `validation.investigated = 0`：静态 only，无运行时验证。
- 依赖阶段：见 §2.3——本轮扫描自报 `packagesScanned = 11 / matched 0`，覆盖极不完整，
  **不能**当作依赖面结论。

---

## 2. 依赖 advisory 联网复核（署名与结论）

### 2.1 方法与可复跑命令

`uv.lock`（PyPI）与 `pnpm-lock.yaml`（npm）里**每一个锁定包**逐一向 OSV 查询：

```bash
python tools/probes/probe_dependency_advisories.py --root . > batches.jsonl
curl -s -X POST https://api.osv.dev/v1/querybatch \
     -H 'Content-Type: application/json' --data @batch-1.json > response-1.json
python tools/probes/probe_dependency_advisories.py --root . --responses response-1.json
```

探针本身**不含网络代码**（只读 lockfile、构造 payload、合并响应）；唯一出网步骤是上面
那条 `curl`。查询时间：2026-09-18T05:01:28Z。

| 输入 | sha256 | 包数 | 查询数 |
| --- | --- | --- | --- |
| `uv.lock` | `sha256:98af1c423afe114cba173502674b9f3340763ad9f0ca50a550f0f61cf5f33390` | 149 | 149（PyPI） |
| `pnpm-lock.yaml` | `sha256:fb03b4db50e1d2f4e87bef04810a91fea165d32aed6181ec2939b58d503458f5` | 264 | 264（npm） |

**结果：3 个包命中 20 条 advisory**（完整清单见
`docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20260918.json`）。

### 2.2 署名与结论

| 包 | 版本 | 来源（谁引入） | 条数 | 最高 CVSS v3 | 可修复版本 |
| --- | --- | --- | --- | --- | --- |
| `undici` | 5.29.0 | `@cursor/sdk@1.0.30`（根 `devDependencies`）的传递依赖 | 12 | 7.5（GHSA-p88m-4jfj-68fv：Set-Cookie 百分号解码导致 HTTP 头注入） | 6.23.0 / 6.24.0 / 6.27.0 / 6.28.0（及 7.x / 8.x 对应版本） |
| `vite` | 6.3.5 | `apps/web` 的 `devDependencies`（直接声明） | 7 | 7.5（GHSA-fx2h-pf6j-xcff：Windows 备选路径绕过 `server.fs.deny`） | 6.3.6 / 6.4.1 / 6.4.2 / 6.4.3 |
| `yaml` | 2.8.1 | `apps/web` 的 `devDependencies`（直接声明） | 1 | 4.3（GHSA-48c2-rrv3-qjmp：深层嵌套 YAML 触发栈溢出） | 2.8.3 |

- 20 条全部有 CVE 别名与 `fixedVersions`；`undici` 的 12 条含请求/响应走私、CRLF 注入、
  cookie 属性注入、WebSocket 解压内存放大等；`vite` 的 7 条含开发服务器任意文件读取与
  `server.fs.deny` 绕过（含 Windows 备选路径）；`yaml` 的 1 条是解析深层嵌套时的栈溢出。
- **影响面判定**：三个包**都不在生产运行依赖链上** —— `apps/web` 的运行依赖只有
  `react` / `react-dom`；`undici` 挂在根 `devDependencies` 的 `@cursor/sdk` 之下；`vite`
  与 `yaml` 是 `apps/web` 的构建/开发工具链。**但 dev 链不等于无风险**：`vite dev server`
  与 YAML 解析都跑在开发者机器与 CI 上，且 `yaml` 的栈溢出对「解析不可信 YAML」的工具
  路径仍然成立。
- **本轮不改依赖版本**：升级 `vite` / `yaml` / `undici` 属**上游 pin 变更**，命中本 GOAL 的
  `escalation_triggers`（`新依赖/上游版本 pin 变更`）⇒ 留给用户/ADR 拍板（见 §6）。

### 2.3 与扫描器自报的矛盾（这是本轮最重要的方法发现）

| 来源 | 包数覆盖 | 命中 |
| --- | --- | --- |
| 2026-09-17 工作树深扫（自报） | 182 | 1 包 1 条，`packages` 数组为空（**未署名**） |
| 2026-09-18 干净 checkout 深扫（自报） | **11** | 0 |
| 本轮独立 OSV 查询（413 个锁定包） | **413** | **3 包 20 条**（署名 + 修复版本） |

同一份 lockfile、同一天：扫描器的依赖阶段两次自报**互相矛盾**（182/1 与 11/0），且都远
小于锁定包总数（413）。**结论：扫描器的依赖 advisory 阶段不能作为依赖面结论的依据**；
它是一个覆盖率不完整的辅助信号。上一轮「1 包 1 条未署名」既不能确认也不能否认——
本轮用可复核的独立查询给出了署名结论（3 包 20 条），并如实登记两者不一致。

---

## 3. hook 侧 `scanner_enobufs`：复现与根因

### 3.1 复现（本机，2/2 次一致）

```bash
echo '{"hook_event_name":"PreToolUse","session_id":"sess_probe_enobufs",
       "cwd":"D:\\research-system","tool_name":"Bash",
       "tool_input":{"command":"git commit -m probe"}}' \
  | node ~/.zcode/cli/plugins/cache/zcode-plugins-official/mimosa/1.0.3/payload/hooks/git-gate-hook.mjs
```

输出（两次运行分别为 790 ms / 767 ms，逐字相同）：

```json
{"systemMessage":"🛡 Mimosa L3：git commit 前深度扫描为 INCONCLUSIVE（scanner_no_output）；不能视为安全。当前兼容模式失败开放。",
 "hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"Mimosa 在 git commit 前没有得到完整扫描结论（scanner_no_output）。本次按兼容策略继续，但不要宣称项目安全；请尽快重新运行完整审计。"}}
```

⇒ hook 侧这个门的**状态码是 `scanner_no_output`**（宿主会话里显示的
`scanner_enobufs` 是同一现象在客户端侧的名字）；策略是**失败开放**（fail-open）。

### 3.2 根因（已定位）

```bash
node <mimosa>/payload/dist/cli.js semgrep status --json
```

```json
{"schemaVersion":"mimosa-managed-semgrep-status/v1","installed":false,"healthy":false,
 "version":"1.136.0","semgrepPath":"",
 "installDir":"C:\\Users\\googl\\.zcode\\mimosa-runtime\\semgrep-1.136.0",
 "source":"https://pypi.org/simple","license":"LGPL-2.1-only",
 "reason":"install_metadata_missing"}
```

- `installDir` **不存在**；`which semgrep` 无命中；`pip show semgrep` 无该包。
- 插件 README 明示检测层依赖 **semgrep**（固定 `1.136.0`，需显式安装到
  `~/.zcode/mimosa-runtime/`）。L3 的 `git commit/push` 深度审计需要该检测层；
  检测层缺失 ⇒ 扫描器**无输出** ⇒ hook 判定 `INCONCLUSIVE(scanner_no_output)` ⇒ 失败开放。
- **旁证（同一机制的另一面）**：`~/.zcode/mimosa-debug.log` 中 stop-hook 的批量扫描出现
  `scan=empty status=? error=spawnSync D:\environment\nodejs\node.exe ETIMEDOUT`
  （本机 2026-09-02 起累计 224 行），随后 `findings=0 status=inconclusive`；
  对应 `contracts/scan-profiles.json` 的 `gate` profile 时限
  （`preToolUse.hardTimeoutMs = 1000`，`p95TargetMs = 300`）——扫描子进程在 Windows 上
  的启动+检测成本轻易越过该预算，于是同一 session 内后续文件批量 `ETIMEDOUT`。
  这两条是**同一条因果链**：门的结论依赖扫描子进程，而该子进程在本机不可用/超预算。

### 3.3 人工步骤（本循环**未执行**，属操作者环境变更）

```bash
# 1) 安装插件固定的 semgrep CE（会联网到 pypi.org；不修改系统 Python、不使用 sudo）
node <插件根>/payload/dist/cli.js semgrep install --accept-license
# 2) 复核状态
node <插件根>/payload/dist/cli.js semgrep status --json     # 期望 installed=true, healthy=true
# 3) 复核 L3 门：重跑 §3.1 的命令，期望不再是 scanner_no_output
```

**执行前须知的后果**（这也是本循环不擅自安装的原因）：L3 门默认
`MIMOSA_GIT_GATE_MODE=graded` —— **high 强制拒绝、medium 询问确认**。检测层一旦可用，
自动提交循环可能被 medium 级 finding 的**交互式确认**挡住；若确实要在无人值守下运行，
需显式设置 `MIMOSA_HOOK_FAILURE_MODE=strict`（更严）或经用户批准调整门模式，两者都是
**安全策略决定**，按本 GOAL 的 `escalation_triggers` 由用户拍板。

---

## 4. 干净 checkout 扫描的 25 条 findings 逐条处置

处置口径与上一轮一致：**结论 / 依据 / 处置**三段式；依据必须落到可重跑的检索或已执行的
用例；「看起来没问题」不构成处置。

### 4.1 HIGH ×1（产品代码）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| H-1 | `packages/application/protocol_authoring/service.py:103` | **误报** | 加载器是 `SafeLoader` 子类（`service.py:83`）；已执行用例 `tests/application/protocol_authoring/test_draft_service.py` **13 passed**，含「`python/object` tag 被拒绝且**不执行**」与「钩子类必须继承 `SafeLoader`」 | 不改代码；登记误报 |

### 4.2 LOW ×5（示例实验的固定 seed）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| L-1…L-5 | `examples/experiments/m12_reference_classification.py:33,42,64,69,142` | **误报** | `random.Random(seed=7)` 供 M12 参考实验的**确定性**合成数据与可复现基线，不参与密钥/令牌/访问判定（沿用 `PA1_MIMOSA_REVIEW.md` 同口径） | 不改代码（改 `secrets` 会破坏参考实验的字节级可复现契约） |

### 4.3 MEDIUM ×19（跨文件污点启发式）

| # | 位置 | 结论 | 依据 | 处置 |
| --- | --- | --- | --- | --- |
| M-1 | `services/worker/__main__.py:135` → 汇点 `adapters/execution/gpu_probe.py:138` | **误报** | 汇点是 `Path(tempfile.mkdtemp(prefix="researchos-gpu-probe-"))`（系统生成临时目录），不是 env 值；env `RESEARCHOS_WORKER_GPU_IMAGE` 进的是 docker 镜像引用；`tests/distributed/test_security_distributed.py` 断言该 env **不进沙箱子进程环境** | 不改代码 |
| M-2 | `tools/PA1R运行演练v1.py:56` → 汇点 `tests/adapters/execution/test_docker_backend_e2e.py:219` | **误报（新增签名）** | 该 `.execute(...)` 是 `DockerExecutionBackend.execute()`（**执行容器**，不是 SQL）；源侧是把 `OS_KEYS` 白名单过滤后的环境变量传给 `subprocess.run(shell=False)` | 不改代码；把该签名补进本文档（上一轮未出现） |
| M-3…M-19 | `tools/probes/probe_{cancel_race,canonical_state,db_failure,migration,outbox,scheduled_recovery,stale_worker}.py` 共 17 行 | **误报** | 同一条启发式：env → `adapters/postgres/db.py:202`（`def migrate(` 行）的 `.execute`。逐行核对：这些位置读的是 **DSN（连接目标）**，SQL 文本来自 `_MIGRATIONS_DIR` 下的仓库内 `*.sql` 文件与字面量 DDL/SELECT，唯一带参语句是 `%s` 参数化 INSERT | 不改代码 |

### 4.4 本轮的方法学更正（重要）

上一轮（RECHECK-091）用 **grep 形态检索**得出「产品树动态 SQL 零命中」。本轮改用
**AST 结构判据**（`tools/probes/probe_dynamic_sql_forms.py`）复核，结论需要**更正为**：

| 判据 | 结果 |
| --- | --- |
| AST 扫描 `packages/` `services/` `adapters/`（510 个 `.py`） | **22 处** `.execute(...)` 的首参由字符串构造（f-string / `+` / `%` / `.format`） |
| AST 扫描 `tools/`（33 个 `.py`） | 0 处 |

逐处核对这 22 处（`adapters/postgres/{eval_report_store,worker_registry,workflow_ops}.py`、
`adapters/sqlite/{eval_report_store,evidence_ledger,memory_store,schedule_store,tool_pack_store}.py`）：
拼接进去的**全部是模块级常量**（`_COLUMNS` / `_REGISTER_SQL` / `SOURCE_COLS` /
`EVIDENCE_COLS` / `_MEMORY_COLS`）、`eval_report_store` 内的**字面量 migration 字典**
（`{"rubric_digest": "TEXT", …}`），或 `db_time_expr()` 返回的**固定 SQL 记号**
（生产为 `now()`，注入时钟时为占位符 `%s` 并把时间值绑定为参数，见
`adapters/postgres/db.py:279-291`）。**外部取值一律走 `%s`/`?` 绑定** ⇒ 结论（安全）不变，
但**依据从「检索零命中」改为「22 处逐处结构核对」**——前者在本轮被证明是**覆盖不足**的
判据（grep 漏掉了 f-string 形态）。

判据有效性（反证）：探针自带 `--selftest`，用合成 AST 节点（不写任何危险源码文本）验证
分类器能**分离开**四种构造形态与三种良性形态，本轮 8/8 全 ok ⇒ 「产品树 22 处且逐处判安全」
不是死判据的空结果。

---

## 5. 未覆盖范围（必须在结论中同读）

1. **静态 only**：无运行时/动态验证；`validation.investigated = 0`。
2. **威胁建模与授权面零覆盖**：`threatModel` 0 入口 / 0 主体 / 0 授权面 ⇒ 越权、
   BOLA/BFLA、业务逻辑风险**不在本次审计射程**；`tests/**` 里的相关用例不能代表独立审计结论。
3. **依赖面**：本轮的结论来自**独立 OSV 查询**（§2），不是扫描器依赖阶段；
   扫描器自报两次互相矛盾（182/1 与 11/0），已知其覆盖不完整（11 ≪ 413）。
4. **hook 侧 L3 门仍是失败开放**：根因（`semgrep` 检测层缺失）已定位，但**修复动作
   （安装检测层 / 调整门模式）未在本循环执行**（环境变更 + 安全策略决定）。
5. **仓库外内容**：`artifacts/`（未跟踪，含明文 token 文件）与 `scratch/` 不再进入扫描输入，
   其内容**未被本轮覆盖**——这是**有意**的边界，不是遗漏；清理属操作者决策。
6. **`tools/probes/` 里的探针**：本轮 17 条 MEDIUM 落在这些**已跟踪的开发探针**上，
   按 §4.3 判为误报；它们是开发工具，不在产品运行路径上。

---

## 6. 结论

1. **干净 checkout 重扫成立**：输入 = 3025 个 tracked 文件（与 `git ls-files` 相等，无
   `scratch/`、无 `artifacts/`），封印
   `sha256:1e549272da4ebf65a87b02d195bf714ed3ef75b29b2db6d689331a617b51116d` 三件产物
   逐件复算 OK；剖面 high 1 / medium 19 / low 5 = **25**，与工作树扫描的 36 条的差异
   **恰好是那 19 条非仓库内容**（§1.3，判据有效性证据）。
2. **依赖 advisory 有了署名与结论**：413 个锁定包逐一查询，**3 包 20 条**
   （`undici@5.29.0` 12 条 / `vite@6.3.5` 7 条 / `yaml@2.8.1` 1 条），全部带 CVE 与修复
   版本，全部位于 **devDependency 链**（`@cursor/sdk` 传递、`apps/web` 直接声明）。
   **本轮不改依赖版本**——pin 变更命中 `escalation_triggers`，留用户/ADR 拍板。
   扫描器依赖阶段的两次自报（182/1、11/0）互相矛盾且覆盖不全，**不作为依据**。
3. **25 条 findings 逐条处置完毕**：1 HIGH + 5 LOW + 19 MEDIUM 全部为误报或开发工具
   （§4），**无产品代码真实缺陷需要修复**；但依据面被**更正**为 AST 结构判据（§4.4），
   grep 形态检索被证明是覆盖不足的判据。
4. **hook 侧根因已定位**：L3 门依赖的 semgrep 检测层**未安装**
   （`installed=false`、`reason=install_metadata_missing`、安装目录不存在），
   门因此失败开放并报 `scanner_no_output`（宿主显示 `scanner_enobufs`）；
   修复配方与后果见 §3.3，**待人工执行**。
5. **本记录不构成「项目安全」或「无已知漏洞」的断言**：未覆盖范围见 §5，
   依赖升级未做，授权面仍未覆盖。

---

## 7. 可复现配方（全部命令）

```bash
# （1）干净 checkout 重扫
git archive HEAD | tar -x -C <仓库外目录>
#    → 文件数应等于 `git ls-files | wc -l`
#    → MCP: security_scan_start(project=<该目录>, depth=deep)，轮询 security_scan_status 至 completed
#    → 产物：~/.mimosa/security-scans/<projectId>/<scanId>/（5 件）；三件摘要与 seal.json 对照应全 OK

# （2）依赖 advisory 联网复核
python tools/probes/probe_dependency_advisories.py --root . > batches.jsonl
curl -s -X POST https://api.osv.dev/v1/querybatch -H 'Content-Type: application/json' \
     --data @batch-1.json > response-1.json
python tools/probes/probe_dependency_advisories.py --root . --responses response-1.json

# （3）动态 SQL 结构判据（含自证）
python tools/probes/probe_dynamic_sql_forms.py --selftest
python tools/probes/probe_dynamic_sql_forms.py --root packages --root services --root adapters

# （4）hook 侧复现与根因
node <插件根>/payload/hooks/git-gate-hook.mjs   < <§3.1 的 payload>
node <插件根>/payload/dist/cli.js semgrep status --json
```
