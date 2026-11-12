from agents.base_agent import BaseAgent
from engine import compute_skill_gap


class SkillGapAgent(BaseAgent):
    def __init__(self):
        super().__init__("Skill Gap Agent")

    def run(self, state: dict):
        requirements = state["required_skills"]
        gaps = compute_skill_gap(state["resume_skills"], requirements)
        preferred_gaps = compute_skill_gap(state["resume_skills"], state["preferred_skills"])
        state["missing_skills"] = gaps
        state["missing_preferred_skills"] = preferred_gaps
        state["overview"] = self._generate_overview(state)
        self.log(state, f"Required skills without a match: {len(gaps)}")
        return state

    def _generate_overview(self, state):
        required = state["required_skills"]
        preferred = state["preferred_skills"]
        if not required and not preferred:
            return (
                "There are no supported skills in the selected requirements. "
                "Try a more detailed description or use the built-in role requirements."
            )

        matched = state["matched_skills"]
        gaps = state["missing_skills"]
        overview = f"Your profile matches {len(matched)} of {len(required)} required skills."
        if not required:
            overview = "The selected requirements contain only preferred skills."
        if preferred:
            overview += f" It also matches {len(state['matched_preferred_skills'])} of {len(preferred)} preferred skills."
        if matched:
            overview += f" Matching examples include {', '.join(matched[:4])}."
        if gaps:
            overview += (
                f" Start by checking whether you can add evidence for {', '.join(gaps[:3])}."
            )
        return overview
