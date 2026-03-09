import os
import re
from typing import Any, Dict, List, Set, Tuple

from flask import Flask, jsonify, request

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


SYSTEM_PROMPT = (
    "You are an AI academic advisor. Help with 4-year schedules, prerequisites, "
    "elective suggestions based on interests, and graduation requirement warnings. "
    "Be practical and clearly label assumptions."
)

INTEREST_TO_ELECTIVES = {
    "ai": ["CS310", "CS360", "DS330"],
    "machine learning": ["CS310", "CS360", "DS330"],
    "data": ["CS340", "CS230", "DS330", "DS340"],
    "security": ["CS320"],
    "cybersecurity": ["CS320"],
    "mobile": ["CS330"],
    "cloud": ["CS350"],
    "software": ["CS250", "CS330"],
    "analytics": ["DS340", "STAT310"],
    "business": ["BUS320", "BUS330"],
    "finance": ["BUS340", "ECON210"],
}

ACADEMIC_DATA: Dict[str, Dict[str, Any]] = {
    "State University": {
        "majors": {
            "Computer Science": {
                "courses": {
                    "FYS100": {"name": "First-Year Seminar", "credits": 1, "prereqs": [], "category": "gened"},
                    "ENG101": {"name": "College Writing", "credits": 3, "prereqs": [], "category": "gened"},
                    "MATH101": {"name": "Calculus I", "credits": 4, "prereqs": [], "category": "math"},
                    "MATH102": {"name": "Calculus II", "credits": 4, "prereqs": ["MATH101"], "category": "math"},
                    "CS101": {"name": "Intro to Programming", "credits": 4, "prereqs": [], "category": "core"},
                    "CS102": {"name": "Data Structures", "credits": 4, "prereqs": ["CS101"], "category": "core"},
                    "CS201": {"name": "Computer Organization", "credits": 3, "prereqs": ["CS102"], "category": "core"},
                    "CS210": {"name": "Discrete Mathematics", "credits": 3, "prereqs": ["MATH101"], "category": "core"},
                    "CS220": {"name": "Algorithms", "credits": 3, "prereqs": ["CS102", "CS210"], "category": "core"},
                    "CS230": {"name": "Databases", "credits": 3, "prereqs": ["CS102"], "category": "core"},
                    "CS240": {"name": "Operating Systems", "credits": 3, "prereqs": ["CS201"], "category": "core"},
                    "CS250": {"name": "Software Engineering", "credits": 3, "prereqs": ["CS220"], "category": "core"},
                    "STAT201": {"name": "Statistics", "credits": 3, "prereqs": ["MATH101"], "category": "math"},
                    "HUM101": {"name": "Humanities Elective", "credits": 3, "prereqs": [], "category": "humanities"},
                    "SOC101": {"name": "Social Science Elective", "credits": 3, "prereqs": [], "category": "social"},
                    "CS310": {"name": "Machine Learning", "credits": 3, "prereqs": ["CS220", "STAT201"], "category": "elective"},
                    "CS320": {"name": "Cybersecurity", "credits": 3, "prereqs": ["CS240"], "category": "elective"},
                    "CS330": {"name": "Mobile App Development", "credits": 3, "prereqs": ["CS250"], "category": "elective"},
                    "CS340": {"name": "Data Visualization", "credits": 3, "prereqs": ["CS230", "STAT201"], "category": "elective"},
                    "CS350": {"name": "Cloud Computing", "credits": 3, "prereqs": ["CS240"], "category": "elective"},
                    "CS360": {"name": "Natural Language Processing", "credits": 3, "prereqs": ["CS310"], "category": "elective"},
                    "CS490": {"name": "Senior Capstone", "credits": 3, "prereqs": ["CS250"], "category": "capstone"},
                },
                "degree_requirements": {
                    "required_courses": [
                        "FYS100", "ENG101", "MATH101", "MATH102", "CS101", "CS102", "CS201",
                        "CS210", "CS220", "CS230", "CS240", "CS250", "STAT201", "CS490",
                    ],
                    "min_credits": 120,
                    "min_humanities_credits": 6,
                    "min_social_credits": 6,
                    "min_elective_credits": 15,
                },
                "four_year_template": [
                    ["FYS100", "ENG101", "CS101", "MATH101"],
                    ["MATH102", "CS102", "HUM101", "SOC101"],
                    ["CS201", "CS210", "STAT201", "HUM101"],
                    ["CS220", "CS230", "SOC101", "ELX100"],
                    ["CS250", "ELX200", "ELX201", "GEN200"],
                    ["CS240", "ELX202", "ELX203", "GEN201"],
                    ["ELX300", "ELX301", "GEN300", "GEN301"],
                    ["CS490", "ELX302", "ELX303", "GEN302"],
                ],
                "default_electives": ["CS310", "CS320", "CS330", "CS340", "CS350"],
            },
            "Data Science": {
                "courses": {
                    "FYS100": {"name": "First-Year Seminar", "credits": 1, "prereqs": [], "category": "gened"},
                    "ENG101": {"name": "College Writing", "credits": 3, "prereqs": [], "category": "gened"},
                    "MATH101": {"name": "Calculus I", "credits": 4, "prereqs": [], "category": "math"},
                    "MATH102": {"name": "Calculus II", "credits": 4, "prereqs": ["MATH101"], "category": "math"},
                    "STAT201": {"name": "Statistics I", "credits": 3, "prereqs": ["MATH101"], "category": "math"},
                    "STAT310": {"name": "Applied Regression", "credits": 3, "prereqs": ["STAT201"], "category": "elective"},
                    "CS101": {"name": "Intro to Programming", "credits": 4, "prereqs": [], "category": "core"},
                    "CS102": {"name": "Data Structures", "credits": 4, "prereqs": ["CS101"], "category": "core"},
                    "DS200": {"name": "Data Wrangling", "credits": 3, "prereqs": ["CS101"], "category": "core"},
                    "DS210": {"name": "Data Ethics", "credits": 3, "prereqs": [], "category": "core"},
                    "DS220": {"name": "Data Visualization", "credits": 3, "prereqs": ["DS200", "STAT201"], "category": "core"},
                    "DS300": {"name": "Machine Learning Foundations", "credits": 3, "prereqs": ["CS102", "MATH102", "STAT201"], "category": "core"},
                    "DS330": {"name": "Applied Machine Learning", "credits": 3, "prereqs": ["DS300"], "category": "elective"},
                    "DS340": {"name": "Business Analytics", "credits": 3, "prereqs": ["DS220"], "category": "elective"},
                    "HUM101": {"name": "Humanities Elective", "credits": 3, "prereqs": [], "category": "humanities"},
                    "HUM102": {"name": "Humanities Elective II", "credits": 3, "prereqs": [], "category": "humanities"},
                    "SOC101": {"name": "Social Science Elective", "credits": 3, "prereqs": [], "category": "social"},
                    "SOC102": {"name": "Social Science Elective II", "credits": 3, "prereqs": [], "category": "social"},
                    "DS490": {"name": "Data Science Capstone", "credits": 3, "prereqs": ["DS300"], "category": "capstone"},
                },
                "degree_requirements": {
                    "required_courses": [
                        "FYS100", "ENG101", "MATH101", "MATH102", "STAT201", "CS101", "CS102",
                        "DS200", "DS210", "DS220", "DS300", "DS490",
                    ],
                    "min_credits": 120,
                    "min_humanities_credits": 6,
                    "min_social_credits": 6,
                    "min_elective_credits": 12,
                },
                "four_year_template": [
                    ["FYS100", "ENG101", "CS101", "MATH101"],
                    ["MATH102", "STAT201", "DS210", "HUM101"],
                    ["CS102", "DS200", "SOC101", "HUM102"],
                    ["DS220", "SOC102", "ELX100", "GEN200"],
                    ["DS300", "ELX200", "ELX201", "GEN201"],
                    ["ELX202", "ELX203", "GEN202", "GEN203"],
                    ["ELX300", "ELX301", "GEN300", "GEN301"],
                    ["DS490", "ELX302", "ELX303", "GEN302"],
                ],
                "default_electives": ["DS330", "DS340", "STAT310"],
            },
        }
    },
    "Metro Tech Institute": {
        "majors": {
            "Computer Science": {
                "courses": {
                    "COLL100": {"name": "College Success", "credits": 2, "prereqs": [], "category": "gened"},
                    "ENG110": {"name": "Technical Writing", "credits": 3, "prereqs": [], "category": "gened"},
                    "MATH115": {"name": "Calculus for Computing", "credits": 4, "prereqs": [], "category": "math"},
                    "CS105": {"name": "Programming Fundamentals", "credits": 4, "prereqs": [], "category": "core"},
                    "CS115": {"name": "Object-Oriented Programming", "credits": 4, "prereqs": ["CS105"], "category": "core"},
                    "CS205": {"name": "Data Structures", "credits": 4, "prereqs": ["CS115"], "category": "core"},
                    "CS215": {"name": "Computer Systems", "credits": 3, "prereqs": ["CS205"], "category": "core"},
                    "CS225": {"name": "Discrete Structures", "credits": 3, "prereqs": ["MATH115"], "category": "core"},
                    "CS305": {"name": "Algorithms", "credits": 3, "prereqs": ["CS205", "CS225"], "category": "core"},
                    "CS315": {"name": "Database Systems", "credits": 3, "prereqs": ["CS205"], "category": "core"},
                    "CS325": {"name": "Operating Systems", "credits": 3, "prereqs": ["CS215"], "category": "core"},
                    "CS335": {"name": "Software Project", "credits": 3, "prereqs": ["CS305"], "category": "core"},
                    "STAT210": {"name": "Statistics for Engineers", "credits": 3, "prereqs": ["MATH115"], "category": "math"},
                    "HUM200": {"name": "Humanities Elective", "credits": 3, "prereqs": [], "category": "humanities"},
                    "SOC200": {"name": "Social Science Elective", "credits": 3, "prereqs": [], "category": "social"},
                    "CS410": {"name": "Cloud Platforms", "credits": 3, "prereqs": ["CS325"], "category": "elective"},
                    "CS420": {"name": "Secure Systems", "credits": 3, "prereqs": ["CS325"], "category": "elective"},
                    "CS430": {"name": "Mobile Engineering", "credits": 3, "prereqs": ["CS335"], "category": "elective"},
                    "CS499": {"name": "Senior Design", "credits": 3, "prereqs": ["CS335"], "category": "capstone"},
                },
                "degree_requirements": {
                    "required_courses": [
                        "COLL100", "ENG110", "MATH115", "CS105", "CS115", "CS205", "CS215",
                        "CS225", "CS305", "CS315", "CS325", "CS335", "STAT210", "CS499",
                    ],
                    "min_credits": 122,
                    "min_humanities_credits": 6,
                    "min_social_credits": 6,
                    "min_elective_credits": 12,
                },
                "four_year_template": [
                    ["COLL100", "ENG110", "CS105", "MATH115"],
                    ["CS115", "CS225", "HUM200", "SOC200"],
                    ["CS205", "STAT210", "HUM200", "GEN200"],
                    ["CS215", "CS315", "SOC200", "GEN201"],
                    ["CS305", "ELX200", "ELX201", "GEN202"],
                    ["CS325", "CS335", "ELX202", "GEN203"],
                    ["ELX300", "ELX301", "GEN300", "GEN301"],
                    ["CS499", "ELX302", "ELX303", "GEN302"],
                ],
                "default_electives": ["CS410", "CS420", "CS430"],
            },
            "Business Analytics": {
                "courses": {
                    "COLL100": {"name": "College Success", "credits": 2, "prereqs": [], "category": "gened"},
                    "ENG110": {"name": "Technical Writing", "credits": 3, "prereqs": [], "category": "gened"},
                    "MATH110": {"name": "Business Calculus", "credits": 3, "prereqs": [], "category": "math"},
                    "STAT200": {"name": "Business Statistics", "credits": 3, "prereqs": ["MATH110"], "category": "math"},
                    "BUS101": {"name": "Intro to Business", "credits": 3, "prereqs": [], "category": "core"},
                    "ECON210": {"name": "Microeconomics", "credits": 3, "prereqs": [], "category": "core"},
                    "ACCT201": {"name": "Financial Accounting", "credits": 3, "prereqs": [], "category": "core"},
                    "BA220": {"name": "Spreadsheet Modeling", "credits": 3, "prereqs": [], "category": "core"},
                    "BA250": {"name": "Programming for Analytics", "credits": 3, "prereqs": [], "category": "core"},
                    "BA310": {"name": "Data Management", "credits": 3, "prereqs": ["BA250"], "category": "core"},
                    "BA320": {"name": "Analytics Methods", "credits": 3, "prereqs": ["STAT200", "BA250"], "category": "core"},
                    "BUS320": {"name": "Marketing Analytics", "credits": 3, "prereqs": ["BA320"], "category": "elective"},
                    "BUS330": {"name": "Operations Analytics", "credits": 3, "prereqs": ["BA320"], "category": "elective"},
                    "BUS340": {"name": "Financial Analytics", "credits": 3, "prereqs": ["BA320", "ACCT201"], "category": "elective"},
                    "HUM200": {"name": "Humanities Elective", "credits": 3, "prereqs": [], "category": "humanities"},
                    "SOC200": {"name": "Social Science Elective", "credits": 3, "prereqs": [], "category": "social"},
                    "BA490": {"name": "Analytics Capstone", "credits": 3, "prereqs": ["BA320"], "category": "capstone"},
                },
                "degree_requirements": {
                    "required_courses": [
                        "COLL100", "ENG110", "MATH110", "STAT200", "BUS101", "ECON210", "ACCT201",
                        "BA220", "BA250", "BA310", "BA320", "BA490",
                    ],
                    "min_credits": 120,
                    "min_humanities_credits": 6,
                    "min_social_credits": 6,
                    "min_elective_credits": 9,
                },
                "four_year_template": [
                    ["COLL100", "ENG110", "BUS101", "MATH110"],
                    ["ECON210", "ACCT201", "BA220", "HUM200"],
                    ["STAT200", "BA250", "SOC200", "GEN200"],
                    ["BA310", "SOC200", "HUM200", "GEN201"],
                    ["BA320", "ELX200", "ELX201", "GEN202"],
                    ["ELX202", "ELX203", "GEN203", "GEN204"],
                    ["ELX300", "ELX301", "GEN300", "GEN301"],
                    ["BA490", "ELX302", "ELX303", "GEN302"],
                ],
                "default_electives": ["BUS320", "BUS330", "BUS340"],
            },
        }
    },
}


