import { getGuidelinesByCode } from '@/lib/guidelines';
import { searchRAGFallback } from '@/lib/rag';

export interface RetrievedGuideline {
    text: string;
    guidelineId: string;
    title: string;
    source: string;
    score: number;
}

function splitCodes(codes: string): string[] {
    return codes
        .replace(/;/g, ',')
        .split(',')
        .map(code => code.trim())
        .filter(Boolean);
}

export function retrieveGuidelineContext({
    deniedService,
    denialReason,
    cptCodes,
    icd10Codes,
    maxResults = 3,
}: {
    deniedService: string;
    denialReason: string;
    cptCodes: string;
    icd10Codes: string;
    maxResults?: number;
}): RetrievedGuideline[] {
    const seenIds = new Set<string>();
    const results: RetrievedGuideline[] = [];

    for (const code of [...splitCodes(cptCodes), ...splitCodes(icd10Codes)]) {
        for (const guideline of getGuidelinesByCode(code)) {
            if (seenIds.has(guideline.id)) continue;
            seenIds.add(guideline.id);
            results.push({
                text: `[${guideline.title}] [Source: ${guideline.source}]\n${guideline.content}`,
                guidelineId: guideline.id,
                title: guideline.title,
                source: guideline.source,
                score: 1.0,
            });
        }
    }

    if (results.length > 0) {
        return results.slice(0, maxResults);
    }

    const ragQuery = `${deniedService} ${denialReason} ${cptCodes} ${icd10Codes}`;
    return searchRAGFallback(ragQuery, maxResults);
}
