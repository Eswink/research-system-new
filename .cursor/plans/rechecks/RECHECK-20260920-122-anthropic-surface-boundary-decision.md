---
id: RECHECK-20260920-122
plan_id: PLAN-20260920-122
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-20
completed_at: 2026-09-20
reviewer: root-agent-goal-009-cycle2
baseline_ref: dcbd313
checked_head: 2785e68
---

# RECHECK-20260920-122 — anthropic 面口径（EC-02 复检）

## 检查范围

**不采信实施叙述**：本复检按 EC-02 的判据自己重跑、自己**压**判据，并逐条核对
「决策是不是真的基于实测证据」。

- **A 判据面**：新判据 `tests/architecture/python/test_anthropic_surface_boundary.py`
  是否**真的**判住了边界（不是恒绿）；
- **B 决策面**：取 (b) 的理由是否**每一条都有仓库证据**（而不是偏好叙事）；
- **C 影响面**：§12.3 列的耦合点是否**逐条属实**（文件在不在、断言写的是什么）；
- **D 反证面**：改绑是否**真的**让它红、复原是否**真的**让它绿；
- **E 门禁面**：受影响套件 + 全量 m0 + 治理；以及 **CI 的反馈**。

## 检查结果

### A 判据面（10 checks 全绿；并**压**过）

`pytest tests/architecture/python/test_anthropic_surface_boundary.py` ⇒ **10 passed**。
判据不恒绿，且**不是空转**——它自己先断言「解析链必须真的解析出模型」
（`test_protocol_roles_resolve_to_at_least_one_model`），否则下面的断言是空集合上的 vacuously true。

### B 决策面（取 (b) 的四条理由逐条回仓库核对）

| 理由 | 核对方式 | 结论 |
| --- | --- | --- |
| run 腿的模型不是 `agnes_flash` | 跑解析链（协议 roles → agents → binding.value → models → endpoints） | `domain_a → research_alpha`、`reviewer_a → reviewer_gamma`；`agnes_flash` 不在 run 腿 ✅ |
| 耦合点 A 存在 | 读 `tests/loaders/test_contract_loaders.py` | `assert model.endpoint_id == "main"`（`models["research_alpha"]`）✅ |
| 耦合点 B 存在 | 读 `tests/e2e/test_ec03_real_runtime_offline_chain.py` + `tests/e2e/live_run_support.py` | `_MockRelayHandler` 自称「最小 **OpenAI-compatible** 端点」；`point_catalog_at` **只换 base_url、保留 protocol** ✅ |
| 风险 D 存在（该路径从未真跑） | cycle 1 的样本 + GOAL-008 的 EC-01 记录 | cycle 1 被 live 消费的是 `OpenAIChatGateway` 的 **probe** 段；run 的 LLM 路径（`llm_factory` 的 `anthropic/` 前缀）**无 live 样本** ✅ |

### C 影响面（§12.3 引用的路径逐条存在）

判据内的 `test_every_cited_repo_path_exists` 会逐条核对**反引号里的仓库路径**；
本轮它**先红过一次**——因为 §12.1 引用了一个既有风格 `path::symbol` 的 token 被判成不存在的路径。
处置是**让判据正确处理 `::symbol` 后缀**（取 `::` 前的文件部分核对），
**不是**把那条引用删掉或放宽判据——**未降低任何断言强度**。

### D 反证面（**先红后绿**，实测）

| 步 | 动作 | 观察 |
| --- | --- | --- |
| 1 | 把 `examples/config/models.yaml` 的 `research_alpha.endpoint` 改成 `agnes-anthropic` | 判据 **RED**：`assert not {'research_alpha': 'ANTHROPIC'}`（且**只有** run 腿那条红，其余 9 条仍绿 ⇒ 判据定位精确） |
| 2 | 复原为 `main` | 判据 **GREEN**：`10 passed` |
| 3 | 复核 `git diff examples/config/models.yaml` | **空**（复原干净，无残留） |

⇒ 判据**真的**对改绑敏感，且红的理由指向 §12.2–12.3 的文档（这正是「不得留模糊状态」要的效果）。

### E 门禁面