def create_client() -> Any:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def split_csv_codes(raw: str) -> Set[str]:
    if not raw:
        return set()
    return {item.strip().upper() for item in raw.split(",") if item.strip()}


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


def get_program(college: str, major: str) -> Tuple[str, str, Dict[str, Any] | None]:
    if college in ACADEMIC_DATA and major in ACADEMIC_DATA[college]["majors"]:
        return college, major, ACADEMIC_DATA[college]["majors"][major]
    default_college = next(iter(ACADEMIC_DATA))
    default_major = next(iter(ACADEMIC_DATA[default_college]["majors"]))
    return default_college, default_major, None


def get_resolved_program(profile: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any], bool]:
    selected_college = (profile.get("college") or "").strip()
    selected_major = (profile.get("major") or "").strip()
    if selected_college in ACADEMIC_DATA and selected_major in ACADEMIC_DATA[selected_college]["majors"]:
        return selected_college, selected_major, ACADEMIC_DATA[selected_college]["majors"][selected_major], True
    default_college = next(iter(ACADEMIC_DATA))
    default_major = next(iter(ACADEMIC_DATA[default_college]["majors"]))
    return default_college, default_major, ACADEMIC_DATA[default_college]["majors"][default_major], False


def course_credits(code: str, courses: Dict[str, Dict[str, Any]]) -> int:
    return int(courses.get(code, {}).get("credits", 3))


