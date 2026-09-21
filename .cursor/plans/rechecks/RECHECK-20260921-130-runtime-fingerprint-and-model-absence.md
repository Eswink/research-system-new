---
id: RECHECK-20260921-130
plan_id: PLAN-20260921-130
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-21
completed_at: 2026-09-21
reviewer: root-agent-goal-010-ec04
baseline_ref: c4a6f7c
checked_head: 本次收口提交（WP3/WP4 + 本 RECHECK + EC-04 置 PASS 同一次提交落地）
---

# RECHECK-20260921-130 — 运行时指纹落读面 + 「模型不存在」provider 侧样本（GOAL-010 EC-04）

## 检查范围

**不采信实施叙述**：从 GOAL-010 里 EC-04 的**原始判定细则**重新核对（不是从 PLAN-130 的叙述）：

1. **四要素落读面**：返回 model 名 / 端点头 / probe 版本 / 兼容性结论要**落读面**，
   而**不是**只活在测试的 `tmp_path` 里（GOAL-009 EC-01 的落盘位置）。
2. **口径**：仍停在 `REPEATABLE_CONFIGURATION`；`system_fingerprint` 缺失是**如实的缺口**，
   **不**降级判定、**也**不用「没看到指纹」冒充「模型可复现」。
3. **「模型不存在」**：要么 **provider 侧真实样本**（点名模型标识的失败 + **零回退**到别的模型），
   要么如实登记未实测 + 代价——**不得**把装配层推断写成 provider 侧观测。
4. **调用纪律**：provider 侧样本若跑，**次数取最小必要**；能复用 EC-01 的 session 就不另发。
5. 另加 PLAN-130 自己的 AC-3/AC-5：**反证成对**（先红后绿）、**不得放宽任何断言强度**。

## 检查结果

### 1. 四要素真的在产品路径上（不是只在测试里）

**重查起点事实**（PLAN-130 的 E-6）：`build_live_run_record` 的调用者当时**只有测试**。
**现状（独立 rg 复算）**：产品根出现两个调用点，链是闭合的——

| 面 | 位置 | 事实 |
| --- | --- | --- |
| 观测来源 | `adapters/openhands/usage_mapping.py` + `session_builder.py` | 取自 adapter **已经在读**的 `ConversationStats`；读不到 ⇒ 空手而归 |
| Port | `packages/application/ports/agent_runtime.py` | `AgentSessionResult.observed_model_identifiers`（加性字段，默认空） |
| 收集 | `packages/application/run_orchestration/phase_runner.py` / `service.py` | `on_observation` 与既有 `on_pause` **同形**；默认不注入 = 不收集 |
| canonical 事实 | `packages/application/run_orchestration/runtime_fingerprint.py:69`（`build_live_run_record`）、`:110`（`MODEL_PROBED`） | **产品调用点**在此（此前只有测试） |
| 读面 | `services/api/run_execution_view.py:56` | 合并呈现，`source` 标明占位/实测 |

**快照同源（独立复算）**：重跑 `tools/gen_openapi.py` ⇒ `docs/api/openapi.m13.json`
**零 diff**（只有一行 CRLF 警告）⇒ 提交的快照与代码同源，不是手改出来的。

### 2. 口径没被放宽（判据纯**加性**）

- `git diff --numstat`：判据面唯一改动是 `tests/architecture/python/test_live_failure_paths_same_source.py`
  **+69 / -0**——**零删除**，即没有任何既有断言被删弱或改窄。
- 结论仍由 `build_live_run_record` 的**既有**两态规则判，读面只**呈现** `verdict`；
  没有新造第二个判据、没有扩 `ModelReproducibilityVerdict` 枚举、没有引入「完全可复现」表述。
- `system_fingerprint` 缺失**只点名、不降级**：判据 `test_the_observed_fingerprint_is_readable_and_named_by_its_source`
  显式断言它在 `missing_fields` 里、而 `returned_model_identifier` **不在**，且 `status` 仍为
  `REPEATABLE_CONFIGURATION`。

### 3. 反证：**本 RECHECK 自己按压**（AC-3，先红后绿）

**按压动作**（在 `services/api/run_execution_view.py` 把合并关掉：`measured = None`）：

- **RED**：`test_the_observed_fingerprint_is_readable_and_named_by_its_source` 失败，
  `assert 'FROZEN_PLACEHOLDER' == 'RUN_OBSERVATION'`——**不是**「恰好绿」。
- 同一次按压里，另两条（占位路径、冻结不可改写）**仍绿** ⇒ 成对判据不是常量。
- **GREEN**（复原后）：三条套件 **12 passed**，且 `git diff --stat services/api/run_execution_view.py`
  **为空**（复原无残留）。

### 4. 「模型不存在」provider 侧真实样本（**走 AC-4 的第一条**）

