import Anthropic from '@anthropic-ai/sdk';
import { GoogleGenerativeAI, EmbedContentRequest } from '@google/generative-ai';

const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || '';
const GEMINI_KEY = process.env.GOOGLE_GENERATIVE_AI_API_KEY || '';
const GEMINI_TEXT_MODELS = (process.env.GEMINI_TEXT_MODELS || 'gemini-2.0-flash-lite,gemini-2.5-flash-lite,gemini-2.5-flash')
    .split(',')
    .map(model => model.trim())
    .filter(Boolean);
const OPENROUTER_KEY = process.env.OPENROUTER_API_KEY || '';
const MAX_INLINE_RATE_LIMIT_WAIT_SECONDS = 20;

// ===== Anthropic client =====
let anthropic: Anthropic | null = null;

function getAnthropicClient(): Anthropic {
    if (!anthropic) {
        anthropic = new Anthropic({ apiKey: ANTHROPIC_KEY });
    }
    return anthropic;
}

// ===== Gemini client =====
let genAI: GoogleGenerativeAI | null = null;

function getGeminiClient(): GoogleGenerativeAI {
    if (!genAI) {
        genAI = new GoogleGenerativeAI(GEMINI_KEY);
    }
    return genAI;
}

// ===== OpenRouter fallback =====
const OPENROUTER_MODELS = [
    'google/gemma-3-12b-it:free',
    'meta-llama/llama-3.3-8b-instruct:free',
    'qwen/qwen3-8b:free',
    'mistralai/mistral-small-3.1-24b-instruct:free',
    'google/gemma-3-4b-it:free',
];

