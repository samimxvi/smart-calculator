"""Streamlit UI for the Smart Calculator Agent.

Run:  streamlit run src/calc_agent/app.py     (or: calc-ui)
"""
from __future__ import annotations

import uuid

import streamlit as st

from calc_agent.agent import ask_with_trace, build_agent
from calc_agent.config import Settings, load_settings
from calc_agent.ollama_check import OllamaUnavailable, list_models

st.set_page_config(page_title="Smart Calculator Agent", page_icon="🧮", layout="centered")

EXAMPLES = [
    "What is 15% of 86.40, split 3 ways?",
    "Invest 10000 at 7% for 15 years, adding 200 monthly. Final balance?",
    "Monthly payment on a 250000 loan at 6.5% over 30 years?",
    "Mean and standard deviation of 12, 15, 9, 22, 18",
    "Solve 2x^2 - 4x - 6 = 0",
    "Convert 72 F to C, and 2.5 km to feet",
]


@st.cache_resource(show_spinner=False)
def get_agent(model: str, base_url: str, temperature: float):
    """One agent per (model, URL, temperature), shared across reruns."""
    return build_agent(Settings(model=model, base_url=base_url, temperature=temperature))


def _md(text: str) -> str:
    """Escape $ so money amounts aren't rendered as LaTeX."""
    return text.replace("$", r"\$")


def render_steps(steps: list[dict]) -> None:
    if not steps:
        return
    with st.expander(f"🔧 Tools used ({len(steps)})"):
        for s in steps:
            args = ", ".join(f"{k}={v!r}" for k, v in s["args"].items())
            result = s["result"] if s["result"] is not None else "(no result)"
            st.code(f"{s['name']}({args})\n→ {result}", language="text")


# ---------------------------------------------------------------- state
st.session_state.setdefault("messages", [])
st.session_state.setdefault("thread_id", str(uuid.uuid4()))

# -------------------------------------------------------------- sidebar
defaults = load_settings()
with st.sidebar:
    st.title("🧮 Calculator Agent")
    base_url = st.text_input("Ollama URL", defaults.base_url)

    try:
        models = list_models(base_url)
    except OllamaUnavailable as exc:
        models, error = [], str(exc)
    else:
        error = "" if models else "No models installed. Run:  ollama pull qwen2.5:7b"

    if error:
        st.error(error)
        model = defaults.model
    else:
        wanted = defaults.model if ":" in defaults.model else defaults.model + ":latest"
        model = st.selectbox(
            "Model",
            models,
            index=models.index(wanted) if wanted in models else 0,
            help="Must support tool calling (qwen2.5, llama3.1, llama3.2, qwen3).",
        )

    temperature = st.slider("Temperature", 0.0, 1.0, defaults.temperature, 0.1)
    show_steps = st.toggle("Show tool calls", value=True)

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

    st.divider()
    st.caption("Try an example")
    for i, example in enumerate(EXAMPLES):
        if st.button(example, key=f"ex{i}", use_container_width=True):
            st.session_state.pending = example

# ----------------------------------------------------------------- main
st.title("🧮 Smart Calculator Agent")
st.caption(f"Running locally with **{model}** via Ollama. Nothing leaves your machine.")

if error:
    st.stop()

if not st.session_state.messages:
    st.info("Ask a math question, or pick an example from the sidebar.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(_md(msg["content"]))
        if show_steps and msg.get("steps"):
            render_steps(msg["steps"])

prompt = st.chat_input("Ask a math question…") or st.session_state.pop("pending", None)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(_md(prompt))

    with st.chat_message("assistant"):
        with st.spinner("Calculating…"):
            try:
                agent = get_agent(model, base_url, temperature)
                # A different model/temperature gets a fresh conversation thread.
                thread = f"{st.session_state.thread_id}:{model}:{temperature}"
                answer, steps = ask_with_trace(agent, prompt, thread)
            except Exception as exc:  # noqa: BLE001
                answer = f"⚠️ {exc}\n\nMake sure the model supports tool calling."
                steps = []
        st.markdown(_md(answer))
        if show_steps:
            render_steps(steps)

    st.session_state.messages.append({"role": "assistant", "content": answer, "steps": steps})