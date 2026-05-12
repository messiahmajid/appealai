import { NextRequest, NextResponse } from 'next/server';
import { searchCPT } from '@/lib/medical-codes';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

export async function GET(request: NextRequest) {
    if (shouldUseFastAPI()) {
        return proxyToBackend(request, '/api/codes/cpt');
    }

    const query = request.nextUrl.searchParams.get('q') || '';
    const results = searchCPT(query);
    return NextResponse.json({ results });
}
