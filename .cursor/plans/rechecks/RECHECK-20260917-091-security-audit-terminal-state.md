---
id: RECHECK-20260917-091
plan_id: PLAN-20260917-091
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle8
baseline_ref: 3a9b86c
checked_head: worktree
---

# RECHECK-20260917-091 — 完整安全审计的可复核终态（GOAL-004 cycle 8 = EC-07）

## 检查范围

PLAN-20260917-091 声称的交付面：EC-07 终态 **a**（扫描跑通 ⇒ findings 逐条处置 + 结论文本），
即 `docs/audits/MIMOSA_DEEP_SCAN_20260917.md` 的证据链、36 条处置表、结论段与未覆盖范围。
**不在本 PLAN**：运行时/动态渗透、威胁建模与业务逻辑审计（本扫描器的覆盖缺口，
已作为 U1/U2 写进记录）、依赖 advisory 的联网复核（U4）、`artifacts/` 与 `scratch/`
两个非仓库目录的内容治理（U3，只登记事实）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 扫描真的跑通（不是又一次 enobufs） | MCP `security_scan_start`（deep）→ `security_scan_status` 至 `completed`，读到 `scanId`/`seal`/`findingCount=36`；产物 5 件落盘于 `~/.mimosa/security-scans/project-c96f90c714f9f3dc0bd2d97f/scan-2026-09-17T20-05-18.700Z-663d0976701f/` | PASS |
| seal 可复核 | 逐件重算 sha256 与 `seal.json.artifacts` 三件对照 | PASS（三件全 `ok`）；聚合 digest 明确记为**不可由产物复算**（不宣称） |
| 结论可复现 | 同 projectId 连续 6 次深扫剖面逐次相同（3 / 28 / 5），`inconclusive` + `partial` 同口径；与 `docs/audits/PA1_MIMOSA_REVIEW.md` 两次记录同口径 | PASS |
| 36 条逐条处置 | 处置表 H-1…H-3、M-01…M-28、L-1…L-5 共 36 行，每行给出「结论 / 依据 / 处置」；依据块 E-1…E-6 逐条对应 | PASS |
| HIGH #1（产品代码）判误报有实测支撑 | `tests/application/protocol_authoring/test_draft_service.py` **13 passed**，含「python/object tag 被拒绝且**不执行**」与「钩子类必须继承 `SafeLoader`」；`service.py:83/99/101-103` 代码行核对 | PASS |
| HIGH #2/#3 判仓库外有 git 侧证据 | `git ls-files artifacts/` = **0**；`git check-ignore -v artifacts/` → `.gitignore:36`；`git log --all -- "*本地_v12.local.yaml"` = 空 | PASS |
| 27 条 MEDIUM 判误报的检索**有判别力** | 全量动态 SQL 形态检索在产品树零命中；同一模式对**蓄意**四形态样本（f-string / `+` / `%` / `.format`）命中、对参数化写法不命中 | PASS |
| 汇点代码事实 | `adapters/postgres/db.py` 五处 execute 逐行核对：迁移文件文本 + 字面量 DDL/SELECT + `%s` 参数化 INSERT；env 读取只在 `resolve_dsn()` | PASS |
| M-28 判误报有实测支撑 | `tests/distributed/test_security_distributed.py::test_worker_child_env_holds_zero_db_credentials` + `::test_secret_enumeration_surface_is_zero` **2 passed**；汇点 = `tempfile.mkdtemp` | PASS |
| 未覆盖范围写明 | 记录 §5/§6：静态-only 边界、threatModel 0 入口/0 主体/0 授权面、业务逻辑候选 0、validation investigated 0、依赖 advisory 未署名未决、扫描输入含 gitignored 目录、hook 侧 enobufs 仍在 | PASS |
| 不宣称「项目安全」 | 记录开头即声明；§4 结论第 5 条与 §6 同读要求 | PASS |
| 无产品代码变更 | 本 cycle 提交只新增/修改文档与 `.cursor/**` 记录 | PASS |

## 反证与实测

- **反证（检索判别力）**：把四种蓄意动态 SQL 形态喂给同一条模式 ⇒ **四行全命中**，
  参数化写法不命中 ⇒ 产品树空结果**不是**因为模式写错（若模式退化，反证会先红）。
- **旁证（写路径受检）**：本轮尝试经 Bash 把上述反证样本**写进仓库**，被 Mimosa 写路径
  检查拦下（要求改走 Write/Edit 通道）⇒ 写路径守卫本身在工作，且与扫描结论无关，已如实
  记入记录 §3 E-1 附注。
- **未做的验证**：没有为"证明判据有效"而**注入**真实缺陷到产品代码；本 EC 的判据是
  文档 + 证据，不涉及产品行为断言，故无「改产品 ⇒ 用例变红」型反证。

## 告警（W）

- **W-1 依赖 advisory 仍未决**：密封产物只给「1 包命中 1 条」，`packages` 数组为空 ⇒
  无法定位是哪个包；联网复核超出本机可验证范围。**不得读作「无已知漏洞」**。
- **W-2 hook 侧 `scanner_enobufs` 未被消除**：commit hook 的扫描通道本轮依旧无结论
  （逐 cycle 现象在 `scratch/goal4-mimosa-enobufs.md`）；独立密封深扫是替代通道，
  两者不互相抵消。
- **W-3 扫描输入含非仓库内容**：`scratch/`（17 条）与 `artifacts/`（2 条 HIGH）合计
  19/36 条 findings 落在 `.gitignore` 覆盖的工作树内容上 ⇒ 处置表口径必须与"仓库内容"
  区分（记录已区分），后续扫描若要"只看仓库"，需在干净 checkout 上重跑。
- **W-4 `artifacts/` 内含明文 token 文件**（未跟踪、从未提交）：本轮只登记事实、不清理
  （清理属操作者决策，且不在 EC 判据内）。
- **W-5 威胁建模/授权面零覆盖**：越权、BOLA/BFLA、业务逻辑风险不在本次审计射程；
  `tests/distributed/` 等产品测试提供的对应证据**不能**代表独立审计结论。

## 结论

EC-07 的终态 **a** 成立：扫描完整跑通（sealed）、36 条 findings 逐条处置（35 条误报/仓库外
+ 1 条产品代码误报，无产品代码真实缺陷需修）、结论段与未覆盖范围同读。**不主张项目安全**；
W-1…W-5 作为诚实边界保留，其中 W-1/W-2 需人工或联网环境才能推进。
