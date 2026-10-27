"""LLM access. Local Ollama by default; Anthropic when LLM_PROVIDER=anthropic.

Settings (environment or .env): LLM_PROVIDER, LLM_MODEL, OLLAMA_URL, ANTHROPIC_API_KEY.
"""
import json
import os
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODELS = {"ollama": "qwen2.5:7b", "anthropic": "claude-haiku-5-5"}


@dataclass
class Completion:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int


def load_env(path=Path(".env")):
    """Minimal .env reader; real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and not key.strip().startswith("#") and value.strip():
            os.environ.setdefault(key.strip(), value.strip())


def settings():
    load_env()
    provider = os.environ.get("LLM_PROVIDER", "ollama")
    return provider, os.environ.get("LLM_MODEL", DEFAULT_MODELS[provider])


def complete(prompt, *, system=None, json_mode=False, max_tokens=512, num_ctx=8192):
    provider, model = settings()
    start = time.perf_counter()
    if provider == "ollama":
        messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"model": model, "messages": messages, "stream": False,
                "options": {"temperature": 0, "num_predict": max_tokens, "num_ctx": num_ctx}}
        if json_mode:
            body["format"] = "json"
        url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434") + "/api/chat"
        request = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=600) as response:
            out = json.load(response)
        text, tokens_in, tokens_out = out["message"]["content"], out.get("prompt_eval_count"), out.get("eval_count")
    elif provider == "anthropic":
        try:
            import anthropic
        except ImportError as e:
            raise SystemExit("LLM_PROVIDER=anthropic needs `pip install anthropic`") from e
        kwargs = {"system": system} if system else {}
        out = anthropic.Anthropic().messages.create(
            model=model, max_tokens=max_tokens, temperature=0,
            messages=[{"role": "user", "content": prompt}], **kwargs)
        text = "".join(block.text for block in out.content if block.type == "text")
        tokens_in, tokens_out = out.usage.input_tokens, out.usage.output_tokens
    else:
        raise SystemExit(f"Unknown LLM_PROVIDER: {provider}")
    return Completion(text, model, tokens_in, tokens_out, int((time.perf_counter() - start) * 1000))
