---
id: GOAL-20260925-015
slug: gate-trustworthiness
title: 质量门可信度：跨套件隔离归零 + 本地判定确定性 + 待拍板决策简报
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-25 用户会话指令（goal 模式）：**建档 GOAL-20260925-015（质量门可信度）并授权本驱动
    自动化循环推进、无需逐轮确认**。authorization 原文要点如下：
    (1) **授权范围（本 GOAL 能自动循环的前提）**：用户**授权修测试隔离与本地判定确定性**
    —— 即 a) 消除「同一套件组合合并跑红、单独跑绿」的**跨套件顺序依赖**（根因若是共享状态：
    连接 / 环境变量 / DB / Docker 残留，按既有教训修**真实来源**：每线程连接、夹具隔离、
    显式 DSN 固化、容器清理）；b) 让「本地 m0 为什么不是 23/23」成为**机械可判**的事实
    （产出并落地**本地跑法协议**：canonical 的 m0 调用方式、DSN 固化、工作树前置条件、
    外部文件存在性处理）。**前提是「不改判据强度、不放宽门禁」**。
    (2) **明确禁止（触及即 BLOCKED）**：
    a) 为消灭本地红而**放宽任何判据 / 门禁 / 放行面**（含 `tests/egress_guard.py` 的
    **目的地判定**、`framework/validate_bundle` 的**检查项**、m0 任一 check 的**阈值**）；
    b) **不得**改 `tests/application/test_m2_audit.py` 的**镜像一致性判据**；
    c) **不得**用 `skip` / `xfail` / 删除测试 / 调整收集顺序掩盖顺序失败；
    d) 为让某个红项消失而豁免 fake-IP 网段（`198.18.0.0/15`）或任何目的地址类别。
    (3) **门禁 scoping 的分界**：若某红项的根因判定为「**门禁本身的 scoping 有误**」
    （例如扫描了不属于仓库的文件）⇒ **不在本循环改门禁**，改为产出**决策简报条目（EC-03）**。
    这一条同时是 EC-02 的第三分类出口。
    (4) **push-to-main-for-CI 授权**：只推 `main`、**不 force**、**不重写历史**、**不推旁支**
    触发 CI；push 前 `git pull --ff-only origin main`。循环预算与纪律以本文件 frontmatter 为准
    （客户端自带的迭代 / 重试 / 超时上限**一律让位于**此）。
    (5) **默认姿态不变**：默认 runtime 保持 **Fake**、默认 CI **离线**（AGENTS.md §11）。
    **本 GOAL 不做任何真实出网调用**（不需要 `.env` 凭据；若某判据需要真实端点出网，
    则该判据**不属于本目标**，如实登记为下一轮输入）。默认门出现非环回目的即判红是
    **正确行为**：本 GOAL 只做**归因与登记**，不动判据。
    (6) **EC 设计口径（各成一条可独立验收、独立 RECHECK 的 EC）**：
    ① **跨套件隔离（主干）**：普查（已知签名 + m0 全量实跑红项，每个红给可复现最小命令）
    → 逐条根因与修法 → **同一套件组合连续两轮全绿** + **反证**（把修前的顺序 / 组合重新
    构造出来 ⇒ 仍能红）；② **本地判定的确定性**：本地跑法协议使每个红**自动归入三类**
    （真实缺陷 / 环境专属 / 门禁 scoping）；具名起点 = `R-F3`（仓库外 gitignored 文件致
    `framework/validate_bundle` 红）与**本机 fake-IP DNS 致 `tests/egress_guard.py` 判红
    两条探针**（**判据正确，机器环境特殊**）；「as-is 本地全绿」若不可达则如实写明
    **支持的跑法**与**不支持的跑法**，并把 GOAL-013 的「临时移出 → 跑 → 移回 +
    `sha256`/`size`/`mtime` 复核」动作**文档化并脚本化**；③ **决策简报（只产出文档、
    零实施动作）**，覆盖 `M-1` / 读类能力预放行 / `R-D1` / hook 侧 L3 门 / 450 行贴线 /
    路径 (B) 的 5 条重设计项 / ADR-0031 / `ModelCompatibilityProfile` / `R-N1` 等；
    ④ **收口复检 + 残余登记**。
    (7) **文档与门禁纪律**：不新增依赖、不改上游 pin、不动 Accepted ADR / 核心安全策略 /
    Canonical State 边界、不把真实 runtime 设为默认、`git add -A` 明文禁止、伪造或夸大
    验证证据明文禁止、**未实跑不得记 PASS**（本机无法验证记 PENDING 并停止推进）。
    (8) **承继边界**：GOAL-001…014 全部**只读**（003 / 011 BLOCKED，其余 ACHIEVED）；
    如需指名只允许按**只追加**补一行事实更正。GOAL-014 的 13 条人工面与全部承继残余
    **原样保留**；**EC-03 的产出是「让这些项可被拍板」，不是「把它们解决了」**。
