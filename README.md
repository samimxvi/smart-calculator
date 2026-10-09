## Smart Calculator Agent

A local-first calculator assistant built with Streamlit, LangChain, and Ollama. The LLM interprets requests and selects tools; Python performs calculations.

## Features

- Safe arithmetic expressions using Python `Decimal`
- Unit conversion with Pint
- Descriptive statistics
- Compound interest
- Fixed-rate amortizing loan payments
- Local chat interface and conversation history

## Requirements

- Python 3.10+
- Ollama installed locally
- A tool-capable Ollama model (example: `llama3.1`)

## Setup

```bash
# 1. Install Ollama, then download the model while you have connectivity
ollama pull llama3.1

# 2. Create and activate a virtual environment
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Start Ollama in a separate terminal if it isn't already running
ollama serve

# 5. Start the app
streamlit run app.py
```

Once the model and Python packages are installed, the app can run without internet access. For a strict offline environment, transfer the model and wheel dependencies to the machine first. The app itself makes no external API calls.

## Example prompts

- `What is (123456789 * 987654321) / 3?`
- `Convert 5 miles to kilometers.`
- `Find the mean, median and standard deviation of 12, 15, 19, 21, 23.`
- `What is the future value of 50000 at 7% annually for 5 years, compounded monthly?`
- `What is the monthly payment on a 250000 loan at 6.5% for 30 years?`

## Accuracy notes

- Arithmetic uses `Decimal`; results are exact for finite decimal operations within the configured precision, while division and some powers can be repeating/rounded.
- Unit conversions use floating-point magnitudes, so they are practical numerical conversions, not guaranteed exact rational results.
- Statistics are computed using Python's `statistics` module and floating-point values.
- Finance tools use `Decimal`, but compound powers and amortization formulas can require rounding. Results are not financial advice.
- This is a prototype. Review formulas and test before relying on it for regulated or mission-critical decisions.

## Troubleshooting

- `ollama list` shows models downloaded locally.
- `ollama run llama3.1` can verify the model works.
- If tool calls fail, use a model with reliable tool-calling support and update Ollama / `langchain-ollama`.
- If port 8501 is in use: `streamlit run app.py --server.port 8502`.