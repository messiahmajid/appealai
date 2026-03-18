import { NextRequest, NextResponse } from 'next/server';
import { searchICD10 } from '@/lib/medical-codes';

export async function GET(request: NextRequest) {
    const query = request.nextUrl.searchParams.get('q') || '';
    const results = searchICD10(query);
    return NextResponse.json({ results });
}
