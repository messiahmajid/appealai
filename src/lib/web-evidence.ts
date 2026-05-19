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
    publicationTypes: string[];
}

interface WebEvidence {
    source: string;
    title: string;
    summary: string;
    citation: string;
    url: string;
    evidenceLevel: string;
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
            const publicationTypes = [...block.matchAll(/<PublicationType[^>]*>([^<]+)<\/PublicationType>/gi)]
                .map(match => cleanXmlText(match[1]));

            // Get first author
            const lastNameMatch = block.match(/<LastName>([^<]+)<\/LastName>/);
            const authors = lastNameMatch ? `${lastNameMatch[1]} et al.` : '';

            const isRetracted = publicationTypes.some(type => /retracted|retraction/i.test(type)) || /retracted publication/i.test(block);
            if (title && abstractText && !isRetracted) {
                articles.push({
                    pmid,
                    title: cleanXmlText(title),
                    abstract: cleanXmlText(abstractText).substring(0, 600),
                    authors,
                    journal: cleanXmlText(journal),
                    year,
                    publicationTypes,
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
    const evidenceFilter = '(humans[MeSH Terms]) AND (systematic review[Publication Type] OR meta-analysis[Publication Type] OR practice guideline[Publication Type] OR randomized controlled trial[Publication Type] OR guideline[Publication Type])';

    // Primary: service + medical necessity + systematic review
    queries.push(`(${deniedService}) AND medical necessity AND ${evidenceFilter}`);

    // Evidence for the specific service
    queries.push(`(${deniedService}) AND clinical outcomes AND evidence-based AND ${evidenceFilter}`);

    // Address the denial reason specifically
    if (denialReason) {
        const shortReason = denialReason.substring(0, 100);
        queries.push(`(${deniedService}) AND (${shortReason}) AND coverage criteria AND humans[MeSH Terms]`);
    }
    if (cptCodes || icd10Codes) {
        queries.push(`(${deniedService}) AND (${cptCodes} ${icd10Codes}) AND medical policy AND humans[MeSH Terms]`);
    }

    return queries;
}

function evidenceLevel(publicationTypes: string[]): string {
    const joined = publicationTypes.join(' ').toLowerCase();
    if (/practice guideline|guideline/.test(joined)) return 'Guideline';
    if (/systematic review|meta-analysis/.test(joined)) return 'Systematic review/meta-analysis';
    if (/randomized controlled trial/.test(joined)) return 'Randomized controlled trial';
    if (/clinical trial/.test(joined)) return 'Clinical trial';
    return 'Peer-reviewed article';
}

const RELEVANCE_STOP_WORDS = new Set([
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'when', 'then', 'than', 'medical',
    'necessity', 'guidelines', 'guideline', 'coverage', 'criteria', 'clinical', 'outcomes',
    'evidence', 'based', 'requested', 'procedure', 'service', 'does', 'meet', 'not',
]);

function relevanceTokens(...values: string[]): string[] {
    return [...new Set(values
        .join(' ')
        .toLowerCase()
        .split(/[^a-z0-9]+/)
        .map(t => t.trim())
        .filter(t => t.length >= 4 && !RELEVANCE_STOP_WORDS.has(t) && !/^\d+$/.test(t)))];
}

function isRelevantArticle(article: PubMedArticle, deniedService: string, denialReason: string, icd10Codes: string): boolean {
    const serviceTokens = relevanceTokens(deniedService);
    const contextTokens = relevanceTokens(deniedService, denialReason, icd10Codes);
    const articleText = `${article.title} ${article.abstract}`.toLowerCase();
    const serviceMatches = serviceTokens.filter(token => articleText.includes(token)).length;
    const contextMatches = contextTokens.filter(token => articleText.includes(token)).length;

    // Require direct service relevance, or multiple broader context overlaps.
    return serviceMatches >= 1 || contextMatches >= 3;
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
    }).filter(a => isRelevantArticle(a, deniedService, denialReason, icd10Codes));

    // Convert to WebEvidence format
    const evidence: WebEvidence[] = uniqueArticles.slice(0, 5).map(a => ({
        source: 'PubMed',
        title: a.title,
        summary: a.abstract,
        citation: `${a.authors} ${a.journal}. ${a.year}. PMID: ${a.pmid}`,
        url: `https://pubmed.ncbi.nlm.nih.gov/${a.pmid}/`,
        evidenceLevel: evidenceLevel(a.publicationTypes),
    }));

    // Format for prompt injection
    const formattedContext = evidence.length > 0
        ? evidence.map((e, i) =>
            `[PubMed ${i + 1}] ${e.title}\nEvidence Level: ${e.evidenceLevel}\nCitation: ${e.citation}\nURL: ${e.url}\n\nFindings: ${e.summary}`
        ).join('\n\n---\n\n')
        : '';

    return { evidence, formattedContext };
}
