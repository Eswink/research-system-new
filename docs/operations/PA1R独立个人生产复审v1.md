# PA-1R 独立个人生产复审 v1

日期：2026-09-05
范围：Research OS Personal Production Baseline 独立复审
方法：不继承 PA-1 PASS 结论；以实际部署、实际 PostgreSQL/Artifact restore、真实 Remote Worker/GPU、故障注入、restored full Research Run 和 release/version truth 为准。

## 0. 最终结论

```text
PA-1R FAIL
Research OS Personal Production Baseline = NOT COMPLETE
```

原因不是运行时、restore、GPU 或 Research Workflow 失败，而是存在一个未关闭的 release/deployment blocker：

- 当前正式 Git revision：`687527394b41834a3e74e84e3ef5cfc01eaca750`；
- 决定性 Release identity 采样时主工作树已有 31 个 dirty entries，其中 10 个为 untracked；写入本复审记录后最终 `git status` 为 32 个 dirty entries / 11 个 untracked（新增项即本报告本身）；
- 本次实际验证使用的关键文件 `tools/personal_reference_workflow.py`、`tools/restore.py`、`packages/application/m12_reference/persistence.py`、`services/worker/reconnect.py` 均不存在于该 HEAD；
- 因此 `git clone/checkout 6875273...` 不能重建本轮已经验证通过的 Personal Production candidate；
- 当前 `.cursor/releases/RELEASE_EVIDENCE.json` 是 2026-08-11 生成的 Cursor framework evidence，不记录本轮 code revision / DB schema / Worker protocol / runtime image / upstream identities，不能充当本轮 Personal Production Release Record。

在上述源码被形成一个不可变、可获取、可重建的正式 release revision，并重新从该 revision 执行 deployment + restore + Reference Run 之前，不满足 PA-1R Exit。

---

## 1. PA-1 Finding Revalidation

本轮不使用 PA-1 的 PASS/FAIL 作为输入。重新验证后：

| Gate | 独立结果 |
|---|---|
| frozen dependency reconstruction | PASS |
| clean PostgreSQL/Collector deployment | PASS |
| actual DB backup/restore | PASS |
| actual Artifact backup/restore/digest | PASS |
| restored Research Truth closure | PASS |
| Secret canary hygiene | PASS |
| Worker reconnect/hard restart | PASS |
| real GPU run/timeout/cancel/restart | PASS |
| Scheduler/Control Plane durable recovery | PASS |
| Collector-down fail-open | PASS |
| clean/restored full Research Workflow | PASS |
| Observability/Cost/Eval truth | PASS with explicit cost degraded semantics |
| Release/version truth | **BLOCKER / FAIL** |

本轮发现并关闭 3 个实现/配置问题：

1. 正式命令 `python tools/personal_reference_workflow.py --help` 初始因 repo import root 缺失而失败；已增加 file-path CLI bootstrap，并回归。
2. `docker-compose.personal.yml` 初始将 PostgreSQL 发布到 `0.0.0.0/[::]`；已改为 `127.0.0.1`，实际重建验证并增加自动回归。
3. CLI bootstrap 初版触发 Ruff E402；已按 repo-path bootstrap 语义增加限定说明/抑制，最终 lint 通过。

## 2. Deployment reconstruction

### 独立环境

- 原 Compose 栈开始时为 down；未把既存运行容器当证据。
- 构造隔离源码目录 `scratch/pa1r-20260905/clean-source-v1`，明确不携带 `.env`、`data/`、`.venv`。
- `uv lock --check`：PASS。
- `uv sync --frozen --dev`：PASS。
- `pnpm install --frozen-lockfile`：PASS。
- GPU image 连续两次 `--no-cache --provenance=false --platform linux/amd64 --build-arg SOURCE_DATE_EPOCH=0` 构建得到完全相同 image ID：
  `sha256:3d306d299abcb7c5384151ee15b6b7f5819e70203e5da50b47341710720c9d5c`。
- digest-qualified local ref 可由 Docker 解析到同一 image。

### clean Personal Production 基础栈

- 独立 Compose project：`pa1rprod2`；独立 PostgreSQL volume；不复用原生产卷。
- PostgreSQL：实际 `16.14`，host `127.0.0.1:17432`。
- OTel Collector：host `127.0.0.1:15318`，healthy。
- PostgreSQL public tables：22；migration versions：`1..9`。
- Control Plane、Gateway、Remote Worker 均从隔离环境启动。

