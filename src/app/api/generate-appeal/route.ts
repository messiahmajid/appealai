import { NextRequest, NextResponse } from 'next/server';
import { generateText, isApiKeyConfigured } from '@/lib/gemini';
import {
    APPEAL_LETTER_SYSTEM,
    buildAppealPrompt,
} from '@/lib/prompts';
import { createAppeal, updateAppeal } from '@/lib/db';
import { searchWebEvidence } from '@/lib/web-evidence';
import { retrieveGuidelineContext } from '@/lib/retrieval';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

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

        // Step 1: Create appeal record
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

        // Step 2: RAG retrieval — prefer exact code matches over loose keyword matches.
        const ragResults = retrieveGuidelineContext({
            deniedService,
            denialReason,
            cptCodes: cptCodes || '',
            icd10Codes: icd10Codes || '',
        });

        const ragContext = ragResults
            .map((r, i) => `[Reference ${i + 1}] ${r.title}\nSource: ${r.source}\nRelevance Score: ${(r.score * 100).toFixed(1)}%\n\n${r.text}`)
            .join('\n\n---\n\n');

        // Step 2b: Web evidence search (PubMed) — runs in parallel-safe manner
        let webEvidenceContext = '';
        let webEvidenceResults: { source: string; title: string; citation: string; url: string }[] = [];
        try {
            const webEvidence = await searchWebEvidence(deniedService, denialReason, cptCodes, icd10Codes);
            webEvidenceContext = webEvidence.formattedContext;
            webEvidenceResults = webEvidence.evidence.map(e => ({
                source: e.source,
                title: e.title,
                citation: e.citation,
                url: e.url,
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
        });

        const generatedLetter = await generateText(APPEAL_LETTER_SYSTEM, prompt, 0.15);

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
            status: 'completed',
            parsedClinicalData: clinicalNotes,
            generatedLetter,
            citations,
            ragSources,
        });

        return NextResponse.json({
            appealId: appeal.id,
            letter: generatedLetter,
            citations,
            ragSources,
            webEvidence: webEvidenceResults,
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
