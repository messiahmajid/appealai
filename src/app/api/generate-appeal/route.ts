import { NextRequest, NextResponse } from 'next/server';
import { generateText, isApiKeyConfigured } from '@/lib/gemini';
import {
    APPEAL_LETTER_SYSTEM,
    APPEAL_REPAIR_SYSTEM,
    buildAppealPrompt,
    buildRepairPrompt,
} from '@/lib/prompts';
import { createAppeal, updateAppeal } from '@/lib/db';
import { searchWebEvidence } from '@/lib/web-evidence';
import { retrieveGuidelineContext } from '@/lib/retrieval';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';
import { runMedicalSafetyChecks, sanitizeGeneratedLetter } from '@/lib/medical-safety';
import { assessClinicalNoteSufficiency, buildStructuredMedicalAnalysis, formatStructuredAnalysisForPrompt } from '@/lib/medical-analysis';

export async function POST(request: NextRequest) {
    let appealId: string | null = null;
    try {
        if (shouldUseFastAPI()) {
            return proxyToBackend(request, '/api/generate-appeal');
        }

        const body = await request.json();
        const {
            clinicalNotes,
            denialReason,
            deniedService,
            cptCodes,
            icd10Codes,
            insuranceCompany,
            patientName,
            patientDOB,
            memberId,
            claimNumber,
            denialDate,
            physicianName,
            physicianNPI,
            practiceName,
        } = body;

        if (!clinicalNotes || !denialReason || !deniedService) {
            return NextResponse.json(
                { error: 'Missing required fields: clinicalNotes, denialReason, deniedService' },
                { status: 400 }
            );
        }

        if (!isApiKeyConfigured()) {
            return NextResponse.json(
                { error: 'Gemini API key not configured. Set GOOGLE_GENERATIVE_AI_API_KEY in .env.local' },
                { status: 500 }
            );
        }

        // Step 1: RAG retrieval and deterministic sufficiency check before any LLM call.
        const ragResults = retrieveGuidelineContext({
            deniedService,
            denialReason,
            cptCodes: cptCodes || '',
            icd10Codes: icd10Codes || '',
        });
        const structuredAnalysis = buildStructuredMedicalAnalysis({ clinicalNotes, ragResults });
        const sufficiencyReport = assessClinicalNoteSufficiency({
            clinicalNotes,
            deniedService,
            denialReason,
            structuredAnalysis,
        });
        if (sufficiencyReport.status === 'block') {
            return NextResponse.json(
                {
                    error: sufficiencyReport.summary,
                    sufficiencyReport,
                },
                { status: 422 },
            );
        }

        // Step 2: Create appeal record after the notes clear the sufficiency gate.
        const appeal = createAppeal({
            patientName: patientName || 'Unknown',
            patientDOB: patientDOB || '',
            memberId: memberId || '',
            insuranceCompany: insuranceCompany || '',
            claimNumber: claimNumber || '',
            denialDate: denialDate || '',
            denialReason,
            deniedService,
            cptCodes: cptCodes || '',
            icd10Codes: icd10Codes || '',
            physicianName: physicianName || '',
            physicianNPI: physicianNPI || '',
            practiceName: practiceName || '',
            clinicalNotes,
        });

        appealId = appeal.id;
        updateAppeal(appeal.id, { status: 'generating' });

        const ragContext = ragResults
            .map((r, i) => `[Reference ${i + 1}] ${r.title}\nSource: ${r.source}\nRelevance Score: ${(r.score * 100).toFixed(1)}%\n\n${r.text}`)
            .join('\n\n---\n\n');
        const structuredAnalysisContext = formatStructuredAnalysisForPrompt(structuredAnalysis);

        // Step 2b: Web evidence search (PubMed) — runs in parallel-safe manner
        let webEvidenceContext = '';
        let webEvidenceResults: { source: string; title: string; citation: string; url: string; evidenceLevel?: string }[] = [];
        let webEvidenceSources: { label: string; text: string }[] = [];
        try {
            const webEvidence = await searchWebEvidence(deniedService, denialReason, cptCodes, icd10Codes);
            webEvidenceContext = webEvidence.formattedContext;
            webEvidenceSources = webEvidence.evidence.map((e, i) => ({
                label: `PubMed ${i + 1}`,
                text: `${e.title}\n${e.citation}\n${e.summary}\n${e.url}`,
            }));
            webEvidenceResults = webEvidence.evidence.map(e => ({
                source: e.source,
                title: e.title,
                citation: e.citation,
                url: e.url,
                evidenceLevel: e.evidenceLevel,
            }));
            if (webEvidence.evidence.length > 0) {
                console.log(`Found ${webEvidence.evidence.length} PubMed articles for web evidence`);
            }
        } catch (err) {
            console.error('Web evidence search failed (non-blocking):', err);
        }

        // Step 3: Generate appeal letter
        const prompt = buildAppealPrompt({
            clinicalNotes,
            parsedData: clinicalNotes,
            denialReason,
            deniedService,
            cptCode: cptCodes,
            icd10Codes,
            insuranceCompany,
            patientName,
            patientDOB,
            memberId,
            claimNumber,
            denialDate,
            physicianName,
            physicianNPI,
            practiceName,
            ragContext,
            webEvidenceContext,
            structuredAnalysisContext,
        });

        let generatedLetter = sanitizeGeneratedLetter(await generateText(APPEAL_LETTER_SYSTEM, prompt, 0.15));

        let safetyReport = runMedicalSafetyChecks({
            letter: generatedLetter,
            clinicalNotes,
            denialReason,
            guidelineSources: ragResults.map((r, i) => ({
                label: `Reference ${i + 1}`,
                text: `${r.title}\n${r.source}\n${r.text}`,
            })),
            pubMedSources: webEvidenceSources,
        });

        if (safetyReport.verdict === 'FAIL') {
            const repairedLetter = await generateText(
                APPEAL_REPAIR_SYSTEM,
                buildRepairPrompt({
                    letter: generatedLetter,
                    clinicalNotes,
                    ragContext,
                    webEvidenceContext,
                    safetyReport,
                }),
                0.05
            );
            generatedLetter = sanitizeGeneratedLetter(repairedLetter);
            safetyReport = {
                ...runMedicalSafetyChecks({
                    letter: generatedLetter,
                    clinicalNotes,
                    denialReason,
                    guidelineSources: ragResults.map((r, i) => ({
                        label: `Reference ${i + 1}`,
                        text: `${r.title}\n${r.source}\n${r.text}`,
                    })),
                    pubMedSources: webEvidenceSources,
                }),
                repairAttempted: true,
                preRepairVerdict: safetyReport.verdict,
            } as typeof safetyReport & { repairAttempted: boolean; preRepairVerdict: string };
        }

        // Step 4: Build citations
        const citations = ragResults.map((r, i) => ({
            index: i + 1,
            guidelineId: r.guidelineId,
            title: r.title,
            source: r.source,
            text: r.text.substring(0, 300) + '...',
        }));

        const ragSources = ragResults.map(r => ({
            guidelineId: r.guidelineId,
            title: r.title,
            source: r.source,
            relevanceScore: r.score,
        }));

        // Step 5: Update appeal with results
        updateAppeal(appeal.id, {
            status: safetyReport.verdict === 'FAIL' ? 'failed' : 'completed',
            parsedClinicalData: clinicalNotes,
            generatedLetter,
            citations,
            ragSources,
            safetyReport: {
                ...safetyReport,
                structuredAnalysis,
                clinicalSufficiency: sufficiencyReport,
            },
        });

        return NextResponse.json({
            appealId: appeal.id,
            letter: generatedLetter,
            citations,
            ragSources,
            webEvidence: webEvidenceResults,
            safetyReport: {
                ...safetyReport,
                structuredAnalysis,
                clinicalSufficiency: sufficiencyReport,
            },
            clinicalSufficiencyReport: sufficiencyReport,
            parsedClinicalData: clinicalNotes,
        });
    } catch (error) {
        console.error('Appeal generation error:', error);
        if (appealId) {
            try { updateAppeal(appealId, { status: 'failed' }); } catch { /* ignore */ }
        }
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Failed to generate appeal letter' },
            { status: 500 }
        );
    }
}
