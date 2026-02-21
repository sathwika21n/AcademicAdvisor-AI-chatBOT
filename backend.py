import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from flask import Flask, jsonify, request, send_from_directory

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "frontend"
INDEX_FILE = "index.html"

SYSTEM_PROMPT = (
    "You are an AI academic advisor. Help with 4-year schedules, prerequisites, "
    "elective suggestions based on interests, and graduation requirement warnings. "
    "Be concise, practical, and avoid claiming institutional policy certainty."
)

COURSES: Dict[str, Dict[str, Any]] = {
    "FYS100": {"name": "First-Year Seminar", "credits": 1, "prereqs": [], "offered": ["fall"], "category": "gened"},
    "ENG101": {"name": "College Writing", "credits": 3, "prereqs": [], "offered": ["fall", "spring"], "category": "gened"},
    "MATH101": {"name": "Calculus I", "credits": 4, "prereqs": [], "offered": ["fall", "spring"], "category": "math"},
    "MATH102": {"name": "Calculus II", "credits": 4, "prereqs": ["MATH101"], "offered": ["fall", "spring"], "category": "math"},
    "CS101": {"name": "Intro to Programming", "credits": 4, "prereqs": [], "offered": ["fall", "spring"], "category": "core"},
    "CS102": {"name": "Data Structures", "credits": 4, "prereqs": ["CS101"], "offered": ["fall", "spring"], "category": "core"},
    "CS201": {"name": "Computer Organization", "credits": 3, "prereqs": ["CS102"], "offered": ["fall"], "category": "core"},
    "CS210": {"name": "Discrete Mathematics", "credits": 3, "prereqs": ["MATH101"], "offered": ["spring"], "category": "core"},
    "CS220": {"name": "Algorithms", "credits": 3, "prereqs": ["CS102", "CS210"], "offered": ["fall", "spring"], "category": "core"},
    "CS230": {"name": "Databases", "credits": 3, "prereqs": ["CS102"], "offered": ["fall", "spring"], "category": "core"},
    "CS240": {"name": "Operating Systems", "credits": 3, "prereqs": ["CS201"], "offered": ["spring"], "category": "core"},
    "CS250": {"name": "Software Engineering", "credits": 3, "prereqs": ["CS220"], "offered": ["fall"], "category": "core"},
    "STAT201": {"name": "Statistics", "credits": 3, "prereqs": ["MATH101"], "offered": ["fall", "spring"], "category": "math"},
    "HUM101": {"name": "Humanities Elective", "credits": 3, "prereqs": [], "offered": ["fall", "spring"], "category": "humanities"},
    "SOC101": {"name": "Social Science Elective", "credits": 3, "prereqs": [], "offered": ["fall", "spring"], "category": "social"},
    "CS310": {"name": "Machine Learning", "credits": 3, "prereqs": ["CS220", "STAT201"], "offered": ["spring"], "category": "elective"},
    "CS320": {"name": "Cybersecurity", "credits": 3, "prereqs": ["CS240"], "offered": ["fall"], "category": "elective"},
    "CS330": {"name": "Mobile App Development", "credits": 3, "prereqs": ["CS250"], "offered": ["spring"], "category": "elective"},
    "CS340": {"name": "Data Visualization", "credits": 3, "prereqs": ["CS230", "STAT201"], "offered": ["fall"], "category": "elective"},
    "CS350": {"name": "Cloud Computing", "credits": 3, "prereqs": ["CS240"], "offered": ["spring"], "category": "elective"},
    "CS360": {"name": "Natural Language Processing", "credits": 3, "prereqs": ["CS310"], "offered": ["spring"], "category": "elective"},
    "CS490": {"name": "Senior Capstone", "credits": 3, "prereqs": ["CS250"], "offered": ["fall", "spring"], "category": "capstone"},
}

DEGREE_REQUIREMENTS = {
    "required_courses": {
        "CS101", "CS102", "CS201", "CS210", "CS220", "CS230", "CS240", "CS250",
        "MATH101", "MATH102", "STAT201", "ENG101", "FYS100", "CS490",
    },
    "min_credits": 120,
    "min_humanities_credits": 6,
    "min_social_credits": 6,
    "min_elective_credits": 15,
}

FOUR_YEAR_TEMPLATE: List[List[str]] = [
    ["FYS100", "ENG101", "CS101", "MATH101"],
    ["MATH102", "CS102", "HUM101", "SOC101"],
    ["CS201", "CS210", "STAT201", "HUM101"],
    ["CS220", "CS230", "SOC101", "ELX100"],
    ["CS250", "ELX200", "ELX201", "GEN200"],
    ["CS240", "ELX202", "ELX203", "GEN201"],
    ["ELX300", "ELX301", "GEN300", "GEN301"],
    ["CS490", "ELX302", "ELX303", "GEN302"],
]

