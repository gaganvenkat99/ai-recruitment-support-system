import requests
import streamlit as st
import time


API_BASE_URL = "http://127.0.0.1:8006"
EXPERIENCE_OPTIONS = ["Any", "1 year", "2 years", "3 years", "4 years", "5 years", "6+ years"]
SKILL_OPTIONS = sorted({
    "C", "C++", "C#", "COBOL", "CSS", "Python", "PHP", "Perl", "Power BI", "PowerPoint",
    "Pandas", "PyTorch", "PySpark", "PostgreSQL", "Java", "JavaScript", "TypeScript",
    "React", "Angular", "Node.js", "Django", "Flask", "FastAPI", "HTML", "SQL", "MySQL",
    "MongoDB", "Excel", "MS Word", "MS Excel", "MS PowerPoint", "Microsoft Word",
    "Microsoft Excel", "Microsoft PowerPoint", "Communication", "Written Communication",
    "Verbal Communication", "Leadership", "Management", "Project Management", "Team Management",
    "Problem Solving", "Presentation", "Explanation Skills", "Analytical Skills", "Data Analysis",
    "Machine Learning", "Deep Learning", "NLP", "Docker", "Kubernetes", "Git", "Linux",
    "Windows", "Networking", "Troubleshooting", "Customer Service", "Negotiation",
    "Public Speaking", "Time Management",
})


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Manrope', sans-serif; color: #15324f; }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(44, 122, 255, 0.12), transparent 22%),
                radial-gradient(circle at top right, rgba(0, 176, 155, 0.10), transparent 18%),
                linear-gradient(180deg, #eef5fb 0%, #e8f1fa 100%);
        }
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1400px; }
        .hero {
            background: linear-gradient(135deg, #081a33 0%, #123a63 48%, #0f6d79 100%);
            border-radius: 30px;
            padding: 36px;
            color: #ffffff !important;
            margin-bottom: 22px;
            box-shadow: 0 24px 55px rgba(9, 28, 52, 0.22);
        }
        .hero h1, .hero p, .hero div, .hero span {
            color: #ffffff !important;
        }
        .hero-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-top: 18px;
        }
        .metric {
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 18px;
            padding: 14px 16px;
        }
        .metric-label {
            color: rgba(255,255,255,0.72);
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        .metric-value {
            font-size: 22px;
            font-weight: 800;
            margin-top: 6px;
        }
        .panel {
            background: rgba(255,255,255,0.95);
            border: 1px solid #d5e3ef;
            border-radius: 24px;
            padding: 22px;
            box-shadow: 0 18px 38px rgba(20,52,82,0.08);
        }
        .candidate {
            background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #d8e5f0;
            border-radius: 20px;
            padding: 18px;
            margin-bottom: 12px;
            box-shadow: 0 10px 22px rgba(20,52,82,0.05);
        }
        .pill { display:inline-block; padding:6px 10px; border-radius:999px; background:#e7fff6; color:#0c7e5c; font-weight:800; font-size:12px; }
        .resume-box { background:#f7fbff; border:1px solid #dbe6f0; border-radius:18px; padding:16px; white-space:pre-wrap; max-height:460px; overflow:auto; color:#18314d; }
        .section-kicker {
            color: #5d748d;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .stTextInput label, .stSelectbox label, .stMultiSelect label, .stSubheader, .stMarkdown, p, div {
            color: #15324f;
        }
        [data-testid="stTextInputRootElement"] input,
        [data-testid="stTextInputRootElement"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stTextInput"] textarea {
            background: #ffffff !important;
            color: #15324f !important;
            caret-color: #0d63f3 !important;
        }
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {
            background: #ffffff !important;
            border-radius: 14px !important;
            border: 1px solid #cfe0ed !important;
            color: #15324f !important;
            box-shadow: none !important;
        }
        div[data-baseweb="select"] input {
            color: #15324f !important;
            caret-color: #0d63f3 !important;
        }
        div[data-baseweb="popover"] *,
        ul[role="listbox"] *,
        li[role="option"] * {
            color: #15324f !important;
        }
        div[data-baseweb="popover"] {
            background: #ffffff !important;
        }
        div[data-baseweb="popover"] ul,
        div[data-baseweb="popover"] li,
        div[data-baseweb="popover"] [role="listbox"],
        div[data-baseweb="popover"] [role="option"] {
            background: #ffffff !important;
            color: #15324f !important;
        }
        div[data-baseweb="popover"] [role="option"][aria-selected="true"] {
            background: #e9f2ff !important;
            color: #0f3357 !important;
        }
        div[data-baseweb="popover"] [role="option"]:hover {
            background: #f2f7fd !important;
            color: #0f3357 !important;
        }
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div,
        div[data-baseweb="select"] p {
            color: #15324f !important;
        }
        .stSelectbox div[data-baseweb="select"] *,
        .stMultiSelect div[data-baseweb="select"] * {
            color: #15324f !important;
        }
        .stMultiSelect [data-baseweb="tag"] {
            background: #e8f2ff !important;
            color: #12385f !important;
        }
        .stMultiSelect [data-baseweb="tag"] span {
            color: #12385f !important;
        }
        input, textarea {
            color: #15324f !important;
        }
        input:focus, textarea:focus,
        [data-testid="stTextInputRootElement"] input:focus,
        [data-testid="stTextInputRootElement"] textarea:focus,
        [data-testid="stTextInput"] input:focus,
        [data-testid="stTextInput"] textarea:focus,
        div[data-baseweb="select"] *:focus,
        div[data-baseweb="input"] *:focus {
            outline: none !important;
            box-shadow: none !important;
            border-color: #cfe0ed !important;
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 14px;
            border: none;
            background: linear-gradient(135deg, #0d63f3 0%, #0b8db0 100%);
            color: white;
            font-weight: 800;
            min-height: 44px;
            box-shadow: 0 12px 24px rgba(13, 99, 243, 0.18);
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            color: white;
            background: linear-gradient(135deg, #0b58d7 0%, #0a7d9d 100%);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_post(path, payload):
    last_error = None
    for _ in range(4):
        try:
            response = requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2)
    raise last_error


def select_candidate(candidate):
    st.session_state["selected_candidate"] = candidate


def render_candidate(candidate, index):
    st.markdown(f"#### {index}. {candidate['candidate_title']}")
    info_cols = st.columns([1, 1, 1])
    info_cols[0].markdown(f"**ID:** {candidate['candidate_id']}")
    info_cols[1].markdown(f"**Experience:** {candidate['experience_display']}")
    info_cols[2].markdown(f"**Score:** {candidate['candidate_score']}")
    st.markdown(f"**Insights:** {candidate['candidate_insights']}")
    cols = st.columns(4)
    labels = ["Candidate ID", "Profile Title", "Candidate Insights", "Candidate Score"]
    for col, label, prefix in zip(cols, labels, ["id", "title", "insight", "score"]):
        with col:
            if st.button(label, key=f"{prefix}_{candidate['candidate_id']}", use_container_width=True):
                select_candidate(candidate)


def render():
    st.set_page_config(page_title="Candidate Discovery Workspace", page_icon="Hiring", layout="wide")
    inject_styles()
    if "candidate_results" not in st.session_state:
        st.session_state["candidate_results"] = []
    if "selected_candidate" not in st.session_state:
        st.session_state["selected_candidate"] = None

    st.markdown(
        """
        <div class="hero">
            <h1 style="margin:0 0 10px 0;">Candidate Discovery Workspace</h1>
            <p style="margin:0;max-width:860px;line-height:1.7;color:rgba(255,255,255,0.86);">
                Search resumes using role, experience, and additional skills. Submit the form to view
                candidate ID, profile title, candidate insights, and candidate score, then open the full resume on click.
            </p>
            <div class="hero-metrics">
                <div class="metric">
                    <div class="metric-label">Search Mode</div>
                    <div class="metric-value">Role + Experience + Skills</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Result View</div>
                    <div class="metric-value">Candidate Cards + Resume Panel</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Designed For</div>
                    <div class="metric-value">Recruiter Workflow</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown('<div class="section-kicker">Search Controls</div>', unsafe_allow_html=True)
        st.subheader("Search Form")
        with st.form("candidate_search_form", clear_on_submit=False):
            role = st.text_input("Role", placeholder="Example: Python Developer")
            experience = st.selectbox("Experience", EXPERIENCE_OPTIONS, index=0)
            additional_skills = st.multiselect("Additional Skills", SKILL_OPTIONS, placeholder="Type C, P, M, etc.")
            submitted = st.form_submit_button("Submit", use_container_width=True)

        if submitted and role.strip():
            payload = {"role": role.strip(), "experience": experience, "additional_skills": additional_skills}
            try:
                with st.spinner("Searching candidates..."):
                    response = api_post("/candidate_search", payload)
                st.session_state["candidate_results"] = response.get("candidates", [])
                st.session_state["selected_candidate"] = st.session_state["candidate_results"][0] if st.session_state["candidate_results"] else None
                if not st.session_state["candidate_results"]:
                    st.info("No candidates matched the selected filters. Try a broader role or fewer skills.")
            except requests.RequestException as exc:
                st.session_state["candidate_results"] = []
                st.session_state["selected_candidate"] = None
                st.error(f"Candidate search failed. Please confirm the backend is running and try again. Details: {exc}")
        elif submitted:
            st.warning("Please enter the required role.")

        results = st.session_state.get("candidate_results", [])
        if results:
            st.divider()
            st.markdown('<div class="section-kicker">Candidate Matches</div>', unsafe_allow_html=True)
            st.subheader("Search Output")
            st.success(f"Top {len(results)} matching candidates found.")
            for index, candidate in enumerate(results, start=1):
                with st.expander(f"{index}. {candidate['candidate_title']} | {candidate['candidate_score']}", expanded=(index == 1)):
                    render_candidate(candidate, index)
                    

    with right:
        candidate = st.session_state.get("selected_candidate")
        st.markdown('<div class="section-kicker">Resume Detail</div>', unsafe_allow_html=True)
        st.subheader("Candidate Resume Detail")
        if candidate:
            st.markdown(f"**Profile Title:** {candidate['candidate_title']}")
            st.markdown(f"**Candidate ID:** {candidate['candidate_id']}")
            st.markdown(f"**Candidate Score:** {candidate['candidate_score']}")
            st.markdown(f"**Experience:** {candidate['experience_display']}")
            st.markdown(f"**Candidate Insights:** {candidate['candidate_insights']}")
            display_text = candidate.get("resume_display_text") or candidate.get("resume_text", "")
            st.markdown(f"<div class='resume-box'>{display_text}</div>", unsafe_allow_html=True)
        else:
            st.info("Click Candidate ID, Profile Title, Candidate Insights, or Candidate Score to display the resume here.")
