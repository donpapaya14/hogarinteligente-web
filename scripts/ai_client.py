"""
AI client: round-robin Groq / GitHub / NVIDIA.
Distribuye carga entre proveedores para maximizar tokens gratuitos.
Fallback inmediato si uno falla — timeout por llamada, sin retries SDK.
"""

import json
import logging
import os
import re as _re
import time

from groq import Groq
from openai import OpenAI

log = logging.getLogger(__name__)

GROQ_MODEL = "llama-3.3-70b-versatile"
# GitHub Models clasifica por tier de rate limit: los "high" (DeepSeek-V3) dan
# 8 peticiones al DÍA en el plan gratuito, los "low" dan 1000.
GITHUB_MODEL = "openai/gpt-4.1-mini"
GITHUB_BASE_URL = "https://models.github.ai/inference"
# NVIDIA: v4-flash es rápido pero inestable (504), llama-3.3 es lento pero fiable
NVIDIA_FAST = "meta/llama-3.1-8b-instruct"
NVIDIA_STABLE = "meta/llama-3.3-70b-instruct"

# Orden: Groq (rápido) → GitHub (fiable) → NVIDIA (generoso, último recurso)
PROVIDERS = ["groq", "github", "nvidia"]
_call_count = 0


def _parse_json(text: str) -> dict:
    """Limpia markdown/think tags y parsea JSON."""
    text = text.strip()
    if "<think>" in text:
        text = _re.sub(r"<think>.*?</think>", "", text, flags=_re.DOTALL).strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    text = _re.sub(r"[\x00--]", "", text)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return json.loads(text.strip(), strict=False)


def _call_groq(prompt: str, temperature: float = 0.7) -> dict:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY no configurada")
    client = Groq(api_key=key, timeout=60.0, max_retries=0)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=temperature,
        max_tokens=8192,
    )
    return json.loads(response.choices[0].message.content)


def _call_github(prompt: str, temperature: float = 0.7) -> dict:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN no configurado")
    client = OpenAI(
        base_url=GITHUB_BASE_URL,
        api_key=token,
        timeout=120.0,
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=GITHUB_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=8192,
    )
    return _parse_json(response.choices[0].message.content)


def _call_nvidia(prompt: str, temperature: float = 0.7) -> dict:
    """NVIDIA: intenta v4-flash (rápido), si 504 → llama-3.3 (estable)."""
    key = os.getenv("NVIDIA_API_KEY")
    if not key:
        raise ValueError("NVIDIA_API_KEY no configurada")
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=key,
        timeout=90.0,
        max_retries=0,
    )
    # Intento 1: v4-flash (rápido cuando funciona)
    try:
        response = client.chat.completions.create(
            model=NVIDIA_FAST,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=8192,
        )
        return _parse_json(response.choices[0].message.content)
    except Exception as e:
        log.warning("NVIDIA v4-flash: %s → probando llama-3.3", str(e)[:60])

    # Intento 2: llama-3.3-70b (lento pero fiable)
    response = client.chat.completions.create(
        model=NVIDIA_STABLE,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=8192,
    )
    return _parse_json(response.choices[0].message.content)


_PROVIDER_MAP = {
    "groq": _call_groq,
    "github": _call_github,
    "nvidia": _call_nvidia,
}

# Reintentos contra el MISMO proveedor antes de saltar al siguiente. El 429 de
# Groq es por tokens-por-minuto (12k), así que esperar unos segundos lo arregla;
# saltar de proveedor al instante quemaba los tres seguidos y mataba el artículo.
RETRIES_PER_PROVIDER = 2
MAX_WAIT_SECONDS = 60

_TRANSIENT_MARKS = ("429", "rate limit", "500", "502", "503", "504",
                    "timed out", "timeout", "service is unavailable", "overloaded")


def _seconds_from_header(raw: str) -> float:
    """Convierte '20', '7.5s', '1m26.4s' o '250ms' a segundos. 0 si no se entiende."""
    if not raw:
        return 0.0
    raw = str(raw).strip()
    try:
        return float(raw)  # retry-after estándar: segundos a secas
    except ValueError:
        pass
    match = _re.fullmatch(r"(?:(\d+)m)?(?:([\d.]+)s)?|([\d.]+)ms", raw)
    if not match:
        return 0.0
    minutes, seconds, millis = match.groups()
    if millis:
        return float(millis) / 1000
    return int(minutes or 0) * 60 + float(seconds or 0)


def _wait_before_retry(error: Exception, attempt: int) -> float:
    """Cuánto esperar: lo que pida el proveedor; si no lo dice, backoff exponencial."""
    headers = getattr(getattr(error, "response", None), "headers", None) or {}
    asked = max(
        _seconds_from_header(headers.get("retry-after", "")),
        _seconds_from_header(headers.get("x-ratelimit-reset-tokens", "")),
    )
    if asked > MAX_WAIT_SECONDS:
        return 0.0  # cuota diaria agotada: esperar no compensa, mejor otro proveedor
    delay = asked + 1 if asked else 10 * (2 ** attempt)
    return min(delay, MAX_WAIT_SECONDS)


def _is_transient(error: Exception) -> bool:
    """True si reintentar tiene sentido (límite de ritmo o caída pasajera)."""
    err = str(error).lower()
    return any(mark in err for mark in _TRANSIENT_MARKS)


def _call_provider(name: str, prompt: str, temperature: float) -> dict:
    """Llama a un proveedor reintentando mientras el fallo sea pasajero."""
    func = _PROVIDER_MAP[name]
    for attempt in range(RETRIES_PER_PROVIDER + 1):
        try:
            return func(prompt, temperature)
        except Exception as e:
            if attempt == RETRIES_PER_PROVIDER or not _is_transient(e):
                raise
            delay = _wait_before_retry(e, attempt)
            if delay <= 0:
                raise
            log.warning("↻ %s: %s → reintento %d/%d en %.0fs",
                        name, str(e)[:80], attempt + 1, RETRIES_PER_PROVIDER, delay)
            time.sleep(delay)


def call_ai(prompt: str, temperature: float = 0.7, **kwargs) -> dict:
    """Round-robin entre proveedores + fallback inmediato.

    Distribuye calls según ARTICLE_INDEX para usar tokens de todos.
    Si uno falla, salta al siguiente. NVIDIA prueba 2 modelos internamente.
    """
    global _call_count
    article_idx = int(os.getenv("ARTICLE_INDEX", "1")) - 1
    rotation = (article_idx * 2 + _call_count) % len(PROVIDERS)
    _call_count += 1

    order = PROVIDERS[rotation:] + PROVIDERS[:rotation]

    errors = []
    for provider_name in order:
        try:
            result = _call_provider(provider_name, prompt, temperature)
            log.info("✓ %s", provider_name)
            return result
        except Exception as e:
            err = str(e)
            errors.append(f"{provider_name}: {err[:100]}")
            log.warning("✗ %s: %s", provider_name, err[:100])
            time.sleep(3)

    raise RuntimeError(f"Todos los proveedores fallaron: {'; '.join(errors)}")