### Hidden manual state 结论

运行态没有依赖旧 `.env` / `data` / `.venv`，但源码层存在 blocker：clean-source 是从当前 dirty worktree（含 untracked files）复制得到，而不是从正式 Release revision checkout 得到。因此“运行时无 hidden state”成立，“release deployment reproducible”不成立。

## 3. PostgreSQL restore evidence

实际 backup：

- `research-os-20260905-123133.dump`：42,310 bytes，PostgreSQL custom format；
- `tools/backup.py --verify --sample 100`：7 blobs checked，0 anomalies。

实际 clean restore target：

- container：`pa1r-restore-postgres-20260905`；
- 独立 volume：`pa1r_restore_20260905_pgdata`；
- host：`127.0.0.1:18432`；
- 独立 restore canary password。

正式 `tools/restore.py` 恢复成功。恢复库再次确认：

- 22 public tables；
- migration `1,2,3,4,5,6,7,8,9`；
- 原 live Reference Run 仍为 `SUCCEEDED`。

结论：actual PostgreSQL restore PASS。

## 4. Artifact restore evidence

实际 Artifact backup：

- `artifacts-20260905-123133.tar.gz`：12,081 bytes；
- restore 到此前为空的 `data/恢复artifacts-v1`；
- `tools/restore.py` 报告 `restored and verified 7 blobs`。

首次 restore 后重新计算全部 7 个 blob 的 SHA-256，均与 content-addressed filename/digest 一致。

在 restored environment 再执行完整 Research Run 后，ArtifactStore 增至 12 blobs；再次全量重算：`digest_mismatch=0`。

结论：Artifact restore + digest integrity PASS。

## 5. Restored Research Truth audit

抽样 live Run：`72640bd4-da5c-41c5-855e-6ac6bd4555df`。

恢复后闭包仍成立：

```text
Run SUCCEEDED
  -> 5 canonical Artifact rows
  -> 3 Evidence rows
  -> 3 Source rows
  -> Claim VERIFIED
  -> 3 SUPPORTS relations
  -> Eval PASS
  -> ExperimentRun SUCCEEDED
  -> ReproducibilityAudit preserved
  -> Memory preserved
  -> Usage entries = 3
  -> Deliverable digest preserved
```

关键原始 digest 保持一致，包括：

- manifest `sha256:2f78343d238acc8c7f7ebd383bfd8394371ccf065189216ecdce69f46f00d401`；
- eval report `sha256:d517b32c33a904ca0520932a7c9f13ce7de186257e8299dbd043196d6901edd8`；
- deliverable `sha256:e8cfc81065ddf7e585f41142a83792929af4178880189aa83c275710db8f3c7e`。

结论：cross-restore Research Truth PASS。

## 6. Secret audit

创建 6 个相互独立的随机 canary：live DB、live Worker enrollment、LLM catalog、restore DB、GPU fault DB、restored Worker enrollment。只报告 SHA-256 短指纹，不记录 secret 值。

最终扫描覆盖：

- Git current tree；
- Git 全历史；
- 展开的 PostgreSQL custom dump；
- 展开的 Artifact tar；
- live/restored Artifact blobs；
- `*.log` / `*.jsonl`；
- telemetry；
- exports。

6 个 canary 在所有上述类别均为 `0` 命中。

结论：本轮 canary Secret hygiene PASS。该结论不等价于证明历史上从未存在任何未知 secret；它证明本轮实际注入的各 trust-domain canary 没有泄漏到要求检查的持久化面。

## 7. Worker recovery

实际 Remote Worker：`pa1r-gpu1`。

- 初始注册 generation=1，protocol=1，runtime=0.4.0，GPU observation 存在。
- 精确 hard-kill 实际 Gateway listener 后，Worker 输出 `gateway unavailable; retrying`。
- Gateway 恢复后 Worker 自动重连并重新注册 generation=2；未手工修改 DB。
- 再启动同 identity 得到 generation=3；精确 hard-kill Worker Python PID；确认进程退出。
- 同 identity 再启动后自动注册 generation=4；未手工修改 DB。

restored environment 另启 `pa1r-restore-gpu1`，使用独立 enrollment canary、无 DB/LLM credential，注册 READY 并完成 restored full Research Run。