- 受影响定向套件：`tests/architecture tests/loaders tests/e2e/test_ec04_live_first_run.py
  tests/e2e/test_ec04_live_gate_offline.py` ⇒ **145 passed / 1 skipped**；
  `test_anthropic_surface_boundary.py` + `test_contract_loaders.py` ⇒ **33 passed**。
- `ruff check` / `ruff format --check` / `mypy`（单文件）⇒ 全绿。
- 全量 m0：见 GOAL-009 迭代日志（**含一次因读旧文件而 stale 的红**，已如实记录）。
- **CI 反馈（本 cycle 的额外判据）**：cycle 1 的推送 `e16e458` 让 CI **红**——
  `framework/validate` 报 `MEM-20260920-094` 缺章节。**CI 是对的**：
  我在本地修好了该条目，但**那次改写没有进暂存区**，于是提交进去的仍是旧形态，
  而本地门之所以绿是因为它读的是**未提交**的文件。已以独立 fix 提交修好（`86e77d8`）。
  **这类「判据读到的文件 ≠ 提交的文件」是本轮唯一的产品级教训**。

## Warnings（不阻断，如实登记）

- **W-1 取 (b) 意味着 run 腿仍走 `OPENAI_COMPATIBLE`。** 这不是「已解决」，而是**被有据地
  选择**的终态：边界现在**可判**、改绑**有路径**、影响面**有实测**。若将来要把 run 腿换成
  `ANTHROPIC`，(a) 的步骤与影响面已写在 `docs/integration/LLM_ENDPOINTS.md` §12.2–12.3，
  但**（a）本身从未实跑验证**——`ANTHROPIC` 的 run 路径仍**无 live 样本**。
- **W-2 §12.3 的「最重影响」是判断，不是实测结论。** 我**没有**真的改绑去跑那条离线门禁
  （那需要动 mock 或该用例），所以「会打到 OpenAI 形态的 mock 上」是从
  `_MockRelayHandler` 的能力（只有 `GET /models` + `POST /v1/chat/completions`）与
  `point_catalog_at` 只换 `base_url` 这两条**推出来的**，属于**强推断**而非实跑。
  如实登记；要坐实需要一次有意的改绑实验（本 cycle 不做，因为那会把测试改动的边界问题
  带进来）。
- **W-3 判据有意的「过严」。** 它把「run 腿必须是 OpenAI 兼容面」钉成硬约束，
  将来**正当**改绑会先撞红。这是**设计意图**（改绑是架构决策，应该撞门），
  但它确实会让「只看 CI 红绿」的人误以为坏了——文档 §12.3 已写明「红是信号不是缺陷」。
- **W-4 判据只覆盖 run 腿/ probe 腿的**协议**，不覆盖**执行**正确性。**
  它不证明 `ANTHROPIC` 形态的请求真的能被端点接受（那需要 live 调用）。
- **W-5 前端渲染 `endpoint_id` 的列**（`ModelCatalogTable` / `ModelDetails` / `ModelInspector`）
  只被**文档列入影响面**，**没有**被任何判据把守；改绑后设计基线是否真的会红，本 cycle 未实测。
- **W-6 CI 台账**：cycle 1 的推送 `e16e458` 触发 **run 35517481162 = failure**（
  `quality-ubuntu-latest` / `quality-windows-latest` 红，`framework/validate`；其余四 job success），
  已按「治理/安全门禁」类处置：**修记录**（`86e77d8`）而不是放宽 validator。该 run 的失败是
  **真实的记录缺陷**，不是 flake。

## 结论

**result: PASS_WITH_WARNINGS**。EC-02 取 **(b)** 并达到终态：边界**可判**（判据 10 checks，
反证先红后绿且定位精确）、改绑**有路径**（步骤 + 实测影响面 + 判据草案，§12.2–12.4）、
读面**同源**（`protocol` / `endpoint_id` 字段被判据核对）、决策**每条理由都有仓库证据**。
PLAN-20260920-122 可置 **DONE**。

**Warning 不阻断的理由**：W-1/W-2/W-4/W-5 都是**如实登记的边界**（哪些是实跑、哪些是强推断、
哪些没被把守），**不是**被掩盖的失败；W-3 是**有意**的判据刚度；W-6 是一条**已修复**的 CI 红，
其记录纠正方式是「修记录」而非「放宽门禁」。**全程未改任何门禁或断言强度。**
