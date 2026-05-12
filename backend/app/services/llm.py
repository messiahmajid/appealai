import structlog
import httpx

from app.config import settings

logger = structlog.get_logger()

OPENROUTER_MODELS = [
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "qwen/qwen3-8b:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-4b-it:free",
]

_PLACEHOLDERS = {"your-api-key-here", "your_api_key_here", "your-key-here", "replace-me", ""}


def _is_configured(key: str) -> bool:
    return bool(key) and key.lower().strip() not in _PLACEHOLDERS


def is_api_key_configured() -> bool:
    return (
        _is_configured(settings.anthropic_api_key)
        or _is_configured(settings.google_generative_ai_api_key)
        or _is_configured(settings.openrouter_api_key)
    )


async def _generate_via_openrouter(
    system_prompt: str, user_prompt: str, temperature: float
) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        for model in OPENROUTER_MODELS:
            try:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": f"{system_prompt}\n\n---\n\n{user_prompt}"}
                        ],
                        "temperature": temperature,
                        "max_tokens": 8192,
                    },
                )
                if resp.status_code == 429:
                    logger.info("openrouter_rate_limited", model=model)
                    continue
                if not resp.is_success:
                    logger.info("openrouter_failed", model=model, status=resp.status_code)
                    continue
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content:
                    logger.info("generated_text", provider="openrouter", model=model)
                    return content
            except Exception as e:
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.info("openrouter_rate_limited", model=model)
                    continue
                raise
    raise RuntimeError("All OpenRouter free models are rate-limited. Please wait and try again.")


async def generate_text(
    system_prompt: str, user_prompt: str, temperature: float = 0.3
) -> str:
    # Priority 1: Anthropic Claude 3.5 Haiku
    if _is_configured(settings.anthropic_api_key):
        try:
            import anthropic

            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await client.messages.create(
                model="claude-3-5-haiku-latest",
                max_tokens=8192,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text_block = next((b for b in response.content if b.type == "text"), None)
            if text_block:
                logger.info(
                    "generated_text",
                    provider="anthropic",
                    model="claude-3-5-haiku",
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                )
                return text_block.text
        except Exception as e:
            msg = str(e)
            if "401" in msg or "invalid" in msg.lower():
                logger.warning("anthropic_key_invalid")
            elif "429" in msg:
                logger.warning("anthropic_rate_limited")
            else:
                logger.warning("anthropic_error", error=msg)

    # Priority 2: Gemini
    if _is_configured(settings.google_generative_ai_api_key):
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.google_generative_ai_api_key)
            model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-lite",
                system_instruction=system_prompt,
                generation_config={"temperature": temperature, "max_output_tokens": 8192},
            )
            result = await model.generate_content_async(user_prompt)
            logger.info("generated_text", provider="gemini", model="gemini-2.0-flash-lite")
            return result.text
        except Exception as e:
            msg = str(e)
            if "429" in msg:
                logger.warning("gemini_rate_limited")
            else:
                logger.warning("gemini_error", error=msg)

    # Priority 3: OpenRouter
    if _is_configured(settings.openrouter_api_key):
        return await _generate_via_openrouter(system_prompt, user_prompt, temperature)

    raise RuntimeError(
        "No API keys configured. Add ANTHROPIC_API_KEY to .env "
        "(or GOOGLE_GENERATIVE_AI_API_KEY / OPENROUTER_API_KEY as free fallbacks)."
    )


async def generate_embedding(text: str) -> list[float]:
    import google.generativeai as genai

    genai.configure(api_key=settings.google_generative_ai_api_key)
    result = await genai.embed_content_async(
        model="models/text-embedding-004",
        content=text,
    )
    return result["embedding"]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    import google.generativeai as genai

    genai.configure(api_key=settings.google_generative_ai_api_key)
    results = []
    for text in texts:
        result = await genai.embed_content_async(
            model="models/text-embedding-004",
            content=text,
        )
        results.append(result["embedding"])
    return results
