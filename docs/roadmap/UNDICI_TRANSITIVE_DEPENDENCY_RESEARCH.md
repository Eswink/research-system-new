# `undici` 传递依赖前置调研（`R-D1` / D-03 剩余面）

**状态**：调研结论，**可拍板**。**本文档不含任何升级动作**——没有 `pnpm` 字段、没有
`pnpm-lock.yaml` 改动、没有新增依赖。它只回答三个问题并给出依据。

- 建档：2026-09-26（GOAL-20260926-018 **EC-02**）
- 关联决策：`docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 的 **D-03**（依赖 pin 升级）
- 关联残余：`R-D1`（Dependabot 告警）
- 复现：见文末「复现命令」；所有数字都可由那些命令重新得出

## 0. 结论先行

| 问题 | 结论 |
| --- | --- |
| ① 上游 `@connectrpc/connect-node` 是否有带 `undici@6`+ 的版本？ | **1.x 全线没有**（`0.13.2`…`1.7.0` 都声明 `undici: ^5.x`）；**2.x 起彻底不依赖 `undici`**，但 2.x 是**破坏性主版本**（要求 `@bufbuild/protobuf 2.x` + `@connectrpc/connect 2.x`），且**父包不接受**它。⇒ **存在"无 undici"的上游版本，但升级面在本仓之外**（归属方 = `@cursor/sdk` 的维护方）。 |
| ② 用 pnpm `overrides` 强制提升是否安全？ | **技术可行、影响面极小（唯一入边 1 条、唯一用点 1 个 import），但越界且无行为收益**：它把 `undici` 提到父包声明区间 `^5.28.4` 之外，绕过上游的版本契约；而当前 Node（22.18.0）下 undici 的**唯一用点根本不可达**。⇒ **不推荐**在没有上游版本的前提下实施；若将来要实施，必须**单独授权** + 定向验证 + 逐字节回滚预案。 |
| ③ 不升的话，8 条告警的实际可利用性？ | **当前路径不可达**。依赖链末端只有**一个** in-repo 导入点（框架技能脚本），它导入 `connect-node` 后 undici 的唯一使用是 `node-headers-polyfill.js` 里的 `Headers`，而该赋值被 **`if (major < 18)`** 守卫——本机与 CI 的 Node 都是 **22.18.0** ⇒ **死分支**。8 条告警全部落在 undici 的**客户端 / fetch / WebSocket / cookie** 面，本仓**不调用**这些 API。**边界**：这是"当前不可达 + 影响面为开发期工具"的评估，**不是**"无风险"断言（见 §4.4）。 |

**本 GOAL（GOAL-20260926-018）对 D-03 剩余面的处置 = 维持现状（登记）**：`yaml` 已升
（EC-01，patch 到 `2.8.4`），`undici` **只调研不升**。要升 ⇒ 需**单独授权**（授权面见 §5.3）。

## 1. 事实底座

### 1.1 依赖链（实测 `pnpm-lock.yaml`）

```
@cursor/sdk@1.0.30                     ← package.json:28（根 devDependencies，精确 pin）
└── @connectrpc/connect-node@1.7.0     ← 声明 undici: ^5.28.4
    └── undici@5.29.0                  ← 8 条告警的载体
