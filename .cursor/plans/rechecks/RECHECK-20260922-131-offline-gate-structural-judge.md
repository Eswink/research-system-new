---
id: RECHECK-20260922-131
plan_id: PLAN-20260922-131
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-22
completed_at: 2026-09-22
reviewer: independent-subagent-pass + root-agent-goal-010-ec05
baseline_ref: 99783e4
checked_head: 本次收口提交（WP2/WP3 + 判据本体 + 本 RECHECK + EC-05 置 PASS 同一次提交落地）
---

# RECHECK-20260922-131 — 默认门离线的整轮结构判据（GOAL-010 EC-05）

## 检查范围

**不采信实施叙述**：从 GOAL-010 里 EC-05 的**原始判定细则**重新核对（不是从 PLAN-131 的叙述）：

1. 判据**存在且是结构判据**：默认路径/默认测试里「出站发生 ⇒ 红」，**不依赖人工观察**。
2. **被压过**：构造一次真实出站 ⇒ RED；复原 ⇒ GREEN；两向都留证。
3. **不得**用「本轮没观测到出站」充当判据；**不得**改成「把凭据清空」这类**依赖环境**的弱化形态。
4. PLAN-131 自己的 AC-1…AC-6（整轮覆盖 / 不依赖环境 / 反证成对 / 不误伤既有套件 /
   口径单一来源 / 门禁与记录）。
5. 另加：**判据不得放宽任何既有断言**（改 validator / 门禁 / 快照 / 断言强度以凑绿）。

## 检查方式

**两遍独立复检**（第一遍在判据落地后、第二遍在按第一遍结论修完之后），由**独立子代理**执行：
不采信本记录与 PLAN 的叙述，自己读源码、自己跑命令、自己做按压，并报告**它自己**看到的原始输出。
两遍都要求：可证伪的具体尝试 + 未验证项清单 + 工作树残留清单。

## 检查结果

### 1. 判据在、且判的是「发生」不是「形态」（两遍都确认）

| 面 | 事实 | 证据 |
| --- | --- | --- |
| 拦截点 | `socket.socket.connect` / `connect_ex` **与**两个具体事件循环类的 `sock_connect` | 独立身份检查：`armed` 后三个对象都指向判据模块的函数 |
| 分类单一来源 | `endpoint_policy.destination_kind`（`return _host_kind(host)`，语义零改动） | 全仓只有一处分类实现；`endpoint_policy.py` diff 为 **+11/-0 纯加性** |
| 放行面 | 只有 `requires_live_llm` marker；无当前用例（收集期/导入期/用例外）**默认拒** | 判据模块内 **零** `os.environ`/`getenv`（独立 `rg` 复算） |
| 两条机制 | **拦**（发数据包之前抛）+ **判**（`pytest_sessionfinish` 按记录把整轮判红） | 第二遍实测：一条被**吞掉**的异步阻断仍让整轮红（`1 passed` 但 **exit 1**） |

### 2. 实测抓到的真实出站（本循环最重要的产出）

判据上线当天，全量默认门里出现一条**真实的收集期出站**：`BLOCKED 198.18.0.59:443 by <outside-a-test>`。
独立复检**自己重跑**并确认因果链：`tests/adapters/openhands/test_adapter_core.py:5`（模块级
`import openhands.sdk`）→ … → `litellm/__init__.py:520` → `get_model_cost_map()` →
`fetch_remote_model_cost_map()` → `httpx.get(<raw.githubusercontent.com 的 cost map>)`。
两向复测（同一棵树，只切一个开关）：置 `LITELLM_LOCAL_MODEL_COST_MAP=True` ⇒ `judged 0`/`blocked 0`/exit 0；
置 `False` ⇒ `judged 1`/`blocked 1`/exit 1 且归因点名 `test_adapter_core.py:5:<module>`。
**结论**：默认门（以及 CI）在**收集期**一直真的出网；判据是**唯一**发现它的东西。

### 3. 第一遍复检抓出的**洞**（W-1，已在同一循环内修掉并被第二遍复验）

第一遍复检**证伪**了当时的头号命题（「任何非环回出站都会让整轮红」）：
`asyncio.open_connection(<LAN IP>)` 在判据武装状态下 **成功握手**且 `judged 0`——Windows 的
Proactor 循环走 `IocpProactor.connect` → `_overlapped.ConnectEx`，**一次都不经过** `socket.socket.connect`。
仓内 `adapters/mcp/transport.py` 正在这条线上。⇒ 判据补**异步面**。

修完第二遍复检复验（同类尝试全部改判）：

```
your W-1 repro (LAN IP, armed) : PublicNetworkBlocked + record(target/kind/origin) + blocking_failures 非空
selector loop (forced)         : PublicNetworkBlocked
anyio connect_tcp (he=True/False): 阻断（ExceptionGroup 包着）
httpx.AsyncClient              : 阻断；**环回正对照 200**
aiohttp                        : PublicNetworkBlocked
```

### 4. 第二遍复检的新发现（W-8）与处置

第一版补的异步拦截装的是**抽象基类** `asyncio.events.AbstractEventLoop`——复检指出并实测：
那份是 `raise NotImplementedError` 桩，**对实际循环不可达**（`AE patch reachable: False`），
selector 循环当时只是**被同步面兜住**。⇒ 改成装两个**具体实现**（`BaseSelectorEventLoop` +
`BaseProactorEventLoop`），并补一条**行为**判据（selector 循环上的异步连接必须被拦下）。

**本 RECHECK 自己按压这个修复**（W-8 的错版复现）：把类表临时改回「只装抽象基类」⇒
**4 个用例真 FAILED** 并打出 `judged 3`/`blocked 0`（异步尝试根本没进判定）；复原 ⇒ 28 passed。

