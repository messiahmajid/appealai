import { NextRequest, NextResponse } from 'next/server';
import { getAllAppeals, getAppealStats } from '@/lib/db';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

export async function GET(request: NextRequest) {
    try {
        if (shouldUseFastAPI()) {
            return proxyToBackend(request, '/api/appeals');
        }

        const appeals = getAllAppeals();
        const stats = getAppealStats();
        return NextResponse.json({ appeals, stats });
    } catch (error) {
        console.error('Failed to fetch appeals:', error);
        return NextResponse.json({ error: 'Failed to fetch appeals' }, { status: 500 });
    }
}
