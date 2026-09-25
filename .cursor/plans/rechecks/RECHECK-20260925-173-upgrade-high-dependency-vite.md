---
id: RECHECK-20260925-173
plan_id: PLAN-20260925-172
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-25
completed_at: 2026-09-25
reviewer: root-agent-goal-016-cycle3 + 只读告警探针（scratch/goal014_c4_residual_probe.py）
baseline_ref: cycle 2 推送 tip `c2bc8a4`
checked_head: 当前树（`vite` 声明 + 锁面 + 记录；**无产品代码改动**）
---

# RECHECK-20260925-173 — D-03(b) high 依赖升级（GOAL-016 cycle 3）

## 检查范围

① 解析版本变化是否**逐包可核对**且**只含被授权的包**（AC-1）；② 全量 web 门（AC-2）；
③ 设计基线是否漂移（AC-3）；④ m0 终态行（AC-4）；⑤ `R-2` 在升级后是否**仍然有效**（AC-5）；
⑥ 越界项是否如实登记（AC-6）；⑦ 升级**没有**动到工作树里的并发写者文件。

## 检查结果

### 一、AC-1｜解析版本变化（before → after）

- **声明面**：`apps/web/package.json` 的 `vite` 由 `"6.3.5"` → **`"6.4.3"`**。
- **锁面**（`git diff pnpm-lock.yaml` 逐行核对，**只改了 `vite` 及其 peer 引用**）：
  - `vite@6.3.5`（`sha512-cZn6NDFE7wdTpINgs++ZJ4N49W2vRp8LCKrn3Ob1kYNtOo21vfDoaV5GzBfLU4MovSAB8uNRm4jgzVQZ+mBzPQ==`）
    → `vite@6.4.3`（`sha512-NTKlcQjlAK7MlQoyb6LgaqHc8sso/pVyUJYWMws3jg21uTJw/LddqIFPcPqP6PzpgbIcZyKI85sFE4HBrQDA8A==`）；
  - `@vitejs/plugin-react@5.1.0` 的 peer 解析由 `(vite@6.3.5…)` → `(vite@6.4.3…)`（**它自己的版本没变**）；
  - 其余解析版本**零变化**（diff 的 9 增 9 删全部落在上述两处）。
- **实际安装**：`node -e "require('./apps/web/node_modules/vite/package.json').version"` ⇒
  **`6.4.3`**；`.pnpm/` 下已无 `vite@6.3.5` 目录。
- **覆盖率**：4 条 high 的 `first_patched_version` = `6.4.2`（`#5`/`#18`）与 `6.4.3`（`#7`/`#20`）
  ⇒ **`6.4.3` 同时覆盖两者**（一次上移覆盖全部 4 条 high）。
- **升级前告警面留档**：`scratch/goal016-c3-alerts-before.txt` = open **23**
  （4 high / 13 medium / 6 low）。

### 二、AC-2｜全量 web 门（逐条实跑）

| 门 | 命令 | 结论 |
| --- | --- | --- |
| 根 `check` | `pnpm run check`（`format:check` / `lint` / `typecheck` / `boundaries` / `test`） | **exit 0** |
| web lint | `pnpm --dir apps/web run lint` | **PASS** |
| web typecheck | `pnpm --dir apps/web run typecheck` | **PASS** |
| web unit | `pnpm --dir apps/web run test` | **PASS** |
| web build | `pnpm --dir apps/web run build` | **PASS** |
| **stub e2e** | `pnpm --dir apps/web run test:e2e` | **`98 passed`** |
| **live e2e** | `pnpm --dir apps/web run test:e2e:live` | **`53 passed`** |

日志：`scratch/goal016-c3-root-check.log` / `-web-{lint,typecheck,test,build}.log` /
`-e2e-stub.log` / `-e2e-live.log`。

### 三、AC-3｜设计基线**零漂移**

- 结构签名门（`apps/web/tests/e2e/design-outline-guard.spec.ts`，比对
  `apps/web/tests/e2e/design-outlines.json`）在 **stub e2e 内通过**
  ⇒ **无需重生成基线**。
