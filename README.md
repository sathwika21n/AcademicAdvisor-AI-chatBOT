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
export OPENAI_API_KEY="your_api_key"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export OPENAI_MODEL="openrouter/auto"
```

4. Start the Streamlit frontend:

```bash
export APP_USERNAME="your_username"
export APP_PASSWORD="your_strong_password"
streamlit run streamlit_app.py
```

5. Open:

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

## Scraping real catalog data

Rather than maintaining `ACADEMIC_DATA` manually, you can pull course
information from university catalog websites.

A helper script lives in `utils/scrape_catalog.py` and works roughly like
this:

```bash
python -m utils.scrape_catalog https://catalog.utdallas.edu/now/courses/cs \
    > data/utd_cs.json
```

Modify `parse_table()` inside the script to match the HTML structure of
each school's catalog; many modern catalogs are rendered with JavaScript
and won’t contain any course rows in the raw HTML, in which case a simple
`requests`/`BeautifulSoup` scraper won’t work. For those sites you’ll need
a headless browser (e.g. Playwright, Selenium) or an official API.

After saving JSON files under the `data/` directory, the backend
automatically loads them when it starts (see `load_additional_data()` in
`backend.py`).