```

- `@cursor/sdk` **不在** web 应用的依赖里，也不在 `packages/` / `services/` / `adapters/` 的
  任何运行时装配里；
- `pnpm-lock.yaml` 中 `undici@5.29.0` 的**入边只有一条**
  （`'@connectrpc/connect-node@1.7.0(...)'` 的 `dependencies.undici`）⇒ **影响面 = 1 个包**；
- 本仓**没有**任何 `import "undici"` 或 `import "@connectrpc/*"`。

### 1.2 告警面（实测 Dependabot REST，2026-09-26）

`GET /repos/Eswink/research-system-new/dependabot/alerts?state=open` ⇒ **9 条**
（`undici` **8** 条 = 6 medium + 2 low；`yaml` **1** 条 = medium）。
留档：`scratch/goal018-gh-alerts.json`。`vite` 的 4 条 high 已由 GOAL-016 EC-03 清除。

| # | GHSA | 严重度 | 落在 undici 的哪一面 | 首个修复版本 |
| --- | --- | --- | --- | --- |
| 13 | `GHSA-2mjp-6q6p-2qxm` | medium | 请求/响应走私（客户端 dispatcher） | 6.24.0 |
| 14 | `GHSA-4992-7rv2-5pvq` | medium | `upgrade` 选项的 CRLF 注入（客户端） | 6.24.0 |
| 22 | `GHSA-35p6-xmwp-9g52` | low | keep-alive 复用导致的响应队列污染 | 6.27.0 |
| 24 | `GHSA-p88m-4jfj-68fv` | medium | `Set-Cookie` 百分号解码导致的头注入 | 6.27.0 |
| 25 | `GHSA-g8m3-5g58-fq7m` | low | `Set-Cookie` SameSite 属性降级 | 6.27.0 |
| 26 | `GHSA-8xcm-r25x-g524` | medium | retry interceptor 的响应失步 | 6.28.0 |
| 27 | `GHSA-v3r7-h72x-cjcm` | medium | cookie 属性注入（domain / setCookie 字段） | 6.28.0 |
| 28 | `GHSA-m8rv-5g2x-5cg5` | medium | blob-like body `type` 属性的 CRLF 注入 | 6.28.0 |

**注意**：`undici` 的**全部修复版本都 ≥ `6.23.0`** ⇒ **没有 `5.x` 的修复版本**
⇒ 修复必然意味着**跨主版本**（这正是不做"顺手升"的原因）。

### 1.3 唯一的运行时代码路径（实测 `node_modules`）

`@connectrpc/connect-node@1.7.0` 的 `dist/esm/index.js` 只为一个**副作用**导入
`./node-headers-polyfill.js`，而该模块对 undici 的引用**只有一行**：

```js
import { Headers as HeadersPolyfill } from "undici";
// ...
const [major] = process.versions.node.split(".").map((value) => parseInt(value, 10));
if (major < 18) {
    if (typeof globalThis.Headers === "undefined") {
        globalThis.Headers = HeadersPolyfill;
    }
}
```

⇒ **undici 的运行时使用 = `Headers` 一个符号，且赋值在 Node ≥ 18 下不执行**。

## 2. 问题①：上游是否有带 `undici@6`+ 的版本

### 2.1 答案：有"不带 undici"的版本，但不在本仓可达的版本线内

实测 `registry.npmjs.org/@connectrpc/connect-node`（33 个版本）的 `dependencies`：

| 版本线 | `undici` 声明 | 备注 |
| --- | --- | --- |
| `0.13.2` … `1.7.0` | `^5.23.0` / `^5.25.4` / `^5.26.2` / `^5.28.2` / `^5.28.3` / `^5.28.4` | **全线 `5.x`**；`1.7.0` 发布于 2025-09-08，是 1.x 的最后一版 |
| `2.0.0-alpha.1` | `^5.28.4` | 过渡版仍带 5.x |
| `2.0.0-beta.1` 起（含 GA `2.0.0`、最新 `2.2.0`） | **无 `dependencies`** | **完全不依赖 undici** |

**2.x 的 peer 要求（实测）**：

| 版本 | `peerDependencies` | `engines.node` |
| --- | --- | --- |
| `1.7.0` | `@bufbuild/protobuf ^1.10.0`, `@connectrpc/connect 1.7.0` | `>=16.0.0` |
| `2.0.0` | `@bufbuild/protobuf ^2.2.0`, `@connectrpc/connect 2.0.0` | `>=18.14.1` |
| `2.2.0` | `@bufbuild/protobuf ^2.7.0`, `@connectrpc/connect 2.2.0` | `>=22` |

而本树现锁 `@bufbuild/protobuf 1.10.0` + `@connectrpc/connect 1.7.0`。

### 2.2 三条可能的升级路径，逐条否定

- **路径 A：升 `@cursor/sdk` 到最新。** **无效**——`@cursor/sdk` 最新版 `1.0.32`
  （2026-09-22）**仍声明** `@connectrpc/connect-node: ^1.6.1` ⇒ 仍解析到 1.x ⇒ 仍带 undici。
  这条路径**无论升到哪个已发布版本都去不掉 undici**。
- **路径 B：直接把 `@connectrpc/connect-node` 提到 2.x。** **不可行**——`@cursor/sdk` 声明的是
  `^1.6.1`，2.x 落在它之外；而且 2.x 要求 `@bufbuild/protobuf 2.x` + `@connectrpc/connect 2.x`，
  本树锁的是 `1.10.0` / `1.7.0`（`@cursor/sdk` 把 `@bufbuild/protobuf` 精确 pin 在 `1.10.0`）
  ⇒ 这是一次**跨三个包的协同主版本迁移**，且**契约由 `@cursor/sdk` 持有**。
- **路径 C：上游改 `@cursor/sdk`。** 这是**唯一干净路径**：等（或要求）`@cursor/sdk` 发一版
  依赖 `@connectrpc/connect-node@2.x`（或干脆不再依赖它）。**归属方 = `@cursor/sdk` 的维护方。**

⇒ **可拍板结论①**：**"能在本仓完成的 undici 升级路径不存在"**；
真正能消掉这 8 条告警的动作发生在 `@cursor/sdk` 的上游。本仓可做的只有两种：
（i）**维持现状并登记**（本 GOAL 的处置）；（ii）**越界用 overrides 强提**（见 §3）。

## 3. 问题②：pnpm `overrides` 强制提升传递依赖是否安全

### 3.1 影响面（实测 = 极小）

- **受影响包数：1**（`@connectrpc/connect-node@1.7.0` 是 `undici@5.29.0` 的**唯一**入边）；
- **受影响代码点：1**（`node-headers-polyfill.js` 的一行 `import`，见 §1.3）；
- **不在任何产品构建产物里**（`@cursor/sdk` 是根 `devDependencies`，不进 `apps/web` bundle）；
- **不在 CI 执行面里**（`.github/workflows/` 无任何对 `@cursor/sdk` /
  `parallel-agent-orchestration` 的引用）；根 `pnpm run check` 只对它做 **prettier 格式检查**；
  真正 import 它的只有 `.cursor/skills/parallel-agent-orchestration/scripts/sdk-adapter.ts`，
  由 `pnpm run agents:parallel` 显式调用（**不属于任何默认门 / CI 作业**）。

### 3.2 两种 overrides 写法与差异

```jsonc
// (A) 全局：会命中所有使用者（本仓只有 1 个）
"pnpm": { "overrides": { "undici": "7.30.0" } }

