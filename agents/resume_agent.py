from agents.base_agent import BaseAgent
from engine import classify_resume_skill_evidence

class ResumeAgent(BaseAgent):
    def __init__(self):
        super().__init__("Resume Intelligence Agent")

    def run(self, state: dict):
        self.log(state, "Starting resume analysis...")

        text = state["resume_text"]
        evidence, negated = classify_resume_skill_evidence(text)
        state["skill_evidence"] = evidence
        state["negated_skill_evidence"] = negated
        state["resume_skills"] = list(evidence)

        self.log(state, f"Detected skill terms in the resume: {len(evidence)}")
        if negated:
            self.log(state, f"Found explicit denials of experience: {len(negated)}")
        return state
