# Technical Documentation: MindHarbor Chatbot

## 1. Project Purpose

This project is a web chatbot focused on **mental wellness support**.  
It is designed to:

- Accept user messages from a browser UI.
- Generate supportive responses.
- Detect high-risk language (self-harm indicators) and return crisis guidance.
- Work in two modes:
  - `LLM mode` (uses OpenAI API if configured).
  - `Fallback mode` (uses built-in response rules if no API key is available).

Important: This is a support tool, not a medical diagnostic system.

## 2. High-Level Architecture

```
Browser (HTML/CSS/JS)
   |
   | POST /api/chat (JSON)
   v
Flask Backend (backend.py)
   |- Crisis detection (keyword-based)
   |- LLM response path (OpenAI)
   |- Fallback response path (rule-based)
   |
   v
JSON response back to browser
```

Core files:

- `backend.py`: API server, logic, safety checks.
- `frontend/index.html`: page structure.
- `frontend/styles.css`: visual design, responsive layout.
- `frontend/app.js`: chat interaction and API calls.
- `requirements.txt`: Python dependencies.

## 3. Backend Deep Dive (`backend.py`)

### 3.1 Imports and Setup

- `Flask`, `jsonify`, `request`, `send_from_directory` are used to build and serve the web app.
- `Path` is used to locate static frontend files.
- OpenAI client import is wrapped in a `try/except` so app can still run even if `openai` package is missing.

References:
- `backend.py:1`
- `backend.py:5`
- `backend.py:7`

### 3.2 Configuration Constants

- `BASE_DIR`, `STATIC_DIR`, `INDEX_FILE` define file locations for serving frontend assets.
- `CRISIS_TERMS` defines simple keyword triggers for risk language.
- `SYSTEM_PROMPT` constrains LLM behavior (supportive, non-diagnostic, safety-aware).
- `FALLBACK_OPENING` is shared phrasing for fallback responses.

References:
- `backend.py:13`
- `backend.py:17`
- `backend.py:29`
- `backend.py:37`

### 3.3 OpenAI Client Initialization

`create_client()`:

- Reads `OPENAI_API_KEY` from environment.
- Returns `None` if key is missing or OpenAI SDK is unavailable.
- Returns `OpenAI(...)` client when available.

This design keeps the app usable even without paid API access.

Reference:
- `backend.py:42`

### 3.4 Safety Detection

`contains_crisis_signal(text)`:

- Converts text to lowercase.
- Checks if any term in `CRISIS_TERMS` appears as a substring.
- Returns boolean.

Reference:
- `backend.py:49`

`crisis_response()`:

- Returns a fixed, immediate safety message with 911/988 guidance.

Reference:
- `backend.py:54`

### 3.5 Fallback Response Engine

`fallback_response(user_text)` is a deterministic rule-based function:

- If input includes anxiety/panic signals: returns breathing + grounding steps.
- If depression/hopelessness signals: returns gentle activation plan.
- If sleep/insomnia signals: returns sleep hygiene steps.
- Otherwise: returns a generic “one-step-at-a-time” plan.

This gives stable support behavior when LLM is not configured or fails.

Reference:
- `backend.py:65`

### 3.6 LLM Response Path

`llm_response(client, history)`:

- Selects model from `OPENAI_MODEL` (default: `gpt-4o-mini`).
- Prepends `SYSTEM_PROMPT`.
- Calls `client.chat.completions.create(...)`.
- Returns model output or fallback text if content is empty.

Reference:
- `backend.py:105`

### 3.7 Flask App and Routes

Global objects:

- `app = Flask(...)` defines the app and static path mapping.
- `client = create_client()` initializes once at startup.

References:
- `backend.py:117`
- `backend.py:118`

Route `GET /`:

- Serves `frontend/index.html`.

Reference:
- `backend.py:121`

Route `POST /api/chat`:

1. Read JSON payload.
2. Validate `message` exists.
3. If user message contains crisis terms -> return `crisis_response`.
4. Sanitize and limit conversation history (last 10 messages, valid roles only).
5. If no OpenAI client -> return fallback response.
6. Else call LLM path.
7. If LLM reply unexpectedly contains crisis term, override with crisis response.
8. If exception occurs, fail gracefully to fallback.

Reference:
- `backend.py:126`

### 3.8 Runtime Entry Point

`if __name__ == "__main__": app.run(...)`:

