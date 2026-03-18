/**
 * Web Evidence Search Module
 *
 * Searches PubMed and medical sources for real evidence to supplement
 * the RAG knowledge base. Used to ground appeal letters in verifiable,
 * current medical literature.
 *
 * All APIs used are free and require no API keys:
 * - PubMed E-utilities (NCBI)
 */

interface PubMedArticle {
    pmid: string;
    title: string;
    abstract: string;
    authors: string;
    journal: string;
    year: string;
}

interface WebEvidence {
    source: string;
    title: string;
    summary: string;
    citation: string;
    url: string;
}

/**
 * Search PubMed for relevant medical evidence.
 * Uses NCBI E-utilities API (free, no key required).
 */
async function searchPubMed(query: string, maxResults: number = 5): Promise<PubMedArticle[]> {
    try {
        // Step 1: Search for article IDs
        const searchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=${maxResults}&sort=relevance&term=${encodeURIComponent(query)}`;
        const searchResponse = await fetch(searchUrl, { signal: AbortSignal.timeout(8000) });

        if (!searchResponse.ok) return [];

        const searchData = await searchResponse.json();
        const ids: string[] = searchData.esearchresult?.idlist || [];

        if (ids.length === 0) return [];

        // Step 2: Fetch article details
        const fetchUrl = `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=${ids.join(',')}`;
        const fetchResponse = await fetch(fetchUrl, { signal: AbortSignal.timeout(8000) });

        if (!fetchResponse.ok) return [];

        const xml = await fetchResponse.text();
        return parsePubMedXml(xml);
    } catch (err) {
        console.error('PubMed search failed:', err);
        return [];
    }
}

/**
 * Parse PubMed XML response into structured articles.
 * Simple XML parsing without external dependencies.
 */
function parsePubMedXml(xml: string): PubMedArticle[] {
    const articles: PubMedArticle[] = [];
    const articleBlocks = xml.split('<PubmedArticle>').slice(1);

    for (const block of articleBlocks) {
        try {
            const pmid = extractXmlTag(block, 'PMID') || '';
            const title = extractXmlTag(block, 'ArticleTitle') || '';
            const abstractText = extractXmlTag(block, 'AbstractText') || '';
            const journal = extractXmlTag(block, 'Title') || '';
            const year = extractXmlTag(block, 'Year') || '';

            // Get first author
            const lastNameMatch = block.match(/<LastName>([^<]+)<\/LastName>/);
            const authors = lastNameMatch ? `${lastNameMatch[1]} et al.` : '';

            if (title && abstractText) {
                articles.push({
                    pmid,
                    title: cleanXmlText(title),
                    abstract: cleanXmlText(abstractText).substring(0, 600),
                    authors,
                    journal: cleanXmlText(journal),
                    year,
                });
            }
        } catch {
            continue;
        }
    }

    return articles;
}

function extractXmlTag(xml: string, tag: string): string | null {
    // Handle tags that may have attributes
    const regex = new RegExp(`<${tag}[^>]*>([\\s\\S]*?)</${tag}>`, 'i');
    const match = xml.match(regex);
    return match ? match[1] : null;
}

function cleanXmlText(text: string): string {
    return text
        .replace(/<[^>]+>/g, '') // Remove nested XML tags
        .replace(/\s+/g, ' ')   // Normalize whitespace
        .trim();
}

/**
 * Build optimized PubMed search queries for a denied service.
 * Focuses on medical necessity evidence, clinical guidelines, and outcomes data.
 */
function buildSearchQueries(deniedService: string, denialReason: string, cptCodes: string, icd10Codes: string): string[] {
    const queries: string[] = [];

    // Primary: service + medical necessity + systematic review
    queries.push(`${deniedService} medical necessity guidelines systematic review`);

    // Evidence for the specific service
    queries.push(`${deniedService} clinical outcomes evidence-based`);

    // Address the denial reason specifically
    if (denialReason) {
        const shortReason = denialReason.substring(0, 100);
        queries.push(`${deniedService} ${shortReason} coverage criteria`);
    }

    return queries;
}

/**
 * Main function: Search for web-based medical evidence to supplement RAG.
 * Returns formatted evidence that can be injected into the appeal prompt.
 */
export async function searchWebEvidence(
    deniedService: string,
    denialReason: string,
    cptCodes: string,
    icd10Codes: string,
): Promise<{ evidence: WebEvidence[]; formattedContext: string }> {
    const queries = buildSearchQueries(deniedService, denialReason, cptCodes, icd10Codes);

    // Search in parallel (but limit to avoid rate limits on PubMed)
    const allArticles: PubMedArticle[] = [];
    for (const query of queries) {
        const articles = await searchPubMed(query, 3);
        allArticles.push(...articles);

        // Small delay to be respectful to PubMed API
        if (queries.indexOf(query) < queries.length - 1) {
            await new Promise(r => setTimeout(r, 500));
        }
    }

    // Deduplicate by PMID
    const seen = new Set<string>();
    const uniqueArticles = allArticles.filter(a => {
        if (seen.has(a.pmid)) return false;
        seen.add(a.pmid);
        return true;
    });

    // Convert to WebEvidence format
    const evidence: WebEvidence[] = uniqueArticles.slice(0, 5).map(a => ({
        source: 'PubMed',
        title: a.title,
        summary: a.abstract,
        citation: `${a.authors} ${a.journal}. ${a.year}. PMID: ${a.pmid}`,
        url: `https://pubmed.ncbi.nlm.nih.gov/${a.pmid}/`,
    }));

    // Format for prompt injection
    const formattedContext = evidence.length > 0
        ? evidence.map((e, i) =>
            `[PubMed ${i + 1}] ${e.title}\nCitation: ${e.citation}\nURL: ${e.url}\n\nFindings: ${e.summary}`
        ).join('\n\n---\n\n')
        : '';

    return { evidence, formattedContext };
}
