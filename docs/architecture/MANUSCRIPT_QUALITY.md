# 手稿的叙述质量与事实一致性口径（本仓**判什么 / 不判什么**）

> 权威实现：`packages/application/deliverable/manuscript_quality.py`
> 判据：`tests/application/test_manuscript_quality.py`
> 引入轮次：GOAL-20261030-101 EC-01（承 GOAL-096 `U-1` → 097 `U-2` → 099 `W-5` →
> 100 `U-2` **连续四轮**登记的同一未覆盖项）
> 调用点：`packages/application/deliverable/manuscript.py::validate_manuscript`
> （手稿装配的**唯一**结构入口 ⇒ 判据不是死代码）

## 1. 这份文档为什么存在

`validate_manuscript` 此前判四件**结构事实**：

1. 八个叙述键齐备且非空；
2. 正文不含任何 Unicode 十进制数位（引用标记 `[n]` 除外）；
3. 引用编号不越界；
4. 没有「列了却从不被引」的孤儿条目。

这四条钉住的是**「谁写的」「数字在哪」「编号是否闭合」**。它们**一个字都不判**
「这段写得对不对」，也不判「`[2]` 是不是真的支持那句话」。本文件把这件长期空白
写成一个**明确、可机械判、且自带射程边界**的口径 —— 而不是继续留白。

**设计原则：必要不充分。** 三条判据每条都封一个**具体且已发生过**的失败形态。
过不了 ⇒ 一定是错的；过了 ⇒ **不代表对**。这个方向的不对称是本设计的全部价值。

## 2. 判什么（三条）

### 2.1 引用—主张**相关**（`check_citation_alignment`）

**规则**：`Results` 节至少带一个 `[n]`，且**每一个被引条目**的 `title` 与正文
（八节合计）**共享至少一个实词**（去停用词、小写、长度 ≥ 3 的英文词；连字符算同一个词）。

**封住的失败形态**：编号对、条目在表里、但引的是**另一篇**（模型自己数编号时系统性
错位 —— GOAL-099 `W-1` 的邻居形态）。

**边界（合约给的正例，不是豁免）**：本 run 一条可引用记录都没有时，`titles` 为空 ⇒
本判据**没有对象**，直接通过。合约 `research_manuscript` 的 HARD RULE 2 末句逐字允许
「write the body without citation marks」；此时判红等于逼模型编造一条文献。

### 2.2 节间不自我重复（`check_section_distinctness`）

**规则**：`abstract` 与 `conclusion` 的**归一化句子集合**不得有交集。归一化 = 小写 +
压缩空白 + NFKC + 去首尾标点。

**封住的失败形态**：一句话在两个总结面里原样出现两次（模型偷懒的典型形态 —— 两个面
本该说不同的事：摘要说做了什么，结论说这意味着什么）。

**边界**：只判**逐字（归一化后）相同**的句子。**同义复述不判**（需要语义等价判定）。

### 2.3 节非空洞（`check_section_depth`）

**规则**：每一节（`title` 除外）的词数 ≥ **8**。

**阈值从哪来（不许拍脑袋）**：三套受控夹具的八节词数实测为

| 夹具 | abstract | introduction | related_work | methods | results | discussion | conclusion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| e2e `direction_to_manuscript_support` | 32 | 24 | 33 | 28 | 39 | 29 | 24 |
| `test_manuscript_assembler` | 16 | 20 | 29 | 25 | 21 | 23 | 17 |
| `test_manuscript_assembly` | 11 | 9 | 11 | 13 | 12 | 12 | 11 |

**实测下界 = 9 词**（`test_manuscript_assembly` 的 introduction）⇒ 阈值取 **8**，
比任何一份夹具的最短节都低。取值理由：只抓「写了几个词就当写完了」这一类，
**不惩罚简洁**。若把阈值抬到 9 以上，三套真夹具会一起判红 —— 那是阈值失控。

**封住的失败形态**：模型漏答一节、只回一两个词。

## 3. **不判什么**（射程边界 —— 本文件最重要的一节）

以下全部在**射程之外**。它们实现于 `manuscript_quality.NOT_JUDGED`，由判据
`test_the_quality_module_declares_what_it_does_not_judge` 钉住逐条在场：

| 不判 | 为什么判不了 |
| --- | --- |
| **`[2]` 是否**支持**了那句话** | 词重叠只说「引的条目与正文**不是无关**」。一篇讲 reproducibility 的文献与一段讲 reproducibility 的正文共享该词，但正文那句话可能**恰好相反**。判「支持」需要语义蕴含。 |
| **论证是否成立** | 前提是否足够、推断是否有效、结论是否被数据支撑 —— 全部需要人评或模型评。阶梯「报告」域的 `下一级`（「叙述质量与事实一致性可判」）**因此仍未达成**。 |
| 方法学是否合适 | 臂选得对不对、指标测没测到想测的东西 —— 需要领域知识。 |
| 引用是否充分 | 一个主张该引 3 篇而只引 1 篇，本套判据**看不见**。 |
| 文风 / 可读性 / 语法 | 不在「事实一致性」范围内。 |
| 跨 run 的结论一致性 | 手稿只覆盖**本 run**（见制品脚注的原话）。 |

**反向误读是明令禁止的**：「词重叠通过」**不得**被读成「引用支持了主张」；「解析没红」
**不得**被读成「叙述质量已判」。这两条写在每个 GOAL 的 `fix_policy.forbidden` 里。

## 4. 为什么这三条值得做（而不是「判不全就不判」）

| 判据 | 封住的形态 | 若不做会怎样 |
| --- | --- | --- |
| 引用—主张相关 | 引错条目（编号对、内容是另一篇） | 引用编号全绿而参考文献**系统性错位** |
| 节间不重复 | 摘要与结论互抄 | 两个总结面冗余，读者以为有两处独立确认 |
| 节非空洞 | 某节只写几个词 | 「八节齐备」判绿，而其中一节实际是空壳 |

三条都是**必要不充分**。把它们写成「叙述质量已判」是**夸大验证证据**，`fix_policy`
逐字禁止。

## 5. 判据在哪 / 怎么跑

```bash
# 三条判据 + 反证臂（20 条）
uv run --frozen --no-sync python -B -m pytest tests/application/test_manuscript_quality.py -q

# 装配路径的回归（改夹具会打到这些）
uv run --frozen --no-sync python -B -m pytest \
  tests/application/test_manuscript_assembler.py \
  tests/application/test_manuscript_assembly.py \
  tests/application/test_manuscript_reference_order.py \
  tests/e2e/test_direction_to_manuscript_product_path.py -q
```

**产品面证据**：`test_build_manuscript_refuses_a_disjoint_citation` 走的是
`build_manuscript`（装配路径的必经函数），不是直接调 `validate_quality` —— 因此
「判据接上了产品路径」有机械证据，而不是一句声明。

## 6. 残余（本口径**不**覆盖，如实登记）

- **语义支持未判**（见 §3 首行）——这是「叙述质量的**强**口径」，需要先论证可判性；
- **阈值只对英文正文标定**：本仓手稿合约要求英文（`MANUSCRIPT_KEYS` 的八节正文），
  非英文正文的词数口径未标定；
- **停用词是封闭词表**：改它等于改口径，必须同轮改
  `test_stopwords_are_the_closed_list`；
- **只判本 run 的手稿**：跨 run 一致性不在射程内。
