import { getGuidelineById } from '@/lib/guidelines';
import type { RetrievedGuideline } from '@/lib/retrieval';

export type CriterionStatus = 'met' | 'unclear' | 'not_met';

export interface EvidenceSpan {
    id: string;
    text: string;
    category: 'diagnosis' | 'imaging' | 'treatment' | 'functional' | 'risk' | 'medication' | 'provider' | 'other';
    start: number;
    end: number;
}

export interface CriterionAssessment {
    guidelineId: string;
    guidelineTitle: string;
    criterion: string;
    status: CriterionStatus;
    evidenceSpanIds: string[];
    missingElements: string[];
    rationale: string;
}

export interface PolicyMetadata {
    guidelineId: string;
    title: string;
    source: string;
    effectiveDate: string;
    lastReviewed: string;
    policyType: 'CMS_NCD' | 'CMS_LCD' | 'NCCN' | 'COMMERCIAL_POLICY' | 'OTHER';
    freshnessStatus: 'current' | 'review_due' | 'stale';
}

export interface StructuredMedicalAnalysis {
    evidenceSpans: EvidenceSpan[];
    criteria: CriterionAssessment[];
    documentationGaps: string[];
    contraindicationWarnings: string[];
    policyMetadata: PolicyMetadata[];
    auditTrail: {
        generatedAt: string;
        promptVersion: string;
        safetyPolicyVersion: string;
        modelRole: string;
        sourceGuidelineIds: string[];
    };
}

export type ClinicalSufficiencyStatus = 'pass' | 'needs_review' | 'block';

export interface ClinicalSufficiencyReport {
    status: ClinicalSufficiencyStatus;
    score: number;
    summary: string;
    presentElements: string[];
    missingElements: string[];
    blockingReasons: string[];
    suggestions: string[];
    warnings: string[];
}

const STOP_WORDS = new Set([
    'the', 'and', 'for', 'with', 'that', 'this', 'from', 'when', 'then', 'than', 'have', 'has',
    'had', 'are', 'was', 'were', 'been', 'being', 'patient', 'documented', 'documentation',
    'required', 'requires', 'including', 'include', 'criteria', 'criterion', 'covered',
]);

function tokenize(text: string): string[] {
    return text
        .toLowerCase()
        .split(/[^a-z0-9.]+/)
        .map(t => t.trim())
        .filter(t => t.length >= 4 && !STOP_WORDS.has(t));
}

function categorizeEvidence(text: string): EvidenceSpan['category'] {
    if (/provider|prescriber|physician|clinician|endocrinolog|diabetes specialist|\bFACE\b|ordering\/rendering|clinic|practice|facility/i.test(text)) return 'provider';
    if (/diagnos|icd|cancer|osteoarthritis|stenosis|spondylolisthesis|apnea|diabetes|obesity|malignan/i.test(text)) return 'diagnosis';
    if (/mri|ct|pet|x-?ray|radiograph|imaging|biopsy|patholog|lab|a1c|ahi/i.test(text)) return 'imaging';
    if (/therapy|pt\b|nsaid|injection|conservative|surgery|medication|trial|failed|treatment/i.test(text)) return 'treatment';
    if (/adl|walking|stairs|function|womac|koos|pain|vas|limitation|mobility/i.test(text)) return 'functional';
    if (/risk|bmi|smok|hypertension|contraindicat|infection|cardiac/i.test(text)) return 'risk';
    if (/mg|dose|methotrexate|biologic|cpap|drug|medication/i.test(text)) return 'medication';
    return 'other';
}