def describe_course(code: str, courses: Dict[str, Dict[str, Any]]) -> str:
    info = courses.get(code)
    if info:
        return f"{code} ({info['name']}, {info['credits']} cr)"
    return code


def generate_plan(completed: Set[str], program: Dict[str, Any], major_name: str) -> str:
    courses = program["courses"]
    template = program["four_year_template"]
    taken = set(completed)
    warnings: List[str] = []
    lines: List[str] = [f"Suggested 4-Year Schedule ({major_name} template):"]

    for idx, term in enumerate(template):
        label = f"Year {idx // 2 + 1} {'Fall' if idx % 2 == 0 else 'Spring'}"
        term_courses: List[str] = []
        for code in term:
            if code.startswith("ELX"):
                term_courses.append(f"{code} (Major/Tech Elective, 3 cr)")
                continue
            if code.startswith("GEN"):
                term_courses.append(f"{code} (General Elective, 3 cr)")
                continue
            if code in taken:
                continue
            prereqs = courses.get(code, {}).get("prereqs", [])
            unmet = [p for p in prereqs if p not in taken]
            if unmet:
                warnings.append(f"{code} has unmet prerequisites: {', '.join(unmet)}")
                term_courses.append(f"{code} (defer: missing {', '.join(unmet)})")
            else:
                term_courses.append(describe_course(code, courses))
                taken.add(code)
        if not term_courses:
            term_courses = ["Open slot (minor, internship, research, or electives)"]

        term_credits = 0
        for item in term_courses:
            code_match = re.match(r"^([A-Z]{2,4}\d{3})\b", item)
            if code_match:
                term_credits += course_credits(code_match.group(1), courses)
            else:
                term_credits += 3

        lines.append(f"- {label} [{term_credits} cr]: " + "; ".join(term_courses))

    if warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in warnings[:8]:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("Confirm this plan against the official catalog and department advisor.")
    return "\n".join(lines)


