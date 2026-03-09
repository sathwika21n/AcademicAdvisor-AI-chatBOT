from __future__ import annotations

import os
import hmac
from typing import Dict, List

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
            --bg-a: #f8f6f2;
            --bg-b: #e9f7f6;
            --ink: #15202b;
            --muted: #4c6170;
            --card: #ffffff;
            --accent: #0f766e;
            --accent-2: #0b5b98;
            --accent-soft: #d8f3f0;
            --line: #d5e3ea;
            --shadow: 0 12px 35px rgba(21, 32, 43, 0.08);
        }

        html, body, [class*="css"] {
            font-family: "IBM Plex Sans", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(60rem 60rem at 10% -5%, #ffffff 5%, rgba(255,255,255,0) 45%),
                radial-gradient(42rem 42rem at 90% 0%, #dff4f0 4%, rgba(223,244,240,0) 50%),
                linear-gradient(140deg, var(--bg-a) 0%, var(--bg-b) 100%);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255,255,255,0.95) 0%, rgba(233,247,246,0.95) 100%);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] div {
            color: var(--ink);
        }

        h1, h2, h3, h4 {
            font-family: "Space Grotesk", sans-serif !important;
            letter-spacing: -0.01em;
            color: var(--ink);
        }

        .hero {
            padding: 1.45rem 1.2rem 1.1rem 1.2rem;
            border: 1px solid rgba(255,255,255,0.85);
            border-radius: 20px;
            background:
                linear-gradient(125deg, rgba(15,118,110,0.14), rgba(11,91,152,0.09) 44%, rgba(255,255,255,0.90) 100%);
            box-shadow: var(--shadow);
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
            border-radius: 16px;
            border: 1px solid var(--line);
            background: var(--card);
            box-shadow: 0 8px 24px rgba(10, 45, 60, 0.06);
        }

        .pill {
            padding: 0.24rem 0.62rem;
            border-radius: 999px;
            border: 1px solid var(--line);
            background: #fff;
            color: var(--muted);
            font-size: 0.78rem;
            display: inline-block;
            margin-right: 0.45rem;
        }

        .visual-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.75rem 0 0.6rem 0;
        }

        .visual-card {
            border: 1px solid rgba(255,255,255,0.86);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            background:
                linear-gradient(145deg, rgba(255,255,255,0.96), rgba(231,245,246,0.95));
            box-shadow: 0 10px 25px rgba(21, 32, 43, 0.08);
        }

        .visual-title {
            margin: 0;
            font-size: 0.8rem;
            color: var(--muted);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .visual-value {
            margin: 0.1rem 0 0 0;
            font-size: 1.32rem;
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            color: var(--ink);
        }

        .visual-note {
            margin: 0.25rem 0 0 0;
            color: var(--muted);
            font-size: 0.82rem;
        }

        .timeline {
            margin-top: 0.35rem;
            display: flex;
            align-items: center;
            gap: 0.45rem;
        }

        .dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: linear-gradient(130deg, var(--accent), var(--accent-2));
            box-shadow: 0 0 0 3px rgba(15,118,110,0.16);
        }

        .bar {
            flex: 1;
            height: 5px;
            border-radius: 99px;
            background: linear-gradient(90deg, rgba(15,118,110,0.92), rgba(11,91,152,0.72));
        }

        .stButton > button {
            border-radius: 12px;
            border: 1px solid #c7dbe6;
            background: linear-gradient(140deg, #ffffff, #edf8ff);
            color: var(--ink);
            font-weight: 600;
        }

        .stButton > button:hover {
            border-color: #97bcd1;
            color: #0d4f81;
        }

        [data-testid="stChatInput"] {
            border: 1px solid #c9dae4;
            border-radius: 14px;
            box-shadow: 0 7px 16px rgba(21, 32, 43, 0.06);
        }

        @media (max-width: 900px) {
            .visual-grid {
                grid-template-columns: 1fr;
            }
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
    if "profile" not in st.session_state:
        st.session_state.profile = {
            "college": "",
            "college_id": "",
            "major": "",
            "year": "",
            "interests": "",
            "completed_courses": "",
        }


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
        st.caption("Enter any university and major. OpenRouter/LLM can respond even if not in local sample catalogs.")
        st.session_state.profile["college"] = st.text_input(
            "University",
            value=st.session_state.profile["college"],
            placeholder="Arizona State University",
        )
        st.session_state.profile["college_id"] = ""
        st.session_state.profile["major"] = st.text_input(
            "Major",
            value=st.session_state.profile["major"],
            placeholder="Computer Science",
        )
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
        """
        <section class="visual-grid">
          <article class="visual-card">
            <p class="visual-title">Roadmap Focus</p>
            <p class="visual-value">8 Semesters</p>
            <p class="visual-note">Balanced workload with prerequisite sequencing.</p>
            <div class="timeline"><span class="dot"></span><span class="bar"></span></div>
          </article>
          <article class="visual-card">
            <p class="visual-title">Personalization</p>
            <p class="visual-value">Major + Interests</p>
            <p class="visual-note">Uses your profile for elective relevance and pacing.</p>
            <div class="timeline"><span class="dot"></span><span class="bar"></span></div>
          </article>
          <article class="visual-card">
            <p class="visual-title">Audit View</p>
            <p class="visual-value">Progress Checks</p>
            <p class="visual-note">Identifies completed, pending, and at-risk requirements.</p>
            <div class="timeline"><span class="dot"></span><span class="bar"></span></div>
          </article>
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
