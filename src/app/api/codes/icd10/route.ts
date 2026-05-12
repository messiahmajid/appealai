import { NextRequest, NextResponse } from 'next/server';
import { searchICD10 } from '@/lib/medical-codes';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

export async function GET(request: NextRequest) {
    if (shouldUseFastAPI()) {
        return proxyToBackend(request, '/api/codes/icd10');
    }

    const query = request.nextUrl.searchParams.get('q') || '';
    const results = searchICD10(query);
    return NextResponse.json({ results });
}