objective: >
    让「本地质量门的结论」重新可信：**同一批套件、同一台机器、同样的调用方式，结论不再随
    顺序或环境漂移**。具体三件事——(1) 把「合并跑红、单独跑绿」的**跨套件顺序依赖归零**
    （普查 → 逐条根因 → 修**真实共享来源**，绝不用 skip/xfail/改收集顺序掩盖），并给出
    **成对反证**证明修的是根因而非把用例挪开；(2) 落一份**本地跑法协议**，使每一次本地红
    都能**机械归入三类**之一（真实缺陷 ⇒ 修代码 / 环境专属 ⇒ 附可复现命令 + 干净基线对照
    证据、登记为环境项**而不动判据** / 门禁 scoping 问题 ⇒ 只登记、进决策简报），
    从而把「本地 m0 为什么不是 23/23」从每轮现场归因变成可复跑的事实；(3) 把散在各 GOAL
    的**待拍板项收成一份可拍板的决策简报**（每项：要决定什么 / 选项 / 每选项影响面与代价 /
    证据出处 / 不做会怎样 / 建议）——**只产出文档，零实施动作**。
    **硬约束**：不放宽任何判据 / 门禁 / 放行面 / 阈值；不改 `test_m2_audit.py` 的镜像一致性
    判据；不新增依赖、不改上游 pin；不动 Accepted ADR / 核心安全策略 / Canonical State 边界；
    默认 runtime 仍为 Fake、默认 CI 仍离线；**本 GOAL 零真实出网调用**。
