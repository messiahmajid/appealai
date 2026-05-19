import { NextRequest, NextResponse } from 'next/server';
import { proxyStreamToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

export async function POST(request: NextRequest) {
    if (shouldUseFastAPI()) {
        return proxyStreamToBackend(request, '/api/generate-appeal/stream');
    }

    return NextResponse.json(
        { error: 'Streaming generation requires the FastAPI backend. Set APPEALAI_USE_FASTAPI=true.' },
        { status: 501 },
    );
}