- Runs Flask dev server on `0.0.0.0:5001`.
- `debug=True` is enabled for development.

Reference:
- `backend.py:161`

## 4. Frontend Deep Dive

## 4.1 HTML Structure (`frontend/index.html`)

Main UI sections:

- Hero section (title/subtitle).
- Safety banner with emergency guidance.
- Chat log container (`#chatLog`).
- Message form with textarea and send button.
- Hidden template (`#bubbleTemplate`) used to clone message bubbles.

Reference:
- `frontend/index.html:10`
- `frontend/index.html:19`
- `frontend/index.html:25`
- `frontend/index.html:27`
- `frontend/index.html:41`

### 4.2 CSS Styling (`frontend/styles.css`)

Design system choices:

- CSS variables for colors/shadows (`:root`).
- Gradient/radial background layers for depth.
- Card-like hero + chat panel.
- Distinct message bubble styles for user and assistant.
- Responsive behavior under `720px` for mobile.
- Lightweight entry animation (`rise`).

Reference:
- `frontend/styles.css:1`
- `frontend/styles.css:18`
- `frontend/styles.css:63`
- `frontend/styles.css:98`
- `frontend/styles.css:179`

### 4.3 JavaScript Behavior (`frontend/app.js`)

State and initialization:

- Reads key DOM elements.
- Keeps an in-memory `history` array.
- Adds an initial assistant greeting.

Reference:
- `frontend/app.js:1`
- `frontend/app.js:7`
- `frontend/app.js:9`

Submit flow:

1. Intercept form submit.
2. Validate non-empty text.
3. Render user bubble immediately.
4. Send `POST /api/chat` with current message + history.
5. On success: render assistant reply and append to history.
6. On failure: render connection error message.
7. Re-enable input and focus.

Reference:
- `frontend/app.js:13`

Helper functions:

- `appendMessage(role, text)` clones template and appends bubble.
- `setBusy(busy)` toggles form/button disabled state and button label.

Reference:
- `frontend/app.js:49`
- `frontend/app.js:59`

## 5. API Contract

### Request (`POST /api/chat`)

```json
{
  "message": "I feel anxious today",
  "history": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "How are you feeling?"}
  ]
}
```

### Response (normal)

```json
{
  "reply": "Supportive assistant response here...",
  "mode": "llm"
}
```

### Response (fallback)

```json
{
  "reply": "Rule-based supportive response here...",
  "mode": "fallback"
}
```

### Response (crisis)

```json
{
  "reply": "Crisis safety message here...",
  "mode": "crisis"
}
```

## 6. Safety Behavior and Current Limitations

Current safety controls:

- Input keyword screening for crisis language.
- Forced crisis response for matched terms.
- LLM prompt instruction to avoid diagnosis/prescriptive certainty.
- Fallback on runtime/API errors.

Limitations:

- Crisis detection is keyword-based only (can miss nuanced phrasing).
- No user authentication or rate limiting.
- Chat history is in-memory only (browser session), no database persistence.
- No observability layer (structured logs, tracing, analytics).

## 7. Error Handling Strategy

Backend:

- Missing message returns `400`.
- OpenAI errors are caught and converted to fallback replies.

Frontend:

- Non-2xx responses throw and show a friendly retry message.

References:
- `backend.py:132`
- `backend.py:149`
- `frontend/app.js:30`
- `frontend/app.js:38`

## 8. Local Run Workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 backend.py
```

Open: `http://localhost:5001`

Optional for LLM mode:

```bash
export OPENAI_API_KEY="your_api_key"
export OPENAI_MODEL="gpt-4o-mini"
```

## 9. Suggested Next Improvements (Technical Roadmap)

1. Replace keyword-only safety checks with a moderation/classification layer.
2. Add persistence (SQLite/Postgres) for user sessions and chat history.
3. Add authentication and basic abuse protection (rate limits, quotas).
4. Add structured logging and error monitoring.
5. Add tests:
   - Unit tests for fallback and crisis detection.
   - API tests for all `/api/chat` modes.
   - Frontend integration tests for message flow.

## 10. Beginner Mental Model

When a user types a message:

1. Frontend sends message JSON to backend.
2. Backend checks for crisis signals first.
3. Backend chooses response engine:
   - OpenAI if configured.
   - Rule-based fallback otherwise.
4. Backend returns reply JSON.
5. Frontend renders assistant bubble.

If you understand those 5 steps, you understand the core architecture of this app.