结论：Remote Worker reconnect/recovery PASS。

## 8. GPU recovery

实际 NVIDIA GPU：RTX 4060 Laptop GPU；驱动 581.80；GPU memory 8188 MiB。

真实 GPU 验证：

- CUDA GEMM smoke：PASS，实际报告 GPU facts，无 CPU fallback；
- GPU timeout：`timeout_seconds=6`，结果 `TIMED_OUT`，执行容器无残留；
- Remote GPU cancel：Control Plane cancel -> container kill/remove -> job `CANCELLED` -> lease release；
- cancel 后 fresh GPU probe：PASS；
- stale-fence late result：HTTP 409 拒绝；
- Worker hard restart 后可重新注册并继续执行。

相关真实 GPU tests：

- GPU smoke + timeout：2 passed；
- distributed GPU cancel/fencing：1 passed。

结论：real GPU run/cancel/timeout/restart/cleanup PASS。

## 9. Research Workflow

### clean environment Run

Run：`72640bd4-da5c-41c5-855e-6ac6bd4555df`。

- 首次故意缺失 `LLM_MAIN_KEY` 时 Preflight 以 `CREDENTIAL_MISSING` fail-closed，未进入执行；
- 按 formal catalog 提供隔离 canary 后重跑；
- RemoteExecutionBackend -> Gateway -> real Docker/GPU Worker；
- Run `SUCCEEDED`；
- 5 Artifacts；3 Evidence；Claim VERIFIED；Eval PASS；3 Usage；Deliverable；Memory；Audit；ExperimentRun 全部落 PostgreSQL/ArtifactStore。

### restored environment Run

Run：`b41fa742-0e75-4632-8f11-36c6f77ebdc6`。

- 使用实际 restore 得到的 PostgreSQL 与 `data/恢复artifacts-v1`；
- 使用独立 restored Gateway + real GPU Worker；
- Run `SUCCEEDED`；
- 5 新 Artifacts；3 Evidence；Claim VERIFIED；Eval PASS；Usage=3；Deliverable 存在；
- 同时确认 backup 恢复进来的旧 Run/Evidence 仍完整。

结论：full Research Workflow 在 clean + restored environment 均 PASS，不是 one-shot workflow。

## 10. Observability / Cost / Eval

### Observability fail-open

- 实际 stop `pa1rprod2-otel-collector-1`，确认 `exited`；
- Collector down 期间执行完整 Reference Run：`2f934fdd-cdf1-4cc8-9245-59647c54e455`；
- Run 仍 `SUCCEEDED`，Eval count=1，Usage count=3，并产生完整 Artifact/Evidence/Claim/Deliverable；
- Collector 重启后恢复 `healthy`。

### Operations truth

实际 Control Plane/Scheduler Python 进程 hard restart 后：

- `/runs/{id}` HTTP 200；
- `/usage` HTTP 200，3 usage entries；
- `/cost` HTTP 200；未冻结 pricing 时明确返回 `MONETARY_UNAVAILABLE`，没有伪造成本；
- `/telemetry` HTTP 200；
- Eval trend HTTP 200，verdict PASS。

真实 PostgreSQL scheduler crash/restart/lease recovery 场景：1 passed；takeover worker 从 canonical DB 恢复并只完成一次。

结论：Observability fail-open、Usage、Cost truth、Eval、durable scheduler state PASS。

## 11. Release truth

### 已独立确认的 runtime/version truth

- Product `VERSION=0.4.0`；
- base HEAD：`687527394b41834a3e74e84e3ef5cfc01eaca750`；
- DB migrations：`1..9`；
- public tables：22；
- Worker protocol：1；
- Worker runtime：0.4.0；
- OpenHands SDK：1.42.0，与 `UPSTREAM_COMPONENTS.yaml` 一致；
- OTel Collector：0.139.0，实际 local image ID `sha256:486748c7b19dd0bf37b24e094fc9ecbdd831b67ef9467e0bfa60d016ec9c396b`；
- PostgreSQL runtime：16.14 / `postgres:16-alpine`；
- GPU application image：`sha256:3d306d299abcb7c5384151ee15b6b7f5819e70203e5da50b47341710720c9d5c`，与 `UPSTREAM_COMPONENTS.yaml` `application_image_digest` 一致；
- GPU base index digest：`sha256:7b324d212a4450795b49edba9949b7cdc72429148a64e974334bfe5774d51385`。