INTEREST_TO_ELECTIVES = {
    "ai": ["CS310", "CS360"],
    "machine learning": ["CS310", "CS360"],
    "data": ["CS340", "CS230", "CS310"],
    "security": ["CS320"],
    "cybersecurity": ["CS320"],
    "mobile": ["CS330"],
    "cloud": ["CS350"],
    "software": ["CS250", "CS330"],
}


def create_client() -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def split_csv_codes(raw: str) -> Set[str]:
    if not raw:
        return set()
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


def course_credits(code: str) -> int:
    return int(COURSES.get(code, {}).get("credits", 3))


def describe_course(code: str) -> str:
    info = COURSES.get(code)
    if info:
        return f"{code} ({info['name']}, {info['credits']} cr)"
    return code


def infer_intents(message: str) -> Set[str]:
    lower = message.lower()
    intents = set()
    if any(token in lower for token in ["4-year", "four year", "plan schedule", "degree plan", "semester plan", "roadmap"]):
        intents.add("plan")
    if any(token in lower for token in ["prereq", "prerequisite", "can i take", "eligible"]):
        intents.add("prereq")
    if any(token in lower for token in ["elective", "interest", "specialization", "focus area"]):
        intents.add("electives")
    if any(token in lower for token in ["graduation", "graduate", "requirement", "audit"]):
        intents.add("graduation")
    if not intents:
        intents.update({"plan", "prereq", "electives", "graduation"})
    return intents


def generate_plan(completed: Set[str]) -> str:
    taken = set(completed)
    warnings: List[str] = []
    lines: List[str] = ["Suggested 4-Year Schedule (CS template):"]

    for idx, term in enumerate(FOUR_YEAR_TEMPLATE):
        label = f"Year {idx // 2 + 1} {'Fall' if idx % 2 == 0 else 'Spring'}"
        term_courses: List[str] = []
        for code in term:
            if code.startswith("ELX"):
                term_courses.append(f"{code} (Tech Elective, 3 cr)")
                continue
            if code.startswith("GEN"):
                term_courses.append(f"{code} (General Elective, 3 cr)")
                continue
            if code in taken:
                continue
            prereqs = COURSES.get(code, {}).get("prereqs", [])
            unmet = [p for p in prereqs if p not in taken]
            if unmet:
                warnings.append(f"{code} moved later because unmet prerequisites: {', '.join(unmet)}")
                term_courses.append(f"{code} (defer: missing {', '.join(unmet)})")
            else:
                term_courses.append(describe_course(code))
                taken.add(code)
        if not term_courses:
            term_courses = ["Free semester slot (consider minor/internship/research)"]
        term_credits = 0
        for item in term_courses:
            code_match = re.match(r"^([A-Z]{2,4}\d{3})\b", item)
            if code_match:
                term_credits += course_credits(code_match.group(1))
            else:
                term_credits += 3
        lines.append(f"- {label} [{term_credits} cr]: " + "; ".join(term_courses))

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings[:6]:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("Note: confirm this plan with your official university catalog and advisor.")
    return "\n".join(lines)


def check_prerequisites(message: str, completed: Set[str]) -> str:
    codes = set(re.findall(r"\b[A-Za-z]{2,4}\d{3}\b", message.upper()))
    if not codes:
        return "Please include a course code (example: CS220) so I can check prerequisites."
    lines = ["Prerequisite Check:"]
    for code in sorted(codes):
        info = COURSES.get(code)
        if not info:
            lines.append(f"- {code}: not found in sample catalog.")
            continue
        prereqs = info["prereqs"]
        unmet = [p for p in prereqs if p not in completed]
        if unmet:
            lines.append(f"- {code}: not ready yet. Missing {', '.join(unmet)}.")
        else:
            lines.append(f"- {code}: eligible based on your completed courses.")
    return "\n".join(lines)


def suggest_electives(message: str, interests_raw: str, completed: Set[str]) -> str:
    interest_text = f"{interests_raw} {message}".lower()
    picks: List[str] = []
    for key, courses in INTEREST_TO_ELECTIVES.items():
        if key in interest_text:
            for course in courses:
                if course not in picks:
                    picks.append(course)
    if not picks:
        picks = ["CS310", "CS320", "CS330", "CS340", "CS350"]

    lines = ["Elective Suggestions:"]
    for code in picks[:6]:
        info = COURSES.get(code)
        if not info:
            continue
        unmet = [p for p in info["prereqs"] if p not in completed]
        readiness = "ready" if not unmet else f"needs {', '.join(unmet)} first"
        lines.append(f"- {code} ({info['name']}): {readiness}.")
    return "\n".join(lines)