exit_criteria:
  - id: EC-01
    criterion: >-
      **跨套件隔离（主干）**：把「合并跑红、单独跑绿」的顺序依赖**归零**。
      三步：① **普查**——把已知签名 + 用**既有 m0 全量配方**跑一遍的实际红项一起列出，
      每个红给一条**可复现最小命令**（含 DSN / 前置条件）；② 对每条给出**根因与修法**
      （根因是共享状态则修真实来源：每线程连接 / 夹具隔离 / 显式 DSN 固化 / 容器与 DB 残留
      清理）；③ **判据**：**同一套件组合连续两轮全绿**，且**反证**——把修前的顺序 / 组合
      重新构造出来 ⇒ **仍能红**（证明修的是根因，不是把用例挪开了）。
      **已知起点（不限于）**：`test_worker_plane_composition`×3 + `test_pg_crash_restart`
      合并跑红、单独跑 7 passed；postgres 标记的用例只在加载 `tests/postgres/conftest` 时
      才 skip（**定向跑会失败而非跳过**）；历史同类（GOAL-007 已修过一例：函数内定义 SDK
      Action 子类污染判别联合 ⇒ 提为模块级）。
      **禁止**：skip / xfail / 删除测试 / 调整收集顺序掩盖；放宽任何判据或阈值。
    verify: >-
      离线判据（默认门可跑、零出网）：① 普查表落仓库文档（红项 / 最小复现命令 / 根因 /
      修法 / 终态），每条可复跑；② 修后**同一套件组合连续两轮**全绿（两轮输出都留档，
      命令逐字相同）；③ **成对反证**：以最小改动把修前顺序 / 组合重新构造成可复现的最小
      命令 ⇒ 判红，且判词与普查登记的失败签名**逐字对应**；撤销构造后 `git diff` 为空。
    status: PASS
    status_note: >-
      2026-09-25 cycle 1 收口（`PLAN-20260925-161` → **DONE**；复检
      `RECHECK-20260925-163` = **PASS_WITH_WARNINGS**；工程记忆 `MEM-20260925-130` / `-131`）。
      **普查（先于修）**：as-is 本机 m0 = **21/23**，两条未绿项拆成**四个红项**，表落
      `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`：**R-1** 草稿列表序 tie
      （`test_list_orders_by_recency_and_filters_project`；**最小复现**
      `pytest tests/contracts/test_protocol_draft_store_order_tie.py -q` ⇒ 修前 **3 failed in 0.34s**，
      三实现全红；根因 = `ORDER BY created_at DESC, draft_id`（**升序** tie-break）与「按新近」
      相反 + InMemory 稳定排序退化为插入序）；**R-2** 默认门凭据泄漏（**最小复现**
      `LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q` ⇒ 修前 `blocked 2` + 整轮红，
      **2.24s** 取代 569s；根因 = `litellm/__init__.py:27` 导入期 `load_dotenv()` 把 gitignored
      `.env` 的凭据键注入进程环境 ⇒ `preflight_support.py:92` 凭据可解析 ⇒ 真的探出厂端点）；
      **R-3** `framework/validate_bundle`（= 环境型残余 `R-F3`，仓库外并发写者文件，实测仍在
      `69944` B / `sha256:7af32093…`；分类 **(iii) 门禁 scoping** ⇒ **只登记**，进 EC-03）；
      **R-4** postgres 标记的跳过只在收集到 `tests/postgres` 时生效（定向跑在 PG 不可达时
      **挂死**：120s 无输出 / exit 143；同文件 + 收集 `tests/postgres` ⇒ `16 passed, 93 skipped
      in 4.22s`）⇒ **(i) 真实缺陷**，实施登记去 cycle 2。
      **修法（真实来源，判据一字未动）**：① 三实现 tie-break 与新近一致（`draft_id DESC` /
      排序键 `(created_at, draft_id)` 反序）；② 新增 `tests/default_gate_credentials.py` +
      `tests/conftest.py` autouse 夹具（未标记 `requires_live_llm` 的用例隐藏出厂目录声明的
      凭据键）+ 双向对齐判据（含子进程按压）。
      **判据先红后绿**：R-1 `3 failed` → `12 passed`；R-2 `blocked 2`（exit 1）→ `blocked 0`
      / `16 passed`。
      **AC-4 连续两轮全绿**（同一组合命令、DSN 固化）：`4455 passed, 19 skipped` ×2
      （`egress guard: FAIL` 计数 **0**；阻断只来自判据自身探针）；对照修前
      `1 failed, 4445 passed …` + `blocked 10` ⇒ **两条红项归零**。
      **成对反证**：`git stash push -- <四显式路径>` 重建修前状态 ⇒ R-1 判据 `3 failed`、
      R-2 按压 `egress guard: FAIL … blocked 2`；`git stash pop` 后 `sha256sum -c` **四行全
      `OK`**（`f7b4eb0c…` / `ac6ac960…` / `c3ee0307…` / `148ac42c…`）。
      **用例数归因**：`4446 → 4455` = **+9、零删除**（+6 新判据逐 ID、+3 规模门禁对新增 `.py`
      的参数化）。
      **一轮如实登记的返工**：首次 8 分钟跑判红 `test_real_repo_is_clean`（本 cycle 新增文档里
      backtick 引用 `tests/postgres/conftest` 缺 `.py`）⇒ 修正后重跑，两轮全绿取自修正后的树；
      **另一次**：首次全量 m0 判红 `framework/validate`（本 cycle 的 MEM 条目缺章节/未入 INDEX）
      ⇒ 补齐后重跑取终态。
      **残余（不隐藏）**：`R-3` 未消 ⇒ as-is 本地 m0 **不是** 23/23（按授权只登记不改门禁）；
      `R-4` 只普查未实施（排 cycle 2）。
      **本 cycle 零真实出网调用**；未动 `tests/egress_guard.py` / `framework/validate_bundle` /
      `tests/application/test_m2_audit.py` / m0 阈值 / 快照。
  - id: EC-02
    criterion: >-
      **本地判定的确定性**：产出并落地一份**本地跑法协议**（canonical 的 m0 调用方式，
      含 DSN 固化、工作树前置条件、外部文件的存在性处理），使每一次本地红都能**机械归入**
      三类之一：**(i) 真实缺陷**（⇒ 修代码）、**(ii) 环境专属**（⇒ 附可复现命令 +
      与**干净基线树**的对照证据，登记为环境项、**不改判据**）、**(iii) 门禁 scoping 问题**
      （⇒ **只登记**，进 EC-03 的决策简报）。
      **两个具名起点**（各须拿到**唯一终态** + 一条**可复跑的归因命令**）：
      a) `R-F3`｜仓库外 gitignored 文件致 `framework/validate_bundle` 红
      （并发写者的在制品，governance 面不属本 GOAL 处置）；b) 本机 fake-IP DNS 致
      `tests/egress_guard.py` 判红**两条探针**（**判据正确、机器环境特殊**——
      **不得**为了变绿而豁免 fake-IP 段或任何目的地址类别）。
      **判据**：「as-is 本地全绿」若不可达，则**如实写明支持的跑法与不支持的跑法**，
      并保证 GOAL-013 那个「临时移出 → 跑 → 移回 + `sha256`/`size`/`mtime` 复核」的动作
      被**文档化并脚本化**（可复跑、零出网、只读外部文件）。
    verify: >-
      `docs/architecture/LOCAL_GATE_PROTOCOL.md`（跑法协议 + 三分类判定条件 + 归因命令）
      + 只读归因脚本（标准库、不 import 仓库代码、零出网）；两条具名起点各一条可复跑命令
      与唯一终态；m0 到**可支持的终态行**（支持 as-is 则 `PASS: profile=m0; 23 deterministic
      checks`；不支持则如实给出「代管后可达」的终态行 + 脚本 + 逐字节复核记录）。
    status: PENDING
  - id: EC-03
    criterion: >-
      **决策简报（只产出文档，不实施）**：把散在各 GOAL 的待拍板项收成一份**可拍板**的
      简报，每项含**六要素**：**要决定什么 / 选项 / 每选项的影响面与代价 / 证据出处 /
      不做会怎样 / 建议**。**必须覆盖（不限于）**：① `M-1`（出厂组合根是否自己接执行体缝
      `ApiDeps.tool_providers`，现状生产为空 dict、由装配方补执行体）；② **读类能力是否
      全局预放行**（承「`W-A` 之外的策略面放宽」与 EC-03 差集表里「该放行」的条目）；
      ③ `R-D1` 依赖 pin 升级（承 GOAL-014 现测 23 条告警 / 4 high，含 `undici`/`vite`/`yaml`）；
      ④ hook 侧 L3 门；⑤ 450 行贴线文件（建档当日实测**四个正好 450 行**）；⑥ 路径 (B) 的
      5 条重设计项；⑦ ADR-0031（`tool_pack.*`）；⑧ `ModelCompatibilityProfile` 是否一等域实体；
      ⑨ `R-N1` 非 ASCII 路径豁免是否需 ADR。
      **判据**：覆盖齐（≥ 九项且每项非空壳）、每项**六要素**非空、**零实施动作**
      （文档之外不产生任何代码 / 配置 / 门禁改动）；该文档是**给用户的决策入口**，
      **不是待办清单**（不得读成「已排期」）。
    verify: >-
      仓库文档（每项六要素可核对 + 证据出处逐条可点）+ 一条**离线一致性判据**
      （简报项与「不进入循环 / 需人工拍板」节的条目**双向对齐**；按压：删一项 ⇒ 判红）；
      `git diff --stat` 证明本 EC **零实施动作**（只增文档 + 判据 + 记录）。
    status: PENDING
  - id: EC-04
    criterion: >-
      **收口复检 + 残余登记**：① **独立复检脚本**（只读、标准库、**不 import 仓库代码**）
      在**当前树**与**干净 checkout** 两处**同判据同结论**；② 本地 m0 到**可支持的终态行**
      （口径见 EC-02，**不得**把「代管后 23/23」写成「本机一直 23/23」）；③ 治理
      `validate.py` **绿**；④ **CI 台账到终态**（M0 六 job + CodeQL，逐 run 逐 job 实查，
      记 run id / 链接）；⑤ **13 条人工面与全部承继残余原样保留**（逐条登记、不隐藏）
      + 本 GOAL 的 `W` 列表 + 新增残余；⑥ 收口 RECHECK 的 `result` = `PASS` 或
      `PASS_WITH_WARNINGS`，且本文件 `latest_recheck` 为**仓库相对路径**。
      **判据**：复检脚本两树**同结论**（差异项只允许是「收口记录尚未落盘」这类时序项，
      落盘后归零，或**已具名**的环境差异）；m0 终态行**逐字**匹配登记口径；
      CI 台账**无未记账 run**。
    verify: >-
      `python .cursor/skills/governance-check/scripts/validate.py` ⇒ 治理验证通过；
      `make validate-all` ⇒ 终态行（脚本化后由 EC-02 的归因脚本给出分类与终态口径）；
      `scratch/verify_goal015_c<n>.py` 两棵树成对输出；CI 台账按
      `scratch/poll_ci_all.sh <sha>` 取 M0 六 job + CodeQL 的真实终态。
    status: PENDING
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据使其通过
    - 放宽 `tests/egress_guard.py` 的目的地判定 / 豁免 fake-IP（`198.18.0.0/15`）或任何目的地址类别
    - 放宽 `framework/validate_bundle`（governance-check）的检查项或扫描范围
    - 放宽 m0 任一 check 的阈值（含 450 行 / 50 行规模门禁）
    - skip/删除测试、加 xfail、或调整收集顺序以掩盖顺序依赖
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
    - 为跑通而放宽出站判据（`tests/egress_guard.py` / 放行面 / `network_domains` 声明）
    - 新增依赖或改上游 pin（用现有依赖实现；解析类需求优先标准库）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的解析/传输库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - >-
    放宽任一判据 / 门禁 / 放行面 / 阈值（含 `tests/egress_guard.py` 的目的地判定、
    `framework/validate_bundle` 的检查项、m0 任一 check 的阈值）—— **立即 BLOCKED**
  - 改 `tests/application/test_m2_audit.py` 的镜像一致性判据 —— **立即 BLOCKED**
  - >-
    以 skip / xfail / 删除测试 / 调整收集顺序的方式让顺序失败「消失」—— **立即 BLOCKED**
  - 把真实 runtime 设为**默认**（默认必须仍是 Fake；只做「显式配置才启用」）—— **立即 BLOCKED**
  - 本 GOAL 出现真实出网调用（本 GOAL 零出网；需要真实端点的判据不属于本目标）
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）—— 上游 pin 变更，需用户或 ADR 拍板
  - 威胁建模/授权面（BOLA/BFLA）覆盖类决策——需用户或 ADR 拍板，本循环不得自行决定
  - ADR-0031（`tool_pack.*`，Status: Proposed）是否采纳——归用户
  - >-
    路径 (B) 的「重新设计需要什么」（`docs/roadmap/PATH_B_REFUTATION_RECORD.md` 的 5 条）
    被判定需要重启时——**需拍板**，本循环不自行重启该路线
  - >-
    读类能力是否**成类预放行**（承 GOAL-014 EC-03 的唯一需拍板项）——本循环**只登记不扩大**，
    触及即 BLOCKED
  - 明文凭据泄露（**即使是可弃用的免费额度**）——立即停止并报告