export function extractEvidenceSpans(clinicalNotes: string): EvidenceSpan[] {
    const spans: EvidenceSpan[] = [];
    const pattern = /[^\n.!?;:]{8,260}(?:[.!?;:]|\n|$)/g;
    let match: RegExpExecArray | null;
    let index = 1;

    while ((match = pattern.exec(clinicalNotes)) !== null) {
        const text = match[0].trim();
        if (!text || !/\d|diagnos|pain|failed|therapy|mri|ct|pet|x-?ray|biopsy|lab|symptom|function|medication|risk|plan|recommend|conservative|provider|prescriber|physician|clinician|endocrinolog|diabetes specialist|\bFACE\b|ordering\/rendering|clinic|practice|facility/i.test(text)) {
            continue;
        }

        spans.push({
            id: `E${index++}`,
            text,
            category: categorizeEvidence(text),
            start: match.index,
            end: match.index + match[0].length,
        });
    }

    return spans.slice(0, 80);
}

function overlapScore(criterion: string, span: EvidenceSpan): number {
    const criterionTokens = new Set(tokenize(criterion));
    const spanTokens = new Set(tokenize(span.text));
    let score = 0;
    for (const token of criterionTokens) {
        if (spanTokens.has(token)) score += 1;
    }
    if (/\bfailed|failure|conservative|therapy|treatment\b/i.test(criterion) && /\bfailed|failure|conservative|therapy|treatment\b/i.test(span.text)) score += 2;
    if (/\bpain|functional|adl|walking|mobility\b/i.test(criterion) && /\bpain|functional|adl|walking|mobility\b/i.test(span.text)) score += 2;
    if (/\bimaging|radiograph|mri|ct|pet|biopsy|patholog\b/i.test(criterion) && /\bimaging|radiograph|mri|ct|pet|biopsy|patholog\b/i.test(span.text)) score += 2;
    if (/\bdiagnos|confirmed|malignan|osteoarthritis|cancer\b/i.test(criterion) && /\bdiagnos|confirmed|malignan|osteoarthritis|cancer\b/i.test(span.text)) score += 2;
    if (/\bprescriber|specialist|endocrinologist|clinician|provider|physician\b/i.test(criterion) && /\bprovider|prescriber|physician|clinician|endocrinolog|diabetes specialist|FACE|clinic|practice|facility\b/i.test(span.text)) score += 3;
    return score;
}

function missingElementsFor(criterion: string, matched: EvidenceSpan[]): string[] {
    if (matched.length > 0) return [];
    const lower = criterion.toLowerCase();
    const missing: string[] = [];
    if (/diagnos|confirmed|malignan|patholog|biopsy/.test(lower)) missing.push('documented diagnosis/pathology confirmation');
    if (/imaging|radiograph|mri|ct|pet/.test(lower)) missing.push('supporting imaging or test result');
    if (/failed|conservative|therapy|treatment|months|weeks/.test(lower)) missing.push('duration and outcome of conservative treatment');
    if (/functional|adl|pain|vas|womac|mobility/.test(lower)) missing.push('functional limitation or pain severity documentation');
    if (/optimized|bmi|a1c|smoking|clearance/.test(lower)) missing.push('medical optimization or risk-factor documentation');
    if (/prescriber|specialist|endocrinologist|clinician|provider|physician/.test(lower)) missing.push('specialist or prescribing clinician documentation');
    return missing.length > 0 ? missing : ['specific chart evidence supporting this criterion'];
}

function classifyCriterion(criterion: string, matched: EvidenceSpan[]): CriterionStatus {
    if (/non-covered|not covered|contraindicat/i.test(criterion)) return 'not_met';
    // Keyword overlap is a retrieval signal, not proof that all required clinical
    // elements are satisfied. Keep matches as clinician-reviewable unless a later
    // element-level validator can prove exact thresholds/durations.
    if (matched.length > 0) return 'unclear';
    return 'unclear';
}

function policyType(source: string): PolicyMetadata['policyType'] {
    if (/National Coverage Determination|NCD/i.test(source)) return 'CMS_NCD';
    if (/Local Coverage Determination|LCD/i.test(source)) return 'CMS_LCD';
    if (/National Comprehensive Cancer Network|NCCN/i.test(source)) return 'NCCN';
    if (/Commercial/i.test(source)) return 'COMMERCIAL_POLICY';
    return 'OTHER';
}