def check_prerequisites(message: str, completed: Set[str], program: Dict[str, Any]) -> str:
    codes = set(re.findall(r"\b[A-Za-z]{2,4}\d{3}\b", message.upper()))
    if not codes:
        return "Please include a course code (example: CS220) so I can check prerequisites."
    courses = program["courses"]
    lines = ["Prerequisite Check:"]
    for code in sorted(codes):
        info = courses.get(code)
        if not info:
            lines.append(f"- {code}: not found in the selected college/major sample catalog.")
            continue
        unmet = [p for p in info.get("prereqs", []) if p not in completed]
        if unmet:
            lines.append(f"- {code}: not ready yet. Missing {', '.join(unmet)}.")
        else:
            lines.append(f"- {code}: eligible based on your completed courses.")
    return "\n".join(lines)


def suggest_electives(message: str, interests_raw: str, completed: Set[str], program: Dict[str, Any]) -> str:
    courses = program["courses"]
    default_electives = [code for code in program.get("default_electives", []) if code in courses]
    interest_text = f"{interests_raw} {message}".lower()
    picks: List[str] = []

    for key, elective_codes in INTEREST_TO_ELECTIVES.items():
        if key in interest_text:
            for code in elective_codes:
                if code in courses and code not in picks:
                    picks.append(code)

    for code in default_electives:
        if code not in picks:
            picks.append(code)

    if not picks:
        picks = [code for code, info in courses.items() if info.get("category") == "elective"][:6]

    lines = ["Elective Suggestions:"]
    for code in picks[:6]:
        info = courses.get(code)
        if not info:
            continue
        unmet = [p for p in info.get("prereqs", []) if p not in completed]
        readiness = "ready now" if not unmet else f"needs {', '.join(unmet)} first"
        lines.append(f"- {code} ({info['name']}): {readiness}.")
    return "\n".join(lines)


