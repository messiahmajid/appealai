export type SafetySeverity = 'error' | 'warning';

export interface SafetyIssue {
    code: string;
    severity: SafetySeverity;
    message: string;
    evidence?: string;
}

export interface SafetyReport {
    verdict: 'PASS' | 'NEEDS_REVIEW' | 'FAIL';
    issues: SafetyIssue[];
    checks: {
        placeholderFree: boolean;
        guidelineCitationsValid: boolean;
        pubMedCitationsValid: boolean;
        quotedClaimsGrounded: boolean;
        numericClaimsGrounded: boolean;
    };
}

export interface SafetySource {
    text: string;
    label: string;
}

export interface RunSafetyChecksParams {
    letter: string;
    clinicalNotes: string;
    denialReason?: string;
    guidelineSources?: SafetySource[];
    pubMedSources?: SafetySource[];
}

const ALLOWED_BRACKET_CONTENT = /^(?:\d+|PubMed\s+\d+|Reference\s+\d+|DOCUMENTATION GAP(?::|\s|$).*)$/i;
const PLACEHOLDER_HINTS = /\b(?:address|phone|fax|date|dob|birth|member|claim|insert|if known|not provided|omitted|current|provider|physician|clinician|doctor|letterhead|practice|facility|office|npi|name|signature|sincerely|to be|blank)\b/i;
const CITATION_OR_SECTION_NUMBER = /^\d{1,2}$/;
const HEADING_ONLY_QUOTE = /^(?:active\s+)?(?:diagnosis|diagnoses|medications?|problems?|assessment|plan|impression|history|clinical summary|review of systems|physical examination|objective data|laboratory results|supporting documentation|documentation gaps?)$/i;

function normalizeText(value: string): string {
    return value
        .normalize('NFKC')
        .replace(/[“”]/g, '"')
        .replace(/[‘’]/g, "'")
        .replace(/[–—−]/g, '-')
        .replace(/\s+/g, ' ')
        .trim()
        .toLowerCase();
}

