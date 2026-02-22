# Technical Documentation: DegreePath Advisor

## Overview

DegreePath Advisor is a web chatbot that helps students with:

- 4-year degree planning
- prerequisite checks
- elective recommendations by interest
- graduation requirement warnings

It runs in:

- rule-based mode (default, no API key needed)
- LLM-enhanced mode (if `OPENAI_API_KEY` is set; supports OpenAI-compatible providers via `OPENAI_BASE_URL`, such as OpenRouter)

## Architecture

Frontend (`frontend/index.html`, `frontend/styles.css`, `frontend/app.js`)
-> sends JSON to backend  
Backend (`backend.py`)
-> computes advisory results and returns JSON

## Backend (`backend.py`)

### Data model

- `COURSES`: sample catalog with course name, credits, prerequisites, offering term, category.
- `DEGREE_REQUIREMENTS`: required course list + minimum credit rules.
- `FOUR_YEAR_TEMPLATE`: template used for semester-by-semester schedule output.
- `INTEREST_TO_ELECTIVES`: maps interest keywords to elective courses.

### Core functions

- `split_csv_codes(raw)`: converts comma-separated course input into a normalized set.
- `infer_intents(message)`: detects user intent (plan/prereq/electives/graduation).
- `generate_plan(completed)`: builds schedule output by year/semester from template.
- `check_prerequisites(message, completed)`: validates whether student can take requested courses.
- `suggest_electives(message, interests_raw, completed)`: recommends electives and readiness.
- `graduation_audit(completed)`: checks credits and requirement gaps.
- `fallback_response(message, profile)`: rule-based orchestration across advisor features.
- `llm_response(...)`: optional LLM refinement on top of rule-based output.

### API endpoint

`POST /api/chat`

Request JSON:

```json
{
  "message": "Check prerequisites for CS220 and CS310",
  "history": [],
  "profile": {
    "major": "Computer Science",
    "year": "Sophomore",
    "interests": "AI, data",
    "completed_courses": "CS101,CS102,MATH101,STAT201"
  }
}
```

Response JSON:

```json
{
  "reply": "Advisor output...",
  "mode": "rule-based"
}
```

Possible modes:

- `rule-based`
- `llm`

## Frontend

### `frontend/index.html`

- Hero section for product purpose.
- Student profile form:
  - major
  - current year
  - interests
  - completed courses
- Quick action buttons:
  - plan schedule
  - check prerequisites
  - suggest electives
  - graduation audit
- Chat panel for conversation.

### `frontend/app.js`

- Reads profile field values.
- Sends `{ message, history, profile }` to backend.
- Maintains local chat history.
- Renders assistant and user bubbles.
- Supports quick action buttons that prefill message box.

### `frontend/styles.css`

- Card-based layout and responsive behavior.
- Distinct styles for profile panel and chat panel.
- Mobile-friendly grid collapse below 720px.

## Run flow

1. User fills profile and sends message.
2. Frontend calls `POST /api/chat`.
3. Backend infers intents and generates advisor results.
4. Backend optionally uses LLM if configured.
5. Response is shown in chat.

## Notes and limits

- Catalog/requirements are sample data; update them for your school.
- Prerequisite checking uses exact course codes and sample prerequisites.
- Graduation audit is policy approximation, not official registrar output.

## Extension roadmap

1. Add real university catalog in JSON/DB.
2. Add multiple majors and minor constraints.
3. Add term availability and seat constraints.
4. Persist users/plans in a database.
5. Add tests for all advisor functions and API cases.