child_plans:
  - .cursor/plans/tasks/PLAN-20260925-161-cross-suite-isolation-census-and-fix.md
latest_recheck: null
memory_entries: []
---

## 目标与退出标准

**一句话**：让「本地质量门的结论」重新可信 —— 同一批套件、同一台机器、同样的调用方式，
结论不再随**顺序**或**环境**漂移。

本 GOAL 的承继起点（事实，不是待办）：

- **跨套件顺序失败签名**（`W-D`，GOAL-012 cycle 1 登记；GOAL-013 / 014 原样承继）：
  4 条失败（`test_worker_plane_composition`×3 + `test_pg_crash_restart`）在**合并跑**里出现、
  **单独跑全绿**；与当时改动无关，前序 GOAL 均未处置。
- **环境型残余 `R-F3`**（GOAL-013 cycle 4 实测）：本机 m0 的 `framework/validate_bundle`
  会被**仓库外**并发写者的 gitignored `scratch/self-governance-bootstrap-prompt.md`
  （**建档当日实测仍在**：`69944` B、
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）判红
  —— 正文里的正则字面量被纯文本链接扫描读成本地链接。成对归因：同一脚本换
  `CURSOR_FRAMEWORK_ROOT`，主树 `exit 1`（只此一条）、干净 worktree（无 `scratch/`）
  `exit 0` 全绿；CI 检出无 `scratch/` ⇒ CI 不受影响。
