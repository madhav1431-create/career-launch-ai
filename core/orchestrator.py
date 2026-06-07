from core.state import create_state
from agents.resume_agent import ResumeAgent
from agents.match_agent import MatchAgent
from agents.skill_gap_agent import SkillGapAgent
from agents.learning_planner import LearningPlannerAgent
from agents.career_strategist import CareerStrategistAgent
from agents.interview_coach import InterviewCoachAgent
from engine import extract_text_from_pdf, detect_skills

class Orchestrator:
    def __init__(self):
        self.agents = [
            ResumeAgent(),
            MatchAgent(),
            SkillGapAgent(),
            LearningPlannerAgent(),
            CareerStrategistAgent(),
            InterviewCoachAgent()
        ]

    def run(self, resume_path, jd_text, target_role):
        state = create_state()

        # Pre-load everything before agents start
        state["resume_text"] = extract_text_from_pdf(resume_path)
        state["jd_text"] = jd_text
        state["jd_skills"] = detect_skills(jd_text.lower())
        state["target_role"] = target_role

        # Run all 6 agents in sequence
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