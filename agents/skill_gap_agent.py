from agents.base_agent import BaseAgent
from engine import compute_skill_gap


class SkillGapAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skill Gap Agent")

    def run(self, state: dict):
        requirements = state["jd_skills"]
        gaps = compute_skill_gap(state["resume_skills"], requirements)
        state["missing_skills"] = gaps
        state["overview"] = self._generate_overview(requirements, state["matched_skills"], gaps)
        self.log(state, f"Target skills without a resume match: {len(gaps)}")
        return state

    def _generate_overview(self, requirements, matched, gaps):
        if not requirements:
            return (
                "The job description contains no supported skill terms. "
                "Try a more detailed description or use the built-in role requirements."
            )

        overview = f"Your resume mentions {len(matched)} of {len(requirements)} target skills."
        if matched:
            overview += f" Matching examples include {', '.join(matched[:4])}."
        if gaps:
            overview += (
                f" Start by checking whether you can add evidence for {', '.join(gaps[:3])}."
            )
        return overview