样本 `tests/e2e/test_live_model_absence.py`：**预置条件式**（未声明 `RESEARCHOS_LIVE_MODEL_ABSENCE_CASE=1`
⇒ SKIP 并点名，**默认门禁下 `1 skipped`**），`requires_live_llm`，`url_policy` **不覆盖**
（走产品默认拒私网策略，**不放松任何门**）。读数逐字取自样本自报的 JSON：

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | 连通性那一步**过了** | `{"step": "connectivity", "ok": true}` ⇒ 端点与凭据都没问题 |
| 2 | 拒的是**那次 chat** | `{"step": "chat", "ok": false, "request_model": "research-os-absent-model-v1"}` |
| 3 | 类别 = `MODEL_RELAY_UNAVAILABLE` | = **5xx** 映射（`failure_category_of_http_status`） |
| 4 | **错误正文点名**了请求的标识 | `message_names_the_absent_model: true` |
| 5 | **零回退 / 无静默映射** | `returned_model_name: null`、`returned_name_differs_from_requested: false` |
| 6 | 凭据未泄漏 | 断言 `credential not in error_message` 通过 |
| 7 | 快拒（非重试到超时） | 全程 ~8.2s |

**新增诚实边界（实测得到，已写进 RUNBOOK §7 第 4 条）**：「模型不存在」**没有专属失败类别**——
它与「中转站故障」共用 `MODEL_RELAY_UNAVAILABLE`，而该类别**在可重试集合里**
（`adapters/relay/transport.py`）。⇒ 判定细则里的「**点名模型标识**」是这一格**唯一**能把它
与「中转站挂了」区分开的读数面；**按类别读会读错**。

### 5. 判据缺陷：本 cycle 自己造成并修好（按压的价值）

新增的「样本必须预置条件式」判据第一版是**文本子串**判据。按压（把样本里的开关名改成
`…_CASE_PRESSED`）⇒ **仍然全绿**（被断言的开关名是别名的前缀）。改成**行为成对**判据后，
第一版仍不红——`_require_case()` 抛的 skip 把**判据自己**变成 skip，而 **skip 不是红**。
最终形态加**等价性断言**（样本的开关常量 == 判据里的开关名）+ 把 skip **转成 `pytest.fail`**；
**再压 ⇒ 真 RED**，复原 ⇒ **21 passed / 1 skipped**（skip 的那条是样本自己）。

### 6. 门禁（**本机实跑**）

- **全量 m0（收口树最终态）**：`PASS: profile=m0; 23 deterministic checks`（exit 0，**0 FAILED**；
  `python/tests` = **4307 passed / 17 skipped**，504.76s；`--keep-going`；CI 同形配置：
  测试 DSN pin + `LLM_MAIN_KEY=""`）。此前三次：WP2 树 `PASS`（4301/16）、WP3 树 `PASS`（4306/17）、
  **收口树首跑 `FAILED: 1 check(s): framework/validate=1`**（治理两条，见下）⇒ 修后末跑 `PASS 23/23`。
- **一次既有环境 flake（不是本 cycle 引入，见 W-7）**：`framework/run_cursor_framework_evals` 在
  本 cycle 的**两次**全量里红过（`WinError 5` @ `os.replace`，`.cursor/runtime/evolution_state.json`），
  **孤立重跑 15/15 绿**（10 次连跑 + 5 次「上一检查 → 该检查」相邻复现），
  且**更早两个 cycle 的 m0 日志里有同签名**（`scratch/m0-cycle12-run7.log` 2026-09-15、
  `scratch/m0-cycle21-run3.log` 2026-09-17 ⇒ 全仓 202 份 m0 日志里 4 份命中）。
  最终全量该检查 **PASS**。归类：**既有、低频（~2%）、与负载相关的 Windows 文件锁**。
- 治理 `validate.py` / `validate_bundle` / `docs_consistency` / framework 组：全绿。
  **收口树首跑曾红 1 项**（`framework/validate=1`）：治理点名本 PLAN 的 `latest_recheck` 为 `null`
  且 `memory_entries` 为空表 ⇒ 补**仓库相对路径** + 落 `MEM-20260921-103` + `INDEX.md` 登记后复跑绿
  （见 W-13）。
- 定向：`ruff check` / `ruff format --check` / `mypy` 对两个改动文件全绿；
  `tests/architecture/python/test_live_failure_paths_same_source.py` 21 passed / 1 skipped。
- **凭据面复核**：全树字面量扫描（排除 `.git`/`.venv`）⇒ 该值只出现在 `.env` 与
  `secrets/llm_key.txt` 两处既有存储位（`.env` 被 gitignore）；**未**进入任何 tracked 文件、
  记录、日志或回显。`RESEARCHOS_AGENT_RUNTIME` **未**写入 `.env`。
- **CI 台账**：`89cfae8` / `c9b0ebb` / `6e3ddba` / `c4a6f7c` 四个推送的 run 与逐 job 结论见 GOAL-010
  「CI 台账」（`c9b0ebb` 的 M0 被下一次推送的 concurrency **取消**，如实登记；其 CodeQL 绿）。

## W 列表（如实登记，**不因收口消失**）

- **W-1** 「模型不存在」**无专属失败类别**（与中转站故障共用 `MODEL_RELAY_UNAVAILABLE`，且**可重试**）。
  读面今天**不解析错误正文** ⇒ 若将来要求读面直接报「模型不存在」，它**做不到**（只能靠消息点名）。
  改分类会触 `docs/reliability/FAILURE_MODEL.md` 的口径，本 cycle **未动**。