- **本机 fake-IP DNS 致 `tests/egress_guard.py` 判红**（承 MEM `local-m0-egress-guard-fake-ip-red`
  与 `live-run-enablement-recipe`）：本机 DNS 走 fake-IP 代理（`198.18.0.0/15`）⇒ 自写
  「地址须全球单播」类检查会拒绝**所有**域名出网，含产品端点域名。**判据正确、机器环境特殊**
  —— 处置只能是**归因 + 登记**，**不得**豁免该网段。
- **已知同类历史修法**（`MEM` 既有教训，本 GOAL 按此口径修真实来源）：每线程连接
  （`psycopg-shared-connection-thread-nesting`）、夹具隔离、显式 DSN 固化、容器清理；
  GOAL-007 修过一例「函数内定义 SDK Action 子类污染判别联合 ⇒ 提为模块级」。

| EC | 标准（简） | 主要交付物 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 跨套件顺序依赖**归零** + 成对反证 | 普查表 + 修法 + 两轮全绿 + 反证 | PENDING |
| EC-02 | 本地判定**机械三分类** | 跑法协议 + 归因脚本 + 两条具名起点终态 | PENDING |
| EC-03 | 决策简报（**零实施**） | 六要素简报 + 一致性判据 | PENDING |
| EC-04 | 收口复检 + 残余登记 | 复检脚本两树 + m0 终态行 + CI 台账 | PENDING |

**依赖关系**：EC-01 与 EC-02 共用同一批「普查 / 归因」证据面（普查表先行）；
EC-03 消费 EC-01/EC-02 判出的「门禁 scoping」类条目（若有）；EC-04 在任何 EC 之后。

**预算**：`max_cycles: 20`、`per_cycle_minutes: 120`（软）、`no_progress_stop_cycles: 2`。
**本 GOAL 零真实出网调用**（无 live 步骤）：若某判据需要真实端点 ⇒ 该判据不属于本目标，
如实登记为下一轮输入。

## 循环入口协议

驱动方（会话 / 定时自动化 / 客户端 goal 模式）进入时，按**迭代日志最后一行** +
**工作树 / 远端实况**判定续点；**禁止凭记忆假设上一轮状态**：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①（先 derive 子 PLAN）。
2. 有子 PLAN 但仍在 `IN_PROGRESS` → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待 / 判定），**禁止猜测绿**。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit + CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后**立即回写本文件**（状态历史 / 迭代日志），保证任意时刻崩溃后重入可续。
同时只允许一个驱动持有 ACTIVE cycle 的推进权。

**每轮只读入口必需的最小集**（`per_cycle_minutes=120` 是硬预算）：本文件 + 当前子 PLAN +
其引用的判据 / 证据；不整目录通读。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 带 `parent_goal: GOAL-20260925-015`
  并投影 `ALL_PLAN`，**同一提交**）。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，**显式路径**）。
- **③ 本地验证**：先自查**规模门禁**（50 行函数 / 450 行文件 —— 建档当日实测**四个文件
  正好 450 行零余量**：`services/api/composition.py`、`adapters/postgres/workflow_engine.py`、
  `adapters/execution/docker_backend.py`、`packages/application/run_orchestration/service.py`
  ⇒ 改动它们**必须先搬代码**）与**快照类门禁**（OpenAPI / 设计基线），再跑
  `make validate-all`（m0 全量 23 项，**独占运行**，避免 `evolution_state.json` 的
  `WinError 5`）+ 受影响定向套件 + web 门；**默认门一律离线**（`tests/egress_guard.py`
  是结构判据：默认门出现非环回目的即判红 —— **不得为本地变绿而放宽它**）。
  **本地不绿不得 push**（承 `MEM-20260924-125`：先等本地门到终态再推送）。