async function generateViaOpenRouter(
    systemPrompt: string,
    userPrompt: string,
    temperature: number
): Promise<string> {
    for (const model of OPENROUTER_MODELS) {
        try {
            const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${OPENROUTER_KEY}`,
                },
                body: JSON.stringify({
                    model,
                    messages: [
                        { role: 'user', content: `${systemPrompt}\n\n---\n\n${userPrompt}` },
                    ],
                    temperature,
                    max_tokens: 8192,
                }),
            });

            if (response.status === 429) {
                console.log(`OpenRouter model ${model} rate-limited, trying next...`);
                continue;
            }

            if (!response.ok) {
                console.log(`OpenRouter model ${model} failed (${response.status}), trying next...`);
                continue;
            }

            const data = await response.json();
            const content = data.choices?.[0]?.message?.content;
            if (content) {
                console.log(`Successfully generated with OpenRouter model: ${model}`);
                return content;
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            if (msg.includes('429') || msg.includes('rate-limit')) {
                console.log(`OpenRouter model ${model} rate-limited, trying next...`);
                continue;
            }
            throw err;
        }
    }
    throw new Error('All OpenRouter free models are rate-limited. Please wait a moment and try again.');
}

function isRateLimitError(message: string): boolean {
    const lower = message.toLowerCase();
    return message.includes('429')
        || lower.includes('rate limit')
        || lower.includes('resource_exhausted')
        || lower.includes('quota');
}

function retryDelaySeconds(message: string): number | null {
    const patterns = [
        /retryDelay['"]?\s*[:=]\s*['"]?(\d+)s/i,
        /retry_delay\s*\{\s*seconds:\s*(\d+)/i,
        /Retry-After['"]?\s*[:=]\s*['"]?(\d+)/i,
    ];
    for (const pattern of patterns) {
        const match = message.match(pattern);
        if (match) return Number(match[1]);
    }
    return null;
}

function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ===== Main text generation =====
// Priority: Anthropic (Haiku) → Gemini → OpenRouter
export async function generateText(
    systemPrompt: string,
    userPrompt: string,
    temperature: number = 0.3
): Promise<string> {
    // Priority 1: Anthropic Claude 3.5 Haiku
    if (isAnthropicKeyConfigured()) {
        try {
            const client = getAnthropicClient();
            const response = await client.messages.create({
                model: 'claude-3-5-haiku-latest',
                max_tokens: 8192,
                temperature,
                system: systemPrompt,
                messages: [{ role: 'user', content: userPrompt }],
            });

            const textBlock = response.content.find(b => b.type === 'text');
            if (textBlock && textBlock.type === 'text') {
                console.log(`Generated with Claude 3.5 Haiku (input: ${response.usage.input_tokens}, output: ${response.usage.output_tokens} tokens)`);
                return textBlock.text;
            }
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : String(err);
            console.error('Anthropic API error:', msg);
            if (msg.includes('401') || msg.includes('invalid')) {
                console.log('Anthropic API key invalid, falling back...');
            } else if (msg.includes('429')) {
                console.log('Anthropic rate-limited, falling back...');
            } else {
                // For non-auth/rate errors, still try fallbacks
                console.log('Anthropic failed, falling back...');
            }
        }
    }

    // Priority 2: Gemini
    if (isGeminiKeyConfigured()) {
        const client = getGeminiClient();
        for (const modelName of GEMINI_TEXT_MODELS) {
            for (let attempt = 0; attempt < 2; attempt += 1) {
                try {
                    const model = client.getGenerativeModel({
                        model: modelName,
                        systemInstruction: systemPrompt,
                        generationConfig: { temperature, maxOutputTokens: 8192 },
                    });
                    const result = await model.generateContent(userPrompt);
                    console.log(`Generated with Gemini model: ${modelName}`);
                    return result.response.text();
                } catch (err: unknown) {
                    const msg = err instanceof Error ? err.message : String(err);
                    if (isRateLimitError(msg)) {
                        const retryAfter = retryDelaySeconds(msg);
                        if (
                            attempt === 0
                            && retryAfter !== null
                            && retryAfter <= MAX_INLINE_RATE_LIMIT_WAIT_SECONDS
                        ) {
                            console.log(`Gemini model ${modelName} rate-limited; retrying after ${retryAfter}s...`);
                            await sleep(retryAfter * 1000);
                            continue;
                        }
                        console.log(`Gemini model ${modelName} rate-limited, trying next fallback...`);
                        break;
                    }
                    console.error(`Gemini model ${modelName} error:`, msg);
                    break;
                }
            }
        }
    }

    // Priority 3: OpenRouter free models
    if (OPENROUTER_KEY && !isPlaceholder(OPENROUTER_KEY)) {
        return await generateViaOpenRouter(systemPrompt, userPrompt, temperature);
    }

    if (isGeminiKeyConfigured()) {
        throw new Error(
            'Gemini API is rate-limited for this project. This may be a per-minute, ' +
            'per-token-minute, or daily quota, so waiting one minute may not be enough. ' +
            'Check AI Studio rate limits, wait for quota reset, or add ANTHROPIC_API_KEY / ' +
            'OPENROUTER_API_KEY to .env.local as a fallback.'
        );
    }

    throw new Error('No API keys configured. Add ANTHROPIC_API_KEY to .env.local (or GOOGLE_GENERATIVE_AI_API_KEY / OPENROUTER_API_KEY as free fallbacks).');
}

// ===== Embeddings (Gemini only) =====
export async function generateEmbedding(text: string): Promise<number[]> {
    const client = getGeminiClient();
    const model = client.getGenerativeModel({ model: 'text-embedding-004' });

    const request: EmbedContentRequest = {
        content: { role: 'user', parts: [{ text }] },
    };

    const result = await model.embedContent(request);
    return result.embedding.values;
}

export async function generateEmbeddings(texts: string[]): Promise<number[][]> {
    const client = getGeminiClient();
    const model = client.getGenerativeModel({ model: 'text-embedding-004' });

    const result = await model.batchEmbedContents({
        requests: texts.map((text) => ({
            content: { role: 'user', parts: [{ text }] },
        })),
    });

    return result.embeddings.map((e) => e.values);
}

// ===== Key validation =====
function isPlaceholder(key: string): boolean {
    const placeholders = ['your-api-key-here', 'your_api_key_here', 'your-key-here', 'replace-me', ''];
    return placeholders.includes(key.toLowerCase().trim());
}

function isAnthropicKeyConfigured(): boolean {
    return !!ANTHROPIC_KEY && !isPlaceholder(ANTHROPIC_KEY);
}

function isGeminiKeyConfigured(): boolean {
    return !!GEMINI_KEY && !isPlaceholder(GEMINI_KEY);
}

export function isApiKeyConfigured(): boolean {
    return isAnthropicKeyConfigured() || isGeminiKeyConfigured() || (!!OPENROUTER_KEY && !isPlaceholder(OPENROUTER_KEY));
}
