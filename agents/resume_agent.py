from agents.base_agent import BaseAgent
from engine import detect_skill_evidence

class ResumeAgent(BaseAgent):
    def __init__(self):
        super().__init__("Resume Intelligence Agent")

    def run(self, state: dict):
        self.log(state, "Starting resume analysis...")

        text = state["resume_text"]
        evidence = detect_skill_evidence(text)
        state["skill_evidence"] = evidence
        state["resume_skills"] = list(evidence)

        self.log(state, f"Detected skill terms in the resume: {len(evidence)}")
        return state
