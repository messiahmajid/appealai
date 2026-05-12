import asyncio
import re
from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    authors: str
    journal: str
    year: str


@dataclass
class WebEvidence:
    source: str
    title: str
    summary: str
    citation: str
    url: str


def _extract_xml_tag(xml: str, tag: str) -> str | None:
    pattern = rf"<{tag}[^>]*>([\s\S]*?)</{tag}>"
    match = re.search(pattern, xml, re.IGNORECASE)
    return match.group(1) if match else None


def _clean_xml_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_pubmed_xml(xml: str) -> list[PubMedArticle]:
    articles: list[PubMedArticle] = []
    blocks = xml.split("<PubmedArticle>")[1:]

    for block in blocks:
        try:
            pmid = _extract_xml_tag(block, "PMID") or ""
            title = _extract_xml_tag(block, "ArticleTitle") or ""
            abstract_text = _extract_xml_tag(block, "AbstractText") or ""
            journal = _extract_xml_tag(block, "Title") or ""
            year = _extract_xml_tag(block, "Year") or ""

            last_name_match = re.search(r"<LastName>([^<]+)</LastName>", block)
            authors = f"{last_name_match.group(1)} et al." if last_name_match else ""

            if title and abstract_text:
                articles.append(
                    PubMedArticle(
                        pmid=pmid,
                        title=_clean_xml_text(title),
                        abstract=_clean_xml_text(abstract_text)[:600],
                        authors=authors,
                        journal=_clean_xml_text(journal),
                        year=year,
                    )
                )
        except Exception:
            continue

    return articles


async def _search_pubmed(
    client: httpx.AsyncClient, query: str, max_results: int = 5
) -> list[PubMedArticle]:
    try:
        search_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&retmode=json&retmax={max_results}&sort=relevance"
            f"&term={httpx.QueryParams({'t': query})['t']}"
        )
        # Use proper encoding
        search_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        )
        search_resp = await client.get(
            search_url,
            params={"db": "pubmed", "retmode": "json", "retmax": max_results, "sort": "relevance", "term": query},
            timeout=8,
        )
        if not search_resp.is_success:
            return []

        ids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        fetch_resp = await client.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={"db": "pubmed", "retmode": "xml", "id": ",".join(ids)},
            timeout=8,
        )
        if not fetch_resp.is_success:
            return []

        return _parse_pubmed_xml(fetch_resp.text)
    except Exception as e:
        logger.warning("pubmed_search_failed", error=str(e))
        return []


def _build_search_queries(
    denied_service: str, denial_reason: str, cpt_codes: str, icd10_codes: str
) -> list[str]:
    queries = [
        f"{denied_service} medical necessity guidelines systematic review",
        f"{denied_service} clinical outcomes evidence-based",
    ]
    if denial_reason:
        short_reason = denial_reason[:100]
        queries.append(f"{denied_service} {short_reason} coverage criteria")
    return queries


async def search_web_evidence(
    denied_service: str,
    denial_reason: str,
    cpt_codes: str,
    icd10_codes: str,
) -> dict:
    queries = _build_search_queries(denied_service, denial_reason, cpt_codes, icd10_codes)

    all_articles: list[PubMedArticle] = []
    async with httpx.AsyncClient() as client:
        for i, query in enumerate(queries):
            articles = await _search_pubmed(client, query, 3)
            all_articles.extend(articles)
            if i < len(queries) - 1:
                await asyncio.sleep(0.5)

    seen: set[str] = set()
    unique: list[PubMedArticle] = []
    for a in all_articles:
        if a.pmid not in seen:
            seen.add(a.pmid)
            unique.append(a)

    evidence: list[WebEvidence] = [
        WebEvidence(
            source="PubMed",
            title=a.title,
            summary=a.abstract,
            citation=f"{a.authors} {a.journal}. {a.year}. PMID: {a.pmid}",
            url=f"https://pubmed.ncbi.nlm.nih.gov/{a.pmid}/",
        )
        for a in unique[:5]
    ]

    formatted_context = ""
    if evidence:
        formatted_context = "\n\n---\n\n".join(
            f"[PubMed {i + 1}] {e.title}\nCitation: {e.citation}\nURL: {e.url}\n\nFindings: {e.summary}"
            for i, e in enumerate(evidence)
        )

    return {
        "evidence": [
            {"source": e.source, "title": e.title, "citation": e.citation, "url": e.url}
            for e in evidence
        ],
        "formattedContext": formatted_context,
    }
