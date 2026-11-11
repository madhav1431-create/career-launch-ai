import streamlit as st
import time
from core.orchestrator import Orchestrator
from engine import UnreadablePDFError

# Page config
st.set_page_config(
    page_title="CareerLaunch AI",
    page_icon="🚀",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .score-card {
        background: linear-gradient(135deg, #1f77b4, #0d47a1);
        color: white;
        padding: 2rem;
        border-radius: 1rem;
        text-align: center;
    }
    .score-number {
        font-size: 4rem;
        font-weight: 800;
    }
    .agent-log {
        background: #0d1117;
        color: #00ff88;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .skill-tag {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        margin: 0.2rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🚀 CareerLaunch AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Multi-Agent Career Intelligence Platform</div>', unsafe_allow_html=True)

# Session state
if "state" not in st.session_state:
    st.session_state.state = None
if "ran" not in st.session_state:
    st.session_state.ran = False

# Sidebar inputs
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/rocket.png", width=80)
    st.title("CareerLaunch AI")
    st.markdown("---")

    st.subheader("📄 Upload Resume")
    resume_file = st.file_uploader("Upload your Resume PDF", type=["pdf"])

    st.subheader("🎯 Target Role")
    target_role = st.selectbox(
        "Select your target role",
        ["Data Scientist", "ML Engineer", "Data Analyst",
         "Backend Developer", "AI Engineer", "Frontend Developer"]
    )

    st.subheader("📋 Job Description")
    jd_text = st.text_area(
        "Paste the Job Description here",
        height=150,
        placeholder="Paste the job description text here..."
    )

    st.markdown("---")
    analyze_btn = st.button("🚀 Launch Career Analysis", use_container_width=True)

# Main logic
if analyze_btn:
    if resume_file is None:
        st.error("Please upload your resume PDF first.")
    elif jd_text.strip() == "":
        st.error("Please paste a job description.")
    else:
        # Show agent workflow live
        st.markdown("## 🤖 Agent Workflow — Live")
        agent_container = st.empty()

        def show_logs(logs):
            log_html = '<div class="agent-log">'
            for log in logs:
                log_html += f'[{log["time"]}] ✅ {log["agent"]} — {log["message"]}<br>'
            log_html += '</div>'
            agent_container.markdown(log_html, unsafe_allow_html=True)

        with st.spinner("Analyzing your resume..."):
            resume_file.seek(0)
            try:
                state = Orchestrator().run(resume_file, jd_text, target_role)
            except UnreadablePDFError as error:
                st.error(str(error))
                st.stop()

        st.session_state.state = state
        st.session_state.ran = True

        # Show final logs
        show_logs(state["agent_logs"])
        st.success("Analysis complete.")
        time.sleep(1)
        st.rerun()

# Results tabs
if st.session_state.ran and st.session_state.state:
    state = st.session_state.state

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 Career Dashboard",
        "🤖 Agent Workflow",
        "🧠 Skill Intelligence",
        "📚 Learning Plan",
        "💡 Project Recs",
        "🎤 Interview Prep"
    ])

    # TAB 1 — Career Dashboard
    with tab1:
        st.markdown("## 🏠 Career Dashboard")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="score-card">
                <div>Target Skill Coverage</div>
                <div class="score-number">{state['match_score']}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.metric("Matched Skills", f"{len(state['matched_skills'])} of {len(state['jd_skills'])}")

        with col3:
            st.metric("Skills Detected", len(state['resume_skills']))
            st.metric("Skill Gaps", len(state['missing_skills']))

        st.markdown("---")
        st.markdown("### 📝 Profile Overview")
        st.info(state['overview'])

        st.markdown("### 🎯 Career Strategy")
        st.success(state['career_strategy'])

    # TAB 2 — Agent Workflow
    with tab2:
        st.markdown("## 🤖 Agent Workflow")
        st.markdown("Every agent ran in sequence, passing results to the next.")
        st.markdown("---")

        for log in state["agent_logs"]:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.markdown(f"⏰ `{log['time']}`")
            with col2:
                st.markdown(f"✅ **{log['agent']}** — {log['message']}")

        st.markdown("---")
        st.markdown("### 🔄 Agent Pipeline")
        agents_flow = [
            ("1", "Resume Intelligence Agent", "Extracted skills from resume"),
            ("2", "Job Match Agent", f"Match Score: {state['match_score']}%"),
            ("3", "Skill Gap Agent", f"{len(state['missing_skills'])} gaps found"),
            ("4", "Learning Planner Agent", f"{len(state['roadmap'])} step roadmap"),
            ("5", "Career Strategist Agent", f"{len(state['project_recommendations'])} projects recommended"),
            ("6", "Interview Coach Agent", "Interview questions generated"),
            ("7", "Hiring Simulation Agent", "Practice feedback prepared"),
        ]

        for num, name, result in agents_flow:
            st.markdown(f"**Agent {num}** — {name} → `{result}`")
            if num != "7":
                st.markdown("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⬇️")

    # TAB 3 — Skill Intelligence
    with tab3:
        st.markdown("## 🧠 Skill Intelligence")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Skills Mentioned in Your Resume")
            for skill in state['resume_skills']:
                st.markdown(f"🟢 {skill.title()}")
                st.text(state["skill_evidence"][skill])

        with col2:
            st.markdown("### Target Skills Without a Resume Match")
            for skill in state['missing_skills']:
                st.markdown(f"🔴 {skill.title()}")

        st.markdown("---")
        st.markdown("### 📊 Match Analysis")
        st.progress(state['match_score'] / 100)
        st.markdown(f"**{state['match_score']}%** of required skills matched")

    # TAB 4 — Learning Plan
    with tab4:
        st.markdown("## 📚 Learning Plan")
        st.markdown(f"**{len(state['roadmap'])} skills** to learn in recommended order")
        st.markdown("---")

        total_weeks = sum(step['weeks'] for step in state['roadmap'])
        st.info(f"⏱️ Estimated total time: **{total_weeks} weeks**")

        for step in state['roadmap']:
            col1, col2, col3 = st.columns([1, 4, 2])
            with col1:
                st.markdown(f"**Step {step['step']}**")
            with col2:
                st.markdown(f"📖 {step['skill'].title()}")
            with col3:
                st.markdown(f"⏱️ {step['weeks']} weeks")

    # TAB 5 — Project Recommendations
    with tab5:
        st.markdown("## 💡 Project Recommendations")
        st.markdown("Build these projects to fill your skill gaps and impress recruiters.")
        st.markdown("---")

        for i, project in enumerate(state['project_recommendations']):
            with st.expander(f"🔨 Project {i+1}: {project['name']}", expanded=True):
                st.markdown(f"**Description:** {project['description']}")
                st.markdown("**Skills Covered:**")
                for skill in project.get('skills_covered', []):
                    st.markdown(f"  - {skill}")

        st.markdown("---")
        st.markdown("## 🏆 Recommended Certifications")
        for cert in state['certifications']:
            col1, col2 = st.columns([3, 2])
            with col1:
                st.markdown(f"📜 **{cert['name']}**")
                st.markdown(f"_{cert['relevance']}_")
            with col2:
                st.markdown(f"🏢 {cert['provider']}")
            st.markdown("---")

    # TAB 6 — Interview Prep
    with tab6:
        st.markdown("## 🎤 Interview Preparation")
        st.markdown(f"Prepared for: **{state['target_role']}** role")
        st.markdown("---")

        questions = state['interview_questions']

        st.markdown("### 💻 Technical Questions")
        for i, q in enumerate(questions.get('technical', [])):
            with st.expander(f"Q{i+1}: {q['question']}"):
                st.markdown(f"**Difficulty:** {q.get('difficulty', 'Medium')}")
                st.markdown(f"**Tip:** {q.get('tip', '')}")

        st.markdown("---")
        st.markdown("### 🤝 Behavioral Questions")
        for i, q in enumerate(questions.get('behavioral', [])):
            with st.expander(f"Q{i+1}: {q['question']}"):
                st.markdown(f"**Tip:** {q.get('tip', '')}")

        st.markdown("---")
        st.markdown("### 🔨 Project-Based Questions")
        for i, q in enumerate(questions.get('project', [])):
            with st.expander(f"Q{i+1}: {q['question']}"):
                st.markdown(f"**Tip:** {q.get('tip', '')}")
