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
  §7 第 4 项（引用是否充分）自 GOAL-20261103-105 起已产出**结构读数**
  （`packages/application/deliverable/citation_sufficiency.py`：每句引用数 / 每条被引
  条目被引次数 / 单支撑节，读数写进 `manuscript.md` 的脚注），但**充分性仍未判**：
  三个阈值常量缺省全是 `None`，**取值待 ≥3 份真实手稿的量分布**（仓内零真实语料）；
- **十一相链于 2026-11-06 首次真实 `SUCCEEDED`**（run `3142b142-0fa2-43b6-ac19-92d2e3934858`，protocol `direction_to_manuscript_v1_0_0`）—— 此前只有 mock e2e。读数落在 `.cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-SUCCEEDED.json`：十一相全 `SUCCEEDED`、18/18 产物字节在场、真实检索三个 PMID（42787049 / 42958757 / 42955413）、两臂实验各落 `metrics`、脚注引用读数 `[52 句 / 6 标记 / 3 条]` 且与正文重算逐项相等。
- **对这条读数的射程**（GOAL-20261104-106）：
  `direction_to_manuscript_v1.yaml`（question → retrieval → novelty → plan → experiment →
  review → manuscript → editorial → revision → submission → report）此前**真实 run 合计
  0 次** —— 它只被 **mock 中转站** e2e 验证过（那条判据自己的 docstring 就写着「真实模型
  条件下的八相由后续 live 判据承担」），而「产品入口跑通全链」那条 live 判据跑的是
  `direction_to_report_v2`（七相）、**不是**十一相。本轮补上 live 判据
  （`tests/e2e/test_the_manuscript_chain_runs_live.py`）并跑到一次 `SUCCEEDED`；读数落在
  `.cursor/plans/goals/evidence/GOAL-20261104-106-manuscript-chain-live.json`
  （run id / 十一相状态 / 每件产物的字节长度 / 引用读数 / 应答重叠）。**这条读数只证明
  链成立**：§2 的三条判据与 §7 的判定表**逐字未动**，`NOT_JUDGED` 仍是五项 ——
  「链跑得通」与「手稿写得好」是两件事，把前者读成后者属于伪造验证证据；
- **阈值只对英文正文标定**：本仓手稿合约要求英文（`MANUSCRIPT_KEYS` 的八节正文），
  非英文正文的词数口径未标定；
- **停用词是封闭词表**：改它等于改口径，必须同轮改
  `test_stopwords_are_the_closed_list`；
- **只判本 run 的手稿**：跨 run 一致性不在射程内。

## 7. 强口径判定（GOAL-20261101-103 EC-05）

**这一节只做论证，不实现任何东西。** §3 的六项「不判」此前是一张清单；本轮把
`manuscript_quality.NOT_JUDGED` 的五项（第六项「跨 run 一致性」不在该常量里，另列于 §3
与 §6）**逐项**过一遍：它到底是**可机械判**，还是**只能人评**。判法列给出的是
「如果要机械判，判据长什么样」；结论列给出本轮的实际判定。

**判定的四条依据**（写下来是为了让"可机械判"不是一个主观词）：

- **P1 确定性**：同样的字节两次运行给同一结论（零模型、零时钟、零出网）；
- **P2 反证可写**：能构造一个**必然判红**的输入（否则判据无从证伪）；
- **P3 不需要外部知识**：不需要领域专家、不需要文献全文、不需要"什么是对的"这类共识；
- **P4 不冒充语义**：判据的通过**不得**被读成「论证成立」（必要不充分）。

一条判据**同时**满足 P1–P4 才算「可机械判」；缺 P3 的典型形态是"看起来可判，实际把
判断外包给了词表"。

