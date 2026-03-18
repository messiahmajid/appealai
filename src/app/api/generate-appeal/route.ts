import { NextRequest, NextResponse } from 'next/server';
import { generateText, isApiKeyConfigured } from '@/lib/gemini';
import { searchRAGFallback } from '@/lib/rag';
import { getGuidelinesByCode } from '@/lib/guidelines';
import {
    APPEAL_LETTER_SYSTEM,
    buildAppealPrompt,
} from '@/lib/prompts';
import { createAppeal, updateAppeal } from '@/lib/db';
import { searchWebEvidence } from '@/lib/web-evidence';

export async function POST(request: NextRequest) {
    let appealId: string | null = null;
    try {
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

        // Step 2: RAG retrieval — code-matching first, keyword as supplement
        // Priority 1: Guidelines that match CPT or ICD-10 codes (most precise)
        const codeMatchedGuidelines = [
            ...getGuidelinesByCode(cptCodes),
            ...icd10Codes.split(',').flatMap((code: string) => getGuidelinesByCode(code.trim())),
        ];

        // Deduplicate code matches
        const seenIds = new Set<string>();
        const ragResults: { text: string; guidelineId: string; title: string; source: string; score: number }[] = [];

        for (const g of codeMatchedGuidelines) {
            if (!seenIds.has(g.id)) {
                seenIds.add(g.id);
                ragResults.push({
                    text: `[${g.title}] [Source: ${g.source}]\n${g.content}`,
                    guidelineId: g.id,
                    title: g.title,
                    source: g.source,
                    score: 1.0,
                });
            }
        }

        // Priority 2: If code matching found fewer than 2, supplement with keyword search
        if (ragResults.length < 2) {
            const ragQuery = `${deniedService} ${denialReason} ${cptCodes} ${icd10Codes}`;
            const keywordResults = searchRAGFallback(ragQuery, 3);
            for (const r of keywordResults) {
                if (!seenIds.has(r.guidelineId)) {
                    seenIds.add(r.guidelineId);
                    ragResults.push(r);
                }
            }
        }

        // Cap at 3 most relevant guidelines to reduce noise and prompt size
        ragResults.splice(3);

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