- **W-2** 样本是**单次观测**：**不**声称该 provider 对**所有**未知模型都如此，也**不**声称
  所有中转站都这么表现（射程声明同时写在样本模块 docstring 里）。
- **W-3** 样本走的是 **endpoint test（probe）** 路径，**不是** run 执行路径；它证明的是
  「provider 面对未知模型会拒绝并点名」，**不**替代 run 侧的失败语义（那由装配层结构判据钉住）。
- **W-4** **真实调用 3 次，超出「1 次」的最小必要**：第 1 次验证判据可跑通；第 2 次把观测打出来；
  第 3 次补**步骤轨迹**。第 3 次是**必要**的——前两次的记录**分不清**是连通性那步还是 chat 那步拒的，
  而这两件事语义完全不同（不区分就可能把「中转站挂了」写成「provider 拒了未知模型」）。
  代价：3 次小请求、合计约 24 秒，无 token 计费面变化（probe 路径不记账）。
- **W-5** `system_fingerprint` 缺失仍报 `REPEATABLE_CONFIGURATION`——**设计内**（AGENTS §4：
  「可重复配置」**不等于**「完全模型可复现」）。这条**不是**缺陷，但它意味着**看到该结论不等于
  拿到了指纹**，读面必须连 `missing_fields` 一起读。
- **W-6** 单值槽位表达不了「一次 run 观测到多个不同 model 名」：多值进 `observed_model_identifiers`，
  单值留 `null` ⇒ 结论**必为** `NOT_VERIFIED`（**不挑一个**代表）。多值本身可见，不会被藏。
- **W-7** `framework/run_cursor_framework_evals` 在本 cycle 的**两次全量里红过**（其余各次绿）：
  `PermissionError [WinError 5] … evolution_state.json.tmp -> evolution_state.json`（`os.replace`）。
  **根因未定论**，但已用证据收窄到**既有、低频、与负载相关的 Windows 文件锁**：
  ① 孤立连跑 **10/10 绿**；② 「上一检查 → 该检查」相邻复现 **5/5 绿**；
  ③ **更早两个 cycle 的 m0 日志里同签名**（2026-09-15 `m0-cycle12-run7`、2026-09-17
  `m0-cycle21-run3`；全仓 202 份 m0 日志中 4 份命中）⇒ **不是本 cycle 引入**（该检查不读
  `docs/` 与本 cycle 的任何产品文件）；④ 本 cycle 末次全量该检查 PASS。
- **W-8** **本 cycle 有一次全量 m0 的证书作废**：该次运行期间执行过 WP4 的**按压**（改产品文件又复原），
  时间窗与 `python/tests` 重叠 ⇒ 那次「23/23」**不作为凭证**，以**复跑**为准。如实登记。
- **W-9** 判据缺陷（文本子串 + skip 不是红）已修（见上 §5），但**同类风险仍在**：
  仓库里其它地方**可能仍有**「按字符串子串判在场」的判据；本次只在新增判据上按压，
  **未**做全仓扫描（那是另一个 EC 的规模）。
- **W-10** `model.probed` **不**进通知白名单（`services/api/routers/notifications.py` 零命中，独立复算）
  ⇒ 指纹事实**不产生用户可见通知**；这是**有意**的（指纹不是通知事件），但意味着
  「落读面」只经 `GET /runs/{id}`，控制台**未**新增渲染分支（⇒ 不触发设计基线重生成）。
- **W-11** 30 条 tracked 非 ASCII 路径（AGENTS §13，承前几个 cycle，未动）。
- **W-12** `domain_discovery` 的 `minimum_sources: 10` 仍**无任何 run 路径行使过**（承 EC-02 W-7）。
- **W-13** **收口树首跑 m0 红 1 项**（`framework/validate=1`，治理）：`latest_recheck` 为 `null`
  且 `memory_entries` 为空表（本 PLAN 置 `DONE` 时暴露）。**已修**（补仓库相对路径 + 落
  `MEM-20260921-103` + INDEX 登记）并复跑绿。登记理由：这是**首跑红**，**不记成绿**；
  同类漏改 GOAL-009 收口时也抓到过（`latest_recheck` 写成裸 ID）。

## 结论

**PASS_WITH_WARNINGS**。EC-04 的三条判定细则**逐条成立**：四要素**在产品路径上**（观测 → canonical
事件 → 读面，且快照与代码同源经独立重算）、口径**停在**两态且缺项逐项点名、provider 侧
「模型不存在」**有实测样本**（点名模型标识 + **零回退**）。反证**由本 RECHECK 亲自按压过**
（关掉合并 ⇒ 真 RED；复原 ⇒ 绿且无残留）。**未放宽任何断言强度**（判据面 diff **+69/-0**）。
W-1（类别不可区分）与 W-4（3 次调用）是**本 cycle 最要紧的两条**：前者是**实测发现的既有边界**，
后者是**对调用纪律的如实超支登记**。W-7/W-8 是**工具面与流程面**的诚实记录，均已用复跑纠正，
**未**据此宣称任何未跑过的门。
