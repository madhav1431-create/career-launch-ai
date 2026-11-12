import os
from copy import deepcopy

from dotenv import load_dotenv

from agents.resume_agent import ResumeAgent
from agents.match_agent import MatchAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.learning_planner import LearningPlannerAgent
from agents.career_strategist import CareerStrategistAgent
from agents.interview_coach import InterviewCoachAgent
from agents.hiring_simulation import HiringSimulationAgent
from core.state import create_state
from engine import classify_requirement_evidence, extract_text_from_pdf, get_role_skills


load_dotenv()


class Orchestrator:
    def __init__(self):
        self.resume_agent = ResumeAgent()
        self.agents = [
            MatchAgent(),
            SkillGapAgent(),
            LearningPlannerAgent(),
        ]

    def preview(self, resume_path, jd_text, target_role):
        state = create_state()
        state["resume_text"] = extract_text_from_pdf(resume_path, preserve_case=True)
        state["target_role"] = target_role

        if jd_text and jd_text.strip():
            state["jd_text"] = jd_text
            required, preferred = classify_requirement_evidence(jd_text)
            state["required_skills"] = list(required)
            state["preferred_skills"] = list(preferred)
            state["requirement_evidence"] = {**required, **preferred}
            state["jd_source"] = "uploaded"
        else:
            state["required_skills"] = list(get_role_skills(target_role))
            state["jd_source"] = "role_based"

        state["jd_skills"] = state["required_skills"] + state["preferred_skills"]
        return self.resume_agent.run(state)

    def run(self, resume_path, jd_text, target_role, include_ai=True, review=None):
        state = self.preview(resume_path, jd_text, target_role)
        return self.analyze(state, include_ai=include_ai, review=review)

    def analyze(self, preview, include_ai=True, review=None):
        state = deepcopy(preview)
        if review is not None:
            self._apply_review(state, review)

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

    @staticmethod
    def _apply_review(state, review):
        for field in ("resume_skills", "required_skills", "preferred_skills"):
            state[field] = list(review[field])
        state["jd_skills"] = state["required_skills"] + state["preferred_skills"]
        state["excluded_skill_evidence"] = {
            skill: line for skill, line in state["skill_evidence"].items()
            if skill not in state["resume_skills"]
        }
        for field, selected in (
            ("skill_evidence", state["resume_skills"]),
            ("requirement_evidence", state["jd_skills"]),
        ):
            state[field] = {skill: line for skill, line in state[field].items() if skill in selected}
        state["review_applied"] = True
