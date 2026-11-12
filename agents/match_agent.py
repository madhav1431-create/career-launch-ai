from agents.base_agent import BaseAgent

class MatchAgent(BaseAgent):
    def __init__(self):
        super().__init__("Job Match Agent")

    def run(self, state: dict):
        self.log(state, "Analyzing job description match...")

        resume_skills = set(state["resume_skills"])
        required = state["required_skills"]
        preferred = state["preferred_skills"]

        matched_required = [skill for skill in required if skill in resume_skills]
        matched_preferred = [skill for skill in preferred if skill in resume_skills]
        state["matched_skills"] = matched_required
        state["matched_preferred_skills"] = matched_preferred
        state["match_score"] = round(100 * len(matched_required) / len(required)) if required else 0
        state["preferred_match_score"] = (
            round(100 * len(matched_preferred) / len(preferred)) if preferred else None
        )
        self.log(state, f"Matched {len(matched_required)} of {len(required)} required skills")
        if preferred:
            self.log(state, f"Matched {len(matched_preferred)} of {len(preferred)} preferred skills")
        return state