// (B) 定向：只改 connect-node 这一条边；影响面最小，语义最清楚
"pnpm": { "overrides": { "@connectrpc/connect-node>undici": "7.30.0" } }
```

两者都需要把新解析结果写进 `pnpm-lock.yaml`（CI 用 `pnpm install --frozen-lockfile`
⇒ lockfile 必须随提交一起进仓）。

### 3.3 回归风险（逐条）

1. **绕过上游版本契约**：`^5.28.4` 的语义是"我知道并验证过 5.x"。强提到 6/7 属于
   **本仓单方面声明"我验证过"**——而验证面（§3.4）在本仓并不存在。
2. **主版本破坏性变更面未知**：5→6/7 的公开 API 变更清单**本仓没有验证过**。
   唯一已知的对照是：`require('undici').Headers` 在 `5.29.0` / `6.29.0` / `7.30.0` / `8.11.2`
   **都在**（`undici@6` 改了内部路径 `lib/fetch/headers` → `lib/web/fetch/headers`，但
   **公开导出名未变**）⇒ **该用点不会因 5→6 而消失**。这只是"不会立刻炸"，不是"没有回归"。
3. **Node engines 收窄**：`undici@6` 要 `node >=18.17`、`@7` 要 `>=20.18.1`、
   `@8` 要 **`>=22.19.0`**。本机与 CI 的 Node 都是 **22.18.0**（`.node-version`）
   ⇒ **`8.x` 会在 engines 上违约**；若将来真要提，**上限是 `7.30.0`**。
4. **未来的静默破裂**：`@cursor/sdk` 将来若升级并自带对
   `@connectrpc/connect-node` 的新约束，overrides 会**继续覆盖**它，冲突会以
   "SDK 行为异常"而不是"安装失败"的形式暴露。
5. **供应链副作用**：在告警面上，"用 overrides 消掉告警"会让
   `pnpm audit` / Dependabot 不再报告该包 ⇒ **告警消失 ≠ 风险已评估**；
   若不留下本文档这样的记录，会**掩盖**一个未验证的组合。

### 3.4 若将来授权实施，必须补齐的验证面（本 GOAL 不做）

- 逐项核对 5→7 的公开 API 差异清单，并**只在用点上**断言（`Headers` 存在且行为一致）；
- 真实跑一次 `pnpm run agents:parallel` 的 SDK 路径（需要 Cursor 侧凭据 ⇒ **属于另一类授权**）；
- 明确 engines 下限（`>=20.18.1`），并让 `.node-version` 与之一致；
- 把 overrides 的**理由与有效期**写进 `UPSTREAM_COMPONENTS.yaml` 的对应条目的 qualification 面。

### 3.5 回滚方式

1. 从 `package.json` 删掉 `pnpm.overrides` 条目；
2. **逐字节回滚 lockfile**：`git checkout -- pnpm-lock.yaml`（比重新解析更可靠——
   重新解析可能顺带移动别的解析结果）；
3. `pnpm install` 让 `node_modules` 回到 `undici@5.29.0`；
4. 复核：`grep -n "undici: 5.29.0" pnpm-lock.yaml` 命中**恰好 1 条**（且只在
   `@connectrpc/connect-node` 的依赖块里）。

⇒ **可拍板结论②**：overrides **技术可行、影响面极小、有明确回滚**，但它
（i）**越界**（把版本提到上游声明的区间之外）、（ii）在当前 Node 下**没有任何可观测的行为
收益**（唯一用点是死分支）、（iii）会让告警面**不再提示**这件事。
⇒ **不建议在没有上游版本的前提下实施**；要实施请按 §3.4 单独授权。

## 4. 问题③：不升的话，8 条告警的实际可利用性

### 4.1 谁在什么路径下调用 `connect-node`

| 环节 | 事实 |
| --- | --- |
| 谁依赖它 | `@cursor/sdk@1.0.30`（根 `devDependencies`，精确 pin） |
| 谁导入 SDK | **全仓唯一一处**：`.cursor/skills/parallel-agent-orchestration/scripts/sdk-adapter.ts`（该文件自述"The only module in the repository allowed to import `@cursor/sdk`"） |
| 谁触发它 | `pnpm run agents:parallel`（Cursor **框架技能**的命令行）；**不属于** m0 / CI / 默认门；CI 里对它的唯一动作是 **prettier 格式检查** |
| 产品面 | **不含**：`apps/web` 的依赖树里没有 `@cursor/sdk`，也没有 `undici` |

### 4.2 运行时可达到的 undici 面

- undici 的**唯一使用**是 `Headers`（§1.3），且**赋值被 Node 代际守卫拦住**：
  本机 `node --version` = **v22.18.0**，CI 用 `node-version-file: .node-version` = **22.18.0**
  ⇒ `if (major < 18)` 恒假 ⇒ `globalThis.Headers` 用的是 **Node 内建实现**，不是 undici 的。
- 8 条告警的**受害面**（§1.2 第三列）分别是：客户端 dispatcher（走私 / 失步）、
  `upgrade` 选项、`Set-Cookie` 解析、cookie 属性、retry interceptor、
  blob-like body 的 `type`、WebSocket 客户端。**本仓没有代码调用其中任何一个**
  （只有 `connect-node` 自己的内部实现会——而它的传输层走 `node:http2`，不走上表这些面）。

### 4.3 逐条可达性判定

| GHSA | 可达？ | 依据 |
| --- | --- | --- |
| `GHSA-2mjp-6q6p-2qxm` | **否** | 需要 `undici` 的客户端发请求；本仓不调用 |
| `GHSA-4992-7rv2-5pvq` | **否** | 需要 `upgrade` 选项 |
| `GHSA-35p6-xmwp-9g52` | **否** | 需要 keep-alive 连接复用 |
| `GHSA-p88m-4jfj-68fv` | **否** | 需要 `Set-Cookie` 解析（fetch cookie 面） |
| `GHSA-g8m3-5g58-fq7m` | **否** | 同上 |
| `GHSA-8xcm-r25x-g524` | **否** | 需要 retry interceptor |
| `GHSA-v3r7-h72x-cjcm` | **否** | 需要 cookie 属性处理 |
| `GHSA-m8rv-5g2x-5cg5` | **否** | 需要 blob-like body |

### 4.4 诚实边界（不得省略）

1. `import` 语句是**求值**的：`connect-node` 被导入时，undici 的 `index.js`（及其模块图）**会
   被加载**。判定的依据是"**8 条告警都不是 import 期缺陷**"，而不是"undici 没被加载"。
2. **本评估不构成"无风险"断言**。它只说：在**当前 Node 版本 + 当前调用路径**下，
   这 8 条的**触发面不可达**；若将来（i）Node 降到 < 18、（ii）本仓开始直接调用 undici 的
   客户端 API、（iii）`connect-node` 改成实际使用 undici 做传输——三条任一成立，
   **本评估立即失效**。
3. 与 `R-M1` 同类约定：**不得**据此宣称"项目安全"。hook 侧（Mimosa）的完整结论仍未有。
4. `undici-types@6.21.0`（lockfile 里另一个含 "undici" 的条目）来自 `@types/node`，
   是**纯类型包**，与这 8 条告警**无关**——不要把它混进来数。

⇒ **可拍板结论③**：**8 条告警在当前树与当前 Node 下不可达**；
风险敞口是"开发期框架工具的一条未被上游验证的依赖边"，**不是产品运行时风险**。

## 5. 可拍板结论与建议

### 5.1 选项

| 选项 | 内容 | 代价 | 本 GOAL 是否可取 |
| --- | --- | --- | --- |
| (a) | **维持现状并登记**（告警面继续显示 8 条，本文档作为记录） | 告警面长期挂 8 条 | **✅ 本 GOAL 的处置** |
| (b) | **pnpm overrides 强提**到 `7.30.0` | 越界 + 未验证 + 掩盖告警（§3.3） | ❌ 需单独授权 |
| (c) | **向上游要一版**（`@cursor/sdk` 改依赖 `connect-node@2.x`） | 等待外部；本仓不可控 | ⏳ 可登记为诉求，不在本仓实施 |
| (d) | 移除 `@cursor/sdk` 依赖 | 会废掉框架技能 `parallel-agent-orchestration` | ❌ 与框架面冲突 |

### 5.2 建议

**取 (a) 维持现状**，并把 (c) 登记为**外部诉求**（这 8 条告警的根因在 `@cursor/sdk` 的依赖声明，
本仓无论怎么改都只能"越界绕过"而不能"正确修复"）。若告警面需要一块干净的判词，
本文档即是：**"8 条 = 1 条未验证的开发期依赖边 + 当前不可达"**。

### 5.3 若将来要升，需单独授权的清单

- 授权面：`pnpm.overrides` 的**具体条目**（建议定向写法 §3.2 (B)）+ 目标版本（**上限 `7.30.0`**）；
- 必跑：`pnpm install` → 全量 web 门 + m0 + `pnpm run check`；
- 必查：`require('undici').Headers` 仍存在且行为一致（唯一用点）；
- 必做：`UPSTREAM_COMPONENTS.yaml` 里该条的 qualification 面记下"越界强提 + 有效期"；
- **回滚**：按 §3.5 逐字节回滚。

## 6. 复现命令

```bash
# 依赖链与唯一入边（应当恰好命中 1 条，且位于 connect-node 的依赖块内）
grep -n "undici: 5.29.0" pnpm-lock.yaml

