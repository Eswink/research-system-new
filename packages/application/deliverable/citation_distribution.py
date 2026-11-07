"""引用充分性的**跨 run 分布读数**与**标定门**（GOAL-20261107-107 EC-04）。

**它补哪一格**：GOAL-20261103-105 做出了三个**单份**读数（每句引用数 / 每条被引次数 /
单支撑节），但把三个阈值全部留成 `None`，理由是「阈值需要先有真实语料标定」。那是对的
—— 而当时仓内**零**真实手稿。现在有了语料（GOAL-20261104-106 的真实 run 落了一份
`manuscript.md`），所以本轮把「有语料就能标定」这件事做成**一条命令**，但**仍然不拍
阈值**：一份不够三类分布，任何数字还是编造。

**三个纯函数**（确定性：零出网、零模型、零时钟、不读文件系统 —— 路径由调用方给）：

1. `collect_readings(texts)`：多份手稿正文 → 每份的三个读数（复用
   `citation_sufficiency.measure_citation_sufficiency`，**不重算**）。
2. `summarize(readings)`：分布读数（份数 / 各类的分位与极值 / 单支撑节总数）。
   **它不产出阈值建议** —— 那需要「什么算够」的判断，本模块不冒充。
3. `calibration_gate(readings)`：明确的语料门 —— 够不够标定，缺什么。

**本模块不做什么**（射程边界，**最重要的一段**）：

* **不写任何阈值**。`MIN_*` 三个常量住在 `citation_sufficiency`，本模块**只读**它们，
  一个字节都不改。`calibration_gate` 返回「不足」时，任何非 `None` 阈值都是**越权**
  （判据钉住这一条）。
* **不判「充分」**。分布回答「这份稿子引了几条」，不回答「该引几条」。
* **不读文件系统**。`collect_readings` 收文本，不收路径 —— 读盘是 `tools/` 入口的事
  （与 `citation_sufficiency` 同一条纪律：纯函数不接触 I/O，才可跨树复现）。

**为什么门开在「三份」**：`MIN_CORPUS = 3` 不是统计学的魔法数字，而是 §7 原文已经写下的
标定条件（「先用 3 份真实 `manuscript.md` 量分布」）。本模块把这个**已经声明的**条件变成
机器可检的门，而不是新发明一个门槛。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from packages.application.deliverable.citation_sufficiency import (
    CITED_SECTIONS,
    measure_citation_sufficiency,
)

#: 标定所需的**最少语料份数**（§7 原文的条件，不是新发明的门槛）。
MIN_CORPUS = 3


@dataclass(frozen=True, slots=True)
class ManuscriptReading:
    """一份手稿的三个读数（`label` 只是便于人读的来源标识，不参与计算）。"""

    label: str
    sentences: int
    marks: int
    references: int
    single_support_sections: int

    @property
    def marks_per_sentence(self) -> float:
        """每句平均引用标记数（0 句 ⇒ 0.0，不是除零）。"""
        return 0.0 if self.sentences == 0 else self.marks / self.sentences


@dataclass(frozen=True, slots=True)
class Distribution:
    """一份语料的分布读数（**只描述，不建议**）。"""

    manuscripts: int
    sentences: tuple[int, ...]
    marks: tuple[int, ...]
    references: tuple[int, ...]
    single_support_total: int
    marks_per_sentence: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class CalibrationGate:
    """标定门：能不能拍阈值，以及缺什么。"""

    #: 语料份数是否达到 `MIN_CORPUS`。
    sufficient: bool
    #: 已有份数（如实报，不夹取）。
    manuscripts: int
    #: 不足时**点名缺什么**（够则为空）。
    missing: tuple[str, ...]

    @property
    def may_calibrate(self) -> bool:
        """与 `sufficient` 同义，读起来更像判据谓词。"""
        return self.sufficient


def _sections(text: str) -> Mapping[str, str]:
    """把一份 `manuscript.md` 切成 `CITED_SECTIONS` 里的那几节（缺节 ⇒ 空串）。

    **按二级标题切**：手稿的形状由汇编器保证（`## 1. Introduction` 等），本函数只认
    行首标题 —— 正文里提到小节名不该改变切分（与宪章解析器同一条纪律）。
    """
    headings = {
        "introduction": "## 1. Introduction",
        "results": "## 4. Results",
        "discussion": "## 5. Discussion",
    }
    sections: dict[str, str] = {}
    for key in CITED_SECTIONS:
        marker = headings[key]
        start = text.find(marker)
        if start == -1:
            sections[key] = ""
            continue
        body_start = start + len(marker)
        nxt = text.find("\n## ", body_start)
        sections[key] = text[body_start : nxt if nxt != -1 else len(text)]
    return sections


def collect_readings(texts: Sequence[tuple[str, str]]) -> tuple[ManuscriptReading, ...]:
    """`[(label, 正文)]` → 每份的三个读数。

    **不传路径**：读盘在 `tools/` 入口（纯函数不接触 I/O）。顺序原样保留 —— 调用方的
    顺序就是分布摘要的顺序，本函数不排序（排序会让「第几份」与输入脱钩）。
    """
    readings: list[ManuscriptReading] = []
    for label, text in texts:
        measured = measure_citation_sufficiency(_sections(text))
        readings.append(
            ManuscriptReading(
                label=label,
                sentences=len(measured.per_sentence),
                marks=sum(item.marks for item in measured.per_sentence),
                references=len(measured.per_reference),
                single_support_sections=len(measured.single_support_sections),
            )
        )
    return tuple(readings)


def summarize(readings: Sequence[ManuscriptReading]) -> Distribution:
    """逐类原值 + 单支撑节总数。**不做统计推断、不给阈值建议。**

    保留原值而不是只给均值：三份语料里「2 / 2 / 9」与「4 / 4 / 5」均值相近而分布不同，
    而后者才是标定时要看的东西。
    """
    return Distribution(
        manuscripts=len(readings),
        sentences=tuple(item.sentences for item in readings),
        marks=tuple(item.marks for item in readings),
        references=tuple(item.references for item in readings),
        single_support_total=sum(item.single_support_sections for item in readings),
        marks_per_sentence=tuple(round(item.marks_per_sentence, 4) for item in readings),
    )


def calibration_gate(readings: Sequence[ManuscriptReading]) -> CalibrationGate:
    """语料够不够标定；不够就**点名缺什么**。

    **它同时也是一条关于阈值的守卫**：门判「不足」时，`citation_sufficiency` 里任何
    被填上的阈值都是**越权**（判据 `test_a_threshold_may_not_be_set_before_the_gate_opens`
    钉住这一条 —— 它读的是既有公开面 `uncalibrated_thresholds()`，不是本模块另立的清单）。
    理由：没有语料支撑的数字不是阈值，是编造。
    """
    count = len(readings)
    if count >= MIN_CORPUS:
        return CalibrationGate(sufficient=True, manuscripts=count, missing=())
    return CalibrationGate(
        sufficient=False,
        manuscripts=count,
        missing=(f"manuscripts: {count} of {MIN_CORPUS} required by MANUSCRIPT_QUALITY.md §7",),
    )


__all__ = [
    "MIN_CORPUS",
    "CalibrationGate",
    "Distribution",
    "ManuscriptReading",
    "calibration_gate",
    "collect_readings",
    "summarize",
]