function freshnessStatus(effectiveDate: string): PolicyMetadata['freshnessStatus'] {
    const effective = new Date(effectiveDate);
    if (Number.isNaN(effective.getTime())) return 'review_due';
    const ageDays = (Date.now() - effective.getTime()) / 86400000;
    if (ageDays > 900) return 'stale';
    if (ageDays > 365) return 'review_due';
    return 'current';
}

function contraindicationWarnings(guidelines: RetrievedGuideline[], clinicalNotes: string): string[] {
    const warnings: string[] = [];
    const note = clinicalNotes.toLowerCase();
    for (const result of guidelines) {
        const nonCovered = result.text.match(/Non-Covered Indications:[\s\S]*?(?=\n\n[A-Z][A-Za-z ]+:|\n\n[A-Z][A-Za-z ]+\n|$)/i)?.[0] || '';
        if (!nonCovered) continue;
        for (const line of nonCovered.split('\n').map(l => l.replace(/^[-\d.\s]+/, '').trim()).filter(Boolean)) {
            const terms = tokenize(line).slice(0, 6);
            if (terms.length >= 2 && terms.some(term => note.includes(term))) {
                warnings.push(`${result.title}: possible non-covered indication overlap - ${line}`);
            }
        }
    }
    return warnings.slice(0, 10);
}

function hasPattern(text: string, pattern: RegExp): boolean {
    return pattern.test(text);
}

function payerRequirementSuggestions(denialReason: string, clinicalNotes: string): string[] {
    const denial = denialReason.toLowerCase();
    const notes = clinicalNotes.toLowerCase();
    const suggestions: string[] = [];

    if (/metformin/.test(denial) && !/metformin/.test(notes)) {
        suggestions.push('Document metformin use, intolerance, contraindication, or the clinical reason it is inappropriate.');
    }
    if (/\b(ozempic|trulicity|glp-?1|preferred formulary|step therapy)\b/.test(denial)
        && !/\b(ozempic|trulicity|semaglutide|dulaglutide|liraglutide|glp-?1)\b/.test(notes)) {
        suggestions.push('Document preferred formulary or step-therapy trials, failures, intolerance, or contraindications.');
    }
    if (/\bweight loss|solely for weight\b/.test(denial) && !/\b(type 2 diabetes|diabetes|a1c|hba1c|e11\.)\b/.test(notes)) {
        suggestions.push('Document that the requested drug is for type 2 diabetes or another covered indication, not solely weight loss.');
    }
    if (/\bconservative|physical therapy|nsaid|therapy\b/.test(denial)
        && !/\b(failed|tried|trial|completed|physical therapy|pt\b|nsaid|injection|conservative)\b/.test(notes)) {
        suggestions.push('Document conservative treatment attempts with dates, duration, response, and reason for failure.');
    }
    if (/\bimaging|x-?ray|mri|ct|radiograph\b/.test(denial)
        && !/\b(x-?ray|radiograph|mri|ct|ultrasound|imaging|report)\b/.test(notes)) {
        suggestions.push('Add relevant imaging or test results, including date and impression.');
    }

    return suggestions;
}