- **④ commit**：显式路径；**绝不 `git add -A`**（并发工作树）。
- **⑤ push + CI**：`git pull --ff-only origin main` → `git push origin main`（只推 main）→
  轮询 CI 到终态（`scratch/poll_ci_all.sh <sha>`：M0 六 job + CodeQL），记录 run id / 链接 /
  逐 job 结论；**本机无法验证记 PENDING 并停止推进**。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；超 `fix_policy` 或命中 `escalation_triggers`
  ⇒ `status: BLOCKED`。
- **⑦ 回写**：EC / 迭代日志 / `child_plans` / `latest_recheck` / 状态历史；
  **收尾前必须回写**；`child_plans` 与 `memory_entries` 每轮与实际派生对齐。
  **记录自洽**：新增 MEM/RECHECK 引用时确保被引用文件在**同一提交**内。

**撤回纪律**（承 GOAL-011…014）：改共享夹具 / 契约时先数清谁拿它的**失败形态**当夹具
（既有教训：「补全被复用的参考资产 = 改它的失败形态」）；CI 判红且根因是夹具语义冲突 ⇒
**优先撤回载体改动**，不改那批夹具迁就；撤回复核用逐字节 `git diff` 证明。
**本地假绿**：`...` 形式链接在 Win32 会剥尾点 ⇒ 涉及路径 / 链接的判据必须在 **Linux 侧**
（CI）复验。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，禁改断言迁就 |
| **顺序依赖（本 GOAL 主战场）** | 「合并跑红、单独跑绿」 | 按 EC-01 口径修**真实共享来源**；**禁止** skip/xfail/改收集顺序；修完给**成对反证** |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境、`R-F3` 外来文件、fake-IP DNS） | 按 `docs/architecture/LOCAL_GATE_PROTOCOL.md`（EC-02 交付物）归因；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂 / 网络 / 依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；**不得绕过**；**不得宣称安全** |

**固定口径**：CI 台账逐条记录每个推送提交触发的 run 到终态；写下某条记录的那个提交自身
的 run 只在回合汇报记账、**不再回写文件**。

## 终止与收口

- **ACHIEVED**：EC-01…EC-04 **全部 PASS** 且有**实跑证据** + 独立 RECHECK
  `PASS` / `PASS_WITH_WARNINGS` + 本文件收口（`latest_recheck` 为**仓库相对路径**）
  + CI 台账到终态。**未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进。
- **BLOCKED**：命中任一 `escalation_triggers`（尤其**放宽任一判据 / 门禁 / 放行面**、
  改 `test_m2_audit.py`、以 skip/xfail 掩盖、依赖 pin 变更）、同一失败签名超过
  `fix_policy` 上限、`max_cycles` 触顶、或连续 `no_progress_stop_cycles` 个 cycle
  未推进任何 EC ⇒ `status: BLOCKED`，**留人工决策**，逐条写明卡在哪、需要拍板什么。
- **ABORTED**：用户撤销目标或授权。
- 收口动作：① RECHECK 定稿；② 本文件 EC 置终态 + 状态历史追加 + 迭代日志补全；
  ③ `child_plans` / `memory_entries` 对齐；④ 残余逐条登记；⑤ CI 台账终态；
  ⑥ `validate.py` 绿。

## 不进入循环 / 需人工拍板

以下项**本循环不做**，也不因本 GOAL 存在而被宣称已解决；触及即 BLOCKED
（承自 GOAL-008…014，作为残余保留；按事实标注已完成 / 已豁免者）。

1. **ADR-0031（`tool_pack.*` 能力策略，`Status: Proposed`）是否采纳**——归用户拍板。
2. **威胁建模 / 授权面覆盖（BOLA / BFLA）**——需用户或 ADR 拍板。
3. **`artifacts/` token 清理**——**【已完成】**（GOAL-011 获删授权；建档实测：
   `git ls-files artifacts/` = 0）⇒ **本项无待办**。
4. **450 行纪律的贴线文件**——大重构会放大 diff 风险，需人工决定。
   （**本 GOAL 相关性**：建档当日实测**四个正好 450 行**且**零余量**——改动它们必须先搬代码；
   EC-03 只**登记**，不在本循环拆分。）
5. **依赖 pin 升级**（`undici` / `vite` / `yaml` 等）——上游 pin 变更，需用户或 ADR 拍板
   （含 `R-D1` 的 23 条告警：4 high / 13 moderate / 6 low；本 GOAL 只**分类**不升级）。
