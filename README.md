## Smart Calculator Agent

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![LangChain](https://img.shields.io/badge/LangChain-1.x-green)
![Ollama](https://img.shields.io/badge/Ollama-local%20LLM-black)
![Streamlit](https://img.shields.io/badge/UI-Streamlit-ff4b4b)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

A **AI calculator agent** built with [LangChain](https://www.langchain.com/), [Ollama](https://ollama.com/) and [Streamlit](https://streamlit.io/).

You ask in plain English. A tool-calling LLM decides which tool to use, and **Python does the exact math**. The model never does arithmetic in its head, because LLMs are unreliable at that. Everything runs on your machine, with no API keys and no data leaving your computer.

<!-- Add a screenshot: save it as docs/screenshot.png and uncomment the line below -->
<!-- ![Screenshot](docs/screenshot.png) -->

## Features

- 💬 **Natural-language math**: "What's 15% tip on $86.40 split 3 ways?"
- 🔧 **Six tools**: expressions, unit conversion, statistics, compound interest, loan payments, quadratic equations
- 🔒 **Safe evaluator**: expressions are parsed with a whitelisted AST. `eval()` is never used
- 🧠 **Conversation memory**: follow-ups like "now divide that by 4" work
- 🔍 **Transparent**: see every tool call, its arguments and its result
- 🖥️ **Two interfaces**: Streamlit web UI and a terminal CLI
- 🔌 **Model-agnostic**: any Ollama model that supports tool calling
- ✅ **Tested**: unit tests for every tool, with no LLM required

## How it works

```mermaid
flowchart LR
    U[You] --> I[Streamlit UI or CLI]
    I --> A[LangChain agent]
    A <--> M[Ollama local LLM]
    A --> T[Tools]
    T --> C[calculate]
    T --> V[convert_units]
    T --> S[statistics_summary]
    T --> F[compound_interest / loan_payment]
    T --> Q[solve_quadratic]
```

1. Your question goes to the agent, which is a local LLM served by Ollama.
2. The model chooses a tool and its arguments.
3. The tool computes the exact result in plain Python.
4. The model explains the result in a short answer.

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com/download)
- A tool-calling model (default: `qwen2.5:7b`, about 5 GB download)

## Quick start

### Windows (PowerShell)

```powershell
winget install Ollama.Ollama        # then reopen PowerShell
ollama pull qwen2.5:7b

git clone https://github.com/<your-username>/smart-calculator-agent.git
cd smart-calculator-agent

py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,ui]"

calc-ui                             # web UI at http://localhost:8501
```

Or run everything in one go: `powershell -ExecutionPolicy Bypass -File .\setup.ps1`

> If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
> In cmd.exe, use `.venv\Scripts\activate.bat`.

### macOS / Linux

```bash
# Install Ollama: https://ollama.com/download  (Linux: curl -fsSL https://ollama.com/install.sh | sh)
ollama pull qwen2.5:7b

git clone https://github.com/<your-username>/smart-calculator-agent.git
cd smart-calculator-agent

python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,ui]"

calc-ui
```

## Usage

### Web UI

```bash
calc-ui
# or: streamlit run src/calc_agent/app.py
```

The sidebar lets you pick any installed Ollama model, adjust temperature, toggle tool-call details, clear the chat, and try example questions.

### Command line

```bash
calc-agent                                        # interactive chat with memory
calc-agent -v                                     # also show tool calls
calc-agent "What is 15% of 86.40, split 3 ways?"  # one-shot question
calc-agent -m llama3.1:8b "Convert 72 F to C"     # choose a model
python -m calc_agent                              # without the launcher
```

### Example questions

- `Invest 10000 at 7% for 15 years, adding 200 a month. What's the final balance?`
- `Monthly payment on a 250000 loan at 6.5% over 30 years?`
- `Mean and standard deviation of 12, 15, 9, 22, 18`
- `Solve 2x^2 - 4x - 6 = 0`
- `Convert 72 F to C, then 2.5 km to feet`
- `sqrt(2) * sin(pi/4) + log10(1000)`

## Tools

| Tool | What it does |
|---|---|
| `calculate` | Evaluates expressions: `+ - * / // % **`, parentheses, `pi`/`e`/`tau`, `sqrt`, `log`, trig, `factorial`, `gcd`, `lcm`, `round`, `min`/`max`, and more |
| `convert_units` | Length, mass, volume, time, data and temperature |
| `statistics_summary` | Count, sum, mean, median, mode, min, max, range, standard deviations |
| `compound_interest` | Investment growth, with optional monthly contributions |
| `loan_payment` | Fixed monthly payment, total paid and total interest |
| `solve_quadratic` | Real and complex roots of `ax² + bx + c = 0` |

## Configuration

Copy `.env.example` to `.env` and edit it:

```env
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_TEMPERATURE=0
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:7b` | Model used by the agent |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Where Ollama is running (set this for a remote machine) |
| `OLLAMA_TEMPERATURE` | `0` | Keep at 0 for the most reliable tool use |

### Choosing a model

The model **must support tool calling**.

| Model | Notes |
|---|---|
| `qwen2.5:7b` | Default. Good balance of speed and tool-use reliability |
| `llama3.1:8b` | Solid alternative |
| `qwen3:8b` | Reasoning model. `<think>` blocks are stripped from answers |
| `qwen2.5:14b` | More reliable on multi-step word problems, needs more RAM |
| `llama3.2:3b` | Fast and light, but less reliable |

## Project structure

```
smart-calculator-agent/
├── pyproject.toml          # dependencies + calc-agent / calc-ui commands
├── requirements.txt
├── setup.ps1               # one-shot Windows setup
├── .env.example
├── .streamlit/config.toml  # disables Streamlit telemetry
├── src/calc_agent/
│   ├── cli.py              # terminal interface
│   ├── app.py              # Streamlit UI
│   ├── ui.py               # calc-ui launcher
│   ├── agent.py            # ChatOllama + create_agent + memory
│   ├── config.py           # settings from env / .env
│   ├── prompts.py          # system prompt
│   ├── ollama_check.py     # list models / pre-flight check
│   └── tools/
│       ├── __init__.py     # ALL_TOOLS registry
│       ├── calculator.py   # safe AST expression evaluator
│       ├── units.py
│       ├── stats.py
│       ├── finance.py
│       └── algebra.py
└── tests/
```

## Adding your own tool

1. Create a file in `src/calc_agent/tools/`. Keep the logic in a plain function and make the tool a thin wrapper, which keeps it easy to test:

```python
   from langchain.tools import tool

   def percent_change(old: float, new: float) -> float:
       if old == 0:
           raise ValueError("old value cannot be 0")
       return (new - old) / old * 100

   @tool
   def percentage_change(old: float, new: float) -> str:
       """Percentage change from an old value to a new value."""
       try:
           return f"{percent_change(old, new):.4g}%"
       except ValueError as exc:
           return f"Error: {exc}"
```

2. Register it in `src/calc_agent/tools/__init__.py` by adding it to `ALL_TOOLS`.

The **docstring is what the model reads** to decide when to use the tool, so describe it and its arguments clearly.

## Testing

```bash
pytest
```

The tests cover the tools only and need neither Ollama nor an internet connection.

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot reach Ollama` | Start the Ollama app, or run `ollama serve` |
| `Model ... is not installed` | `ollama pull <model>` |
| `does not support tools` | Use a tool-capable model (see the table above) |
| Ignores tools or gives wrong answers | Try a larger model, and keep `OLLAMA_TEMPERATURE=0` |
| Slow first answer | The model is loading into memory. Later answers are faster |
| `calc-agent` / `calc-ui` not found | Activate the virtual environment, or use `python -m calc_agent` / `streamlit run src/calc_agent/app.py` |
| Port 8501 in use | `calc-ui --server.port 8502` |
| Streamlit asks for an email | Press Enter to skip |

## Limitations

- Small local models can occasionally pick the wrong tool or mis-parse a word problem. Use the "Show tool calls" toggle to check.
- There is no symbolic algebra (simplify, differentiate, integrate) yet. Only the quadratic solver is built in.
- Conversation memory is in-process and is lost when you restart.