export function assessClinicalNoteSufficiency(params: {
    clinicalNotes: string;
    deniedService: string;
    denialReason: string;
    structuredAnalysis?: StructuredMedicalAnalysis;
}): ClinicalSufficiencyReport {
    const notes = params.clinicalNotes.trim();
    const evidenceSpans = params.structuredAnalysis?.evidenceSpans || extractEvidenceSpans(notes);
    const lower = notes.toLowerCase();

    const elements = [
        {
            key: 'diagnosis',
            label: 'Diagnosis or covered indication',
            weight: 20,
            present: hasPattern(lower, /\b(diagnos|assessment|impression|icd-?10|dx\b|type 2 diabetes|diabetes|osteoarthritis|cancer|malignan|angina|stenosis|sleep apnea|e11\.)\b/i)
                || evidenceSpans.some(span => span.category === 'diagnosis'),
            suggestion: 'Add the diagnosis/covered indication and ICD-10 code when available.',
        },
        {
            key: 'objective',
            label: 'Objective findings, labs, imaging, or measured severity',
            weight: 20,
            present: hasPattern(lower, /\b(a1c|hba1c|bmi|ldl|ef|ahi|kellgren|grade|stage|mm|cm|x-?ray|radiograph|mri|ct|pet|biopsy|pathology|stress test|echo|ultrasound|\d+\/10|%|\d+\.\d+)\b/i)
                || evidenceSpans.some(span => span.category === 'imaging'),
            suggestion: 'Add objective support such as labs, imaging/test reports, measured severity, or dated exam findings.',
        },
        {
            key: 'treatment',
            label: 'Prior treatment history, failure, intolerance, or contraindication',
            weight: 20,
            present: hasPattern(lower, /\b(failed|failure|tried|trial|completed|intoler|contraindicat|therapy|physical therapy|pt\b|nsaid|injection|medication|metformin|insulin|ozempic|trulicity|empagliflozin|glipizide|statin)\b/i)
                || evidenceSpans.some(span => span.category === 'treatment' || span.category === 'medication'),
            suggestion: 'Add prior therapies with dates/duration, outcome, intolerance, contraindication, or reason alternatives are inappropriate.',
        },
        {
            key: 'timeline',
            label: 'Dates or treatment duration',
            weight: 15,
            present: hasPattern(lower, /\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d+\s*(day|days|week|weeks|month|months|year|years)\b|\bsince\b|\bfrom\b/i),
            suggestion: 'Add dates and durations for symptoms, medication trials, procedures, and failed treatments.',
        },
        {
            key: 'symptoms',
            label: 'Symptoms, functional impact, or clinical risk',
            weight: 15,
            present: hasPattern(lower, /\b(pain|symptom|dyspnea|angina|hypoglycemia|infection|walking|stairs|adl|function|limitation|worsening|risk|comorbid|hypertension|obesity|cardiac)\b/i)
                || evidenceSpans.some(span => span.category === 'functional' || span.category === 'risk'),
            suggestion: 'Add symptom severity, functional limitations, clinical risk, or impact on daily activities.',
        },
        {
            key: 'plan',
            label: 'Clear request, plan, or medical rationale',
            weight: 10,
            present: hasPattern(lower, /\b(plan|recommend|request|requires|medical necessity|medically necessary|prescribed|initiate|proceed|refer)\b/i)
                || lower.includes(params.deniedService.toLowerCase()),
            suggestion: 'Add the requested service/drug and the clinician rationale for why it is medically necessary now.',
        },
    ];

    const presentElements = elements.filter(e => e.present).map(e => e.label);
    const missingElements = elements.filter(e => !e.present).map(e => e.label);
    const suggestions = [
        ...elements.filter(e => !e.present).map(e => e.suggestion),
        ...payerRequirementSuggestions(params.denialReason, notes),
    ];
    const score = Math.min(100, elements.reduce((sum, e) => sum + (e.present ? e.weight : 0), 0) + Math.min(10, evidenceSpans.length));
    const blockingReasons: string[] = [];

    if (notes.length < 120) {
        blockingReasons.push('Clinical notes are too short to support a medically grounded appeal.');
    }
    if (!elements[0].present && !elements[1].present) {
        blockingReasons.push('Clinical notes do not clearly document a diagnosis/indication or objective clinical support.');
    }
    if (score < 45) {
        blockingReasons.push('Clinical notes are missing too many core medical-necessity elements.');
    }

    const uniqueSuggestions = [...new Set(suggestions)].slice(0, 8);
    const warnings = [
        ...payerRequirementSuggestions(params.denialReason, notes),
        ...(params.structuredAnalysis?.contraindicationWarnings || []),
    ];
    const status: ClinicalSufficiencyStatus = blockingReasons.length > 0
        ? 'block'
        : score < 75 || uniqueSuggestions.length > 0
            ? 'needs_review'
            : 'pass';

    return {
        status,
        score,
        summary: status === 'block'
            ? 'The clinical notes are not sufficient to generate a medically grounded appeal yet.'
            : status === 'needs_review'
                ? 'The clinical notes can be used, but adding the missing details would strengthen the appeal.'
                : 'The clinical notes contain the core elements needed for a grounded appeal.',
        presentElements,
        missingElements,
        blockingReasons,
        suggestions: uniqueSuggestions,
        warnings: [...new Set(warnings)].slice(0, 8),
    };
}

