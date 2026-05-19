import { NextRequest } from 'next/server';
import { proxyToBackend, shouldUseFastAPI } from '@/lib/backend-proxy';

export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
    const { id } = await params;
    if (shouldUseFastAPI()) {
        return proxyToBackend(request, `/api/appeals/${id}/download`);
    }
    return new Response('Download requires FastAPI backend', { status: 501 });
}
