"""Agent construction and helpers to ask questions."""
from __future__ import annotations

import re

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from .config import Settings
from .prompts import SYSTEM_PROMPT
from .tools import ALL_TOOLS

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


def build_agent(settings: Settings):
    """Create the agent backed by a local Ollama model."""
    llm = ChatOllama(
        model=settings.model,
        base_url=settings.base_url,
        temperature=settings.temperature,
    )
    return create_agent(
        model=llm,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),  # conversation memory per thread_id
    )


def _text(content) -> str:
    """Message content is either a string or a list of content blocks."""
    if isinstance(content, str):
        text = content
    else:
        text = "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    # Reasoning models (e.g. qwen3, deepseek-r1) may emit <think> blocks.
    return _THINK_RE.sub("", text).strip()


def ask_with_trace(agent, question: str, thread_id: str = "default"):
    """Send one question.

    Returns (answer, steps) where steps is a list of
    {"name": str, "args": dict, "result": str | None} for this turn only.
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        {"configurable": {"thread_id": thread_id}},
    )
    messages = result["messages"]

    # With memory enabled, `messages` holds the whole history; only inspect this turn.
    last_human = max((i for i, m in enumerate(messages) if m.type == "human"), default=-1)
    steps, by_id = [], {}
    for m in messages[last_human + 1:]:
        for call in getattr(m, "tool_calls", None) or []:
            step = {"name": call["name"], "args": call["args"], "result": None}
            steps.append(step)
            by_id[call.get("id")] = step
        if m.type == "tool" and getattr(m, "tool_call_id", None) in by_id:
            by_id[m.tool_call_id]["result"] = _text(m.content)

    return _text(messages[-1].content), steps


def ask(agent, question: str, thread_id: str = "default"):
    """Like ask_with_trace, but returns [(tool_name, args), ...] (used by the CLI)."""
    answer, steps = ask_with_trace(agent, question, thread_id)
    return answer, [(s["name"], s["args"]) for s in steps]