def graduation_audit(completed: Set[str], program: Dict[str, Any], major_name: str) -> str:
    courses = program["courses"]
    reqs = program["degree_requirements"]
    required = set(reqs["required_courses"])
    missing_required = sorted(required - completed)
    completed_credits = sum(course_credits(code, courses) for code in completed if code in courses)

    humanities_credits = sum(course_credits(c, courses) for c in completed if courses.get(c, {}).get("category") == "humanities")
    social_credits = sum(course_credits(c, courses) for c in completed if courses.get(c, {}).get("category") == "social")
    elective_credits = sum(course_credits(c, courses) for c in completed if courses.get(c, {}).get("category") == "elective")

    lines = [f"Graduation Audit ({major_name}, sample policy):"]
    lines.append(f"- Total completed credits: {completed_credits} / {reqs['min_credits']}")
    lines.append(f"- Humanities credits: {humanities_credits} / {reqs['min_humanities_credits']}")
    lines.append(f"- Social science credits: {social_credits} / {reqs['min_social_credits']}")
    lines.append(f"- Elective credits: {elective_credits} / {reqs['min_elective_credits']}")
    lines.append(f"- Required courses completed: {len(required & completed)} / {len(required)}")
    if missing_required:
        lines.append("- Missing required courses: " + ", ".join(missing_required[:15]))

    if completed_credits < reqs["min_credits"]:
        lines.append(f"- Warning: need at least {reqs['min_credits'] - completed_credits} more credits.")
    if humanities_credits < reqs["min_humanities_credits"]:
        lines.append("- Warning: humanities minimum not met.")
    if social_credits < reqs["min_social_credits"]:
        lines.append("- Warning: social science minimum not met.")
    if elective_credits < reqs["min_elective_credits"]:
        lines.append("- Warning: elective minimum not met.")
    if not missing_required and completed_credits >= reqs["min_credits"]:
        lines.append("- Status: appears on track based on this sample dataset.")
    return "\n".join(lines)


