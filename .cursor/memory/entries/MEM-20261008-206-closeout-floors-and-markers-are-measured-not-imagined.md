---
id: MEM-20261008-206
title: "收口断言的下界与标记形态必须取实测：不可满足的下界让判据永红，裸子串标记会被无关字符串喂饱"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-335-goal-036-ec05-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-336-goal-036-ec05-self-bootstrap-closeout.md
supersedes: []
tags: [closeout-assertions, judge-design, false-green, goal-036]
---

## 做了什么

GOAL-036 收口时新写的断言集里，两处**起草缺陷**在编入树之前被门链自己抓到（同一中间态
`65 PASS / 6 FAIL` 逐条报出）：

1. **例数下界取了未实测的数**：`CASE_FLOORS` 给既有夹具面
   `tests/adapters/canonical/test_canonical_read_provider.py` 写了 `10`，实测该文件
   **7** 个用例 ⇒ 这条断言**在任何树上都判红**（不可满足的下界 = 判据永红，与「防删减」
   的意图完全相反）。
2. **残余标记用了裸子串**：`RESIDUAL_MARKERS = ("M-1", …, "M-5")`，而 `M-1` / `M-2`
   是 `MEM-160` / `MEM-20261008-197` 的**子串**（`MEM-1` / `MEM-2`）⇒ 在**一条残余都没写**
   的中间态上，`residuals-enumerated` 判**绿**（假绿），另三条 `M-3`…`M-5` 判红。

## 为什么这样做

两条是同一类错误的两面：**判据的「形状」必须取自实测，而不是想象。**

- 下界的方向：下界不是「越大越严」—— 大于实测值的下界把「防删减」偷换成「永远红」，
  而永远红的判据在实践中会被当成噪声绕过（等于**零**防护）。
  正确的下界 = **当场实测的例数**（只防掉下来）。
- 标记的方向：标记串必须**在受判面里有唯一身份**。裸 `M-1` 撞上 `MEM-160` 是**构造性**的
  （`MEM-<数字>` 的分隔符正好是 `-`，于是 `MEM-160` 含 `M-1`）—— 这种命中与「残余写没写」
  无关，所以它把判据喂饱成了恒真。带回引号的 `` `M-1` `` 才是「登记形态」而不是「碰巧的
  子串」；同一收紧后，未写残余的中间态**逐条判红**（可证伪性当场恢复）。

## 怎么做与复现

两条都可被单变量按压：

```bash
# ① 下界：把下界改回 10（不可满足）⇒ 该条永久 FAIL；改回实测 7 ⇒ 恢复可判
uv run --frozen --no-sync python -B tools/verify_goal036_closeout.py --root . --verdict-only \
  | grep "cases-"
# ② 标记：把 RESIDUAL_MARKERS 改回裸子串、并删掉 GOAL 里的残余条目 ⇒ 仍 PASS（假绿）；
#    改回回引号形态 ⇒ 同一棵树当行 FAIL（并列出全部缺失标记）
```

写新断言集的顺序建议：**先跑一次中间态**（本 GOAL 的形态 = 记录未写、归档未生成），
把每条 FAIL 逐条归因（是「该红」还是「起草错」）；不可满足的下界与恒真标记都会在这一步
现形（前者是「该绿的红了」，后者是「该红的绿了」）。

## 适用边界

- 适用于**收口断言集 / 门禁脚本**这一类「机械判据」的起草与修订。
- 不适用于「受判面本身就是计数语义」的断言（那种下界另说，见
  `tests/architecture/python/test_delivery_semantics_wording.py` 的豁免表形态）。
- 子串命中的风险与**文本空间**有关：新增标记词时应先 `rg` 一遍它是不是别的登记串的子串
  （本仓的 `MEM-<数字>` / `PLAN-<数字>` 是常见撞点）。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-335-goal-036-ec05-self-bootstrap-closeout.md`
- `.cursor/plans/rechecks/RECHECK-20261008-336-goal-036-ec05-self-bootstrap-closeout.md`
- 取证：`tools/verify_goal036_closeout.py` 的起草中间态读数 `65 PASS / 6 FAIL`
  （逐条归因见 RECHECK 第 1 节）
