# DegreePath Advisor

AI academic advisor chatbot with a Python backend and responsive web frontend.

## Features

- Plan a suggested 4-year degree schedule
- Check course prerequisites
- Suggest electives based on interests
- Warn about graduation requirement gaps

## Run locally

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optional: enable LLM-enhanced responses:

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="gpt-4o-mini"
```

4. Start the app:

```bash
python3 backend.py
```

5. Open:

`http://localhost:5001`

## Notes

- Without `OPENAI_API_KEY`, the app still works in rule-based advisor mode.
- The included catalog and graduation rules are sample data; adjust them to your university policy.