### 5. 反证成对与按压（本 RECHECK 的独立证据）

| 按压 | 结果 |
| --- | --- |
| 撤防同步面（`disarm()`） | 证物用例 RED |
| 临时停用会话级红灯 + 吞掉异常的出站 | **用例全绿但 exit 0**（= 修之前的形态） |
| 恢复会话级红灯 + 同一发 | **用例仍绿但 exit 1**（判据按记录判红） |
| 异步面 armed→disarmed→re-armed | `BLOCKED` ⇒ `reached the wire: connected (!!)` ⇒ `BLOCKED` |
| W-8 错版 | 4 个用例 RED |

**如实更正的判断**：derive 稿与 P-1 曾写「撤防后也不会真出网（地址不可路由）」——**错**。
独立复检与本人实测都确认：本机 fake-IP/TUN 代理对**任意** IP 秒回连接
（`192.0.2.x` / `198.51.100.x` / `203.0.113.1` / `1.1.1.1` 全部 0.02s CONNECTED）。
⇒ 撤防类按压**必然**产生一次受控出站；证物「不真出网」的唯一保证是**判据先于 SYN 拦下**。
该更正已写回 PLAN（M-8 / P-1）、判据注释与 `MEM-20260922-104`。

### 6. 不误伤既有套件（AC-4）

- 独立复检跑**全量默认门**：`4142 passed / 209 skipped`，`judged 652`、`blocked 5`（**5 条全部是
  判据自证探针**），exit 0。
- 异步面落地后，独立复检另跑三套真实异步套件：`tests/tooling/test_loopback_proxy.py` 8 passed、
  `tests/contracts/test_tool_provider_contract.py` 18 passed（streamable-HTTP MCP over loopback），
  均 `blocked 0`；并给出环回正对照（`httpx.AsyncClient` 对环回 mock 返回 200）。
- 本人定向：`tests/architecture/python/test_dependency_boundaries.py` 2 passed（判据引入的
  `packages` 导入未越界）。

### 7. 没有放宽任何判据（AC-5 / 范围第 5 条）

- 独立复检的 `git diff --numstat` 与 `--diff-filter=D` 复算：**零删除**；`tests/e2e/` 里既有的
  逐用例「关闭门不得开 socket」断言**原样未动**；没有改 validator / 门禁 / 快照 / 测试断言来凑绿。
- 分类语义复用既有唯一实现；`Domain` 一字未动；产品源码零改动。

## 结论

**PASS_WITH_WARNINGS。** EC-05 的两条核心命题（**结构判据存在**、**被压过**）都成立，
且比原计划更强：判据不仅被按压，还**在真实运行里抓到并定位了一条谁也没想到的收集期出站**
（litellm 导入期拉 cost map），并暴露了 Windows 异步栈这个**逃逸面**（W-1，已修并复验）。

## 警告（W 列表）

| # | 严重度 | 内容 |
| --- | --- | --- |
| W-1 | 已修（第一遍复检发现） | Windows Proactor 循环绕开 `socket.socket.connect` ⇒ 异步出站完全不可见。已补异步面并被第二遍复验（selector/anyio/httpx-async/aiohttp 全阻断，环回正对照通过） |
| W-2 | 登记（不修） | **环回转发代理**是判据的盲区：`HTTP(S)_PROXY=http://127.0.0.1:...` 时目的地确实是本机（复检实测本地监听器收到 `GET http://example.invalid/ping`）。已写进判据 docstring 与 PLAN R-5；要覆盖需在应用层判，另行设计 |
| W-3 | 登记 | 会话级红灯的**端到端**链路由外部探针证明（套件内用新守卫 + 桩会话压钩子；异步证物用豁免探针地址）——套件内没有「真·整轮 + 异步 + 红」的合一用例 |
| W-4 | 登记 | 判据武装与 litellm 开关都在 **conftest 导入期**生效，晚于 `-p` / `PYTEST_PLUGINS` / pytest11 entry points；第三方插件若在导入期出网会先于判据（本机只装了 anyio 插件） |
| W-5 | 登记（live 面） | plugin 钩子按注册**逆序**执行 ⇒ `guard.leave()` 早于 fixture teardown；live 用例若在 teardown 出网会被判红（fail-closed，但会误伤 live 跑的收尾） |
| W-6 | 登记 | 进程若不走 `pytest_sessionfinish`（硬杀 / `os._exit`）则不判红；rootdir 不含 `tests/` 的调用不加载判据（该形态在 E-5 已声明不在射程） |
| W-7 | 登记（射程） | `getaddrinfo` / UDP / 子进程 / 非 python 作业不在射程；`asyncio.open_connection("hostname", …)` 的 DNS 查询发生在被判定之前 |
| W-8 | 已修（第二遍复检发现） | 第一版异步拦截装的是**抽象基类**（`NotImplementedError` 桩，对实际循环不可达）⇒ 改装两个具体实现 + 补 selector 行为判据；错版按压 ⇒ 4 个用例 RED |
| W-9 | 登记 | 套件内 `guard.disarm()` 的按压用例靠 `finally` 复原；硬杀进程会让该次会话余下部分**无守卫** |
| W-10 | 登记（工具面） | `validate_bundle.py` 的「旧项目版本引用」正则会把 RFC 5737 TEST-NET-1 地址读成旧版本号（本循环只**绕开**，不改门禁） |
| W-11 | 登记（工具面） | `.cursor/runtime/evolution_state.json` **无跨进程锁**：两次并发调用 framework evals ⇒ `WinError 5` / eval 失败（已复现）；**m0 必须独占运行** |
| W-12 | 登记（纠正） | derive 稿与 P-1 的「撤防后不会真出网」经实测**证伪**（本机代理对任意 IP 秒回）；撤防类按压必然产生受控出站，已更正记录 |