6. **hook 侧 L3 门**——治理面，需人工决定（EC-03 只**登记**）。
7. **把真实 runtime 设为默认**——默认必须仍是 Fake；本循环只做「显式配置才启用」。
8. **为 anthropic 形态引入 SDK / 新依赖**——优先用手写 HTTP；需要新依赖即 BLOCKED。
9. **把凭据写进 CI**（哪怕是为了让 CI 里看到 live 或检索分支）——**本循环明文禁止**；
   CI 必须保持离线。
10. **`ModelCompatibilityProfile` 是否按 AGENTS.md §1 建为一等域实体**——涉及 Domain 面与
    可能的 Canonical State 边界，需拍板。
11. **放宽 `AcceptanceCriteria`（或改合约）使其通过**——本 GOAL 明文禁止；
    这是「把门改成不挡路」。
12. **`secrets/llm_key.txt`（gitignored、untracked 的第二份凭据副本）**——**【已完成】**
    （GOAL-011 获删授权并在建档当日执行完毕）⇒ **本项无待办**。
13. **30 条已跟踪路径含非 ASCII（中文）文件名，违反 AGENTS.md §13**——**【已登记豁免】**：
    按 AGENTS.md §13 明文「既有历史路径不会仅为满足本规则而批量重命名」的口径，
    **不**批量重命名；若判定需要 ADR，则**产出 ADR 草案**、**不自行改判**。

**本 GOAL 特有的项（需用户拍板 / 明文不重启）**：

- **路径 (B) 的 5 条重设计项**（`docs/roadmap/PATH_B_REFUTATION_RECORD.md`）——**需拍板**。
  本循环**不自行重启**该路线；该记录的状态词「已否证 / 待重新设计」**原样保留**，
  不得读成待办功能、也不得读成已完成。
- **`W-A` 之外的策略面放宽**——**需另行拍板**：其余任何放宽（`default_effect`、
  `deny`、`require_approval`、`allow_with_constraints`、其他能力的 allow）本循环不得自行放宽。
- **门禁 scoping 的自我修正**——若 EC-01/EC-02 判出某红项根因是「门禁扫描了不属于仓库的
  文件」这类 **scoping 有误**，**本循环不改门禁**（放宽 `framework/validate_bundle` 的检查项
  即 `fix_policy.forbidden`）⇒ **只登记为决策简报条目（EC-03）**。
- **本机环境的 DNS / 代理特殊性**（fake-IP `198.18.0.0/15`）——**不改机器网络配置**，
  也不改判据；只做归因与登记。
- **`M-1`（出厂组合根是否自己接执行体缝 `ApiDeps.tool_providers`）**——本循环**只登记不实施**。

**承继的诚实边界（如实保留，不是待办）**：

- `R-F1`｜收敛 / 一致性判定含主观面时必须先**操作化**。
- `R-F2`｜真实数据 / 调用规模不足时的**诚实边界**。
- `R-F3`｜仓库外并发写者文件致 **as-is 本地 m0 可能停在 22/23**；CI 检出无 `scratch/`
  ⇒ **CI 不受影响**。未转绿前**不得**声称本地全绿（本 GOAL 的 EC-02 正是要把它变成
  **脚本化、可复跑**的事实，而不是每轮现场归因）。
- **`R-M1`｜Mimosa 钩子侧 `scanner_enobufs` 未得完整结论**——**不得**宣称项目安全。
- **`R-D1` / `R-B1` / `R-N1`**——依赖告警 / 承继残余 / 非 ASCII 路径豁免，原样保留。

