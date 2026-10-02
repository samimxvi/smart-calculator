"""Command-line interface: interactive chat or one-shot question."""
from __future__ import annotations

import argparse
import sys
from dataclasses import replace

from .agent import ask, build_agent
from .config import load_settings
from .ollama_check import OllamaUnavailable, check_ollama

BANNER = "Smart Calculator Agent | model: {model}\nAsk any math question. Type 'exit' to quit.\n"
THREAD_ID = "cli-session"


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="calc-agent",
        description="A local calculator agent (LangChain + Ollama).",
    )
    p.add_argument("question", nargs="*", help="Ask one question and exit. Omit for interactive mode.")
    p.add_argument("-m", "--model", help="Ollama model (overrides OLLAMA_MODEL).")
    p.add_argument("--base-url", help="Ollama URL (overrides OLLAMA_BASE_URL).")
    p.add_argument("-v", "--verbose", action="store_true", help="Show the tools the agent calls.")
    p.add_argument("--skip-check", action="store_true", help="Skip the Ollama pre-flight check.")
    return p.parse_args(argv)


def _respond(agent, question: str, verbose: bool) -> bool:
    try:
        answer, calls = ask(agent, question, THREAD_ID)
    except Exception as exc:  # noqa: BLE001
        print(
            f"\nError: {exc}\n"
            "Tip: the model must support tool calling "
            "(e.g. qwen2.5, llama3.1, llama3.2, qwen3).\n",
            file=sys.stderr,
        )
        return False
    if verbose:
        for name, args in calls:
            print(f"  [tool] {name}({args})")
    print(f"\n{answer}\n")
    return True


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    settings = load_settings()
    if args.model:
        settings = replace(settings, model=args.model)
    if args.base_url:
        settings = replace(settings, base_url=args.base_url)

    if not args.skip_check:
        try:
            check_ollama(settings.base_url, settings.model)
        except OllamaUnavailable as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

    agent = build_agent(settings)

    if args.question:
        return 0 if _respond(agent, " ".join(args.question), args.verbose) else 1

    print(BANNER.format(model=settings.model))
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit", "q"}:
            break
        if question:
            _respond(agent, question, args.verbose)
    return 0