function normalizeForGrounding(value: string): string {
    return normalizeText(value)
        .replace(/&/g, ' and ')
        .replace(/[^a-z0-9%/]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

function groundingTokens(value: string): string[] {
    return normalizeForGrounding(value)
        .split(' ')
        .filter(token => token.length > 1 || /\d/.test(token));
}

function hasOrderedTokenWindow(quote: string, source: string): boolean {
    const quoteTokens = groundingTokens(quote);
    const sourceTokens = groundingTokens(source);
    if (quoteTokens.length < 4 || sourceTokens.length < quoteTokens.length) return false;

    const maxWindow = quoteTokens.length + Math.max(6, Math.ceil(quoteTokens.length * 0.75));
    for (let start = 0; start < sourceTokens.length; start += 1) {
        if (sourceTokens[start] !== quoteTokens[0]) continue;
        let quoteIndex = 0;
        const end = Math.min(sourceTokens.length, start + maxWindow);
        for (let sourceIndex = start; sourceIndex < end; sourceIndex += 1) {
            if (sourceTokens[sourceIndex] === quoteTokens[quoteIndex]) {
                quoteIndex += 1;
                if (quoteIndex === quoteTokens.length) return true;
            }
        }
    }

    return false;
}

function unique<T>(values: T[]): T[] {
    return [...new Set(values)];
}

function sourceContains(value: string, sources: SafetySource[]): boolean {
    const normalized = normalizeForGrounding(value);
    if (!normalized) return true;
    return sources.some(source => {
        const normalizedSource = normalizeForGrounding(source.text);
        return normalizedSource.includes(normalized) || hasOrderedTokenWindow(value, source.text);
    });
}

function findBracketIssues(letter: string): SafetyIssue[] {
    const issues: SafetyIssue[] = [];
    const matches = letter.matchAll(/\[([^\]]+)\]/g);

    for (const match of matches) {
        const content = match[1].trim();
        if (ALLOWED_BRACKET_CONTENT.test(content)) continue;

        if (PLACEHOLDER_HINTS.test(content) || !/^\d+$/.test(content)) {
            issues.push({
                code: 'UNRESOLVED_PLACEHOLDER',
                severity: 'error',
                message: `Potential unresolved placeholder or unsupported bracketed text: [${content}]`,
                evidence: `[${content}]`,
            });
        }
    }

    return issues;
}

function isPlaceholderBracket(content: string): boolean {
    if (ALLOWED_BRACKET_CONTENT.test(content)) return false;
    return PLACEHOLDER_HINTS.test(content) || /^[A-Z0-9 _/-]{3,}$/.test(content);
}

export function sanitizeGeneratedLetter(letter: string): string {
    return letter
        .replace(/\s*\[SOURCE [A-Z]\]/g, '')
        .replace(/^(\s{0,3}(?:#{1,6}\s*)?(?:\*\*)?)Documentation Gaps(?:\*\*)?\s*$/gim, '$1Clinical Rationale for Exception')
        .replace(/\[DOCUMENTATION GAP[.:]\s*([\s\S]*?)\]/g, 'Additional supporting rationale: $1')
        .replace(/\[DOCUMENTATION GAP\]\s*:\s*/g, 'Additional supporting rationale: ')
        .replace(/\[DOCUMENTATION GAP[.:]\s*/g, 'Additional supporting rationale: ')
        .split('\n')
        .map(line => {
            const bracketMatches = [...line.matchAll(/\[([^\]]+)\]/g)];
            if (
                bracketMatches.length > 0
                && bracketMatches.every(match => isPlaceholderBracket(match[1].trim()))
            ) {
                return '';
            }
            return line.replace(/\[([^\]]+)\]/g, (full, content: string) => (
                isPlaceholderBracket(content.trim()) ? '' : full
            ));
        })
        .join('\n')
        .replace(/[ \t]+\n/g, '\n')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
}

function findGuidelineCitationIssues(letter: string, guidelineCount: number): SafetyIssue[] {
    const issues: SafetyIssue[] = [];
    const numericRefs = unique(
        [...letter.matchAll(/(?<!PubMed\s)\[(\d+)\]/gi)].map(match => Number(match[1]))
    );

    for (const ref of numericRefs) {
        if (ref < 1 || ref > guidelineCount) {
            issues.push({
                code: 'INVALID_GUIDELINE_CITATION',
                severity: 'error',
                message: `Guideline citation [${ref}] does not map to any retrieved guideline source.`,
                evidence: `[${ref}]`,
            });
        }
    }

    if (guidelineCount > 0 && numericRefs.length === 0) {
        issues.push({
            code: 'MISSING_GUIDELINE_CITATIONS',
            severity: 'warning',
            message: 'Letter includes guideline context but does not cite any numbered guideline references.',
        });
    }

    return issues;
}

function findPubMedCitationIssues(letter: string, pubMedCount: number): SafetyIssue[] {
    const issues: SafetyIssue[] = [];
    const pubMedRefs = unique(
        [...letter.matchAll(/\[PubMed\s+(\d+)\]/gi)].map(match => Number(match[1]))
    );

    for (const ref of pubMedRefs) {
        if (ref < 1 || ref > pubMedCount) {
            issues.push({
                code: 'INVALID_PUBMED_CITATION',
                severity: 'error',
                message: `PubMed citation [PubMed ${ref}] does not map to any retrieved PubMed source.`,
                evidence: `[PubMed ${ref}]`,
            });
        }
    }

    return issues;
}

function quotedClaimsNeedGrounding(value: string): boolean {
    if (value.length < 8) return false;
    if (/^https?:\/\//i.test(value)) return false;
    if (HEADING_ONLY_QUOTE.test(value.trim())) return false;
    return /\d|pain|mass|lesion|deficit|stenosis|fracture|cancer|tumor|malign|biopsy|therapy|medication|exam|imaging|mri|ct|pet|x-ray|xray|lab|a1c|bmi|symptom|diagnos|criterion|requires|denial|not medically necessary/i.test(value);
}

function findQuotedClaimIssues(letter: string, sources: SafetySource[]): SafetyIssue[] {
    const issues: SafetyIssue[] = [];
    const quoted = unique(
        [...letter.matchAll(/"([^"]{4,240})"/g)]
            .map(match => match[1].trim())
            .filter(quotedClaimsNeedGrounding)
    );

    for (const quote of quoted) {
        if (!sourceContains(quote, sources)) {
            issues.push({
                code: 'UNGROUNDED_QUOTE',
                severity: 'warning',
                message: 'Quoted clinical, denial, or guideline text was not found verbatim in the supplied sources.',
                evidence: quote,
            });
        }
    }

    return issues;
}

function extractNumericFacts(text: string): string[] {
    const facts = [...text.matchAll(/\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d+(?:\.\d+)?\s?(?:%|mg\/dL|mmHg|cm|mm|kg\/m2|kg\/m²|weeks?|months?|years?|days?|hours?|\/10|points?|QALY|mL|L))\b/gi)]
        .map(match => match[0].trim())
        .filter(value => !CITATION_OR_SECTION_NUMBER.test(value));

    return unique(facts);
}

function findNumericClaimIssues(letter: string, sources: SafetySource[]): SafetyIssue[] {
    const issues: SafetyIssue[] = [];
    const numbers = extractNumericFacts(letter);

    for (const value of numbers) {
        if (!sourceContains(value, sources)) {
            issues.push({
                code: 'UNGROUNDED_NUMERIC_CLAIM',
                severity: 'warning',
                message: 'Numeric value in the letter was not found in the clinical notes, guidelines, denial reason, or PubMed context.',
                evidence: value,
            });
        }
    }

    return issues;
}

function buildSources(params: RunSafetyChecksParams): SafetySource[] {
    return [
        { label: 'clinicalNotes', text: params.clinicalNotes },
        { label: 'denialReason', text: params.denialReason || '' },
        ...(params.guidelineSources || []),
        ...(params.pubMedSources || []),
    ];
}

export function runMedicalSafetyChecks(params: RunSafetyChecksParams): SafetyReport {
    const guidelineCount = params.guidelineSources?.length || 0;
    const pubMedCount = params.pubMedSources?.length || 0;
    const allSources = buildSources(params);

    const placeholderIssues = findBracketIssues(params.letter);
    const guidelineCitationIssues = findGuidelineCitationIssues(params.letter, guidelineCount);
    const pubMedCitationIssues = findPubMedCitationIssues(params.letter, pubMedCount);
    const quotedClaimIssues = findQuotedClaimIssues(params.letter, allSources);
    const numericClaimIssues = findNumericClaimIssues(params.letter, allSources);

    const issues = [
        ...placeholderIssues,
        ...guidelineCitationIssues,
        ...pubMedCitationIssues,
        ...quotedClaimIssues,
        ...numericClaimIssues,
    ];

    const hasErrors = issues.some(issue => issue.severity === 'error');
    const hasWarnings = issues.some(issue => issue.severity === 'warning');

    return {
        verdict: hasErrors ? 'FAIL' : hasWarnings ? 'NEEDS_REVIEW' : 'PASS',
        issues,
        checks: {
            placeholderFree: placeholderIssues.length === 0,
            guidelineCitationsValid: guidelineCitationIssues.every(issue => issue.severity !== 'error'),
            pubMedCitationsValid: pubMedCitationIssues.length === 0,
            quotedClaimsGrounded: quotedClaimIssues.length === 0,
            numericClaimsGrounded: numericClaimIssues.length === 0,
        },
    };
}

export function safetyReportToVerificationChecks(report: SafetyReport) {
    return [
        {
            check: 'Deterministic Placeholder Check',
            status: report.checks.placeholderFree ? 'PASS' : 'FAIL',
            details: report.checks.placeholderFree
                ? 'No unresolved bracket placeholders were detected.'
                : report.issues.filter(i => i.code === 'UNRESOLVED_PLACEHOLDER').map(i => i.message).join(' '),
        },
        {
            check: 'Deterministic Citation Check',
            status: report.checks.guidelineCitationsValid && report.checks.pubMedCitationsValid ? 'PASS' : 'FAIL',
            details: report.checks.guidelineCitationsValid && report.checks.pubMedCitationsValid
                ? 'All numbered guideline and PubMed citations map to retrieved sources.'
                : report.issues.filter(i => i.code.includes('CITATION')).map(i => i.message).join(' '),
        },
        {
            check: 'Deterministic Grounding Check',
            status: report.checks.quotedClaimsGrounded && report.checks.numericClaimsGrounded ? 'PASS' : 'WARNING',
            details: report.checks.quotedClaimsGrounded && report.checks.numericClaimsGrounded
                ? 'Quoted and numeric claims were found in the supplied sources.'
                : report.issues.filter(i => i.code.includes('UNGROUNDED')).map(i => `${i.message} ${i.evidence || ''}`).join(' '),
        },
    ] as const;
}
