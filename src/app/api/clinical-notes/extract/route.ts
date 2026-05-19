import { NextRequest, NextResponse } from 'next/server';
import { inflateRawSync, inflateSync } from 'zlib';

const BACKEND_URL = process.env.APPEALAI_BACKEND_URL || 'http://localhost:8000';
const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;
const MAX_DECOMPRESSED_BYTES = 25 * 1024 * 1024;
const MAX_ZIP_ENTRIES = 200;

export const runtime = 'nodejs';

function normalizeText(text: string): string {
    return text
        .replace(/\0/g, '')
        .replace(/[ \t]+/g, ' ')
        .replace(/\n{3,}/g, '\n\n')
        .trim();
}

function decodeXml(text: string): string {
    return text
        .replace(/&lt;/g, '<')
        .replace(/&gt;/g, '>')
        .replace(/&amp;/g, '&')
        .replace(/&quot;/g, '"')
        .replace(/&apos;/g, "'");
}

function unzipEntries(buffer: Buffer): Map<string, Buffer> {
    if (buffer.length > MAX_UPLOAD_BYTES) {
        throw new Error('File is too large. Upload a file under 10 MB.');
    }
    const entries = new Map<string, Buffer>();
    let eocd = -1;
    for (let i = buffer.length - 22; i >= 0; i--) {
        if (buffer.readUInt32LE(i) === 0x06054b50) {
            eocd = i;
            break;
        }
    }
    if (eocd < 0) throw new Error('Invalid DOCX file.');

    const centralDirectorySize = buffer.readUInt32LE(eocd + 12);
    const centralDirectoryOffset = buffer.readUInt32LE(eocd + 16);
    let offset = centralDirectoryOffset;
    const end = centralDirectoryOffset + centralDirectorySize;
    let entryCount = 0;
    let decompressedTotal = 0;

    while (offset < end && buffer.readUInt32LE(offset) === 0x02014b50) {
        entryCount += 1;
        if (entryCount > MAX_ZIP_ENTRIES) {
            throw new Error('DOCX contains too many internal files.');
        }
        const method = buffer.readUInt16LE(offset + 10);
        const compressedSize = buffer.readUInt32LE(offset + 20);
        const uncompressedSize = buffer.readUInt32LE(offset + 24);
        const fileNameLength = buffer.readUInt16LE(offset + 28);
        const extraLength = buffer.readUInt16LE(offset + 30);
        const commentLength = buffer.readUInt16LE(offset + 32);
        const localHeaderOffset = buffer.readUInt32LE(offset + 42);
        const fileName = buffer.subarray(offset + 46, offset + 46 + fileNameLength).toString('utf8');

        const localNameLength = buffer.readUInt16LE(localHeaderOffset + 26);
        const localExtraLength = buffer.readUInt16LE(localHeaderOffset + 28);
        const dataStart = localHeaderOffset + 30 + localNameLength + localExtraLength;
        const compressed = buffer.subarray(dataStart, dataStart + compressedSize);

        decompressedTotal += uncompressedSize;
        if (decompressedTotal > MAX_DECOMPRESSED_BYTES) {
            throw new Error('DOCX expanded content is too large.');
        }

        if (method === 0) {
            entries.set(fileName, compressed);
        } else if (method === 8) {
            entries.set(fileName, inflateRawSync(compressed));
        }

        offset += 46 + fileNameLength + extraLength + commentLength;
    }

    return entries;
}

function extractDocxText(data: ArrayBuffer): string {
    const entries = unzipEntries(Buffer.from(data));
    const names = ['word/document.xml', ...[...entries.keys()].filter(name => /^word\/(?:header|footer)\d+\.xml$/i.test(name)).sort()];
    const paragraphs: string[] = [];

    for (const name of names) {
        const xml = entries.get(name)?.toString('utf8');
        if (!xml) continue;

        const paragraphMatches = [...xml.matchAll(/<w:p[\s\S]*?<\/w:p>/g)];
        const blocks = paragraphMatches.length > 0 ? paragraphMatches.map(match => match[0]) : [xml];

        for (const block of blocks) {
            const text = block
                .replace(/<w:tab\/>/g, '\t')
                .replace(/<w:br\/>|<w:cr\/>/g, '\n')
                .match(/<w:t[^>]*>([\s\S]*?)<\/w:t>/g)
                ?.map(part => decodeXml(part.replace(/<[^>]+>/g, '')))
                .join('') || '';
            if (text.trim()) paragraphs.push(text.trim());
        }
    }

    const text = normalizeText(paragraphs.join('\n'));
    if (!text) throw new Error('No readable text found in DOCX file.');
    return text;
}

