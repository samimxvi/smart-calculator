import streamlit as st
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from calculator_tools import calculator_tools

st.set_page_config(page_title="Offline AI Calculator", page_icon="🧮", layout="centered")
st.title("🧮 Offline AI Calculator")
st.caption("Local AI · Exact Python tools · Math, units, statistics & finance")

with st.sidebar:
    st.header("Local model")
    model = st.text_input("Ollama model", value="llama3.1")
    st.caption("The model must already be downloaded in Ollama.")
    st.code("ollama pull llama3.1\nollama serve", language="bash")
    st.divider()
    st.markdown("**Privacy:** prompts are sent to your local Ollama service. This app does not call a cloud LLM API.")

SYSTEM_PROMPT = """You are a careful calculator assistant running locally.
Use tools for every calculation, conversion, statistical computation, or financial computation.
Never mentally calculate a numeric answer when a tool is available.
Explain which tool result supports your answer. Preserve exact fractions/decimal strings when provided.
For ambiguous inputs, ask a concise clarifying question rather than guessing.
State assumptions and units. Do not claim a result is exact if the tool returns an approximation.
Available tools cover safe arithmetic, unit conversions, descriptive statistics, and common finance formulas."""

@st.cache_resource(show_spinner=False)
def build_agent(model_name: str):
    llm = ChatOllama(model=model_name, temperature=0)
    return create_agent(model=llm, tools=calculator_tools, system_prompt=SYSTEM_PROMPT)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Try: Convert 5 miles to km, or calculate compound interest...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking locally and running tools…"):
                agent = build_agent(model)
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ]
                result = agent.invoke({"messages": history})
                answer = result["messages"][-1].content
                if isinstance(answer, list):
                    answer = "\n".join(
                        part.get("text", str(part)) if isinstance(part, dict) else str(part)
                        for part in answer
                    )
                st.markdown(answer)
        except Exception as exc:
            answer = (
                "I couldn't reach the local model or complete the request. "
                "Check that Ollama is running, the model is installed, and the model supports tool calling.\n\n"
                f"**Technical detail:** `{type(exc).__name__}: {exc}`"
            )
            st.error(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})

if st.session_state.messages:
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()
