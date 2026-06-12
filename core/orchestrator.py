from core.state import create_state
from agents.resume_agent import ResumeAgent
from agents.match_agent import MatchAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.learning_planner import LearningPlannerAgent
from agents.career_strategist import CareerStrategistAgent
from agents.interview_coach import InterviewCoachAgent
from agents.hiring_simulation import HiringSimulationAgent
from engine import extract_text_from_pdf, detect_skills, get_role_skills

class Orchestrator:
    def __init__(self):
        self.agents = [
            ResumeAgent(),
            MatchAgent(),
            SkillGapAgent(),
            LearningPlannerAgent(),
            CareerStrategistAgent(),
            InterviewCoachAgent(),
            HiringSimulationAgent()
        ]

    def run(self, resume_path, jd_text, target_role):
        state = create_state()

        # Load resume
        state["resume_text"] = extract_text_from_pdf(resume_path)
        state["target_role"] = target_role

        # If JD provided use it, else use role based requirements
        if jd_text and jd_text.strip():
            state["jd_text"] = jd_text
            state["jd_skills"] = detect_skills(jd_text.lower())
            state["jd_source"] = "uploaded"
        else:
            role_skills = get_role_skills(target_role)
            state["jd_text"] = ""
            state["jd_skills"] = role_skills
            state["jd_source"] = "role_based"

        # Run all 7 agents in sequence
        for agent in self.agents:
            state = agent.run(state)

        # Compute final readiness score
        state["career_readiness_score"] = self._compute_readiness(state)

        return state

    def _compute_readiness(self, state):
        match = state["match_score"] * 0.4

        total_skills = len(state["resume_skills"]) + len(state["missing_skills"])
        if total_skills > 0:
            coverage = (len(state["resume_skills"]) / total_skills) * 100 * 0.4
        else:
            coverage = 0

        if state["level"] == "Senior":
            bonus = 20
        elif state["level"] == "Mid":
            bonus = 15
        else:
            bonus = 10

        score = round(match + coverage + bonus)
        return min(100, score)