- **未**重生成任何基线、**未**调 `maxDiffPixelRatio` 或任何容差。

### 四、AC-5｜`R-2` 在升级后**仍然有效**

- `pytest tests/architecture/python/test_default_gate_credential_isolation.py
  tests/architecture/python/test_default_gate_isolation_probe.py -q` ⇒ **`3 passed`**。
- 全量 web 门的日志里 `egress guard: judged 0 connection attempt(s); blocked 0`，
  **零** `egress guard: FAIL` 行 ⇒ 默认门**仍不得**看到凭据、未因升级而出网。

### 五、AC-6｜越界项如实登记（**不做**且写明理由）

- **`undici`**：as-is `5.29.0`，修复版本 `6.24.0` / `6.27.0` / `6.28.0` ⇒
  **主版本跳跃**（`5.x → 6.x`，breaking）⇒ D-03(b) 明文**不做**；它是 8 条**低 / 中**告警，
  **无 high** ⇒ 不属于「high 先升」的范围。
- **`yaml`**：as-is `2.8.1`，修复版本 `2.8.3` ⇒ **patch 且可安全升级**，
  但它是 **medium**、**非 high** ⇒ 按「high 先升、minor/patch 合批」排**下一批**。
- **剩余 19 条**（13 medium + 6 low）原样保留（`R-D1` 未清部分）。

### 六、并发写者文件未被卷入

- 工作树里三处**他人**的未提交条目（`apps/web/src/features/models/ModelDetails.tsx`、
  `packages/domain/model_drift.py`、`services/api/dto/models.py`）**不在**本 cycle 的改动集里
  ⇒ **未**被 `git add`、**未**被提交（`git diff --cached --stat` 逐条核对）。

## 附：m0 终态行

- **代管后的树**（`R-3` 的文件临时移出）：**`PASS: profile=m0; 23 deterministic checks`**
  （退出码 0，**首次即通过**；`PASS [` 行数 = **24**，即 23 项 + 计数之外的
  `release-assets-immutable`，符合 `LOCAL_GATE_POLICY` 的既有口径）。
  代管脚本逐字节复核**一致**：`size=69944` / `mtime_ns=1790187424185178900` /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`。
  日志：`scratch/goal016-c3-m0-quarantined.log`；
  轮次输出：`scratch/goal016-c3-m0-quarantine-run.txt`。
- **as-is 的树**：唯一预置红 = `framework/validate_bundle`（`R-3`），与本 cycle 改动无关。
- **口径**：代管后的终态行**不得**读成「as-is 本机全绿」。
- **记录时序声明**：本轮 m0 在**冻结树**上跑；本节的补写发生在该跑**之后**，属**只写记录**
  （不改判据 / 产品代码 / 门禁 / 依赖）。

## 结论

- **AC-1…AC-6 全部成立** ⇒ **GOAL-016 EC-03 = PASS**。
- **PASS_WITH_WARNINGS 的三条警告**：
  - **W-1｜4 条 high 只是告警面的 1/6**：`vite` 的 high 全清，但**剩余 19 条**
    （13 medium + 6 low）与 `undici` 的**主版本跳跃**都在**授权范围之外**
    ⇒ **不得**把本轮读成「依赖告警已清零」。
  - **W-2｜本机出厂端点 / 上游仍非确定**：cycle 2 登记的 **`W-7`** 继续有效
    （本 cycle 的 live e2e 与 m0 均依赖真实网络与真实凭据）；本 RECHECK **不**宣称
    「本机全量门纯离线」。
  - **W-3｜`R-3` 仍在**：as-is 本机 m0 的唯一预置红仍来自仓库外 / gitignored 的并发写者文件
    （`framework/validate_bundle`）；处置属 **D-10**（**需另行授权**），本 GOAL 只引用不改。
- **未改动**：产品代码、策略面、门禁、阈值、判据、运行时默认值。
- **本 cycle 是唯一动产品依赖的 EC**（D-03 明文）；其余 EC **不得**顺带动 pin。
