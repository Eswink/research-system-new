---
id: MEM-20260923-116
title: "本机全量 m0 转绿的配方：那条 fake-IP 红的真因是 `.env` 里的 `LLM_MAIN_KEY` / `RESEARCHOS_DATABASE_URL`"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.88
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-151-live-page-read-face-batch-two.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-152-live-page-read-face-batch-two.md
supersedes: []
---

## 做了什么

本机全量 `m0` 长期停在 **22/23**：`python/tests` 的自身数字是
`4413 passed, 0 failed`，但进程 `exit 1`，判词是出站判据拦到一个
`198.18.x.x:443`（fake-IP 段）连接。cycle 2 定位到真因并复现出**转绿配方**。

真因：本机 `.env` 里 `LLM_MAIN_KEY` 与 `RESEARCHOS_DATABASE_URL` **非空**，
被 `litellm` 的 `load_dotenv()` 注进进程环境 ⇒ 组合根按 `.env` 的端点/DB 配置
解析主机名并尝试健康探测 ⇒ 本机 DNS 走 fake-IP 代理（`198.18.0.0/15`）⇒ 出站判据判红。
**这不是代码缺陷，也不是判据缺陷**：判据抓到的是一次**真实出站尝试**。

**同一个注入源还造成第二件事（本轮顺带查出）**：`tests/e2e/test_run_chain_retrieval_live.py`
的凭据门 `_live_credentials()` 取目录声明的 `credential_ref`（本仓 = `LLM_MAIN_KEY`），
取到就**真跑一次 live 检索**、取不到才 skip。`.env` 把它注进来 ⇒ 那一轮的**本地
m0 实际跑了一次真实联网检索**（日志里该文件是 `.`），本地默认门的「离线」只是没被出站判据抓到而已。
本配方清空该键后同一文件如实变 `s`。实测证据：
`grep -o "test_run_chain_retrieval_live\.py.\{0,3\}" scratch/goal013-c1-m0.log` ⇒ `. `；
同一条命令对 `scratch/goal013-c2-m0.log` ⇒ `s`。总用例数不变（4430 = 4413+17 = 4412+18），
**恰好一条**从 passed 变 skipped ⇒ 差异可完整归因到这一条，没有别的隐藏变化。
⇒ 清空这两个键不只是「让门变绿」，它把本地 m0 从**偷偷联了网**改回**默认离线**。

## 为什么这样做

EC-05 明文要求收口时本地 m0 **23/23**。此前只把这条红「归因」给环境并放着
（22/23 加一段解释），收口时就会一直在。归因写清 ≠ 门变绿——
**只有把注入源掐掉，判据才会自己转绿**。

## 怎么做与复现

逐字命令（一次成功，`0 failed` 且判据不再报 blocked）：

```bash
RESEARCHOS_POSTGRES_DSN="postgresql://research_os:research_os_m14_test@localhost:15432/research_os" \
RESEARCHOS_DATABASE_URL="" LLM_MAIN_KEY="" \
RESEARCHOS_OTEL_COLLECTOR_ENDPOINT="http://localhost:4318" \
RESEARCHOS_REQUIRE_COLLECTOR="1" RESEARCHOS_REQUIRE_POSTGRES="1" \
uv run --frozen --no-sync python -B \
  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
```

四个要点，缺一条就回到 22/23：

1. **`LLM_MAIN_KEY=""` 与 `RESEARCHOS_DATABASE_URL=""` 必须显式清空**——
   只 `env -u` 或只设 DSN 不够：`litellm` 的 `load_dotenv()` 会把 `.env` 重新注回。
   空串能让「有值就用」的取值链走到下一个键。
2. **`RESEARCHOS_POSTGRES_DSN` 必须钉到 test DSN**（`localhost:15432`），
   否则组合根会去连 `.env` 指向的库。
3. 起容器：`docker compose --project-directory . -f infra/compose/postgres-test.yaml
   -f infra/compose/otel-evidence.yaml up -d --build --wait` —— **collector 与 postgres 都要**，
   缺 collector 时 `python/tests` 报 `MaxRetryError 127.0.0.1:4318`。
4. 单测快速探针（几秒），用来确认配方生效再跑全量：

   ```bash
   RESEARCHOS_POSTGRES_DSN="…:15432/research_os" RESEARCHOS_DATABASE_URL="" LLM_MAIN_KEY="" \
     uv run --frozen --no-sync python -B -m pytest \
       "tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure" -q
   ```

   成功的标志是输出里出现 `egress guard: judged 1 connection attempt(s); blocked 0`。

**不得**为了转绿去放宽 `tests/egress_guard.py` 或加豁免名单——判据抓的是真出站。

## 适用边界

- 只在**本机**跑全量 m0 时适用；CI 侧不受影响（CI 环境没有这份 `.env`），
  所以 CI 的 m0 一直是 23/23 —— 本机 22/23 与 CI 23/23 可以同时为真，不矛盾。
- 清空这两个键会改变被测进程的**解析结果**：凡是断言「按 `.env` 解析出某端点/某库」的用例，
  在这个配方下的语义是「按本配方给的环境解析」。既有 m0 全套在本配方下 23/23 通过，
  说明没有用例依赖 `.env` 的那两个值。
- **判据口径**：同一个配方会让 1 条 live 用例从 passed 变 skipped（见上）。
  「passed → skipped」**不是**放宽：skip 不是 PASS，该用例的权威结论仍由 CI 中
  具备凭据的环境承担。但它意味着**不能拿本配方下的 `4412 passed` 与旧配方下的
  `4413 passed` 直接比大小**——两者不是同一集合，要按「总用例数 + skip 名单」比。
- 若将来 `.env` 新增其它被 `load_dotenv` 注入的键（尤其端点/凭据类），需要按同样方式补清空。

## 来源

- `scratch/goal013-c2-m0.log`（本配方下的全量 m0 终局）、
  `scratch/goal013-c2-m0-fixprobe.txt`（单测探针：`blocked 0`）。
- 相关：[[MEM-20260923-117-live-page-equals-read-face-writing-traps]]（同 cycle 的判据写法陷阱）。
- 既有的同族记录「本地 m0 egress guard fake-IP red」止于归因；本条把它推进到**可复现的转绿配方**。