def build_options_payload() -> Dict[str, Any]:
    colleges = []
    for college_name, college_data in ACADEMIC_DATA.items():
        majors = sorted(college_data["majors"].keys())
        colleges.append({"name": college_name, "majors": majors})
    default_college = colleges[0]["name"]
    default_major = colleges[0]["majors"][0]
    return {
        "colleges": colleges,
        "default_college": default_college,
        "default_major": default_major,
    }


def fallback_response(message: str, profile: Dict[str, Any]) -> str:
    completed = split_csv_codes(profile.get("completed_courses", ""))
    interests = (profile.get("interests") or "").strip()
    intents = infer_intents(message)
    college, major, program, exact_match = get_resolved_program(profile)
    selected_college = (profile.get("college") or "").strip()
    selected_major = (profile.get("major") or "").strip()

    sections: List[str] = []

    if (selected_college or selected_major) and not exact_match:
        sections.append(
            f"Program context: {selected_college or 'University not provided'} / "
            f"{selected_major or 'Major not provided'}."
        )
        sections.append(
            "This exact program is not in the local sample dataset, so I will provide general advising guidance."
        )
        if "electives" in intents:
            sections.append(
                "Elective Suggestions:\n- Share interests and career goals, and I can suggest likely elective areas and course types."
            )
        if "prereq" in intents:
            sections.append(
                "Prerequisite Check:\n- Exact prerequisites vary by catalog year; verify with your university's official course catalog."
            )
        if "plan" in intents:
            sections.append(
                "4-Year Plan:\n- I can draft a semester-by-semester plan structure and sequencing assumptions for your stated university/major."
            )
        if "graduation" in intents:
            sections.append(
                "Graduation Audit:\n- I can estimate progress, but exact requirement checks need your school's official degree worksheet."
            )
        return "\n\n".join(sections)

    if not exact_match:
        sections.append(
            f"Note: selected college/major not found. Using {college} - {major} sample dataset. "
            "Use the dropdowns to choose an available program."
        )
    sections.append(f"Program: {college} / {major}")

    if "plan" in intents:
        sections.append(generate_plan(completed, program, major))
    if "prereq" in intents:
        sections.append(check_prerequisites(message, completed, program))
    if "electives" in intents:
        sections.append(suggest_electives(message, interests, completed, program))
    if "graduation" in intents:
        sections.append(graduation_audit(completed, program, major))
    return "\n\n".join(sections)


def llm_response(client: Any, history: List[Dict[str, str]], profile: Dict[str, Any], rule_result: str) -> str:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    profile_text = (
        "Student profile:\n"
        f"- College: {profile.get('college') or 'not provided'}\n"
        f"- Major: {profile.get('major') or 'not provided'}\n"
        f"- Year: {profile.get('year') or 'not provided'}\n"
        f"- Interests: {profile.get('interests') or 'not provided'}\n"
        f"- Completed courses: {profile.get('completed_courses') or 'none'}\n\n"
        "Use the rule-based output as the primary source because it reflects the local sample degree-plan dataset.\n"
        f"{rule_result}"
    )
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "system", "content": profile_text}] + history
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=800,
    )
    return completion.choices[0].message.content or rule_result


app = Flask(__name__)
client = create_client()


@app.get("/api/options")
def options() -> Any:
    return jsonify(build_options_payload())


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
