import { NextResponse } from 'next/server';
import { getAllAppeals, getAppealStats } from '@/lib/db';

export async function GET() {
    try {
        const appeals = getAllAppeals();
        const stats = getAppealStats();
        return NextResponse.json({ appeals, stats });
    } catch (error) {
        console.error('Failed to fetch appeals:', error);
        return NextResponse.json({ error: 'Failed to fetch appeals' }, { status: 500 });
    }
}
