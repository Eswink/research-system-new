"""NCBI E-utilities 响应解析与归一化（与 ncbi.py 拆分，保持模块规模阈值）。

纯函数：efetch XML → article dict；esearch/elink JSON 归一化。
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from packages.application.ports.errors import InvalidInputError


def parse_efetch_xml(content: bytes) -> dict[str, object]:
    """efetch XML → {"articles": [normalized article, ...]}。

    PA-1 扫描处置：输入是不可信 HTTP 字节。std ET 展开内部实体
    （entity-expansion DoS）——输入拒绝 DOCTYPE/ENTITY 声明，并设 5MB 上限。
    """
    if len(content) > 5 * 1024 * 1024:
        raise InvalidInputError("efetch response exceeds 5MB limit")
    head = content.lstrip()[:256].upper()
    if b"<!DOCTYPE" in head or b"<!ENTITY" in head:
        raise InvalidInputError("efetch response must not declare DOCTYPE/ENTITY")
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


__all__ = ["extract_article", "normalize_elink", "normalize_esearch", "parse_efetch_xml"]
