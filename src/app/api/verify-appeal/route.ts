import { NextRequest, NextResponse } from 'next/server';
import { generateText, isApiKeyConfigured } from '@/lib/gemini';
import { VERIFICATION_SYSTEM, buildVerificationPrompt } from '@/lib/prompts';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

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

        if (!isApiKeyConfigured()) {
            return NextResponse.json(
                { error: 'API key not configured' },
                { status: 500 }
            );
        }

        const verificationPrompt = buildVerificationPrompt({
            letter,
            clinicalNotes,
            ragContext: ragContext || '',
            denialReason,
        });

        const verificationRaw = await generateText(VERIFICATION_SYSTEM, verificationPrompt, 0.1);
        const jsonMatch = verificationRaw.match(/\{[\s\S]*\}/);

        if (jsonMatch) {
            const verification = JSON.parse(jsonMatch[0]);
            return NextResponse.json({ verification });
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