export function buildStructuredMedicalAnalysis(params: {
    clinicalNotes: string;
    ragResults: RetrievedGuideline[];
}): StructuredMedicalAnalysis {
    const evidenceSpans = extractEvidenceSpans(params.clinicalNotes);
    const criteria: CriterionAssessment[] = [];
    const policyMetadata: PolicyMetadata[] = [];

    for (const result of params.ragResults) {
        const guideline = getGuidelineById(result.guidelineId);
        const approvalCriteria = guideline?.approvalCriteria || [];

        if (guideline) {
            policyMetadata.push({
                guidelineId: guideline.id,
                title: guideline.title,
                source: guideline.source,
                effectiveDate: guideline.effectiveDate,
                lastReviewed: new Date().toISOString().slice(0, 10),
                policyType: policyType(guideline.source),
                freshnessStatus: freshnessStatus(guideline.effectiveDate),
            });
        }

        for (const criterion of approvalCriteria) {
            const ranked = evidenceSpans
                .map(span => ({ span, score: overlapScore(criterion, span) }))
                .filter(item => item.score >= 2)
                .sort((a, b) => b.score - a.score)
                .slice(0, 3)
                .map(item => item.span);

            const status = classifyCriterion(criterion, ranked);
            const missing = missingElementsFor(criterion, ranked);
            criteria.push({
                guidelineId: result.guidelineId,
                guidelineTitle: result.title,
                criterion,
                status,
                evidenceSpanIds: ranked.map(span => span.id),
                missingElements: missing,
                rationale: ranked.length > 0
                    ? `Candidate chart evidence span(s): ${ranked.map(span => span.id).join(', ')}. Clinician review required before treating the criterion as met.`
                    : `No direct chart evidence found for: ${missing.join(', ')}.`,
            });
        }
    }

    const documentationGaps = criteria
        .filter(c => c.status !== 'met')
        .flatMap(c => c.missingElements.map(m => `${c.guidelineTitle}: ${m}`));

    return {
        evidenceSpans,
        criteria,
        documentationGaps: [...new Set(documentationGaps)].slice(0, 20),
        contraindicationWarnings: contraindicationWarnings(params.ragResults, params.clinicalNotes),
        policyMetadata,
        auditTrail: {
            generatedAt: new Date().toISOString(),
            promptVersion: 'appeal-v2-structured-criteria',
            safetyPolicyVersion: 'medical-safety-v2',
            modelRole: 'drafting-support-with-deterministic-grounding-checks',
            sourceGuidelineIds: params.ragResults.map(r => r.guidelineId),
        },
    };
}

export function formatStructuredAnalysisForPrompt(analysis: StructuredMedicalAnalysis): string {
    return JSON.stringify({
        instructions: 'Use this as a planning aid. Do not cite this JSON as a source. Cite only Source A/B/C. If a criterion is unclear or not_met, state a documentation gap instead of claiming it is met.',
        evidenceSpans: analysis.evidenceSpans.map(span => ({
            id: span.id,
            category: span.category,
            text: span.text,
        })),
        criteria: analysis.criteria,
        documentationGaps: analysis.documentationGaps,
        contraindicationWarnings: analysis.contraindicationWarnings,
        policyMetadata: analysis.policyMetadata,
    }, null, 2);
}
