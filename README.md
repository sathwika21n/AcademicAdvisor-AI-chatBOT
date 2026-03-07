# DegreePath Advisor

AI academic advisor chatbot with a Python backend and Streamlit frontend.

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

3. Optional: enable LLM-enhanced responses (OpenAI-compatible APIs like OpenAI or OpenRouter):

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="gpt-4o-mini"
```

OpenRouter example:

```bash
export COLLEGESCORECARD_API_KEY="you_API_key"
export US_GOV_API_URL="https://developer.nrel.gov/api/alt-fuel-stations/v1.json?"
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="openrouter/auto"
```

4. Optional: set app login credentials (defaults shown):

```bash
export APP_USERNAME="student"
export APP_PASSWORD="advisor123"
```

5. Start the Streamlit frontend:

```bash
streamlit run streamlit_app.py
```

6. Open:

`http://localhost:8501`

## Optional: run Flask API directly

If you want the API-only server for testing:

```bash
python3 backend.py
```

Then open `http://localhost:5001`.

## Notes

- Without `OPENAI_API_KEY`, the app still works in rule-based advisor mode.
- You can use OpenRouter because the backend uses the OpenAI-compatible SDK interface (`OPENAI_BASE_URL`).
- The included catalog and graduation rules are sample data; adjust them to your university policy.
- Streamlit login uses `APP_USERNAME` and `APP_PASSWORD`; if unset, defaults are `student` / `advisor123`.
