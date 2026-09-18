---
id: MEM-20260918-067
title: "审计残留的三条可复核终态：advisory 要署名、干净 checkout 用导出树、hook enobufs 根因是检测层缺失"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-093-security-audit-residual-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-093-security-audit-residual-recheck.md
supersedes: []
tags:
  - security-audit
  - dependency-advisory
  - mimosa
  - scanner-enobufs
  - false-positive-disposition
  - evidence
---

# 审计残留：可复核终态怎么写

## 做了什么

GOAL-005 cycle 1（EC-01）把 GOAL-004 收口时登记的三条审计残留做成终态，全程
**无产品代码变更**：

1. **依赖 advisory 联网署名**：写 `tools/probes/probe_dependency_advisories.py`（**不含网络
   代码**——只读 lockfile、构造 OSV payload、合并响应；出网由操作者 `curl` 完成）。
   413 个锁定包（PyPI 149 + npm 264）⇒ **3 包 20 条**：`undici@5.29.0`（12，来源
   `@cursor/sdk@1.0.30` 的传递依赖）、`vite@6.3.5`（7）、`yaml@2.8.1`（1），全部在
   **devDependency 链**（`apps/web` 运行依赖只有 react/react-dom），全部带 CVE 与
   `fixedVersions`。证据：`docs/audits/MIMOSA_DEPENDENCY_ADVISORIES_20260918.json`。
2. **干净 checkout 重扫**：`git archive HEAD | tar -x -C <仓库外目录>` ⇒ 3025 文件 ==
   `git ls-files` 3025；新封印 `sha256:1e549272…`，剖面 **25**（1/19/5），三件产物摘要
   逐件 OK。工作树扫描 36 条里 **19 条**（`artifacts/` 2 HIGH + `scratch/` 17 MEDIUM）
   在干净输入上归零。
3. **hook 侧 `scanner_enobufs` 根因**：手工喂 `git commit` 的 PreToolUse payload 给
   `git-gate-hook.mjs`，2/2 次逐字输出 `INCONCLUSIVE（scanner_no_output）`（790/767 ms）；
   `cli.js semgrep status --json` ⇒ `installed:false` / `reason:install_metadata_missing`，
   `~/.zcode/mimosa-runtime/semgrep-1.136.0` 不存在 ⇒ **L3 门的检测层没装**，扫描器无输出，
   门按 `open` 失败开放。宿主会话里显示的 `scanner_enobufs` 就是它。

## 为什么这样做

- **「未署名」的命中既不能确认也不能否认**：上一轮只拿到「1 包 1 条」而 `packages` 为空。
  要把它变成结论，只能自己按 lockfile 逐包查询，并记录 lockfile digest + 查询命令 +
  每条 advisory 的 CVE/CVSS/修复版本——否则就是拿一句话换一句话。
- **扫描器的依赖阶段不能当依据**：同一份 lockfile，扫描器两次自报
  `182 包/1 条（未署名）`（工作树）与 `11 包/0 条`（干净 checkout），而独立查询是
  413 包/3 包 20 条 ⇒ 自报覆盖不全且互相矛盾，只能作为辅助信号。
- **扫描输入边界会改变结论**：19 条 findings 的差异证明「未覆盖范围」不是套话；
  判据必须是可查事实（导出文件数 == `git ls-files` 条数、树内无 `scratch/`/`artifacts/`），
  不是「清干净了再扫」的口头描述。
- **写路径守卫拦 Bash 直写源码**：本轮想用 heredoc 造反证样本（含 f-string SQL 的 `.py`）
  被拦下——这是**产品能力在工作**，不是障碍；改用合成 AST 节点做自证，反而更强。

## 怎么做与复现

```bash
# （1）干净 checkout：判据 = 导出文件数 == git ls-files 条数，且树内无 scratch//artifacts/
git archive HEAD | tar -x -C <仓库外目录>
#     → MCP security_scan_start(project=<该目录>, depth=deep) → security_scan_status 轮询至 completed
#     → 三件产物 sha256 与 seal.json.artifacts 逐件对照（应全 OK）

# （2）依赖 advisory：探针不含网络代码，出网只有这一条 curl
python tools/probes/probe_dependency_advisories.py --root . > batches.jsonl
curl -s -X POST https://api.osv.dev/v1/querybatch -H 'Content-Type: application/json' \
     --data @batch-1.json > response-1.json
python tools/probes/probe_dependency_advisories.py --root . --responses response-1.json

# （3）动态 SQL 结构判据（自带反证，不写危险源码文本）
python tools/probes/probe_dynamic_sql_forms.py --selftest
python tools/probes/probe_dynamic_sql_forms.py --root packages --root services --root adapters

# （4）hook 侧复现与根因
cat > payload.json <<'EOF'
{"hook_event_name":"PreToolUse","session_id":"sess_probe","cwd":"<repo>","tool_name":"Bash",
 "tool_input":{"command":"git commit -m probe"}}
EOF
node <插件根>/payload/hooks/git-gate-hook.mjs < payload.json
node <插件根>/payload/dist/cli.js semgrep status --json
```

## 适用边界（踩过的坑）

- **grep 形态检索是覆盖不足的判据**：本轮改用 AST 才发现产品树有 **22 处** `.execute()`
  首参由字符串构造（上一轮 grep 说「零命中」）。逐处核对后结论未变（拼接进去的是模块常量
  与固定 `now()`/`%s` 记号，取值全部参数绑定），但**依据被更正**；
  引用 RECHECK-091 该条时应以本轮记录为准。
- **AST 探针的自证不能靠"注入真实缺陷"**：写路径守卫不允许把危险源码写进仓库；
  用 `ast` 手工构造节点做 `--selftest`（8/8 ok）同样能证明分类器非空转。
- **本机解析器把公网域名映射到保留段**（`api.osv.dev` → `198.18.0.4`，fake-IP/代理）：
  「解析后拒绝私有/保留地址」的校验在本机**会拒绝真实公网请求**。这类校验属产品代码口径；
  开发者侧的一次性复核走显式 `curl` 步骤更诚实（也避免把校验削弱成摆设）。
- **hook 侧是失败开放且修与不修都是策略决定**：`graded` 模式 high 拒绝 / medium **询问
  确认**——装上检测层后，无人值守提交可能被交互式确认挡住 ⇒ 修复动作留人工。
- **依赖升级未做**：3 包 20 条全部有修复版本，但版本变更属上游 pin 变更（escalation），
  本循环只交付署名与影响面判定。**不得**读作「依赖面无风险」。
- 相关：[[MEM-20260917-066]]（同主题的上一轮终态与诚实边界）、
  [[MEM-20260915-047]]（声明要有消费者 / 证据口径）。

## 来源

- PLAN-20260918-093 / RECHECK-20260918-093（GOAL-20260918-005 cycle 1 = EC-01）。
- 上游：`docs/audits/MIMOSA_DEEP_SCAN_20260917.md`（GOAL-004 EC-07）与 RECHECK-091 的
  W-1…W-5；本轮记录 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md`。
