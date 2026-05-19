/**
 * RAG (Retrieval-Augmented Generation) Pipeline
 * 
 * Uses Gemini text-embedding-004 for embeddings and cosine similarity
 * for retrieval over the medical guidelines knowledge base.
 * Embeddings are cached in a JSON file on disk for fast restarts.
 */

import { generateEmbedding, generateEmbeddings } from './gemini';
import { getGuidelineChunks } from './guidelines';
import * as fs from 'fs';
import * as path from 'path';

const CACHE_DIR = path.join(process.cwd(), '.cache');
const EMBEDDINGS_CACHE = path.join(CACHE_DIR, 'guideline-embeddings.json');

interface EmbeddedChunk {
    id: string;
    text: string;
    guidelineId: string;
    title: string;
    source: string;
    embedding: number[];
}

interface RAGResult {
    text: string;
    guidelineId: string;
    title: string;
    source: string;
    score: number;
}

let embeddedChunks: EmbeddedChunk[] | null = null;

function cosineSimilarity(a: number[], b: number[]): number {
    let dotProduct = 0;
    let normA = 0;
    let normB = 0;
    for (let i = 0; i < a.length; i++) {
        dotProduct += a[i] * b[i];
        normA += a[i] * a[i];
        normB += b[i] * b[i];
    }
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

function loadCachedEmbeddings(): EmbeddedChunk[] | null {
    try {
        if (fs.existsSync(EMBEDDINGS_CACHE)) {
            const data = JSON.parse(fs.readFileSync(EMBEDDINGS_CACHE, 'utf-8'));
            if (Array.isArray(data) && data.length > 0 && data[0].embedding) {
                return data;
            }
        }
    } catch {
        // Cache corrupted, will regenerate
    }
    return null;
}

function saveCachedEmbeddings(chunks: EmbeddedChunk[]): void {
    try {
        if (!fs.existsSync(CACHE_DIR)) {
            fs.mkdirSync(CACHE_DIR, { recursive: true });
        }
        fs.writeFileSync(EMBEDDINGS_CACHE, JSON.stringify(chunks));
    } catch (err) {
        console.error('Failed to save embeddings cache:', err);
    }
}

export async function initializeRAG(): Promise<void> {
    // Check if already initialized
    if (embeddedChunks) return;

    const currentChunks = getGuidelineChunks();
    const currentChunkIds = new Set(currentChunks.map(c => c.id));

    // Try loading from cache
    const cached = loadCachedEmbeddings();
    if (cached && cached.length === currentChunks.length && cached.every(c => currentChunkIds.has(c.id))) {
        embeddedChunks = cached;
        console.log(`Loaded ${cached.length} cached guideline embeddings`);
        return;
    } else if (cached) {
        console.log('Guideline corpus changed; regenerating guideline embeddings');
    }

    // Generate fresh embeddings
    console.log('Generating guideline embeddings (first run)...');
    const texts = currentChunks.map(c => c.text);

    // Batch embed in groups of 10
    const allEmbeddings: number[][] = [];
    for (let i = 0; i < texts.length; i += 10) {
        const batch = texts.slice(i, i + 10);
        const batchEmbeddings = await generateEmbeddings(batch);
        allEmbeddings.push(...batchEmbeddings);
    }

    embeddedChunks = currentChunks.map((chunk, i) => ({
        ...chunk,
        embedding: allEmbeddings[i],
    }));

    // Cache for next startup
    saveCachedEmbeddings(embeddedChunks);
    console.log(`Generated and cached ${embeddedChunks.length} guideline embeddings`);
}

export async function searchRAG(query: string, topK: number = 5): Promise<RAGResult[]> {
    if (!embeddedChunks || embeddedChunks.length === 0) {
        await initializeRAG();
    }

    if (!embeddedChunks || embeddedChunks.length === 0) {
        throw new Error('RAG pipeline not initialized — no guideline embeddings available');
    }

    // Embed the query
    const queryEmbedding = await generateEmbedding(query);

    // Compute similarity scores
    const scored = embeddedChunks.map(chunk => ({
        text: chunk.text,
        guidelineId: chunk.guidelineId,
        title: chunk.title,
        source: chunk.source,
        score: cosineSimilarity(queryEmbedding, chunk.embedding),
    }));

    // Sort by score descending and return top-k
    scored.sort((a, b) => b.score - a.score);

    // Deduplicate by guidelineId, keeping the highest-scoring chunk per guideline
    const seen = new Set<string>();
    const deduped: RAGResult[] = [];
    for (const result of scored) {
        if (!seen.has(result.guidelineId)) {
            seen.add(result.guidelineId);
            deduped.push(result);
        }
        if (deduped.length >= topK) break;
    }

    return deduped;
}

/**
 * Fallback keyword-based search when API key is not configured
 */
export function searchRAGFallback(query: string, topK: number = 5): RAGResult[] {
    const chunks = getGuidelineChunks();
    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 2);

    const scored = chunks.map(chunk => {
        const text = chunk.text.toLowerCase();
        let score = 0;
        for (const term of terms) {
            const escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            const matches = (text.match(new RegExp(escaped, 'g')) || []).length;
            score += matches;
        }
        // Normalize
        score = score / Math.max(terms.length, 1);
        return {
            text: chunk.text,
            guidelineId: chunk.guidelineId,
            title: chunk.title,
            source: chunk.source,
            score,
        };
    });

    scored.sort((a, b) => b.score - a.score);

    const seen = new Set<string>();
    const deduped: RAGResult[] = [];
    for (const result of scored) {
        if (result.score > 0 && !seen.has(result.guidelineId)) {
            seen.add(result.guidelineId);
            deduped.push(result);
        }
        if (deduped.length >= topK) break;
    }

    return deduped;
}