# 本仓是否直接导入 undici / connectrpc（应当无输出）
grep -rn "from \"undici\"\|from \"@connectrpc" --include=*.ts --include=*.tsx apps packages services adapters tests

# connect-node 里 undici 的唯一用点
cat node_modules/.pnpm/@connectrpc+connect-node@1.7.0*/node_modules/@connectrpc/connect-node/dist/esm/node-headers-polyfill.js

# Node 版本（决定 `if (major < 18)` 是否为死分支）
node --version && cat .node-version
```

上游元数据（只读）：

```bash
curl -s https://registry.npmjs.org/@connectrpc%2Fconnect-node | python -c "import json,sys; d=json.load(sys.stdin); [print(v, d['versions'][v].get('dependencies'), d['versions'][v].get('peerDependencies'), d['versions'][v].get('engines')) for v in ('1.7.0','2.0.0','2.2.0')]"
curl -s https://registry.npmjs.org/@cursor%2Fsdk | python -c "import json,sys; d=json.load(sys.stdin); [print(v, (d['versions'][v].get('dependencies') or {}).get('@connectrpc/connect-node')) for v in ('1.0.30','1.0.31','1.0.32')]"
```

告警面（只读，需令牌）：

```bash
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/Eswink/research-system-new/dependabot/alerts?state=open&per_page=100"
```
