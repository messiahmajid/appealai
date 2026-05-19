export interface ParsedDetails {
    patientName?: string;
    patientDOB?: string;
    memberId?: string;
    insuranceCompany?: string;
    claimNumber?: string;
    denialDate?: string;
    deniedService?: string;
    cptCodes?: string;
    icd10Codes?: string;
    physicianName?: string;
    practiceName?: string;
    denialReason?: string;
}

const DENIAL_SECTION_END =
    /^\s*(?:Appeal Deadline|Recommended Appeal Focus|Submitted Documentation|Clinical Notes|Provider Attestation)\s*:/im;

function clean(value: string | undefined): string | undefined {
    const cleaned = value
        ?.replace(/\*\*/g, '')
        .replace(/^[\s:,-]+|[\s,;]+$/g, '')
        .trim();
    return cleaned || undefined;
}

function firstMatch(text: string, patterns: RegExp[]): string | undefined {
    for (const pattern of patterns) {
        const match = text.match(pattern);
        const value = clean(match?.[1]);
        if (value) return value;
    }
    return undefined;
}

function sectionBetween(text: string, start: RegExp, end: RegExp): string | undefined {
    const startMatch = start.exec(text);
    if (!startMatch) return undefined;
    const afterStart = text.slice((startMatch.index || 0) + startMatch[0].length);
    const endMatch = end.exec(afterStart);
    return clean(endMatch ? afterStart.slice(0, endMatch.index) : afterStart);
}

function normalizeDate(value: string | undefined): string | undefined {
    if (!value) return undefined;
    const match = value.match(/\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b/);
    if (!match) return value;
    const year = match[3].length === 2 ? `20${match[3]}` : match[3];
    return `${match[1].padStart(2, '0')}/${match[2].padStart(2, '0')}/${year}`;
}

