---
id: MEM-20260920-087
title: "framework/validate_bundle 会扫全树 .py（含 gitignored scratch/）找旧协议版本号（v0.2.x / v0.3.x 形态）——IP 字面量 TEST-NET-1 网段会命中并被报成旧版本引用"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.95
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-114-anthropic-protocol-execution-path.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-114-anthropic-protocol-execution-path.md
supersedes: []
tags:
  - gates
  - validate-bundle
  - false-positive
  - scratch-dir
  - m0
---

# 旧版本号扫描会把 TEST-NET 网段当版本号（GOAL-20260920-008 / cycle 1）

## 做了什么

本轮的本地工具 `scratch/ci_poll.py`（gitignored，用 GitHub REST API 查 CI）里有一个 SSRF
阻断网段表，其中 TEST-NET-1 网段（`192.0.2.x/24`）命中 `framework/validate_bundle` 的
**旧项目版本引用** 正则，整条 m0 判红：

```text
FAILED [framework/validate_bundle]: exit 1
验证失败:
- 发现旧项目版本引用: scratch\ci_poll.py
```

## 为什么这样做（可复用结论）

1. **扫描射程**：`validate_bundle.py::repository_files()` 用 `os.walk(ROOT)` 遍历**整棵树**，
   只排除 `NON_SOURCE_DIRS`；`scratch/` **不在**排除名单里 ⇒ **gitignored 的临时脚本同样参与
   治理门禁**。把一次性工具丢进 `scratch/` 并不能让它免检。
2. **触发模式**：`re.compile(r"(?<![0-9])v?(?:0\.2\.[0-9]+|0\.3\.0)(?![0-9])")`，扫描后缀
   `.md/.mdc/.yaml/.yml/.json/.py/.txt`。它的 lookbehind 只排除**数字**，所以
   TEST-NET-1 网段里的第二个八位组（前面是 `.`）**会命中**；`0.0.0.0/8`、`10.0.0.0/8`
   之类的常见网段字面量不会。
3. **处置（反更严，不是绕门）**：把显式网段表改成「显式网段 + 地址分类兜底」
   （`is_private / is_reserved / is_loopback / is_link_local / is_multicast / is_unspecified`），
   于是 TEST-NET-1 地址判红、代理 fake-IP 段单独豁免。改完反而比原来更严。
4. **一般化**：任何写进仓库树（含 `scratch/`）的文件都可能被 `validate_bundle` 扫到——
   引入 IP 字面量、示例版本串、第三方文档片段时先想一下这个正则。

## 怎么做与复现

```sh
# 复现误判：任意 .py/.md 里出现 TEST-NET-1 网段字面量（或其它含旧版本号形态的片段）
python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py
#   → 验证失败: - 发现旧项目版本引用: <该文件>

# 触发它的正则（validate_bundle.py 约第 277 行）
# (?<![0-9])v?(?:0\.2\.[0-9]+|0\.3\.0)(?![0-9])
```

**当轮处置（照抄这个方向）**：不要为了过门而删掉安全网段——
把网段表换成「显式网段 + `ipaddress` 地址分类兜底」（`is_private` / `is_reserved` /
`is_loopback` / `is_link_local` / `is_multicast` / `is_unspecified`），再对确需豁免的段
（如本机 DNS 代理的 fake-IP `198.18.0.0/15`）单独放行。结果比原来更严：
TEST-NET-1 地址判红、`127.0.0.1`/`10.x`/`169.254.x` 判红。

**写文档时同样要注意**：本记忆条目自身也曾因此判红——凡是要写出这类网段字面量的地方，
用 `192.0.2.x` 这种**不带完整数字段**的写法，或直接用「TEST-NET-1 网段」描述。

## 适用边界

- 适用于**本仓 m0 的 `framework/validate_bundle` 门**；扫描后缀 `.md/.mdc/.yaml/.yml/.json/.py/.txt`，
  排除 `NON_SOURCE_DIRS` 与 `runtime/`、`.cursor/plans/archive/`，**不排除 `scratch/`**。
- 误判只发生在**字面量恰好含旧版本号形态**时（TEST-NET-1 网段即属此列）；
  `0.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12` 之类不受影响。
- 不要据此把文件挪出树来"过门"——`scratch/` 参与门禁是设计使然；要么改写法，要么确认该文件
  确实不该留在树里。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260920-114-anthropic-protocol-execution-path.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-114-anthropic-protocol-execution-path.md`（G4）
- 代码：`.cursor/skills/system-spec-check/scripts/validate_bundle.py`（`repository_files` / 旧版本正则）、
  `scratch/ci_poll.py`（当轮的触发文件）
