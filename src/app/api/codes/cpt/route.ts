import { NextRequest, NextResponse } from 'next/server';
import { searchCPT } from '@/lib/medical-codes';

export async function GET(request: NextRequest) {
    const query = request.nextUrl.searchParams.get('q') || '';
    const results = searchCPT(query);
    return NextResponse.json({ results });
}