function extractIcd10Codes(text: string): string | undefined {
    const matches = text.match(/\b[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?\b/g) || [];
    const codes = [...new Set(matches.map(code => code.toUpperCase()))];
    return codes.length > 0 ? codes.slice(0, 12).join(', ') : undefined;
}

function normalizeCodeList(value: string | undefined, fallbackText = ''): string | undefined {
    if (!value) return extractIcd10Codes(fallbackText);
    return extractIcd10Codes(value) || extractIcd10Codes(fallbackText);
}

function extractCptCodes(text: string): string | undefined {
    const matches = text.match(/\b(?:[A-Z]\d{4}|\d{5})\b/g) || [];
    const codes = [...new Set(matches.filter(code => /^\d{5}$/.test(code) || /^[A-Z]\d{4}$/.test(code)))];
    return codes.length > 0 ? codes.slice(0, 12).join(', ') : undefined;
}

export function parseDenialDetails(text: string): ParsedDetails {
    const parsed: ParsedDetails = {};

    parsed.insuranceCompany = firstMatch(text, [
        /^\s*(?:Payer|Insurance Company|Plan)\s*:\s*(.+)$/im,
    ]);
    parsed.patientName = firstMatch(text, [
        /^\s*(?:Patient|Patient Name)\s*:\s*(.+)$/im,
    ]);
    parsed.memberId = firstMatch(text, [
        /^\s*(?:Member ID|Subscriber ID|Insurance ID)\s*:\s*(.+)$/im,
    ]);
    parsed.patientDOB = normalizeDate(firstMatch(text, [
        /^\s*(?:DOB|Date of Birth)\s*:\s*(.+)$/im,
    ]));
    parsed.physicianName = firstMatch(text, [
        /^\s*(?:Provider|Requesting Physician|Ordering\/Rendering Provider|Prescriber)\s*:\s*(.+)$/im,
    ]);
    parsed.practiceName = firstMatch(text, [
        /^\s*(?:Facility|Clinic|Practice|Practice Name)\s*:\s*(.+)$/im,
    ]);
    parsed.deniedService = firstMatch(text, [
        /^\s*(?:Requested Medication|Requested Service|Denied Service|Service|Procedure|Medication)\s*:\s*(.+)$/im,
    ]);
    parsed.icd10Codes = normalizeCodeList(firstMatch(text, [
        /^\s*(?:ICD-10|ICD10|Diagnosis Code(?:\(s\))?|ICD-10 Diagnosis Code(?:\(s\))?)\s*:\s*(.+)$/im,
    ]), text);
    const cptField = firstMatch(text, [
        /^\s*(?:CPT|CPT Code(?:\(s\))?|HCPCS|NDC)\s*:\s*(.+)$/im,
    ]);
    parsed.cptCodes = cptField ? (extractCptCodes(cptField) || clean(cptField)) : undefined;
    parsed.denialDate = normalizeDate(firstMatch(text, [
        /^\s*(?:Date of Denial|Denial Date|Decision Date)\s*:\s*(.+)$/im,
    ]));
    parsed.claimNumber = firstMatch(text, [
        /^\s*(?:Case\s*\/\s*Authorization Number|Authorization Number|Case Number|Claim\/Reference Number|Claim Number|Reference Number|PA Number)\s*:\s*(.+)$/im,
    ]);
    parsed.denialReason = sectionBetween(
        text,
        /^\s*Reason for Denial\s*:\s*/im,
        DENIAL_SECTION_END,
    );

    return parsed;
}

export function parseClinicalNoteDetails(text: string): ParsedDetails {
    const parsed: ParsedDetails = {};
    const compact = text.replace(/[ \t]+/g, ' ');

    parsed.patientName = firstMatch(text, [
        /^\s*(?:Patient|Patient Name)\s*[:\n]\s*(.+)$/im,
        /^\s*Name\s*:\s*(.+)$/im,
        /\bPatient\s+(.+?)\s+(?:DOB\s*\/\s*Age|DOB|Date of Birth)\b/i,
    ]);
    parsed.patientDOB = normalizeDate(firstMatch(text, [
        /^\s*(?:DOB\s*\/\s*Age|DOB|Date of Birth)\s*[:\n]\s*(.+)$/im,
        /\b(?:DOB\s*\/\s*Age|DOB|Date of Birth)\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})/i,
    ])?.replace(/\s*\/\s*Age\b.*$/i, ''));
    parsed.memberId = firstMatch(text, [
        /^\s*(?:Member ID|Subscriber ID|Insurance ID)\s*[:\n]\s*(.+)$/im,
    ]);
    parsed.insuranceCompany = firstMatch(text, [
        /^\s*(?:Primary Insurance|Insurance)\s*[:\n]\s*(.+)$/im,
        /\bPrimary Insurance\s+(.+?)(?:\s+Visit Type\b|\n|$)/i,
    ]);
    parsed.physicianName = firstMatch(text, [
        /^\s*(?:Ordering\/Rendering Provider|Provider|Physician)\s*[:\n]\s*(.+)$/im,
        /\bOrdering\/Rendering Provider\s+(.+?)(?:\s+Clinic\b|\n|$)/i,
    ]);
    parsed.practiceName = firstMatch(text, [
        /^\s*(?:Clinic|Facility|Practice)\s*[:\n]\s*(.+)$/im,
        /\bClinic\s+(.+?)(?:\s+Primary Insurance\b|\n|$)/i,
    ]);
    parsed.deniedService = clean(firstMatch(text, [
        /request to initiate\s+([^.;\n]+?)(?:\s+after\b|\.|;|\n)/i,
        /Start\s+([^.;\n]*?(?:Mounjaro|tirzepatide|Ozempic|Trulicity|semaglutide|dulaglutide)[^.;\n]*?)(?:\.|;|\n)/i,
        /(?:Orders|Prescriptions)[\s\S]*?[-•]\s*([^:\n]*(?:Mounjaro|tirzepatide|Ozempic|Trulicity|semaglutide|dulaglutide)[^:\n]*)/i,
        /requested (?:medication|service)\s*[:\n]\s*(.+)$/im,
    ])?.replace(/^Start\s+/i, ''));
    parsed.icd10Codes = normalizeCodeList(firstMatch(text, [
        /^\s*(?:ICD-10|ICD10)\s*:\s*(.+)$/im,
    ]), compact);

    return parsed;
}

export function mergeDetails(primary: ParsedDetails, fallback: ParsedDetails): ParsedDetails {
    return {
        ...fallback,
        ...Object.fromEntries(Object.entries(primary).filter(([, value]) => !!value)),
    };
}
