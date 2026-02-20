import os
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend"
INDEX_FILE = "index.html"

CRISIS_TERMS = {
    "suicide",
    "kill myself",
    "end my life",
    "harm myself",
    "self harm",
    "self-harm",
    "i want to die",
    "i don't want to live",
    "hurting myself",
}

SYSTEM_PROMPT = (
    "You are a supportive mental wellness assistant for non-diagnostic guidance. "
    "Use empathetic language, ask one short clarifying question when useful, and "
    "offer practical coping steps. Do not provide diagnosis, medication dosing, or "
    "medical/legal certainty. If user expresses risk of self-harm or harm to others, "
    "urge immediate local emergency help and crisis hotlines."
)

FALLBACK_OPENING = (
    "I hear you, and I’m glad you reached out. I’m here to support you."
)


def create_client() -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def contains_crisis_signal(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in CRISIS_TERMS)


def crisis_response() -> str:
    return (
        "I’m really glad you shared this. Your safety matters most right now.\n\n"
        "If you might act on these thoughts, call emergency services immediately "
        "(911 in the U.S.). You can also call or text 988 (Suicide & Crisis Lifeline) "
        "right now for 24/7 support.\n\n"
        "If you’re outside the U.S., contact your local emergency number or nearest "
        "crisis line. If you want, I can stay with you while you take that next step."
    )


def fallback_response(user_text: str) -> str:
    prompt_lower = user_text.lower()
    if "anx" in prompt_lower or "panic" in prompt_lower:
        return (
            f"{FALLBACK_OPENING} Anxiety can feel intense, but it can pass.\n\n"
            "Try this quick reset:\n"
            "1. Inhale for 4 seconds, exhale for 6 seconds, repeat for 1-2 minutes.\n"
            "2. Name 5 things you can see, 4 you can feel, 3 you can hear.\n"
            "3. Take one tiny next step (water, short walk, text a trusted person).\n\n"
            "Would you like a 5-minute plan for the rest of today?"
        )
    if "depress" in prompt_lower or "empty" in prompt_lower or "hopeless" in prompt_lower:
        return (
            f"{FALLBACK_OPENING} Feeling low can make everything heavier.\n\n"
            "A gentle plan for now:\n"
            "1. Do one body reset: drink water, shower, or step outside.\n"
            "2. Choose one manageable task under 10 minutes.\n"
            "3. Reach out to one person with a short check-in message.\n\n"
            "If this has been lasting for a while, talking to a licensed therapist "
            "could really help. Want help drafting a message to someone you trust?"
        )
    if "sleep" in prompt_lower or "insomnia" in prompt_lower:
        return (
            f"{FALLBACK_OPENING} Sleep issues are exhausting.\n\n"
            "Try a wind-down routine tonight:\n"
            "1. No caffeine late day and avoid screens 30-60 mins before bed.\n"
            "2. Keep lights low and do a calm activity (reading, stretching, breathing).\n"
            "3. If awake >20 mins, leave bed briefly and return when sleepy.\n\n"
            "Want a personalized routine based on your schedule?"
        )
    return (
        f"{FALLBACK_OPENING} Thank you for sharing that.\n\n"
        "We can take this one step at a time. A simple structure is:\n"
        "1. Name what you’re feeling in one sentence.\n"
        "2. Pick one immediate coping action (breathing, grounding, short walk).\n"
        "3. Identify one person/resource you can contact today.\n\n"
        "Would you like me to help you build a plan for the next hour?"
    )


def llm_response(client: Any, history: List[Dict[str, str]]) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.6,
        max_tokens=400,
    )
    return completion.choices[0].message.content or fallback_response(history[-1]["content"])


app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path="/static")
client = create_client()


@app.get("/")
def home() -> Any:
    return send_from_directory(STATIC_DIR, INDEX_FILE)


@app.post("/api/chat")
def chat() -> Any:
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []

    if not message:
        return jsonify({"error": "Message is required."}), 400

    if contains_crisis_signal(message):
        return jsonify({"reply": crisis_response(), "mode": "crisis"})

    safe_history: List[Dict[str, str]] = []
    for item in history[-10:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            safe_history.append({"role": role, "content": content})
    safe_history.append({"role": "user", "content": message})

    if client is None:
        return jsonify({"reply": fallback_response(message), "mode": "fallback"})

    try:
        reply = llm_response(client, safe_history)
        if contains_crisis_signal(reply):
            reply = crisis_response()
            mode = "crisis"
        else:
            mode = "llm"
        return jsonify({"reply": reply, "mode": mode})
    except Exception:
        return jsonify({"reply": fallback_response(message), "mode": "fallback"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