### 未关闭 BLOCKER

决定性 Release identity 采样时 source identity（随后仅新增本复审报告这一 untracked 文件）：

- dirty entries：31；
- untracked files：10；
- 最终交付前 `git status`：32 dirty entries / 11 untracked；
- tracked patch SHA-256（排除 history-session）：`be703e27fe4b2511456fbcc30aef244d183fb3fd05803f48dea06aece48651e8`（该值是在最终 lint 修补前采集，仅作为中间证据，不作为 Release identity）；
- 关键 runtime/restore 文件直接查询 `HEAD:path` 均为 `MISSING_FROM_HEAD`：
  - `tools/personal_reference_workflow.py`；
  - `tools/restore.py`；
  - `packages/application/m12_reference/persistence.py`；
  - `services/worker/reconnect.py`。

因此：当前能描述“本机工作树 candidate”，但没有一个正式 immutable Release revision 能被另一 clean checkout 获取并重建。本轮不能把 base HEAD + 本机 dirty state 宣称为生产 Release Record。

**Release/version truth = FAIL / BLOCKER OPEN。**

最小关闭动作：把本轮已验证 candidate 形成正式 immutable release revision（不得遗漏当前 untracked runtime files），生成包含 code revision / DB schema / Worker protocol / runtime & OCI digests / upstream pins 的 Personal Production Release Record，然后严格从该 revision 新 checkout，再执行 frozen install -> deployment -> actual restore -> restored full Reference Run -> version recheck。

## 12. Remaining non-blocking debt

以下不改变本轮唯一 blocker 的性质：

- `/cost` 在无 frozen pricing / GPU price source 时为 `MONETARY_UNAVAILABLE`；这是显式 truthful degraded state，不是 blocker。
- Starlette TestClient 当前产生一条 upstream deprecation warning；相关回归仍全部通过。
- 本轮创建了隔离 audit containers/volumes/source scratch；为保留可复核证据未执行 volume destruction。
- 现有操作员 `.env` 与新版 `.env.example` 存在配置漂移/placeholder；clean canary deployment 已证明运行路径不依赖它，但上线前仍应按正式文档重新填写。

## 13. PA-1R PASS / FAIL

```text
PA-1R FAIL
```

理由：PA-1R Exit 要求 deployment 与 release/version truth 独立成立且无未关闭 BLOCKER；当前正式 Git revision 不能包含并重建实际被审计的 candidate。

## 14. Personal Production Baseline

```text
Research OS Personal Production Baseline = NOT COMPLETE
```

因此不启动 M18/M19。

---

## Regression summary

- Ruff（`tools/personal_reference_workflow.py` + PA-1R tooling test）：PASS。
- PA-1R 相关最终 pytest：55 passed，1 upstream deprecation warning。
- real GPU smoke + timeout：2 passed。
- distributed Remote GPU cancel/fencing：1 passed。
- PostgreSQL scheduler crash/restart recovery：1 passed。
- clean full Reference Run：SUCCEEDED。
- Collector-down full Reference Run：SUCCEEDED。
- restored full Reference Run：SUCCEEDED。

## 本轮直接修复

- `tools/personal_reference_workflow.py`：正式 file-path CLI 可执行 + 限定 E402 bootstrap 说明。
- `docker-compose.personal.yml`：PostgreSQL host publish 收紧为 loopback-only。
- `docs/operations/PERSONAL_DEPLOYMENT.md`：同步 DB/OTLP loopback trust boundary。
- `tests/tooling/test_personal_reference_workflow.py`：CLI + PostgreSQL loopback regression。

Domain/API/schema：本轮没有新增 Domain/API/schema；验证既有 migration 1..9。
安全/凭据：收紧 PostgreSQL host exposure；6 类 canary 0 leakage；Worker 明确不接收 DB/LLM credential。
兼容性/迁移：runtime/schema identities 一致；唯一阻断为源码尚未形成正式 release revision。
上游：OpenHands 1.42.0、OTel Collector 0.139.0、PostgreSQL 16.x、GPU OCI identities 已复核。
下一项任务：仅关闭 Release/version truth blocker 并从正式 revision 重跑 PA-1R；在 PA-1R PASS 前不得进入 M18/M19。
