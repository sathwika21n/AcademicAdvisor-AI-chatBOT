from __future__ import annotations

import os
import hmac
from typing import Any, Dict, List

import streamlit as st

import backend


st.set_page_config(
    page_title="DegreePath Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --bg: #f5f3ef;
            --ink: #17252f;
            --muted: #5f6b73;
            --card: #ffffff;
            --accent: #0f766e;
            --accent-soft: #d9f3ef;
            --line: #d7e0e4;
        }

        html, body, [class*="css"]  {
            font-family: "IBM Plex Sans", sans-serif;
            background: radial-gradient(circle at 10% 10%, #fff 0%, #f5f3ef 42%, #ece8e1 100%);
            color: var(--ink);
        }

        h1, h2, h3, h4 {
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -0.01em;
            color: var(--ink);
        }

        .hero {
            padding: 1.4rem 1.2rem 1rem 1.2rem;
            border: 1px solid var(--line);
            border-radius: 18px;
            background:
                linear-gradient(125deg, rgba(15,118,110,0.10), rgba(255,255,255,0.85)),
                #fff;
            margin-bottom: 1rem;
        }

        .eyebrow {
            display: inline-block;
            font-size: 0.78rem;
            font-weight: 700;
            color: #0a5d56;
            background: var(--accent-soft);
            border-radius: 999px;
            padding: 0.28rem 0.7rem;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .subhead {
            color: var(--muted);
            margin-top: 0.2rem;
            margin-bottom: 0;
        }

        .stChatMessage {
            border-radius: 14px;
            border: 1px solid var(--line);
            background: var(--card);
        }

        .pill {
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: #fff;
            color: var(--muted);
            font-size: 0.78rem;
            display: inline-block;
            margin-right: 0.45rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "auth_user" not in st.session_state:
        st.session_state.auth_user = ""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi, I am your AI academic advisor. I can build a 4-year schedule, "
                    "check prerequisites, suggest electives, and warn about graduation requirements."
                ),
            }
        ]
    if "school_results" not in st.session_state:
        st.session_state.school_results = []
    if "selected_school_id" not in st.session_state:
        st.session_state.selected_school_id = ""
    if "selected_school_label" not in st.session_state:
        st.session_state.selected_school_label = ""
    if "major_options" not in st.session_state:
        st.session_state.major_options = []
    if "profile" not in st.session_state:
        options = backend.build_options_payload()
        default_college = options["default_college"]
        default_major = options["default_major"]
        st.session_state.profile = {
            "college": default_college,
            "college_id": "",
            "major": default_major,
            "year": "",
            "interests": "",
            "completed_courses": "",
        }
        college_data = next((c for c in options["colleges"] if c["name"] == default_college), None)
        st.session_state.major_options = college_data["majors"] if college_data else [default_major]


def validate_login(username: str, password: str) -> bool:
    expected_user = os.getenv("APP_USERNAME", "student")
    expected_password = os.getenv("APP_PASSWORD", "advisor123")
    user_ok = hmac.compare_digest(username.strip(), expected_user)
    pass_ok = hmac.compare_digest(password, expected_password)
    return user_ok and pass_ok


