---
id: MEM-20260926-148
title: "认证运维面：把「401 是否正常」写成四步判据 + 部署面只给检查项并如实登记不可验证"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-198-auth-ops-face-enable-rotate-disable-and-401-verification.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-199-auth-ops-face-recheck.md
supersedes: []
tags: [auth-ops, 401-verification, deployment-face, goal-020, ec-03, windows-of-judgement]
---

## 做了什么

给控制面写面认证补上**运维面**（GOAL-020 EC-03）：**开启 / 轮换 / 关闭 / 验证 401 / 部署面**
五个面写进三处文档（`docs/integration/LIVE_MODEL_RUNBOOK.md` §2.2/§2.3、
`docs/security/IDENTITY_AND_ACCESS.md`、`docs/api/CONTROL_PLANE_API.md`），
`THREAT_MODEL.md` §6.7 同步一条；并用真实进程**实测**了 401 验证步骤。

## 为什么这样做

### 1. 「401 是否正常」必须是**判据**，不是感觉

认证开启后「写被拒」有两类原因：**认证生效**，或**别的错**（载荷非法 / 路径写错 /
服务没起来）。四步把它分开：

| 步骤 | 请求 | 期望 | 不是期望值说明什么 |
| --- | --- | --- | --- |
| ① | `GET /health` 不带 token | **200** | 读面被拦 ⇒ 与口径不符（不是认证问题） |
| ② | `POST /projects` **不带** token | **401** + 点名缺头 | 写面未被保护 ⇒ 确认进程读到变量（须重启） |
| ③ | `POST /projects` **带错** token | **401** + 点名不匹配 | 同上 |
| ④ | `POST /projects` **带对** token | **2xx** | 认证已放行、被**别的**规则拒（如 422）⇒ 改请求 |

**实测口径（本机，真实进程）**：关闭态 **200 / 201 / 警告在场**；
开启态 **200 / 401 / 401 / 201**，两个 401 的 `detail` **各自点名成因**。

**驱动侧两个坑（都踩过）**：①探针发**空载荷** ⇒ 关闭态得 **422**（载荷非法），
把「认证是否放行」与「载荷是否合法」混在一起 ⇒ 必须发**合法**载荷；
②按大写 `Bearer` 匹配正文，而正文是小写 `bearer` ⇒ **断言两个拒绝的成因各自被点名**，
不要匹配某一个词的大小写。

### 2. 部署面：**给检查项**与**给结论**是两件事

认证在**进程内**实现；前面有反代 / TLS / 多副本时，「谁在调用」多出几个**本仓没有验证面**
的变量。因此本节只给**四条检查项**，其中两条**必须**如实登记为**本机不可验证**：
①反代透传 `Authorization`（两个信任域不得共用同一个头）；②TLS 在反代终止
（bearer 凭据在明文 HTTP 上等于公开）；③多副本须同值（本实现无共享会话 ⇒ 不一致表现为
**间歇 401**，**未实测**）；④反代 / TLS / 多副本行为**未验证**。
⇒ **收口「未验证」残余的正确形态 = 可复核的检查项 + 明确的未验证声明**，
**不是**把它写成已验证。

### 3. 既有文档判据的**有界观察窗**约束

`test_control_plane_auth_same_source.py` 对每份文档要求「自己的未覆盖锚点 + 自己的必需措辞」，
且**观察窗只有 1200 字**（从锚点起算）。实测 `THREAT_MODEL.md` §6.7 的必需措辞
`零夸大` 落在 **offset 1054** ⇒ 在它**之前**加长会把该措辞挤出窗口、判据**假红**。
⇒ 本轮的追加一律放在该措辞**之后**（新增 5 行仍让 offset 1054 < 1200）。
**这是一条通用形状**：判据用**有界窗**锚定声明附近时，新增内容要挑**不把必需措辞推出去**的位置。

## 怎么做与复现

```bash
# 401 验证实测（真实进程；token 现场生成、只走 env、不落盘）
uv run --frozen --no-sync python -B scratch/goal020-ec03-401-verification.py
# 文档同源判据（必须零改动且全绿）
uv run --frozen --no-sync python -B -m pytest \
  tests/architecture/python/test_control_plane_auth_same_source.py \
  tests/architecture/python/test_runbook_same_source.py -q
```

## 适用边界

- **本轮没有把部署面变成已验证**：只把「未验证」写成**可复核的检查项**；
  要变成已验证需要真实部署拓扑（本机没有）。
- **runbook 的 `## 1.`…`## 5.` 五个节名是冻结的**（既有判据逐字断言）⇒ 新增内容
  只能走 `###`；新出现的反引号**环境变量名**必须真实存在于代码里。
- **不得**把运维文档读成安全结论；`R-M1` 未收口。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-198-auth-ops-face-enable-rotate-disable-and-401-verification.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-199-auth-ops-face-recheck.md`
- 脚本：`scratch/goal020-ec03-401-verification.py`（+ `scratch/goal020-ec03/401-verification-summary.json`）
- 相关记忆：`MEM-20260926-147`（前端凭据面）、`MEM-20260926-146`（记录面覆盖）、
  `MEM-20260926-144`（同源文档需要可按压的声明句）