def graduation_audit(completed: Set[str]) -> str:
    required = DEGREE_REQUIREMENTS["required_courses"]
    missing_required = sorted(required - completed)
    completed_credits = sum(course_credits(code) for code in completed if code in COURSES)

    humanities_credits = sum(
        course_credits(code)
        for code in completed
        if COURSES.get(code, {}).get("category") == "humanities"
    )
    social_credits = sum(
        course_credits(code)
        for code in completed
        if COURSES.get(code, {}).get("category") == "social"
    )
    elective_credits = sum(
        course_credits(code)
        for code in completed
        if COURSES.get(code, {}).get("category") == "elective"
    )

    lines = ["Graduation Requirement Audit (sample CS policy):"]
    lines.append(f"- Total completed credits: {completed_credits} / {DEGREE_REQUIREMENTS['min_credits']}")
    lines.append(f"- Humanities credits: {humanities_credits} / {DEGREE_REQUIREMENTS['min_humanities_credits']}")
    lines.append(f"- Social science credits: {social_credits} / {DEGREE_REQUIREMENTS['min_social_credits']}")
    lines.append(f"- Technical elective credits: {elective_credits} / {DEGREE_REQUIREMENTS['min_elective_credits']}")
    lines.append(f"- Required courses completed: {len(required & completed)} / {len(required)}")
    if missing_required:
        lines.append("- Missing required courses: " + ", ".join(missing_required[:12]))
    if completed_credits < DEGREE_REQUIREMENTS["min_credits"]:
        lines.append(
            f"- Warning: you still need at least {DEGREE_REQUIREMENTS['min_credits'] - completed_credits} credits."
        )
    if humanities_credits < DEGREE_REQUIREMENTS["min_humanities_credits"]:
        lines.append("- Warning: humanities minimum not met.")
    if social_credits < DEGREE_REQUIREMENTS["min_social_credits"]:
        lines.append("- Warning: social science minimum not met.")
    if elective_credits < DEGREE_REQUIREMENTS["min_elective_credits"]:
        lines.append("- Warning: technical elective minimum not met.")
    if not missing_required and completed_credits >= DEGREE_REQUIREMENTS["min_credits"]:
        lines.append("- Status: on track for graduation based on this sample dataset.")
    return "\n".join(lines)


def fallback_response(message: str, profile: Dict[str, Any]) -> str:
    completed = split_csv_codes(profile.get("completed_courses", ""))
    interests = (profile.get("interests") or "").strip()
    intents = infer_intents(message)

    sections: List[str] = []
    if "plan" in intents:
        sections.append(generate_plan(completed))
    if "prereq" in intents:
        sections.append(check_prerequisites(message, completed))
    if "electives" in intents:
        sections.append(suggest_electives(message, interests, completed))
    if "graduation" in intents:
        sections.append(graduation_audit(completed))
    return "\n\n".join(sections)


def llm_response(client: Any, history: List[Dict[str, str]], profile: Dict[str, Any], rule_result: str) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    profile_text = (
        "Student profile:\n"
        f"- Major: {profile.get('major') or 'Computer Science'}\n"
        f"- Year: {profile.get('year') or 'not provided'}\n"
        f"- Interests: {profile.get('interests') or 'not provided'}\n"
        f"- Completed courses: {profile.get('completed_courses') or 'none'}\n\n"
        "Rule-based draft advisory output:\n"
        f"{rule_result}"
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "system", "content": profile_text}] + history
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=700,
    )
    return completion.choices[0].message.content or rule_result


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
    profile = payload.get("profile") or {}

    if not message:
        return jsonify({"error": "Message is required."}), 400

    safe_history: List[Dict[str, str]] = []
    for item in history[-10:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            safe_history.append({"role": role, "content": content})
    safe_history.append({"role": "user", "content": message})

    rule_result = fallback_response(message, profile)
    if client is None:
        return jsonify({"reply": rule_result, "mode": "rule-based"})

    try:
        reply = llm_response(client, safe_history, profile, rule_result)
        return jsonify({"reply": reply, "mode": "llm"})
    except Exception:
        return jsonify({"reply": rule_result, "mode": "rule-based"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
