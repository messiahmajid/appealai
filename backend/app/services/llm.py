import hashlib
import json
import os
import re
from pathlib import Path

import structlog
import httpx
from google import genai

from app.config import settings

logger = structlog.get_logger()

_RESPONSE_CACHE_DIR = Path(os.getcwd()) / ".cache" / "responses"


def _cache_key(system_prompt: str, user_prompt: str, temperature: float) -> str:
    blob = json.dumps([system_prompt, user_prompt, temperature], sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def _get_cached_response(key: str) -> str | None:
    path = _RESPONSE_CACHE_DIR / f"{key}.txt"
    if path.exists():
        logger.info("cache_hit", key=key[:12])
        return path.read_text()
    return None


def _save_cached_response(key: str, text: str) -> None:
    _RESPONSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (_RESPONSE_CACHE_DIR / f"{key}.txt").write_text(text)


OPENROUTER_MODELS = [
    "google/gemma-3-12b-it:free",
    "meta-llama/llama-3.3-8b-instruct:free",
    "qwen/qwen3-8b:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "google/gemma-3-4b-it:free",
]

_PLACEHOLDERS = {"your-api-key-here", "your_api_key_here", "your-key-here", "replace-me", ""}
_MAX_INLINE_RATE_LIMIT_WAIT_SECONDS = 20


def _is_configured(key: str) -> bool:
    return bool(key) and key.lower().strip() not in _PLACEHOLDERS


def _get_gemini_client() -> genai.Client | None:
    if not _is_configured(settings.google_generative_ai_api_key):
        return None
    return genai.Client(api_key=settings.google_generative_ai_api_key)


def _gemini_text_models() -> list[str]:
    models = [model.strip() for model in settings.gemini_text_models.split(",") if model.strip()]
    return models or ["gemini-2.0-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]


def _retry_delay_seconds(message: str) -> int | None:
    patterns = [
        r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+)s",
        r"retry_delay\s*\{\s*seconds:\s*(\d+)",
        r"Retry-After['\"]?\s*[:=]\s*['\"]?(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.I)
        if match:
            return int(match.group(1))
    return None


def _is_rate_limit_error(message: str) -> bool:
    lower = message.lower()
    return (
        "429" in message
        or "rate limit" in lower
        or "resource_exhausted" in lower
        or "quota" in lower
    )


def is_api_key_configured() -> bool:
    return (
        _is_configured(settings.google_generative_ai_api_key)
        or _is_configured(settings.anthropic_api_key)
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
    key = _cache_key(system_prompt, user_prompt, temperature)
    cached = _get_cached_response(key)
    if cached is not None:
        return cached

    result = await _generate_text_uncached(system_prompt, user_prompt, temperature)
    _save_cached_response(key, result)
    return result


async def _generate_text_uncached(
    system_prompt: str, user_prompt: str, temperature: float = 0.3
) -> str:
    # Priority 1: Gemini free-tier models. Try lower-quota-pressure models first;
    # 429s may be per-minute, per-token-minute, or per-day, so do not keep
    # waiting on one exhausted model when another configured model may still work.
    client = _get_gemini_client()
    if client:
        import asyncio

        rate_limited_models: list[str] = []
        for model in _gemini_text_models():
            for attempt in range(2):
                try:
                    response = await client.aio.models.generate_content(
                        model=model,
                        contents=f"{system_prompt}\n\n---\n\n{user_prompt}",
                        config=genai.types.GenerateContentConfig(
                            temperature=temperature,
                            max_output_tokens=8192,
                        ),
                    )
                    logger.info("generated_text", provider="gemini", model=model)
                    return response.text
                except Exception as e:
                    msg = str(e)
                    if _is_rate_limit_error(msg):
                        retry_after = _retry_delay_seconds(msg)
                        rate_limited_models.append(model)
                        if (
                            attempt == 0
                            and retry_after is not None
                            and retry_after <= _MAX_INLINE_RATE_LIMIT_WAIT_SECONDS
                        ):
                            logger.info(
                                "gemini_rate_limited_retrying",
                                model=model,
                                wait=retry_after,
                                attempt=attempt + 1,
                            )
                            await asyncio.sleep(retry_after)
                            continue
                        logger.info(
                            "gemini_model_rate_limited",
                            model=model,
                            retry_after=retry_after,
                        )
                        break

                    logger.warning("gemini_error", model=model, error=msg)
                    break

        if rate_limited_models:
            logger.warning("gemini_rate_limited_exhausted", models=sorted(set(rate_limited_models)))

    # Priority 2: Anthropic Claude 3.5 Haiku (paid)
    if _is_configured(settings.anthropic_api_key):
        try:
            import anthropic

            anthropic_client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            response = await anthropic_client.messages.create(
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

    # Priority 3: OpenRouter (free models)
    if _is_configured(settings.openrouter_api_key):
        return await _generate_via_openrouter(system_prompt, user_prompt, temperature)

    if _is_configured(settings.google_generative_ai_api_key):
        raise RuntimeError(
            "Gemini API is rate-limited for this project. This may be a per-minute, "
            "per-token-minute, or daily quota, so waiting one minute may not be enough. "
            "Check AI Studio rate limits, wait for quota reset, or add ANTHROPIC_API_KEY / "
            "OPENROUTER_API_KEY to .env as a fallback."
        )
    raise RuntimeError(
        "No API keys configured. Add GOOGLE_GENERATIVE_AI_API_KEY to .env "
        "(free — get one at https://aistudio.google.com/apikey)."
    )


def is_embedding_available() -> bool:
    return _is_configured(settings.google_generative_ai_api_key)


async def generate_embedding(text: str) -> list[float]:
    client = _get_gemini_client()
    if not client:
        raise RuntimeError("Embedding requires GOOGLE_GENERATIVE_AI_API_KEY")
    response = await client.aio.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    return response.embeddings[0].values


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    import asyncio

    client = _get_gemini_client()
    if not client:
        raise RuntimeError("Embedding requires GOOGLE_GENERATIVE_AI_API_KEY")
    results = []
    for i, text in enumerate(texts):
        for attempt in range(3):
            try:
                response = await client.aio.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text,
                )
                results.append(response.embeddings[0].values)
                break
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    wait = (attempt + 1) * 40
                    logger.info("embedding_rate_limited", waiting=wait, item=i)
                    await asyncio.sleep(wait)
                else:
                    raise
        if i > 0 and i % 5 == 0:
            await asyncio.sleep(2)
    return results
