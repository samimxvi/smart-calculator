"""Helpers to talk to a local Ollama server: list models and pre-flight checks."""
from __future__ import annotations

import json
import urllib.error
import urllib.request


class OllamaUnavailable(RuntimeError):
    """Ollama is unreachable or the requested model is not installed."""


def list_models(base_url: str, timeout: float = 3.0) -> list[str]:
    """Return the names of models installed in Ollama (e.g. 'qwen2.5:7b')."""
    url = base_url.rstrip("/") + "/api/tags"
    # Bypass any system proxy: Ollama is local.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(url, timeout=timeout) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as exc:
        raise OllamaUnavailable(
            f"Cannot reach Ollama at {base_url}. Start the Ollama app from the "
            "Start menu (or run `ollama serve` in another terminal)."
        ) from exc
    return [m.get("name", "") for m in data.get("models", [])]


def check_ollama(base_url: str, model: str, timeout: float = 3.0) -> None:
    installed = list_models(base_url, timeout)
    wanted = model if ":" in model else f"{model}:latest"
    if wanted not in installed:
        raise OllamaUnavailable(
            f"Model '{model}' is not installed. Run:  ollama pull {model}\n"
            f"Installed models: {', '.join(installed) or '(none)'}"
        )