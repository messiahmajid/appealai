import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.APPEALAI_BACKEND_URL || 'http://localhost:8000';

export function shouldUseFastAPI(): boolean {
    return process.env.APPEALAI_USE_FASTAPI !== 'false';
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

    const contentType = response.headers.get('content-type') || 'application/json';
    const isText = contentType.startsWith('text/') || contentType.includes('json');
    const body = isText ? await response.text() : await response.arrayBuffer();

    const respHeaders: Record<string, string> = { 'content-type': contentType };
    const disposition = response.headers.get('content-disposition');
    if (disposition) respHeaders['content-disposition'] = disposition;

    return new NextResponse(body, {
        status: response.status,
        headers: respHeaders,
    });
}

export async function proxyStreamToBackend(request: NextRequest, path: string): Promise<NextResponse> {
    const upstreamUrl = new URL(path, BACKEND_URL);
    upstreamUrl.search = request.nextUrl.search;

    const headers = new Headers(request.headers);
    headers.delete('host');

    const response = await fetch(upstreamUrl, {
        method: request.method,
        headers,
        body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.text(),
    });

    return new NextResponse(response.body, {
        status: response.status,
        headers: {
            'content-type': response.headers.get('content-type') || 'text/event-stream',
            'cache-control': response.headers.get('cache-control') || 'no-cache',
            connection: 'keep-alive',
            'x-accel-buffering': 'no',
        },
    });
}
