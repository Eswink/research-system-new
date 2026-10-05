"""NCBI E-utilities 响应解析与归一化（与 ncbi.py 拆分，保持模块规模阈值）。

纯函数：efetch XML → article dict；esearch/elink JSON 归一化。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from packages.application.ports.errors import InvalidInputError

#: DOCTYPE 声明的扫描窗口（内部子集标记 `[` 必须出现在这一窗内；声明恒在根元素之前）。
_DECLARATION_WINDOW = 4096


def _reject_unsafe_declarations(content: bytes) -> None:
    """拒绝**实体声明**与**内部 DTD 子集**——entity-expansion DoS 的真实入口。

    GOAL-011 EC-01 的 live 实测更正了这条口径：真实 efetch 响应**带外部 DOCTYPE**
    （`<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2025//EN"
    "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_250101.dtd">`）。早先"拒绝一切
    DOCTYPE"的写法会拒掉**每一次真实 efetch**（离线夹具没带 DOCTYPE，所以从未被测到；
    离线判据全绿而真实读取必红）。风险是实体展开，不是 DOCTYPE 本身，边界因此收到
    它本身：`<!ENTITY`（唯一合法的实体声明拼写，大小写敏感）一律拒绝；DOCTYPE 带内部
    子集（`[`，实体定义只能写在那里）一并拒绝；外部 DOCTYPE 交 std ET 处理——ET 不取
    外部实体。5MB 上限不变。
    """
    if b"<!ENTITY" in content:
        raise InvalidInputError("efetch response must not declare ENTITY")
    start = content.find(b"<!DOCTYPE")
    if start != -1:
        declaration = content[start : start + _DECLARATION_WINDOW].split(b">", 1)[0]
        if b"[" in declaration:
            raise InvalidInputError("efetch response must not declare an internal DTD subset")


def parse_efetch_xml(content: bytes) -> dict[str, object]:
    """efetch XML → {"articles": [normalized article, ...]}。

    PA-1 扫描处置：输入是不可信 HTTP 字节。std ET 展开内部实体
    （entity-expansion DoS）——按 `_reject_unsafe_declarations` 的表征拒绝，并设 5MB 上限。
    """
    if len(content) > 5 * 1024 * 1024:
        raise InvalidInputError("efetch response exceeds 5MB limit")
    _reject_unsafe_declarations(content)
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise InvalidInputError(f"efetch response is not well-formed XML: {exc}") from exc
    articles = []
    for citation in root.findall(".//PubmedArticle"):
        medline = citation.find("MedlineCitation")
        if medline is None:
            continue
        articles.append(extract_article(medline))
    return {"articles": articles}


def extract_article(medline: ET.Element) -> dict[str, object]:
    """MedlineCitation → 归一化 article dict（缺失字段空字符串）。"""
    pmid = medline.findtext("PMID") or ""
    article = medline.find("Article")
    title = ""
    abstract = ""
    journal = ""
    year = ""
    authors: list[str] = []
    if article is not None:
        title = "".join(article.findtext("ArticleTitle") or "").strip()
        abstract = " ".join(
            item.strip() for item in (article.findtext("Abstract/AbstractText") or "").split()
        )
        journal = article.findtext("Journal/Title") or ""
        year = article.findtext("Journal/JournalIssue/PubDate/Year") or ""
        author_list = article.find("AuthorList")
        if author_list is not None:
            for author in author_list.findall("Author"):
                last = author.findtext("LastName")
                fore = author.findtext("ForeName")
                collective = author.findtext("CollectiveName") or ""
                name = f"{fore or ''} {last or ''}".strip() or collective
                if name:
                    authors.append(name)
    return {
        "pmid": pmid,
        "title": title,
        "abstract": abstract,
        "journal": journal,
        "year": year,
        "authors": authors,
    }


def normalize_esearch(payload: dict[str, object], term: str) -> dict[str, object]:
    """esearch JSON → {count, ids, query}；结构非法抛 InvalidInputError。"""
    result = payload.get("esearchresult")
    if not isinstance(result, dict):
        raise InvalidInputError("esearch response missing esearchresult")
    count_raw = result.get("count", 0)
    idlist = result.get("idlist", [])
    if not isinstance(idlist, list):
        raise InvalidInputError("esearch response idlist must be a list")
    try:
        count = int(count_raw)
    except (TypeError, ValueError) as exc:
        raise InvalidInputError("esearch response count must be an integer") from exc
    return {
        "count": count,
        "ids": [str(item) for item in idlist],
        "query": term,
    }


def normalize_elink(payload: dict[str, object], pmid: str) -> dict[str, object]:
    """elink JSON → {pmid, pmc_links}；结构非法抛 InvalidInputError。"""
    links: list[str] = []
    linksets = payload.get("linksets", [])
    if not isinstance(linksets, list):
        raise InvalidInputError("elink response linksets must be a list")
    for linkset in linksets:
        if not isinstance(linkset, dict):
            continue
        for linkdb in linkset.get("linksetdbs", []):
            if not isinstance(linkdb, dict):
                continue
            raw_links = linkdb.get("links", [])
            if isinstance(raw_links, list):
                links.extend(str(item) for item in raw_links)
    return {"pmid": str(pmid), "pmc_links": links}


#: `citation.validate` 的三态判词（GOAL-20261006-031 EC-02）。**逐条写明语义**：
#:
#: * `SUPPORTED` —— 来源解析出 linkset 且 **≥1 条** PMC 链接 ⇒ 引用被来源支持；
#: * `UNSUPPORTED` —— 来源解析出 linkset 但**零链接** ⇒ 引用**不被来源支持**；
#: * `UNDETERMINED` —— 来源**没有** linkset（含 `linksets` 缺失 / 空列表 / 结构不可用）
#:   ⇒ **无法判定**；**不得**当成 `SUPPORTED`，也**不得**读成 `UNSUPPORTED`
#:   （「说了零条」与「没说话」是两件事）。
#:
#: 为什么三态而不是布尔：`pmc_links == []` 这一个读数把后两种来源合并了 —— 二值化的
#: 判定会把「来源没有这条引用的信息」谎报成「引用不被支持」。
CITATION_SUPPORTED = "SUPPORTED"
CITATION_UNSUPPORTED = "UNSUPPORTED"
CITATION_UNDETERMINED = "UNDETERMINED"
CITATION_VERDICTS = (CITATION_SUPPORTED, CITATION_UNSUPPORTED, CITATION_UNDETERMINED)


def validate_citation_support(payload: dict[str, object], pmid: str) -> dict[str, object]:
    """elink payload → 三态判定 `{pmid, pmc_links, verdict, reason}`。

    **取数只有一套**：本函数调 `normalize_elink`（与 `citation.inspect` **同一个**
    归一化实现）—— 三态是**在其之上**的判定层，不另解析一遍 linksets，也不新造第二个
    取数面（授权 2 明文要求）。结构非法（`linksets` 不是列表）由 `normalize_elink`
    照旧抛 `InvalidInputError`。
    """
    normalized = normalize_elink(payload, pmid)
    raw_links = normalized["pmc_links"]
    assert isinstance(raw_links, list)
    links = [str(item) for item in raw_links]
    linksets = payload.get("linksets", [])
    has_linkset = isinstance(linksets, list) and len(linksets) > 0
    if not has_linkset:
        verdict = CITATION_UNDETERMINED
        reason = "no linkset from the source: cannot decide whether the citation is supported"
    elif links:
        verdict = CITATION_SUPPORTED
        reason = f"{len(links)} PMC link(s) support the citation"
    else:
        verdict = CITATION_UNSUPPORTED
        reason = "linkset present but zero PMC links: the citation is not supported by the source"
    return {
        "pmid": str(pmid),
        "pmc_links": links,
        "verdict": verdict,
        "reason": reason,
    }


__all__ = [
    "CITATION_SUPPORTED",
    "CITATION_UNDETERMINED",
    "CITATION_UNSUPPORTED",
    "CITATION_VERDICTS",
    "extract_article",
    "normalize_elink",
    "normalize_esearch",
    "parse_efetch_xml",
    "validate_citation_support",
]


__all__ = ["extract_article", "normalize_elink", "normalize_esearch", "parse_efetch_xml"]
