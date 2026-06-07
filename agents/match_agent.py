from agents.base_agent import BaseAgent

class MatchAgent(BaseAgent):
    def __init__(self):
        super().__init__("Job Match Agent")

    def run(self, state: dict):
        self.log(state, "Analyzing job description match...")

        resume_skills = state["resume_skills"]
        jd_skills = state["jd_skills"]

        if len(jd_skills) == 0:
            state["match_score"] = 0
            self.log(state, "No JD skills found")
            return state

        matched = [s for s in jd_skills if s in resume_skills]
        score = round((len(matched) / len(jd_skills)) * 100)

        state["match_score"] = score
        self.log(state, f"Match Score: {score}% — {len(matched)}/{len(jd_skills)} skills matched")
        return state