import { NextRequest, NextResponse } from 'next/server';
import { generateText, isApiKeyConfigured } from '@/lib/gemini';
import { VERIFICATION_SYSTEM, buildVerificationPrompt } from '@/lib/prompts';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';
import { runMedicalSafetyChecks, safetyReportToVerificationChecks } from '@/lib/medical-safety';

function splitGuidelineSources(ragContext: string): { label: string; text: string }[] {
    if (!ragContext.trim()) return [];

    const matches = [...ragContext.matchAll(/\[Reference\s+(\d+)\]/gi)];
    if (matches.length === 0) {
        return [{ label: 'Guideline Context', text: ragContext }];
    }

    return matches.map((match, index) => {
        const start = match.index || 0;
        const end = matches[index + 1]?.index ?? ragContext.length;
        return {
            label: `Reference ${match[1]}`,
            text: ragContext.slice(start, end),
        };
    });
}

function splitPubMedSources(ragContext: string): { label: string; text: string }[] {
    const matches = [...ragContext.matchAll(/\[PubMed\s+(\d+)\]/gi)];
    return matches.map((match, index) => {
        const start = match.index || 0;
        const end = matches[index + 1]?.index ?? ragContext.length;
        return {
            label: `PubMed ${match[1]}`,
            text: ragContext.slice(start, end),
        };
    });
}

export async function POST(request: NextRequest) {
    try {
        if (shouldUseFastAPI()) {
            return proxyToBackend(request, '/api/verify-appeal');
        }

        const { letter, clinicalNotes, ragContext, denialReason } = await request.json();

        if (!letter || !clinicalNotes || !denialReason) {
            return NextResponse.json(
                { error: 'Missing required fields: letter, clinicalNotes, denialReason' },
                { status: 400 }
            );
        }

        const deterministicReport = runMedicalSafetyChecks({
            letter,
            clinicalNotes,
            denialReason,
            guidelineSources: splitGuidelineSources(ragContext || ''),
            pubMedSources: splitPubMedSources(ragContext || ''),
        });

        const verificationPrompt = buildVerificationPrompt({
            letter,
            clinicalNotes,
            ragContext: ragContext || '',
            denialReason,
        });

        if (!isApiKeyConfigured()) {
            return NextResponse.json({
                verification: {
                    overallVerdict: deterministicReport.verdict,
                    confidenceScore: deterministicReport.verdict === 'PASS' ? 0.8 : 0.6,
                    checks: safetyReportToVerificationChecks(deterministicReport),
                    flaggedIssues: deterministicReport.issues.map(issue => `${issue.code}: ${issue.message}`),
                    summary: 'Deterministic verification completed. LLM verification was skipped because the API key is not configured.',
                    deterministicReport,
                },
            });
        }

        const verificationRaw = await generateText(VERIFICATION_SYSTEM, verificationPrompt, 0.1);
        const jsonMatch = verificationRaw.match(/\{[\s\S]*\}/);

        if (jsonMatch) {
            const verification = JSON.parse(jsonMatch[0]);
            const deterministicChecks = safetyReportToVerificationChecks(deterministicReport);
            const hasDeterministicFailure = deterministicReport.verdict === 'FAIL';
            const hasDeterministicWarnings = deterministicReport.verdict === 'NEEDS_REVIEW';
            const mergedVerdict = hasDeterministicFailure
                ? 'FAIL'
                : hasDeterministicWarnings && verification.overallVerdict === 'PASS'
                    ? 'NEEDS_REVIEW'
                    : verification.overallVerdict;

            return NextResponse.json({
                verification: {
                    ...verification,
                    overallVerdict: mergedVerdict,
                    checks: [...(verification.checks || []), ...deterministicChecks],
                    flaggedIssues: [
                        ...(verification.flaggedIssues || []),
                        ...deterministicReport.issues.map(issue => `${issue.code}: ${issue.message}`),
                    ],
                    deterministicReport,
                },
            });
        }

        return NextResponse.json(
            { error: 'Failed to parse verification response' },
            { status: 500 }
        );
    } catch (error) {
        console.error('Verification error:', error);
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Verification failed' },
            { status: 500 }
        );
    }
}