**EC-03 的定位（必须写清，避免读错）**：EC-03 的产出是**「让这些项可被拍板」**，
**不是「把它们解决了」**。简报是给用户的决策入口，不是待办清单，也不是排期。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | （建档，无子 PLAN） | `1d8fe1f`（**推送 tip**，推送区间 `414f2e5..1d8fe1f`） | 治理 `validate.py` = `Cursor 治理验证通过` | M0 [36036419844](https://github.com/Eswink/research-system-new/actions/runs/36036419844) **六 job 全 success** + CodeQL [36036419719](https://github.com/Eswink/research-system-new/actions/runs/36036419719) **3/3 success** | — | EC-01…EC-04 全 PENDING；起点已定位（`W-D` 顺序签名 4 条 / `R-F3` 外来文件实测仍在且 `sha256` 已记 / 本机 fake-IP DNS 致 egress_guard 判红两条探针 / 450 行贴线**四个零余量** / 13 条人工面 + 承继残余）。**建档时零代码改动**（只增本文件） | cycle 1 = **EC-01 普查 + 修真实来源**（见下一行） |
| 1 | PLAN-20260925-161（EC-01） | derive `d472b7f`（PLAN-161 + `ALL_PLAN` 投影 + `child_plans`）；WP1–WP5 实施与收口回写见回合汇报 | **普查**：as-is m0 = **21/23**（两红项拆成 R-1…R-4，各有最小复现命令；表落 `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md`）。**修后**：同一组合命令**连续两轮** `4455 passed, 19 skipped`（`egress guard: FAIL` 计数 **0**；阻断只来自判据自身探针）；定向套件 `993 passed, 2 skipped` / `blocked 0`；`validate.py` = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks`；m0 全量终态见台账行 | 见下方 CI 台账 | **一次返工如实登记**：首轮判红 `test_real_repo_is_clean`（新增文档的 backtick 引用缺 `.py`）⇒ 修正后重跑取两轮；**另一次**：首次 m0 判红 `framework/validate`（本 cycle MEM 条目缺章节 / 未入 INDEX）⇒ 补齐后重跑取终态 | **EC-01 = PASS**。红项归零进度：**R-1 已归零 / R-2 已归零 / R-3 只登记（(iii) 门禁 scoping ⇒ 去 EC-03）/ R-4 只普查（(i) ⇒ 排 cycle 2）**；`W-D` 历史签名实测不再复现 | cycle 2 = **EC-02 本地判定确定性**：跑法协议 + 机械三分类 + 两条具名起点终态 + **R-4 实施**（postgres 跳过守卫提为加载无关） |

### CI 台账（逐 run 逐 job 实查；全部落在 main）

| 推送 | 提交 | run | 六 job 结论 |
| --- | --- | --- | --- |
| 建档（GOAL-015 落地） | 见回合汇报 | 见回合汇报 | 见回合汇报 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | ACTIVE | 建档：用户会话指令（goal 模式）授权修测试隔离与本地判定确定性（不改判据强度、不放宽门禁），四 EC 设计（跨套件隔离主干 / 本地判定确定性 / 决策简报 / 收口复检）。零代码改动。 |
| 2026-09-25 | ACTIVE | cycle 1：**EC-01 = PASS**（普查四红项 + 两处真实来源修复 + 连续两轮全绿 + 成对反证逐字节还原）。红项归零进度：R-1 / R-2 已归零；R-3 只登记（去 EC-03）；R-4 只普查（排 cycle 2）。 |

## 当前续点

- **cycle 1 已收口（EC-01 = PASS）**：子 PLAN `PLAN-20260925-161`（`DONE`）、复检
  `RECHECK-20260925-163`（`PASS_WITH_WARNINGS`，警告 = `R-3` 未消 + `R-4` 排后）、记忆
  `MEM-20260925-130` / `-131`。**下一轮 = cycle 2（EC-02 本地判定确定性）**：
  ① 跑法协议 `docs/architecture/LOCAL_GATE_PROTOCOL.md`（canonical m0 调用 + DSN 固化 +
  工作树前置条件 + 外部文件存在性处理 + **三分类**判定条件与归因命令）；
  ② 两条具名起点各拿唯一终态：`R-F3`（= 本 GOAL 的 `R-3`，门禁 scoping ⇒ 只登记，进 EC-03）
  与 fake-IP 出站判据（已由 `R-2` 修复归零 ⇒ 归因命令 = `LLM_MAIN_KEY=<任意值> pytest
  tests/api/test_runs_api.py -q`，修前 `blocked 2` / 修后 `blocked 0`）；
  ③ **实施 R-4**（把 postgres 跳过守卫提为加载无关，消除定向跑挂死）；
  ④ 把「代管 → 跑 → 还原」脚本化（EC-02 明文要求）。
- **cycle 1 的可复用事实（按需回看）**：
  1. **最小复现法**：顺序 / 时序类红 ⇒ 冻结共享输入（时钟 / 环境变量）。冻结时钟探针见
     `scratch/goal015_c1_order_tie_probe.py`；凭据注入复现见 `MEM-20260925-130`。
  2. **既有归因的一处更正**：出站判据的红**不是** fake-IP DNS 造成的（放行面只有
     `localhost`），根因是凭据可解析 ⇒ 见 `MEM-20260925-131`。
  3. **DSN 固化配方**：`RESEARCHOS_POSTGRES_DSN` pin 到 postgres-test DSN、
     `DATABASE_URL` / `POSTGRES_DSN` 清空（`scratch/goal015_m0_run.sh`）。
  4. **m0 必须独占**；记录未写完会让 `framework/validate` 判红（本 cycle 实测两次返工都属此类）。
- **开局已核实的文件层事实（决定可行性）**：
  1. `scratch/self-governance-bootstrap-prompt.md` **仍在**（`69944` B、
     `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`）⇒
     as-is 本地 m0 停在 **22/23** 形态（唯一未绿 = `framework/validate_bundle`）；
     CI 检出无 `scratch/` ⇒ 不受影响。
  2. 工作树有**并发写者**的未提交改动（`apps/web/src/features/models/ModelDetails.tsx`、
     `packages/domain/model_drift.py`、`services/api/dto/models.py`）⇒ **本 GOAL 不碰、不提交**
     这三处；只按显式路径提交本 GOAL 自己的产物。
  3. 规模门禁贴线：**四个正好 450 行零余量**（见「单 cycle SOP」③）。
  4. `make validate-all` = `.cursor/skills/cursor-framework-check/scripts/run_all_checks.py
     --profile m0 --keep-going`；m0 = python 6 + typescript 9 + framework 8 = **23** 项。