| # | `NOT_JUDGED` 项 | 判定 | 依据 | 若可机械判，判法是什么 |
| --- | --- | --- | --- | --- |
| 1 | `whether a citation supports the sentence it is attached to (only: not unrelated)` | **只能人评** | 缺 P3 | 词重叠（现有 `check_citation_alignment`）判的是"有交集"，不是"蕴含"。要判「支持」，需要对**被引条目的全文**做语义蕴含判定 —— 而本 run 只落了标题与摘要片段（`tool-result` 的 `title` / `abstractText` 截断），**输入本身不足以判定**。换任何确定性算法都只是换个词表：仍会在"反对该主张的文献与主张共享关键词"上判绿（正是 §3 首行那个反例）。**出路**：需要外部语义模型（付费、非确定性）⇒ 属「外部评审面板」而不是本口径。 |
| 2 | `whether the argument holds (premises sufficient / inference valid / conclusion supported)` | **只能人评** | 缺 P3 | 这是**形式论证有效性**问题。可机械判的只有它的**退化子集**：「结论里的数字是否出现在事实表里」——而这一条**已经**由装配期的数字禁令与引用闭合判掉了（`validate_manuscript` 的四条结构事实）。剩下的「推断有效」需要形式化整篇论证（前提/推理规则/结论），本仓手稿是自由文本、没有形式结构 ⇒ 无从对齐。 |
| 3 | `whether the method is appropriate for the question` | **只能人评** | 缺 P3 | 「臂选得对不对、指标测没测到想测的东西」需要领域知识。可机械判的退化子集是「声明的臂是否都跑过、指标名是否都在事实表里」——那属于实验域已有的判据（`experiment_design` / `arm_comparison`），不属叙述质量，也不回答"合适"。 |
| 4 | `whether the citation set is sufficient for each claim` | **可机械判（弱口径）** | P1–P4 全满足 | 判法：对每个**带引用标记的主张句**，数它引了几条；再对**每一条被引条目**判「它在本 run 的其他主张里被引了几次」。产出两个读数即可判「某条被引用一次而它是某节唯一的支撑」这类**可数**形态。**边界**：它判的是**计数分布**，不是「够不够」——"该引 3 篇"永远需要人定阈值。本轮**不实现**：阈值需要先有真实语料标定（现有夹具的正文是受控短文本，计数分布不具代表性），而 GOAL-101 已经用「阈值必须实测而来」这条纪律钉住过同类取值（`MIN_SECTION_WORDS = 8`）。**下一轮输入**：先用 3 份真实 `manuscript.md` 量分布，再定阈值。 |
| 5 | `writing style, readability, grammar` | **可机械判（弱口径，且价值低）** | P1/P2 满足；P4 需显式声明 | 判法：句长分布、被动语态比例、连续重复词。**为什么不建议做**：这些读数与「稿子写得好不好」的关联很弱，而误报代价高（一份简洁的 Methods 会被判"句子太短"）。本仓的选择是**不做**，并在 §3 明写「不在射程内」——**不想判**与**判不了**要分开记。 |

**结论（下一轮的输入）**：

1. **五项里四项在可判性上分成两类** —— 1/2/3 是**只能人评**（缺 P3：输入或知识不在仓内），
   4/5 是**可机械判但本轮不实现**（4 缺阈值标定，5 价值低且误报高）。这个区分本身就是
   本轮要交付的东西：它把「叙述质量未判」从一句笼统的缺口拆成了**一个外部评审面板需求**
   加**两个待标定的弱判据**。
2. **强口径（"论证成立"）在结构上不可达**：要判它必须引入语义蕴含模型 ⇒ 非确定性、
   有成本、且通过也不代表对（P4）。因此**不把它写成判据**是正确的，而不是偷懒。
3. **本轮不改变 `NOT_JUDGED` 的内容**：五项逐字保留。新增的 §7 是**论证**，不是新判据
   —— 判据 `test_the_quality_module_declares_what_it_does_not_judge` 仍然要求它们在场。
   若将来实现第 4 项，那一项才从 `NOT_JUDGED` 移到 §2，且同轮改那条判据。
4. **下一轮候选**（按可判性排序）：① 第 4 项的计数分布判据（先标定阈值）；
   ② 「外部评审面板」——把只能人评的三项交给真人/独立模型，并在读面标注**谁**判的
   （与 `ReviewFinding.reviewer_model` 同一口径）。

**反向误读仍然是明令禁止的**：本节的存在**不**意味着强口径已判。§3 的两条禁令逐字有效。

**第 1/2/3 项的出口已经落地，但本口径仍然不判**（GOAL-20261107-107）：`deliverable/manuscript_panel.py` 把这三项交给**独立模型**，判词落 `ReviewFinding`（`review_type = manuscript_panel`）并带 `reviewer_model` 归因 —— 这正是上面候选 ② 说的形态。三条边界逐条可判：判词是 **advisory**（不产生 `Decision`、不参与验收门）；网关失败落 `PANEL_UNAVAILABLE` 而**不**折算成任何一态；`NOT_JUDGED` **五项逐字不动** —— 确定性模块仍然不判这三项，面板是**另一个判者**。**读这一句时最容易犯的错**：把「有第三方判词」读成「叙述质量已判」。面板说的是「某个模型认为它可以/不可以」，不是「论证成立」。

**判词现在可核验（GOAL-20261111-111），但射程仍不充分**：`REFUTED` 的 `rationale` 必须**落在正文的字节上**——点名 `S<n>`（且在句数范围内）或引用一段正文真实子串；指不到就**降级** `AMBIGUOUS` 并点名缺什么（`deliverable/panel_grounding.py`）。这让判词本身**可被反驳**：读者能核对它指的是哪一句、那句话在不在。**它仍然不是「论证成立」**：核验通过的判词只说明「某个模型认为 X 句有问题，且那句话确实在正文里」。`NOT_JUDGED` 五项与上面的判定表**一字未动**；引用充分性的阈值仍全 `None`（不在这里拍板）。