function decodePdfLiteral(value: string): string {
    return value
        .replace(/\\\(/g, '(')
        .replace(/\\\)/g, ')')
        .replace(/\\\\/g, '\\')
        .replace(/\\n|\\r/g, '\n')
        .replace(/\\t/g, '\t')
        .replace(/\\([0-7]{1,3})/g, (_, octal) => String.fromCharCode(parseInt(octal, 8)));
}

function extractPdfText(data: ArrayBuffer): string {
    const buffer = Buffer.from(data);
    if (buffer.length > MAX_UPLOAD_BYTES) {
        throw new Error('File is too large. Upload a file under 10 MB.');
    }
    const chunks: string[] = [];
    const source = buffer.toString('latin1');
    let decompressedTotal = 0;

    for (const match of source.matchAll(/stream\r?\n([\s\S]*?)\r?\nendstream/g)) {
        const raw = Buffer.from(match[1], 'latin1');
        const streams = [raw];
        try {
            const decompressed = inflateSync(raw);
            decompressedTotal += decompressed.length;
            if (decompressedTotal > MAX_DECOMPRESSED_BYTES) {
                throw new Error('PDF expanded content is too large.');
            }
            streams.push(decompressed);
        } catch (error) {
            if (error instanceof Error && error.message.includes('too large')) {
                throw error;
            }
            // Uncompressed or unsupported stream; keep raw candidate only.
        }
        for (const stream of streams) {
            const text = stream.toString('latin1');
            for (const textMatch of text.matchAll(/\((?:\\.|[^\\)])*\)\s*Tj/g)) {
                const rawText = textMatch[0];
                chunks.push(decodePdfLiteral(rawText.slice(1, rawText.lastIndexOf(')'))));
            }
            for (const arrayMatch of text.matchAll(/\[([\s\S]*?)\]\s*TJ/g)) {
                for (const item of arrayMatch[1].matchAll(/\((?:\\.|[^\\)])*\)/g)) {
                    chunks.push(decodePdfLiteral(item[0].slice(1, -1)));
                }
            }
        }
    }

    const text = normalizeText(chunks.join(' '));
    if (!text) throw new Error('No readable text found in PDF. Scanned PDFs require OCR before upload.');
    return text;
}

function extractLocally(data: ArrayBuffer, filename: string, contentType: string): string | null {
    if (contentType.startsWith('text/') || /\.(txt|md|csv)$/i.test(filename)) {
        return normalizeText(new TextDecoder('utf-8').decode(data));
    }
    if (/\.docx$/i.test(filename) || contentType.includes('officedocument.wordprocessingml.document')) {
        return extractDocxText(data);
    }
    if (/\.pdf$/i.test(filename) || contentType === 'application/pdf') {
        return extractPdfText(data);
    }
    return null;
}

export async function POST(request: NextRequest) {
    const data = await request.arrayBuffer();
    const filename = request.headers.get('x-file-name') || '';
    const contentType = request.headers.get('content-type') || 'application/octet-stream';

    if (!data.byteLength) {
        return NextResponse.json({ error: 'No file data received.' }, { status: 400 });
    }
    if (data.byteLength > MAX_UPLOAD_BYTES) {
        return NextResponse.json({ error: 'File is too large. Upload a file under 10 MB.' }, { status: 413 });
    }

    try {
        const text = extractLocally(data, filename, contentType);
        if (text !== null) {
            return NextResponse.json({ text, fileName: filename, characterCount: text.length });
        }
    } catch (error) {
        return NextResponse.json(
            { error: error instanceof Error ? error.message : 'Unable to extract text from file.' },
            { status: 400 }
        );
    }

    try {
        const upstream = await fetch(new URL('/api/clinical-notes/extract', BACKEND_URL), {
            method: 'POST',
            headers: {
                'content-type': contentType,
                'x-file-name': filename,
            },
            body: data,
        });
        const body = await upstream.text();
        return new NextResponse(body, {
            status: upstream.status,
            headers: { 'content-type': upstream.headers.get('content-type') || 'application/json' },
        });
    } catch {
        return NextResponse.json(
            { error: 'Unsupported file type. Upload TXT, MD, CSV, DOCX, or text-based PDF.' },
            { status: 503 }
        );
    }
}
