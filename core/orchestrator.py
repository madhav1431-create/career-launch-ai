import os

from dotenv import load_dotenv

from agents.resume_agent import ResumeAgent
from agents.match_agent import MatchAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.learning_planner import LearningPlannerAgent
from agents.career_strategist import CareerStrategistAgent
from agents.interview_coach import InterviewCoachAgent
from agents.hiring_simulation import HiringSimulationAgent
from core.state import create_state
from engine import detect_skill_evidence, extract_text_from_pdf, get_role_skills


load_dotenv()


class Orchestrator:
    def __init__(self):
        self.agents = [
            ResumeAgent(),
            MatchAgent(),
            SkillGapAgent(),
            LearningPlannerAgent(),
        ]

    def run(self, resume_path, jd_text, target_role, include_ai=True):
        state = create_state()
        state["resume_text"] = extract_text_from_pdf(resume_path, preserve_case=True)
        state["target_role"] = target_role

        if jd_text and jd_text.strip():
            state["jd_text"] = jd_text
            state["requirement_evidence"] = detect_skill_evidence(jd_text)
            state["jd_skills"] = list(state["requirement_evidence"])
            state["jd_source"] = "uploaded"
        else:
            state["jd_skills"] = get_role_skills(target_role)
            state["jd_source"] = "role_based"

        api_key = os.getenv("GROQ_API_KEY", "").strip() if include_ai else ""
        state["ai_enabled"] = bool(api_key)
        agents = [
            *self.agents,
            CareerStrategistAgent(api_key=api_key),
            InterviewCoachAgent(api_key=api_key),
            HiringSimulationAgent(enabled=state["ai_enabled"]),
        ]
        for agent in agents:
            state = agent.run(state)

        # Keep the legacy score field aligned with the role-specific match.
        state["career_readiness_score"] = state["match_score"]
        return state
