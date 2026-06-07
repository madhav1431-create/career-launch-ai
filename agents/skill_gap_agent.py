from agents.base_agent import BaseAgent
from engine import compute_skill_gap, generate_overview

class SkillGapAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skill Gap Agent")

    def run(self, state: dict):
        self.log(state, "Detecting skill gaps...")

        gap = compute_skill_gap(state["resume_skills"], state["jd_skills"])
        overview, level = generate_overview(
            state["target_role"],
            state["resume_skills"],
            state["jd_skills"],
            gap
        )

        state["missing_skills"] = gap
        state["overview"] = overview
        state["level"] = level

        self.log(state, f"Found {len(gap)} skill gaps | Level: {level}")
        return state