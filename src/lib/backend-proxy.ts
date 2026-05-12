import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.APPEALAI_BACKEND_URL || 'http://localhost:8000';

export function shouldUseFastAPI(): boolean {
    return process.env.APPEALAI_USE_FASTAPI === 'true';
}

export async function proxyToBackend(request: NextRequest, path: string): Promise<NextResponse> {
    const upstreamUrl = new URL(path, BACKEND_URL);
    upstreamUrl.search = request.nextUrl.search;

    const headers = new Headers(request.headers);
    headers.delete('host');

    const response = await fetch(upstreamUrl, {
        method: request.method,
        headers,
        body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text(),
    });

    const body = await response.text();
    return new NextResponse(body, {
        status: response.status,
        headers: {
            'content-type': response.headers.get('content-type') || 'application/json',
        },
    });
}
