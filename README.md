<<<<<<< HEAD
# MindHarbor Chatbot

Supportive mental-health chatbot with a Python backend and a responsive web frontend.

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

3. Optional: enable LLM responses:

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

- Without `OPENAI_API_KEY`, the app still works using built-in supportive fallback responses.
- If crisis language is detected, the app returns immediate safety messaging and hotline guidance.
=======