def render_login() -> None:
    st.markdown(
        """
        <section class="hero">
          <span class="eyebrow">Secure Access</span>
          <h1 style="margin:0.15rem 0 0.15rem 0;">Sign In to DegreePath</h1>
          <p class="subhead">Use your account credentials to access advising tools.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.2, 1])
    with center:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)
        if submitted:
            if validate_login(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_user = username.strip()
                st.success("Login successful.")
                st.rerun()
            else:
                st.error("Invalid username or password.")
        st.caption("Set `APP_USERNAME` and `APP_PASSWORD` env vars to change login credentials.")


def assistant_reply(message: str, profile: Dict[str, str]) -> Dict[str, str]:
    safe_history: List[Dict[str, str]] = []
    for item in st.session_state.messages[-10:]:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role in {"user", "assistant"} and content:
            safe_history.append({"role": role, "content": content})
    safe_history.append({"role": "user", "content": message})

    rule_result = backend.fallback_response(message, profile)
    if backend.client is None:
        return {"reply": rule_result, "mode": "rule-based"}
    try:
        llm = backend.llm_response(backend.client, safe_history, profile, rule_result)
        return {"reply": llm, "mode": "llm"}
    except Exception:
        return {"reply": rule_result, "mode": "rule-based"}


def update_major_options_from_selection(selected: str, options: Dict[str, Any]) -> None:
    college_data = next((c for c in options["colleges"] if c["name"] == selected), None)
    majors = college_data["majors"] if college_data else []
    st.session_state.major_options = majors or ["No majors available"]
    if st.session_state.profile["major"] not in st.session_state.major_options:
        st.session_state.profile["major"] = st.session_state.major_options[0]


def render_sidebar() -> None:
    with st.sidebar:
        st.subheader("Account")
        if st.session_state.authenticated:
            st.caption(f"Signed in as `{st.session_state.auth_user or 'user'}`")
            if st.button("Log Out", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.auth_user = ""
                st.rerun()
        st.divider()

        st.header("Student Profile")
        options = backend.build_options_payload()
        directory_on = backend.collegescorecard_enabled()

        if directory_on:
            st.caption("College directory: College Scorecard API connected")
            q = st.text_input("Search U.S. colleges", placeholder="Arizona State")
            if st.button("Search Schools", use_container_width=True):
                st.session_state.school_results = backend.directory_search_schools(q.strip())

            if st.session_state.school_results:
                labels = [s["label"] for s in st.session_state.school_results]
                default_idx = 0
                if st.session_state.selected_school_label in labels:
                    default_idx = labels.index(st.session_state.selected_school_label)
                chosen_label = st.selectbox("Select School", labels, index=default_idx)
                selected = next((x for x in st.session_state.school_results if x["label"] == chosen_label), None)
                if selected:
                    st.session_state.selected_school_label = selected["label"]
                    st.session_state.selected_school_id = selected["school_id"]
                    st.session_state.profile["college"] = selected["name"]
                    st.session_state.profile["college_id"] = selected["school_id"]
                    majors = backend.directory_school_majors(selected["school_id"])
                    st.session_state.major_options = majors or ["No majors found from directory"]
            elif q.strip():
                st.info("No schools found. Try a different search.")
        else:
            st.caption("Using local sample colleges (set `COLLEGESCORECARD_API_KEY` to enable live directory).")
            colleges = [c["name"] for c in options["colleges"]]
            current_college = st.session_state.profile["college"]
            default_index = colleges.index(current_college) if current_college in colleges else 0
            selected_college = st.selectbox("College", colleges, index=default_index)
            st.session_state.profile["college"] = selected_college
            st.session_state.profile["college_id"] = ""
            update_major_options_from_selection(selected_college, options)

        major_choices = st.session_state.major_options or ["No majors available"]
        current_major = st.session_state.profile["major"]
        major_index = major_choices.index(current_major) if current_major in major_choices else 0
        st.session_state.profile["major"] = st.selectbox("Major", major_choices, index=major_index)
        st.session_state.profile["year"] = st.text_input(
            "Current Year",
            value=st.session_state.profile["year"],
            placeholder="Freshman / Sophomore...",
        )
        st.session_state.profile["interests"] = st.text_input(
            "Interests",
            value=st.session_state.profile["interests"],
            placeholder="AI, cybersecurity, data...",
        )
        st.session_state.profile["completed_courses"] = st.text_area(
            "Completed Courses (comma-separated)",
            value=st.session_state.profile["completed_courses"],
            placeholder="CS101, MATH101, ENG101",
            height=95,
        )


def render_chat() -> None:
    st.markdown(
        """
        <section class="hero">
          <span class="eyebrow">AI Academic Advisor</span>
          <h1 style="margin:0.15rem 0 0.15rem 0;">DegreePath Advisor</h1>
          <p class="subhead">Build a 4-year roadmap, check prerequisites, discover electives, and audit graduation progress.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="pill">4-Year Planner</span><span class="pill">Prereq Checker</span><span class="pill">Elective Recommender</span><span class="pill">Grad Audit</span>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    if col1.button("Plan 4-Year Schedule", use_container_width=True):
        st.session_state.quick_prompt = "Build my 4-year degree schedule."
    if col2.button("Check Prerequisites", use_container_width=True):
        st.session_state.quick_prompt = "Check prerequisites for CS220 and CS310."
    if col3.button("Suggest Electives", use_container_width=True):
        st.session_state.quick_prompt = "Suggest electives based on my interests."
    if col4.button("Graduation Audit", use_container_width=True):
        st.session_state.quick_prompt = "Audit my graduation requirements."

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    pending_prompt = st.session_state.pop("quick_prompt", None)
    user_input = st.chat_input(
        "Ask about schedules, prerequisites, electives, or graduation...",
    )
    prompt = pending_prompt or user_input
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            result = assistant_reply(prompt, st.session_state.profile)
            reply = f"{result['reply']}\n\n`mode: {result['mode']}`"
            st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})


def main() -> None:
    inject_styles()
    init_state()
    if not st.session_state.authenticated:
        render_login()
        return
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
